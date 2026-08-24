# REAL HOME NETWORK DISCOVERY

## Mission

Replace simulated discovery with actual network scanning.

**Rule:** NO baseline data. NO placeholders. Only real evidence.

---

## Architecture

### Real Discovery Script: `real-home-discovery.js`

Performs actual network scanning using four independent methods:

#### 1. **ARP Scan** (`arp-scan`)
- **What:** Sends ARP requests to every IP on the subnet
- **Returns:** MAC addresses, vendor names (from OUI database)
- **Evidence:** Actual ARP protocol responses
- **Confidence:** 100% (devices must respond to ARP to exist)

```bash
arp-scan --localnet --numeric
# 192.168.1.100  aa:bb:cc:dd:ee:ff  Hikvision Digital Technology
```

#### 2. **System ARP Table** (`arp`)
- **What:** Queries local ARP cache
- **Returns:** IP → MAC mappings from system
- **Evidence:** Previous network communication
- **Confidence:** 95% (may be stale)

```bash
arp -a
# router (192.168.1.1) at aa:bb:cc:dd:ee:01 [ether] on eth0
```

#### 3. **Port Scanning** (`nmap`)
- **What:** TCP/UDP port scanning and OS fingerprinting
- **Returns:** Open ports, service detection, OS hints
- **Evidence:** Actual port responses
- **Confidence:** 90% (some services hidden/filtered)

```bash
nmap -sV -O 192.168.1.0/24
# 192.168.1.100: 554/open (RTSP), 80/open (HTTP), 443/open (HTTPS)
```

#### 4. **Router API** (if available)
- **What:** Query DHCP/device list from router
- **Returns:** All connected devices from authoritative source
- **Evidence:** Router's device database
- **Confidence:** 100% (router tracks all connections)

```bash
curl http://192.168.1.1/api/devices
# Returns: IP, MAC, hostname, connection time
```

---

## Output Format

### Real Inventory Example

```json
{
  "timestamp": "2026-08-24T14:30:00.000Z",
  "network": "192.168.1.0/24",
  "discoveryMethods": ["arp-scan", "arp", "nmap", "router-api"],
  "totalDevices": 8,
  "devices": [
    {
      "ip": "192.168.1.1",
      "mac": "aa:bb:cc:dd:ee:01",
      "vendor": "TP-Link Technologies",
      "detectionMethods": ["arp-scan", "arp"],
      "source": "ARP Protocol",
      "openPorts": [22, 80, 443, 53],
      "discoveryTimestamp": "2026-08-24T14:30:05.123Z",
      "confidence": 100
    },
    {
      "ip": "192.168.1.100",
      "mac": "aa:bb:cc:dd:ee:10",
      "vendor": "Hikvision Digital Technology",
      "detectionMethods": ["arp-scan", "nmap"],
      "source": "ARP Protocol + Port Scan",
      "openPorts": [554, 80, 443],
      "discoveryTimestamp": "2026-08-24T14:30:12.456Z",
      "confidence": 100
    }
  ]
}
```

### Markdown Report Example

```markdown
# REAL HOME NETWORK INVENTORY

**Discovery Timestamp:** 2026-08-24T14:30:00.000Z
**Network Scanned:** 192.168.1.0/24
**Total Devices:** 8
**Detection Methods Used:** arp-scan, arp, nmap, router-api

## DEVICES DISCOVERED

### 192.168.1.1
- **MAC Address:** aa:bb:cc:dd:ee:01
- **Vendor:** TP-Link Technologies
- **Detection Method:** arp-scan, arp
- **Source:** ARP Protocol
- **Confidence:** 100%
- **Open Ports:** 22, 80, 443, 53
- **Discovery Time:** 2026-08-24T14:30:05.123Z

### 192.168.1.100
- **MAC Address:** aa:bb:cc:dd:ee:10
- **Vendor:** Hikvision Digital Technology
- **Detection Method:** arp-scan, nmap
- **Source:** ARP Protocol + Port Scan
- **Confidence:** 100%
- **Open Ports:** 554, 80, 443
- **Discovery Time:** 2026-08-24T14:30:12.456Z
```

