# Pristine ShenOSKernel 42.2 distribution

`ShenOSKernel-42.2/` is the unchanged contents of the upstream release asset:
https://github.com/Shen-Language/shen-sources/releases/download/shen-42.2/ShenOSKernel-42.2.tar.gz

Archive SHA-256: `1d02273003654d34ec020ae67cb214ecec410dee3350419ff807d82b652678d8`.
Tag `shen-42.2` points to source commit `73507e069fe147aefb728d632c4ce40bc6a7b314`.
The source tag was read back from GitHub on 2026-10-11.
GitHub's automatically generated tag archive is a different artifact and must not
be substituted for the distribution identity.

File hashes are in `comparison/shen42.2-source.lock.json`. Retain LICENSE.txt;
put adaptations outside this directory. Vendoring is not runtime qualification.

Run `python3 scripts/fetch-shen42.py` to populate the ignored distribution.
The fetcher checks the archive hash and every extracted file before publication.
Upstream example files contain personal Windows paths rejected by the local
commit guard; the guard stays enabled and the upstream files stay unchanged.
