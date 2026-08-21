import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerFirewallTools(server) {
  // 1. FIREWALLSTATUS
  server.tool(
    "firewallStatus",
    "Get Windows Firewall status",
    {},
    async () => {
      const result = runPowerShell(`
        Get-NetFirewallProfile |
        Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. FIREWALLRULES
  server.tool(
    "firewallRules",
    "List firewall rules",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 100 }) => {
      const result = runPowerShell(`
        Get-NetFirewallRule -Enabled $true |
        Select-Object Name, DisplayName, Direction, Action, Enabled, @{Name='Protocol';Expression={($_.Protocol -join ',')}} |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. INBOUNDRULES
  server.tool(
    "inboundRules",
    "List inbound firewall rules",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-NetFirewallRule -Direction Inbound -Enabled $true |
        Select-Object Name, DisplayName, Action, Enabled |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. OUTBOUNDRULES
  server.tool(
    "outboundRules",
    "List outbound firewall rules",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-NetFirewallRule -Direction Outbound -Enabled $true |
        Select-Object Name, DisplayName, Action, Enabled |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. DISABLEDFIREWALLRULES
  server.tool(
    "disabledFirewallRules",
    "List disabled firewall rules",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-NetFirewallRule -Enabled $false |
        Select-Object Name, DisplayName, Direction, Action |
        Select-Object -First ${limit} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

