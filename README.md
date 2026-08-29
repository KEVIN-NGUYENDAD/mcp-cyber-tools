# MCP Cyber Tools - Windows SOC/DFIR Analysis Server

A comprehensive **Model Context Protocol (MCP)** server providing 90+ security analysis tools for Windows incident response, threat hunting, and forensics. Built for SOC analysts, DFIR teams, and security researchers.

> **📌 NOTE:** This repository contains **TWO separate MCP servers**:
> - **`cyber-tools`** (this README) — 90+ general Windows security analysis tools
> - **`home-soc`** (see [DEPLOYMENT.md](./DEPLOYMENT.md)) — Home network monitoring + threat prediction (Phase 1-4)
>
> For HOME SOC deployment, see **[DEPLOYMENT.md](./DEPLOYMENT.md)** for detailed setup instructions.

## Features

✅ **90+ Tools** across 4 phases
✅ **Modular Architecture** (host, network, process, services, eventlogs, persistence, defender, firewall, forensics, hunting, incident)
✅ **Report Generation** (JSON, HTML, Audit reports)
✅ **Windows PowerShell Integration** (WMI, registry, event logs)
✅ **Threat Hunting Capabilities** (IOC detection, persistence checking, lateral movement)
✅ **Incident Response Workflows** (evidence collection, timeline generation, security audits)
✅ **Production Ready** (error handling, logging, structured output)

---

## Architecture

```
mcp-cyber-tools/
├── server.js                    # Main MCP server
├── modules/
│   ├── shared.js               # Shared utilities
│   ├── reportGenerator.js       # Report generation
│   ├── host.js                 # 10 host enumeration tools
│   ├── network.js              # 10 network analysis tools
│   ├── process.js              # 10 process analysis tools
│   ├── services.js             # 5 service analysis tools
│   ├── eventlogs.js            # 10 event log tools
│   ├── firewall.js             # 5 firewall tools
│   ├── defender.js             # 5 Windows Defender tools
│   ├── persistence.js          # 10 persistence mechanism tools
│   ├── forensics.js            # 10 forensic analysis tools
│   ├── hunting.js              # 10 threat hunting tools
│   └── incident.js             # 10 incident response tools
├── reports/                     # Generated reports (JSON/HTML)
├── package.json
├── TOOLS_REFERENCE.md          # Complete tools documentation
└── README.md                    # This file
```

---

## Quick Start

### Prerequisites
- Node.js 18+
- Windows 10/11 or Windows Server 2019+
- PowerShell 5.0+
- Claude Desktop app

### Installation

```bash
# Clone/navigate to project
cd mcp-cyber-tools

# Install dependencies
npm install

# Test the server
node server.js
```

### Integration with Claude Desktop

1. Edit `%APPDATA%\Claude\claude_desktop_config.json` (on Windows):

```json
{
  "mcpServers": {
    "cyber-tools": {
      "command": "node",
      "args": ["C:\\mcp-cyber-tools\\server.js"],
      "cwd": "C:\\mcp-cyber-tools"
    }
  }
}
```

**Note:** On Windows, Claude Desktop reads from `%APPDATA%\Claude\claude_desktop_config.json`, NOT `~/.claude/mcp.json`.

2. Restart Claude Desktop
3. Tools will appear in Claude's tool palette

