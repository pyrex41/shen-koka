# Shen 42.2 ecosystem implementation

The active implementation objective supersedes the S42 baseline in PLAN.md:
qualify CL, Go, Lua, Rust, Erl, ShenScript, Scheme, Julia, Swift, Truffle, C,
Koka, Forth and LLVM against community ShenOSKernel 42.2. Joy remains a bounded
image target. Alternate checkouts are not additional runtimes.

## Fixed contract

Use the pristine release archive and source identity in the new source lock.
Every full runtime needs 143 canonical assertions in 37 reports plus 123 extension
assertions. Preserve historical S42 reports and their 134+8 inventory unchanged.
Full-suite success is only one qualification gate.

Strings segment UTF-8 into Unicode scalar values and individual invalid byte
units, preserving bytes and equality-compatible hashing. Source loading must not
reinterpret UTF-8 as Latin-1. Byte IO stays raw. Follow upstream pr hush behavior.
Declare numeric profiles. Boot definitions before exactly one shen.initialise,
initialize features/pattern matching and community stlib.initialise. Namespaces
and type annotations remain explicit extensions.

## Execution sequence

1. Snapshot default branches in isolated worktrees, run complete before-change
   suites, migrate Koka/Forth and repair all concrete cohort failures. Complete
   LLVM using existing ORC/function cells, with Boehm default and ownership work
   preserved separately. Export independent pinned toolchains.
2. Bifrost: require-all, structured report, exact capability/numeric declarations,
   distinct target/mode evidence and integrity controls. Yggdrasil: Koka/Forth/LLVM
   builders, isolated artifacts, initializer/order contracts, full stage-1 host
   matrix, dependency notices, dynamic function cells and woven traces.
3. Full/shaken/optimized deployment corpus; actual execution on x86_64 Linux,
   aarch64 Darwin and aarch64 Linux. Missing workers stay UNKNOWN. LLVM 21 with
   Darwin support. Resume inputs bind compilers, ABI, platform, flags and hashes;
   final validation/link always run.
4. Cold/warm paired measurements and two-hour bounded resource workloads per
   runtime/mode. Accept optimization only at >=10% target median improvement,
   paired 95% CI excluding zero, <=5% regression elsewhere, no gate regression.
   Bound cold builds to two hours and compilation steps to five minutes.
5. Opt-in Koka effect-search prototype with scoped cut, branch substitutions,
   ordered solutions and independent finite-search oracle. Canonical Prolog stays
   default unless full 266 assertions and measured acceptance rule pass.
6. Scoped repair PRs, refreshed merge gates, validated SHA pins, cohort lock,
   installed-package rebuilds and qualified Koka 0.1.0-42.2.1 release.

Acadia, Datum and Shen-Backpressure supply downstream regression gates. Source,
language, shared semantics, harness integrity, deployment, platforms and resource
qualification all require complete evidence. CI/merge status remains separate.

## Current evidence boundary

Branch codex/shen42-ecosystem starts at Koka 2e42917. The release archive hash and
source tag were verified live. The distribution is preserved unchanged locally and is populated in fresh
checkouts by scripts/fetch-shen42.py, with archive and complete file verification.
New locks inventory exactly 143+123 assertions; nested extension assertions are
included in source order. The inventory reproduces all 142 historical assertion
identities unchanged. Runner controls cover both denominators, report counters,
duplicates, truncated output, spoofed skips and visible failures. Raw logs remain
byte files. Suite identity is explicitly distinct from unverified runtime identity.

Validation: `python3 scripts/test-suite-inventory.py` (4 tests),
`python3 scripts/test-suite-runner.py` (13 tests), and `git diff --check`.
The missing-build control emits nonzero and 143+123 UNKNOWN, never PASS.
No cohort, runtime migration, deployment, platform or resource gate is complete.

Fetch the pristine distribution with `python3 scripts/fetch-shen42.py`, then
run the source-bound suite with:

```sh
python3 scripts/run-shen-suite.py \
  --suite-lock comparison/shen42.2-suite.lock.json \
  --assertions comparison/shen42.2-assertions.json \
  --source-lock comparison/shen42.2-source.lock.json \
  --distribution vendor/ShenOSKernel-42.2 \
  --output /tmp/shen42-candidate-report
```

The Koka default launcher currently needs an actual build; the runtime still boots
S42. Passing an external launcher requires --launcher and its actual argv syntax
through --script-command. This runner does not establish that launcher's runtime
kernel identity, installed-package identity, ABI or platform qualification.

## Baseline build boundary

Shen-Go default HEAD fetched over HTTPS is 1f587de (merged #62). The preserved
original checkout remains untouched; shen-go-42-cohort is a fresh worktree on
codex/shen42-cohort-baseline. Host Go 1.25.10 is rejected by go.mod's >=1.27
requirement. The repository's Nix environment selects Go 1.27.0. No host-compiler
substitution or cached suite result is accepted as baseline execution.

Additional controls verified actual fresh extraction from the downloaded archive,
idempotent source verification, modified-source rejection, wrong-archive
rejection with no published directory, and mixed-profile comparison rejection
before execution. The commit hook rejected upstream Windows example paths; the
fetch workflow preserves those upstream bytes without changing the guard.

Shen-Go's fresh pinned build completed. Corrected attempt 02 passes canonical
143/143 (all 37 cumulative reports) and extensions 123/123, exit 0 in each lane.
Raw lane logs and a portable source/build summary are preserved under
`evidence/shen42.2-go-baseline/`. The first attempt loaded kerneltests directly,
failed with undefined report, and was retained separately; the new lock now uses
upstream runme.shen and a regression check enforces the entrypoint. These results
establish the language-suite baseline on Darwin arm64 only. Numeric, UTF-8,
StLib-profile, deployment, installation, resources and other platforms remain
unqualified. This does not qualify the complete ecosystem.
