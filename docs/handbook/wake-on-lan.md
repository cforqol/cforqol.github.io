---
tags: [networking, wake-on-lan, ubuntu, openwrt, bonding, pbr]
date: 2025-01-15
---
# Wake-on-LAN: Sending, Configuring, and Troubleshooting Magic Packets

A comprehensive guide to waking a powered-off Ubuntu server via Wake-on-LAN, including setup, bonding quirks, OpenWrt firewall/PBR routing, and hardware diagnostics.

## Prerequisites

- An Ubuntu machine to act as the sender (client)
- A target server with a network interface that supports Wake-on-LAN
- Access to the server's BIOS/UEFI
- (Optional) An OpenWrt router with SSH access
- (Optional) Familiarity with `ethtool`, `tcpdump`, and systemd service management

## Why it's built this way

Wake-on-LAN operates at Layer 2 (Data Link Layer), not Layer 3. This means:

- **Hostnames don't work natively.** A powered-off server has no IP address and doesn't respond to DNS/mDNS. The only thing active is the NIC, which blindly listens for a magic packet containing its hardcoded MAC address.
- **Broadcast packets are required.** WoL relies on broadcast packets (e.g., `10.0.0.255`). These packets cannot survive being routed through VPN tunnels like WireGuard.
- **Bonding complicates things.** `bond0` is a virtual interface with no physical NIC. WoL must be enabled on the physical slave interfaces, and switch behavior during LACP teardown can block packets.
- **The OS only configures the NIC; the motherboard must power it.** Even if Ubuntu says `Wake-on: g`, the BIOS must supply standby voltage to the PCIe slot after shutdown.

What was rejected:
- Using hostnames directly with `wakeonlan` (technically impossible at Layer 2)
- Relying solely on `netplan` for WoL persistence (inconsistent across Ubuntu versions)
- Sending WoL packets through WireGuard tunnels (broadcast packets are destroyed by WG)

## Setup

### 1. Install the WoL tool on your Ubuntu machine

```bash
sudo apt update
sudo apt install wakeonlan
```

### 2. Find your server's MAC address (when the server is already off)

Check these locations in order:

1. **Router DHCP leases:** Log into your router's web interface and look for Connected Devices / DHCP Client List. Even powered-off devices often remain in the lease table.
2. **ARP cache on Ubuntu:** Run `ip neigh` (or `arp -a`) on any machine that recently communicated with the server.
3. **Router static IP reservations:** If you reserved a static IP, the MAC is listed next to it.
4. **Physical hardware:** Look for a sticker on the back/bottom of the server, or on the NIC itself. You can also briefly boot into BIOS/UEFI and check System/Network Information.

### 3. Send the magic packet

```bash
# Basic broadcast (default 255.255.255.255)
wakeonlan <MAC_ADDRESS>

# Target a specific subnet broadcast (useful for cross-subnet WoL)
wakeonlan -i 10.0.0.255 <MAC_ADDRESS>
```

### 4. Use hostnames instead of MAC addresses (optional)

Since WoL can't resolve hostnames natively, use one of these workarounds:

**Option A: Bash alias (single server)**
```bash
# Add to ~/.bashrc
alias wake-myserver='wakeonlan 1A:2B:3C:4D:5E:6F'
```

**Option B: Lookup script (multiple servers)**
```bash
#!/bin/bash
# Save to /usr/local/bin/wake
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

**Option C: Query the router dynamically (OpenWrt)**
```bash
# One-liner (requires SSH keys to router)
ssh root@192.168.1.1 "grep -i my-server /tmp/dhcp.leases | awk '{print \$2}'" | xargs wakeonlan
```

### 5. Configure WoL on the server's NIC

Install `ethtool` and check support:

```bash
sudo apt install ethtool
ip link                    # Find your interface name (e.g., enp3s0)
sudo ethtool enp3s0        # Look for "g" in "Supports Wake-on"
```

Enable temporarily:
```bash
sudo ethtool -s enp3s0 wol g
```

Make permanent with a systemd service:
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

### 6. Configure WoL when using network bonding (bond0)

WoL cannot be enabled on `bond0` directly. You must enable it on **each physical slave interface**:

```bash
sudo ethtool -s eno1 wol g
sudo ethtool -s eno2 wol g
```

Create systemd services for each slave:
```bash
sudo systemctl enable wol@eno1.service
sudo systemctl enable wol@eno2.service
```

### 7. Configure OpenWrt firewall for cross-subnet WoL

If sending WoL from WiFi (10.0.1.0/24) to LAN (10.0.0.0/24), add a firewall rule:

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

Also ensure inter-zone forwarding exists:
```bash
uci add firewall forwarding
uci set firewall.@forwarding[-1].src='wlan'
uci set firewall.@forwarding[-1].dest='lan'
uci commit firewall
/etc/init.d/firewall restart
```

### 8. Fix PBR (Policy-Based Routing) intercepting local traffic

If you use `pbr` to route traffic through WireGuard (`wg1`), PBR will swallow broadcast packets and destroy them in the tunnel. You must tell PBR to ignore local subnets:

```bash
uci add_list pbr.config.ignored_destinations='10.0.0.0/24'
uci add_list pbr.config.ignored_destinations='10.0.1.0/24'
uci add_list pbr.config.ignored_destinations='10.0.0.255'
uci commit pbr
/etc/init.d/pbr restart
```

If `ignored_destinations` is unavailable in your PBR version, create a bypass policy:
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

### 9. Managing scripts across multiple machines

| Method | Best for | How |
| --- | --- | --- |
| Git repo | Developers, multiple scripts | Push scripts to GitHub/GitLab, clone on each machine, add folder to `PATH` |
| Ansible | Homelabs with many machines | Write a playbook that installs tools and deploys scripts automatically |
| Syncthing/Nextcloud | Non-technical sync | Put scripts in a synced folder, mirror across machines |
| Router-based script | Minimal footprint | Put the script on OpenWrt itself, call via SSH from any machine |

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

## If it breaks

| Symptom | Cause | Fix |
| --- | --- | --- |
| Server doesn't wake up | BIOS cutting power to NIC (ErP/EuP enabled) | Enter BIOS, disable ErP Ready, enable "Power On by PCI-E" |
| Server doesn't wake up (bonded NICs) | Switch tearing down LACP bond on shutdown | Change bond mode to Active-Backup (mode 1), or unplug secondary cable |
| Server doesn't wake up | Wrong MAC address being used | Send WoL to ALL MAC addresses (bond0, eno1, eno2) to find the correct one |
| `ethtool` shows `Wake-on: d` after reboot | WoL setting not persisted | Create a systemd `wol@.service` for each physical interface |
| WoL works from wired but not WiFi | PBR intercepting broadcast and sending to WireGuard | Add local subnets to PBR ignored destinations |
| WoL works from wired but not WiFi | Firewall blocking cross-zone traffic | Add forwarding rule from `wlan` zone to `lan` zone, allow UDP port 9 |
| Packet not reaching server | Router not forwarding broadcast | Use `wakeonlan -i 10.0.0.255 <MAC>` to target the specific subnet broadcast |
| Server wakes from `etherwake` on router but not from Ubuntu | Ubuntu machine sending to wrong broadcast address | Verify with `tcpdump -i any udp port 9` on Ubuntu that the packet is leaving |
| NIC link lights are off when server is shut down | Motherboard not supplying standby power | Check BIOS power management settings; ensure ErP is disabled |
| WoL works at 100Mbps but not 1Gbps | NIC firmware bug with high link speeds | Update NIC firmware / motherboard BIOS; try forcing lower link speed |

## Change log

- 2025-01-15 — first write-up
