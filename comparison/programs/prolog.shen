\\ Predicate names are local to this process; retain the kernel's first answer.
(defprolog koka.parent
  abe homer <-- ;
  homer bart <-- ;
  homer lisa <--;)

(defprolog koka.grandparent
  X Z <-- (koka.parent X Y) (koka.parent Y Z);)

(do (print (prolog? (koka.grandparent abe Who) (return Who))) (nl))
