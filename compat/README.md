# Optional community pattern-hook adapter

The pinned S42 `core.kl` has neither `shen.*custom-pattern-compiler*` nor
`shen.*custom-pattern-reducer*` hooks. The bundled community extension sets
those globals but the S42 compiler never reads them. Both pinned reference
ports fail the first extension assertion without an adapter.

`SHEN_KOKA_PPM_COMPAT=1` installs this separate adapter after the pristine boot.
Default boot does not install it. The adapter preserves the original
`shen.<pattern>` and `shen.triple-stack` under explicit names, adds the two
hook boundaries, and delegates ordinary patterns to those originals. No
vendored kernel source is edited. This is compatibility work, not a native
optimization or replacement of the Shen compiler.

The two retained original function bodies come from pinned `core.kl` and are
covered by `kernel/UPSTREAM-LICENSE` (Mark Tarver's BSD 3-Clause license).
The new hook code is port-specific. Extension qualification requires all eight
unchanged assertions plus canonical regression checks with the adapter enabled.
Until those runs pass, this adapter is experimental.