---

## Deployment Instructions

### Prerequisites

Install required tools on your home network desktop/server:

```bash
# Ubuntu/Debian
sudo apt-get install arp-scan nmap

# macOS
brew install arp-scan nmap

# Fedora/RHEL
sudo dnf install arp-scan nmap
```

### Run Real Discovery

```bash
# Default: scan 192.168.1.0/24
node real-home-discovery.js

# Custom subnet
node real-home-discovery.js 10.0.0.0/24
```

### Output Files

Generated in `./reports/real-home-discovery/`:

- `inventory-YYYY-MM-DD.json` — Detailed JSON with all fields
- `REAL_HOME_INVENTORY.md` — Human-readable markdown report
- `latest-inventory.json` — Latest scan for comparisons

---

## Verification Checklist

### ✅ Real Discovery Proof

- [ ] MAC addresses are actual hardware addresses (not `xx:xx:xx:xx:xx:xx`)
- [ ] Vendor names are real manufacturers (not `router-brand`, `desktop`)
- [ ] Detection methods are real tools (`arp-scan`, `nmap`, `router-api`)
- [ ] Open ports are actual discovered ports (not hardcoded)
- [ ] Confidence is based on detection method reliability
- [ ] Timestamps match actual scan time (not simulated)
- [ ] Device count matches real network (not baseline count)

### ❌ Failures (Simulated Data)

- ❌ MACs are masked (`xx:xx:xx:xx:xx:xx`)
- ❌ Vendors are generic (`router-brand`, `desktop`)
- ❌ Detection method is `baseline`
- ❌ Ports are hardcoded expectations
- ❌ All devices have `confidence: 100` (impossible)
- ❌ Data comes from `device-baseline.json`

---

## Integration with HOME SOC

Replace simulated discovery with real:

### Before (Simulated)
```javascript
// home-network-discovery.js
discoverDevices() {
  // Returns data from device-baseline.json
  // All devices present, no detection methods
}
```

### After (Real)
```javascript
// Update home-network-discovery.js to use real-home-discovery.js
import { RealHomeDiscovery } from './real-home-discovery.js';

async discoverDevices() {
  const discovery = new RealHomeDiscovery('192.168.1.0/24');
  const results = await discovery.discover();
  return results; // Real network evidence
}
```

---

## Data Privacy

Real discovery reveals:
- Every device on your network
- MAC addresses (hardware identifiers)
- Open ports (potential entry points)
- Service versions (security posture)

**Store securely:**
- Encrypt inventory files
- Restrict file permissions: `chmod 600 inventory-*.json`
- Do not commit to public repos
- Archive locally for forensics

---

## Troubleshooting

### arp-scan: Permission denied
```bash
sudo arp-scan --localnet --numeric
# or
sudo setcap cap_net_raw=ep /usr/bin/arp-scan
```

### nmap: Not installed
```bash
sudo apt-get install nmap
```

### Router API: Not responding
- Check router supports API (newer routers only)
- Verify network connectivity: `ping 192.168.1.1`
- Check router documentation for API endpoint

### No devices found
- Verify network is active: `ping 192.168.1.100`
- Check subnet is correct: `ip route`
- Confirm ARP is not blocked by firewall

---

## Next: Integration

Once real discovery is working:

1. Update `home-network-discovery.js` to use real results
2. Update `home-soc-brief.js` to parse real inventory
3. Change device status from simulated to actual
4. Store real inventory for change detection
5. Generate real HOME SOC briefs from real network data

---

**Status:** ✅ Real discovery script ready for deployment on actual home network

**Environment Limitation:** Current sandboxed environment has no network access (cannot execute now)

**Next Action:** Deploy `real-home-discovery.js` on your actual home network desktop
