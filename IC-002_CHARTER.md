# IC-002 Charter: Authentication Boundary Analysis

**Opened:** August 22, 2026  
**Investigation Type:** Windows Permission Mechanism Discovery  
**Discipline:** Follow IC-001 proven methodology  

---

## PHILOSOPHICAL FOUNDATION

**What This IS:**
```
Explain the mechanism
↓
Understand why access is denied
↓
Identify the exact boundary
↓
Then design minimal fix
```

**What This IS NOT:**
```
Assume why it's broken
↓
Try various fixes
↓
Hope one works
↓
Waste effort
```

**Core Principle:**
> The fix reveals itself after understanding the mechanism.

---

## INVESTIGATION SCOPE

**NOT:** "Fix authentication audit"

**INSTEAD:** "Identify exact permission boundary mechanism"

### Questions to Answer

```
□ Is it Event Log Readers group membership?
□ Is it Security log ACL permissions?  
□ Is it UAC/elevation token requirement?
□ Is it Local Security Policy?
□ Is it execution context (MCP vs interactive)?
□ Is it combination of above?
```

### Experimental Discovery Plan (E1-E7 Pattern from IC-001)

**E1: Group Membership Test**
```
Command: Get-LocalGroupMember -Group "Event Log Readers"
Question: Is current user in this group?
Expected: Yes/No result
```

**E2: Security Log ACL Test**
```
Command: Get-Acl "\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\..."
Question: What permissions does current user have on Security log?
Expected: ACL object with permission details
```

**E3: UAC Token Test**
```
Command: whoami /priv
Question: Does user have necessary privileges?
Expected: Token elevation requirements identified
```

**E4: Policy Test**
```
Command: auditpol /get /category:*
Question: What audit policies are set?
Expected: Policy configuration details
```

**E5: Execution Context Test**
```
Compare:
  - Direct PowerShell (works)
  - MCP tool invocation (fails)
Question: Is permission different in MCP context?
Expected: Context-dependent behavior identified
```

**E6: Isolation Test**
```
Test each mechanism in isolation:
  - Add user to Event Log Readers (test)
  - Modify ACL (test)
  - Elevate UAC token (test)
Question: Which single change unblocks access?
Expected: Single root cause identified
```

**E7: Verification Test**
```
Reproduce exact failure:
  - Confirm failure with current config
  - Apply identified mechanism
  - Confirm success
Expected: Repeatable, verifiable mechanism
```

---

## SUCCESS CRITERIA

### Phase 1: Root Cause Identified ✅
```
(Likely already true from IC-001 discovery)
Confidence: 97%
Candidate: Permission boundary exists
```

### Phase 2: Mechanism Verified ⏳
```
Required:
  - E1-E7 experimental results
  - Specific mechanism identified (not vague "permission")
  - 95%+ confidence on exact cause
  
Example verified mechanisms:
  ✅ "User not in Event Log Readers group" (specific)
  ❌ "Permission problem" (vague)
  ✅ "Security log ACL requires Admin" (specific)
  ❌ "ACL issue" (vague)
```

### Phase 3: Schema Locked ⏳
```
Before fix design:
  - Exact mechanism documented
  - Preconditions understood
  - Fix approach clear
```

### Phase 4: Minimal Fix Designed ⏳
```
Expected:
  - Operational change (likely: add to group)
  - Or code change (if MCP context issue)
  - 1-5 line modification
  - Low risk
```

### Phase 5: Delta Measured ⏳
```
Metric: Authentication Visibility %
Before: 0% (audit blocked)
After: ~100% (audit succeeds)
Expected Delta: +100%
Gate: PASS if delta > 0%
```

---

## DIFFERENCE FROM IC-001 TRACK B

### IC-001 Track B (MCP Defect)
```
Defect Type:    Application code issue
Investigation:  What's wrong with the wrapper?
Fix:            Change logging method
Risk:           Low (2 lines, isolated)
Scope:          cyber-tools codebase
```

### IC-002 Track A (Windows Boundary)
```
Defect Type:    Environment/permission configuration
Investigation:  Why does Windows deny access?
Fix:            Likely operational (add to group)
Risk:           Medium (touches Windows security)
Scope:          Windows permission model (external)
```

### Key Difference
```
IC-001 Track B:
  Question: How do we fix our code?
  Answer: Stop logging to stdout

IC-002 Track A:
  Question: How does Windows restrict access?
  Answer: [E1-E7 to determine]
```

---

## INVESTIGATION DISCIPLINE

### Discipline Rule 1: Narrow from Vague to Specific
```
Start: "Permission boundary"
↓ (through E1-E7)
End: "Event Log Readers group membership"
```

