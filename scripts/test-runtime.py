#!/usr/bin/env python3
"""Focused semantic checks; these never replace the full distribution gate."""
import json,pathlib,subprocess,hashlib,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
cases={
 'deep-ordered-operands':('(set c 0) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) (cons (set c (+ (value c) 1)) ())))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))) (value c)', '0\n[1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64]\n64'),
 'deep-lexical-capture':('(let X0 0 (let X1 1 (let X2 2 (let X3 3 (let X4 4 (let X5 5 (let X6 6 (let X7 7 (let X8 8 (let X9 9 (let X10 10 (let X11 11 (let X12 12 (let X13 13 (let X14 14 (let X15 15 (let X16 16 (let X17 17 (let X18 18 (let X19 19 (let X20 20 (let X21 21 (let X22 22 (let X23 23 (let X24 24 (let X25 25 (let X26 26 (let X27 27 (let X28 28 (let X29 29 (let X30 30 (let X31 31 (let X32 32 (let X33 33 (let X34 34 (let X35 35 (let X36 36 (let X37 37 (let X38 38 (let X39 39 (+ X0 X39)))))))))))))))))))))))))))))))))))))))))', '39'),
 'fraction-pos-truncation':('(pos "abcd" 1.5)','"b"'),
 'fraction-vector-truncation':('(trap-error (<-address (absvector 1.5) 1) (lambda E caught))','caught'),
 'fraction-character-code':('(trap-error (n->string 65.5) (lambda E caught))','caught'),
 'negative-character-code':('(trap-error (n->string -1) (lambda E caught))','caught'),
 'large-character-code':('(trap-error (n->string 1114112) (lambda E caught))','caught'),
 'nonfinite-character-code':('(trap-error (n->string (* 1e308 1e308)) (lambda E caught))','caught'),

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
