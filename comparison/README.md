# Comparison backpressure

The seed suite covers 17 observations, including the failure sentinel, non-strict
control, exceptions, closures, repeated thaw, aliased vectors, evaluation order,
and a first Prolog solution. Goldens are intended semantic assertions; Koka passed all 17 in the initial integrated run. The pinned reference
ports have retained golden mismatches; see `evidence/011-bifrost-seed`. The larger fault and generation
campaign is specified in [the plan](../PLAN.md).

The primary language backpressure gate is the **full Shen test distribution**:
134 canonical assertions in 35 report groups and eight bundled extension
assertions. [The pinned inventory](shen-suite.lock.json) records every test-tree
file and its hash. The seed suite is an additional comparison lane.

`scripts/run-shen-suite.py` is the full-suite driver. Candidate iterations attempt
the entire suite before and after feature changes. Expected early failures stay
FAIL, unreachable assertions stay UNKNOWN, and the denominators remain fixed.
Feature checkpoints can advance with the overall suite red when their declared
assertions pass and previously passing assertions do not regress. P3 and full
port completion require both entire lanes green. See the plan's full-suite
development policy for continuation prompts, per-assertion evidence, and the
end-of-suite counter reset. The seed checker does not validate full-suite reports.

`scripts/check-comparison.py` checks the leading JSON object emitted by the
inspected Bifrost CLI. It requires the exact suite case set, each required
implementation, PASS for every required cell, and its exact normalized golden.
Known divergence is FAIL. Missing ports, SKIP cells, malformed output, and
incomplete cases are UNKNOWN. Both FAIL and UNKNOWN exit nonzero.

This checker validates reported observations. It does not establish clean source,
binary provenance, file/heap trace equivalence, or the correctness of Bifrost's
normalization. Those remain separate provenance and state-trace obligations. Its default requires Koka, so a run
against only existing ports cannot qualify the new port.

## Reference lane

Use clean worktrees at the source identities chosen for P0; preserve the existing
dirty siblings. Build launchers in their pinned Nix environments and record their
binary hashes. Explicit environment overrides prevent accidental PATH fallback.

The following commands are recipes after those prerequisites, not executed results.
Run from the Shen-Koka checkout with a Bifrost binary built from the recorded SHA:

```sh
mkdir -p artifacts/reference
export BIFROST_SHEN_LUA=/absolute/clean/shen-lua/bin/shen
export BIFROST_SHEN_GO=/absolute/clean/shen-go/.bin/shen-go
/absolute/clean/bifrost/.bin/bifrost \
  --suite comparison/bifrost.suite.json --impls shen-lua,shen-go --json \
  > artifacts/reference/bifrost.stdout 2> artifacts/reference/bifrost.stderr
python3 scripts/check-comparison.py \
  --input artifacts/reference/bifrost.stdout --required shen-lua,shen-go
```

Record and require both exit codes; checker success never overrides a failed
Bifrost process. Process-group timeout and bounded logging belong in the gate
runner specified in P0. The reference lane establishes the seed reference
behavior, not Shen-Koka compatibility.

## Candidate lane

Use Bifrost branch `integrate/shen-koka` with the built Shen-Koka launcher.
Attempts 033 and 071 passed all 17 Koka seed cells and the strict checker:

```sh
mkdir -p artifacts/candidate
export BIFROST_SHEN_KOKA=/absolute/clean/shen-koka/bin/shen-koka
/absolute/clean/bifrost/.bin/bifrost \
  --suite comparison/bifrost.suite.json --impls shen-lua,shen-go,shen-koka --json \
  > artifacts/candidate/bifrost.stdout 2> artifacts/candidate/bifrost.stderr
python3 scripts/check-comparison.py --input artifacts/candidate/bifrost.stdout
```

Run the existing Bifrost corpus as an additional lane. The seed checker is
deliberately bound to this suite; it does not qualify a different corpus report.

## Deployment lane

Yggdrasil branch `integrate/shen-koka` registers `koka` (interpreter-backed) and
`koka-native` (direct callbacks). Set `YGGDRASIL_SHEN_KOKA_DIR` to this checkout.
Attempt 101 executes the registered native target's hello build and runs its
artifact in isolation. Attempts 092/100 verify initializer-once and user-file
order for both builders. Eval-capable manifests are still explicitly refused.
Use Bifrost `--shake` on a separate script-only suite. Do not feed this mixed eval/script
seed report to a deploy gate and assume the eval rows were standalone artifacts.
Compare Go/Lua/Koka artifacts and their full runtime legs with matching inputs.
Run Yggdrasil trace checks with complete end records and canonical/lowered pairs.

## Evidence and feedback

Keep one report per source/binary identity and case. Never replace raw observations
with a hand-edited PASS. Incomplete run setup remains UNKNOWN. Mutant controls
must include a skipped cell with case verdict PASS, a missing implementation,
a truncated object, a wrong golden, and an empty case set.

The checker passed the constructed [scaffold controls](../research/scaffold-validation.json)
and actual 17-case Koka reports (033/071/108). Full interpreter attempts 085/091/099 pass
134 canonical and eight extension assertions using the explicit PPM compatibility
profile in both lanes. The three-reference seed result remains FAIL; sentinel
printing and empty-vector-slot discrepancies are retained. Native full-kernel
attempts remain UNKNOWN until a complete executable and all assertions are observed.

Future feedback records include the first failing scenario, raw output paths,
minimized source, exact reproduction argv, and which gate blocked promotion.
Use a dedicated scenario runner for state/IO traces and resource measurements,
then let Shen-Backpressure's configurable command gates consume its exit status
if that integration is selected. No Koka guard emitter is assumed.


The heavy stage-1 lane passes across pinned Go/Lua and Koka (136), using
Bifrost's `-heavy-timeout 15m` and Yggdrasil's new script host mode for Koka.
The default five-minute budget remains unchanged. Direct comparison 132 verifies
that kernel and both manifests match byte for byte; 129 retains the earlier
empty-file failure under the quiet host invocation. Koka's updated Bifrost
integration still passes the strict 17-case seed gate (137). The separate light
corpus remains 64 PASS / 1 FAIL / 1 DIVERGE out of 66 (120).
