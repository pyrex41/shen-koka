#!/usr/bin/env python3
"""Focused semantic checks; these never replace the full distribution gate."""
import json,pathlib,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
cases={
 'fail-value':('(defun fail () shen.fail!) (trap-error (fail) (lambda E wrong))','fail\nshen.fail!'),
 'freeze-repeat':('(set c 0) (let F (freeze (set c (+ (value c) 1))) (cons (thaw F) (cons (thaw F) ())))','0\n[1 2]'),
 'vector-alias':('(let X (absvector 2) (let Y X (let Z (address-> X 1 42) (<-address Y 1))))','42'),
 'vector-sentinel':('(<-address (absvector 1) 0)','shen.fail!'),
 'error':('(trap-error (simple-error "hello") (lambda E (error-to-string E)))','"hello"'),
 'lexical':('(let X 7 (let F (lambda Y (+ X Y)) (let X 100 (F 2))))','9'),
 'order':('(set c 0) (cons (set c 1) (cons (value c) ()))','0\n[1 1]'),
 'non-strict':('(if true 42 (simple-error "bad")) (and false (simple-error "bad")) (or true (simple-error "bad"))','42\nfalse\ntrue'),
 'redefine':('(defun f () 1) (defun g () (f)) (g) (defun f () 2) (g)','f\ng\n1\nf\n2'),
 'self-tail':('(defun loop (N) (if (= N 0) true (loop (- N 1)))) (loop 1000000)','loop\ntrue'),
 'mutual-tail':('(defun a (N) (if (= N 0) true (b (- N 1)))) (defun b (N) (a N)) (a 1000000)','a\nb\ntrue'),
 'indirect-tail':('(defun loop (F N) (if (= N 0) true (F F (- N 1)))) (loop loop 1000000)','loop\ntrue'),
}
results={}
for name,(source,expected) in cases.items():
 try:
  p=subprocess.run([str(ROOT/'bin/shen-koka'),'kl','-e',source],capture_output=True,text=True,timeout=30)
  results[name]={'source':source,'expected':expected,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'status':'PASS' if p.returncode==0 and p.stdout.strip()==expected else 'FAIL'}
 except subprocess.TimeoutExpired:
  results[name]={'source':source,'status':'UNKNOWN','blocker':'30 second timeout'}
print(json.dumps({'binary_sha256':hashlib.sha256((ROOT/'.build/shen-koka').read_bytes()).hexdigest(),'cases':results},indent=2))
raise SystemExit(0 if all(r['status']=='PASS' for r in results.values()) else 1)