**For HOME SOC deployment,** see [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step MCP registration instructions.

---

## Tool Categories

### Phase 1: Core Analysis (30 tools)

**Host Enumeration (10)**
- System information, user accounts, installed software, environment variables
- Users: `whoami`, `hostname`, `systemInfo`, `localUsers`, `localAdmins`, `installedSoftware`, `sharedFolders`, `environmentVars`, `userProfiles`, `loggedOnUsers`

**Network Analysis (10)**
- Network configuration, connections, DNS, ARP, routing
- Tools: `ipconfig`, `netstat`, `arp`, `routePrint`, `dnsCache`, `ping`, `tracert`, `nslookup`, `scanPort`, `activeConnections`

**Process Analysis (10)**
- Running processes, memory/CPU usage, process trees, suspicious processes
- Tools: `tasklist`, `processMonitor`, `processDetails`, `processTree`, `processByPid`, `runningProcesses`, `cpuUsage`, `memoryUsage`, `topProcesses`, `suspiciousProcesses`

### Phase 2: System Security (25 tools)

**Services (5)** - Service status and configuration
**Event Logs (10)** - Security, system, application, RDP, USB logs
**Firewall (5)** - Firewall rules and status
**Defender (5)** - Malware threats, scan history, exclusions

### Phase 3: Forensics & Persistence (20 tools)

**Persistence (10)** - Registry keys, startup programs, scheduled tasks, WMI, services
**Forensics (10)** - File hashes, metadata, recent files, alternate data streams, temp files

### Phase 4: Threat Hunting & IR (20 tools)

**Hunting (10)** - Encoded PowerShell, suspicious services, credential dumping, network beacons, LOLBins
**Incident Response (10)** - Evidence collection, process/service snapshots, network state, timeline generation, audit reports

---

## Usage Examples

### Get System Information
```
Claude: Run systemInfo tool
→ Returns: OS version, CPU count, RAM, build number, install date
```

### Check Security Status
```
Claude: Check firewall and defender status
→ Returns: Firewall profiles and Defender protection status
```

### Collect Evidence
```
Claude: Collect evidence for incident INC-2024-001
→ Returns: JSON report saved to ./reports/incident_[timestamp].json
```

### Hunt for Threats
```
Claude: Hunt for encoded PowerShell and suspicious services
→ Returns: Found 3 suspicious services and 2 encoded PowerShell commands
```

### Generate Audit Report
```
Claude: Generate a full security audit
→ Returns: HTML report saved to ./reports/audit_[timestamp].html
```

---

## Report Generation

Tools automatically generate reports in the `./reports/` directory:

- **JSON Reports**: Structured data for programmatic processing
- **HTML Reports**: Formatted for viewing in browsers
- **Audit Reports**: Security assessment in tabular format

### Report Types
- `incident_*.json` - Incident response data
- `audit_*.html` - Security audit reports
- `general_*.json` - General analysis data

---

## Configuration

Edit `server.js` to customize:
- Report output directory (default: `./reports/`)
- Module imports (enable/disable phases)
- Server metadata (name, version)

---

## Security Considerations

⚠️ **Requires Administrator Privileges**
- Most tools need admin rights for full functionality
- Run Claude with elevated privileges or the MCP server as admin

⚠️ **Data Sensitivity**
- Reports may contain sensitive system information
- Store reports securely
- Don't share reports without proper authorization

⚠️ **Incident Response**
- Tools are designed for authorized security analysis only
- Use only on systems you own or have explicit permission to analyze
- Follow your organization's incident response procedures

---

## Troubleshooting

### Server Won't Start
```bash
# Check Node.js version
node --version  # Should be 18+

# Check dependencies
npm install

# Run with verbose output
node server.js 2>&1
```

### Tools Not Appearing in Claude
1. Check `claude_desktop_config.json` path is correct
2. Restart Claude Desktop completely
3. Verify server.js runs without errors: `node server.js`

### PowerShell Execution Errors
```powershell
# Check PowerShell execution policy
Get-ExecutionPolicy

# Set if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Permission Denied Errors
- Run as Administrator
- Check file/registry permissions for target paths

---

## Contributing

To add new tools:

1. Create/edit a module file (e.g., `modules/custom.js`)
2. Implement `registerCustomTools(server)` function
3. Import in `server.js`
4. Update `TOOLS_REFERENCE.md`

Example module structure:
```javascript
import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerCustomTools(server) {
  server.tool(
    "toolName",
    "Description",
    { param1: z.string() },
    async ({ param1 }) => {
      const result = runPowerShell("your-command");
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
```

---

## Performance Notes

- Network tools may timeout on unreachable hosts (60s default)
- Event log queries limited to prevent memory issues
- Process monitoring excludes system processes by default
- Report generation may take 1-2 seconds for large datasets

---

## Roadmap

- [ ] Remote system analysis support
- [ ] Machine learning-based anomaly detection
- [ ] Database storage for historical reports
- [ ] Web dashboard for report viewing
- [ ] MITRE ATT&CK framework mapping
- [ ] Integration with threat intelligence feeds

---

## License

ISC License

---

## Support

For issues, feature requests, or improvements:
1. Check `TOOLS_REFERENCE.md` for usage examples
2. Review error messages in server output
3. Verify tool parameters match documentation
4. Test tool independently before reporting

---

**Version**: 1.0.0
**Status**: Production Ready ✓
**Tools**: 90+ Security Analysis Tools
**Modules**: 11 (Host, Network, Process, Services, EventLogs, Firewall, Defender, Persistence, Forensics, Hunting, Incident)
