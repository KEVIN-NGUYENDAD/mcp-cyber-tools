import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerHuntingTools(server) {
  // 1. HUNTENCODEDPOWERSHELL
  server.tool(
    "huntEncodedPowerShell",
    "Hunt for encoded PowerShell commands",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WinEvent -FilterHashtable @{LogName='Windows PowerShell'; Id=400,600,800} -MaxEvents 100 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'EncodedCommand|FromBase64|DownloadString' } |
        Select-Object TimeCreated, Message |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. HUNTPERSISTENCE
  server.tool(
    "huntPersistence",
    "Hunt for persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(`
        $findings = @();
        $findings += Get-ScheduledTask | Where-Object { $_.TaskPath -notmatch '\\Microsoft\\' };
        $runKeys = Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue;
        if ($runKeys) { $findings += $runKeys | ConvertTo-Json };
        $findings | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. HUNTSUSPICIOUSSERVICES
  server.tool(
    "huntSuspiciousServices",
    "Hunt for suspicious services",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object {
          $_.DisplayName -like '*Remote*' -or
          $_.DisplayName -like '*Update*' -or
          $_.DisplayName -like '*System*' -or
          $_.Name -match '^[a-z]{1,3}' -or
          $_.Path -notmatch 'system32|syswow64|windows'
        } | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. HUNTSUSPICIOUSTASKS
  server.tool(
    "huntSuspiciousTasks",
    "Hunt for suspicious scheduled tasks",
    {},
    async () => {
      const result = runPowerShell(`
        Get-ScheduledTask |
        Where-Object { $_.TaskPath -notmatch '\\Microsoft\\' -and $_.State -ne 'Disabled' } |
        Select-Object TaskName, TaskPath, State |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. HUNTCREDENTIALDUMPING
  server.tool(
    "huntCredentialDumping",
    "Hunt for credential dumping attempts",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'lsass|mimikatz|ntdsutil|registry|sam' } |
        Select-Object TimeCreated, Message |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. HUNTLATERALMOVEMENT
  server.tool(
    "huntLateralMovement",
    "Hunt for lateral movement indicators",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4769,4768} -MaxEvents 500 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'Network|3389|445' } |
        Select-Object TimeCreated, Id, Message |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. HUNTREMOTEDESKTOP
  server.tool(
    "huntRemoteDesktop",
    "Hunt for RDP activity and anomalies",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4648,4778,4779} -MaxEvents 100 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, Message |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. HUNTNETWORKBEACONS
  server.tool(
    "huntNetworkBeacons",
    "Hunt for network beacon indicators",
    {},
    async () => {
      const result = runPowerShell(`
        Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        ForEach-Object {
          $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue;
          @{
            Process = $process.Name;
            RemoteAddress = $_.RemoteAddress;
            RemotePort = $_.RemotePort;
            LocalPort = $_.LocalPort;
          }
        } |
        Where-Object { $_.RemotePort -in @(443,80,8080,53) } |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. HUNTLIVINGOFFTHELND
  server.tool(
    "huntLivingOffTheLand",
    "Hunt for Living off the Land Binaries (LOLBins)",
    {},
    async () => {
      const result = runPowerShell(`
        $lolbins = @('powershell', 'cmd', 'wscript', 'cscript', 'regsvcs', 'regasm', 'msiexec', 'rundll32', 'schtasks', 'certutil');
        Get-Process | Where-Object { $_.Name -in $lolbins } |
        Select-Object Name, Id, Path, StartTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. HUNTINDICATORS
  server.tool(
    "huntIndicators",
    "Hunt for various IOCs (Indicators of Compromise)",
    {
      indicatorType: z.enum(["suspicious_ports", "unusual_binaries", "network_anomalies"]).optional()
    },
    async ({ indicatorType = "suspicious_ports" }) => {
      let command;
      if (indicatorType === "suspicious_ports") {
        command = `
          Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
          Where-Object { $_.RemotePort -in @(4444,5555,6666,7777,8888,9999) } |
          Select-Object LocalAddress, RemoteAddress, RemotePort, OwningProcess
        `;
      } else if (indicatorType === "unusual_binaries") {
        command = `
          Get-Process | Where-Object { $_.Path -like '*temp*' -or $_.Path -like '*appdata*' -or $_.Path -match '\\\\[^\\\\]{1,3}\\\\' } |
          Select-Object Name, Path, Id
        `;
      } else {
        command = `
          Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
          Select-Object RemoteAddress, RemotePort, OwningProcess | Sort-Object RemotePort | Select-Object -Unique
        `;
      }
      const result = runPowerShell(command + " | ConvertTo-Json");
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

