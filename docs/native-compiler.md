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

The runtime with this interface passes all 142 pinned assertions (052). Directly
compiled focused programs pass 27 cases (053), including million-step tail calls,
GC, vector aliasing, repeatable thaw, dynamic redefinition and exception recovery.
These focused programs do not replace a full native-kernel suite run.

An early generator emitted nested temporary expressions. The actual Yggdrasil
hello build exceeded its 900-second compiler budget (051). The next version emits
flat temporary bindings also exceeded that budget (055). A further iteration
removes duplicate roots and redundant live temporary bindings. Until
that succeeds and broader compiled-path gates pass, the builder defaults to the
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
