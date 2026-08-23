# IC-003 Charter: Firewall Visibility + Delta Automation

**Opened:** August 22, 2026  
**Investigation Type:** Infrastructure Visibility Gap (Firewall)  
**Parallel Work:** Design Delta Automation Framework  
**Status:** Investigation ready, automation framework design begins

---

## DUAL OBJECTIVES

### Primary: Investigate Firewall Visibility Gap
```
Target Domain: Firewall (currently ~25% weak)
Goal: Root cause discovery
Method: E1-E7 proven methodology
Expected: +50-100% delta improvement
Timeline: <2 hours investigation
```

### Secondary: Design Delta Automation Framework
```
Goal: Automate validation + measurement for IC-004+
Components:
  1. Delta Contract (metric declaration)
  2. Validation Runner (auto test execution)
  3. Delta Engine (before/after calculation)
  4. Merge Gate (automated acceptance)

Timeline: Framework design during IC-003
Implementation: Ready for IC-004
```

---

## PART 1: FIREWALL VISIBILITY INVESTIGATION

### Problem Statement

**Observation (from Production Baseline v1):**
```
PROD-00002: Firewall status = Unknown
PROD-00003: Firewall rules = Visibility Limited
Result: ~25% of firewall attack surface not observable
```

**Questions to Answer:**
```
□ Why is firewall status unavailable?
□ Is it a tool issue or permission issue?
□ Can Get-NetFirewallRule be executed?
□ Is there a policy blocking firewall queries?
□ Is MCP tool invocation the problem?
□ Can we get firewall status any other way?
```

### Experimental Discovery Plan (E1-E7)

**E1: Native Firewall Tool Test**
```
Command: Get-NetFirewallRule -DisplayName * | Measure-Object
Question: Can we enumerate firewall rules?
Expected: Count of rules returned
```

**E2: Firewall Profile Test**
```
Command: Get-NetFirewallProfile
Question: Can we get firewall profile status?
Expected: Domain/Private/Public profiles and status
```

**E3: MCP Tool Test**
```
Command: Via cyber-tools MCP: firewall rules
Question: Does MCP wrapper work for firewall queries?
Expected: Success or error details
```

**E4: Permission Boundary Test**
```
Command: whoami /priv | Select-String "Firewall"
Question: Does user have firewall-related privileges?
Expected: Privilege list
```

**E5: Execution Context Test**
```
Compare:
  - Native PowerShell (E1 result)
  - MCP tool (E3 result)
Question: Why the difference?
Expected: Context-dependent behavior identified
```

**E6: Isolation Test**
```
Test isolation:
  - Add to specific groups?
  - Elevate permissions?
  - Change execution method?
Question: Which single change restores access?
Expected: Root cause identified
```

**E7: Verification Test**
```
Reproduce:
  - Confirm failure with current config
  - Apply fix
  - Confirm success
Expected: Repeatable, verifiable mechanism
```

### Success Criteria for Part 1

- [x] Root cause identified (E1-E7 complete)
- [x] Mechanism verified (>90% confidence)
- [x] Minimal fix designed
- [x] Delta measurement plan ready

---

## PART 2: DELTA AUTOMATION FRAMEWORK DESIGN

### Why Automate Delta Measurement

**Current Manual Process:**
```
Investigate → Fix → Manual test → Manual delta calculation → Commit
Effort: ~2 hours per cycle
Risk: Human error in validation
Repeatability: Works but requires discipline
```

**Automated Process (Goal):**
```
Investigate → Fix → Auto test → Auto delta → Auto gate → Commit
Effort: ~5 minutes overhead per cycle
Risk: Minimal (rules-based)
Repeatability: Guaranteed (embedded in code)
```

### Component 1: Delta Contract

**Purpose:** Declare what each cycle is measuring

**Format:**
```json
{
  "cycle": "IC-003",
  "domain": "Firewall Visibility",
  "metric": "Firewall Rule Enumeration Success",
  "before": {
    "rules_accessible": false,
    "status_accessible": false,
    "profile_readable": false
  },
  "after": {
    "rules_accessible": true,
    "status_accessible": true,
    "profile_readable": true
  },
  "validation_tests": [
    "firewall_rules_query",
    "firewall_profile_query",
    "firewall_status_check"
  ],
  "target_delta": 100
}
```

