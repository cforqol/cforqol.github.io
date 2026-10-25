---
tags: [zfs, storage, mountpoints]
date: 2026-10-25
---
# Mountpoints

<span class="status status-draft">draft</span>

Where datasets appear in the filesystem, and the layout that keeps the pool root out of the way.

## The property

`mountpoint` is a dataset property and it inherits — set it at the level you mean and children follow.

| Value | Effect |
|-------|--------|
| `/some/path` | mounted there by ZFS |
| `none` | no path assigned; children still can be |
| `legacy` | ZFS leaves it alone, you mount via `/etc/fstab` |
| `-` | inherit from parent |

## The layout

The pool root is a container, not a home. Nothing lives in `/tank` itself:

```bash
zfs create -o mountpoint=/tank -o canmount=off tank
zfs create -o mountpoint=/tank/data tank/data
zfs create -o mountpoint=/tank/vm   tank/vm
```

```
/tank          canmount=off    container only
/tank/data     real dataset
/tank/vm       real dataset
```

`zfs list` stays a clean tree, and you never dump files into a dataset with no properties of its own.

## Change a mountpoint

```bash
zfs set mountpoint=/srv/data tank/data
zfs unmount tank/data
zfs mount tank/data
```

This changes where the dataset *appears*. It moves no data.

## Mounting

```bash
zfs mount -a              # everything not already mounted
zfs mount -R tank         # one tree, recursively
zfs mount -O tank/data    # overlay an existing mount
zfs unmount tank/data
zfs unmount -f tank/data  # force
```

## Legacy mounts

For tooling or an initramfs that expects `/etc/fstab`:

```bash
zfs set mountpoint=legacy tank/data
```

```
# /etc/fstab
tank/data  /tank/data  zfs  defaults,noatime  0 0
```

You give up ZFS mount ordering and `zfs mount -a`. Use it only where something requires it.

## Gotchas

!!! warning
    Never set a mountpoint over a directory that already contains files. ZFS doesn't merge — it mounts on top and the originals vanish from view until you unmount. You'll find them again, but not before a bad afternoon.

- `canmount=off` and `mountpoint=none` are different things. The first means "never mounts". The second means "no path, but it could".
- Use `canmount=off` on the pool root. Use `mountpoint=none` on containers whose children carry their own paths.
- Setting `mountpoint=/` on the wrong dataset hides your root filesystem.
- `zfs mount -a` respects hierarchy — a child can't mount before its parent.
- `unmount` fails "busy" while anything holds a file open. `lsof +D /tank/data` before reaching for `-f`.
- A `legacy` dataset is invisible to `zfs mount -a` and to `zfs-mount.service`.
- Changing a mountpoint doesn't migrate data. Moving it to a *different dataset* is `zfs rename` or a copy.
- `sharenfs` / `zfs share` is independent of `mountpoint`. Sharing doesn't imply mounting.

## Change log

- 2026-10-25 — first write-up
