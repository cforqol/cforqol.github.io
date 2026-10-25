---
tags: [zfs, storage, pool]
date: 2026-10-25
---
# Pool creation

<span class="status status-draft">draft</span>

Creating `tank`. Read [Vdevs and mirrors](vdevs.md) first if you haven't picked a topology — it's the decision you can't take back.

## Prerequisites

- All disks present: `ls -l /dev/disk/by-id/`
- Old signatures wiped: `wipefs -a /dev/disk/by-id/...`
- No conflicting pool already importable: `zpool import -d /dev/disk/by-id`
- ashift, topology and mountpoint decided

## Decisions, in order

| # | Decision | Reversible |
|---|----------|------------|
| 1 | `ashift` | never |
| 2 | vdev topology | never — add-only |
| 3 | redundancy level | never |
| 4 | mountpoint | yes |
| 5 | dataset properties | yes |

## Ashift

The minimum block size ZFS writes. Set at creation, never again.

| Value | Block | Use |
|-------|-------|-----|
| 9 | 512 B | ancient disks, and only then |
| 12 | 4 KiB | 512e and 4Kn disks — the default |
| 13 | 8 KiB | rare, some SSDs |

Get it wrong on a 4Kn disk and every write becomes a read-modify-write. You pay for it permanently. Detection behind a RAID controller is unreliable, so **state it explicitly**.

## Create

```bash
# wipe stale signatures first
wipefs -a /dev/disk/by-id/ata-WDC_WD40_1

zpool create \
  -o ashift=12 \
  -o autoexpand=on \
  -o autotrim=on \
  -O compression=zstd \
  -O xattr=sa \
  -O acltype=posixacl \
  -O relatime=on \
  -O mountpoint=/tank \
  -O canmount=off \
  tank mirror \
  /dev/disk/by-id/ata-WDC_WD40_1 \
  /dev/disk/by-id/ata-WDC_WD40_2
```

`-o` sets pool properties. `-O` sets properties on the root dataset. That `-O` set is the baseline you'd otherwise regret skipping.

Dry run first:

```bash
zpool create -n -v -o ashift=12 tank mirror /dev/disk/by-id/A /dev/disk/by-id/B
```

## After

```bash
zpool status -v tank
zpool list -v tank
zfs get compressratio tank
```

Then create datasets — layout is in [Mountpoints](mountpoints.md).

## Why these options

- **`ashift=12`** — non-negotiable on modern disks.
- **`autoexpand=on`** — replacing every disk in a vdev with a bigger one grows the vdev. Without it you're running `zpool online -e` by hand.
- **`autotrim=on`** — SSDs only. Keeps free blocks genuinely free.
- **`compression=zstd`** — strong ratio at lz4-class speed. Fewer blocks written often means *better* throughput.
- **`xattr=sa`** — extended attributes in the inode rather than a hidden directory. Faster, and required for correct POSIX ACLs.
- **`acltype=posixacl`** — what Linux tooling expects.
- **`canmount=off` on the root** — keeps `/tank` a pure container. Nothing lives there.

## Gotchas

!!! warning
    Never `zpool create` over a disk that already holds a pool without running `zpool import` first. `-f` will happily take it, and you'll wonder where the data went.

- `ashift` is per-vdev and fixed. A vdev added later must match.
- Don't create with a mountpoint over a non-empty directory. ZFS mounts on top rather than merging.
- The pool auto-mounts on create. `-O canmount=off` prevents that.
- `zpool create -f` forces over existing signatures. It does not merge them.
- One vdev means one failure domain. See [Vdevs and mirrors](vdevs.md).
- A failed `cache` or `log` device never loses data. A failed top-level data vdev always does.
- Pool names are global to the host. An imported disk from another machine can collide.

## Change log

- 2026-10-25 — first write-up
