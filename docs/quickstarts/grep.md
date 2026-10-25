---
tags: [shell, cli, search]
---
# grep

Search text across files and streams.

## Flags

| Flag | Does |
|------|------|
| `-r` | recurse into directories |
| `-n` | print line numbers |
| `-i` | case-insensitive |
| `-l` | filenames only, no matches |
| `-c` | count matches per file |
| `-v` | invert — lines that *don't* match |
| `-w` | whole words only |
| `-F` | fixed string, no regex |
| `-C n` | n lines of context |
| `-A n` / `-B n` | n lines after / before |
| `--include='*.py'` | only these files (needs `-r`) |
| `--exclude-dir=.git` | skip these directories |
| `-e PAT` | multiple patterns |

## Recipes

```bash
# find a string in a tree, skipping noise
grep -rn --include='*.py' --exclude-dir=.git 'TODO' ./src

# case-insensitive with context
grep -i -C 3 'error' app.log

# which files mention it
grep -rl 'old-api' .

# count per file, hiding zeroes
grep -rc 'import requests' . | grep -v ':0$'

# whole word, fixed string, no regex
grep -rwF 'config' .

# search a stream
ps aux | grep -v grep | grep nginx

# recursive replace via sed
grep -rl 'old-api' . | xargs sed -i 's/old-api/new-api/g'
```

## Gotchas

- Quote the pattern. An unquoted `*` gets expanded by the shell first.
- `--include` does nothing without `-r`.
- `-r` doesn't follow symlinks; `-R` does.
- Exit codes: `0` found, `1` not found, `2` error. `set -e` will kill a script on a legitimate "not found".
- `-I` skips binary files, `-a` forces them to be treated as text.

## Related

- [sed](sed.md)
