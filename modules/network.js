import { z } from "zod";
import { runCmd, runCmdArgs, runPowerShell, formatResponse, hostSchema } from "./shared.js";

export function registerNetworkTools(server) {
  // 1. IPCONFIG
  server.tool(
    "ipconfig",
    "Display network configuration",
    {
      verbose: z.boolean().optional()
    },
    async ({ verbose = false }) => {
      const cmd = verbose ? "ipconfig /all" : "ipconfig";
      const result = runCmd(cmd);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. NETSTAT
  server.tool(
    "netstat",
    "Display network connections and statistics",
    {
      filter: z.enum(["all", "established", "listening"]).optional()
    },
    async ({ filter = "all" }) => {
      let cmd = "netstat -ano";
      if (filter === "established") cmd += " | findstr ESTABLISHED";
      if (filter === "listening") cmd += " | findstr LISTENING";
      const result = runCmd(cmd);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. ARP
  server.tool(
    "arp",
    "Display ARP cache",
    {},
    async () => {
      const result = runCmd("arp -a");
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. ROUTEPRINT
  server.tool(
    "routePrint",
    "Display routing table",
    {},
    async () => {
      const result = runCmd("route print");
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. DNSCACHE
  server.tool(
    "dnsCache",
    "Display DNS resolver cache",
    {
      action: z.enum(["view", "flush"]).optional()
    },
    async ({ action = "view" }) => {
      let cmd;
      if (action === "view") {
        cmd = "ipconfig /displaydns";
      } else {
        cmd = "ipconfig /flushdns";
      }
      const result = runCmd(cmd);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. PING
  server.tool(
    "ping",
    "Ping a host",
    {
      host: hostSchema,
      count: z.coerce.number().int().min(1).max(20).optional()
    },
    async ({ host, count = 4 }) => {
      // INJ-01: mảng đối số, không dòng lệnh. `host` không bao giờ được cmd.exe đọc.
      const result = runCmdArgs("ping", ["-n", String(count), host]);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. TRACERT
  server.tool(
    "tracert",
    "Trace route to host",
    {
      host: hostSchema
    },
    async ({ host }) => {
      const result = runCmdArgs("tracert", [host]);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. NSLOOKUP
  server.tool(
    "nslookup",
    "DNS lookup",
    {
      host: hostSchema,
      server: hostSchema.optional()
    },
    async ({ host, server }) => {
      const result = runCmdArgs("nslookup", server ? [host, server] : [host]);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. SCANPORT
  server.tool(
    "scanPort",
    "Check if TCP port is open",
    {
      host: hostSchema,
      port: z.coerce.number().int().min(1).max(65535)
    },
    async ({ host, port }) => {
      // INJ-02: `$host`/`$port` do PowerShell đọc từ biến môi trường, không do
      // JavaScript nội suy vào thân script. `$Host` là biến tự động của
      // PowerShell nên tham số đổi tên thành `target`.
      const result = runPowerShell(`
        $result = Test-NetConnection -ComputerName $target -Port ([int]$port) -WarningAction SilentlyContinue;
        @{
          ComputerName = $result.ComputerName;
          RemotePort = $result.RemotePort;
          TcpTestSucceeded = $result.TcpTestSucceeded;
        } | ConvertTo-Json
      `, { target: host, port });
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. ACTIVECONNECTIONS
  server.tool(
    "activeConnections",
    "Get active network connections with process info",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 100 }) => {
      const result = runPowerShell(`
        Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        ForEach-Object {
          $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue;
          @{
            LocalAddress = $_.LocalAddress;
            LocalPort = $_.LocalPort;
            RemoteAddress = $_.RemoteAddress;
            RemotePort = $_.RemotePort;
            State = $_.State;
            ProcessId = $_.OwningProcess;
            ProcessName = $process.Name;
          }
        } |
        Select-Object -First $limit |
        ConvertTo-Json
      `, { limit: String(limit) });
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
