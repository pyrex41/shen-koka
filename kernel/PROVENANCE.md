# Vendored source identities

The kernel payload under `klambda/`, its extension sources, and the canonical
test tree are copied from the community ShenOSKernel 43.1 release:

- tag: `shen-43.1`
- source commit: `715824a52b55e9c81a9501df8548ff3edd8411f5`
- release archive SHA-256: `900eedef44f440af78f9395ed06e689ce1604546fc309f5bc7c8bc84cc651920`

The release contains 24 generated KLambda modules plus `stlib.kl`; the Koka
port retains its pre-existing `backend.kl` as a port shim outside that release
payload. The host loader runs the release initializer and all three phases
(`shen.initialise-environment`, `shen.initialise-lambda-forms`, and
`shen.initialise-signedfuncs`) before commands or scripts execute.

`comparison/shen-suite.lock.json` records the current 43.1 test-tree hashes
and the 154 canonical assertions. Historical 42.x evidence remains in prior
commits; it is not used as current qualification.
