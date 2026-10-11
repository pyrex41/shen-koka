# Direct compiler development

The published all-pass interpreter checkpoint is `5197c2967b6a2d4341a0650e1758109003713975`
on `implement/klambda-runtime`. Native compiler work is isolated on
`implement/native-compiler` and is not yet standalone-qualified.

The generator emits Koka callbacks with explicit captured values. It preserves
left-to-right evaluation and dynamic function lookup. Tail calls return requests
to the shared machine, including protected calls whose handler is evaluated only
on error. Partial application and overapplication use the same dispatch boundary.
There is no host closure hidden from the Shen vector collector: registered native
roots include locals and all suspended interpreter frames across nested calls.

The runtime with this interface passes all 142 pinned assertions (085). Directly
compiled focused programs now pass 43 cases (086), including million-step tail calls,
GC, vector aliasing, repeatable thaw, dynamic redefinition and exception recovery.
These focused programs do not replace a full native-kernel suite run.

An early generator emitted nested temporary expressions. The actual Yggdrasil
hello build exceeded its 900-second compiler budget (051). The next version emits
flat temporary bindings also exceeded that budget (055). A further iteration
removes duplicate roots and redundant live temporary bindings. The reduced-root version compiled and ran the actual hello slice (062). It
remains only one standalone case. Until broader compiled-path gates pass, the builder defaults to the
interpreter-backed path; `--native` is explicitly experimental.

Koka 3.2.3 generated an invalid fall-through for an empty `Recover` match branch
in root enumeration. The recorded native crash trace and C excerpt are in 048.
Explicitly retaining its error value avoids the empty branch; all 27 compiled
focused cases and the full interpreter suite pass with this workaround.

```sh
nix develop --command python3 scripts/test-native.py --output artifacts/native-check
nix develop --command bin/shen-koka build-slice --native MANIFEST OUTPUT
nix develop --command python3 scripts/build-native-kernel.py --output artifacts/native-kernel
```

Native kernel generation preserves every pinned module's load-time form order.
Slice generation instead invokes the manifest's synthesized initializer once.
Eval-capable slices remain explicitly refused. Native kernel full-suite results,
standalone parity, build-time budgets, platform lanes and long-running memory
qualification remain open gates.

Deep expressions are split into additional callbacks, preserving ordered effects
and captured values. Argument lists are destructured once instead of repeatedly
using effectful indexing. Native builds serialize shared staging/cache access;
each artifact carries the relevant upstream notices. Attempt 068 records the
first pattern-unpacking generator's indentation failure; 070 passes all 37 cases
after correction. The earlier full-kernel build had 2,834 callbacks across 71 modules.
The current depth-six split emits 4,591 callbacks, grouped into 287 modules
by the default `--module-size 16`. Its full-suite gate is still pending; attempt 067 records the
pre-build state with all 142 assertions UNKNOWN.

```sh
python3 scripts/run-shen-suite.py --native-artifact artifacts/native-kernel-001 \
  --ppm-compat --timeout 1800 --output artifacts/native-kernel-suite
```

The native-artifact lane verifies build metadata, generator/source/compatibility
hashes, and the compiled binary, then freezes the executable and compatibility
files across both lanes. It does not fall back to the ordinary launcher when
an artifact is missing. Suite runners now retain their own source snapshots.

Monolithic full-kernel compilation ended with SIGKILL after 795 seconds (073).
The batched build reached module 23 and exposed an ambiguous unannotated `Nil`
in a value-producing conditional (078). The generator now annotates these
values explicitly. It also treats boolean constants introduced by `and`/`or`
as literals, independently of lexical names. Attempt 086 passes 43 native cases.

Full-kernel builds compile each generated module as a library in a separate
compiler process before linking. They omit debug information by default, retain
per-step resource counters, and reuse unchanged staging files on retry. The
30-minute whole-build budget is configurable with `--timeout`; each compiler
step is bounded to five minutes. Partial compilation is not a usable artifact.


### Bounded compilation and cache reuse

Attempt 087 passed the previously failing conditional module, then timed out
compiling the next module at 300 seconds. Attempt 090 retains all 134 + 8 native
assertions as UNKNOWN. Space optimization alone also timed out (093). Earlier
expression splitting passes all 43 native cases (094).

Koka 3.2.3's `src/Compile/Build.hs` assigns interfaces without inline definitions
`PhaseLinked`, but interfaces with inline definitions `PhaseIfaceLoaded`.
`validateDependencies` invalidates a module whose dependencies have a lower
phase. This caused the IO module and its callers to be recompiled on each batch.
The IO error predicate is now an inline helper; generated modules expose inline
callback-count metadata. Stream operations themselves remain out of line.
Attempt 096 passes all 43 native cases; the identical-source rebuild in 097
reparses only the entry module and completes in 21.32 seconds. This is a measured
cache workaround, not a change to the pinned Koka compiler.

Full boot iterates the generated entry IDs in original form order, avoiding one
enormous unrolled boot function. Artifacts retain builder snapshots and hashes
of every generated module and boot source; the native suite lane checks them.
The initializer-once, multi-user-file-order fixture passes in interpreter-backed
(092) and directly compiled (100) standalone artifacts, from empty working
directories. These checks supplement the complete kernel suite.


Explicit Koka library roots are reparsed even with a complete cache. Importing
batches through tiny roots reuses completed modules (112: 2.09 seconds). The first
probe had a name collision and is retained as FAIL in 111. Build 004 was
interrupted at batch 78; its old in-memory log buffers and final build record
were lost (102), and the full suite remains 134 + 8 UNKNOWN (103). No executable
or Shen assertion reports were produced by that attempt.

The builder now writes `compile.log` and `progress.json` after each batch and
checks `OUTPUT/CANCEL` once per second. Creating that file stops the compiler
process group and returns through normal metadata capture. Control 113 verifies
that output, progress, and descendant-pipe cleanup survive cancellation. Use
this file-based control instead of killing the builder process. The next build
uses importing batches and preserves all generated-source hashes.
