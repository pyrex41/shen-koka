module shen/boot
import shen/values
import shen/world
import shen/machine
import shen/read-kl
import std/os/env
import std/os/file
import std/os/path

pub fun eval-source(w:world,source:string): <st<global>,exn,div,console> value {
  // Use the pinned Shen reader and compiler, including macro expansion.
  val forms=invoke(w,Sym("read-from-string"),[Text(source)])
  var result : value := Nil
  items(forms).foreach fn(form) { result := invoke(w,Sym("eval"),[form]) }
  result
}
pub fun boot(w:world,root:string): <st<global>,exn,div,console,fsys,ndet> () {
  [("*stinput*",Stream(0)),("*stoutput*",Stream(1)),("*sterror*",Stream(2)),
   ("*home-directory*",Text("")),("*language*",Text("Koka")),
   ("*implementation*",Text("Koka 3.2.3")),("*port*",Text("shen-koka")),
   ("*porters*",Text("Shen-Koka contributors")),("*os*",Text("Unix")),("*release*",Text("0.0.1"))].foreach fn((k,v)) { global-set(w,k,v); () }
  ["yacc","core","load","prolog","reader","sequent","sys","toplevel","track","writer","backend","macros","declarations","t-star","types","extension-features","extension-expand-dynamic","extension-launcher"].foreach fn(name) {
    val code=read-text-file(path(root++"/kernel/klambda/"++name++".kl"))
    try(fn() { parse-kl(code).foreach(fn(form) { evaluate(w,form); () }) }, fn(e) throw("boot "++name++": "++e.message))
  }
  if get-env-value("SHEN_KOKA_PPM_COMPAT").default("0")=="1" then {
    parse-kl(read-text-file(path(root++"/compat/programmable-pattern-matching.kl"))).foreach(fn(form) { evaluate(w,form); () })
  }
}
