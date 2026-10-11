# Research for the Shen Koka port

Checked 2026-10-11. Source-backed observations below distinguish existing
behavior from proposed implementation. See `research/source-inventory.json` for
the observed local revisions, remote heads, dirty state, and module hashes.

## What the effect sketch establishes

Koka supports control operations with multiple resumptions. Its documented
`choice-all` resumes with each Boolean and wraps normal returns in a singleton
list. Inner state handlers produce state local to each resumption; outer state
handlers can share state across strands. This makes handler placement part of
the program's semantics. [Koka tour](https://koka-lang.github.io/koka/doc/book.html#sec-multi-resume)

Koka's pinned handler samples provide executable source for choice, failure,
and state. Use the actual compiler syntax rather than treating the supplied
sketch as tested Koka. [Handler samples at v3.2.8](https://github.com/koka-lang/koka/blob/v3.2.8/samples/handlers/basic.kk)

The inspected release candidate is v3.2.8, whose annotated tag resolves to
commit `68ad565235a9a238010e039e51b43fe592f4fd1e`. No `koka` command was found
on the initial session PATH. The dependency flake subsequently selected Koka
3.2.3 from the shared Bifrost/Yggdrasil/Shen-Go Nixpkgs lock. The researched
3.2.8 examples need compile checking against that development compiler.

## Corrections required before prototyping

### Choice must control the branch

In the supplied `member`, `choice()` is executed and ignored. Every nonmatching
prefix duplicates the same suffix search. For `[1,2,3,4,3]`, matching 3 first
occurs after two such points, so the mathematical sketch collects four `True`
values, not two. It never enumerates the later match. This is a derivation from
the sketch, not a compiler run.

A pure nondeterministic selector should choose between taking the head and
searching the tail, aborting on the empty list. A membership enumerator checks
the selected element and aborts on mismatch. Searching `[1,2,3,4,3]` then has
two successes because the two occurrences are distinct branches. A deterministic
membership predicate and a first-match walker have different contracts.

The supplied `walk` also ignores choice, so it duplicates suffix results. Its
Shen predicate-success behavior is better investigated first through the existing
kernel's pattern compiler and guard semantics.

### Three different meanings of failure

The inspected S42 source says `(defun fail () shen.fail!)` in `sys.kl`. Ordinary
Shen failure is therefore a sentinel value at this boundary. It is not equivalent
to a host operation that aborts without resuming. [Pinned Shen-Lua sys.kl](https://github.com/pyrex41/shen-lua/blob/614cd0754a741c8070c467b2b07f07943d17f4ff/klambda/sys.kl)

Prolog helpers use `false` to reject a branch, frozen continuations to continue
search, vector writes to bind/unwind variables, and lock/depth state for cut.
`shen.bind!`, `shen.unwind`, `shen.gc`, and `shen.cut` are concrete compatibility
boundaries. [Pinned Prolog kernel](https://github.com/pyrex41/shen-lua/blob/614cd0754a741c8070c467b2b07f07943d17f4ff/klambda/prolog.kl)

An experimental no-resume operation should be named `search-abort` or equivalent,
distinct from Shen `fail`. The sketch's `fun fail() ... fail()` also risks recursive
self-call/operation-name ambiguity and omits the failure effect from its callers'
signatures. Compile-check the chosen declaration and handlers in P1.

Boolean choice alone cannot signal an empty result under `choice-all`: that
handler resumes both values. Suppressing one branch still leaves the other;
pruning a search leaf needs an explicit abort/empty-result convention.

### State restoration is selective

Placing a state handler inside choice gives a useful branch-state model. It does
not automatically make references, aliased mutable vectors, global bindings, file
writes, or foreign state transactional. The manual reset in the sketch restores
one binding; it is not a deep copy and does not specify exception cleanup.

The substitution trail must be independent of ordinary Shen mutable globals.
Inference counters and limits must follow the pinned kernel's observed behavior.
Branch-local variable allocation needs recovery as well as binding recovery.
All-solutions results must snapshot substitutions before a subsequent branch
changes them.

### Cut needs invocation scope

Discarding all remaining resumptions implements a particular committed search,
not necessarily Shen cut. The inspected `shen.cut` evaluates its continuation
and interacts with locks if that continuation returns false. Preserve the exact
predicate/caller boundary and nested query behavior before replacing it.

### Freeze is repeatable computation

`freeze` can be represented by a closure taking no arguments; `thaw` invokes it.
It does not require a new suspension effect and must not silently become memoized
laziness. [Shen generic functions](https://shenlanguage.org/SD/Generic.html)

Koka's cleanup primitives also cover abandoned resumptions. Stored raw control
contexts require explicit lifetime/finalization management; avoid them in the
first DFS prototype. [Pinned handler runtime](https://github.com/koka-lang/koka/blob/v3.2.8/lib/std/core/hnd.kk)

## Current comparison repositories

The remote heads were read through GitHub's API, independently of local tracking
branches. The observed local versions are not a claim of current reference
qualification. Shen-Lua has tracked local edits and both runtime checkouts are
behind their live remote heads. Preserve them and build clean pinned worktrees.

| Repository | Read path | Integration finding |
|---|---|---|
| Bifrost | `adapters.json`, `adapters.go`, `runmatrix.go`, `matrix.go`, `shake.go` | Runtime order is hardcoded; suite manifests and JSON case output exist; target mapping must include Koka |
| Yggdrasil | `builders.json`, `yggdrasil.shen`, port contract and lowering docs | Data-driven builders, synthetic initializer, phase-aware native metadata, KL tracing |
| Shen-Lua | `compiler.lua`, `boot.lua`, `klambda/PROVENANCE.md`, primitive and Prolog tests | Refreshed S42 load-time boot, native compiler, aliases/errors/freeze reference cases |
| Shen-Go | `kl/types.go`, `codegen/codegen.go`, `cmd/yggdrasil-build`, flake | Float64 boxed numbers, compiled runtime, tail-call lowering, pinned Go toolchain |

The 19 local Lua/Go `.kl` modules are byte-identical. Every one of Yggdrasil's
15 `.kl` modules matches its namesake in those ports. Yet Yggdrasil's source
comments still refer to S41.2 in places; compare actual bytes and boot logic
rather than trusting prose version labels. Its `synthesize-initialise` wraps
kept load-time forms so the builder contract continues to work.

Bifrost's `--json` prints a JSON object followed by a human matrix. The object
contains `available`, `skipped`, and per-case `verdict`, `detail`, and per-port
`status`/`norm`. A parser must decode the leading object and tolerate the trailing
matrix, while rejecting malformed evidence. `skipNote` can return verdict PASS
with every per-port status SKIP; matrix exit zero alone is insufficient.
[Pinned matrix implementation](https://github.com/pyrex41/bifrost/blob/65236412511ace29934163cc21a418de4223b234/runmatrix.go)

Yggdrasil's port contract distinguishes existing consumers from proposed facts.
`port_reads: unknown` blocks verified initializer pruning. Native overrides need
their actual installation phase and drift checks. New Koka declarations must
derive from Koka source, not inherit the Go list. [Port contract](https://github.com/pyrex41/yggdrasil/blob/a40d8c5b6ed1eb2b5d7a4511e61d0304ce9a2e3d/docs/port-contract.md)

## Backpressure boundary

The proposed comparison system is semantic feedback between implementation steps:
fresh candidate binaries must meet required reference/golden cells before an
optimization or release advances. It is separate from runtime queue flow control.

The sibling Shen-Backpressure project already has configurable command gates,
sampled spec-equivalence, and discharge reports. It can eventually run the
comparison command as a gate. Koka guard generation is not established there;
do not assume `sb gen` supports Koka or label sampled cross-port results a proof
for all programs. [Shen-Backpressure](https://github.com/pyrex41/shen-backpressure)

## Remaining research probes

- Build the exact Koka pin through Nix on the initial two platforms; test effect
  syntax, closure representation, foreign calls, runtime rooting, and tail behavior.
- Compare numeric, Unicode, mutable alias, cyclic heap, and function-redefinition
  behavior on clean runtime revisions, with canonical/native modes identified.
- Determine cut scope, exception unwinding, inference accounting, and variable
  reclamation through exact ordered traces of small Prolog programs.
- Verify generated artifacts' dependency/redistribution requirements and runtime
  provenance; inspect optimized C only after a stable compiler pipeline exists.
- Confirm every Yggdrasil field/command against its checkout at integration time.
  A static contract declaration is not behavior evidence.

## Primary sources

Alongside the pinned links above:

- [Koka types](https://github.com/koka-lang/koka/blob/v3.2.8/lib/std/core/types.kk)
  and [float64 library](https://github.com/koka-lang/koka/blob/v3.2.8/lib/std/num/float64.kk).
- [Shen porting guide](https://github.com/Shen-Language/shen-sources/blob/master/doc/porting.md).
  Treat its version-specific assumptions as historical until checked against S42.
- [Shen S series](https://www.shenlanguage.org/S-series.html): kernel-owned partial
  application and reclaimed Prolog binding-vector space motivate preserving the
  selected kernel as the baseline.
- [Bifrost](https://github.com/pyrex41/bifrost),
  [Yggdrasil](https://github.com/pyrex41/yggdrasil),
  [Shen-Lua](https://github.com/pyrex41/shen-lua), and
  [Shen-Go](https://github.com/pyrex41/shen-go).