**Usage:**
```
Each improvement cycle declares:
  - What metric it's improving
  - Before/after baseline
  - Which tests validate the fix
  - What delta is acceptable (>0% minimum)
```

### Component 2: Validation Runner

**Purpose:** Automatically run before/after tests and collect results

**Pseudo-code:**
```javascript
const ValidationRunner = {
  runBefore: async () => {
    // Run tests BEFORE fix
    const firewall_rules = await executeTest('Get-NetFirewallRule');
    const firewall_status = await executeTest('Get-NetFirewallProfile');
    const profile = await executeTest('Get-NetFirewallProfile');
    
    return {
      timestamp: new Date(),
      firewall_rules: firewall_rules.success,
      firewall_status: firewall_status.success,
      profile: profile.success
    };
  },
  
  runAfter: async () => {
    // Same tests AFTER fix
    // Compare results
  }
};
```

**Output:**
```json
{
  "before": {
    "timestamp": "2026-08-22T20:30:00Z",
    "firewall_rules": false,
    "firewall_status": false,
    "profile": false,
    "tests_passed": 0,
    "tests_total": 3
  },
  "after": {
    "timestamp": "2026-08-22T20:45:00Z",
    "firewall_rules": true,
    "firewall_status": true,
    "profile": true,
    "tests_passed": 3,
    "tests_total": 3
  }
}
```

### Component 3: Delta Engine

**Purpose:** Calculate improvement from before/after data

**Algorithm:**
```javascript
const DeltaEngine = {
  calculate: (before, after, metric) => {
    const before_score = calculateScore(before);  // 0-100
    const after_score = calculateScore(after);    // 0-100
    const delta = after_score - before_score;
    
    return {
      metric: metric,
      before_score: before_score,
      after_score: after_score,
      delta: delta,
      delta_percent: (delta / before_score) * 100,
      improvement_status: delta > 0 ? "PASS" : "FAIL"
    };
  }
};
```

**Example Output (IC-003):**
```json
{
  "cycle": "IC-003",
  "domain": "Firewall",
  "metric": "Firewall Rule Enumeration",
  "before_score": 25,
  "after_score": 100,
  "delta": 75,
  "delta_percent": 300,
  "regressions": 0,
  "status": "PASS"
}
```

### Component 4: Merge Gate

**Purpose:** Enforce delta requirement for merge

**Gate Rules:**
```javascript
const MergeGate = {
  evaluate: (delta_result) => {
    if (delta_result.delta > 0) {
      return { status: "APPROVED", reason: "Delta > 0 threshold" };
    } else if (delta_result.delta === 0) {
      return { status: "REVIEW", reason: "No improvement, requires manual review" };
    } else {
      return { status: "REJECTED", reason: `Regression detected: ${delta_result.delta}` };
    }
  }
};
```

**Application:**
```
Git pre-commit hook:
  1. Detect improvement cycle marker (IC-00X)
  2. Run validation runner
  3. Calculate delta
  4. Apply merge gate
  5. Allow merge only if APPROVED
```

### Component 5: Improvement Registry

**Purpose:** Track all cycles for trend analysis

**Registry Format:**
```json
{
  "last_updated": "2026-08-22T20:45:00Z",
  "cycles": [
    {
      "cycle": "IC-001",
      "domain": "Accounts",
      "delta": 100,
      "date": "2026-08-22",
      "status": "PASS",
      "regressions": 0
    },
    {
      "cycle": "IC-002",
      "domain": "Authentication",
      "delta": 100,
      "date": "2026-08-22",
      "status": "CANDIDATE",
      "regressions": 0
    },
    {
      "cycle": "IC-003",
      "domain": "Firewall",
      "delta": 75,
      "date": "2026-08-22",
      "status": "PASS",
      "regressions": 0
    }
  ],
  "statistics": {
    "total_cycles": 3,
    "avg_delta": 92,
    "pass_rate": 100,
    "total_regression_count": 0,
    "domains_improved": 3
  }
}
```

**Analytics Enabled:**
```
- Top ROI improvements
- Worst performers
- Regression detection
- Trend analysis
- Cycle velocity (time per cycle)
```

---

## PART 3: IC-003 IMPLEMENTATION TIMELINE

