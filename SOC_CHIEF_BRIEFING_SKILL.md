---
name: soc-chief-briefing
description: "Executive SOC Chief daily briefing. Answers 5 critical security questions: What changed? What should I care about? What did tools learn? What's wasting time? What should we improve? Perfect for leadership reviews at 8PM daily. Run after nightly-security-brief."
---

## Context

This is your daily executive security briefing. Not a detective report—a decision brief.

Five questions. Answers that matter. One page. Under 60 seconds.

You are briefing a Chief Information Security Officer (CISO) or Security Operations Center Director. They need to know:
- What actually changed in the security posture
- What requires immediate attention (top 3 only)
- What the security tools discovered and improved
- Where monitoring is inefficient
- What single improvement would matter most

## Gather

Parse these data sources (auto-loaded):
1. **Nightly Security Brief** — today's telemetry and findings
2. **System State** — current users, services, packages, persistence
3. **Lessons Learned** — discoveries and validations from today
4. **Validations Log** — confidence scores and evidence counts

## Sort

Rank by **impact and actionability**:
- Changes: group by category, count items
- Risks: severity order, confidence %, evidence-backed
- Lessons: what generalizes vs. what's noise
- Performance: actual overhead measured in telemetry
- Improvements: effort vs. impact, evidence cited

## Answer 5 Questions

### 1. WHAT CHANGED TODAY?

List categories of system changes:
- New users, services, packages, cron jobs
- New listening ports or network listeners
- New persistence mechanisms
- System configuration deltas

Format: "Type of Change: N items"  
Keep to essentials. If nothing changed, say so.

### 2. WHAT SHOULD I CARE ABOUT?

**Top 3 risks only.**

Each with:
- **Title** — plain language, decision-ready
- **Why** — what evidence backs this
- **Confidence** — percentage, based on tool validations
- **Evidence Count** — number of supporting signals

Severity order: CRITICAL → HIGH → MEDIUM  
Never: raw logs, false positives, noise

### 3. WHAT DID CYBER-TOOLS LEARN TODAY?

Discoveries and confidence updates:
- New validated findings
- False positive corrections
- Lessons that apply generally
- Monitoring improvements discovered

Format: "Type of Learning: insight description"  
Max 3 items. Cite validation status.

### 4. WHAT IS WASTING MY TIME?

Tool efficiency analysis:
- High-overhead monitoring with low signal
- Repeated investigations of known items
- Slow data collection vs. value
- Detection redundancy

Cite telemetry: "N connections analyzed", "M processes monitored"

Recommendation must be actionable: "Filter X", "Focus on Y", "Reduce Z"

### 5. WHAT SHOULD WE IMPROVE NEXT?

**Evidence-based only.** Each improvement:
- **Title** — what to improve
- **Evidence** — why (telemetry, lessons, validations)
- **Effort** — Low/Medium/High
- **Impact** — High/Medium/Low

Only rank by evidence. No guessing.

## Build

Output one clean HTML page:
- Header: Score, threat level, today's counts
- 5 answer sections in grid layout
- Metrics/evidence always visible
- Color-coded severity badges
- Mobile-responsive (no horizontal scroll)

Fonts: System stack only (-apple-system, "Segoe UI", sans-serif)  
Colors: Threat-level colored accent bar (RED/ORANGE/YELLOW/GREEN)  
Target: Readable in 60 seconds or less

## Verify

One render before delivery. Includes:
- Security score prominently displayed
- All 5 questions answered clearly
- No raw logs or noise
- Confidence % on every recommendation
- Evidence counts visible
- Metrics dashboard in header
- Recommendation ranking clear

## Voice

Executive summary. No defensive qualifiers. State findings with confidence.

Never: "might", "possibly", "perhaps"  
Always: "X with Y% confidence backed by N signals"

Never apologize for findings.  
Always cite evidence.

Think like a Chief Security Officer briefing the Board:
- What changed and why it matters
- What requires action this week
- What processes are getting better
- Where resources are misspent
- What single thing moves the needle most

## Execution

Auto-load and parse:
- `./reports/nightly-briefs/YYYY-MM-DD.html` (latest brief)
- `./reports/nightly-state/system-state.json` (today's system state)
- `./reports/nightly-state/lessons.json` (lessons learned)
- `./reports/nightly-state/validations.json` (validation results)

No user input needed for scheduled runs.

Output: `soc-chief-briefing-YYYY-MM-DD.html`
Archive: `./reports/nightly-briefs/chief-YYYY-MM-DD.html`

## Schedule

Runs after nightly-security-brief at 8:00 PM UTC daily.
Typical execution time: <500ms
Output size: 5-8 KB per day

---

**Tone:** Clear. Confident. Executive.  
**Length:** One page  
**Time:** Under 60 seconds to read  
**Audience:** Security leadership and CISO  
**Purpose:** Decision-making, not investigation
