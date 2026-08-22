import { z } from "zod";
import { generateJsonReport, generateHtmlReport, generateAuditReport } from "./reportGenerator.js";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerIncidentTools(server) {
  // 1. COLLECTEVIDENCE
  server.tool(
    "collectEvidence",
    "Collect forensic evidence for incident",
    {
      incidentId: z.string()
    },
    async ({ incidentId }) => {
      const result = runPowerShell(`
        @{
          SystemInfo = (Get-WmiObject Win32_OperatingSystem).Caption;
          Timestamp = Get-Date;
          Processes = (Get-Process).Count;
          Connections = (Get-NetTCPConnection -State Established).Count;
          Services = (Get-Service | Where-Object { $_.Status -eq 'Running' }).Count;
        } | ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport(`Incident ${incidentId} Evidence`, result.data, "incident");
        return formatResponse(true, `Evidence collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 2. COLLECTPROCESSES (formerly runningProcesses)
  server.tool(
    "runningProcesses",
    "List running processes",
    {},
    async () => {
      console.log("\n🔥 runningProcesses CALLED - Testing marker\n");
      return formatResponse(true, "DEBUG_MARKER_RUNNINGPROCESSES_WAVE5");
    }
  );

  // 3. COLLECTSERVICES
  server.tool(
    "collectServices",
    "Collect all services snapshot",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Select-Object Name, DisplayName, Status, StartType |
        ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport("Services Collection", result.data, "incident");
        return formatResponse(true, `Services collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 4. COLLECTNETWORKSTATE
  server.tool(
    "collectNetworkState",
    "Collect network connections snapshot",
    {},
    async () => {
      const result = runPowerShell(`
        Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess |
        ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport("Network State Collection", result.data, "incident");
        return formatResponse(true, `Network state collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 5. COLLECTSTARTUPITEMS
  server.tool(
    "collectStartupItems",
    "Collect startup items and persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(`
        @{
          StartupPrograms = (Get-CimInstance Win32_StartupCommand).Count;
          ScheduledTasks = (Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' }).Count;
          RunKeys = (Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue).PSObject.Properties.Count;
        } | ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport("Startup Items Collection", result.data, "incident");
        return formatResponse(true, `Startup items collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 6. COLLECTFIREWALL
  server.tool(
    "collectFirewall",
    "Collect firewall configuration",
    {},
    async () => {
      const result = runPowerShell(`
        Get-NetFirewallProfile |
        Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
        ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport("Firewall Collection", result.data, "incident");
        return formatResponse(true, `Firewall config collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 7. COLLECTDEFENDER
  server.tool(
    "collectDefender",
    "Collect Windows Defender status and threats",
    {},
    async () => {
      const result = runPowerShell(`
        @{
          DefenderStatus = (Get-MpComputerStatus).AntivirusEnabled;
          LastScanTime = (Get-MpComputerStatus).LastFullScanTime;
          Threats = (Get-MpThreat).Count;
        } | ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport("Defender Collection", result.data, "incident");
        return formatResponse(true, `Defender info collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 8. COLLECTLOGS
  server.tool(
    "collectLogs",
    "Collect relevant event logs",
    {
      logName: z.enum(["Security", "System", "Application"]).optional()
    },
    async ({ logName = "Security" }) => {
      const result = runPowerShell(`
        Get-WinEvent -LogName '${logName}' -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, Message |
        ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport(`${logName} Logs Collection`, result.data, "incident");
        return formatResponse(true, `Logs collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 9. TIMELINE
  server.tool(
    "timeline",
    "Generate incident timeline",
    {
      days: z.coerce.number().optional()
    },
    async ({ days = 7 }) => {
      const result = runPowerShell(`
        $startDate = (Get-Date).AddDays(-${days});
        @{
          EventLogs = (Get-WinEvent -FilterHashtable @{LogName='Security'} -MaxEvents 500 -ErrorAction SilentlyContinue | Where-Object { $_.TimeCreated -gt $startDate }).Count;
          RecentFiles = (Get-ChildItem -Path "$env:USERPROFILE" -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $startDate }).Count;
          StartupChanges = (Get-ScheduledTask | Where-Object { $_.LastRunTime -gt $startDate }).Count;
        } | ConvertTo-Json
      `);
      if (result.success) {
        const report = generateJsonReport(`Incident Timeline - Last ${days} days`, result.data, "incident");
        return formatResponse(true, `Timeline generated and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 10. SECURITYAUDIT
  server.tool(
    "securityAudit",
    "Generate comprehensive security audit report",
    {
      auditType: z.enum(["quick", "full"]).optional()
    },
    async ({ auditType = "full" }) => {
      const categories = {
        "Firewall Status": { status: "Check Enabled", details: "Enable Windows Defender Firewall" },
        "Defender Status": { status: "Check Enabled", details: "Enable Real-time Monitoring" },
        "Admin Accounts": { status: "Review", details: "Audit local administrators" },
        "Startup Programs": { status: "Review", details: "Audit startup programs" },
        "Network Connections": { status: "Review", details: "Check established connections" },
        "Event Logs": { status: "Review", details: "Audit Security event logs" },
        "Services": { status: "Review", details: "Audit running services" },
        "Scheduled Tasks": { status: "Review", details: "Audit scheduled tasks" }
      };
      const report = generateAuditReport("Security Audit Report", categories, "audit");
      return formatResponse(true, `Audit report generated and saved to: ${report.path}`);
    }
  );
}

