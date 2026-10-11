#!/usr/bin/env python3
"""Focused semantic checks; these never replace the full distribution gate."""
import json,pathlib,subprocess,hashlib,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
cases={
 'stale-stream-write':('(set *home-directory* "") (let A (open "stream-probe.tmp" out) (let C (close A) (let B (open "stream-probe.tmp" out) (let Old (trap-error (write-byte 65 A) (lambda E stale)) (let C (close B) Old)))))','""\nstale'),
 'stale-stream-close':('(set *home-directory* "") (let A (open "stream-probe.tmp" out) (let C (close A) (let B (open "stream-probe.tmp" out) (let Old (trap-error (close A) (lambda E stale)) (let New (write-byte 66 B) (let C (close B) (cons Old (cons New ()))))))))','""\n[stale 66]'),

 'untaken-malformed-form':('(if true 42 (lambda X Y Z))','42'),
 'operator-before-arguments':('(set c 0) (((lambda X (lambda Y Y)) (set c 1)) (value c))','0\n1'),

 'negative-pos':('(trap-error (pos "a" -1) (lambda E caught))','caught'),
 'fractional-address':('(trap-error (<-address (absvector 1) 0.5) (lambda E caught))','caught'),

 'gc-cycle-reclamation':('(defun garbage (N) (if (= N 0) (< (shen-koka.heap-live) 1024) (let V (absvector 1) (let X (address-> V 0 V) (garbage (- N 1)))))) (garbage 10000)','garbage\ntrue'),
 'gc-closure-root':('(defun churn (N) (if (= N 0) true (let V (absvector 1) (churn (- N 1))))) (let V (absvector 1) (let X (address-> V 0 42) (let F (freeze (<-address V 0)) (let X (churn 3000) (thaw F)))))','churn\n42'),
 'gc-error-handler-root':('(defun churn (N) (if (= N 0) (simple-error "done") (let V (absvector 1) (churn (- N 1))))) (let V (absvector 1) (let X (address-> V 0 42) (trap-error (churn 3000) (lambda E (<-address V 0)))))','churn\n42'),
 'gc-operand-root':('(defun churn (N) (if (= N 0) true (let V (absvector 1) (churn (- N 1))))) (defun first (X Y) (<-address X 0)) (first (address-> (absvector 1) 0 42) (churn 3000))','churn\nfirst\n42'),

 'partial-application':('(defun sum (X Y) (+ X Y)) ((sum 20) 22)','sum\n42'),
 'over-application':('((lambda X (lambda Y (+ X Y))) 20 22)','42'),
 'vector-structural-equality':('(let A (absvector 1) (let B (absvector 1) (= A B)))','true'),
 'vector-cycle-equality':('(let A (absvector 1) (let B (absvector 1) (let X (address-> A 0 A) (let Y (address-> B 0 B) (= A B)))))','true'),
 'closure-self-equality':('(let F (lambda X X) (= F F))','true'),
 'closure-distinct':('(= (lambda X X) (lambda X X))','false'),
 'boolean-rhs':('(trap-error (and true 42) (lambda E invalid))','invalid'),
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
  with tempfile.TemporaryDirectory(prefix='shen-case-') as cwd:
   p=subprocess.run([str(ROOT/'bin/shen-koka'),'kl','-e',source],cwd=cwd,capture_output=True,text=True,timeout=30)
  results[name]={'source':source,'expected':expected,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'status':'PASS' if p.returncode==0 and p.stdout.strip()==expected else 'FAIL'}
 except subprocess.TimeoutExpired:
  results[name]={'source':source,'status':'UNKNOWN','blocker':'30 second timeout'}
print(json.dumps({'binary_sha256':hashlib.sha256((ROOT/'.build/shen-koka').read_bytes()).hexdigest(),'cases':results},indent=2))
raise SystemExit(0 if all(r['status']=='PASS' for r in results.values()) else 1)
