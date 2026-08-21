import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerPersistenceTools(server) {
  // 1. STARTUPPROGRAMS
  server.tool(
    "startupPrograms",
    "List startup programs",
    {},
    async () => {
      const result = runPowerShell(`
        Get-CimInstance Win32_StartupCommand |
        Select-Object Name, Command, Location, User |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. STARTUPFOLDERS
  server.tool(
    "startupFolders",
    "List files in startup folders",
    {},
    async () => {
      const result = runPowerShell(`
        $commonStartup = @(
          "$env:PROGRAMDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
          "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        );
        foreach ($folder in $commonStartup) {
          if (Test-Path $folder) {
            Get-ChildItem $folder -Recurse | Select-Object FullName, LastWriteTime
          }
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. SCHEDULEDTASKS
  server.tool(
    "scheduledTasks",
    "List scheduled tasks",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 100 }) => {
      const result = runPowerShell(`
        Get-ScheduledTask |
        Where-Object { $_.State -ne 'Disabled' } |
        Select-Object TaskName, TaskPath, State, @{Name='LastRun';Expression={$_.LastRunTime}} |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. REGISTRYRUNKEYS
  server.tool(
    "registryRunKeys",
    "List Registry Run keys",
    {},
    async () => {
      const result = runPowerShell(`
        @(
          'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
          'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        ) | ForEach-Object {
          if (Test-Path $_) {
            Get-ItemProperty $_ | ConvertTo-Json
          }
        }
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. REGISTRYRUNONCE
  server.tool(
    "registryRunOnce",
    "List Registry RunOnce keys",
    {},
    async () => {
      const result = runPowerShell(`
        @(
          'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
          'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
        ) | ForEach-Object {
          if (Test-Path $_) {
            Get-ItemProperty $_ | ConvertTo-Json
          }
        }
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. WMIPERSISTENCE
  server.tool(
    "wmiPersistence",
    "Check WMI persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WmiObject __EventFilter -Namespace root\\subscription -ErrorAction SilentlyContinue |
        Select-Object Name, Query |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. SERVICEPERSISTENCE
  server.tool(
    "servicePersistence",
    "Check service persistence",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' } |
        Select-Object Name, DisplayName, StartType, Status |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. BROWSERPERSISTENCE
  server.tool(
    "browserPersistence",
    "Check browser extensions and plugins",
    {},
    async () => {
      const result = runPowerShell(`
        $chromeExt = Get-ChildItem "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Extensions" -ErrorAction SilentlyContinue;
        @{
          ChromeExtensions = ($chromeExt | Select-Object Name).Name;
          InternetExplorerPlugins = (Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue).PSObject.Properties.Name;
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. DLLHIJACKLOCATIONS
  server.tool(
    "dllHijackLocations",
    "List potential DLL hijacking locations",
    {},
    async () => {
      const result = runPowerShell(`
        $locations = @(
          'C:\\Windows\\System32',
          'C:\\Program Files',
          'C:\\Program Files (x86)',
          "$env:TEMP"
        );
        @{
          DLLSearchPaths = $locations;
          ImportantSystemDirs = (Get-ChildItem 'C:\\Windows\\System32' -Filter '*.dll' -ErrorAction SilentlyContinue | Select-Object -First 10).Name;
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. PERSISTENCEAUDIT
  server.tool(
    "persistenceAudit",
    "Audit all persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(`
        @{
          StartupPrograms = (Get-CimInstance Win32_StartupCommand).Count;
          ScheduledTasks = (Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' }).Count;
          RunKeys = (Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue).PSObject.Properties.Count;
          Services = (Get-Service | Where-Object { $_.StartType -eq 'Automatic' }).Count;
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

