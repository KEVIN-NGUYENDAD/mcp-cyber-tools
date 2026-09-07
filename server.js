import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Import Phase 1 modules
import { registerHostTools } from "./modules/host.js";
import { registerNetworkTools } from "./modules/network.js";
import { registerProcessTools } from "./modules/process.js";

// Import Phase 2 modules (placeholders)
import { registerServicesTools } from "./modules/services.js";
import { registerEventLogsTools } from "./modules/eventlogs.js";
import { registerFirewallTools } from "./modules/firewall.js";
import { registerDefenderTools } from "./modules/defender.js";

// Import Phase 3 modules (placeholders)
import { registerPersistenceTools } from "./modules/persistence.js";
import { registerForensicsTools } from "./modules/forensics.js";

// Import Phase 4 modules (placeholders)
import { registerHuntingTools } from "./modules/hunting.js";
import { registerIncidentTools } from "./modules/incident.js";

// Import Event Hub module (Phase E: MCP Interface)
import { registerEventHubTools } from "./modules/eventHub.js";

// Global shutdown handler
let serverConnected = false;
let transportConnected = false;

process.on('exit', (code) => {
  console.error(`[SHUTDOWN-EXIT] Process exit with code: ${code}`);
  console.error(`[SHUTDOWN-STATE] serverConnected=${serverConnected}, transportConnected=${transportConnected}`);
});

process.on('SIGINT', () => {
  console.error('[SHUTDOWN-SIGINT] Received SIGINT signal');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('[SHUTDOWN-SIGTERM] Received SIGTERM signal');
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error('[CRASH-UNCAUGHT-EXCEPTION]', {
    name: err.name,
    message: err.message,
    stack: err.stack,
    code: err.code
  });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[CRASH-UNHANDLED-REJECTION]', {
    reason,
    promise,
    stack: reason?.stack
  });
  process.exit(1);
});

const server = new McpServer({
  name: "cyber-tools",
  version: "1.0.0"
});

console.error("[INIT] Server created");

console.error("Loading Phase 1 modules...");
try {
  registerHostTools(server);
  registerNetworkTools(server);
  registerProcessTools(server);
  console.error("[INIT] Phase 1 modules loaded");
} catch (err) {
  console.error("[INIT-ERROR] Phase 1 failed:", err.message);
  throw err;
}

console.error("Loading Phase 2 modules...");
try {
  registerServicesTools(server);
  registerEventLogsTools(server);
  registerFirewallTools(server);
  registerDefenderTools(server);
  console.error("[INIT] Phase 2 modules loaded");
} catch (err) {
  console.error("[INIT-ERROR] Phase 2 failed:", err.message);
  throw err;
}

console.error("Loading Phase 3 modules...");
try {
  registerPersistenceTools(server);
  registerForensicsTools(server);
  console.error("[INIT] Phase 3 modules loaded");
} catch (err) {
  console.error("[INIT-ERROR] Phase 3 failed:", err.message);
  throw err;
}

console.error("Loading Phase 4 modules...");
try {
  registerHuntingTools(server);
  registerIncidentTools(server);
  console.error("[INIT] Phase 4 modules loaded");
} catch (err) {
  console.error("[INIT-ERROR] Phase 4 failed:", err.message);
  throw err;
}

console.error("Loading Event Hub module...");
try {
  registerEventHubTools(server);
  console.error("[INIT] Event Hub module loaded");
} catch (err) {
  console.error("[INIT-ERROR] Event Hub failed:", err.message);
  throw err;
}

const transport = new StdioServerTransport();
console.error("[INIT] StdioServerTransport created");

try {
  console.error("[CONNECT] Attempting to connect server to transport...");
  await server.connect(transport);
  serverConnected = true;
  transportConnected = true;
  console.error("[CONNECT] Server connected to transport");
} catch (err) {
  console.error("[CONNECT-ERROR] Failed to connect:", {
    name: err.name,
    message: err.message,
    stack: err.stack,
    code: err.code
  });
  process.exit(1);
}

console.error("✓ Cyber Tools MCP Server Started - 90+ Security Analysis Tools Ready");