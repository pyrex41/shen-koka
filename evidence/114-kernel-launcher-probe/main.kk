import shen/values
import shen/read-kl
import shen/world
import shen/machine
import shen/boot
import shen/io
import std/num/int32
import std/os/env
import std/os/file
import std/os/path
// Keep the pinned reader, history, package handling and typechecking toplevel.
// The host owns only EOF termination; the upstream recursive loop ignores EOF.
fun repl(w:world) {
  invoke(w,Sym("shen.initialise_environment"),[])
  invoke(w,Sym("shen.prompt"),[])
  try(fn() { invoke(w,Sym("shen.read-evaluate-print"),[]); () },fn(e) {
    if !(stdin-eof() && e.message=="error: empty stream") then println(e.message)
  })
  if !stdin-eof() then repl(w)
}
fun start-repl(w:world) {
  boot(w,get-env-value("SHEN_KOKA_ROOT").default("."))
  invoke(w,Sym("shen.credits"),[])
  repl(w)
}
fun finish-command(w:world,result:value) {
 match result {
  Pair(Sym("success"),Nil) -> ()
  Pair(Sym("launch-repl"),_) -> { invoke(w,Sym("shen.credits"),[]); repl(w) }
  Pair(Sym("error"),Pair(Text(message),Nil)) -> throw(message)
  _ -> throw("invalid launcher result: "++render(result))
 }
}
fun cli() {
 val w=new-world()
 match get-args() {
   [] -> start-repl(w)
   ["repl"] -> start-repl(w)
   ["--version"] -> println("shen-koka 0.0.1 experimental; pinned Shen 42")
   ["kl","-e",code] -> parse-kl(code).foreach(fn(v) println(render(evaluate(w,v))))
   ["kl",file] -> parse-kl(read-text-file(path(file))).foreach(fn(v) println(render(evaluate(w,v))))
   Cons("eval",args) -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); finish-command(w,invoke(w,Sym("shen.x.launcher.eval-command"),[list-value(args.map(fn(s) Text(s)))])) }
   Cons("script",Cons(file,args)) -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); finish-command(w,invoke(w,Sym("shen.x.launcher.script-command"),[Text(file),list-value(args.map(fn(s) Text(s)))])) }
   _ -> throw("usage: shen-koka {kl -e EXPR|kl FILE|eval -e EXPR|script FILE|repl}")
 }
}

pub fun main() { try(cli,fn(e) { println("shen-koka: " ++ e.message); process-exit(1.int32) }) }
