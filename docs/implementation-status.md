# Implementation status

The Koka-owned interpreter boots the unchanged pinned S42 kernel and passes
**134/134 canonical assertions plus 8/8 bundled extension assertions** in the
documented adapter-enabled configuration. This is a kernel compatibility result,
not full-port release qualification.

## Implemented and tested

| Capability | Evidence | Qualification boundary |
|---|---|---|
| KLambda values, lexical closures, currying, redefinition, explicit tail-call machine | 098: 43 focused PASS | Includes million-step self, mutual and indirect calls |
| Full kernel compiler, typechecker, Prolog, YACC, macros, packages and dynamic evaluation | 131: 134 + 8 PASS | All 35 canonical reports captured; no UNKNOWN or regressions |
| Primitive inventory, positive observations and wrong arities | 098: 68 PASS | Supplemental gate, including NUL/255 byte IO; not the primary denominator |
| Vector aliases, cycles, structural equality and tracing collection | Focused checks and full suite | Long-running memory budgets remain unqualified |
| Generation-tagged streams | 054 failure; 056/058/057 after repair | Closed handles cannot alias a new stream |
| Numeric conversions | 061/081 failures; 083/085 after repair | String positions/vector sizes truncate; vector indices and character codes reject fractions |
| CLI strings, sentinel, ordered eval flags, script arguments and quiet loading | 116: 10 PASS | Original kernel reader/compiler and script launcher retained |
| Kernel-backed REPL | 032: four probes PASS | EOF, expression, multiline input and recovery |
| Standard library | 035: installer completed | Individual library operations are not all qualified |
| Bifrost launcher | 119: 17 required Koka cells PASS | Strict checker PASS; three-reference discrepancies remain |
| Direct KL-to-Koka callbacks | 096: 43 compiled checks PASS | Full compiled-kernel suite pending |
| Yggdrasil standalone hello | 034 interpreter-backed; 101 registered native target PASS | Both run without installed kernel; broader deployment matrix pending |
| Nix runtime package | 126/127: current CLI package, ten CLI checks and 134 + 8 PASS | x86_64 Linux with pinned Nix dependencies |

The full-suite result uses `SHEN_KOKA_PPM_COMPAT=1` in both lanes. Default boot
remains pristine; the separate `compat/` adapter supplies the community pattern
hooks absent from S42. No vendored kernel module was edited. The full runtime
uses original load-time forms; standalone slices use the synthesized manifest
initializer. Ordinary `(fail)` remains the `shen.fail!` value, distinct from errors.

Attempt 127 runs the current immutable Nix-store launcher; 126 verifies its installed source and binary hashes and all ten CLI cases. Attempt 131 retests the
current CLI and runtime and preserves both raw streams
and all cumulative counters before reset, and verifies the exact 63-file inventory
and assertion identities. Its runner source and raw-log hashes were verified. Attempt 084 records the
installed binary hash and validates it against the installed build manifest.

## Published

The complete interpreter checkpoint remains on `implement/klambda-runtime` at
`5197c2967b6a2d4341a0650e1758109003713975`. Current compiler development and
its evidence are published on `implement/native-compiler`. The immutable
packaged-runtime checkpoint `21c243b9221f63b8a10fed02a428246cead0e333` precedes
the cache and smaller-module work described below; source/binary hashes in
each evidence directory identify exactly what was tested.

Integration branches:

- `pyrex41/bifrost:integrate/shen-koka`, commit `5aa7a36c835a2132b45966eb6e80ea5763868cf8`.
- `pyrex41/yggdrasil:integrate/shen-koka`, commit `aa60af61f410b92cec485b50865c3d5b20d8a28b`.

Both integrations passed `go test ./...`. GitHub API publication preserves the
exact local Git tree; commit SHAs differ because the API creates the commits.
Command-line push lacked credentials. Initial base was `c2bcf31`; no AGENTS.md
existed there. Detached pinned reference worktrees were used without resetting
or cleaning the original checkouts.

## Open gates

- Full compiled-kernel build and its unchanged 142-assertion suite. Attempt 067
  records the missing-artifact baseline as all UNKNOWN. Focused native checks
  cannot promote this gate.
- General full-versus-sliced-versus-lowered deployment, complete trace comparisons, and larger standalone programs. Initializer/order
  fixtures pass both execution modes (092/100); the registered direct-native
  Yggdrasil target passes its actual hello build and isolated run (101). The default builder remains interpreter-backed;
  direct lowering uses explicit `--native`.
- Interpreter-backed eval-capable slices pass the isolated metaevaluation fixture (130),
  including runtime definition and string evaluation. Broader dynamic deployment
  comparisons remain open; directly compiled eval-capable slices are still refused.
- Additional platform lanes, full primitive edge
  profiles, long-running memory and performance distributions, and release gates.
- The optional effect-search experiment is deferred; kernel Prolog stays intact.

The three-reference seed gate remains FAIL: Lua/Go print the fail sentinel
differently, and Go's empty raw-vector slot differs as a value. Attempts 020 and
060 retain explicit value and numeric/Unicode probes. Lua uses byte-oriented
string operations where Koka and Go use codepoints for the tested reads. Do not
normalize these discrepancies into agreement or infer missing tests passed.

## Reproduce

```sh
nix develop --command bash scripts/build.sh
nix develop --command python3 scripts/test-runtime.py
nix develop --command python3 scripts/test-primitives.py
nix develop --command python3 scripts/run-shen-suite.py \
  --ppm-compat --timeout 1800 --output artifacts/suite-check \
  --previous evidence/085-nix-vector-bound-full/report.json
nix develop --command python3 scripts/test-native.py --output artifacts/native-check
nix develop --command bin/shen-koka build-slice --native MANIFEST OUTPUT
```

See [native compiler](native-compiler.md), [memory model](memory.md), and
[comparison instructions](../comparison/README.md) for the separate gates.

The first monolithic compiled-kernel build was killed by signal 9 (073). Its
post-build suite is all UNKNOWN (074). Batched library compilation reached a
real conditional `Nil` type-inference error (078), with all assertions UNKNOWN
in 079. Explicit value annotations repair that error; introduced boolean
constants also ignore lexical shadowing. All 43 compiled checks pass (086).
Attempt 087 passed that conditional, then hit the next module's five-minute
compiler limit. Attempt 090 remains 134 + 8 UNKNOWN. Earlier callback splitting
and a measured cache workaround pass 43 native cases (096); the next full
compiled-kernel build is in progress and is not yet qualified.


The broader built-in Bifrost light corpus is separately qualified: 110 records
57 PASS / 9 FAIL out of 66; 120 records 64 PASS / 1 FAIL / 1 DIVERGE. The remaining
file-write mismatch is the unchanged S42 `pr` suppression under `*hush*` (121).
The load-echo row changed only for Lua; isolated cold/warm runs reproduce that
reference cache difference (122). Neither difference is normalized away. The
single heavy stage-1 case is UNKNOWN. These outcomes block full cross-port
qualification despite the complete primary Shen suite passing.
