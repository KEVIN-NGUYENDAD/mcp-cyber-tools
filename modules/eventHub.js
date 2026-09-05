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

// Each tool maps onto one of the questions the AI Personal Security
// Manager answers on Claude iPhone/iPad: "what's my current risk?",
// "what changed today?", "what incidents are active?", "what should I
// do next?". Default output is plain text (format: "text"), the same
// rendering daily_brief_generator.py uses for the 8PM brief -- pass
// format: "json" for the structured form instead.
export function registerEventHubTools(server) {
  // 1. GET_SECURITY_SCORE -- "What's my current risk?"
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

  // 2. GET_DAILY_BRIEF -- "What changed today?" / "What should I do next?"
  server.tool(
    "get_daily_brief",
    "Get the SentinelOps Daily Brief for a given date (default today): security score, today's changes, current risk, recommended actions. Plain text by default; format: 'json' for structured data.",
    { date: z.string().optional(), format: z.enum(["text", "json"]).optional() },
    async ({ date, format }) => {
      const args = [];
      if (date) args.push("--date", date);
      if (format) args.push("--format", format);
      const result = runPython("daily_brief_generator.py", args);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. GET_RECENT_INCIDENTS -- "What incidents are active?"
  server.tool(
    "get_recent_incidents",
    "Get incidents recorded in the Daily Brief Store over the last N days (default 7). Plain text by default; format: 'json' for structured data.",
    { days: z.coerce.number().optional(), format: z.enum(["text", "json"]).optional() },
    async ({ days, format }) => {
      const args = ["--incidents"];
      if (days) args.push("--days", String(days));
      if (format) args.push("--format", format);
      const result = runPython("daily_brief_generator.py", args);
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
