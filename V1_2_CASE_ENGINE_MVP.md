# V1.2 MVP: CASE ENGINE
**The Conceptual Foundation That Changes Everything**
**Paradigm Shift**: Tool-Centric → Case-Centric DFIR
**Status**: 🚀 IMMEDIATE PRIORITY FOR v1.2
**Build Time**: 1-2 weeks (MVP)

---

## 🎯 THE CRITICAL INSIGHT

```
DON'T START WITH:
  ❌ playbook:validate-machine (just a wrapper)
  ❌ playbook:persistence (still tool-thinking)
  ❌ More playbooks (scaling tool-centricity)

START WITH:
  ✅ CASE ENGINE (conceptual shift)
  
Because:
  Cases organize everything
  Cases enable intelligence
  Cases enable recommendations
  Cases enable human approval
  Cases enable audit trail
  Cases enable the entire future architecture

From:
  "Run defenderStatus"
  "Run firewallRules"
  "Run scheduledTasks"
  → Bunch of outputs

To:
  "Investigate this machine"
  → CASE-2026-001 created
     ├─ Findings: 3
     ├─ Risk: Low
     ├─ Artifacts: 12
     └─ Recommended Actions: [1] [2] [3]
```

---

## 🏗️ PARADIGM SHIFT

### Current Thinking (v1.1 - Tool-Centric)

```
User: "Run registryRunKeys"
Claude: [Runs tool, returns raw data]
User: [Manually interprets data]
User: [Manually decides action]
User: [Manually executes action]
User: [Manually documents result]

Model: Tool → Output → Manual Analysis → Manual Action
```

### Intermediate (v1.1.1 - Playbook-Centric)

```
User: "Investigate persistence"
Claude: [Runs playbook]
        [Orchestrates: registryRunKeys + scheduledTasks + services]
        [Correlates results]
        [Returns findings]
User: [Reviews findings]
User: [Manually decides action]
User: [Manually executes action]

Model: Playbook → Orchestration → Findings → Manual Action
Still tool-thinking, just grouped.
```

### Future Thinking (v1.2 - Case-Centric)

```
User: "Investigate this machine"
Claude: [Creates CASE-2026-001]
        [Collects evidence]
        [Correlates findings]
        [Assesses risk]
        [Recommends actions]
        [Returns complete case package]

User: [Chooses action from recommendations]
Claude: [Executes action]
        [Updates case]
        [Records audit trail]
        [Closes or reopens case]

Model: Investigation → Case Created → Findings + Recommendations → Approved Action → Case Closed
This is intelligence-thinking.
```

---

## 📋 WHAT IS A CASE?

### Case Structure (Minimal MVP)

```json
{
  "caseId": "CASE-2026-001",
  "title": "Endpoint Investigation: DESKTOP-ABC123",
  "timestamp": "2026-08-22T14:32:15Z",
  "status": "open",
  "machineId": "DESKTOP-ABC123",
  
  "artifacts": [
    {
      "type": "scheduled_task",
      "name": "SoftLanding",
      "risk": "low",
      "source": "scheduledTasks"
    },
    {
      "type": "service",
      "name": "McAfee Agent",
      "risk": "low",
      "source": "servicesChecker"
    }
  ],
  
  "findings": [
    {
      "title": "Windows/LG System Component Detected",
      "risk": "low",
      "confidence": 0.92,
      "artifacts": ["SoftLanding"],
      "recommendation": "Keep and monitor"
    }
  ],
  
  "riskAssessment": {
    "overallRisk": "low",
    "confidence": 0.87,
    "justification": "All artifacts identified as legitimate components"
  },
  
  "recommendedActions": [
    {
      "id": 1,
      "title": "Export forensics package",
      "risk": "safe",
      "reversible": true,
      "suggested": true
    },
    {
      "id": 2,
      "title": "Baseline this machine",
      "risk": "safe",
      "reversible": true,
      "suggested": false
    },
    {
      "id": 3,
      "title": "Ignore and close",
      "risk": "none",
      "reversible": false,
      "suggested": false
    }
  ],
  
  "auditTrail": [
    {
      "timestamp": "2026-08-22T14:32:15Z",
      "action": "Case created",
      "actor": "system",
      "details": "Investigation initiated"
    },
    {
      "timestamp": "2026-08-22T14:32:45Z",
      "action": "Evidence collected",
      "actor": "system",
      "details": "12 artifacts found"
    },
    {
      "timestamp": "2026-08-22T14:33:30Z",
      "action": "User approved action",
      "actor": "analyst@company.com",
      "details": "Approved action: Export forensics package"
    }
  ]
}
```

