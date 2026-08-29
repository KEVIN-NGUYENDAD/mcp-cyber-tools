/**
 * SOC Chief Briefing - Executive Summary
 *
 * Daily 8 PM briefing for security leadership.
 * Parses nightly brief, telemetry, lessons, validations.
 * Answers 5 critical questions in under 60 seconds.
 *
 * Output: One-page executive brief (HTML artifact)
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { join } from "path";

class SOCChiefBriefing {
  constructor() {
    this.timestamp = new Date().toISOString();
    this.reportDate = new Date().toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric"
    });
    this.reportTime = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit"
    });

    this.stateDir = "./reports/nightly-state";
    this.reportsDir = "./reports/nightly-briefs";
    this.lessonsFile = join(this.stateDir, "lessons.json");
    this.validationsFile = join(this.stateDir, "validations.json");
    this.stateFile = join(this.stateDir, "system-state.json");
    this.latestBriefFile = join(this.reportsDir, `${this.getDateString()}.html`);
  }

  getDateString() {
    return new Date().toISOString().split("T")[0];
  }

  loadLatestBrief() {
    try {
      if (existsSync(this.latestBriefFile)) {
        return readFileSync(this.latestBriefFile, "utf8");
      }
    } catch (e) {
      console.warn("Could not load latest brief");
    }
    return null;
  }

  loadLessons() {
    try {
      if (existsSync(this.lessonsFile)) {
        return JSON.parse(readFileSync(this.lessonsFile, "utf8"));
      }
    } catch (e) {
      console.warn("Could not load lessons");
    }
    return [];
  }

  loadValidations() {
    try {
      if (existsSync(this.validationsFile)) {
        return JSON.parse(readFileSync(this.validationsFile, "utf8"));
      }
    } catch (e) {
      console.warn("Could not load validations");
    }
    return [];
  }

  loadSystemState() {
    try {
      if (existsSync(this.stateFile)) {
        return JSON.parse(readFileSync(this.stateFile, "utf8"));
      }
    } catch (e) {
      console.warn("Could not load system state");
    }
    return null;
  }

  extractBriefData(briefHTML) {
    const data = {
      securityScore: 85,
      threatLevel: "YELLOW",
      changes: 0,
      topRisks: [],
      findings: [],
      telemetry: {}
    };

    try {
      // Extract security score
      const scoreMatch = briefHTML.match(/<div class="score-value">(\d+)<\/div>/);
      if (scoreMatch) data.securityScore = parseInt(scoreMatch[1]);

      // Extract threat level
      const threatMatch = briefHTML.match(/THREAT.*?(GREEN|YELLOW|ORANGE|RED)/);
      if (threatMatch) data.threatLevel = threatMatch[1];

      // Extract changes count
      const changesMatch = briefHTML.match(/<div class="score-value">(\d+)<\/div>\s*<div class="score-label">Changes Detected/);
      if (changesMatch) data.changes = parseInt(changesMatch[1]);

      // Extract telemetry values
      const telemetryMatches = briefHTML.match(/<div class="telemetry-value">(\d+|✓|✗)<\/div>\s*<div class="telemetry-label">([^<]+)<\/div>/g);
      if (telemetryMatches) {
        telemetryMatches.forEach(match => {
          const valueMatch = match.match(/<div class="telemetry-value">([^<]+)<\/div>\s*<div class="telemetry-label">([^<]+)<\/div>/);
          if (valueMatch) {
            data.telemetry[valueMatch[2]] = valueMatch[1];
          }
        });
      }
    } catch (e) {
      console.warn("Error parsing brief HTML:", e.message);
    }

    return data;
  }

  // Question 1: What changed today?
  generateChangesAnalysis(systemState, lessons) {
    const changes = [];

    if (systemState) {
      // Count users
      const userCount = systemState.users?.length || 0;
      if (userCount > 0) {
        changes.push({
          type: "System Users",
          count: userCount,
          priority: "normal"
        });
      }

      // Count services
      const serviceCount = systemState.services?.length || 0;
      if (serviceCount > 0) {
        changes.push({
          type: "Active Services",
          count: serviceCount,
          priority: "normal"
        });
      }

      // Count cron jobs
      const cronCount = systemState.cronJobs?.length || 0;
      if (cronCount > 0) {
        changes.push({
          type: "Scheduled Tasks",
          count: cronCount,
          priority: "high"
        });
      }

      // Count packages
      const pkgCount = systemState.packages?.length || 0;
      if (pkgCount > 0) {
        changes.push({
          type: "Installed Packages",
          count: pkgCount,
          priority: "normal"
        });
      }

      // Count listening ports
      const portCount = systemState.listeningPorts?.length || 0;
      if (portCount > 0) {
        changes.push({
          type: "Listening Ports",
          count: portCount,
          priority: "high"
        });
      }
    }

    return changes.length > 0 ? changes : [{ type: "No significant changes", count: 0, priority: "normal" }];
  }

  // Question 2: What should I care about?
  generateTopRisks(briefData, validations) {
    const risks = [];

    // Map threat level to risk items
    if (briefData.threatLevel === "RED") {
      risks.push({
        rank: 1,
        title: "CRITICAL THREAT",
        description: "System threat level RED - immediate investigation required",
        confidence: 95,
        evidenceCount: 3
      });
    } else if (briefData.threatLevel === "ORANGE") {
      risks.push({
        rank: 1,
        title: "High-Risk Changes",
        description: `${briefData.changes} significant system changes detected`,
        confidence: 90,
        evidenceCount: briefData.changes
      });
    }

    // Add validated findings
    const validatedRisks = validations
      ?.filter(v => v.severity === "HIGH" || v.severity === "CRITICAL")
      ?.slice(0, 2)
      ?.map((v, idx) => ({
        rank: (risks.length + idx + 1),
        title: v.title || "Validated Finding",
        description: v.description || "See validation log",
        confidence: v.confidence || 85,
        evidenceCount: v.evidenceCount || 1
      }));

    return [...risks, ...(validatedRisks || [])].slice(0, 3);
  }

  // Question 3: What did cyber-tools learn today?
  generateLessonsLearned(lessons, validations) {
    const insights = [];

    // Add top lessons
    if (lessons && lessons.length > 0) {
      lessons.slice(0, 2).forEach((lesson, idx) => {
        insights.push({
          type: "Lesson",
          content: typeof lesson === "string" ? lesson : lesson.description || "Security observation recorded",
          impact: idx === 0 ? "high" : "medium"
        });
      });
    }

    // Add validation updates
    const newValidations = validations
      ?.filter(v => v.status === "NEW" || v.status === "UPDATED")
      ?.slice(0, 1)
      ?.map(v => ({
        type: "Validation Update",
        content: `${v.title}: confidence ${v.confidence}%`,
        impact: "medium"
      }));

    return [...insights, ...(newValidations || [])];
  }

  // Question 4: What is wasting my time?
  generateToolPerformance(briefData) {
    const performance = [];

    // Analyze telemetry for inefficiencies
    const telemetry = briefData.telemetry || {};

    // High connection count = potential noise
    const connections = parseInt(telemetry["Connections"] || "0");
    if (connections > 50) {
      performance.push({
        issue: "High Connection Volume",
        metric: `${connections} connections analyzed`,
        impact: "Medium",
        recommendation: "Consider filtering by known-good traffic"
      });
    }

    // Process monitoring efficiency
    const processes = parseInt(telemetry["Processes Monitored"] || "0");
    if (processes > 100) {
      performance.push({
        issue: "Process Monitoring Overhead",
        metric: `${processes} processes tracked`,
        impact: "Low",
        recommendation: "Focus on suspicious/changed processes only"
      });
    }

    // Add baseline efficiency score
    if (performance.length === 0) {
      performance.push({
        issue: "Monitoring Efficient",
        metric: "Focused collection with no waste",
        impact: "None",
        recommendation: "Continue current monitoring strategy"
      });
    }

    return performance.slice(0, 2);
  }

  // Question 5: What should we improve next?
  generateImprovements(briefData, systemState, lessons) {
    const improvements = [];

    // Security score improvement
    const scoreGap = 100 - briefData.securityScore;
    if (scoreGap > 10) {
      improvements.push({
        priority: 1,
        title: `Close Security Score Gap (${scoreGap} points)`,
        evidence: `Current score: ${briefData.securityScore}/100`,
        effort: "Medium",
        impact: "High"
      });
    }

    // Firewall/persistence improvements
    if (briefData.threatLevel !== "GREEN") {
      improvements.push({
        priority: 2,
        title: "Harden Persistence Defenses",
        evidence: "Cron/startup monitoring active",
        effort: "Low",
        impact: "High"
      });
    }

    // Network monitoring
    const ports = parseInt(briefData.telemetry["Listening Ports"] || "0") || 0;
    if (ports > 5) {
      improvements.push({
        priority: 3,
        title: `Audit ${ports} Network Listeners`,
        evidence: `${ports} ports require validation`,
        effort: "Medium",
        impact: "Medium"
      });
    }

    return improvements.slice(0, 3);
  }

  async generateBriefing() {
    console.log("Generating SOC Chief Briefing...");

    // Load all data sources
    const briefHTML = this.loadLatestBrief();
    const briefData = briefHTML ? this.extractBriefData(briefHTML) : {};
    const lessons = this.loadLessons();
    const validations = this.loadValidations();
    const systemState = this.loadSystemState();

    // Generate answers to 5 questions
    const q1_changes = this.generateChangesAnalysis(systemState, lessons);
    const q2_risks = this.generateTopRisks(briefData, validations);
    const q3_lessons = this.generateLessonsLearned(lessons, validations);
    const q4_performance = this.generateToolPerformance(briefData);
    const q5_improvements = this.generateImprovements(briefData, systemState, lessons);

    const html = this.generateHTML({
      briefData,
      q1_changes,
      q2_risks,
      q3_lessons,
      q4_performance,
      q5_improvements
    });

    // Save files
    const filename = `soc-chief-briefing-${this.getDateString()}.html`;
    writeFileSync(filename, html);

    const archiveFilename = join(this.reportsDir, `chief-${this.getDateString()}.html`);
    writeFileSync(archiveFilename, html);

    console.log(`✓ SOC Chief Briefing generated`);
    console.log(`  File: ${filename}`);
    console.log(`  Security Score: ${briefData.securityScore}/100`);
    console.log(`  Threat Level: ${briefData.threatLevel}`);
    console.log(`  Top Risks: ${q2_risks.length}`);
    console.log(`  Recommended Actions: ${q5_improvements.length}`);

    return { filename, archiveFilename, html };
  }

  generateHTML(data) {
    const { briefData, q1_changes, q2_risks, q3_lessons, q4_performance, q5_improvements } = data;

    const threatColors = {
      RED: "#D32F2F",
      ORANGE: "#F57C00",
      YELLOW: "#FBC02D",
      GREEN: "#388E3C"
    };

    const threatColor = threatColors[briefData.threatLevel] || "#1976D2";

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SOC Chief Briefing - ${this.reportDate}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Segoe UI", sans-serif;
      background: #FCFCFB;
      color: #2E2C27;
      line-height: 1.6;
    }
    .container {
      max-width: 960px;
      margin: 0 auto;
      padding: 40px 30px;
    }
    .header {
      margin-bottom: 30px;
      padding-bottom: 20px;
      border-bottom: 2px solid #E1E1DF;
    }
    .header-meta {
      font-size: 11px;
      color: #6B6A63;
      margin-bottom: 10px;
    }
    h1 {
      font-size: 32px;
      margin-bottom: 20px;
      color: #2E2C27;
      font-weight: 600;
    }
    .score-card {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-top: 20px;
    }
    .score-box {
      padding: 15px;
      background: #F9F9F7;
      border-radius: 6px;
      border-left: 4px solid ${threatColor};
      text-align: center;
    }
    .score-value {
      font-size: 32px;
      font-weight: bold;
      color: ${threatColor};
      margin-bottom: 5px;
    }
    .score-label {
      font-size: 12px;
      color: #6B6A63;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 30px;
    }
    .section {
      background: #F9F9F7;
      padding: 20px;
      border-radius: 6px;
      border: 1px solid #E4E3DC;
    }
    .section h2 {
      font-size: 16px;
      margin-bottom: 15px;
      color: #2E2C27;
      border-bottom: 2px solid #E1E1DF;
      padding-bottom: 10px;
      font-weight: 600;
    }
    .section h3 {
      font-size: 14px;
      margin-top: 15px;
      margin-bottom: 8px;
      color: #2E2C27;
      font-weight: 600;
    }
    .item {
      margin-bottom: 12px;
      padding: 10px;
      background: #FCFCFB;
      border-radius: 4px;
      border-left: 3px solid #1976D2;
    }
    .item.high {
      border-left-color: #D32F2F;
    }
    .item.medium {
      border-left-color: #FBC02D;
    }
    .item.low {
      border-left-color: #388E3C;
    }
    .item-title {
      font-weight: bold;
      color: #2E2C27;
      font-size: 13px;
      margin-bottom: 4px;
    }
    .item-meta {
      font-size: 11px;
      color: #6B6A63;
    }
    .item-description {
      font-size: 12px;
      color: #6B6A63;
      margin-top: 4px;
    }
    .badge {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: bold;
      margin-right: 6px;
      background: ${threatColor};
      color: white;
    }
    .full-width {
      grid-column: 1 / -1;
      margin-top: 10px;
    }
    .footer {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #E1E1DF;
      font-size: 11px;
      color: #B4B3A8;
      text-align: center;
    }
    @media (max-width: 768px) {
      .main-grid { grid-template-columns: 1fr; }
      .score-card { grid-template-columns: 1fr 1fr; }
      .container { padding: 20px 15px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-meta">${this.reportDate} • ${this.reportTime} UTC</div>
      <h1>SOC Chief Briefing</h1>
      <div class="score-card">
        <div class="score-box">
          <div class="score-value">${briefData.securityScore}</div>
          <div class="score-label">Security Score</div>
        </div>
        <div class="score-box">
          <div class="score-value">${briefData.threatLevel}</div>
          <div class="score-label">Threat Level</div>
        </div>
        <div class="score-box">
          <div class="score-value">${briefData.changes}</div>
          <div class="score-label">Changes Today</div>
        </div>
        <div class="score-box">
          <div class="score-value">${q2_risks.length}</div>
          <div class="score-label">Top Risks</div>
        </div>
      </div>
    </div>

    <div class="main-grid">
      <!-- Q1: Changes -->
      <div class="section">
        <h2>What Changed Today?</h2>
        ${q1_changes.map(change => `
          <div class="item ${change.priority}">
            <div class="item-title">${change.type}</div>
            <div class="item-meta">${change.count} item${change.count !== 1 ? 's' : ''}</div>
          </div>
        `).join('')}
      </div>

      <!-- Q2: Top Risks -->
      <div class="section">
        <h2>What Should I Care About?</h2>
        ${q2_risks.map(risk => `
          <div class="item high">
            <div class="item-title">#${risk.rank}: ${risk.title}</div>
            <div class="item-description">${risk.description}</div>
            <div class="item-meta">Confidence: ${risk.confidence}% • Evidence: ${risk.evidenceCount}</div>
          </div>
        `).join('')}
      </div>

      <!-- Q3: Lessons Learned -->
      <div class="section">
        <h2>What Did Tools Learn?</h2>
        ${q3_lessons.map(lesson => `
          <div class="item ${lesson.impact === 'high' ? 'high' : 'medium'}">
            <div class="item-title">${lesson.type}</div>
            <div class="item-description">${lesson.content}</div>
          </div>
        `).join('')}
      </div>

      <!-- Q4: Tool Performance -->
      <div class="section">
        <h2>What Is Wasting Time?</h2>
        ${q4_performance.map(perf => `
          <div class="item ${perf.impact === 'High' ? 'high' : 'medium'}">
            <div class="item-title">${perf.issue}</div>
            <div class="item-description">${perf.metric}</div>
            <div class="item-meta">→ ${perf.recommendation}</div>
          </div>
        `).join('')}
      </div>

      <!-- Q5: Improvements -->
      <div class="section full-width">
        <h2>What Should We Improve Next?</h2>
        ${q5_improvements.map(improvement => `
          <div class="item high">
            <span class="badge">#${improvement.priority}</span>
            <div class="item-title">${improvement.title}</div>
            <div class="item-description">${improvement.evidence}</div>
            <div class="item-meta">Effort: ${improvement.effort} • Impact: ${improvement.impact}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="footer">
      <p>Generated: ${this.timestamp}</p>
      <p>Executive Summary • One-Page Brief • ${(60)}s Read Time</p>
    </div>
  </div>
</body>
</html>`;
  }
}

// Run if invoked directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const briefing = new SOCChiefBriefing();
  briefing.generateBriefing().catch(console.error);
}

export { SOCChiefBriefing };
