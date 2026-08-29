---
name: multi-device-security-brief
description: "Unified security briefing across Desktop, Laptop, and iPhone. Aggregates findings from all devices into one executive summary answering 5 questions: What changed? Which device? Highest risk? Lessons learned? What to improve? Perfect for personal SOC oversight. Run after all device briefs complete."
---

## Context

This is your personal SOC executive briefing across all devices.

Not separate device reports. One unified view. All devices one question: "What's my security state?"

You are the CISO of your own devices. Desktop, Laptop, iPhone are your sensors. Every night they report. You need one unified briefing.

What changed across all devices.  
Which device carries the highest risk.  
What you need to act on.  
What the system is learning.  
Where to improve next.

## Gather

Auto-load from:
1. **Desktop Brief** — Desktop system security report (nightly brief)
2. **Laptop Brief** — Laptop system security report (nightly brief)
3. **iPhone Brief** — iPhone device security report (device brief)
4. **Device Data** — State files from each device
5. **Unified Lessons** — Cross-device insights

## Sort

Rank findings by:
1. **Impact** (across all devices)
2. **Risk Severity** (CRITICAL → LOW)
3. **Evidence** (confidence %)
4. **Actionability** (what you can do)

## Answer 5 Questions

### 1. WHAT CHANGED TODAY?

Across all devices:
- Which devices changed
- What type of change (OS, security, apps, etc.)
- Count of changes per device

Format: "Desktop: 3 changes | Laptop: 0 changes | iPhone: 0 changes"

### 2. WHICH DEVICE CHANGED?

List devices with changes and what they are:
- Desktop: new services, packages, ports
- Laptop: similar system changes
- iPhone: iOS update, apps, settings

### 3. WHAT IS THE HIGHEST RISK?

Cross-device risk ranking:
- Top 5 risks across all devices
- Device attribution (which device)
- Severity level
- Confidence %
- Evidence count

### 4. WHAT DID CYBER-TOOLS LEARN?

Unified lessons from all devices:
- System-level discoveries
- Device-level insights
- Cross-device patterns
- Improvement opportunities

Format: "Type: discovery description"

### 5. WHAT SHOULD BE IMPROVED NEXT?

Evidence-based priorities:
- Rank by impact and ease
- Support from multiple signals
- Cross-device view
- Actionable steps

## Build

Output one clean HTML page:
- Header: Overall score, threat level, per-device scores
- 5 answer sections
- Device status boxes (score + changes)
- Risk findings (device-attributed)
- Recommendations ranked
- Lessons learned
- Color-coded severity badges
- Mobile-responsive

Fonts: System stack only  
Colors: Threat-level accent bar  
Target: Readable in 60 seconds

## Verify

Before delivery:
- Overall security score prominently displayed
- Per-device scores visible
- All devices accounted for
- Top risks ranked by severity
- Device attribution clear
- Confidence % on findings
- Recommendations prioritized
- No raw device dumps
- Threat level color-coded

## Voice

Executive briefing for personal SOC chief (you).

One unified view of all security.

Confident language. Evidence-backed claims. Clear device attribution.

Never: "might", "possibly", "perhaps"  
Always: "X with Y% confidence based on Z signals from [device]"

Think like a CISO reviewing the SOC dashboard:
- What's my overall risk posture
- Which sensor (device) is alerting
- What requires my attention
- What's improving
- What needs fixing

## Execution

Auto-load and parse:
- `nightly-security-brief-YYYY-MM-DD.html` (desktop)
- `nightly-security-brief-YYYY-MM-DD.html` (laptop - can be separate)
- `iphone-security-brief-YYYY-MM-DD.html` (iPhone)
- Device state files from all sources

Generate:
- `multi-device-security-brief-YYYY-MM-DD.html` (unified report)
- Archive: `./reports/multi-device-briefs/YYYY-MM-DD.html`

## Scoring

Overall Score Calculation (Weighted Average):
- Desktop: 40% weight (primary sensor)
- Laptop: 40% weight (secondary sensor)
- iPhone: 20% weight (mobile sensor)

Formula: (Desktop × 0.4) + (Laptop × 0.4) + (iPhone × 0.2)

Threat Level Mapping:
- GREEN: ≥85 (All systems secure)
- YELLOW: 70-84 (Monitor closely)
- ORANGE: 50-69 (Action recommended)
- RED: <50 (Critical - address now)

## Schedule

Recommended: Daily at 8:15 PM UTC (after all device briefs complete)
- 8:00 PM: Desktop nightly brief
- 8:05 PM: Laptop nightly brief (or parallel)
- 8:10 PM: iPhone device brief
- 8:15 PM: Multi-device aggregation ← This runs

Execution time: <500ms  
Output size: 8-12 KB per day  
Archive: 30 days = ~270 KB

## Integration

### Device Briefs Required

This aggregator depends on:
1. **Desktop Brief** — nightly-security-brief.js at 8:00 PM
2. **Laptop Brief** — nightly-security-brief.js at 8:00 PM (or separate instance)
3. **iPhone Brief** — iphone-security-brief.js at 8:10 PM

All three must complete before multi-device brief runs.

### Data Flow

```
Desktop Report (80/100)
    ↓
Laptop Report (80/100)
    ↓
iPhone Report (95/100)
    ↓
Multi-Device Aggregator
    ├─ Parse all three reports
    ├─ Extract scores
    ├─ Calculate weighted average: 83/100
    ├─ Determine threat level: YELLOW
    ├─ Extract cross-device risks
    ├─ Rank recommendations
    ├─ Aggregate lessons
    └─ Generate unified briefing
    ↓
One-Page Executive Summary
```

## Success Indicators

✅ All three device briefs loaded successfully  
✅ Overall score calculated correctly (weighted average)  
✅ Per-device scores visible  
✅ Threat level determined accurately  
✅ Cross-device risks identified  
✅ Device attribution clear (which device changed)  
✅ Top 5 risks ranked by severity  
✅ Confidence % on findings  
✅ Recommendations actionable  
✅ Lessons aggregated  
✅ One page, readable in <60 seconds  

## Customization

### Adjust Device Weights

Edit scoring formula in `calculateOverallScore()`:

```javascript
// Current: Desktop 40%, Laptop 40%, iPhone 20%
const weights = {
  desktop: 0.4,   // Change this weight
  laptop: 0.4,    // Change this weight
  iphone: 0.2     // Change this weight
};
```

### Add More Devices

To monitor additional devices:
1. Add device name to `deviceNames` array
2. Add brief loading logic for new device
3. Update weights to sum to 1.0
4. Adjust scoring formula

### Change Schedule

Edit `.claude/multi-device-trigger-config.json`:
```json
{
  "schedule": {
    "cron": "20 20 * * *"  // Change to 8:20 PM UTC
  }
}
```

---

**Tone:** Unified SOC overview. CISO perspective.  
**Length:** One page  
**Time:** Under 60 seconds  
**Audience:** You (personal SOC chief)  
**Purpose:** Unified security posture across all devices
