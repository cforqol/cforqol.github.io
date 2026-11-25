---
tags: [networking, wake-on-lan, ubuntu, openwrt, bonding, pbr]
---

# Wake-on-LAN: the server that wouldn't wake

A powered-off Ubuntu server that ignored every magic packet, and the four separate things that were stopping the packet from reaching its NIC.

## Symptoms

Work the table top to bottom. The first two rows account for most cases, and row one is the one everybody misses because the machine looks fine — it's just that nothing is powering the network card.

| Symptom | Cause | Fix |
| --- | --- | --- |
| NIC link lights are dark when the server is shut down | Motherboard not supplying standby power to the PCIe slot | Disable ErP/EuP Ready in BIOS, enable "Power On by PCI-E" |
| Server doesn't wake at all | BIOS cutting power to the NIC (ErP/EuP enabled) | Disable ErP Ready in BIOS/UEFI |
| Server doesn't wake, NICs are bonded | Switch tearing down the LACP bond on shutdown | Change bond mode to Active-Backup (mode 1), or unplug the secondary cable as a test |
| Server doesn't wake, nothing obviously wrong | Wrong MAC address being used | Send to every MAC (bond0, eno1, eno2) and see which one works |
| `ethtool` shows `Wake-on: d` after a reboot | WoL setting not persisted | Create a `wol@.service` for each physical interface |
| Works from wired, fails from WiFi | PBR intercepting the broadcast and routing it into WireGuard | Add local subnets to PBR `ignored_destinations` |
| Works from wired, fails from WiFi | Firewall blocking cross-zone traffic | Add forwarding rule `wlan` → `lan`, allow UDP port 9 |
| Packet never reaches the server | Router not forwarding the broadcast | `wakeonlan -i 10.0.0.255 <MAC>` to target the subnet broadcast |
| Router's `etherwake` works, Ubuntu doesn't | Ubuntu sending to the wrong broadcast address | `tcpdump -i any udp port 9` on Ubuntu and confirm the packet is leaving |
| Works at 100Mbps, fails at 1Gbps | NIC firmware bug at high link speed | Update NIC firmware and motherboard BIOS, or force a lower link speed |

## Cause

Wake-on-LAN runs at Layer 2, not Layer 3. A powered-off machine has no IP address and answers no DNS, so the only thing listening is the NIC itself, waiting for a magic packet containing its hardcoded MAC. That single fact explains almost every failure below:

- **Broadcasts are mandatory.** WoL relies on broadcast packets (`10.0.0.255`), and broadcasts do not survive being routed through a WireGuard tunnel.
- **The OS configures the NIC; the motherboard powers it.** Even with `Wake-on: g` confirmed, the board has to keep standby voltage on the PCIe slot after shutdown.
- **`bond0` is virtual.** It has no physical NIC, so `ethtool -s bond0 wol g` does nothing. WoL has to be enabled on the slaves.
- **The setting is not durable across a hard power-off.** The OS tells the NIC to listen during a graceful shutdown. Pull the plug and the NIC forgets.

The four that actually bit here, in the order they were ruled out:

1. **ErP/EuP Ready in BIOS.** Cuts standby power to the PCIe slot on shutdown. Link lights go dark. Nothing else matters until this is off.
2. **LACP bonding (mode 4).** On shutdown the switch sees LACP drop and disables the ports, so the magic packet has nowhere to land.
3. **PBR routing local traffic into `wg1`.** Policy-based routing swallows the broadcast and destroys it in the tunnel.
4. **`bond0` instead of the slaves.** Enabling WoL on the bond interface silently does nothing.

### What I rejected

- Sending to hostnames directly with `wakeonlan` — impossible at Layer 2, the name has no meaning to a powered-off NIC.
- Relying on `netplan` alone for WoL persistence — inconsistent across Ubuntu versions.
- Sending WoL packets through the WireGuard tunnel — broadcast is destroyed by design.

## Fix

One change per cause, in the order they were applied:

1. **BIOS:** disable ErP/EuP Ready, enable "Power On by PCI-E". Verify by checking the NIC link lights with the machine shut down — they should stay lit.
2. **Bonding:** either move to Active-Backup (mode 1), or accept mode 4 and enable `wol g` on each physical slave.
3. **PBR:** add both local subnets and the subnet broadcast address to `ignored_destinations`.
4. **Persistence:** a `wol@.service` instance per physical interface, so the setting survives reboot.
5. **Cross-subnet:** firewall rule from `wlan` to `lan` on UDP port 9, plus forwarding, plus an explicit `-i` broadcast address.

Exact commands for all of it are in the reference below.

## Gotchas

!!! warning
    **ErP/EuP Ready in BIOS will kill WoL.** This power-saving feature cuts standby power to the PCIe slot when the server shuts down. If the link lights on the NIC are completely dark when the server is off, the motherboard is not powering the NIC. Disable ErP Ready in BIOS/UEFI.

!!! warning
    **LACP bonding (mode 4) breaks WoL.** When the server powers off, the switch detects LACP dropping and disables the ports. The magic packet never reaches the NIC. Use Active-Backup (mode 1) instead, or unplug the secondary cable as a test.

!!! warning
    **WireGuard cannot transmit broadcast packets.** If PBR routes your local subnet traffic into `wg1`, WoL broadcasts will be destroyed. You must add a PBR bypass rule for local subnets.

!!! warning
    **Pulling the power plug disables WoL on many motherboards.** The OS must tell the NIC to listen before shutting down. Always shut down gracefully with `sudo shutdown now`.

!!! warning
    **`bond0` does not support WoL.** You must enable `wol g` on the physical slave interfaces (e.g., `eno1`, `eno2`), not on the virtual bond interface.

## Reference: how it's configured

### 1. Install the tool on the sending machine

```bash
sudo apt update
sudo apt install wakeonlan
