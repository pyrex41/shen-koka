# Vendored source identities

The KLambda modules, test tree, and StLib are copied without source edits from
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
