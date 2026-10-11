module shen/machine
import shen/values
import shen/compile-kl
import shen/world
import shen/io
import std/num/int32
import std/num/float64

// Frames represent only pending work. Function application never adds a return frame.
type frame {
  Bind(name:string,body:term,env:environment)
  Select(yes:term,no:term,env:environment)
  Operator(args:list<term>,env:environment)
  Argument(fnval:value,done:list<value>,todo:list<term>,env:environment)
  Catch(hndl:term,env:environment)
  CatchNative(hndl:value)
  Recover(message:string)
  ApplyRest(args:list<value>)
}
type machine-state { Eval(expr:term,env:environment); Apply(fnval:value,args:list<value>); Return(result:value); Raise(message:string) }
fun nth(xs:list<value>,i:int): exn value { match xs { [] -> throw("wrong form arity"); Cons(x,rest) -> if i==0 then x else nth(rest,i - 1) } }
fun bind-args(ps:list<string>,vs:list<value>,env:environment): <exn,div> environment {
  match (ps,vs) { ([],[]) -> env; (Cons(p,pt),Cons(v,vt)) -> bind-args(pt,vt,Cons((p,v),env)); _ -> throw("wrong function arity") }
}
fun address-index(n:float64): exn int {
  val i=n.int
  if i.float64!=n then throw("vector index must be an integer") else i
}
fun primitive(w:world,name:string,args:list<value>): <st<global>,exn,div,console> value {
  fun a(i:int) { nth(args,i) }
  match (name,args) {
    ("open",[Text(name),Sym(dir)]) -> {
      if dir!="in" && dir!="out" then throw("invalid stream direction")
      val home=string-value(global-get(w,"*home-directory*"))
      val id=stream-open(home++name,dir=="out").int
      if id<0 then throw("cannot open " ++ home ++ name) else Stream(id)
    }
    ("read-byte",[Stream(id)]) -> { val n=stream-read(id.int32).int; if n < -1 then throw("read-byte error") else Num(n.float64) }
    ("write-byte",[Num(n),Stream(id)]) -> { if n<0.0 || n>255.0 || n.int.float64!=n then throw("write-byte: expected byte"); val result=stream-write(id.int32,n.int.int32).int; if result<0 then throw("write-byte error") else Num(result.float64) }
    ("close",[Stream(id)]) -> { if stream-close(id.int32).int!=0 then throw("close error"); Nil }
    ("get-time",[Sym(kind)]) -> Num(clock-time(kind=="run"))
    ("shen-koka.heap-live",[]) -> Num(live-vectors((!w.heap)).float64)
    ("list",xs) -> list-value(xs)
    ("cons",[x,y]) -> Pair(x,y)
    ("hd",[x]) -> head(x)
    ("tl",[x]) -> tail(x)
    ("cons?",[x]) -> truth(match x { Pair(_,_) -> True; _ -> False })
    ("number?",[x]) -> truth(match x { Num(_) -> True; _ -> False })
    ("string?",[x]) -> truth(match x { Text(_) -> True; _ -> False })
    ("absvector?",[x]) -> truth(match x { Vec(_) -> True; _ -> False })
    ("intern",[Text(x)]) -> Sym(x)
    ("set",[x,y]) -> global-set(w,symbol(x),y)
    ("value",[x]) -> global-get(w,symbol(x))
    ("=",[x,y]) -> truth(equal-value(w,x,y))
    ("+",[x,y]) -> Num(numeric(x)+numeric(y))
    ("-",[x,y]) -> Num(numeric(x)-numeric(y))
    ("*",[x,y]) -> Num(numeric(x)*numeric(y))
    ("/",[x,y]) -> { val n=numeric(y); if n==0.0 then throw("division by zero") else Num(numeric(x)/n) }
    ("<",[x,y]) -> truth(numeric(x)<numeric(y))
    (">",[x,y]) -> truth(numeric(x)>numeric(y))
    ("<=",[x,y]) -> truth(numeric(x)<=numeric(y))
    (">=",[x,y]) -> truth(numeric(x)>=numeric(y))
    ("cn",[Text(x),Text(y)]) -> Text(x++y)
    ("str",[x]) -> match x {
      Sym(s) -> Text(s)
      Num(n) -> Text(n.show)
      Text(s) -> Text(s)
      _ -> throw("str: cannot convert non-atomic value")
    }
    ("pos",[Text(s),Num(n)]) -> { if !n.is-finite || n<0.0 then throw("pos: out of range"); val cs=s.list; match cs.drop(n.truncate.int).head { Just(c) -> Text(c.string); Nothing -> throw("pos: out of range") } }
    ("tlstr",[Text(s)]) -> match s.list { Cons(_,rest) -> Text(rest.string); _ -> throw("tlstr: empty string") }
    ("n->string",[Num(n)]) -> { if !n.is-finite || n<0.0 || n>1114111.0 || n.int.float64!=n then throw("n->string: expected character code"); Text(n.int.char.string) }
    ("string->n",[Text(s)]) -> match s.list { Cons(c,_) -> Num(c.int.float64); _ -> throw("string->n: empty string") }
    ("absvector",[Num(n)]) -> {
      if !n.is-finite then throw("absvector: expected finite size")
      val size=n.truncate
      if size<0.0 || size>268435456.0 then throw("absvector: size out of range")
      alloc-vector(w,size.int)
    }
    ("<-address",[v,Num(n)]) -> vector-get(w,v,address-index(n))
    ("address->",[v,Num(n),x]) -> vector-set(w,v,address-index(n),x)
    ("simple-error",[Text(s)]) -> throw(s)
    ("error-to-string",[Fault(s)]) -> Text(s)
    ("shen.char-stinput?",[_]) -> Sym("false")
    ("shen.char-stoutput?",[_]) -> Sym("false")
    _ -> throw("unknown primitive or wrong arguments: " ++ name)
  }
}
fun step(w:world,c:machine-state,ks:list<frame>): <st<global>,div,console> (machine-state,list<frame>) {
  match c {
    Eval(expr,env) -> match expr {
      Literal(v) -> (Return(v),ks)
      Variable(s) -> (Return(lookup(env,s).default(Sym(s))),ks)
      Define(name,ps,body) -> { define-function(w,name,make-closure(w,ps,body,[])); (Return(Sym(name)),ks) }
      Lambda(ps,body) -> (Return(make-closure(w,ps,body,env)),ks)
      Let(name,binding,body) -> (Eval(binding,env),Cons(Bind(name,body,env),ks))
      Branch(test,yes,no) -> (Eval(test,env),Cons(Select(yes,no,env),ks))
      Trap(body,hndl) -> (Eval(body,env),Cons(Catch(hndl,env),ks))
      Call(op,args) -> (Eval(op,env),Cons(Operator(args,env),ks))
    }
    Apply(f,args) -> match f {
      Closure(_,ps,body,env) -> try(fn() {
        val n=ps.length
        if args.length < n then
          (Return(make-closure(w,ps.drop(args.length),body,bind-args(ps.take(args.length),args,env))),ks)
        elif args.length > n then
          (Eval(body,bind-args(ps,args.take(n),env)),Cons(ApplyRest(args.drop(n)),ks))
        else (Eval(body,bind-args(ps,args,env)),ks)
      },fn(e) (Raise(e.message),ks))
      Compiled(_,arity,code,captured,bound) -> {
        val all=bound ++ args
        if all.length < arity then (Return(make-compiled(w,arity,code,captured,all)),ks) else {
          val rest=if all.length > arity then Cons(ApplyRest(all.drop(arity)),ks) else ks
          val (vs,ts)=machine-roots(c,rest)
          try(fn() {
            match call-native(w,code,captured,all.take(arity),vs,ts) {
              Done(v) -> (Return(v),rest)
              TailApply(f,xs) -> (Apply(f,xs),rest)
              Protected(body,hndl) -> (Apply(body,[]),Cons(CatchNative(hndl),rest))
            }
          },fn(e) (Raise(e.message),rest))
        }
      }
      Sym("eval-kl") -> try(fn() { match args { [x] -> (Eval(compile-term(x),[]),ks); _ -> (Raise("eval-kl: wrong arity"),ks) } },fn(e) (Raise(e.message),ks))
      Sym("thaw") -> match args { [x] -> (Apply(x,[]),ks); _ -> (Raise("thaw: wrong arity"),ks) }
      Sym(name) -> match find((!w.functions),name) {
        Just(v) -> (Apply(v,args),ks)
        Nothing -> try(fn() (Return(primitive(w,name,args)),ks),fn(e) (Raise(e.message),ks))
      }
      _ -> (Raise("application of non-function"),ks)
    }
    Return(v) -> match ks {
      [] -> (Return(v),[])
      Cons(k,rest) -> match k {
        Bind(name,body,env) -> (Eval(body,Cons((name,v),env)),rest)
        Select(yes,no,env) -> match v { Sym("true") -> (Eval(yes,env),rest); Sym("false") -> (Eval(no,env),rest); _ -> (Raise("expected boolean"),rest) }
        Operator(args,env) -> match args { [] -> (Apply(v,[]),rest); Cons(x,xs) -> (Eval(x,env),Cons(Argument(v,[],xs,env),rest)) }
        Argument(f,done,todo,env) -> match todo { [] -> (Apply(f,Cons(v,done).reverse),rest); Cons(x,xs) -> (Eval(x,env),Cons(Argument(f,Cons(v,done),xs,env),rest)) }
        Catch(_,_) -> (Return(v),rest)
        CatchNative(_) -> (Return(v),rest)
        Recover(msg) -> (Apply(v,[Fault(msg)]),rest)
        ApplyRest(args) -> (Apply(v,args),rest)
      }
    }
    Raise(msg) -> match ks {
      [] -> (Raise(msg),[])
      Cons(CatchNative(hndl),rest) -> (Apply(hndl,[]),Cons(Recover(msg),rest))
      Cons(Catch(hndl,env),rest) -> (Eval(hndl,env),Cons(Recover(msg),rest))
      Cons(_,rest) -> (Raise(msg),rest)
    }
  }
}
// Collection occurs only between machine steps, after primitive temporaries
// have disappeared. Every suspended operand, handler and lexical binding is a root.
fun machine-roots(c:machine-state,ks:list<frame>) {
  var vs : list<value> := []
  var ts : list<term> := []
  fun env(e:environment) { vs := e.map(fn((_,v)) v) ++ vs }
  match c {
    Eval(t,e) -> { ts := Cons(t,ts); env(e) }
    Apply(f,args) -> { vs := Cons(f,args) ++ vs }
    Return(v) -> { vs := Cons(v,vs) }
    Raise(_) -> ()
  }
  ks.foreach fn(k) {
    match k {
      Bind(_,body,e) -> { ts := Cons(body,ts); env(e) }
      Select(yes,no,e) -> { ts := Cons(yes,Cons(no,ts)); env(e) }
      Operator(args,e) -> { ts := args ++ ts; env(e) }
      Argument(f,done,todo,e) -> { vs := Cons(f,done) ++ vs; ts := todo ++ ts; env(e) }
      Catch(hndl,e) -> { ts := Cons(hndl,ts); env(e) }
      CatchNative(hndl) -> { vs := Cons(hndl,vs) }
      Recover(msg) -> { vs := Cons(Fault(msg),vs) }
      ApplyRest(args) -> { vs := args ++ vs }
  } }
  (vs,ts)
}
fun collect-machine(w:world,c:machine-state,ks:list<frame>): <st<global>,exn,div> () {
  val (vs,ts)=machine-roots(c,ks)
  collect-vectors(w,vs,ts)
}
fun run(w:world,c:machine-state,ks:list<frame>): <st<global>,exn,div,console> value {
  if (!w.allocations) >= (!w.gc-at) then collect-machine(w,c,ks)
  match (c,ks) {
    (Return(v),[]) -> v
    (Raise(msg),[]) -> throw(msg)
    _ -> {
      val (next,frames)=step(w,c,ks)
      run(w,next,frames)
    }
  }
}
pub fun invoke(w:world,f:value,args:list<value>): <st<global>,exn,div,console> value { run(w,Apply(f,args),[]) }
pub fun evaluate(w:world,expr:value): <st<global>,exn,div,console> value { run(w,Eval(compile-term(expr),[]),[]) }

pub fun invoke-protected(w:world,body:value,hndl:value): <st<global>,exn,div,console> value { run(w,Apply(body,[]),[CatchNative(hndl)]) }
