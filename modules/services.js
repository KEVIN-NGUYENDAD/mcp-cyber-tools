import { z } from "zod";
import { runPowerShell, runCmd, formatResponse } from "./shared.js";

export function registerServicesTools(server) {
  // 1. SERVICESCHECKER
  server.tool(
    "servicesChecker",
    "List all services",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service |
        Select-Object Name, DisplayName, Status, StartType |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. RUNNINGSERVICES
  server.tool(
    "runningServices",
    "List running services only",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object { $_.Status -eq 'Running' } |
        Select-Object Name, DisplayName, StartType, ServiceName |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. STOPPEDSERVICES
  server.tool(
    "stoppedServices",
    "List stopped services",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object { $_.Status -eq 'Stopped' } |
        Select-Object Name, DisplayName, StartType |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. AUTOSTARTSERVICES
  server.tool(
    "autoStartServices",
    "List services set to autostart",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object { $_.StartType -eq 'Automatic' } |
        Select-Object Name, DisplayName, Status |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. DISABLEDSERVICES
  server.tool(
    "disabledServices",
    "List disabled services",
    {},
    async () => {
      const result = runPowerShell(`
        Get-Service | Where-Object { $_.StartType -eq 'Disabled' } |
        Select-Object Name, DisplayName, Status |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

