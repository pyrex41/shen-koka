# Command-line behavior

`eval -e EXPR` uses the pinned Shen reader and compiler. Strings print as text;
other values keep the port's diagnostic rendering, including explicit
`shen.fail!`. The KLambda `kl` command retains quoted-string diagnostics.

Eval actions execute left to right. Short and long spellings are supported:

- `-e` / `--eval EXPR`: evaluate and print the last result.
- `-l` / `--load FILE`: invoke the original kernel loader, including its chatter
  and typechecking behavior.
- `-s` / `--set KEY VALUE`: evaluate the key and value, then set the global.
- `-q` / `--quiet`: set `*hush*` for following actions; computation still runs.
- `-r` / `--repl`: enter the kernel-backed REPL with host EOF termination.

`script FILE ARGS...` uses the pinned `shen.x.launcher.script-command` and its
quiet loader. Program output remains visible; top-level return values are not
implicitly echoed. `*argv*` is `[FILE | ARGS]`. Errors and invalid arguments
exit nonzero. Ten focused CLI contracts are retained in evidence 116.

The original S42 `pr` checks `*hush*` before inspecting its stream. This may differ
from reference-port file-output policies; the broader Bifrost corpus is a
separate comparison gate. Do not infer its result from the primary Shen suite.

```sh
nix develop --command python3 scripts/test-cli.py
bin/shen-koka eval -s '*example*' 9 -e '(value *example*)'
bin/shen-koka script program.shen alpha beta
```
