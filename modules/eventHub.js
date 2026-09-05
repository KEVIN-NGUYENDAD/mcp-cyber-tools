import { z } from "zod";
import { runCmd, formatResponse } from "./shared.js";

// MCP Interface for the SentinelOps Event Hub (Phase E). Shells out to
// the Phase B/C/D Python scripts (change_detector.py, daily_brief_store.py,
// daily_brief_generator.py, baseline_store.py) via their CLI entry points
// and returns their JSON stdout as-is. No pipeline logic lives here.
function runPython(scriptName, args = []) {
  const quotedArgs = args.map((a) => `"${a}"`).join(" ");
  const command = `python scripts/${scriptName} ${quotedArgs}`.trim();
  return runCmd(command);
}

export function registerEventHubTools(server) {
  // 1. GET_SECURITY_SCORE
  server.tool(
    "get_security_score",
    "Get the SentinelOps security score for a given date (default today)",
    { date: z.string().optional() },
    async ({ date }) => {
      const args = ["--score-only"];
      if (date) args.push("--date", date);
      const result = runPython("daily_brief_generator.py", args);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. GET_DAILY_BRIEF
  server.tool(
    "get_daily_brief",
    "Get the SentinelOps Daily Brief (JSON + plain text) for a given date, default today",
    { date: z.string().optional() },
    async ({ date }) => {
      const args = date ? ["--date", date] : [];
      const result = runPython("daily_brief_generator.py", args);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. GET_RECENT_INCIDENTS
  server.tool(
    "get_recent_incidents",
    "Get incidents recorded in the Daily Brief Store over the last N days (default 7)",
    { days: z.coerce.number().optional() },
    async ({ days }) => {
      const args = ["recent-incidents"];
      if (days) args.push("--days", String(days));
      const result = runPython("daily_brief_store.py", args);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. GET_ASSET_STATUS
  server.tool(
    "get_asset_status",
    "Get the last-known Baseline Store snapshot for a source (e.g. defender_status, device_inventory)",
    { source: z.string() },
    async ({ source }) => {
      const result = runPython("baseline_store.py", ["load", source]);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
