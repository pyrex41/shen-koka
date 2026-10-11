The actual Yggdrasil hello slice compiled with direct callbacks and produced the
expected stdout, exit 0, and empty stderr from an empty temporary directory with
SHEN_KOKA_ROOT=/nonexistent. See run.json for the exact executable hash.

The 99,384,088-byte executable includes debug information; its ELF text section
is 5,584,514 bytes. Compare elf-sections.txt rather than treating the entire file
as instruction bytes. This single successful artifact is not the full native
kernel gate or a general deployment qualification.
