# Vendored source identities

The KLambda modules and test tree are copied without source edits from the
community ShenOSKernel 43.1 release (`shen-43.1`, commit
`715824a52b55e9c81a9501df8548ff3edd8411f5`, archive SHA-256
`900eedef44f440af78f9395ed06e689ce1604546fc309f5bc7c8bc84cc651920`). The
pre-existing StLib is copied without source edits from
`pyrex41/shen-lua` at `614cd0754a741c8070c467b2b07f07943d17f4ff`.
The `extensions/` Shen sources are copied from `pyrex41/shen-go` at
`c22151dc55cafac7e5b904b8c58c6280c38801b2` (the pinned Lua checkout lacks them).
See `UPSTREAM-LICENSE` and the retained directory provenance files.

`comparison/shen-suite.lock.json` verifies all 63 test files before each run.
`research/source-inventory.json` pins all 19 KL hashes. No upstream kernel
function has been replaced by a native implementation. Full boot evaluates
all module forms in order, including load-time initialization; it does not
invoke a synthetic initializer.

The existing upstream provenance contains historical wording and unresolved
mirror-import identifiers; it is retained as received, not asserted as newly
verified provenance. The actual Git revisions and file hashes above are the
reproduction boundary for this port.
