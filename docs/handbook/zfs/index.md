---
tags: [zfs, storage]
---
# ZFS

How storage on this machine is laid out, and why.

Commands are in the [zpool](../quickstarts/zpool.md) and [zfs](../quickstarts/zfs.md) quick starts. This section is the reasoning.

## Read in this order

| Page | Covers |
|------|--------|
| [Pool creation](pool-creation.md) | ashift, topology choice, the `zpool create` you actually run |
| [Vdevs and mirrors](vdevs.md) | raid10, growing, replacing disks, failure domains |
| [Mountpoints](mountpoints.md) | where datasets appear, and the container layout |
| [Snapshots](snapshots.md) | naming, retention, automation, recovery |

## Standing rules

1. **Always `/dev/disk/by-id/`.** Never `/dev/sdX`.
2. **`ashift=12`**, decided once at creation, never again.
3. **`zpool add` is not `zpool attach`.** One creates a new vdev, the other grows an existing one.
4. **`zpool status -v` before and after every change.**
5. **Snapshots are not backups.** Offsite copies come from [borg](../../quickstarts/borgbackup.md) or `zfs send`.

## The decisions that can't be undone

ashift, vdev topology, redundancy level. Everything else — mountpoints, properties, dataset layout — is changeable. Spend your thinking time in the first group.
