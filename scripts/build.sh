#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build
# Never publish a stale executable after a failed compile. Use isolated staging
# for the output. Serial compilation avoids the observed empty-object failure.
build_dir=$(mktemp -d .build/compile-XXXXXX)
koka -j1 -isrc -O2 --builddir="${SHEN_KOKA_BUILD_CACHE:-.build/koka-serial}" -o "$build_dir/shen-koka" src/shen/main.kk
chmod +x "$build_dir/shen-koka"
mv "$build_dir/shen-koka" .build/shen-koka
python3 - <<'PY'
import hashlib,json,pathlib
r=pathlib.Path('.')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
j={'binary_sha256':sha(r/'.build/shen-koka'),'sources':{str(p):sha(p) for p in sorted((r/'src').rglob('*')) if p.is_file()},'flake_lock_sha256':sha(r/'flake.lock')}
(r/'.build/build.json').write_text(json.dumps(j,indent=2)+'\n')
PY
