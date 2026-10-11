# Implementation progress

Work branch: `implement/klambda-runtime`. Initial base: `c2bcf31`.
No AGENTS.md exists at that base. Reference worktrees were created detached at
all four revisions in `research/source-inventory.json`; existing checkouts were
not reset or cleaned.

## Implemented

- Koka-owned boxed KLambda values, minimal KL reader, lexical closures, separate
  globals/function bindings, dynamic function dispatch, and explicit machine frames.
- Non-strict forms, repeatable freeze/thaw, catchable errors, byte streams, and
  mutable vector handles with shared identity.
- Full S42 load-time boot using unchanged pinned modules; Shen source evaluation
  and script loading through the original reader/compiler.
- Full-distribution runner with fixed 134 + 8 denominators, group reports,
  preserved stdout/stderr, source assertion identities, and previous-PASS checks.

## Tested so far

See `evidence/` for individual attempts. The focused runtime report includes
million-step self, mutual, and indirect calls, dynamic redefinition, lexical
capture, aliasing, failure-as-value, operand order, and repeated thaw.
These checks supplement the canonical suite; they do not qualify the port.

Linux uses `nix develop` and `nix develop .#comparison` with the unchanged lock.
Koka 3.2.3, Go 1.27.0 and LuaJIT 2.1.1774638290 were executed. Other platforms
have not been tested in this implementation session.

## Reproduction

```sh
nix develop --command bash scripts/build.sh
bin/shen-koka eval -e '(+ 1 2)'
bin/shen-koka kl -e '(trap-error (simple-error "x") (lambda E 42))'
nix develop --command python3 scripts/test-runtime.py
nix develop --command python3 scripts/run-shen-suite.py --output artifacts/run-001
# After a change, use a fresh output path and compare the earlier report:
nix develop --command python3 scripts/run-shen-suite.py \
  --output artifacts/run-002 --previous artifacts/run-001/report.json
```

Suite scripts execute from their prescribed distribution directories. The runner
supplies yes responses to failure-continuation prompts; it does not alter test
predictions or implement missing semantics. Nonzero exits and incomplete report
sets prevent qualification. A duplicate full run is rejected, rather than silently
counting just the first 134 assertions. Raw reports are never overwritten.

## Remaining limitations

This is a bounded bootstrap runtime, not a qualified long-lived deployment.
The vector arena currently retains allocated vectors until process exit; a
tracing collector and cycle/retained-root stress checks are still required.
The CLI REPL, standard-library boot, standalone compiler, and slice builder
remain work in progress. Numeric/Unicode edge cases and primitive arity/type
coverage are not fully qualified. The optional effect-search experiment has
not been started.
