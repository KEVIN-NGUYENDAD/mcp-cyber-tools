import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerDefenderTools(server) {
  // 1. DEFENDERSTATUS
  server.tool(
    "defenderStatus",
    "Get Windows Defender status",
    {},
    async () => {
      const result = runPowerShell(`
        Get-MpPreference |
        Select-Object DisableRealtimeMonitoring, DisableBehaviorMonitoring, DisableBlockAtFirstSeen, DisableIOAVProtection |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. DEFENDERTHREATS
  server.tool(
    "defenderThreats",
    "Get detected threats",
    {},
    async () => {
      const result = runPowerShell(`
        Get-MpThreat -ErrorAction SilentlyContinue |
        Select-Object Name, Resources, IsActive, ActionsTaken |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. DEFENDERHISTORY
  server.tool(
    "defenderHistory",
    "Get Defender scan history",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 20 }) => {
      const result = runPowerShell(`
        Get-MpComputerStatus |
        Select-Object LastFullScanTime, LastQuickScanTime, AntivirusSignatureLastUpdated, EngineVersion |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. DEFENDEREXCLUSIONS
  server.tool(
    "defenderExclusions",
    "List Defender exclusions",
    {},
    async () => {
      const result = runPowerShell(`
        @{
          FilePathExclusions = (Get-MpPreference).ExclusionPath;
          ProcessExclusions = (Get-MpPreference).ExclusionProcess;
          ExtensionExclusions = (Get-MpPreference).ExclusionExtension;
        } | ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. DEFENDERQUICKSCAN
  server.tool(
    "defenderQuickScan",
    "Get Defender quick scan info",
    {},
    async () => {
      const result = runPowerShell(`
        Get-MpComputerStatus |
        Select-Object LastQuickScanTime, LastQuickScanEndTime, QuickScanSignatureVersion, EngineVersion |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

