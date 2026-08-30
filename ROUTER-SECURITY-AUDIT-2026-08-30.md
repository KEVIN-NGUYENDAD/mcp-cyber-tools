# HOME SOC - Router Security Audit Report
**Date**: 2026-08-30  
**Router**: Cox Gateway (ARRIS CGM4331COM)  
**IP**: 192.168.0.1

---

## Executive Summary

✅ **Security Status: GOOD**

Removed 1 high-risk IoT device (camera with Telnet), hardened router by disabling UPnP and MoCA. No port forwarding rules exposed. Firewall in Custom Security mode.

---

## Actions Completed

### 1. Camera Removal ✅
- **Device**: Shenzhen OEM Camera (192.168.0.25)
- **Risks Removed**: 
  - CRITICAL: Telnet (port 23) - unencrypted login
  - HTTP (port 80) - basic auth only
  - RTSP (port 554)
- **Action**: Factory reset → Unplugged
- **Status**: Confirmed DEAD via ping/port scan

### 2. UPnP Disabled ✅
- **Previous**: Enabled (allows devices to auto-open ports)
- **Action**: Advanced > Device Discovery > UPnP: Disable
- **Impact**: Prevents automatic port forwarding misconfigurations

### 3. MoCA Disabled ✅
- **Previous**: Enabled (coax-based home networking)
- **Action**: Gateway > Connection > MoCA: Disable
- **Impact**: Removes potential LAN-to-WAN bridge vulnerability

---

## Network Inventory

### Connected Devices (Active)
| Device | IP | Connection | MAC | Status |
|---|---|---|---|---|
| Desktop | 192.168.0.233 | WiFi 2.4GHz | 9c:b1:50:... | ✅ |
| Laptop | 192.168.0.233 | WiFi 5GHz | 9c:b1:50:... | ✅ |
| iPhone | 192.168.0.XX | WiFi 5GHz | (Apple) | ✅ |
| iPad | 192.168.0.XX | WiFi 5GHz | (Apple) | ✅ |
| Reolink Camera | 192.168.0.21 | Ethernet | ec:71:db:... | ✅ |
| Amazon Echo | 192.168.0.33 | WiFi 2.4GHz | 1c:d6:be:... | ✅ |

### Removed Devices
| Device | IP | Reason |
|---|---|---|
| Shenzhen Camera | 192.168.0.25 | CRITICAL: Telnet port 23 open |

---

## Router Configuration Review

| Setting | Status | Assessment |
|---|---|---|
| **Firewall Level** | Custom Security | ✅ Hardened |
| **Port Forwarding** | None configured | ✅ Good |
| **Remote Management** | Disabled (8080/8181) | ✅ Good |
| **UPnP** | DISABLED | ✅ Good |
| **MoCA** | DISABLED | ✅ Good |
| **HTTP Blocking** | Disabled (port 80/443 open) | ⚠️ Normal |
| **P2P Blocking** | Enabled | ✅ Good |
| **ICMP Blocking** | Enabled | ✅ Good |

---

## Remaining Risks (Minimal)

### Low Risk
- **Reolink Camera MQTT (1883)**: Enabled for app access, but:
  - NOT exposed to Internet (no port forwarding)
  - Behind firewall (LAN only)
  - Can be restricted if needed

### Informational
- **WiFi 2.4GHz + 5GHz active**: Dual-band coverage normal
- **Firmware v23.2**: Check Cox for updates periodically

---

## Recommendations

### Daily Operations
1. ✅ Run weekly network scans to detect new devices
2. ✅ Monitor connected device list in Cox UI
3. ⚠️ Periodically audit open ports (port 1883 from Reolink expected)

### Monthly Maintenance
1. Check for firmware updates from Cox
2. Review Connected Devices for unknown/rogue devices
3. Verify no port forwarding rules appeared

### Annual Review
1. Audit WiFi passwords (recommend change annually)
2. Review firewall rules
3. Check for manufacturer end-of-life on Reolink camera

---

## Daily Scanning Schedule

**Recommendation**: Run `iot-device-scanner.js` daily at **9 PM** (or weekly if daily is too verbose)

**Purpose**: 
- Track device additions/removals
- Alert on new open ports
- Catch security regressions early

**Command**:
```bash
node iot-device-scanner.js > network-scan-$(date +\%Y-\%m-\%d).txt
```

---

## Files Generated

- `network-scan-*.json` - Full device inventory with port details
- `ROUTER-SECURITY-AUDIT-2026-08-30.md` - This report

---

**Report Generated**: 2026-08-30 (End of Day)  
**Next Review**: 2026-09-06 (1 week)  
**Status**: ✅ COMPLETE
