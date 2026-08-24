import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class HomeNetworkDiscovery {
  constructor() {
    this.baselineDir = './reports/home-soc-state';
    this.reportsDir = './reports/home-soc-briefs';
    this.ensureDirectories();
    this.loadBaseline();
  }

  ensureDirectories() {
    [this.baselineDir, this.reportsDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  loadBaseline() {
    const baselinePath = path.join(this.baselineDir, 'device-baseline.json');
    if (fs.existsSync(baselinePath)) {
      try {
        this.baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
      } catch (e) {
        this.baseline = this.getDefaultBaseline();
      }
    } else {
      this.baseline = this.getDefaultBaseline();
      this.saveBaseline();
    }
  }

  getDefaultBaseline() {
    return {
      lastUpdated: new Date().toISOString(),
      knownDevices: {
        router: { ip: '192.168.1.1', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'router-brand', expectedPorts: [80, 443, 53] },
        desktop: { ip: '192.168.1.10', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'desktop', expectedPorts: [] },
        laptop: { ip: '192.168.1.11', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'laptop', expectedPorts: [] },
        iphone: { ip: '192.168.1.12', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'apple', expectedPorts: [] },
        camera1: { ip: '192.168.1.100', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'hikvision', expectedPorts: [554, 80] },
        camera2: { ip: '192.168.1.101', mac: 'xx:xx:xx:xx:xx:xx', vendor: 'hikvision', expectedPorts: [554, 80] }
      },
      networkSegments: [
        { range: '192.168.1.0/24', name: 'Home LAN', purpose: 'Primary home network' }
      ],
      expectedVendors: ['router-brand', 'desktop', 'laptop', 'apple', 'hikvision', 'tp-link', 'netgear'],
      ignoredDevices: [],
      createdAt: new Date().toISOString()
    };
  }

  saveBaseline() {
    const baselinePath = path.join(this.baselineDir, 'device-baseline.json');
    fs.writeFileSync(baselinePath, JSON.stringify(this.baseline, null, 2));
  }

  discoverDevices() {
    // Framework for network discovery
    // In real environment, would use nmap, arp-scan, or similar
    // For demo, return baseline + simulated discovery

    const discovered = {
      timestamp: new Date().toISOString(),
      devices: [],
      summary: {
        total: 0,
        online: 0,
        offline: 0,
        unknown: 0
      }
    };

    // Simulate discovery using baseline
    Object.entries(this.baseline.knownDevices).forEach(([name, device]) => {
      discovered.devices.push({
        id: name,
        ip: device.ip,
        mac: device.mac,
        vendor: device.vendor,
        openPorts: device.expectedPorts,
        status: 'online', // Would be determined by actual scan
        confidence: 100,
        firstSeen: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        type: this.classifyDevice(name, device.vendor)
      });

      discovered.summary.total++;
      if (device.status !== 'offline') {
        discovered.summary.online++;
      }
    });

    return discovered;
  }

  classifyDevice(name, vendor) {
    if (name === 'router' || vendor.toLowerCase().includes('router')) return 'router';
    if (name.includes('camera') || vendor.toLowerCase().includes('hikvision')) return 'camera';
    if (vendor.toLowerCase().includes('apple') || name === 'iphone') return 'mobile';
    if (name === 'desktop') return 'desktop';
    if (name === 'laptop') return 'laptop';
    return 'unknown';
  }

  detectChanges(currentDevices, previousDevices) {
    const changes = {
      newDevices: [],
      offlineDevices: [],
      onlineDevices: [],
      portChanges: [],
      vendorChanges: [],
      configChanges: []
    };

    if (!previousDevices) {
      return changes;
    }

    // Track new devices
    currentDevices.forEach(current => {
      const previous = previousDevices.find(p => p.ip === current.ip);
      if (!previous) {
        changes.newDevices.push({
          id: current.id,
          ip: current.ip,
          vendor: current.vendor,
          type: current.type,
          confidence: current.confidence
        });
      } else {
        // Check for port changes
        if (JSON.stringify(current.openPorts) !== JSON.stringify(previous.openPorts)) {
          changes.portChanges.push({
            device: current.id,
            ip: current.ip,
            newPorts: current.openPorts,
            oldPorts: previous.openPorts
          });
        }

        // Check for vendor changes (firmware update indicator)
        if (current.vendor !== previous.vendor) {
          changes.vendorChanges.push({
            device: current.id,
            ip: current.ip,
            newVendor: current.vendor,
            oldVendor: previous.vendor
          });
        }
      }
    });

    // Track offline devices
    previousDevices.forEach(previous => {
      const current = currentDevices.find(c => c.ip === previous.ip);
      if (!current) {
        changes.offlineDevices.push({
          id: previous.id,
          ip: previous.ip,
          vendor: previous.vendor,
          type: previous.type
        });
      }
    });

    return changes;
  }

  assessCameraRisks(devices) {
    const risks = [];

    devices.forEach(device => {
      if (device.type !== 'camera') return;

      // RTSP exposure (port 554)
      if (device.openPorts.includes(554)) {
        risks.push({
          device: device.id,
          type: 'camera',
          severity: 'HIGH',
          title: 'RTSP Stream Exposed',
          description: `Camera at ${device.ip} has RTSP port (554) open to network`,
          ports: [554],
          recommendation: 'Restrict RTSP to local network only',
          confidence: 100
        });
      }

      // HTTP exposure (unencrypted)
      if (device.openPorts.includes(80)) {
        risks.push({
          device: device.id,
          type: 'camera',
          severity: 'MEDIUM',
          title: 'HTTP Access Enabled',
          description: `Camera at ${device.ip} allows HTTP (unencrypted) access`,
          ports: [80],
          recommendation: 'Use HTTPS only, disable HTTP access',
          confidence: 95
        });
      }

      // Missing HTTPS
      if (!device.openPorts.includes(443) && device.openPorts.includes(80)) {
        risks.push({
          device: device.id,
          type: 'camera',
          severity: 'MEDIUM',
          title: 'No HTTPS Available',
          description: `Camera at ${device.ip} has no HTTPS encryption option`,
          recommendation: 'Enable HTTPS and disable HTTP',
          confidence: 90
        });
      }
    });

    return risks;
  }

  assessRouterRisks(devices) {
    const risks = [];
    const router = devices.find(d => d.type === 'router');

    if (!router) return risks;

    // Public HTTP access
    if (router.openPorts.includes(80)) {
      risks.push({
        device: router.id,
        type: 'router',
        severity: 'CRITICAL',
        title: 'Router Web UI Public Access',
        description: 'Router web interface (port 80) accessible from WAN',
        ports: [80],
        recommendation: 'Disable WAN access to router admin panel',
        confidence: 100
      });
    }

    // Default credentials risk (can't detect, but common issue)
    risks.push({
      device: router.id,
      type: 'router',
      severity: 'HIGH',
      title: 'Default Credentials Check',
      description: 'Verify router is not using default admin credentials',
      recommendation: 'Change admin password to strong, unique credential',
      confidence: 85
    });

    // UPnP risk
    risks.push({
      device: router.id,
      type: 'router',
      severity: 'MEDIUM',
      title: 'UPnP Port Mapping Risk',
      description: 'UPnP can allow applications to open ports automatically',
      recommendation: 'Disable UPnP if not needed, monitor port mappings',
      confidence: 80
    });

    return risks;
  }

  generateNetworkReport(devices, changes, cameraRisks, routerRisks) {
    const allRisks = [...cameraRisks, ...routerRisks];
    const criticalCount = allRisks.filter(r => r.severity === 'CRITICAL').length;
    const highCount = allRisks.filter(r => r.severity === 'HIGH').length;

    // Calculate network security score
    let score = 85; // Start at good

    if (changes.newDevices.length > 0) score -= 5;
    if (changes.offlineDevices.length > 0) score -= 3;
    if (changes.portChanges.length > 0) score -= 5;
    if (criticalCount > 0) score -= 15;
    if (highCount > 0) score -= 5;

    score = Math.max(0, Math.min(100, score));

    return {
      score,
      threatLevel: this.determineThreatLevel(score),
      deviceCount: devices.length,
      onlineCount: devices.filter(d => d.status === 'online').length,
      offlineCount: devices.filter(d => d.status === 'offline').length,
      cameras: devices.filter(d => d.type === 'camera').length,
      changes,
      risks: allRisks.sort((a, b) => {
        const severity = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
        return severity[a.severity] - severity[b.severity];
      }).slice(0, 5)
    };
  }

  determineThreatLevel(score) {
    if (score >= 85) return 'GREEN';
    if (score >= 70) return 'YELLOW';
    if (score >= 50) return 'ORANGE';
    return 'RED';
  }

  saveDiscovery(discovery) {
    const today = new Date().toISOString().split('T')[0];
    const discoveryPath = path.join(this.baselineDir, `discovery-${today}.json`);

    fs.writeFileSync(discoveryPath, JSON.stringify(discovery, null, 2));

    // Save as current discovery for next comparison
    const currentPath = path.join(this.baselineDir, 'current-devices.json');
    const previousPath = path.join(this.baselineDir, 'previous-devices.json');

    if (fs.existsSync(currentPath)) {
      const current = JSON.parse(fs.readFileSync(currentPath, 'utf8'));
      fs.writeFileSync(previousPath, JSON.stringify(current, null, 2));
    }

    fs.writeFileSync(currentPath, JSON.stringify(discovery.devices, null, 2));
  }

  discover() {
    console.log('Starting home network discovery...');

    // Discover devices
    const discovered = this.discoverDevices();

    // Load previous state for change detection
    const previousPath = path.join(this.baselineDir, 'previous-devices.json');
    let previousDevices = null;
    if (fs.existsSync(previousPath)) {
      try {
        previousDevices = JSON.parse(fs.readFileSync(previousPath, 'utf8'));
      } catch (e) {
        // Continue without previous
      }
    }

    // Detect changes
    const changes = this.detectChanges(discovered.devices, previousDevices);

    // Assess risks
    const cameraRisks = this.assessCameraRisks(discovered.devices);
    const routerRisks = this.assessRouterRisks(discovered.devices);

    // Generate report
    const report = this.generateNetworkReport(discovered.devices, changes, cameraRisks, routerRisks);

    // Save discovery
    this.saveDiscovery(discovered);

    // Output summary
    console.log('✓ Network discovery complete');
    console.log(`  Devices found: ${discovered.summary.total}`);
    console.log(`  Online: ${discovered.summary.online}`);
    console.log(`  Cameras: ${report.cameras}`);
    console.log(`  Network Score: ${report.score}/100`);
    console.log(`  Threat Level: ${report.threatLevel}`);
    if (changes.newDevices.length > 0) console.log(`  New devices: ${changes.newDevices.length}`);
    if (changes.offlineDevices.length > 0) console.log(`  Offline: ${changes.offlineDevices.length}`);
    if (report.risks.length > 0) console.log(`  Risks detected: ${report.risks.length}`);

    return report;
  }
}

// Execute
const discovery = new HomeNetworkDiscovery();
discovery.discover();

export { HomeNetworkDiscovery };
