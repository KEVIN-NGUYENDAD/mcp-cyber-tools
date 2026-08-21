# MCP Cyber Tools - 90+ Security Analysis Tools Reference

**Total Tools: 90+ | Status: Production Ready**

---

## Phase 1: Core Analysis (30 Tools) ✓

### Host Enumeration (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `whoami` | Get current user identity | - |
| `hostname` | Get computer hostname | - |
| `systemInfo` | Detailed system information (OS, CPU, RAM) | - |
| `localUsers` | List all local user accounts | - |
| `localAdmins` | List local administrators | - |
| `installedSoftware` | List installed applications | `limit` (default: 50) |
| `sharedFolders` | List shared network resources | - |
| `environmentVars` | Get environment variables | `scope` (User/Machine/Process) |
| `userProfiles` | List all user profiles with SIDs | - |
| `loggedOnUsers` | Get currently logged on users | - |

### Network Analysis (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `ipconfig` | Display network configuration | `verbose` (boolean) |
| `netstat` | Network connections & statistics | `filter` (all/established/listening) |
| `arp` | Display ARP cache | - |
| `routePrint` | Display routing table | - |
| `dnsCache` | Display/flush DNS resolver cache | `action` (view/flush) |
| `ping` | Ping a host | `host`, `count` (default: 4) |
| `tracert` | Trace route to host | `host` |
| `nslookup` | DNS lookup | `host`, `server` (optional) |
| `scanPort` | Check if TCP port is open | `host`, `port` |
| `activeConnections` | Active network connections with process info | `limit` (default: 100) |

### Process Analysis (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `tasklist` | List all running processes | `verbose` (boolean) |
| `processMonitor` | Monitor top 20 processes by memory | - |
| `processDetails` | Get detailed info for specific process | `processId` |
| `processTree` | Display process tree (parent-child) | - |
| `processByPid` | Get process info by PID | `pid` |
| `runningProcesses` | Summary of running processes | `limit` (default: 50) |
| `cpuUsage` | Get top CPU consuming processes | `limit` (default: 10) |
| `memoryUsage` | Get top memory consuming processes | `limit` (default: 10) |
| `topProcesses` | Get top processes by metric | `metric` (memory/cpu/handles), `limit` |
| `suspiciousProcesses` | Find potentially suspicious processes | - |

---

## Phase 2: System Security (25 Tools) ✓

### Services (5 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `servicesChecker` | List all services | - |
| `runningServices` | List running services only | - |
| `stoppedServices` | List stopped services | - |
| `autoStartServices` | List services set to autostart | - |
| `disabledServices` | List disabled services | - |

### Event Logs (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `eventLogs` | Get recent Event Logs | `logName` (System/Application/Security), `count` |
| `securityLogs` | Get Security Event Logs | `count` (default: 100) |
| `systemLogs` | Get System Event Logs | `count` (default: 100) |
| `applicationLogs` | Get Application Event Logs | `count` (default: 100) |
| `failedLogons` | Get failed login attempts (Event 4625) | `count` (default: 50) |
| `successfulLogons` | Get successful login events (Event 4624) | `count` (default: 50) |
| `powershellLogs` | Get PowerShell event logs | `count` (default: 100) |
| `rdpLogs` | Get RDP connection logs | `count` (default: 50) |
| `usbLogs` | Get USB device connection logs | `count` (default: 50) |
| `serviceLogs` | Get service start/stop logs | `count` (default: 50) |

### Firewall (5 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `firewallStatus` | Get Windows Firewall status | - |
| `firewallRules` | List firewall rules | `limit` (default: 100) |
| `inboundRules` | List inbound firewall rules | `limit` (default: 50) |
| `outboundRules` | List outbound firewall rules | `limit` (default: 50) |
| `disabledFirewallRules` | List disabled firewall rules | `limit` (default: 50) |

### Windows Defender (5 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `defenderStatus` | Get Windows Defender status | - |
| `defenderThreats` | Get detected threats | - |
| `defenderHistory` | Get Defender scan history | `limit` (default: 20) |
| `defenderExclusions` | List Defender exclusions | - |
| `defenderQuickScan` | Get quick scan info | - |

---

## Phase 3: Forensics & Persistence (20 Tools) ✓

### Persistence Analysis (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `startupPrograms` | List startup programs | - |
| `startupFolders` | List files in startup folders | - |
| `scheduledTasks` | List scheduled tasks | `limit` (default: 100) |
| `registryRunKeys` | List Registry Run keys | - |
| `registryRunOnce` | List Registry RunOnce keys | - |
| `wmiPersistence` | Check WMI persistence mechanisms | - |
| `servicePersistence` | Check service persistence | - |
| `browserPersistence` | Check browser extensions/plugins | - |
| `dllHijackLocations` | List potential DLL hijacking locations | - |
| `persistenceAudit` | Audit all persistence mechanisms | - |

