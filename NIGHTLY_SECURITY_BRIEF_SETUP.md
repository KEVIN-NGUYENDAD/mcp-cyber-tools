# Nightly Security Brief - Setup & Operation Guide

## Overview

The **Nightly Security Brief** is an automated daily security reporting system that generates and delivers a comprehensive security status report at **8:00 PM UTC** every day.

**Architecture:** Cloned from the existing `morning` briefing skill  
**Schedule:** Daily at 8:00 PM UTC (20:00)  
**Delivery:** Claude Code session HTML artifact + archive  
**Content:** Security score, findings, recommendations, telemetry  

---

## Architecture

### Files

| File | Purpose |
|------|---------|
| `NIGHTLY_SECURITY_BRIEF_SKILL.md` | Skill definition (Claude skill format) |
| `nightly-security-brief-trigger.js` | Generator implementation (Node.js) |
| `.claude/nightly-brief-trigger-config.json` | Trigger configuration |
| `NIGHTLY_SECURITY_BRIEF_SETUP.md` | This guide |

### System Flow

```
8:00 PM UTC Daily
    ↓
Trigger fires (cron: 0 20 * * *)
    ↓
Invoke: node nightly-security-brief-trigger.js
    ↓
Gather security data from system
    ├─ Process analysis
    ├─ Network connections
    ├─ Persistence mechanisms
    └─ Threat indicators
    ↓
Generate HTML artifact
    ↓
Deliver to Claude session
    ↓
Archive to ./reports/nightly-briefs/
```

---

## Components

### 1. Skill Definition (NIGHTLY_SECURITY_BRIEF_SKILL.md)

Defines the briefing structure using the same format as the `morning` skill:

**Sections:**
- Visual security score and threat level
- New security findings
- Process-level findings (suspicious activity)
- Persistence mechanism findings (scheduled tasks, startup items)
- Network connection findings (unusual traffic)
- Ranked recommendations
- Key lessons learned from the day
- System telemetry summary

**Language:** Follows morning skill voice: observe and report objectively, no commands embedded, no sensitive data exposure.

### 2. Generator (nightly-security-brief-trigger.js)

Node.js implementation that:

**Data Collection:**
```javascript
gatherSecurityData() → {
  timestamp,
  reportDate,
  reportTime,
  securityScore (0-100),
  threatLevel (RED/ORANGE/YELLOW/GREEN),
  newFindings[],
  processFindings[],
  persistenceFindings[],
  networkFindings[],
  recommendations[],
  lessonsLearned[],
  telemetrySummary
}
```

**Score Calculation:**
- Base: 85
- Deductions: Suspicious processes (-10 each), high connections (-5)
- Range: 0-100

**Threat Level Mapping:**
- GREEN: ≥90
- YELLOW: 75-89
- ORANGE: 50-74
- RED: <50

**HTML Generation:**
Styled single-page artifact with:
- Header: Date, score, threat badge
- Sections: Each finding type, recommendations, telemetry
- Responsive design (mobile-friendly)
- Color-coded severity badges

### 3. Trigger Configuration (.claude/nightly-brief-trigger-config.json)

Defines the scheduled execution:

```json
{
  "schedule": "0 20 * * *",    // 8PM UTC daily
  "timezone": "UTC",
  "command": "node nightly-security-brief-trigger.js",
  "delivery": "html_artifact + archive",
  "archive_path": "./reports/nightly-briefs/"
}
```

---

## Setup Instructions

### Step 1: Verify Files in Place

```bash
cd /home/user/mcp-cyber-tools

# Check files exist
ls -la NIGHTLY_SECURITY_BRIEF_SKILL.md
ls -la nightly-security-brief-trigger.js
ls -la .claude/nightly-brief-trigger-config.json
```

### Step 2: Test Generator Locally

```bash
# Generate a test briefing
node nightly-security-brief-trigger.js

# Verify output
ls -la nightly-security-brief-*.html
```

### Step 3: Install to Claude Skills (Manual)

Copy skill to Claude's skill directory:

```bash
# Copy skill definition
cp NIGHTLY_SECURITY_BRIEF_SKILL.md /root/.claude/skills/synced/nightly-security-brief/SKILL.md

# Verify installation
ls -la /root/.claude/skills/synced/nightly-security-brief/
```

### Step 4: Schedule the Trigger

Use Claude Code's trigger/scheduling system to create the recurring 8PM task:

**Via Code:**
```bash
# Create trigger (using Claude Code Remote MCP)
# Trigger: "Nightly Security Brief"
# Schedule: "0 20 * * *" (8PM daily UTC)
# Command: "node nightly-security-brief-trigger.js"
# Location: "/home/user/mcp-cyber-tools"
```

**Via UI:**
- Open Claude Code
- Go to: Settings → Scheduled Tasks → Create New
- Name: "Nightly Security Brief 8PM"
- Schedule: Daily at 8:00 PM UTC
- Command: `node nightly-security-brief-trigger.js`
- Working Directory: `/home/user/mcp-cyber-tools`
- Save

---

## Operation

### Manual Execution

```bash
# Generate briefing on-demand
node nightly-security-brief-trigger.js

# Output:
# ✓ Nightly Security Brief generated: nightly-security-brief-2026-08-24.html
#   Security Score: 75
#   Threat Level: YELLOW
#   Findings: 8
```

### Automatic Execution

At 8:00 PM UTC daily:
1. Claude Code trigger fires
2. Generator runs and collects system data
3. HTML artifact generated with current security findings
4. Delivered to your Claude session
5. Archived to `./reports/nightly-briefs/YYYY-MM-DD.html`

### Viewing Reports

