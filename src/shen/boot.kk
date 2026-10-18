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
pub fun initialize-platform(w:world): <st<global>> () {
  [
   ("shen.*history*",list-value([])),("shen.*tc*",Sym("false")),("shen.*source-form-handlers*",list-value([])),("*macros*",list-value([])),("shen.*gensym*",Num(0.0)),
   ("shen.*tracking*",list-value([])),("shen.*profiled*",list-value([])),("shen.*special*",list-value([])),("shen.*extraspecial*",list-value([])),("shen.*spy*",Sym("false")),
   ("shen.*datatypes*",list-value([])),("shen.*alldatatypes*",list-value([])),("shen.*shen-type-theory-enabled?*",Sym("true")),("shen.*package*",Sym("null")),
   ("shen.*synonyms*",list-value([])),("shen.*occurs*",Sym("true")),("shen.*factorise?*",Sym("false")),("shen.*maxinferences*",Num(1000000.0)),
   ("*maximum-print-sequence-size*",Num(20.0)),("shen.*call*",Num(0.0)),("shen.*infs*",Num(0.0)),("*hush*",Sym("false")),
   ("shen.*optimise*",Sym("false")),("*version*",Text("43.1")),("shen.*names*",list-value([])),("shen.*step*",Sym("false")),("shen.*it*",Text("")),
   ("shen.*residue*",list-value([])),("*absolute*",list-value([])),("shen.*prolog-memory*",Num(1000.0)),("shen.*loading?*",Sym("false")),("shen.*userdefs*",list-value([])),
   ("shen.*demodulation-function*",list-value([])),("shen.*custom-pattern-compiler*",Sym("false")),("shen.*custom-pattern-reducer*",Sym("false")),
   ("*stinput*",Stream(0)),("*stoutput*",Stream(1)),("*sterror*",Stream(2)),
   ("*home-directory*",Text("")),("*property-vector*",Vec(0)),("*language*",Text("Koka")),
   ("*implementation*",Text("Koka 3.2.3")),("*port*",Text("shen-koka")),
   ("*porters*",Text("Shen-Koka contributors")),("*os*",Text("Unix")),("*release*",Text("0.0.1"))].foreach fn((k,v)) { global-set(w,k,v); () }
}
pub fun boot(w:world,root:string): <st<global>,exn,div,console,fsys,ndet> () {
  initialize-platform(w)
  ["yacc","core","load","prolog","reader","sequent","sys","dict","t-star","toplevel","track","types","writer","backend","macros","declarations","init","extension-features","extension-expand-dynamic","extension-launcher","extension-programmable-pattern-matching","extension-namespaces","extension-type-annotations"].foreach fn(name) {
    val code=read-text-file(path(root++"/kernel/klambda/"++name++".kl"))
    try(fn() { parse-kl(code).foreach(fn(form) { evaluate(w,form); () }) }, fn(e) throw("boot "++name++": "++e.message))
  }
  load-compat(w,root)
}
pub fun load-compat(w:world,root:string): <st<global>,exn,div,console,fsys,ndet> () {
  if get-env-value("SHEN_KOKA_PPM_COMPAT").default("0")=="1" then {
    parse-kl(read-text-file(path(root++"/compat/programmable-pattern-matching.kl"))).foreach(fn(form) { evaluate(w,form); () })
  }
}
