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
  invoke(w,Sym("shen.initialise"),[])
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
fun print-cli-result(result:value) {
 // Strings are CLI output, while symbols (including shen.fail!) remain explicit.
 match result { Text(s) -> println(s); _ -> println(render(result)) }
}
fun eval-arguments(w:world,args:list<string>) {
 match args {
  [] -> ()
  Cons(flag,rest) -> {
   val name=match invoke(w,Sym("shen.x.launcher.eval-flag-map"),[Text(flag)]) { Text(s) -> s; _ -> flag }
   match (name,rest) {
    ("--eval",Cons(code,more)) -> {
     val result=eval-source(w,code)
     if !boolean(global-get(w,"*hush*")) then print-cli-result(result)
     eval-arguments(w,more)
    }
    ("--load",Cons(file,more)) -> { invoke(w,Sym("load"),[Text(file)]); eval-arguments(w,more) }
    ("--quiet",more) -> { global-set(w,"*hush*",Sym("true")); eval-arguments(w,more) }
    ("--set",Cons(key,Cons(setting,more))) -> {
     val k=eval-source(w,key)
     val v=eval-source(w,setting)
     invoke(w,Sym("set"),[k,v]); eval-arguments(w,more)
    }
    ("--repl",_) -> { invoke(w,Sym("shen.credits"),[]); repl(w) }
    _ -> throw("Invalid eval argument: "++flag)
   }
  }
 }
}
fun cli() {
 val w=new-world()
 match get-args() {
   [] -> start-repl(w)
   ["repl"] -> start-repl(w)
   ["--version"] -> println("shen-koka 0.0.1 experimental; pinned Shen 43.1")
   ["kl","-e",code] -> parse-kl(code).foreach(fn(v) println(render(evaluate(w,v))))
   ["kl",file] -> parse-kl(read-text-file(path(file))).foreach(fn(v) println(render(evaluate(w,v))))
   Cons("eval",args) -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); eval-arguments(w,args) }
   Cons("script",Cons(file,args)) -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); finish-command(w,invoke(w,Sym("shen.x.launcher.script-command"),[Text(file),list-value(args.map(fn(s) Text(s)))])) }
   _ -> throw("usage: shen-koka {kl -e EXPR|kl FILE|eval -e EXPR|script FILE|repl}")
 }
}

pub fun main() { try(cli,fn(e) { println("shen-koka: " ++ e.message); process-exit(1.int32) }) }
