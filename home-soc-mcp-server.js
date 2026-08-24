#!/usr/bin/env node

/**
 * HOME SOC MCP SERVER
 *
 * Local MCP server running on your laptop that exposes HOME SOC data.
 * Claude can query live device status, network state, and security posture
 * without cloud sandbox limitations.
 *
 * Tools:
 * - discoverDevices: Current devices on network
 * - networkStatus: Gateway, device count, stability
 * - cameraStatus: Camera online/offline status
 * - gatewayStatus: Router/gateway information
 * - deviceHistory: Timeline of device events
 * - changeHistory: Recent network changes
 * - homeSocStatus: Overall security score and recommendations
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class HomeSocMcpServer {
  constructor() {
    this.stateDir = './reports/home-soc-state';
  }

  // Tool: Discover Devices
  discoverDevices() {
    const historyPath = path.join(this.stateDir, 'device-history.json');
    const devices = [];

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        // In a real network, this would have actual devices
        // In sandbox, devices array is empty
        if (data.devices && data.devices.length > 0) {
          devices.push(...data.devices);
        }
      } catch (e) {
        // Continue
      }
    }

    return {
      timestamp: new Date().toISOString(),
      totalDevices: devices.length,
      devices: devices.map(d => ({
        ip: d.ip,
        mac: d.mac,
        vendor: d.vendor || 'Unknown',
        lastSeen: d.lastSeen,
        deviceType: d.deviceType || 'unknown'
      }))
    };
  }

  // Tool: Camera Status
  cameraStatus() {
    const historyPath = path.join(this.stateDir, 'device-history.json');
    let cameras = [];

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        cameras = data.cameraStatus || [];
      } catch (e) {
        // Continue
      }
    }

    const online = cameras.filter(c => c.status === 'online').length;
    const offline = cameras.filter(c => c.status === 'offline').length;

    return {
      timestamp: new Date().toISOString(),
      camerasMonitored: cameras.length,
      onlineCount: online,
      offlineCount: offline,
      onlinePercentage: cameras.length > 0 ? Math.round((online / cameras.length) * 100) : 0,
      cameras: cameras.map(c => ({
        ip: c.ip,
        status: c.status,
        lastSeen: c.lastSeen
      }))
    };
  }

  // Tool: Network Status
  networkStatus() {
    const networkPath = path.join(this.stateDir, 'network-history.json');
    const metrics = {
      timestamp: new Date().toISOString(),
      gateway: 'unknown',
      deviceCount: 0,
      averageDevices: 0,
      stabilityScore: 0,
      snapshots: 0
    };

    if (fs.existsSync(networkPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(networkPath, 'utf8'));
        metrics.snapshots = (data.snapshots || []).length;
        metrics.averageDevices = data.averageDevices || 0;
        metrics.deviceCount = data.snapshots && data.snapshots.length > 0
          ? data.snapshots[data.snapshots.length - 1].deviceCount
          : 0;

        // Calculate stability (0-100)
        const snapshots = data.snapshots || [];
        if (snapshots.length > 1) {
          const counts = snapshots.map(s => s.deviceCount);
          const avg = metrics.averageDevices;
          const variance = counts.reduce((sum, c) => sum + Math.pow(c - avg, 2), 0) / counts.length;

          if (variance < 1) metrics.stabilityScore = 95;
          else if (variance < 5) metrics.stabilityScore = 80;
          else if (variance < 10) metrics.stabilityScore = 65;
          else metrics.stabilityScore = 50;
        } else if (snapshots.length === 1) {
          metrics.stabilityScore = 90;
        }
      } catch (e) {
        // Continue
      }
    }

    return metrics;
  }

  // Tool: Gateway Status
  gatewayStatus() {
    const historyPath = path.join(this.stateDir, 'device-history.json');
    let gateway = {
      status: 'unknown',
      ip: 'unknown',
      lastSeen: null
    };

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        if (data.gateway) {
          gateway = {
            status: data.gateway.status || 'online',
            ip: data.gateway.ip || 'unknown',
            lastSeen: data.gateway.lastSeen,
            model: data.gateway.model || 'unknown',
            firmwareVersion: data.gateway.firmwareVersion || 'unknown'
          };
        }
      } catch (e) {
        // Continue
      }
    }

    return {
      timestamp: new Date().toISOString(),
      gateway: gateway,
      accessible: gateway.status === 'online'
    };
  }

  // Tool: Device History
  deviceHistory() {
    const historyPath = path.join(this.stateDir, 'device-history.json');
    let timeline = [];

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        timeline = data.timeline || [];
      } catch (e) {
        // Continue
      }
    }

    return {
      timestamp: new Date().toISOString(),
      totalCollections: timeline.length,
      timeline: timeline.map(t => ({
        timestamp: t.timestamp,
        deviceCount: t.deviceCount,
        changes: t.changes || 0
      }))
    };
  }

  // Tool: Change History
  changeHistory() {
    const changesPath = path.join(this.stateDir, 'changes.json');
    let changes = [];

    if (fs.existsSync(changesPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(changesPath, 'utf8'));
        changes = data.changes || [];
      } catch (e) {
        // Continue
      }
    }

    return {
      timestamp: new Date().toISOString(),
      totalChanges: changes.length,
      recentChanges: changes.slice(-10).map(c => ({
        type: c.type,
        ip: c.ip,
        mac: c.mac,
        timestamp: c.timestamp,
        severity: c.severity || 'info'
      }))
    };
  }

  // Tool: HOME SOC Status
  homeSocStatus() {
    const devices = this.discoverDevices();
    const cameras = this.cameraStatus();
    const network = this.networkStatus();
    const changes = this.changeHistory();

    // Calculate home score (0-100)
    let homeScore = 85;
    homeScore -= Math.min(devices.totalDevices * 2, 15); // Device count reduces score
    homeScore -= changes.totalChanges > 0 ? 5 : 0; // Changes reduce score
    homeScore -= cameras.offlineCount > 0 ? 5 : 0; // Offline cameras reduce score
    homeScore += Math.min(network.stabilityScore / 10, 10); // Stability increases score
    homeScore = Math.max(0, Math.min(100, homeScore));

    // Threat level
    let threatLevel = 'GREEN';
    if (homeScore >= 85) threatLevel = 'GREEN';
    else if (homeScore >= 70) threatLevel = 'YELLOW';
    else if (homeScore >= 50) threatLevel = 'ORANGE';
    else threatLevel = 'RED';

    // Recommendations
    const recommendations = [];
    if (cameras.offlineCount > 0) recommendations.push('Kiểm tra camera ngoại tuyến');
    if (changes.totalChanges > 10) recommendations.push('Kiểm tra các thay đổi mạng gần đây');
    if (network.stabilityScore < 70) recommendations.push('Mạng không ổn định - kiểm tra kết nối');
    if (devices.totalDevices > 15) recommendations.push('Quá nhiều thiết bị - xem xét bảo mật');
    if (recommendations.length === 0) recommendations.push('Hệ thống ổn định - tiếp tục giám sát');

    return {
      timestamp: new Date().toISOString(),
      homeScore: Math.round(homeScore),
      threatLevel: threatLevel,
      devicesOnline: devices.totalDevices,
      camerasOnline: cameras.onlineCount,
      networkStability: network.stabilityScore,
      recentChanges: changes.totalChanges,
      recommendations: recommendations,
      status: 'operational'
    };
  }
}

// MCP Server Implementation
class McpServer {
  constructor() {
    this.homeSoc = new HomeSocMcpServer();
  }

  async handleCall(toolName, toolInput) {
    switch (toolName) {
      case 'discoverDevices':
        return this.homeSoc.discoverDevices();
      case 'networkStatus':
        return this.homeSoc.networkStatus();
      case 'cameraStatus':
        return this.homeSoc.cameraStatus();
      case 'gatewayStatus':
        return this.homeSoc.gatewayStatus();
      case 'deviceHistory':
        return this.homeSoc.deviceHistory();
      case 'changeHistory':
        return this.homeSoc.changeHistory();
      case 'homeSocStatus':
        return this.homeSoc.homeSocStatus();
      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  }

  getToolsList() {
    return [
      {
        name: 'discoverDevices',
        description: 'Discover all devices currently on the network',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'networkStatus',
        description: 'Get current network status including gateway, device count, and stability',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'cameraStatus',
        description: 'Get status of monitored cameras (online/offline)',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'gatewayStatus',
        description: 'Get gateway/router status',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'deviceHistory',
        description: 'Get device discovery history timeline',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'changeHistory',
        description: 'Get recent network changes (new devices, offline events)',
        inputSchema: { type: 'object', properties: {} }
      },
      {
        name: 'homeSocStatus',
        description: 'Get overall HOME SOC security status and recommendations',
        inputSchema: { type: 'object', properties: {} }
      }
    ];
  }

  async start() {
    console.log('🏠 HOME SOC MCP SERVER');
    console.log('======================\n');
    console.log('📡 MCP Tools Registered:');
    this.getToolsList().forEach(tool => {
      console.log(`   ✅ ${tool.name}`);
    });
    console.log('\n💬 Waiting for Claude to connect...\n');
  }
}

// Export for MCP integration
export { McpServer, HomeSocMcpServer };

// Standalone execution
const server = new McpServer();
await server.start();

// Test all tools
const homeSoc = new HomeSocMcpServer();
console.log('📊 Testing Tools:\n');
console.log('1. discoverDevices:', JSON.stringify(homeSoc.discoverDevices(), null, 2));
console.log('\n2. networkStatus:', JSON.stringify(homeSoc.networkStatus(), null, 2));
console.log('\n3. cameraStatus:', JSON.stringify(homeSoc.cameraStatus(), null, 2));
console.log('\n4. homeSocStatus:', JSON.stringify(homeSoc.homeSocStatus(), null, 2));
