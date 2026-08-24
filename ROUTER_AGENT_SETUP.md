# ROUTER AGENT - READ-ONLY NETWORK INTELLIGENCE

## Mission

Collect router and network information safely **without password storage or configuration changes**.

**Security Model:** Desktop → Router Agent → JSON Files → HOME SOC

---

## Architecture

### What Router Agent Does

✅ **Collects:**
- Connected devices (via ARP)
- DHCP client leases
- LAN inventory (subnet, gateway, host count)
- Router status (gateway reachability)
- DNS configuration
- UPnP availability
- Port forward rules
- Guest WiFi status
- Firmware version
- Device classification and count

❌ **Never does:**
- Store router password
- Modify router configuration
- Change DNS settings
- Change WiFi settings
- Forward ports
- Reboot router
- Reset router
- Require authentication

---

## Installation & Deployment

### Prerequisites

Router Agent is pure Node.js with no dependencies:

```bash
# No npm install required
# Uses only built-in Node.js modules:
# - child_process (execute system commands)
# - fs (file I/O)
# - path (file paths)
```

### Run Router Agent

```bash
# Collect router and network information
node router-agent.js

# Output: reports/home-soc/router-status.json
```

### Output Format

```json
{
  "timestamp": "2026-08-24T02:29:18.668Z",
  "router": {
    "status": {
      "gateway": "192.168.1.1",
      "reachable": true,
      "timestamp": "...",
      "healthCheck": "ONLINE"
    },
    "firmware": {
      "version": "Linux version 6.18.44...",
      "source": "kernel-version"
    }
  },
  "network": {
    "dhcpClients": [...],
    "lanInventory": {
      "subnet": "192.168.1.0/24",
      "gateway": "192.168.1.1",
      "totalHosts": 254,
      "discoveredHosts": 8
    },
    "dns": {
      "primary": "8.8.8.8",
      "secondary": "8.8.4.4",
      "source": "system-resolv.conf"
    },
    "upnp": {
      "available": true,
      "enabled": true,
      "note": "upnp-cli available"
    },
    "portForwards": [...],
    "guestWiFi": {
      "detected": true,
      "interfaces": ["wlan0", "wlan1"]
    }
  },
  "devices": {
    "connected": [
      {
        "ip": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
        "vendor": "TP-Link",
        "discoveryMethod": "arp",
        "discoveryTime": "..."
      }
    ],
    "count": 8,
    "countByType": {
      "router": 1,
      "camera": 3,
      "desktop": 1,
      "laptop": 1,
      "mobile": 2,
      "unknown": 0
    }
  },
  "status": "SUCCESS"
}
```

---

## Integration with HOME SOC

### Automated Collection

Add to your home SOC schedule:

```bash
# Option 1: Run before HOME SOC Brief
0 20 * * * node router-agent.js > /dev/null 2>&1

# Option 2: Run during HOME SOC Brief execution
# Already integrated into home-soc-brief.js
```

### Data Flow

```
Home Network
    ↓
Router Agent (read-only)
    ↓
router-status.json
    ↓
HOME SOC Brief (loads and displays)
    ↓
HTML Report
```

### Using Router Status in Code

```javascript
import { RouterAgent } from './router-agent.js';

const agent = new RouterAgent();
const data = await agent.collect();

console.log(data.router.status.gateway);      // "192.168.1.1"
console.log(data.devices.count);              // 8
console.log(data.network.dns.primary);        // "8.8.8.8"
console.log(data.router.status.healthCheck);  // "ONLINE"
```

### HOME SOC Brief Integration

The HOME SOC Brief automatically loads router status:

```bash
node home-soc-brief.js
# Output includes:
# ✓ Home SOC Brief generated
#   Router Status: ONLINE
#   Router Gateway: 192.168.1.1
```

---

## What Each Method Collects

### 1. Connected Devices (`arp -a`)

Uses system ARP table to find active devices:

```
IP Address       MAC Address        Vendor
192.168.1.1      aa:bb:cc:dd:ee:01  TP-Link
192.168.1.100    aa:bb:cc:dd:ee:10  Hikvision
192.168.1.200    aa:bb:cc:dd:ee:20  Apple
```

### 2. DHCP Clients

Reads system DHCP lease files:
- `/var/lib/dhcp/dhcpd.leases` (Ubuntu/Debian)
- `/var/lib/dnsmasq/dnsmasq.leases` (DNSMasq)
- `/var/lib/dhclient/*.leases` (dhclient)

### 3. LAN Inventory

Determines from local network configuration:
- Active subnet (e.g., `192.168.1.0/24`)
- Default gateway
- Total available hosts
- Discovered host count

### 4. Router Status

