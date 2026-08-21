import { z } from "zod";
import { runCmd, runPowerShell, formatResponse } from "./shared.js";

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
      host: z.string(),
      count: z.coerce.number().optional()
    },
    async ({ host, count = 4 }) => {
      const result = runCmd(`ping -n ${count} ${host}`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. TRACERT
  server.tool(
    "tracert",
    "Trace route to host",
    {
      host: z.string()
    },
    async ({ host }) => {
      const result = runCmd(`tracert ${host}`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. NSLOOKUP
  server.tool(
    "nslookup",
    "DNS lookup",
    {
      host: z.string(),
      server: z.string().optional()
    },
    async ({ host, server }) => {
      const cmd = server ? `nslookup ${host} ${server}` : `nslookup ${host}`;
      const result = runCmd(cmd);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. SCANPORT
  server.tool(
    "scanPort",
    "Check if TCP port is open",
    {
      host: z.string(),
      port: z.coerce.number()
    },
    async ({ host, port }) => {
      const result = runPowerShell(`
        $result = Test-NetConnection -ComputerName ${host} -Port ${port} -WarningAction SilentlyContinue;
        @{
          ComputerName = $result.ComputerName;
          RemotePort = $result.RemotePort;
          TcpTestSucceeded = $result.TcpTestSucceeded;
        } | ConvertTo-Json
      `);
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
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