```bash
# List all generated briefs
ls -la ./reports/nightly-briefs/

# View specific date
cat ./reports/nightly-briefs/2026-08-24.html
```

---

## Customization

### Change Schedule

Edit `.claude/nightly-brief-trigger-config.json`:

```json
{
  "schedule": {
    "cron": "0 19 * * *"    // Change to 7:00 PM UTC
  }
}
```

Common cron expressions:
- `0 20 * * *` - 8:00 PM daily (default)
- `0 18 * * *` - 6:00 PM daily
- `0 22 * * *` - 10:00 PM daily
- `0 20 * * 1-5` - Weekdays only (Mon-Fri)

### Add Custom Findings Section

Edit `nightly-security-brief-trigger.js`:

```javascript
// In gatherSecurityData():
data.customFinding = this.gatherCustomData();

// In generateHTMLBrief():
// Add to findingsHTML template
```

### Adjust Security Score Weights

Edit `calculateSecurityScore()`:

```javascript
// Modify deduction weights
score -= 15 * suspicious;    // Was: 10 * suspicious
score -= 8;                  // Was: 5
```

### Change Threat Level Thresholds

Edit `determineThreatLevel()`:

```javascript
if (score >= 95) return "GREEN";   // Was: >= 90
if (score >= 80) return "YELLOW";  // Was: >= 75
// etc.
```

---

## Troubleshooting

### Generator Won't Run

```bash
# Check Node.js version
node --version              # Should be 18+

# Check dependencies
npm install                 # Reinstall if needed

# Test execution
node nightly-security-brief-trigger.js

# Check error output
node nightly-security-brief-trigger.js 2>&1
```

### No Trigger Execution

1. Verify trigger is enabled:
   ```bash
   # Check config
   cat .claude/nightly-brief-trigger-config.json
   ```

2. Verify cron schedule:
   ```bash
   # Check system cron
   crontab -l
   ```

3. Check logs:
   ```bash
   # Claude Code session logs
   ls -la /root/.claude/sessions/
   ```

### Missing Findings

1. Verify system has data to report:
   ```bash
   ps aux | wc -l              # Check processes
   netstat -an | wc -l         # Check connections
   ```

2. Check permissions:
   ```bash
   # May need elevated privileges for some system calls
   sudo node nightly-security-brief-trigger.js
   ```

### HTML Rendering Issues

1. Validate HTML:
   ```bash
   # Test render
   node -e "const{chromium}=require('playwright');..."
   ```

2. Check styles:
   - Color values in palette
   - Font stack compatibility
   - Responsive breakpoints

---

## Comparison: Morning vs. Nightly Brief

| Aspect | Morning Brief | Nightly Brief |
|--------|---------------|---------------|
| **Schedule** | 11:00 AM daily | 8:00 PM daily |
| **Purpose** | Day overview | Security summary |
| **Content** | Calendar, email, tasks | Security findings |
| **Data Source** | Integrations (Gmail, Calendar) | System telemetry |
| **Audience** | Personal productivity | Security team |
| **Skill** | `morning` | `nightly-security-brief` |
| **Implementation** | Claude skill (Anthropic) | Custom Node.js |
| **Deployment** | Built-in | This repository |

---

## Architecture Reuse

The nightly brief **reuses the morning briefing architecture:**

✓ Same HTML artifact delivery mechanism  
✓ Same scheduling/trigger infrastructure  
✓ Same styling foundation  
✓ Same skill definition format  
✓ Same data gathering pattern  
✓ Same responsive design approach  

**Differences:**
- Content: Security vs. calendar-based
- Data source: System telemetry vs. integrations
- Audience: Security team vs. individual
- Schedule: 8PM vs. 11AM

---

## Monitoring & Alerts

### Success Indicators

- Daily HTML artifact generated
- Security score calculated
- All sections populated
- No errors in logs
- Archived to reports directory

### Failure Indicators

- Trigger doesn't fire (check cron)
- Generator crashes (check Node.js)
- Empty findings (check system permissions)
- Missing archive (check directory permissions)

### Check Status

```bash
# View latest brief
ls -lt ./reports/nightly-briefs/ | head -1

# Verify content
grep "Security Score" ./reports/nightly-briefs/latest.html

# Check generator logs
tail -n 100 /root/.claude/sessions/*.log | grep nightly
```

---

## Maintenance

### Daily

- Monitor briefing delivery (automated)
- Review findings for action items
- Acknowledge recommendations

### Weekly

- Review trend in security score
- Analyze patterns in findings
- Update threat thresholds if needed

### Monthly

- Audit of all archived briefs
- Performance review
- Update findings criteria
- Adjust weights/scoring

---

## Documentation

**Related Files:**
- `NIGHTLY_SECURITY_BRIEF_SKILL.md` - Skill specification
- `nightly-security-brief-trigger.js` - Implementation code
- `.claude/nightly-brief-trigger-config.json` - Configuration
- `DFIR_TRIAGE_REPORT.md` - Security baseline
- `LINUX_MCP_IMPLEMENTATION_SUMMARY.md` - MCP architecture
- `LINUX_MCP_DEMO.js` - Process analysis tools

**Learning Resources:**
- Morning skill: `/root/.claude/skills/synced/morning/SKILL.md`
- Claude Code docs: https://claude.ai/code
- Node.js child_process: https://nodejs.org/api/child_process.html
- Cron expressions: https://crontab.guru

---

**Status:** ✅ READY TO DEPLOY

**Next Steps:**
1. Commit these files to branch
2. Verify trigger installation
3. Test at scheduled time (8PM UTC)
4. Monitor first week for issues
5. Adjust as needed based on findings
