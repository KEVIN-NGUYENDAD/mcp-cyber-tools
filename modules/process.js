import { z } from "zod";
import { runCmd, runPowerShell, formatResponse } from "./shared.js";

export function registerProcessTools(server) {
  // 1. TASKLIST
  server.tool(
    "tasklist",
    "List all running processes",
    {
      verbose: z.boolean().optional()
    },
    async ({ verbose = false }) => {
      const cmd = verbose ? "tasklist /v" : "tasklist";
      const result = runCmd(cmd);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. PROCESSMONITOR
  server.tool(
    "processMonitor",
    "Monitor process metrics",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Process | Select-Object Name, Id, Handles, @{Name='WorkingSetMB';Expression={[math]::Round($_.WorkingSet/1MB,2)}}, CPU, @{Name='CreationTime';Expression={$_.StartTime}} |
        Sort-Object WorkingSetMB -Descending |
        Select-Object -First 20 |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. PROCESSDETAILS
  server.tool(
    "processDetails",
    "Get detailed info for a specific process",
    {
      processId: z.coerce.number()
    },
    async ({ processId }) => {
      const result = runPowerShell(`
        $proc = Get-Process -Id ${processId} -ErrorAction SilentlyContinue;
        if ($proc) {
          @{
            Name = $proc.Name;
            Id = $proc.Id;
            Path = $proc.Path;
            CommandLine = (Get-WmiObject Win32_Process -Filter "ProcessId=${processId}" -ErrorAction SilentlyContinue).CommandLine;
            Handles = $proc.Handles;
            Threads = $proc.Threads.Count;
            WorkingSetMB = [math]::Round($proc.WorkingSet/1MB,2);
            VirtualMemoryMB = [math]::Round($proc.VirtualMemorySize/1MB,2);
            CPU = $proc.CPU;
            StartTime = $proc.StartTime;
            UserName = (Get-WmiObject Win32_Process -Filter "ProcessId=${processId}" -ErrorAction SilentlyContinue).GetOwner().Domain + '\' + (Get-WmiObject Win32_Process -Filter "ProcessId=${processId}" -ErrorAction SilentlyContinue).GetOwner().User;
          } | ConvertTo-Json
        } else {
          "Process not found"
        }
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. PROCESSTREE
  server.tool(
    "processTree",
    "Display process tree (parent-child relationships)",
    {},
    async () => {
      const result = runPowerShell(`
        Get-WmiObject Win32_Process |
        Select-Object ProcessId, Name, ParentProcessId |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. PROCESSBYPID
  server.tool(
    "processByPid",
    "Get process info by PID",
    {
      pid: z.coerce.number()
    },
    async ({ pid }) => {
      const result = runPowerShell(`
        Get-Process -Id ${pid} -ErrorAction SilentlyContinue |
        Select-Object Name, Id, Path, StartTime, Threads, Handles |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. RUNNINGPROCESSES
  server.tool(
    "runningProcesses",
    "Get summary of running processes",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-Process |
        Sort-Object WorkingSet -Descending |
        Select-Object -First ${limit} Name, Id, WorkingSet, CPU, StartTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. CPUUSAGE
  server.tool(
    "cpuUsage",
    "Get CPU usage by process",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 10 }) => {
      const result = runPowerShell(`
        Get-Process |
        Where-Object { $_.CPU -ne $null } |
        Sort-Object CPU -Descending |
        Select-Object -First ${limit} Name, Id, CPU |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. MEMORYUSAGE
  server.tool(
    "memoryUsage",
    "Get memory usage by process",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 10 }) => {
      const result = runPowerShell(`
        Get-Process |
        Sort-Object WorkingSet -Descending |
        Select-Object -First ${limit} Name, Id, @{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet/1MB,2)}} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. TOPPROCESSES
  server.tool(
    "topProcesses",
    "Get top processes by various metrics",
    {
      metric: z.enum(["memory", "cpu", "handles"]).optional(),
      limit: z.coerce.number().optional()
    },
    async ({ metric = "memory", limit = 10 }) => {
      let sortField;
      if (metric === "memory") sortField = "WorkingSet";
      else if (metric === "cpu") sortField = "CPU";
      else sortField = "Handles";

      const result = runPowerShell(`
        Get-Process |
        Sort-Object ${sortField} -Descending |
        Select-Object -First ${limit} Name, Id, ${sortField} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. SUSPICIOUSPROCESSES
  server.tool(
    "suspiciousProcesses",
    "Find potentially suspicious processes",
    {},
    async () => {
      const result = runPowerShell(`
        $suspicious = @('svchost', 'wmiprvse', 'rundll32', 'regsvcs', 'regasm', 'InstallUtil', 'regsvr32');
        Get-Process |
        Where-Object { $_.Name -in $suspicious -or $_.Name -like '*temp*' -or $_.Name -like '*tmp*' } |
        Select-Object Name, Id, Path, StartTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
