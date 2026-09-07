# Telegram Dashboard - Formatted Output Examples

## /status Command

```
━━━━━ SECURITY STATUS ━━━━━

Risk Profile
🟠 HIGH
Score: 74/100

Monitored Assets
🖥️ 11 Devices
🌐 Multiple Network Zones

Threat Summary
🚨 18 Open Incidents
   🔴 7 Critical
   🟠 11 High

Detection Engine
🎯 21 Threat Patterns
✅ Actively Monitoring
⚙️ Polling: Active
```

## /open Command

```
━━━━━ INCIDENT QUEUE ━━━━━

🔴 CRITICAL THREATS (7)
────────────────────────────────
INC-0001 | Persistence Detected
  Confidence: 98%
INC-0002 | Lateral Movement
  Confidence: 95%
INC-0003 | Credential Dumping
  Confidence: 92%

🟠 HIGH PRIORITY (11)
────────────────────────────────
INC-0004 | Suspicious Process
  Host: LAPTOP-01
INC-0005 | Registry Persistence
  Host: SERVER-01

🟡 MEDIUM (0)

🟢 LOW (0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## /executive Command

```
┌─ SENTINELOPS EXECUTIVE ─┐

📊 ASSET POSTURE
11 Monitored Devices
Multiple Security Zones Active

🚨 THREAT LANDSCAPE
18 Open Incidents
  └ 🔴 7 Critical
  └ 🟠 11 High Severity

🎯 OVERALL RISK
🟠 HIGH
  Score: 74/100

🔒 APPLICATION SECURITY
✅ SSL/TLS: VALID
  87 days until cert renewal

🌐 DOMAIN OPERATIONS
✅ DNS Health: 100%

└────────────────────┘
```

## Design Principles

✅ **Visual Hierarchy** - Use borders and spacing
✅ **Severity Colors** - 🔴 Red, 🟠 Orange, 🟡 Yellow, 🟢 Green
✅ **Card Layout** - Organized sections with clear labels
✅ **Icon Usage** - Emoji for quick visual scanning
✅ **No Raw Data** - Only relevant metrics shown
✅ **Executive Format** - Brief, actionable information

## Real SOC Console Resemblance

- CrowdStrike Mobile: Clean card design with severity indicators
- Microsoft Sentinel Mobile: Structured sections with quick metrics
- Splunk Mobile: Risk scores and incident counts at a glance

This is NOT a debug log. This IS a mobile security dashboard.
