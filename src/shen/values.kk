module shen/values
import std/num/float64

pub type value {
  Nil
  Sym(name:string)
  Text(text:string)
  Num(number:float64)
  Pair(first:value, rest:value)
  Closure(identity:int,params:list<string>, body:term, env:list<(string,value)>)
  Vec(id:int)
  Stream(id:int)
  Fault(message:string)
}
// Predecoded executable forms: compile once at defun/eval-kl, never on a call.
pub type term {
  Literal(value:value)
  Variable(name:string)
  Define(name:string,params:list<string>,body:term)
  Lambda(params:list<string>,body:term)
  Let(name:string,binding:term,body:term)
  Branch(test:term,yes:term,no:term)
  Trap(body:term,recover:term)
  Call(operator:term,args:list<term>)
}
pub alias environment = list<(string,value)>
pub fun truth(b:bool): value { if b then Sym("true") else Sym("false") }
pub fun boolean(v:value): exn bool {
  match v { Sym("true") -> True; Sym("false") -> False; _ -> throw("expected boolean") }
}
pub fun symbol(v:value): exn string { match v { Sym(s) -> s; _ -> throw("expected symbol") } }
pub fun string-value(v:value): exn string { match v { Text(s) -> s; _ -> throw("expected string") } }
pub fun numeric(v:value): exn float64 { match v { Num(n) -> n; _ -> throw("expected number") } }
pub fun head(v:value): exn value { match v { Pair(a,_) -> a; _ -> throw("hd of non-cons") } }
pub fun tail(v:value): exn value { match v { Pair(_,b) -> b; _ -> throw("tl of non-cons") } }
pub fun items(v:value): <exn,div> list<value> {
  match v { Nil -> []; Pair(a,b) -> Cons(a,items(b)); _ -> throw("expected proper list") }
}
pub fun list-value(xs:list<value>): value { xs.foldr(Nil,fn(x,r) Pair(x,r)) }
pub fun equal(a:value,b:value): div bool {
  match (a,b) {
    (Nil,Nil) -> True
    (Sym(x),Sym(y)) -> x==y
    (Text(x),Text(y)) -> x==y
    (Num(x),Num(y)) -> x==y
    (Pair(x,xs),Pair(y,ys)) -> equal(x,y) && equal(xs,ys)
    (Vec(x),Vec(y)) -> x==y
    (Stream(x),Stream(y)) -> x==y
    (Closure(x,_,_,_),Closure(y,_,_,_)) -> x==y
    _ -> False
  }
}
pub fun render(v:value): div string {
  match v {
    Nil -> "[]"
    Sym(s) -> s
    Text(s) -> "\"" ++ s ++ "\""
    Num(n) -> n.show
    Pair(a,b) -> "[" ++ render(a) ++ render-tail(b) ++ "]"
    Closure(_,_,_,_) -> "#<function>"
    Vec(n) -> "#<vector " ++ n.show ++ ">"
    Stream(n) -> "#<stream " ++ n.show ++ ">"
    Fault(s) -> s
  }
}
fun render-tail(v:value): div string {
  match v { Nil -> ""; Pair(a,b) -> " " ++ render(a) ++ render-tail(b); _ -> " | " ++ render(v) }
}
pub fun lookup(env:environment,name:string): maybe<value> {
  match env { [] -> Nothing; Cons((k,v),xs) -> if k==name then Just(v) else lookup(xs,name) }
}
