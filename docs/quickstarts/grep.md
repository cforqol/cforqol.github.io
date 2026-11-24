---
tags: [shell, cli, search]
---

# grep

Search text across files and streams.

## Flags

| Flag | Does |
| --- | --- |
| `-r` | recurse into directories |
| `-R` | recurse, following symlinks |
| `-n` | print line numbers |
| `-i` | case-insensitive |
| `-l` | filenames only, no matches |
| `-c` | count matches per file |
| `-v` | invert — lines that _don't_ match |
| `-w` | whole words only |
| `-F` | fixed string, no regex |
| `-C n` | n lines of context (both sides) |
| `-A n` | n lines after each match |
| `-B n` | n lines before each match |
| `-I` | skip binary files |
| `-a` | treat binary files as text |
| `--include='*.py'` | only these files (needs `-r`) |
| `--exclude='*.log'` | skip these files (needs `-r`) |
| `--exclude-dir=.git` | skip these directories (needs `-r`) |
| `--exclude-from=FILE` | skip files matching patterns in FILE |
| `-e PAT` | multiple patterns |

## Recipes

Basic usage, simplest first.

### Basic search

```bash
# plain search in one file
grep 'error' app.log

# case-insensitive
grep -i 'error' app.log

# with line numbers
grep -n 'error' app.log

# whole words only
grep -w 'config' app.log

# fixed string, no regex
grep -F 'a.b(c' app.log
```

### Context around matches

```bash
# 3 lines after each match
grep -A 3 'error' app.log

# 3 lines before each match
grep -B 3 'error' app.log

# 3 lines before and after
grep -C 3 'error' app.log

# -C with no number defaults to 2
grep -C 'error' app.log

# combine with other flags
grep -in -C 2 'error' app.log
```

`-A` = after, `-B` = before, `-C` = both (`-C 3` is the same as `-A 3 -B 3`). Match groups are separated by `--` in the output.

### Recursion

```bash
# recursive across a tree
grep -r 'TODO' ./src

# which files mention it
grep -rl 'old-api' .

# follow symlinks too (default -r doesn't)
grep -R 'TODO' ./src
```

### Scoping the search

```bash
# only certain file types
grep -rn --include='*.py' 'TODO' ./src

# skip noise directories
grep -rn --exclude-dir=.git 'TODO' .

# skip noise files
grep -rn --exclude='*.log' 'TODO' .

# both at once
grep -rn --exclude-dir=node_modules --exclude='*min.js' 'TODO' .
```

### Filtering output

```bash
# lines that don't match
grep -v 'debug' app.log

# count per file, hiding zeroes
grep -rc 'import requests' . | grep -v ':0'

# drop grep itself from a process listing
ps aux | grep -v grep | grep nginx
```

### Combining with other tools

```bash
# search a stream
ps aux | grep nginx

# recursive replace via sed
grep -rl 'old-api' . | xargs sed -i 's/old-api/new-api/g'
```

## Excluding directories

Use `--exclude-dir` to skip whole folders. It needs `-r` to do anything.

```bash
# one directory
grep -r --exclude-dir=node_modules 'error' .

# several, chained
grep -r --exclude-dir=node_modules --exclude-dir=.git 'error' .

# several, brace-expanded
grep -r --exclude-dir={node_modules,.git,dist} 'error' .

# by pattern — skip all hidden dirs
grep -r --exclude-dir='.*' 'error' .
```

Just the folder name is enough (`node_modules`, not `./node_modules`); it's excluded anywhere it appears in the walk.

## Excluding files

Use `--exclude` to skip files by **basename**, matched with shell globs — not regex.

```bash
# by extension
grep -r --exclude='*.log' 'error' .

# by substring — wrap in * * to get "contains"
grep -r --exclude='*test*' 'error' .

# multiple patterns
grep -r --exclude='*.log' --exclude='*backup*' 'error' .

# patterns from a file, one per line
grep -r --exclude-from=patterns.txt 'error' .

# dirs and files together
grep -r --exclude-dir=.git --exclude='*min.js' 'error' .
```

Gotcha: there's no regex in `--exclude`, so `*string*` is the only way to say "filename contains string". If you need real regex on paths, drive it from `find` instead:

```bash
find . -type f ! -name '*test*' -exec grep -H 'error' {} +
```

## Gotchas

- Quote the pattern. An unquoted `*` gets expanded by the shell first.
- `--include`, `--exclude`, and `--exclude-dir` do nothing without `-r`.
- `--exclude` matches basenames with globs, not regex — use `*str*` for "contains".
- `-r` doesn't follow symlinks; `-R` does.
- `-C` with no number defaults to 2.
- Exit codes: `0` found, `1` not found, `2` error. `set -e` will kill a script on a legitimate "not found".
- `-I` skips binary files, `-a` forces them to be treated as text.

## Related

- [sed](sed.md)
