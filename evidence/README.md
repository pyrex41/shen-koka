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
