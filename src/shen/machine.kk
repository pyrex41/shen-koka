module shen/machine
import shen/values
import shen/world
import shen/io
import std/num/int32
import std/num/float64

// Frames represent only pending work. Function application never adds a return frame.
type frame {
  Bind(name:string,body:value,env:environment)
  Select(yes:value,no:value,env:environment)
  Operator(args:list<value>,env:environment)
  Argument(fnval:value,done:list<value>,todo:list<value>,env:environment)
  Catch(hndl:value,env:environment)
  Recover(message:string)
}
type machine-state { Eval(expr:value,env:environment); Apply(fnval:value,args:list<value>); Return(result:value); Raise(message:string) }
fun nth(xs:list<value>,i:int): exn value { match xs { [] -> throw("wrong form arity"); Cons(x,rest) -> if i==0 then x else nth(rest,i - 1) } }
fun bind-args(ps:list<string>,vs:list<value>,env:environment): <exn,div> environment {
  match (ps,vs) { ([],[]) -> env; (Cons(p,pt),Cons(v,vt)) -> bind-args(pt,vt,Cons((p,v),env)); _ -> throw("wrong function arity") }
}
fun cond-expr(xs:list<value>): <exn,div> value {
  match xs { [] -> Pair(Sym("simple-error"),list-value([Text("cond: no true branch")])); Cons(cl,rest) -> list-value([Sym("if"),head(cl),head(tail(cl)),cond-expr(rest)]) }
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
    ("write-byte",[Num(n),Stream(id)]) -> { val result=stream-write(id.int32,n.int.int32).int; if result<0 then throw("write-byte error") else Num(result.float64) }
    ("close",[Stream(id)]) -> { if stream-close(id.int32).int!=0 then throw("close error"); Nil }
    ("get-time",[Sym(kind)]) -> Num(clock-time(kind=="run"))
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
    ("=",[x,y]) -> truth(equal(x,y))
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
    ("pos",[Text(s),Num(n)]) -> { val cs=s.list; match cs.drop(n.int).head { Just(c) -> Text(c.string); Nothing -> throw("pos: out of range") } }
    ("tlstr",[Text(s)]) -> match s.list { Cons(_,rest) -> Text(rest.string); _ -> throw("tlstr: empty string") }
    ("n->string",[Num(n)]) -> Text(n.int.char.string)
    ("string->n",[Text(s)]) -> match s.list { Cons(c,_) -> Num(c.int.float64); _ -> throw("string->n: empty string") }
    ("absvector",[Num(n)]) -> alloc-vector(w,n.int)
    ("<-address",[v,Num(n)]) -> vector-get(w,v,n.int)
    ("address->",[v,Num(n),x]) -> vector-set(w,v,n.int,x)
    ("simple-error",[Text(s)]) -> throw(s)
    ("error-to-string",[Fault(s)]) -> Text(s)
    ("shen.char-stinput?",[_]) -> Sym("false")
    ("shen.char-stoutput?",[_]) -> Sym("false")
    _ -> throw("unknown primitive or wrong arguments: " ++ name)
  }
}
fun step(w:world,c:machine-state,ks:list<frame>): <st<global>,exn,div,console> (machine-state,list<frame>) {
  match c {
    Eval(expr,env) -> match expr {
      Sym(s) -> (Return(lookup(env,s).default(expr)),ks)
      Pair(op,rest) -> {
        val xs=items(rest)
        match op {
          Sym("type") -> (Eval(nth(xs,0),env),ks)
          Sym("defun") -> { val name=symbol(nth(xs,0)); val ps=items(nth(xs,1)).map(symbol); define-function(w,name,Closure(ps,nth(xs,2),[])); (Return(Sym(name)),ks) }
          Sym("lambda") -> (Return(Closure([symbol(nth(xs,0))],nth(xs,1),env)),ks)
          Sym("freeze") -> (Return(Closure([],nth(xs,0),env)),ks)
          Sym("let") -> (Eval(nth(xs,1),env),Cons(Bind(symbol(nth(xs,0)),nth(xs,2),env),ks))
          Sym("if") -> (Eval(nth(xs,0),env),Cons(Select(nth(xs,1),nth(xs,2),env),ks))
          Sym("cond") -> (Eval(cond-expr(xs),env),ks)
          Sym("and") -> (Eval(list-value([Sym("if"),nth(xs,0),nth(xs,1),Sym("false")]),env),ks)
          Sym("or") -> (Eval(list-value([Sym("if"),nth(xs,0),Sym("true"),nth(xs,1)]),env),ks)
          Sym("trap-error") -> (Eval(nth(xs,0),env),Cons(Catch(nth(xs,1),env),ks))
          _ -> (Eval(op,env),Cons(Operator(xs,env),ks))
        }
      }
      _ -> (Return(expr),ks)
    }
    Apply(f,args) -> match f {
      Closure(ps,body,env) -> (Eval(body,bind-args(ps,args,env)),ks)
      Sym("eval-kl") -> (Eval(nth(args,0),[]),ks)
      Sym("thaw") -> (Apply(nth(args,0),[]),ks)
      Sym(name) -> match find((!w.functions),name) {
        Just(v) -> (Apply(v,args),ks)
        Nothing -> (Return(primitive(w,name,args)),ks)
      }
      _ -> throw("application of non-function")
    }
    Return(v) -> match ks {
      [] -> (Return(v),[])
      Cons(k,rest) -> match k {
        Bind(name,body,env) -> (Eval(body,Cons((name,v),env)),rest)
        Select(yes,no,env) -> (Eval(if boolean(v) then yes else no,env),rest)
        Operator(args,env) -> match args { [] -> (Apply(v,[]),rest); Cons(x,xs) -> (Eval(x,env),Cons(Argument(v,[],xs,env),rest)) }
        Argument(f,done,todo,env) -> match todo { [] -> (Apply(f,Cons(v,done).reverse),rest); Cons(x,xs) -> (Eval(x,env),Cons(Argument(f,Cons(v,done),xs,env),rest)) }
        Catch(_,_) -> (Return(v),rest)
        Recover(msg) -> (Apply(v,[Fault(msg)]),rest)
      }
    }
    Raise(msg) -> match ks {
      [] -> (Raise(msg),[])
      Cons(Catch(hndl,env),rest) -> (Eval(hndl,env),Cons(Recover(msg),rest))
      Cons(_,rest) -> (Raise(msg),rest)
    }
  }
}
fun run(w:world,c:machine-state,ks:list<frame>): <st<global>,exn,div,console> value {
  match (c,ks) {
    (Return(v),[]) -> v
    (Raise(msg),[]) -> throw(msg)
    _ -> {
      val (next,frames)=try(fn() step(w,c,ks),fn(e) (Raise(e.message),ks))
      run(w,next,frames)
    }
  }
}
pub fun invoke(w:world,f:value,args:list<value>): <st<global>,exn,div,console> value { run(w,Apply(f,args),[]) }
pub fun evaluate(w:world,expr:value): <st<global>,exn,div,console> value { run(w,Eval(expr,[]),[]) }
