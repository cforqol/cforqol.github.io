---
tags: [zfs, storage, pool]
---
# zpool

Pool creation, health, and disk replacement.

Dataset-level work is [zfs](zfs.md).

## Subcommands

| Command | Does |
|---------|------|
| `zpool status` | health, errors, scrub progress |
| `zpool list` | capacity summary |
| `zpool create` | new pool |
| `zpool add` | add a vdev |
| `zpool attach` / `detach` | grow or shrink a mirror |
| `zpool replace` | swap a disk |
| `zpool remove` | remove a vdev |
| `zpool offline` / `online` | take a disk out, put it back |
| `zpool scrub` | verify everything against checksums |
| `zpool clear` | reset error counters |
| `zpool import` / `export` | move a pool between systems |
| `zpool upgrade` | enable newer feature flags |
| `zpool history` | every command ever run on the pool |
| `zpool iostat` | live throughput |
| `zpool trim` | SSD discard |

## Recipes

```bash
# always by-id, never /dev/sdX
ls -l /dev/disk/by-id/

# two-disk mirror — ashift is set at creation and never again
zpool create -o ashift=12 tank mirror \
  /dev/disk/by-id/ata-WDC_WD40_1 \
  /dev/disk/by-id/ata-WDC_WD40_2

# raidz2, six disks
zpool create -o ashift=12 tank raidz2 \
  /dev/disk/by-id/ata-DISK{1,2,3,4,5,6}

# full health report
zpool status -v tank

# verify everything against checksums
zpool scrub tank

# weekly scrub on a timer
systemctl enable --now zfs-scrub-weekly@tank.timer

# a disk died — replace it
zpool replace tank /dev/disk/by-id/ata-OLD /dev/disk/by-id/ata-NEW

# watch the resilver
zpool status -v tank

# hot spare
zpool add tank spare /dev/disk/by-id/ata-SPARE

# move a pool to another machine
zpool export tank
# ... physically move the disks ...
zpool import tank

# what did I do last week
zpool history tank | tail -40

# clear errors once the cause is fixed
zpool clear tank
```

## Gotchas

- **Use `/dev/disk/by-id/`.** `/dev/sdX` reorders across reboots and the pool comes up degraded or won't import at all.
- `ashift=12` is set at creation and **cannot be changed**. Wrong ashift costs you write performance permanently. Get it right the first time.
- `zpool add` creates a new vdev. Removing one later is limited — mirrors and top-level vdevs only, and raidz removal is newer and slow. To grow an existing mirror, use `attach`.
- `zpool upgrade` writes new feature flags. An older kernel or older ZFS release then can't import the pool.
- Losing a top-level vdev loses the whole pool. `raidz1` on large disks has a real rebuild-failure window — `raidz2` is the safer default.
- `zpool destroy` is immediate. `zpool import -D` sometimes finds destroyed pools, but don't rely on it.
- A failed `log` (SLOG) or `cache` (L2ARC) device won't lose data. Both are replaceable.
- `zpool scrub` on a busy pool hurts. Schedule it.
- `zpool clear` hides errors. Read `zpool status -v` first, then clear.

## Related

- [zfs](zfs.md) — datasets, snapshots, send/recv
