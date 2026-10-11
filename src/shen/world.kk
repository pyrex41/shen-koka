module shen/world
import shen/values
pub type table<a> { Empty; Node(key:string, item:a, left:table<a>, right:table<a>) }
pub fun find(t:table<a>,key:string): maybe<a> {
  match t { Empty -> Nothing; Node(k,v,l,r) -> if key==k then Just(v) elif key<k then find(l,key) else find(r,key) }
}
pub fun put(t:table<a>,key:string,v:a): table<a> {
  match t { Empty -> Node(key,v,Empty,Empty); Node(k,x,l,r) -> if key==k then Node(k,v,l,r) elif key<k then Node(k,x,put(l,key,v),r) else Node(k,x,l,put(r,key,v)) }
}
pub struct world {
  globals:ref<global,table<value>>
  functions:ref<global,table<value>>
  heap:ref<global,list<(int,ref<global,vector<value>>)>>
  next-id:ref<global,int>
}
pub fun new-world(): <st<global>> world { World(ref(Empty),ref(Empty),ref([]),ref(0)) }
pub fun global-get(w:world,k:string): <st<global>,exn,div> value {
  match find((!w.globals),k) { Just(v) -> v; Nothing -> throw("unbound global: " ++ k) }
}
pub fun global-set(w:world,k:string,v:value): st<global> value { w.globals.set(put((!w.globals),k,v)); v }
pub fun define-function(w:world,k:string,v:value): st<global> () { w.functions.set(put((!w.functions),k,v)) }
pub fun alloc-vector(w:world,n:int): <st<global>,exn,div> value {
  if n<0 then throw("negative vector size")
  val id=(!w.next-id); w.next-id.set(id + 1)
  w.heap.set(Cons((id,ref(vector(n,Sym("shen.fail!")))),(!w.heap)))
  Vec(id)
}
fun vector-ref(h:list<(int,ref<global,vector<value>>)>,id:int): exn ref<global,vector<value>> {
  match h { [] -> throw("invalid vector handle"); Cons((k,v),xs) -> if id==k then v else vector-ref(xs,id) }
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
