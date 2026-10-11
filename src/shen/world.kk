module shen/world
import shen/values
import std/core/unsafe
pub type table<a> { Empty; Node(key:string, item:a, left:table<a>, right:table<a>) }
pub fun find(t:table<a>,key:string): maybe<a> {
  match t { Empty -> Nothing; Node(k,v,l,r) -> if key==k then Just(v) elif key<k then find(l,key) else find(r,key) }
}
pub fun put(t:table<a>,key:string,v:a): table<a> {
  match t { Empty -> Node(key,v,Empty,Empty); Node(k,x,l,r) -> if key==k then Node(k,v,l,r) elif key<k then Node(k,x,put(l,key,v),r) else Node(k,x,l,put(r,key,v)) }
}
type vector-tree { NoVectors; VectorNode(slot:maybe<ref<global,vector<value>>>, zero:vector-tree, one:vector-tree) }
fun vector-put(t:vector-tree,id:int,r:ref<global,vector<value>>): div vector-tree {
  val (slot,z,o)=match t { NoVectors -> (Nothing,NoVectors,NoVectors); VectorNode(s,z,o) -> (s,z,o) }
  if id==0 then VectorNode(Just(r),z,o)
  elif id % 2 == 0 then VectorNode(slot,vector-put(z,id / 2,r),o)
  else VectorNode(slot,z,vector-put(o,id / 2,r))
}
pub struct world {
  globals:ref<global,table<value>>
  functions:ref<global,table<value>>
  heap:ref<global,vector-tree>
  next-id:ref<global,int>
  allocations:ref<global,int>
  gc-at:ref<global,int>
}
pub fun new-world(): <st<global>> world { World(ref(Empty),ref(Empty),ref(NoVectors),ref(0),ref(0),ref(1024)) }
pub fun global-get(w:world,k:string): <st<global>,exn,div> value {
  match find((!w.globals),k) { Just(v) -> v; Nothing -> throw("unbound global: " ++ k) }
}
pub fun global-set(w:world,k:string,v:value): st<global> value { w.globals.set(put((!w.globals),k,v)); v }
pub fun define-function(w:world,k:string,v:value): st<global> () { w.functions.set(put((!w.functions),k,v)) }
pub fun alloc-vector(w:world,n:int): <st<global>,exn,div> value {
  if n<0 then throw("negative vector size")
  w.allocations.set((!w.allocations) + 1)
  val id=(!w.next-id); w.next-id.set(id + 1)
  w.heap.set(vector-put((!w.heap),id,ref(vector(n,Sym("shen.fail!")))))
  Vec(id)
}
fun vector-ref(h:vector-tree,id:int): <exn,div> ref<global,vector<value>> {
  match h {
    NoVectors -> throw("invalid vector handle")
    VectorNode(slot,z,o) -> if id==0 then match slot { Just(r) -> r; Nothing -> throw("invalid vector handle") }
      elif id % 2 == 0 then vector-ref(z,id / 2) else vector-ref(o,id / 2)
  }
}
pub fun vector-get(w:world,v:value,i:int): <st<global>,exn,div> value {
  match v { Vec(id) -> { val r=vector-ref((!w.heap),id); (!r)[i] }; _ -> throw("expected vector") }
}
pub fun vector-set(w:world,v:value,i:int,x:value): <st<global>,exn,div> value {
  match v {
    Vec(id) -> { val r=vector-ref((!w.heap),id); r.modify(fn(loc) { loc[i] := x }); v }
    _ -> throw("expected vector")
  }
}

pub fun make-closure(w:world,ps:list<string>,body:term,env:environment): st<global> value {
  val id=(!w.next-id); w.next-id.set(id + 1)
  Closure(id,ps,body,env)
}
// Structural equality preserves handle identity for mutation, and terminates on
// cyclic vector graphs by remembering already-compared handle pairs.
pub fun equal-value(w:world,a:value,b:value): <st<global>,exn,div> bool {
  equal-seen(w,a,b,[])
}
fun equal-seen(w:world,a:value,b:value,seen:list<(int,int)>): <st<global>,exn,div> bool {
  match (a,b) {
    (Pair(x,xs),Pair(y,ys)) -> unsafe-ptr-eq(a,b) || (equal-seen(w,x,y,seen) && equal-seen(w,xs,ys,seen))
    (Vec(x),Vec(y)) -> {
      if x==y || seen.any(fn((p,q)) p==x && q==y) then True else {
        val xs = !(vector-ref((!w.heap),x))
        val ys = !(vector-ref((!w.heap),y))
        xs.length==ys.length && equal-slots(w,xs,ys,0,Cons((x,y),seen))
      }
    }
    _ -> equal(a,b)
  }
}
fun equal-slots(w:world,xs:vector<value>,ys:vector<value>,i:int,seen:list<(int,int)>): <st<global>,exn,div> bool {
  if i==xs.length then True else
    equal-seen(w,xs[i],ys[i],seen) && equal-slots(w,xs,ys,i + 1,seen)
}

