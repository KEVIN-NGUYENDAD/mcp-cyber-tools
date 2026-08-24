---
name: home-soc-brief
description: "Complete home network security briefing spanning network infrastructure, devices, and cameras. Aggregates network discovery, Desktop, Laptop, and iPhone into one unified home security overview. Answers: What changed? Which device needs attention? Highest risk? System lessons? What to improve? Perfect for home SOC oversight combining network + endpoint security."
---

## Context

This is your personal Home SOC executive briefing covering entire home security.

Not just devices. Your entire home network. Routers, cameras, desktops, phones—all one question: "What's my complete home security state?"

You are the CISO of your entire home. Network is your infrastructure. Desktop, Laptop, iPhone are your endpoints. Cameras are your sensors. Every night they report. You need one unified briefing.

What changed across network and all devices.  
Which device or network component carries the highest risk.  
What you need to act on immediately.  
What the system is learning about your home.  
Where to improve next.

## Gather

Auto-load from:
1. **Network Discovery** — Home network scan (devices, IPs, ports)
2. **Desktop Brief** — Desktop system security report (nightly brief)
3. **Laptop Brief** — Laptop system security report (nightly brief)
4. **iPhone Brief** — iPhone device security report (device brief)
5. **Network State** — Device baseline (known devices, expected configs)
6. **Lessons** — Cross-device insights

## Sort

Rank findings by:
1. **Impact** (network-wide or device-specific)
2. **Risk Severity** (CRITICAL → LOW)
3. **Evidence** (confidence %)
4. **Actionability** (what you can do)
5. **Scope** (network vs. endpoint)

## Answer 5 Questions

### 1. WHAT CHANGED TODAY?

Across network and all devices:
- New devices joined network
- Devices went offline
- Network configuration changes
- Port changes
- System changes on endpoints

Format: "Network: 1 new device | Desktop: 2 changes | Laptop: 0 changes | iPhone: 0 changes"

### 2. WHICH DEVICE NEEDS ATTENTION?

List devices with changes and scope:
- Network level: new devices, offline cameras, port changes
- Desktop: new services, packages, ports
- Laptop: system changes
- iPhone: iOS update, apps, settings

### 3. WHAT IS THE HIGHEST RISK?

Home-wide risk ranking:
- Top 5 risks across network and all devices
- Device/network attribution
- Severity level (CRITICAL/HIGH/MEDIUM/LOW)
- Confidence %
- Evidence count

### 4. WHAT DID CYBER-TOOLS LEARN?

Unified lessons from network and devices:
- Network-level discoveries (new device types, port patterns)
- Device-level insights (system changes)
- Cross-device patterns (coordinated activity)
- Home security improvement opportunities

Format: "Type: discovery description"

### 5. WHAT SHOULD BE IMPROVED NEXT?

Evidence-based priorities:
- Rank by impact and ease
- Support from multiple signals
- Network-wide + endpoint view
- Actionable steps

## Build

Output one clean HTML page:
- Header: Overall home score, threat level, network + per-device scores
- 5 answer sections
- Network status (devices online, cameras, open ports)
- Device status boxes (score + changes)
- Risk findings (device/network-attributed)
- Changes summary (new devices, offline, ports)
- Recommendations ranked
- Lessons learned
- Color-coded severity badges
- Mobile-responsive

Fonts: System stack only  
Colors: Threat-level accent bar  
Target: Readable in 60 seconds

## Verify

Before delivery:
- Overall home security score prominently displayed
- Network score visible
- Per-device scores visible (Desktop, Laptop, iPhone)
- All devices accounted for
- Top risks ranked by severity
- Device/network attribution clear
- Confidence % on findings
- Changes summary accurate
- Recommendations prioritized
- No raw network dumps
- Threat level color-coded

## Voice

Executive briefing for personal Home SOC chief (you).

One unified view of entire home security.

Confident language. Evidence-backed claims. Clear device/network attribution.

Never: "might", "possibly", "perhaps"  
Always: "X with Y% confidence based on Z signals from [device/network]"

Think like a CISO reviewing the home SOC dashboard:
- What's my overall home security posture
- Which sensor (network or device) is alerting
- What requires my immediate attention
- What's improving
- What needs fixing across home

## Execution

