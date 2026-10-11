# Implementation progress

Work branch: `implement/native-compiler`; the complete interpreter checkpoint
also remains on `implement/klambda-runtime`. Initial base: `c2bcf31`.
No AGENTS.md exists at that base. Reference worktrees were created detached at
all four revisions in `research/source-inventory.json`; existing checkouts were
not reset or cleaned.

## Implemented

- Koka-owned boxed KLambda values, minimal KL reader, lexical closures, separate
  globals/function bindings, dynamic function dispatch, and explicit machine frames.
- Non-strict forms, repeatable freeze/thaw, catchable errors, byte streams, and
  mutable vector handles with shared identity.
- Predecoded executable terms, structural vector equality (including cycles),
  closure identity, partial application and overapplication.
- Vector lookup trie and machine-safe-point tracing collection; focused cyclic
  garbage and retained-root checks pass (see [memory model](memory.md)).
- Kernel-backed REPL with clean EOF, multiline input and error recovery.
- Full S42 load-time boot using unchanged pinned modules; Shen source evaluation
  and script loading through the original reader/compiler.
- Full-distribution runner with fixed 134 + 8 denominators, group reports,
  preserved stdout/stderr, source assertion identities, and previous-PASS checks.

## Published

The runtime checkpoint is published at `5197c2967b6a2d4341a0650e1758109003713975`
on `pyrex41/shen-koka:implement/klambda-runtime`. GitHub API publication preserves
the exact local tree; local commit SHAs differ because the API creates commits.
Command-line Git push lacked credentials in this environment.

Bifrost integration: `pyrex41/bifrost:integrate/shen-koka`,
`5aa7a36c835a2132b45966eb6e80ea5763868cf8`.
Yggdrasil integration: `pyrex41/yggdrasil:integrate/shen-koka`,
`0c8023875439bea3c3dafcb001c7b6aed7769f95`.
Both integration repositories passed their Go tests. They remain experimental.

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
The vector collector has focused cycle/retained-root coverage, but long-lived
RSS and embedding-root qualification remain required. The pinned standard-library installer has completed successfully (035);
individual library operations are not comprehensively qualified. the direct standalone compiler remains incomplete. An interpreter-backed slice builder now builds a native hello
artifact from the actual Yggdrasil manifest and runs it without the full kernel.
It is not the planned direct KL-to-Koka compiler. Eval-capable slices are refused
with exit code 3. Broader standalone parity remains pending. Numeric/Unicode edge cases and primitive arity/type
coverage are not fully qualified. The optional effect-search experiment has
not been started.

## Comparison findings

The Koka candidate passed all 17 seed goldens. The three-port gate remains FAIL:
Lua/Go print `(fail)` as `...`; Go renders an empty raw vector slot as `#<raw >`.
Those failures are retained. Explicit value probes in `evidence/020-sentinel-values`
show Lua agrees that an empty slot is the fail sentinel, while pinned Go does not.
Both references agree that `(fail)` equals the interned sentinel.

Both pinned references fail the first bundled community PPM assertion and abort
before the other seven. The S42 compiler lacks the hooks expected by that
extension. The opt-in adapter in `compat/` passed all eight unchanged extension
assertions in a focused run. Through attempt 031, the canonical lane ran without the adapter while the
extension lane enabled it. Attempt 037 uses one adapter-enabled configuration
for both lanes; future `--ppm-compat` runs follow that policy.
The pristine default kernel is still available with the adapter disabled.

Builds use Koka `-j1`: parallel compilation twice left an empty object and failed
to link. This is an observed toolchain/environment failure, not a diagnosis of
its upstream cause. Builds publish an executable only after successful linking,
and full-suite runs reject a binary whose recorded source hashes are stale.

## Current checkpoint

The completed predecoded attempt (017) records 100/134 canonical PASS, zero
observed FAIL, 34 UNKNOWN, and 8/8 extension PASS. It is not a full-port pass.
Later immutable-snapshot attempts exercise structural equality, collection,
handler placement and the REPL build. Their final reports, when present, take
precedence over these interim counts. Cancelled attempt 023 records 16 PASS and
118 UNKNOWN, with all eight extensions UNKNOWN; its regression list is retained.

All 23 focused checks passed after collection (028) and after handler changes
(030). The REPL's EOF, expression, multiline and recovery probes passed (032).
Neither these probes nor the seed suite replaces the 142-assertion gate.

Runs started before immutable snapshots may span a rebuild between lanes. Such
runs retain raw evidence but cannot establish a single-build combined result.
New runs freeze the native payload and boot inputs, enforce stream-size limits,
and support cancellation by creating `CANCEL` inside their output directory.

Attempt 031 completed all 134 canonical assertions and all eight extensions,
with all 35 canonical counter reports consistent and no regressions. It uses
the two explicitly recorded profiles described above. Attempt 037 checks the
new boundary fixes with the adapter enabled consistently in both lanes. The
latest focused set has 25 PASS (038), and the current standalone hello artifact
also runs without a kernel installation (034).

## Coherent kernel-compatibility result

Attempt 037 completed with **134/134 canonical PASS and 8/8 extension PASS**,
zero FAIL, zero UNKNOWN, all 35 canonical reports consistent, and no regressions
against the earlier 102-pass baseline. The same immutable native payload and
adapter-enabled boot configuration were used for both lanes. Binary SHA-256:
`13d0a4dd3b9553f418f0c1077a14280211ac9079133c60e32c3da90e490b2d6b`.

This establishes the full pinned suite for that configuration. It does not
qualify the planned direct compiler, other platforms, long-running memory
budgets, all standard-library operations, or the broader release matrix. Direct
KL-to-Koka lowering is the next implementation stage; the optional search
experiment remains deferred.

## Stream lifetime checkpoint

Attempt 057 passes all 134 canonical and eight extension assertions with the
adapter enabled in both lanes, all 35 reports captured and no regressions from
052. Attempt 054 demonstrated that a closed stream handle could alias a newly
opened file. Generation-tagged stream slots now reject stale reads, writes and
closes without affecting the new owner. Both interpreter (056) and directly
compiled (058) focused sets pass 29 cases. The optional native hello build still
has no qualified result; attempts 051 and 055 timed out and remain recorded.

Attempt 060 records numeric/Unicode discrepancies between pinned references.
Attempt 061 identifies rounding errors in Koka's index and character conversions;
those are outstanding at this checkpoint, not covered by the complete suite.