// Numeric identities never repeat. Vectors and closures share the identity space,
// so one traced-id trie cuts both mutable cycles and shared closure environments.
type marks { Unmarked; Mark(marked:bool,zero:marks,one:marks) }
fun marked(ms:marks,id:int): div bool {
  match ms { Unmarked -> False; Mark(b,z,o) -> if id==0 then b elif id % 2 == 0 then marked(z,id / 2) else marked(o,id / 2) }
}
fun mark(ms:marks,id:int): div marks {
  val (b,z,o)=match ms { Unmarked -> (False,Unmarked,Unmarked); Mark(b,z,o) -> (b,z,o) }
  if id==0 then Mark(True,z,o) elif id % 2 == 0 then Mark(b,mark(z,id / 2),o) else Mark(b,z,mark(o,id / 2))
}
type trace-work { ValueRoot(v:value); TermRoot(t:term) }
fun env-roots(env:environment,rest:list<trace-work>): list<trace-work> {
  env.foldl(rest,fn(xs,(_,v)) Cons(ValueRoot(v),xs))
}
fun trace(w:world,todo:list<trace-work>,seen:marks): <st<global>,exn,div> marks {
  match todo {
    [] -> seen
    Cons(work,rest) -> match work {
      ValueRoot(v) -> match v {
        Pair(x,y) -> trace(w,Cons(ValueRoot(x),Cons(ValueRoot(y),rest)),seen)
        Vec(id) -> if marked(seen,id) then trace(w,rest,seen) else {
          val slots = !(vector-ref((!w.heap),id))
          trace(w,slots.list.foldl(rest,fn(xs,v) Cons(ValueRoot(v),xs)),mark(seen,id))
        }
        Closure(id,_,body,env) -> if marked(seen,id) then trace(w,rest,seen) else
          trace(w,Cons(TermRoot(body),env-roots(env,rest)),mark(seen,id))
        _ -> trace(w,rest,seen)
      }
      TermRoot(t) -> match t {
        Literal(v) -> trace(w,Cons(ValueRoot(v),rest),seen)
        Variable(_) -> trace(w,rest,seen)
        Define(_,_,body) -> trace(w,Cons(TermRoot(body),rest),seen)
        Lambda(_,body) -> trace(w,Cons(TermRoot(body),rest),seen)
        Let(_,binding,body) -> trace(w,Cons(TermRoot(binding),Cons(TermRoot(body),rest)),seen)
        Branch(test,yes,no) -> trace(w,Cons(TermRoot(test),Cons(TermRoot(yes),Cons(TermRoot(no),rest))),seen)
        Trap(body,hndl) -> trace(w,Cons(TermRoot(body),Cons(TermRoot(hndl),rest)),seen)
        Call(op,args) -> trace(w,Cons(TermRoot(op),args.foldl(rest,fn(xs,t) Cons(TermRoot(t),xs))),seen)
      }
    }
  }
}
fun table-roots(t:table<value>,rest:list<trace-work>): list<trace-work> {
  match t { Empty -> rest; Node(_,v,l,r) -> table-roots(l,table-roots(r,Cons(ValueRoot(v),rest))) }
}
fun sweep(t:vector-tree,seen:marks,id:int,bit:int): div vector-tree {
  match t {
    NoVectors -> NoVectors
    VectorNode(slot,z,o) -> {
      val live=if marked(seen,id) then slot else Nothing
      val zs=sweep(z,seen,id,bit * 2)
      val os=sweep(o,seen,id + bit,bit * 2)
      match (live,zs,os) { (Nothing,NoVectors,NoVectors) -> NoVectors; _ -> VectorNode(live,zs,os) }
    }
  }
}
pub fun collect-vectors(w:world,values:list<value>,terms:list<term>): <st<global>,exn,div> () {
  val roots=values.foldl(terms.map(TermRoot),fn(xs,v) Cons(ValueRoot(v),xs))
  val seen=trace(w,table-roots((!w.globals),table-roots((!w.functions),roots)),Unmarked)
  w.heap.set(sweep((!w.heap),seen,0,1))
  w.gc-at.set((!w.allocations) + 1024)
}

pub fun live-vectors(t:vector-tree): int {
  match t { NoVectors -> 0; VectorNode(slot,z,o) -> (if slot.is-just then 1 else 0) + live-vectors(z) + live-vectors(o) }
}
