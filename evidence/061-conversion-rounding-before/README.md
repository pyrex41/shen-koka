# Conversion mismatch before repair

Koka KL probes:

```sh
bin/shen-koka kl -e '(pos "abcd" 1.5) (trap-error (n->string 65.5) (lambda E caught)) (trap-error (n->string -1) (lambda E caught))'
```

Pinned Go probes use `eval -e` separately for each form, with `/.` in place
of `lambda`. The first attempted Go command contained all three forms but its
CLI evaluated only the first; the two remaining forms were then run separately.
The output files contain all three observations in order.

Koka returns `"c"`, `"B"`, and the replacement character. Go returns `b`,
`caught`, `caught`. Koka's host float64-to-int conversion rounds to nearest;
this must not substitute for truncating an index or validating a character code.
Reference binary provenance is retained in attempt 060.
