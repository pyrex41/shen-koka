(load "harness.shen")
(report "proof assistant"

   (tc +) true
   (load "proof assistant.shen") loaded
   (tc -) false)

(report "quantifier machine"

  (tc +) true
   (load "qmachine.shen") loaded
   (exists [1 (+ 1) (= 100)] (> 50)) true
   (tc -) false) 
 
(report "depth first search"

   (tc +) true
   (load "depth.shen") loaded
   (depth 4 (/. X [(+ X 3) (+ X 4) (+ X 5)]) (/. X (= X 27)) (/. X (> X 27))) [4 7 10 13 16 19 22 27]
   (depth 4 (/. X [(+ X 3)]) (/. X (= X 27)) (/. X (> X 27))) []
   (tc -) false) 

(report "secd"

   (tc +) true
   (load "secd1.shen") loaded
   (evaluate [[lambda x x] b]) b   
   (evaluate [lambda x x]) [closure [] x x]
   (let If [lambda z [lambda x [lambda y [[z x] y]]]]
        True [lambda x [lambda y x]]
        (evaluate [[[If True] a] b]))  a)
        
(report "unification"

   (tc -)  false
   (load "unification.shen") loaded
   (unify [f a] X) [[X f a]]
   (unify [f Y] [f b]) [[Y | b]])
   
(report "total in Prolog"

 (load "totalprolog.shen")  loaded
 (prolog? (findall Age (lived Person Age) Ages) 
          (total Ages Total) 
          (return Total))   7625)
          
(report "Prolog fork"
 
   (load "fork.shen") loaded
   (prolog? (g1 a))    true) 
   
(report "Prolog interpreter"

   (tc +) true
   (load "prologinterp.shen") loaded 
   (tc -) false)                      
   
(reset)