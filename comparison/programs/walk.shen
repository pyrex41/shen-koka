\\ A deterministic first-success walker. The empty input returns Shen's sentinel.
(define koka.walk
  F [] -> (fail)
  F [X | Y] -> X where (F X)
  F [_ | Y] -> (koka.walk F Y))

(do (print (koka.walk (/. X (= X 3)) [1 2 3 4 3])) (nl))