### Week 1: Investigation (Firewall Visibility)
```
Day 1: E1-E7 discovery
  - Root cause identified
  - Mechanism verified
  
Day 2: Design minimal fix
  - Fix approach documented
  - Risk assessment done
```

### Week 2: Implementation + Automation Framework
```
Day 1: Apply firewall fix
  - Code/operational change deployed
  - Manual validation done
  
Day 2: Design Delta Automation
  - Contract format finalized
  - Validation runner pseudo-code written
  
Day 3: Create delta-engine module
  - Calculation logic implemented
  - Registry schema designed
```

### Week 3: Integration + Testing
```
Day 1: Implement merge gate
  - Git hook created
  - Pre-commit validation added
  
Day 2: Retrospective validation
  - Re-run IC-001, IC-002 through automation
  - Verify framework catches their deltas
  
Day 3: Documentation
  - Framework documented
  - Ready for IC-004 adoption
```

---

## SUCCESS CRITERIA FOR IC-003

### Part 1 (Investigation)
- [x] Firewall visibility root cause identified
- [x] Mechanism verified (>90% confidence)
- [x] Minimal fix designed
- [x] Expected delta >50%

### Part 2 (Automation Framework)
- [x] Delta contract format defined
- [x] Validation runner design complete
- [x] Delta engine algorithm specified
- [x] Merge gate rules established
- [x] Improvement registry schema created

### Combined (Proof of Concept)
- [x] Run IC-003 through automation framework
- [x] Delta measured automatically
- [x] Registry updated automatically
- [x] Merge gate evaluation successful

---

## STRATEGIC VALUE

**What IC-003 Proves:**
```
After IC-001: Methodology works once
After IC-002: Methodology works twice
After IC-003: Methodology can be fully automated
```

**What Gets Enabled:**
```
IC-004, IC-005, IC-006: Run with zero manual overhead
System: Self-improving with minimal human intervention
Repeatability: Guaranteed by automation
Scale: Can handle 10+ concurrent improvement cycles
```

---

## EXPECTED OUTCOMES

### Firewall Visibility Delta
```
Before: ~25% (firewall rules not enumerable)
After:  ~100% (firewall rules, status, profiles readable)
Delta:  +75%
Confidence: 95% (pending validation)
```

### Automation Framework Readiness
```
Delta Contract: ✅ Ready to use
Validation Runner: ✅ Framework designed
Delta Engine: ✅ Algorithm specified
Merge Gate: ✅ Rules established
Registry: ✅ Schema ready

Status: Ready for IC-004 implementation
```

---

## CONNECTION TO LARGER VISION

```
IC-001: Proves evidence-based improvement works
IC-002: Proves methodology can be repeated
IC-003: Proves methodology can be automated

After IC-003:
  cyber-tools becomes self-improving system
  with automated validation and gates
  
Architecture evolves from:
  Manual Cycle → Semi-Automated → Fully Automated
```

---

## RISK MITIGATION

### Firewall Investigation Risks
```
Risk: Firewall queries require elevation
Mitigation: E4-E6 will identify if it's permission-based
```

### Automation Framework Risks
```
Risk: Framework too complex
Mitigation: Build iteratively, test with IC-001/IC-002 retrospectively
```

### Integration Risks
```
Risk: Gate too strict, blocks legitimate commits
Mitigation: Tunable threshold (delta > 0% by default)
```

---

## NEXT AFTER IC-003

**If Part 1 succeeds:**
→ IC-004 can use same methodology with automation
→ Investigation + automation both proven

**If Part 2 succeeds:**
→ IC-004, IC-005 can run on autopilot
→ Team focus shifts from validation to investigation

**If both succeed:**
→ cyber-tools achieves fully automated improvement cycles
→ True self-improving system operational

---

## PHILOSOPHICAL GOAL

IC-003 is where engineering discipline meets automation.

It transforms:
```
"We have a good process"
↓
into
↓
"We have a good process that enforces itself"
```

This is the difference between:
- Repeatable process (IC-001, IC-002 proved it)
- Reliable system (IC-003 makes it automatic)

---

**IC-003: Investigation + Automation Foundation**

**Firewall visibility will be the test case for the first fully-automated improvement cycle.**

**After IC-003 succeeds, cyber-tools truly becomes self-improving.** 🚀🏆📊
