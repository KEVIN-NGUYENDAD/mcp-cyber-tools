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

const server = new McpServer({
  name: "cyber-tools",
  version: "1.0.0"
});

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

console.error("Loading Event Hub module...");
registerEventHubTools(server);

const transport = new StdioServerTransport();

await server.connect(transport);

console.error("✓ Cyber Tools MCP Server Started - 90+ Security Analysis Tools Ready");