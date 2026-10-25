---
tags: [shell, cli]
---
# sed

Stream editor. Find and replace, line deletion, in-place edits.

## Flags

| Flag | Does |
|------|------|
| `-i` | edit files in place |
| `-i.bak` | in place, keep a `.bak` |
| `-n` | suppress auto-print |
| `-E` | extended regex |
| `-e` | multiple expressions |

## Recipes

```bash
# replace first match per line
sed 's/old/new/' file

# replace all matches per line
sed 's/old/new/g'

# in place, with backup
sed -i.bak 's/old/new/g' file.txt

# delete matching lines
sed '/^#/d' file.conf

# print only lines 10-20
sed -n '10,20p' file

# strip trailing whitespace
sed -i 's/[[:space:]]*$//' file
```

## Gotchas

- `-i` takes an optional suffix. GNU accepts `sed -i 's/a/b/' f`; BSD/macOS needs `sed -i '' 's/a/b/' f`.
- The delimiter is arbitrary — `sed 's|/usr/local|/opt|g'` for paths.
- `&` in the replacement means the whole match. Escape it as `\&` for a literal.

## Related

- [grep](grep.md)
