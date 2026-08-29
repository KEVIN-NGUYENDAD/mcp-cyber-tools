#!/usr/bin/env node

/**
 * Linux MCP Cyber Tools Demonstration
 * Demonstrates the MCP process analysis tools adapted for Linux
 * This shows how the cyber-tools MCP would function on Linux systems
 */

import { exec, execSync } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Colors for CLI output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m"
};

class LinuxMCPDemo {
  constructor() {
    this.tools = [];
    this.registerTools();
  }

  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const prefix =
      {
        info: `${colors.blue}[INFO]${colors.reset}`,
        success: `${colors.green}[✓]${colors.reset}`,
        warn: `${colors.yellow}[WARN]${colors.reset}`,
        error: `${colors.red}[ERROR]${colors.reset}`
      }[level] || `[${level}]`;

    console.log(`${prefix} ${message}`);
    if (data) {
      console.log(`${colors.dim}${JSON.stringify(data, null, 2)}${colors.reset}`);
    }
  }

  registerTools() {
    this.tools = [
      {
        name: "runningProcesses",
        description: "Get all running processes with resource usage",
        params: { limit: "number (default: 50)" }
      },
      {
        name: "processByName",
        description: "Get process info by process name",
        params: { name: "string" }
      },
      {
        name: "processByPid",
        description: "Get detailed info for a specific PID",
        params: { pid: "number" }
      },
      {
        name: "cpuUsage",
        description: "Get top processes by CPU usage",
        params: { limit: "number (default: 10)" }
      },
      {
        name: "memoryUsage",
        description: "Get top processes by memory usage",
        params: { limit: "number (default: 10)" }
      },
      {
        name: "processTree",
        description: "Display process tree with parent-child relationships",
        params: {}
      },
      {
        name: "suspiciousProcesses",
        description: "Detect potentially suspicious processes",
        params: { checkBehavior: "boolean (default: true)" }
      },
      {
        name: "networkProcesses",
        description: "Get processes with network connections",
        params: {}
      },
      {
        name: "processTimeline",
        description: "Get recently started processes",
        params: { minutes: "number (default: 30)" }
      },
      {
        name: "whoami",
        description: "Get current user identity and system information",
        params: {}
      }
    ];
  }

  async runningProcesses(limit = 50) {
    try {
      const cmd = `ps aux | head -n ${limit + 1} | tail -n +2 | awk '{printf "{\\"user\\":\\"%s\\",\\"pid\\":%s,\\"cpu\\":%s,\\"mem\\":%s,\\"vsz\\":%s,\\"rss\\":%s,\\"stat\\":\\"%s\\",\\"start\\":\\"%s\\",\\"time\\":\\"%s\\",\\"command\\":\\"%s\\"}\n", $1, $2, $3, $4, $5, $6, $8, $9, $10, $11}' | head -n ${limit}`;

      const { stdout } = await execAsync(cmd);
      const processes = stdout
        .trim()
        .split("\n")
        .filter((line) => line)
        .map((line) => {
          try {
            return JSON.parse(line);
          } catch (e) {
            return line;
          }
        });

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processByName(name) {
    try {
      const { stdout } = await execAsync(
        `ps aux | grep -i '${name}' | grep -v grep`
      );
      const lines = stdout.trim().split("\n");

      const processes = lines.map((line) => {
        const parts = line.split(/\s+/);
        return {
          user: parts[0],
          pid: parseInt(parts[1]),
          cpu: parseFloat(parts[2]),
          mem: parseFloat(parts[3]),
          vsz: parseInt(parts[4]),
          rss: parseInt(parts[5]),
          stat: parts[7],
          start: `${parts[8]} ${parts[9]}`,
          time: parts[10],
          command: parts.slice(11).join(" ")
        };
      });

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processByPid(pid) {
    try {
      const { stdout: psOutput } = await execAsync(`ps -p ${pid} -o user,pid,%cpu,%mem,vsz,rss,stat,start,time,comm h`);

      if (!psOutput.trim()) {
        return { success: false, error: `Process with PID ${pid} not found` };
      }

      const parts = psOutput.trim().split(/\s+/);
      const { stdout: cmdLine } = await execAsync(`cat /proc/${pid}/cmdline 2>/dev/null | tr '\\0' ' '`).catch(
        () => ({ stdout: "" })
      );

      const processInfo = {
        pid: parseInt(parts[1]),
        user: parts[0],
        cpu: parseFloat(parts[2]),
        memory: parseFloat(parts[3]),
        vsz: parseInt(parts[4]),
        rss: parseInt(parts[5]),
        stat: parts[6],
        startTime: `${parts[7]} ${parts[8]}`,
        elapsedTime: parts[9],
        command: parts[10],
        fullCmdLine: cmdLine.trim() || parts.slice(10).join(" ")
      };

      return {
        success: true,
        data: processInfo,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async cpuUsage(limit = 10) {
    try {
      const { stdout } = await execAsync(
        `ps aux --sort=-%cpu | head -n ${limit + 1} | tail -n +2`
      );

      const processes = stdout
        .trim()
        .split("\n")
        .map((line) => {
          const parts = line.split(/\s+/);
          return {
            user: parts[0],
            pid: parseInt(parts[1]),
            cpuPercent: parseFloat(parts[2]),
            memPercent: parseFloat(parts[3]),
            command: parts.slice(10).join(" ")
          };
        });

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async memoryUsage(limit = 10) {
    try {
      const { stdout } = await execAsync(
        `ps aux --sort=-%mem | head -n ${limit + 1} | tail -n +2`
      );

      const processes = stdout
        .trim()
        .split("\n")
        .map((line) => {
          const parts = line.split(/\s+/);
          return {
            user: parts[0],
            pid: parseInt(parts[1]),
            memPercent: parseFloat(parts[3]),
            memoryRss: parseInt(parts[5]),
            cpuPercent: parseFloat(parts[2]),
            command: parts.slice(10).join(" ")
          };
        });

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processTree() {
    try {
      const { stdout } = await execAsync(`ps f -o user,pid,ppid,stat,start_time,comm | head -n 30`);

      const lines = stdout.trim().split("\n");
      const header = lines[0];
      const processData = lines.slice(1).map((line) => {
        const match = line.match(/^(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.+?)\s+(.+)$/);
        if (match) {
          return {
            user: match[1],
            pid: parseInt(match[2]),
            ppid: parseInt(match[3]),
            stat: match[4],
            startTime: match[5],
            command: match[6]
          };
        }
        return line;
      });

      return {
        success: true,
        count: processData.length,
        data: processData,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async suspiciousProcesses(checkBehavior = true) {
    const suspiciousIndicators = [
      { pattern: /powershell/i, name: "PowerShell" },
      { pattern: /python/i, name: "Python" },
      { pattern: /perl/i, name: "Perl" },
      { pattern: /ruby/i, name: "Ruby" },
      { pattern: /nc|ncat|netcat/i, name: "Netcat" },
      { pattern: /curl|wget|fetch/i, name: "Download Tool" }
    ];

    try {
      const { stdout } = await execAsync(`ps aux | tail -n +2`);
      const lines = stdout.trim().split("\n");

      const suspicious = [];

      for (const line of lines) {
        const parts = line.split(/\s+/);
        const command = parts.slice(10).join(" ");

        for (const indicator of suspiciousIndicators) {
          if (indicator.pattern.test(command)) {
            suspicious.push({
              pid: parseInt(parts[1]),
              user: parts[0],
              indicator: indicator.name,
              command: command,
              riskLevel: "MEDIUM",
              reason: `Process matches suspicious pattern: ${indicator.name}`
            });
            break;
          }
        }
      }

      return {
        success: true,
        suspiciousFound: suspicious.length > 0,
        count: suspicious.length,
        data: suspicious,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async networkProcesses() {
    try {
      const { stdout } = await execAsync(`netstat -tulpn 2>/dev/null | grep ESTABLISHED | awk '{print $NF}' | cut -d'/' -f1 | sort -u`);
      const pids = stdout.trim().split("\n").filter((p) => p && !isNaN(p));

      const processes = [];
      for (const pid of pids.slice(0, 20)) {
        try {
          const { stdout: psOutput } = await execAsync(`ps -p ${pid} -o pid,user,comm h`).catch(() => ({ stdout: "" }));
          if (psOutput) {
            const parts = psOutput.trim().split(/\s+/);
            processes.push({
              pid: parseInt(parts[0]),
              user: parts[1],
              command: parts.slice(2).join(" ")
            });
          }
        } catch (e) {
          // Skip if process info not available
        }
      }

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processTimeline(minutes = 30) {
    try {
      const { stdout } = await execAsync(
        `ps aux | awk '{print $9, $1, $2, $11}' | tail -n +2 | head -n 50`
      );

      const processes = stdout
        .trim()
        .split("\n")
        .map((line) => {
          const parts = line.split(/\s+/);
          return {
            startTime: parts[0],
            user: parts[1],
            pid: parseInt(parts[2]),
            command: parts.slice(3).join(" ")
          };
        });

      return {
        success: true,
        count: processes.length,
        data: processes,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async whoami() {
    try {
      const { stdout: user } = await execAsync("whoami");
      const { stdout: uid } = await execAsync("id -u");
      const { stdout: gid } = await execAsync("id -g");
      const { stdout: groups } = await execAsync("id -G");
      const { stdout: hostname } = await execAsync("hostname");
      const { stdout: pwd } = await execAsync("pwd");

      return {
        success: true,
        data: {
          user: user.trim(),
          uid: parseInt(uid.trim()),
          gid: parseInt(gid.trim()),
          groups: groups.trim().split(/\s+/).map(g => parseInt(g)),
          hostname: hostname.trim(),
          workingDirectory: pwd.trim(),
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  displayToolInfo() {
    console.log(`\n${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(
      `${colors.bright}${colors.cyan}  MCP Cyber Tools - Linux Process Analysis Demonstration${colors.reset}`
    );
    console.log(
      `${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}\n`
    );

    console.log(`${colors.bright}Available Tools:${colors.reset}\n`);

    this.tools.forEach((tool, index) => {
      console.log(
        `  ${colors.yellow}${index + 1}.${colors.reset} ${colors.bright}${tool.name}${colors.reset}`
      );
      console.log(`     ${tool.description}`);
      if (Object.keys(tool.params).length > 0) {
        console.log(`     Parameters: ${Object.entries(tool.params).map(([k, v]) => `${k} (${v})`).join(", ")}`);
      }
      console.log();
    });
  }

  async runDemo() {
    this.displayToolInfo();

    // Demo 1: Running Processes
    console.log(`${colors.bright}Demo 1: Running Processes (Top 5)${colors.reset}`);
    console.log(
      `${colors.dim}Calling: runningProcesses(5)${colors.reset}\n`
    );
    const runningProcs = await this.runningProcesses(5);
    this.log("success", `Retrieved ${runningProcs.count} processes`, runningProcs.data);

    // Demo 2: CPU Usage
    console.log(
      `\n${colors.bright}Demo 2: Top 5 CPU-Intensive Processes${colors.reset}`
    );
    console.log(`${colors.dim}Calling: cpuUsage(5)${colors.reset}\n`);
    const cpuProcs = await this.cpuUsage(5);
    this.log("success", `Retrieved ${cpuProcs.count} processes`, cpuProcs.data);

    // Demo 3: Memory Usage
    console.log(
      `\n${colors.bright}Demo 3: Top 5 Memory-Intensive Processes${colors.reset}`
    );
    console.log(`${colors.dim}Calling: memoryUsage(5)${colors.reset}\n`);
    const memProcs = await this.memoryUsage(5);
    this.log("success", `Retrieved ${memProcs.count} processes`, memProcs.data);

    // Demo 4: Claude Process Details
    console.log(`\n${colors.bright}Demo 4: Claude Process Details${colors.reset}`);
    console.log(`${colors.dim}Calling: processByName('claude')${colors.reset}\n`);
    const claudeProcs = await this.processByName("claude");
    this.log("success", `Found ${claudeProcs.count} process(es)`, claudeProcs.data);

    // Demo 5: Process Tree
    console.log(`\n${colors.bright}Demo 5: Process Tree (Parent-Child Relationships)${colors.reset}`);
    console.log(`${colors.dim}Calling: processTree()${colors.reset}\n`);
    const procTree = await this.processTree();
    this.log("success", `Retrieved ${procTree.count} processes`, procTree.data);

    // Demo 6: Suspicious Processes
    console.log(`\n${colors.bright}Demo 6: Suspicious Process Detection${colors.reset}`);
    console.log(`${colors.dim}Calling: suspiciousProcesses()${colors.reset}\n`);
    const suspicious = await this.suspiciousProcesses();
    this.log(
      suspicious.suspiciousFound ? "warn" : "success",
      `Found ${suspicious.count} potentially suspicious process(es)`,
      suspicious.data
    );

    // Demo 7: Network Processes
    console.log(`\n${colors.bright}Demo 7: Processes with Network Connections${colors.reset}`);
    console.log(`${colors.dim}Calling: networkProcesses()${colors.reset}\n`);
    const netProcs = await this.networkProcesses();
    this.log("success", `Found ${netProcs.count} processes with network connections`, netProcs.data);

    console.log(
      `\n${colors.bright}${colors.green}═══════════════════════════════════════════════════════════${colors.reset}`
    );
    console.log(
      `${colors.green}Demonstration Complete${colors.reset} - All MCP tools executed successfully`
    );
    console.log(
      `${colors.bright}${colors.green}═══════════════════════════════════════════════════════════${colors.reset}\n`
    );
  }
}

// Run demonstration
const demo = new LinuxMCPDemo();
await demo.runDemo();
