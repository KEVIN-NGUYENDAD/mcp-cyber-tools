---
name: iphone-security-brief
description: "Daily iPhone security posture briefing. Tracks device configuration, detects changes, identifies risks, and provides actionable recommendations. Perfect for BYOD security and device compliance. Run daily at 8:10 PM after SOC briefings."
---

## Context

This is your daily device security briefing for iPhone/iPad management.

Not forensics. Not deep analysis. Just: "Is my iPhone secure today?"

One page. Answer in 30 seconds. Evidence-backed findings. Actionable recommendations.

You are monitoring managed devices (BYOD program, corporate fleet, or personal device enrolled in MDM). You need to know:
- What changed since yesterday
- What security issues exist
- Why they matter (with confidence %)
- What to do about them
- Trends over 30 days

## Gather

Auto-load from:
1. **Device Data** — Current iPhone configuration (iOS version, screen lock, VPN, profiles, etc.)
2. **Previous Device State** — Yesterday's baseline for delta analysis
3. **Trends Log** — 30-day risk score history
4. **Current State** — Device info, apps, storage, network status

Data sources:
- MDM API (enrollment, compliance, profiles)
- iCloud API (device info)
- Local monitoring (if device is managed)
- Manual import (JSON structure with device properties)

## Sort

Rank findings by:
1. **Severity** (CRITICAL → HIGH → MEDIUM → LOW)
2. **Confidence %** (based on detection method)
3. **Evidence Count** (how many signals support this)
4. **Actionability** (can the user fix it?)

## Answer 5 Questions

### 1. SECURITY SCORE (0-100)

Calculate from:
- Passcode strength (0-10 points)
- VPN status (0-10 points)
- MDM enrollment (0-10 points)
- Auto-updates enabled (0-8 points)
- DNS over HTTPS (0-8 points)
- iOS version currency (0-10 points)
- WiFi security (0-6 points)
- Storage usage (0-5 points)
- Biometric setup (0-5 points)
- Find My enabled (0-5 points)

Threat Level:
- GREEN: ≥85 (Secure)
- YELLOW: 70-84 (Review Soon)
- ORANGE: 50-69 (High Risk)
- RED: <50 (Critical - Action Now)

### 2. CHANGES SINCE YESTERDAY

List:
- iOS version updates
- Security settings changed
- Device profiles added/removed
- VPN connect/disconnect
- New apps installed (count)
- WiFi networks changed
- MDM enrollment status changed
- Auto-update setting changed

Format: "Type: change description" or "No changes detected"

### 3. RISK FINDINGS (MAX 5)

Each finding shows:
- **Title** — plain language, decision-ready
- **Severity** — CRITICAL/HIGH/MEDIUM/LOW
- **Description** — why it matters
- **Confidence %** — detection reliability
- **Recommendation** — what to do

Never: speculation, false positives, noise

### 4. RECOMMENDATIONS (MAX 5)

Prioritized by severity. Each includes:
- **Title** — action to take
- **Priority** — P1/P2/P3
- **Effort** — Low/Medium/High
- **Impact** — Low/Medium/High
- **Evidence** — data supporting this

Evidence from: device config, threat model, best practices

### 5. TREND SUMMARY

Show:
- **Days Tracked** — rolling 30-day window
- **30-Day Average** — risk score trend
- **Direction** — improving/stable/declining
- **Improvements Suggested** — count of actionable improvements

## Build

Output one clean HTML page:
- Header: Score, threat level, change count, findings count
- 5 sections in responsive grid (2 columns on desktop, 1 on mobile)
- Color-coded severity badges
- Metrics always visible
- Mobile-responsive (no horizontal scroll)

Fonts: System stack only  
Colors: Threat-level colored accent bar  
Target: Readable in 30 seconds or less

## Verify

Before delivery:
- Security score prominently displayed (top-left)
- All 5 sections answered clearly
- Confidence % on every finding
- Recommendations ranked by priority
- Severity badges color-coded
- Changes from yesterday visible
- Trend showing 30-day pattern
- No raw device data dumps

## Voice

Executive summary for device owner + security team.

Confident. Clear. No defensive language.

Never: "might have", "possibly could", "perhaps"  
Always: "X with 95% confidence based on Y signals"

Think like a device health report:
- What changed and why it matters
- What security issues require action
- What can wait until later
- What the device is improving on
- What the 30-day trend shows

## Execution

Auto-load and parse:
- Device data (current state JSON)
- Previous device state (for delta analysis)
- Trends log (30-day score history)

Generate:
- `iphone-security-brief-YYYY-MM-DD.html` (local, today's date)
- `./reports/iphone-briefs/YYYY-MM-DD.html` (archive)

## Schedule

Recommended: Daily at 8:10 PM UTC (after SOC briefings complete)

Execution time: <300ms  
Output size: 7-9 KB per day  
Archive: 30 days of briefs = ~220 KB

## Data Integration

### Feed Device Data

Option 1: MDM API call
```javascript
const deviceData = await mdm.getDeviceInfo(deviceId);
```

Option 2: Manual JSON structure
```javascript
{
  model: "iPhone 15 Pro",
  iosVersion: "18.0",
  security: { passcodeEnabled: true, faceIdEnabled: true },
  network: { vpnConnected: true, dnsOverHttps: true },
  device: { mdmEnrolled: true, autoUpdateEnabled: true }
}
```

Option 3: iCloud API
```javascript
const device = await icloud.getDeviceInfo(token);
```

Place device data in: `./reports/iphone-state/current-device.json`

### Trends Over Time

Automatically tracked in: `./reports/iphone-state/trends.json`
- Last 30 days of risk scores
- Trend analysis (improving/stable/declining)
- 30-day average calculation

## Success Indicators

✅ Daily HTML briefing generated  
✅ Security score visible (0-100)  
✅ Threat level prominently displayed  
✅ All changes from yesterday listed  
✅ Top 5 risks ranked by severity  
✅ Recommendations prioritized (P1/P2/P3)  
✅ Confidence % shown on findings  
✅ 30-day trend visible  
✅ Readable in 30 seconds or less  
✅ No errors in execution  

## Integration Points

### With MDM System
- Pull device data from MDM API
- Track compliance state
- Monitor profile status
- Correlate with policy violations

### With Security Team
- Use for BYOD compliance reviews
- Share with device owners
- Track fleet health trends
- Identify risky devices early

### With Nightly SOC Brief
- Runs after SOC Chief Briefing (8:10 PM)
- Provides device-level perspective
- Complements system-level monitoring
- Adds BYOD visibility to security posture

---

**Tone:** Clear. Secure. Device-focused.  
**Length:** One page  
**Time:** Under 30 seconds to read  
**Audience:** Device owner + security team  
**Purpose:** Device health & compliance checks
