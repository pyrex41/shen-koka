# Shen on Koka

Experimental Shen port using Koka, with
Bifrost comparison gates and Yggdrasil standalone artifacts.

Status on 2026-10-11: experimental Koka KLambda interpreter and pinned S42
kernel boot implemented. Full-port qualification is pending. The adapter-enabled interpreter passes all
134 canonical and eight extension assertions; the direct compiler passes 43
focused cases and one actual Yggdrasil standalone hello case.
See [implementation progress](docs/implementation-status.md) and `evidence/`
for executed results, limitations, and reproduction commands.

- [Full port plan](PLAN.md): architecture choices, semantics, phases, and exit gates.
- [Research](docs/research.md): checked sources, corrections to the effect sketch,
  and current repository integration points.
- [Comparison backpressure](comparison/README.md): required full Shen suite,
  pinned inventory, additional seed suite, and strict seed report checker.
- [Source inventory](research/source-inventory.json): observed checkout and remote
  identities, kernel hashes, and toolchain candidate.

The implemented starting point is a KLambda runtime executing the pinned Shen
kernel. Native Koka compilation and effect-based search follow behind comparison
gates. This retains Shen's compiler, typechecker, Prolog, YACC, packages, and
dynamic evaluation while those gates are established.

## Dependencies through Nix

```sh
nix develop                         # Koka and native build tools
nix develop .#comparison             # also Go 1.27 and LuaJIT
nix develop --command koka --version
nix build .#toolchain                # composable port tools
nix build .#shen-koka                # experimental runtime package
```

The lock uses the same Nixpkgs revision as Bifrost, Yggdrasil, and Shen-Go,
providing Koka 3.2.3, its C runtime/compiler, CMake, Make, Git, Python, jq, and
ripgrep. The comparison shell sets `GOTOOLCHAIN=local`. When composing
`#comparison-toolchain` directly with `nix shell`, set that variable explicitly.
Reference runtime sources and Bifrost/Yggdrasil binaries remain separate checkouts.

Supported flake systems are aarch64 Darwin, aarch64 Linux, and x86_64 Linux.
Koka 3.2.8 remains a researched upgrade candidate; the selected development
compiler is 3.2.3. `.envrc` supports opt-in direnv activation.

Validation: flake outputs evaluated for all three systems; the native toolchain
built and compiled/ran a Koka program on aarch64 Darwin. The pinned Linux development and comparison shells now build and execute
the runtime; current port qualification is recorded separately in `evidence/`. The comparison report checker passed nine constructed controls.

The flake and lock are tracked in Git so the commands above can see them through
Nix's Git source filtering.

## Build and run

```sh
nix develop --command bash scripts/build.sh
bin/shen-koka eval -e '(+ 1 2)'
bin/shen-koka script program.shen
bin/shen-koka repl
nix develop --command python3 scripts/test-runtime.py
nix develop --command python3 scripts/test-primitives.py
nix develop --command python3 scripts/test-cli.py
nix develop --command python3 scripts/run-shen-suite.py \
  --output artifacts/suite-001 --timeout 1800 --ppm-compat
```

The optional `--ppm-compat` test lane enables the documented community pattern
matching adapter for both the canonical and extension lanes. Default boot uses the unchanged pinned
kernel. A full-suite timeout is UNKNOWN for every unreached assertion, not a pass.

`bin/shen-koka build-slice MANIFEST OUTPUT` builds an interpreter-backed native
Yggdrasil artifact. It executes the manifest's synthesized initializer exactly
once. Its interpreter-backed path supports eval-capable manifests (the isolated
metaevaluation fixture passes); add `--native` for experimental direct
KL-to-Koka callbacks, which still refuse eval-capable manifests. The Yggdrasil integration exposes these as `koka` and
`koka-native`; both initializer/order fixtures pass. Full compiled-kernel
qualification is still pending; see [native compiler status](docs/native-compiler.md).

See [CLI behavior](docs/cli.md) for ordered eval actions, script arguments,
quiet loading, and the separate KLambda diagnostic format.
