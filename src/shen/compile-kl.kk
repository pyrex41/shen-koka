module shen/compile-kl
import shen/values
fun conditional(xs:list<value>): <exn,div> term {
  match xs {
    [] -> Call(Variable("simple-error"),[Literal(Text("cond: no true branch"))])
    Cons(cl,rest) -> match items(cl) {
      [test,body] -> Branch(compile-term(test),compile-term(body),conditional(rest))
      _ -> throw("invalid cond clause")
    }
  }
}
pub fun compile-term(expr:value): <exn,div> term {
  match expr {
    Sym(name) -> Variable(name)
    Pair(op,rest) -> {
      val xs=items(rest)
      match (op,xs) {
        (Sym("defun"),[name,params,body]) -> Define(symbol(name),items(params).map(symbol),compile-term(body))
        (Sym("lambda"),[name,body]) -> Lambda([symbol(name)],compile-term(body))
        (Sym("freeze"),[body]) -> Lambda([],compile-term(body))
        (Sym("let"),[name,binding,body]) -> Let(symbol(name),compile-term(binding),compile-term(body))
        (Sym("if"),[test,yes,no]) -> Branch(compile-term(test),compile-term(yes),compile-term(no))
        (Sym("and"),[a,b]) -> Branch(compile-term(a),Branch(compile-term(b),Literal(Sym("true")),Literal(Sym("false"))),Literal(Sym("false")))
        (Sym("or"),[a,b]) -> Branch(compile-term(a),Literal(Sym("true")),Branch(compile-term(b),Literal(Sym("true")),Literal(Sym("false"))))
        (Sym("cond"),clauses) -> conditional(clauses)
        (Sym("trap-error"),[body,recover]) -> Trap(compile-term(body),compile-term(recover))
        (Sym("type"),[body,_]) -> compile-term(body)
        _ -> Call(compile-term(op),xs.map(compile-term))
      }
    }
    _ -> Literal(expr)
  }
}
