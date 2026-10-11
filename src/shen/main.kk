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
fun cli() {
 val w=new-world()
 match get-args() {
   ["--version"] -> println("shen-koka 0.0.1 experimental KLambda (kernel not booted)")
   ["kl","-e",code] -> parse-kl(code).foreach(fn(v) println(render(evaluate(w,v))))
   ["kl",file] -> parse-kl(read-text-file(path(file))).foreach(fn(v) println(render(evaluate(w,v))))
   ["eval","-e",code] -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); println(render(eval-source(w,code))) }
   ["script",file] -> { boot(w,get-env-value("SHEN_KOKA_ROOT").default(".")); invoke(w,Sym("load"),[Text(file)]); () }
   _ -> throw("usage: shen-koka {kl -e EXPR|kl FILE|eval -e EXPR|script FILE}")
 }
}

pub fun main() { try(cli,fn(e) { println("shen-koka: " ++ e.message); process-exit(1.int32) }) }
