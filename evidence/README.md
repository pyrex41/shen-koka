# Development evidence

These are development attempts, not release qualification. Reports from dirty
sources are retained with that status. See each JSON file and both raw streams.

- 000: no launcher; all 142 assertions UNKNOWN.
- 001: Lua invoked with the wrong CLI profile; setup failure, all UNKNOWN.
- 002: Lua's own test tree; 134 canonical PASS, missing extension source.
- 003: first launcher was not executable; all UNKNOWN.
- 004: Lua with the assembled distribution; canonical ran twice and is rejected
  as an unexpected report set; first extension assertion FAIL, seven unreached.
- 005: KL-only launcher; no Shen script support, all UNKNOWN.
- 006: bootable Koka candidate; 94 canonical PASS, 6 FAIL, 34 UNKNOWN at the
  300-second timeout. First extension FAIL, seven unreached.
- 007: pinned Go reference; 134 canonical PASS; first extension FAIL, seven
  unreached. Both reference ports disagree with the extension expectations.
- 008: **invalid candidate-source pairing**: an incremental compile failed and
  left the previous executable available. Retained for diagnosis only; do not
  use it as evidence for the primitive fixes. This discovered the need for the
  build-provenance guard introduced before attempt 009.
- 009: fresh isolated build, source/binary hashes checked, 1500-second lane
  budget, compared against every assertion passed in 006.

The focused KL report is independent supplemental evidence, including three
million-step tail-call shapes. It does not replace the full distribution.

Later attempts retain their full reports and raw streams under numbered paths.
017 is the first 100 canonical / 8 extension PASS snapshot, with 34 canonical
assertions still UNKNOWN. 023 was deliberately cancelled and retains regressions
to UNKNOWN. 025 and later full runs freeze their executable and boot inputs, so
concurrent rebuilding cannot replace the extension candidate. 015 and 019 began
before this protection; treat any combined result as mixed-build evidence.

Focused runtime checks 028/030 include collection; 032 contains REPL transcripts.
The Bifrost and Yggdrasil integration branches are recorded in the implementation
status. No partial report or supplementary probe establishes full qualification.

037 is the first coherent-profile complete result: 134 canonical and eight
extension assertions PASS, all counters captured, zero UNKNOWN, no regressions.
Both lanes use the adapter and an immutable payload. 031 also passes both lanes
but records distinct adapter settings; it is retained without conflating those
configurations.

052 passes the complete 134 + 8 gate after native-call root integration.
053 passes 27 direct native cases. 054 reproduces a stale-stream alias bug.
055 retains the second native hello compiler timeout. 056 and 058 each pass
29 focused cases after generation-tagged stream handles; 057 passes the complete
gate with no regressions. 059 is a failed UTF-8-decoding probe harness; 060
retains corrected byte-preserving numeric/character observations. 061 records
conversion rounding mismatches that remain open at this checkpoint.

062 records the first successful direct native Yggdrasil hello artifact,
including an isolated execution and ELF-section sizes. 063 passes 37 interpreter
checks after conversion fixes; 064 passes all 142 primary assertions without
regressions. 065 observes native workspace locking. 066 passes 37 split-generator
checks. 067 is the missing native-kernel pre-build gate: all 142 UNKNOWN. 068
retains an indentation/compiler failure, followed by 37 compiled PASS in 070.
069 reproduces the metaprogramming scenario in isolation. 071 passes all 17
required Koka Bifrost cells and the strict checker.

072 passes 68 primitive inventory/observation/arity checks. 073 retains the
SIGKILLed monolithic native kernel build; 074 records all 142 native assertions
UNKNOWN. 075/076 qualify the first installed Nix runtime against all 142 tests.
077 passes 37 native cases without debug info. 078/079 retain the batched native
kernel's Nil inference failure and all-UNKNOWN suite. 080/082 pass 40 interpreter
and compiled conditional checks. 081 reproduces a huge vector request wrongly
returning a vector; 083 passes 43 interpreter and 68 primitive checks after its
range repair. 084/085 validate the rebuilt Nix package and all 142 assertions.
086 passes all 43 compiled checks with the same primitive repair.


087 records full native build 003 reaching its per-module timeout after fixing
Nil inference. 088/089 are invalid previous-report path invocations and contain
no assertion results; corrected attempt 090 retains all 142 native assertions
UNKNOWN. 091 repeats the installed interpreter's 134 + 8 PASS. 092 passes the
interpreter-backed initializer/order fixture. 093 shows -O1 alone also times out.
094 passes 43 depth-six native cases. 095 retains the missing next native artifact
as 134 + 8 UNKNOWN. 096 passes 43 native cases with the cache workaround; 097
proves identical-source dependency reuse. 098 passes 43 interpreter and 68
primitive checks. 100 passes the direct-native initializer/order fixture.
104 checks that an invalid previous-report path is rejected before execution.

099 passes all 134 canonical and eight extension assertions with the rebuilt
cache-helper runtime, without UNKNOWN or regressions. 101 passes the actual
Yggdrasil koka-native target build and isolated execution; publication identity
is retained. 105 confirms preserved reference heads and clean pinned worktrees.
106 is the missing native-kernel-004 baseline (134 + 8 UNKNOWN). 107 retains
Bifrost outputs without independently captured exit codes; corrected 108 passes
all 17 cells with both launcher and strict checker exiting zero.


102/103 retain interrupted native build 004 and its 134 + 8 UNKNOWN suite.
109 records exact-tree publication of the all-pass cache checkpoint. 110 runs
all 66 built-in light Bifrost cases across three pinned ports: 57 PASS / 9 FAIL;
the heavy case remains UNKNOWN. 111 retains a cache-probe naming failure; 112
proves reuse after fixing that probe. 113 checks durable cancellation and child
cleanup. 114 catches a sentinel-rendering regression in the first launcher
candidate; its exact source is retained. Its full suite passes in 115, but that
alone does not qualify the failed CLI observation. The corrected CLI passes ten
checks (116), all 134 + 8 assertions (117), and all 17 seed cells (119). 118 is the
missing native-kernel-005 baseline, all 142 UNKNOWN. 120 improves the light corpus
to 64 PASS / 1 FAIL / 1 DIVERGE. 121 isolates hush/file behavior; 122 reproduces
Lua's cold/warm load-echo change while Koka/Go observations stay stable.

123 audits exact-tree publication of the CLI checkpoint. 126 validates the current installed Nix package and ten CLI cases; 127 passes all 134 + 8 assertions with verified source, runner and raw-log hashes and no regressions. 128 retains the heavy stage-1 matrix: Go/Lua artifacts match, Koka produces none within the host budget. The outer driver then fails on a wrong binary path, so its process exit code is unknown; the raw matrix is not promoted to a qualified result.