Auto-load and parse:
- Network discovery results (current network state)
- Device baseline (known devices, expected IPs/MACs)
- `nightly-security-brief-YYYY-MM-DD.html` (desktop)
- `nightly-security-brief-YYYY-MM-DD.html` (laptop)
- `iphone-security-brief-YYYY-MM-DD.html` (iPhone)
- Device state files from all sources

Generate:
- `home-soc-brief-YYYY-MM-DD.html` (unified home report)
- Archive: `./reports/home-soc-briefs/YYYY-MM-DD.html`

## Scoring

Overall Score Calculation (Weighted Average):
- Network: 30% weight (infrastructure sensor)
- Desktop: 25% weight (primary endpoint)
- Laptop: 25% weight (secondary endpoint)
- iPhone: 20% weight (mobile endpoint)

Formula: (Network × 0.30) + (Desktop × 0.25) + (Laptop × 0.25) + (iPhone × 0.20)

Threat Level Mapping:
- GREEN: ≥85 (Home network secure)
- YELLOW: 70-84 (Monitor closely)
- ORANGE: 50-69 (Action recommended)
- RED: <50 (Critical - address now)

## Schedule

Recommended: Daily at 8:00 PM UTC (after all sensors report)
- 8:00 PM: Desktop nightly brief
- 8:05 PM: SOC Chief briefing (desktop synthesis)
- 8:10 PM: iPhone device brief
- 8:15 PM: Multi-device briefing (desktop + laptop + iPhone)
- 8:20 PM: Home SOC briefing ← This runs (includes network)

Alternative: Replace 8:00 PM nightly brief with Home SOC that includes network + all devices

Execution time: <500ms  
Output size: 12-16 KB per day  
Archive: 30 days = ~400 KB

## Integration

### Prerequisite Components

This home briefing depends on:
1. **Network Discovery** — home-network-discovery.js (discovers and monitors network)
2. **Desktop Brief** — nightly-security-brief.js (endpoint monitoring)
3. **iPhone Brief** — iphone-security-brief.js (device monitoring)

All three sources contribute to the unified home briefing.

### Data Flow

```
Network Discovery (score, devices, risks)
    ↓
Desktop Brief (80/100)
    ↓
Laptop Brief (80/100)
    ↓
iPhone Brief (95/100)
    ↓
Home SOC Aggregator
    ├─ Parse all sources
    ├─ Extract network score
    ├─ Extract device scores
    ├─ Calculate weighted average: 79/100
    ├─ Determine threat level: YELLOW
    ├─ Extract network + device risks
    ├─ Detect network changes
    ├─ Rank recommendations
    ├─ Aggregate lessons
    └─ Generate unified home briefing
    ↓
One-Page Home Security Summary
```

## Success Indicators

✅ Network discovery running  
✅ All device briefs loaded successfully  
✅ Overall home score calculated correctly (weighted average)  
✅ Network score visible  
✅ Per-device scores visible  
✅ Threat level determined accurately  
✅ Network + device risks identified  
✅ Device/network attribution clear  
✅ New devices detected  
✅ Offline devices detected  
✅ Top 5 risks ranked by severity  
✅ Confidence % on findings  
✅ Changes summary accurate  
✅ Recommendations actionable  
✅ Lessons aggregated  
✅ One page, readable in <60 seconds  

## Customization

### Adjust Device/Network Weights

Edit scoring formula in `calculateHomeScore()`:

```javascript
// Current: Network 30%, Desktop 25%, Laptop 25%, iPhone 20%
const weights = {
  network: 0.30,   // Change this weight
  desktop: 0.25,   // Change this weight
  laptop: 0.25,    // Change this weight
  iphone: 0.20     // Change this weight
};
```

### Adjust Network Monitoring Scope

In `home-network-discovery.js`, customize:
1. Network segments (IP ranges to scan)
2. Known devices (baseline expectations)
3. Expected vendors (filter unknown devices)
4. Security policies (baseline requirements)

### Change Schedule

Edit `.claude/home-soc-trigger-config.json`:
```json
{
  "schedule": {
    "cron": "20 20 * * *"  // Change to 8:20 PM UTC
  }
}
```

---

**Tone:** Unified home security overview. Home CISO perspective.  
**Length:** One page  
**Time:** Under 60 seconds  
**Audience:** You (home security chief)  
**Purpose:** Complete home security posture across network + devices  
**Scope:** Router, WiFi, cameras, Desktop, Laptop, iPhone