### Discipline Rule 2: Verify Each Hypothesis
```
Don't assume: "UAC is required"
Instead test:
  1. Create user without UAC elevation
  2. Try to access Security log
  3. Confirm if UAC is actually the issue
```

### Discipline Rule 3: Separate Mechanisms
```
If E3 (UAC) fails AND E1 (Group membership) fails:
  Don't combine them
  Test each individually
  Identify which is blocking access
```

### Discipline Rule 4: Reproduction Test
```
Once mechanism identified:
  1. Reproduce failure (confirm diagnosis)
  2. Apply fix (operational or code)
  3. Reproduce success (confirm cure)
  4. Verify no side effects
```

---

## EXPECTED OUTCOMES

### Scenario A: Group Membership (Most Likely)
```
Finding: User not in "Event Log Readers" group
Fix: Add-LocalGroupMember -Group "Event Log Readers" -Member "tamng"
Complexity: Operational (not code)
Risk: Low
Delta: +100%
```

### Scenario B: ACL Permissions
```
Finding: Security log ACL restricts non-admin read
Fix: Modify ACL to grant user read permission
Complexity: Admin script
Risk: Medium (security log ACL)
Delta: +100%
```

### Scenario C: MCP Context Issue
```
Finding: Permission works in PowerShell, fails in MCP context
Fix: Change how MCP invokes PowerShell (code change)
Complexity: Code (similar to Track B)
Risk: Low (isolated)
Delta: +100%
```

### Scenario D: Combination (Least Likely)
```
Finding: Multiple mechanisms required
Fix: Apply several changes (staged approach)
Complexity: Multiple steps
Risk: Moderate
Delta: +100% (or phased)
```

---

## DELIVERABLES

### IC-002 Root Cause Report
```
Content:
  - E1-E7 experimental results
  - Mechanism identification
  - Confidence level (>95%)
  - Why this mechanism blocks access
  - Operational vs code fix determination
```

### IC-002 Delta Measurement  
```
Content:
  - Before: 0% auth visibility
  - After: 100% auth visibility
  - Measured delta: +100%
  - Gate decision: PASS/FAIL
```

### IC-002 Implementation
```
Content:
  - Specific fix (operational or code)
  - Change details
  - Validation results
  - Zero regression confirmation
```

---

## TIMELINE EXPECTATIONS

| Phase | Duration | Deliverable |
|-------|----------|------------|
| E1-E7 (Discovery) | 1-2 hours | Root cause identified |
| Schema Verification | 1 hour | Mechanism confirmed |
| Fix Design | 0.5 hours | Minimal change defined |
| Implementation | 0.5 hours | Fix deployed |
| Validation | 0.5 hours | Delta measured |
| Documentation | 1 hour | Reports complete |

**Total Expected:** 4-5 hours (similar scope to IC-001)

---

## SUCCESS DEFINITION

IC-002 succeeds if:

- [x] **Mechanism identified** (E1-E7 complete)
- [x] **Verified (>95% confidence)**
- [x] **Minimal fix deployed** (1-5 changes)
- [x] **Delta measured** (0% → ~100%)
- [x] **Zero regressions**

---

## RELATIONSHIP TO IC-001

### What IC-001 Proved
```
Production data reveals specific problems
Root cause analysis works
Minimal fixes have high ROI
Methodology is repeatable
```

### How IC-002 Applies It
```
Same 7-phase cycle
Same experimental discipline
Same minimal fix principle
Same delta measurement gate
```

### Building Block Pattern
```
IC-001: MCP Transport Defect
        Account Visibility: 0% → 100%
        
IC-002: Windows Permission Boundary
        Auth Visibility: 0% → ~100%
        
IC-003: Firewall Visibility
        Firewall Visibility: 0% → ~100%
        
Result: Strong 6/8 → Strong 8/8 domains
```

---

## NOT SCOPE FOR IC-002

```
❌ Refactor Windows security handling
❌ Implement new auth features
❌ Build audit log dashboard
❌ Change MCP security model
❌ Add new cyber-tools features
```

## ONLY SCOPE FOR IC-002

```
✅ Understand exact permission mechanism
✅ Identify blocking factor (group/ACL/UAC/policy)
✅ Apply minimal fix (1-5 changes or operational)
✅ Measure delta (0% → 100%)
✅ Document findings
```

---

## OPENING STATE

```
Problem: Authentication audit blocked
Confidence: High (observed in production)
Root Cause Candidate: Permission boundary
Confidence: 97% (from IC-001)
Mechanism: Unknown (E1-E7 needed)
Status: Ready for discovery phase
```

---

**IC-002 is open.**

**Follow IC-001 methodology.**

**Discover the mechanism, the fix follows.** 🚀
