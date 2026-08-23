import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { instrumentTool, TelemetryEngine } from "./modules/telemetry.js";

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

const server = new McpServer({
  name: "cyber-tools",
  version: "1.0.0"
});

// Initialize telemetry engine (creates telemetry directory)
const telemetryEngine = new TelemetryEngine();

// Wrap server.tool to automatically instrument all tools
const originalTool = server.tool.bind(server);
server.tool = (name, description, schema, handler) => {
  return originalTool(name, description, schema, instrumentTool(name, handler));
};

console.error("Loading Phase 1 modules...");
registerHostTools(server);
registerNetworkTools(server);
registerProcessTools(server);

console.error("Loading Phase 2 modules...");
registerServicesTools(server);
registerEventLogsTools(server);
registerFirewallTools(server);
registerDefenderTools(server);

console.error("Loading Phase 3 modules...");
registerPersistenceTools(server);
registerForensicsTools(server);

console.error("Loading Phase 4 modules...");
registerHuntingTools(server);
registerIncidentTools(server);

const transport = new StdioServerTransport();

await server.connect(transport);

console.error("✓ Cyber Tools MCP Server Started - 90+ Security Analysis Tools Ready");