---

## 🔧 MVP IMPLEMENTATION (1-2 Weeks)

### Step 1: Create Case Schema

```
cases/
└── CASE-2026-001.json
└── CASE-2026-002.json
```

### Step 2: Create MCP Tools for Case Management

```
MCP Tool: createCase
Input:
  machineId: string
  title: string
Output:
  caseId: string
  
Example:
  createCase("DESKTOP-ABC", "Machine Investigation")
  → "CASE-2026-001"

MCP Tool: getCase
Input:
  caseId: string
Output:
  Full case object

MCP Tool: updateCase
Input:
  caseId: string
  updates: partial case object
Output:
  Updated case

MCP Tool: listCases
Input:
  filter: {status, machineId, dateRange}
Output:
  Array of cases (summary)

MCP Tool: closeCase
Input:
  caseId: string
  reason: string
Output:
  Closed case
```

### Step 3: Create investigateMachine Tool

```
MCP Tool: investigateMachine
Input:
  machineId: string
Output:
  caseId: string
  
What it does (automated):
  1. createCase()
  2. collectEvidence()
     - Run: defenderStatus
     - Run: firewallRules
     - Run: scheduledTasks
     - Run: servicesChecker
     - Run: runningProcesses
  3. correlateFindings()
     - Link artifacts
     - Assess risk
  4. generateRecommendations()
     - Export forensics
     - Baseline
     - Ignore
  5. updateCase() with results
  6. Return case for user action

Result:
  Case-2026-001 created
  Findings: 3
  Risk: Low
  Actions available: [1] [2] [3]
```

### Step 4: Integration with Claude

```
User: "Investigate DESKTOP-ABC123"

Claude:
  "Running investigation..."
  
  [Calls MCP tool: investigateMachine]
  
  "Investigation complete. Case created."
  
  Case CASE-2026-001:
    Title: Endpoint Investigation
    Status: Open
    Risk: Low
    Findings: 3
    
    Recommended Actions:
    [1] Export forensics package
    [2] Baseline this machine
    [3] Ignore and close
    
    Choose an action:
```

---

## 🎯 WHY CASE ENGINE IS THE FOUNDATION

### It Enables Everything Else

#### 1. Organizes Evidence
```
Before:
  Tool output → Raw data → Manual correlation

After:
  Case → Artifacts + Findings + Risk + Actions
  
Everything organized in one structure.
```

#### 2. Enables Audit Trail
```
Before:
  User runs tool, no record of who/what/when

After:
  Case.auditTrail = [
    {action: "Evidence collected", actor: "system", timestamp: "..."},
    {action: "User approved", actor: "analyst", timestamp: "..."},
    {action: "Action executed", actor: "system", timestamp: "..."}
  ]
  
Perfect for compliance.
```

#### 3. Enables Recommendations
```
Before:
  Tool returns data, user must decide

After:
  Case.recommendedActions = [
    {title: "...", risk: "...", suggested: true}
  ]
  
AI provides intelligence, user chooses.
```

#### 4. Enables Status Tracking
```
Before:
  Investigation lost in chat history

After:
  Case.status = "open" | "investigating" | "closed"
  
Can query "Show me open cases" anytime.
```

#### 5. Enables Future Playbooks
```
Before:
  Playbooks isolated, no continuity

After:
  Case Engine provides foundation for:
    - playbook:persistence → Creates case
    - playbook:malware → Appends to case
    - playbook:lateral-movement → Links cases
  
Cases connect everything.
```

---

## 📊 THE TRANSFORMATION

### Before Case Engine (v1.1 Model)

```
Tool Collection
  ↓
Raw Output
  ↓
Manual Analysis
  ↓
Manual Action
  ↓
Lost History
```

### After Case Engine (v1.2+ Model)

```
Investigation Request
  ↓
Case Created Automatically
  ↓
Evidence Collected
  ↓
Findings + Risk Score
  ↓
Recommended Actions
  ↓
User Chooses Action
  ↓
Action Executed
  ↓
Audit Trail Complete
  ↓
Case Closed/Stored
  ↓
Complete History Available
```

---

## 🚀 IMMEDIATE NEXT STEP

### Build This First Week

