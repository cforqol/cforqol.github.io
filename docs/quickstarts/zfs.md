---
tags: [zfs, storage, filesystem, snapshots]
---
# zfs

Datasets, properties, snapshots, send/recv.

Pool-level work is [zpool](zpool.md). Naming, retention and recovery live in the [ZFS snapshots handbook](../handbook/zfs/snapshots.md).

## Subcommands

| Command | Does |
|---------|------|
| `zfs list` | datasets |
| `zfs create pool/name` | new dataset |
| `zfs destroy pool/ds` | delete a dataset |
| `zfs get all pool/ds` | read properties |
| `zfs set key=value pool/ds` | write a property |
| `zfs inherit key pool/ds` | reset to the parent value |
| `zfs send` / `zfs receive` | replicate a snapshot |
| `zfs rename` | rename a dataset or snapshot |
| `zfs mount` / `zfs unmount` | manual mount control |

## Snapshots

| Command | Does |
|---------|------|
| `zfs snapshot pool/ds@name` | take one |
| `zfs snapshot -r pool/ds@name` | recursive over the tree |
| `zfs snapshot -o key=value` | set properties at creation |
| `zfs list -t snapshot` | list them |
| `zfs destroy pool/ds@name` | remove one |
| `zfs destroy pool/ds@a%z` | range, `%` inclusive |
| `zfs destroy pool/ds@a#z` | range, `#` exclusive |
| `zfs rollback pool/ds@name` | revert, destroying newer snapshots |
| `zfs rollback -r` | ...and newer snapshots recursively |
| `zfs rollback -R` | ...and any clones |
| `zfs clone pool/ds@name pool/new` | writable copy from a snapshot |
| `zfs promote pool/new` | make a clone independent |
| `zfs hold keep pool/ds@name` | pin against destroy |
| `zfs holds -r pool` | list holds |
| `zfs release keep pool/ds@name` | unpin |
| `zfs diff pool/ds@a pool/ds@b` | changed files between snapshots |
| `zfs bookmark pool/ds@name pool/ds#bm` | cheap ref that survives pruning |
| `zfs get -t snapshot all pool/ds@name` | snapshot properties |
| `zfs set snapdir=visible pool/ds` | expose `.zfs/snapshot` in `ls` |

## Recipes

```bash
# take one, named so it sorts chronologically
zfs snapshot tank/data@manual_2026-10-25_preupgrade

# whole tree
zfs snapshot -r tank/data@auto_2026-10-25_0300_daily

# list, newest last
zfs list -t snapshot -o name,used,creation -s creation -r tank | tail -20

# read a file out of a snapshot — live dataset untouched
ls /tank/data/.zfs/snapshot/
cp /tank/data/.zfs/snapshot/auto_2026-10-25_0300_daily/app.conf /tmp/

# clone and test, instead of rolling back
zfs clone tank/data@auto_2026-10-25_0300_daily tank/recovered
zfs promote tank/recovered

# rollback — destroys newer snapshots
zfs rollback -r tank/data@auto_2026-10-25_0300_daily

# pin before a risky change
zfs snapshot tank/data@keep_2026-10-25_preupgrade
zfs hold keep tank/data@keep_2026-10-25_preupgrade

# what changed since
zfs diff tank/data@auto_2026-10-25_0300_daily

# delete a range of automated snapshots, exclusive end
zfs destroy tank/data@auto_2026-10-01#auto_2026-10-15

# send parent that survives pruning
zfs bookmark tank/data@auto_2026-10-25_0300_daily tank/data#oct25

# how much are snapshots holding
zfs list -o name,usedbysnapshots -s usedbysnapshots -r tank | tail -10
```

## Send / receive

```bash
# full
zfs send tank/data@snap | ssh host zfs recv backup/data

# incremental — parent must exist on both ends
zfs send -i tank/data@prev tank/data@snap | ssh host zfs recv backup/data

# raw, stays encrypted on the wire and at rest
zfs send -w tank/secret@snap | ssh host zfs recv backup/secret
```

## Gotchas

- `zfs destroy` is instant and has no undo. Snapshots are the only safety net.
- `zfs destroy -r tank/data@snap` removes that snapshot **and every snapshot older than it**. One command can cost you a week.
- `zfs rollback` **destroys every snapshot newer than the target**. `-r` adds recursion, `-R` also takes dependent clones. Cloning instead avoids all of it.
- A clone's origin snapshot can't be destroyed — it gets `defer_destroy=on` and `zfs destroy` refuses. `zfs promote` the clone to break the link.
- `zfs send -r` replicates the tree and properties. `-i` is incremental. `-R` also preserves the snapshot graph.
- An incremental send needs the parent snapshot alive on *both* ends. Prune it and the chain breaks — that's what `zfs bookmark` is for.
- `-w` sends raw encrypted data. The receiver can't mount it without the key.
- Snapshots sort by **name**, not creation time. `-s creation` if you've ever renamed one.
- `snapdir=visible` makes `.zfs/snapshot` appear in `ls` and in `find` — some tools then recurse into every snapshot.
- `zfs get all` is enormous. `zfs get -s local` shows only what's explicitly set here.

## Related

- [zpool](zpool.md) — pool creation, scrubs, disk replacement
- [ZFS snapshots handbook](../handbook/zfs-snapshots.md) — naming, retention, automation, recovery
- [borgbackup](borgbackup.md) — offsite, deduplicated copies
