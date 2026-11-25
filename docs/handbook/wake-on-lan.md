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
```

### 2. Find the server's MAC address while it's off

Check these in order:

1. **Router DHCP leases** — log into the router and look at Connected Devices / DHCP Client List. Powered-off devices usually stay in the lease table.
2. **ARP cache on Ubuntu** — `ip neigh` (or `arp -a`) on any machine that recently talked to the server.
3. **Router static IP reservations** — the MAC is listed next to the reservation.
4. **Physical hardware** — sticker on the back or bottom of the server, or on the NIC. A brief boot into BIOS/UEFI also shows it under System/Network Information.

### 3. Send the magic packet

```bash
# basic broadcast (default 255.255.255.255)
wakeonlan <MAC_ADDRESS>

# target a specific subnet broadcast (cross-subnet WoL)
wakeonlan -i 10.0.0.255 <MAC_ADDRESS>
```

### 4. Use hostnames instead of MACs

WoL can't resolve names, so pick a workaround.

**Option A — bash alias, single server:**

```bash
# add to ~/.bashrc
alias wake-myserver='wakeonlan 1A:2B:3C:4D:5E:6F'
```

**Option B — lookup script, multiple servers:**

```bash
#!/bin/bash
# save to /usr/local/bin/wake
declare -A MACS=(
    ["myserver"]="1A:2B:3C:4D:5E:6F"
    ["nas"]="AA:BB:CC:DD:EE:FF"
    ["desktop"]="11:22:33:44:55:66"
)
if [ -z "$1" ]; then
    echo "Usage: wake <hostname>"
    echo "Available hosts: ${!MACS[@]}"
    exit 1
fi
HOST=$1
MAC=${MACS[$HOST]}
if [ -n "$MAC" ]; then
    echo "Sending magic packet to $HOST ($MAC)..."
    wakeonlan $MAC
else
    echo "Error: Host '$HOST' not found."
    exit 1
fi
```

**Option C — query the router dynamically (OpenWrt):**

```bash
# one-liner, requires SSH keys to the router
ssh root@192.168.1.1 "grep -i my-server /tmp/dhcp.leases | awk '{print \$2}'" | xargs wakeonlan
```

The `\$2` is deliberate — it stops the local shell expanding `$2` before the command reaches the router.

### 5. Configure WoL on the server's NIC

```bash
sudo apt install ethtool
ip link                    # find the interface name (e.g. enp3s0)
sudo ethtool enp3s0        # look for "g" in "Supports Wake-on"
```

Enable it temporarily:

```bash
sudo ethtool -s enp3s0 wol g
```

Make it permanent with a systemd unit:

```bash
sudo nano /etc/systemd/system/wol@.service
```

```ini
[Unit]
Description=Wake-on-LAN for %i
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/ethtool -s %i wol g

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable wol@enp3s0.service
sudo systemctl start wol@enp3s0.service
```

### 6. Bonded interfaces

WoL can't be enabled on `bond0`. Enable it on each physical slave:

```bash
sudo ethtool -s eno1 wol g
sudo ethtool -s eno2 wol g
```

```bash
sudo systemctl enable wol@eno1.service
sudo systemctl enable wol@eno2.service
```

### 7. OpenWrt firewall for cross-subnet WoL

Sending from WiFi (`10.0.1.0/24`) to LAN (`10.0.0.0/24`):

```bash
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-WoL-WLAN-to-LAN'
uci set firewall.@rule[-1].src='wlan'
uci set firewall.@rule[-1].dest='lan'
uci set firewall.@rule[-1].proto='udp'
uci set firewall.@rule[-1].dest_port='9'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
/etc/init.d/firewall restart
```

Inter-zone forwarding also has to exist:

```bash
uci add firewall forwarding
uci set firewall.@forwarding[-1].src='wlan'
uci set firewall.@forwarding[-1].dest='lan'
uci commit firewall
/etc/init.d/firewall restart
```

### 8. Stop PBR intercepting local traffic

If `pbr` routes traffic through WireGuard (`wg1`), it swallows the broadcast and kills it in the tunnel. Tell it to ignore local subnets:

```bash
uci add_list pbr.config.ignored_destinations='10.0.0.0/24'
uci add_list pbr.config.ignored_destinations='10.0.1.0/24'
uci add_list pbr.config.ignored_destinations='10.0.0.255'
uci commit pbr
/etc/init.d/pbr restart
```

If `ignored_destinations` doesn't exist in your PBR version, build a bypass policy instead:

```bash
uci add pbr policy
uci set pbr.@policy[-1].name='Bypass-Local-LAN'
uci set pbr.@policy[-1].src_addr='10.0.0.0/24 10.0.1.0/24'
uci set pbr.@policy[-1].dest_addr='10.0.0.0/24 10.0.1.0/24 10.0.0.255'
uci set pbr.@policy[-1].chain='PREROUTING'
uci set pbr.@policy[-1].action='Disable'
uci reorder pbr.@policy[0]=0
uci commit pbr
/etc/init.d/pbr restart
```