### File Forensics (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `checkHash` | Calculate SHA256 hash of file | `path` |
| `readLogFile` | Read log file content | `path`, `lines` (default: 100) |
| `fileMetadata` | Get file metadata (timestamps, size, perms) | `path` |
| `recentFiles` | Get recently accessed files | `limit` (default: 50) |
| `downloadsFolder` | List files in Downloads | `limit` (default: 50) |
| `desktopFiles` | List files on Desktop | - |
| `tempFiles` | List files in TEMP directory | `limit` (default: 50) |
| `recycleBin` | List files in Recycle Bin | `limit` (default: 50) |
| `alternateDataStreams` | Find alternate data streams (ADS) | `path` (default: C:\\) |
| `suspiciousExecutables` | Find potentially suspicious executables | `path` |

---

## Phase 4: Threat Hunting & Incident Response (20 Tools) ✓

### Threat Hunting (10 tools)
| Tool | Description | Parameters |
|------|-------------|------------|
| `huntEncodedPowerShell` | Hunt for encoded PowerShell commands | - |
| `huntPersistence` | Hunt for persistence mechanisms | - |
| `huntSuspiciousServices` | Hunt for suspicious services | - |
| `huntSuspiciousTasks` | Hunt for suspicious scheduled tasks | - |
| `huntCredentialDumping` | Hunt for credential dumping attempts | - |
| `huntLateralMovement` | Hunt for lateral movement indicators | - |
| `huntRemoteDesktop` | Hunt for RDP activity and anomalies | - |
| `huntNetworkBeacons` | Hunt for network beacon indicators | - |
| `huntLivingOffTheLand` | Hunt for LOLBins (Living off the Land) | - |
| `huntIndicators` | Hunt for various IOCs | `indicatorType` (suspicious_ports/unusual_binaries/network_anomalies) |

### Incident Response (10 tools)
| Tool | Description | Output |
|------|-------------|--------|
| `collectEvidence` | Collect forensic evidence | JSON Report |
| `collectProcesses` | Collect running processes snapshot | JSON Report |
| `collectServices` | Collect services snapshot | JSON Report |
| `collectNetworkState` | Collect network connections snapshot | JSON Report |
| `collectStartupItems` | Collect startup items & persistence | JSON Report |
| `collectFirewall` | Collect firewall configuration | JSON Report |
| `collectDefender` | Collect Defender status & threats | JSON Report |
| `collectLogs` | Collect relevant event logs | JSON Report |
| `timeline` | Generate incident timeline | JSON Report |
| `securityAudit` | Generate comprehensive security audit | HTML Report |

---

## Report Generation

All Incident Response tools automatically generate reports:
- **JSON Reports**: Raw data in JSON format (for processing)
- **HTML Reports**: Formatted HTML (for viewing/sharing)

Reports are saved to: `./reports/`

---

## Usage Examples

### Basic Host Enumeration
```
whoami                              # Get current user
systemInfo                          # Get system details
localAdmins                         # List administrators
```

### Network Analysis
```
ipconfig[verbose: true]             # Detailed network config
activeConnections[limit: 50]        # Show active network connections
scanPort[host: "192.168.1.1", port: 445]  # Check SMB port
```

### Security Audit
```
defenderStatus                      # Check Defender
firewallStatus                      # Check Firewall
securityAudit                       # Full security audit
```

### Threat Hunting
```
huntEncodedPowerShell              # Hunt for malicious PowerShell
huntPersistence                     # Find persistence mechanisms
huntLivingOffTheLand                # Find LOLBins usage
```

### Incident Response
```
collectEvidence[incidentId: "INC-001"]  # Collect evidence
timeline[days: 7]                       # Generate 7-day timeline
securityAudit[auditType: "full"]       # Full security audit
```

---

## Quick Start

### 1. Start the MCP Server
```bash
node server.js
```

### 2. Register with Claude Desktop
Edit `~/.claude/profiles/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cyber-tools": {
      "command": "node",
      "args": ["C:\\path\\to\\server.js"]
    }
  }
}
```

### 3. Use in Claude
Ask Claude to use any of the 90+ tools for security analysis.

---

## Best Practices

✓ **For Security Audits**: Use `securityAudit` tool
✓ **For Threat Hunting**: Use `hunt*` tools  
✓ **For Incident Response**: Use `collect*` tools
✓ **For Persistence Analysis**: Use `registry*` and `startup*` tools
✓ **For Timeline Analysis**: Use `timeline` tool

---

**Version**: 1.0.0 | **Tools**: 90+ | **Status**: Production Ready
