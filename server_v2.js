import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import fs from "fs";
import { execSync } from "child_process";

const server = new McpServer({
  name: "cyber-tools",
  version: "1.0.0"
});

// READ LOG FILE
server.tool(
  "readLogFile",
  "Read a log file",
  {
    path: z.string()
  },
  async ({ path }) => {
    try {
      const content = fs.readFileSync(path, "utf8");

      return {
        content: [
          {
            type: "text",
            text: content
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: `ERROR: ${err.message}`
          }
        ]
      };
    }
  }
);

// CHECK HASH
server.tool(
  "checkHash",
  "Get SHA256 hash",
  {
    path: z.string()
  },
  async ({ path }) => {
    try {
      const output = execSync(
        `powershell Get-FileHash -Algorithm SHA256 "${path}"`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// SCAN PORT
server.tool(
  "scanPort",
  "Check TCP port",
  {
    host: z.string(),
    port: z.coerce.number()
  },
  async ({ host, port }) => {
    try {
      const output = execSync(
        `powershell Test-NetConnection -ComputerName ${host} -Port ${port}`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// NSLOOKUP
server.tool(
  "nslookup",
  "DNS Lookup",
  {
    host: z.string()
  },
  async ({ host }) => {
    try {
      const output = execSync(
        `nslookup ${host}`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// PING
server.tool(
  "ping",
  "Ping Host",
  {
    host: z.string()
  },
  async ({ host }) => {
    try {
      const output = execSync(
        `ping ${host}`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// TRACERT
server.tool(
  "tracert",
  "Trace Route",
  {
    host: z.string()
  },
  async ({ host }) => {
    try {
      const output = execSync(
        `tracert ${host}`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// IPCONFIG
server.tool(
  "ipconfig",
  "Network Configuration",
  {},
  async () => {
    try {
      const output = execSync(
        `ipconfig /all`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// NETSTAT
server.tool(
  "netstat",
  "Network Connections",
  {},
  async () => {
    try {
      const output = execSync(
        `netstat -ano`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// TASKLIST
server.tool(
  "tasklist",
  "Running Processes",
  {},
  async () => {
    try {
      const output = execSync(
        `tasklist`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// SERVICES
server.tool(
  "servicesChecker",
  "List Services",
  {},
  async () => {
    try {
      const output = execSync(
        `sc query`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// EVENT LOGS
server.tool(
  "eventLogs",
  "Windows Event Logs",
  {
    count: z.coerce.number()
  },
  async ({ count }) => {
    try {
      const output = execSync(
        `powershell Get-EventLog -LogName System -Newest ${count}`
      ).toString();

      return {
        content: [
          {
            type: "text",
            text: output
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

// PROCESS MONITOR
server.tool(
  "processMonitor",
  "Node Memory Statistics",
  {},
  async () => {
    try {
      const mem = process.memoryUsage();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(mem, null, 2)
          }
        ]
      };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: err.message
          }
        ]
      };
    }
  }
);

const transport = new StdioServerTransport();

await server.connect(transport);

console.error("Cyber Tools MCP Server Started");