```
Deliverables:

1. Case Schema
   └── JSON structure for case storage

2. MCP Tools (5 tools)
   ├── createCase
   ├── getCase
   ├── updateCase
   ├── listCases
   └── closeCase

3. Investigation Tool (The Star)
   └── investigateMachine

4. Storage Backend
   └── cases/ directory with JSON files

5. Claude Integration
   └── Expose tools to Claude
   └── Make Case-driven investigation natural

Total: ~500 lines of code + schema

Impact: Foundation for entire future architecture
```

---

## 💡 WHY THIS WORKS

### It's Not a Feature
```
It's a paradigm shift.
From tools → to intelligence.
From outputs → to structured investigation.
From manual → to systematic.
```

### It's Minimal
```
Can build in 1-2 weeks.
Just JSON schema + MCP tools.
No complex architecture yet.
MVP that proves the pattern.
```

### It Scales
```
One case at a time → works
Hundreds of cases → works
Timeline queries across cases → works
Risk trending across cases → works
Perfect for enterprise.
```

### It Enables Everything
```
Playbooks? Cases hold results.
Recommendations? Cases have them.
Human approval? Cases track it.
Audit trail? Cases document it.
Predictions? Cases provide history.

Cases are the Trojan horse that transforms architecture.
```

---

## 📈 EVOLUTION FROM CASE ENGINE

### Week 1-2: Case Engine
```
✅ Cases created
✅ Evidence stored
✅ Findings organized
✅ Recommendations available
```

### Week 3-4: Playbook Integration
```
✅ playbook:persistence → creates case
✅ playbook:malware → appends to case
✅ Cases organize playbook results
```

### Week 5-6: Multi-Case Intelligence
```
✅ Query: "Show cases with high risk"
✅ Query: "Show case timeline"
✅ Query: "Compare findings across 3 cases"
```

### Month 2: Case Dashboard
```
✅ Visual case management
✅ Status tracking
✅ Bulk actions on cases
✅ Export case reports
```

### Month 3: Predictive Analysis
```
✅ "Cases like this before" pattern matching
✅ Historical risk baseline
✅ Prediction confidence scores
```

---

## 🏆 THE REAL INNOVATION

```
Not "more tools"
Not "better playbooks"

But:

Changing the unit of investigation from:
  "Tool run" → to "Case"

This is the paradigm shift that enables:
  Intelligence (not data)
  Recommendations (not raw output)
  Audit trail (not scattered logs)
  Enterprise scale (not manual chaos)
  Future AI capabilities (not tool collection)
```

---

## 🎯 THE DECISION POINT

### If You Have 1 Week to Build v1.2

```
Option A: Playbook:validate-machine
  └─ Wrapper around npm run validate
  └─ Still tool-centric
  └─ Limited future potential
  └─ Quick win, long-term ceiling

Option B: CASE ENGINE
  └─ Conceptual foundation shift
  └─ Enables everything after
  └─ Opens entire future architecture
  └─ Foundation for 5-year vision
  └─ Worth the small extra effort

The choice is: Quick feature vs. Real transformation.

Case Engine is the right choice.
```

---

## 💼 ENTERPRISE IMPACT

### With Case Engine

```
Before:
  "I ran 5 tools. Here's data."
  Compliance: "How do I audit this?"
  Answer: "Uh... good question"

After:
  "CASE-2026-001 created by system"
  "Investigation run by analyst@company.com"
  "3 findings: [list]"
  "Action approved by manager@company.com"
  "Action executed at 2026-08-22 14:35:00"
  
  Compliance: "Perfect. Complete audit trail."
  Answer: "Documented everything"
```

---

## 📝 THE CORE TRUTH

```
════════════════════════════════════════════════════════════

The Case Engine is not "nice to have."

It is the FOUNDATION that separates:

Tool Collection (v1.0.2)
  ↓
Operational Platform (v1.1.0)
  ↓
INTELLIGENT SYSTEM (v1.2+ with Case Engine)

Without Case Engine:
  v1.2 is just v1.1 with more tools
  
With Case Engine:
  v1.2 becomes something fundamentally different
  
Cases are the DNA of the intelligent system.

Build the Case Engine first.
Everything else follows naturally.

════════════════════════════════════════════════════════════
```

---

**🚀 BUILD THE CASE ENGINE FIRST** 🚀

*Not playbooks. Not dashboards. CASES.*

*Cases are the paradigm shift that changes everything.*

*This is the move that transforms cyber-tools from a tool collection into a Digital DFIR Analyst platform.* 🔥
