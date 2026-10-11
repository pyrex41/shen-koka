module shen/read-kl
import shen/values
import std/num/float64
fun space(c:char): bool { c==' ' || c=='\n' || c=='\r' || c=='\t' }
fun skip(cs:list<char>): list<char> { cs.drop-while(space) }
fun quoted(cs:list<char>,acc:list<char>): exn (value,list<char>) {
  match cs {
    [] -> throw("unterminated KL string")
    Cons('"',rest) -> (Text(acc.reverse.string),rest)
    Cons(c,rest) -> quoted(rest,Cons(c,acc))
  }
}
fun atom(cs:list<char>,acc:list<char>): (value,list<char>) {
  match cs {
    Cons(c,rest) -> if !space(c) && c!='(' && c!=')' then atom(rest,Cons(c,acc)) else finish-atom(acc,cs)
    [] -> finish-atom(acc,cs)
  }
}
fun finish-atom(acc:list<char>,rest:list<char>): (value,list<char>) {
  val s=acc.reverse.string
  val v=match (if s=="+" || s=="-" || s=="" then Nothing else parse-float64(s)) { Just(n) -> Num(n); Nothing -> Sym(s) }
  (v,rest)
}
fun read-list(cs:list<char>,acc:list<value>): <exn,div> (value,list<char>) {
  match skip(cs) {
    [] -> throw("unterminated KL list")
    Cons(')',rest) -> (list-value(acc.reverse),rest)
    xs -> { val (v,rest)=read-one(xs); read-list(rest,Cons(v,acc)) }
  }
}
fun read-one(cs:list<char>): <exn,div> (value,list<char>) {
  match skip(cs) {
    [] -> throw("unexpected KL EOF")
    Cons('(',rest) -> read-list(rest,[])
    Cons(')',_) -> throw("unexpected KL close")
    Cons('"',rest) -> quoted(rest,[])
    xs -> atom(xs,[])
  }
}
fun read-many(cs:list<char>,acc:list<value>): <exn,div> list<value> {
  match skip(cs) { [] -> acc.reverse; xs -> { val (v,rest)=read-one(xs); read-many(rest,Cons(v,acc)) } }
}
pub fun parse-kl(s:string): <exn,div> list<value> { read-many(s.list,[]) }
