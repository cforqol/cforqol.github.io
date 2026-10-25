---
tags: [backup, borg, storage]
---
# borgbackup

Deduplicating, compressed, encrypted backups. Content-addressed, so identical data is stored once.

## Subcommands

| Command | Does |
|---------|------|
| `borg init --encryption=repokey` | create a repo |
| `borg create repo::archive paths` | new archive |
| `borg list repo` | archives in a repo |
| `borg list repo::archive` | files in an archive |
| `borg info repo::archive` | stats |
| `borg extract repo::archive path` | restore |
| `borg mount repo::archive mnt` | browse as a filesystem |
| `borg diff repo::a repo::b` | compare two archives |
| `borg prune` | apply a retention policy |
| `borg compact` | reclaim space freed by prune |
| `borg check` | verify repo and archive integrity |
| `borg delete` | remove an archive or a repo |
| `borg key export` | back up the encryption key |
| `borg break-lock` | clear a stuck lock |

## Flags

| Flag | Does |
|------|------|
| `--stats` | summary at the end |
| `--progress` | live progress |
| `--list` | list files as they're archived |
| `--dry-run` | show what would happen |
| `-C zstd,3` | compression (also `lz4`, `none`) |
| `--exclude` / `--exclude-from` | skip patterns |
| `--exclude-caches` | skip anything with a `CACHEDIR.TAG` |
| `--one-file-system` | don't cross mount points |
| `--remote-path` | path to borg on the remote |
| `--keep-daily` etc. | retention, for `prune` only |

## Recipes

```bash
# repo, key stored inside the repo
borg init --encryption=repokey ssh://host/./backups/tank

# BACK THIS UP SOMEWHERE ELSE
borg key export ssh://host/./backups/tank ~/borg-key.txt

# archive home, skipping caches and other filesystems
borg create --stats --progress --compression zstd,3 \
  --one-file-system --exclude-caches \
  --exclude '*.iso' --exclude '*/node_modules' \
  ssh://host/./backups/tank::home-{now:%Y-%m-%d} /home/me

# what's in there
borg list ssh://host/./backups/tank
borg list ssh://host/./backups/tank::home-2026-10-25

# retention, dry run first
borg prune --list --dry-run ssh://host/./backups/tank \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 12

# for real, then reclaim
borg prune ssh://host/./backups/tank \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 12
borg compact ssh://host/./backups/tank

# restore a single file
borg extract ssh://host/./backups/tank::home-2026-10-25 home/me/.bashrc

# browse without extracting
mkdir /tmp/b
borg mount ssh://host/./backups/tank::home-2026-10-25 /tmp/b
borg umount /tmp/b

# monthly integrity check
borg check --verify-data ssh://host/./backups/tank
```

## Gotchas

- **Lose the key and the data is gone.** `borg key export` it somewhere that isn't the repo. With `repokey` the key lives *in* the repo, so a stolen repo plus the passphrase is readable.
- `borg prune` **refuses to run** without at least one `--keep-*`. That's deliberate — it stops you wiping everything.
- `prune` alone frees nothing. You must `borg compact` after it, or the repo keeps growing.
- Never run two borg processes against one repo. Use a lockfile or a systemd timer with `Persistent=true`.
- A crashed run leaves a stale lock. `borg break-lock` clears it — only when nothing is running.
- `--one-file-system` matters. Without it you'll slurp every mount under the path, including network shares.
- Set the remote repo to `append-only`. A compromised client then can't destroy history — real ransomware protection.
- Archive names are free-form. `{now:%Y-%m-%d}` in the name is the standard trick.
- Borg 2.0 renamed a lot of the CLI. Pin your version.

## Related

- [zfs](zfs.md) — `zfs send` for local, borg for offsite
