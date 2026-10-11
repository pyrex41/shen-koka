# Shen on Koka

Research and implementation plan for a complete Shen port using Koka, with
Bifrost comparison gates and Yggdrasil standalone artifacts.

Status on 2026-10-11: planning, dependency toolchains, and comparison scaffolding.
The Shen runtime, Shen compiler, launcher, and port qualification are pending.

- [Full port plan](PLAN.md): architecture choices, semantics, phases, and exit gates.
- [Research](docs/research.md): checked sources, corrections to the effect sketch,
  and current repository integration points.
- [Comparison backpressure](comparison/README.md): required full Shen suite,
  pinned inventory, additional seed suite, and strict seed report checker.
- [Source inventory](research/source-inventory.json): observed checkout and remote
  identities, kernel hashes, and toolchain candidate.

The proposed starting point is a KLambda runtime executing the pinned Shen
kernel. Native Koka compilation and effect-based search follow behind comparison
gates. This retains Shen's compiler, typechecker, Prolog, YACC, packages, and
dynamic evaluation while those gates are established.

## Dependencies through Nix

```sh
nix develop                         # Koka and native build tools
nix develop .#comparison             # also Go 1.27 and LuaJIT
nix develop --command koka --version
nix build .#toolchain                # composable port tools, not a Shen runtime
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
built and compiled/ran a Koka program on aarch64 Darwin. Linux execution remains
pending. The comparison report checker passed nine constructed controls.

The flake and lock are tracked in Git so the commands above can see them through
Nix's Git source filtering.
