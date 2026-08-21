import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerHostTools(server) {
  // 1. WHOAMI
  server.tool(
    "whoami",
    "Get current user identity",
    {},
    async () => {
      const result = runPowerShell("[System.Security.Principal.WindowsIdentity]::GetCurrent().Name");
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. HOSTNAME
  server.tool(
    "hostname",
    "Get computer hostname",
    {},
    async () => {
      const result = runPowerShell("[System.Net.Dns]::GetHostName()");
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. SYSTEMINFO
  server.tool(
    "systemInfo",
    "Get detailed system information",
    {},
    async () => {
      const result = runPowerShell(`
        $os = Get-WmiObject Win32_OperatingSystem;
        $cs = Get-WmiObject Win32_ComputerSystem;
        @{
          OSVersion = $os.Version;
          OSCaption = $os.Caption;
          BuildNumber = $os.BuildNumber;
          ComputerName = $cs.Name;
          Manufacturer = $cs.Manufacturer;
          Model = $cs.Model;
          TotalMemoryGB = [math]::Round($cs.TotalPhysicalMemory / 1GB);
          CPUCount = $cs.NumberOfProcessors;
          InstallDate = $os.InstallDate;
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. LOCALUSERS
  server.tool(
    "localUsers",
    "List all local user accounts",
    {},
    async () => {
      const result = runPowerShell(`
        Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. LOCALADMINS
  server.tool(
    "localAdmins",
    "List all local administrators",
    {},
    async () => {
      const result = runPowerShell(`
        Get-LocalGroupMember -Group "Administrators" | Select-Object Name, ObjectClass | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. INSTALLEDSOFTWARE
  server.tool(
    "installedSoftware",
    "List installed software",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
        Select-Object DisplayName, DisplayVersion, Publisher, InstallDate -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -ne $null } |
        Sort-Object DisplayName |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. SHAREDFOLDERSLOCAL
  server.tool(
    "sharedFolders",
    "List shared network resources",
    {},
    async () => {
      const result = runPowerShell(`
        Get-SmbShare | Select-Object Name, Path, Description | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. ENVIRONMENTVARS
  server.tool(
    "environmentVars",
    "Get environment variables",
    {
      scope: z.enum(["User", "Machine", "Process"]).optional()
    },
    async ({ scope = "Process" }) => {
      const result = runPowerShell(`
        [Environment]::GetEnvironmentVariables([System.EnvironmentVariableTarget]::${scope}) |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. USERPROFILES
  server.tool(
    "userProfiles",
    "List all user profiles on system",
    {},
    async () => {
      const result = runPowerShell(`
        Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList' |
        Where-Object { $_.PSChildName -like 'S-1-5-21*' } |
        Select-Object @{Name='SID';Expression={$_.PSChildName}}, @{Name='ProfilePath';Expression={$_.ProfilePath}} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. LOGGEDONUSERS
  server.tool(
    "loggedOnUsers",
    "Get currently logged on users",
    {},
    async () => {
      const result = runPowerShell(`
        quser 2>$null | ConvertFrom-String | Select-Object P1, P2, P3, P4 | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