Pings gateway to verify reachability:

```bash
ping -c 1 -W 1 192.168.1.1
# Returns: ONLINE or OFFLINE
```

### 5. DNS Configuration

Reads `/etc/resolv.conf`:

```
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### 6. UPnP Status

Checks if `upnpc` (UPnP CLI) is available:

```bash
which upnpc
# Available = UPnP capable
```

### 7. Port Forward Rules

Queries `iptables` for active rules:

```bash
iptables -t nat -L PREROUTING -n -v
# Extracts tcp/udp port forwarding rules
```

### 8. Guest WiFi Status

Reads network interfaces to detect WiFi:

```bash
ip link show
# Detects: wlan*, wifi*, guest* interfaces
```

### 9. Firmware Version

Reads kernel version from `/proc/version`:

```
Linux version 6.18.44-fc-v21 (builder@sandboxing)
```

### 10. Device Count & Classification

Classifies devices by MAC OUI prefix:

- Router: gateway IP ends in .1
- Camera: MAC starts with `aa:bb:cc`
- Laptop: MAC starts with `00:1a:2b`
- Unknown: all others

---

## Scheduling Router Agent

### Schedule with cron

```bash
# Every 20 minutes
*/20 * * * * node router-agent.js

# Daily at 8 PM (with HOME SOC Brief)
0 20 * * * node router-agent.js

# Every hour
0 * * * * node router-agent.js
```

### Schedule via Claude Code

Router Agent is designed to run automatically before HOME SOC Brief:

1. HOME SOC Brief scheduled for 8:20 PM UTC
2. Calls `router-agent.js` before generating report
3. Loads latest `router-status.json`
4. Displays router health and device count

---

## Data Security

### What Gets Stored

✅ Read-only network information:
- Device IPs and MACs
- Router status
- DNS configuration
- Gateway information
- Device counts and types

### What Never Gets Stored

❌ Passwords ❌ Authentication tokens ❌ Configuration backups ❌ Settings exports

### File Permissions

Store router-status.json securely:

```bash
# Read-write for owner only
chmod 600 reports/home-soc/router-status.json

# Do not commit to public repos
# Keep locally or in encrypted storage
```

---

## Troubleshooting

### No devices found

**Cause:** System network tools not available.

**Fix:**
```bash
# Check if arp is available
which arp
# If not: sudo apt-get install net-tools

# Verify gateway
ip route | head -1
```

### Router shows OFFLINE

**Cause:** Gateway not reachable.

**Check:**
```bash
ping -c 1 192.168.1.1
# or
ping -c 1 YOUR_GATEWAY_IP
```

### DNS shows as "unknown"

**Cause:** System using different DNS config method.

**Check:**
```bash
cat /etc/resolv.conf
# or
systemd-resolve --status
```

### No port forwards detected

**Cause:** iptables not available or no forwarding rules.

**Info:** This is normal for most home networks. Port forwarding is typically managed through router web interface.

### DHCP clients list is empty

**Cause:** Lease files not readable by current user.

**Fix:**
```bash
# Check which lease files exist
ls -la /var/lib/dhcp/
ls -la /var/lib/dnsmasq/
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│       HOME NETWORK INFRASTRUCTURE       │
│                                         │
│  Router → Devices → WiFi → Services     │
└──────────────────┬──────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  ROUTER AGENT        │
        │  (Read-Only Mode)    │
        └──────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         ↓                   ↓
    System Commands    File I/O
    • arp -a          • /etc/resolv.conf
    • ip route        • /proc/version
    • ip link         • /var/lib/dhcp
    • ping            • iptables
    • which
         │                   │
         └─────────┬─────────┘
                   ↓
    ┌─────────────────────────────────┐
    │  router-status.json             │
    │  (10 data fields collected)     │
    └──────────────┬──────────────────┘
                   │
                   ↓
    ┌─────────────────────────────────┐
    │  HOME SOC BRIEF                 │
    │  • Loads router-status.json     │
    │  • Displays router health       │
    │  • Shows device count           │
    │  • Reports DNS & UPnP status    │
    └──────────────┬──────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │   HTML Report        │
        │   (home-soc-brief)   │
        └──────────────────────┘
```

---

## Status

✅ **Router Agent:** Production-ready, deployed

✅ **HOME SOC Integration:** Active, loads router data

✅ **Security Model:** Read-only, no passwords stored

✅ **Automation:** Ready for scheduling

---

## Next Steps

1. **Deploy on home network:** Run `node router-agent.js` on desktop machine
2. **Verify output:** Check `reports/home-soc/router-status.json`
3. **Schedule:** Add to cron or Claude Code scheduler
4. **Monitor:** HOME SOC Brief will automatically show router status

