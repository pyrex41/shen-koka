# Dynamic standalone deployment

`program.shen` exercises runtime eval, definition/redefinition, string reading,
typechecked dynamic definition and file loading. It writes its own load fixture
in the working directory. Load chatter goes to an explicit file stream, then
standard output is restored; `expected` is the six-line observable result.
`program.kl` retains the reference-generated KL bytes used by passing attempt 140.

Build with the Yggdrasil integration and the Koka development shell:

```sh
export YGGDRASIL_SHEN_KOKA_DIR=/absolute/shen-koka
yggdrasil build comparison/slices/dynamic/program.shen artifacts/dynamic \
  --target koka --host /absolute/reference-shen-go
```

Run `artifacts/dynamic/koka-artifact/run` from an empty temporary directory with
`SHEN_KOKA_ROOT=/nonexistent-kernel`. The artifact embeds only manifest sources
and calls the synthesized initializer once. The direct native slice variant
continues to reject `needs-eval=true`; this fixture qualifies the interpreter-backed
standalone path. Evidence 139 preserves the earlier failed assumption that Go's
loader chatter would obey `*hush*`; no log normalization converts that to a pass.
