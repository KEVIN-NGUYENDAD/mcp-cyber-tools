import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerEventLogsTools(server) {
  // 1. EVENTLOGS
  server.tool(
    "eventLogs",
    "Get recent Event Logs",
    {
      logName: z.enum(["System", "Application", "Security"]).optional(),
      count: z.coerce.number().optional()
    },
    async ({ logName = "System", count = 50 }) => {
      const result = runPowerShell(`Get-WinEvent -LogName '${logName}' -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. SECURITYLOGS
  server.tool(
    "securityLogs",
    "Get Security Event Logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 100 }) => {
      const result = runPowerShell(`Get-WinEvent -LogName 'Security' -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message | ConvertTo-Json -Depth 5`);

      if (result.success && result.data) {
        try {
          const parsed = JSON.parse(result.data);
          const sliced = Array.isArray(parsed) ? parsed.slice(0, 3) : [parsed];
          console.log("🔍 securityLogs: Returning", sliced.length, "items (SMALL PAYLOAD TEST)");
          return formatResponse(true, JSON.stringify(sliced, null, 2), null);
        } catch (e) {
          console.log("❌ securityLogs: Parse error:", e.message);
          return formatResponse(false, null, "JSON parse error: " + e.message);
        }
      }

      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. SYSTEMLOGS
  server.tool(
    "systemLogs",
    "Get System Event Logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 100 }) => {
      const result = runPowerShell(`Get-WinEvent -LogName 'System' -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. APPLICATIONLOGS
  server.tool(
    "applicationLogs",
    "Get Application Event Logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 100 }) => {
      const result = runPowerShell(`Get-WinEvent -LogName 'Application' -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. FAILEDLOGONS
  server.tool(
    "failedLogons",
    "Get failed login attempts",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 50 }) => {
      const result = runPowerShell(`Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. SUCCESSFULLOGONS
  server.tool(
    "successfulLogons",
    "Get successful login events",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 50 }) => {
      const result = runPowerShell(`Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. POWERSHELLLOGS
  server.tool(
    "powershellLogs",
    "Get PowerShell event logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 100 }) => {
      const result = runPowerShell(`Get-WinEvent -FilterHashtable @{LogName='Windows PowerShell'} -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. RDPLOGS
  server.tool(
    "rdpLogs",
    "Get RDP connection logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 50 }) => {
      // Log Security doi quyen nang cao va thuong dong. Log
      // TerminalServices-LocalSessionManager ghi chinh cac phien RDP va doc
      // duoc khong can nang quyen — nen tool nay hoi ca hai, danh dau nguon.
      // Rong o day chi con nghia "khong co phien RDP nao", chu khong phai
      // "khong nhin duoc".
      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $rows = @(
          Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4778,4779} -MaxEvents ${count} -ErrorAction SilentlyContinue |
          ForEach-Object { [PSCustomObject]@{ TimeCreated = $_.TimeCreated; Id = $_.Id; Source = 'Security'; Fallback = $false; Message = ([string]$_.Message) } }
        ) + @(
          Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TerminalServices-LocalSessionManager/Operational'; Id=21,22,23,24,25,39,40} -MaxEvents ${count} -ErrorAction SilentlyContinue |
          ForEach-Object {
            $msg = [string]$_.Message
            # 'Source Network Address: LOCAL' nghia la dang nhap tai may, khong
            # phai RDP tu xa. Keo ra thanh truong rieng de hai thu do khong con
            # doc giong nhau trong bang tong hop.
            $addr = if ($msg -match 'Source Network Address:\\s*(\\S+)') { $Matches[1] } else { $null }
            [PSCustomObject]@{ TimeCreated = $_.TimeCreated; Id = $_.Id; Source = 'TerminalServices'; Fallback = $true; RemoteAddress = $addr; IsRemote = ($addr -ne $null -and $addr -ne 'LOCAL'); Message = $msg }
          }
        )
        $rows = @($rows | Sort-Object TimeCreated -Descending | Select-Object -First ${count})
        if ($rows.Count -eq 0) { Write-Output '[]' } else { Write-Output ($rows | ConvertTo-Json -Depth 5 -Compress) }
        exit 0
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. USBLOGS
  server.tool(
    "usbLogs",
    "Get USB device connection logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 50 }) => {
      const result = runPowerShell(`Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Disk'} -MaxEvents ${count} -ErrorAction SilentlyContinue | Where-Object { $_.Message -like '*USB*' } | Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. SERVICELOGS
  server.tool(
    "serviceLogs",
    "Get service start/stop logs",
    {
      count: z.coerce.number().optional()
    },
    async ({ count = 50 }) => {
      const result = runPowerShell(`Get-WinEvent -FilterHashtable @{LogName='System'; Id=7034,7035,7036,7040,7045} -MaxEvents ${count} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 5`);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

