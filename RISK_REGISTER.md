# Cyber Tools MCP - Risk Register

**Phiên bản**: v1.0.2  
**Ngày**: 2026-08-21  
**Chủ đề**: Critical Risks & Mitigation cho Production Release

---

## 🔴 CRITICAL RISKS (R-001 to R-007)

### R-001: File Collision (collectEvidence/timeline)

**Mức độ**: HIGH  
**Xác suất**: MEDIUM (khi chạy đồng thời)  
**Tác động**: Data Loss / Overwrite Evidence

**Mô tả**:
```
Claude gọi 3 tools gần như cùng lúc:
- securityAudit
- collectEvidence  
- timeline

Cùng một timestamp → Overwrite file
Mất chứng cứ investigation
```

**Mitigation**:
- ✅ Sử dụng Timestamped + UUID filenames
- ✅ Tạo unique folder per investigation
- ✅ Verify file before write (file locking)
- ✅ Test concurrent execution (Tier 2)

**Status**: MITIGATABLE - add to test suite

---

### R-002: PowerShell Serialization Failure

**Mức độ**: HIGH  
**Xác suất**: HIGH (dễ xảy ra)  
**Tác động**: Broken JSON → Claude crash

**Mô tả**:
```
WMI objects không serialize correctly:
- systemInfo (complex OS object)
- firewallRules (nested structures)
- scheduledTasks (COM objects)
- Get-MpComputerStatus (PowerShell custom types)

Result: {"data": {}} - empty response
Claude: "Dữ liệu không tìm thấy"
```

**Mitigation**:
- ✅ ConvertTo-Json -Depth 5 everywhere
- ✅ Select-Object explicit fields
- ✅ Test high-risk tools in Tier 2
- ✅ Add serialization test cases (7 tools)

**Status**: PARTIALLY MITIGATED (v1.0.1) - VERIFY in v1.0.2

---

### R-003: Access Denied Silent Failure

**Mức độ**: HIGH  
**Xác suất**: MEDIUM  
**Tác động**: False Negatives / Missing Data

**Mô tả**:
```
Tools phụ thuộc admin permissions:
- securityLogs (event log access)
- systemLogs (system log access)
- rdpLogs (RDP events)
- registryRunKeys (HKLM access)

Non-admin user → No error, empty result
Analyst: "Không có sự kiện nào"
Thực tế: "Bạn không có quyền"
```

**Mitigation**:
- ✅ Clear error response: {"success": false, "error": "AccessDenied"}
- ✅ Suggest escalation: "Run as Administrator"
- ✅ Partial results when possible
- ✅ Test on non-admin account (Tier 2)

**Status**: NEEDS TESTING - add to Tier 2

---

### R-004: Query Timeout (Large Dataset)

**Mức độ**: HIGH  
**Xác suất**: MEDIUM  
**Tác động**: Investigation Incomplete / Claude Timeout

**Mô tả**:
```
Tools có thể timeout:
- securityLogs [count: 10000]
- eventLogs [30 days] → 50000+ entries
- timeline [days: 365] - correlate 1000s events
- collectEvidence - full system scan

Timeout 30+ seconds:
→ Claude loses connection
→ Investigation aborted
→ Evidence incomplete
```

**Mitigation**:
- ✅ Set 30-second timeout limits
- ✅ Pagination support (offset/limit)
- ✅ Return partial results + "hasMore" flag
- ✅ Graceful timeout message
- ✅ Test with large datasets (Tier 2: 3 cases)

**Status**: NEEDS IMPLEMENTATION - Tier 2

---

### R-005: False Positive Hunting

**Mức độ**: MEDIUM  
**Xác suất**: MEDIUM  
**Tác động**: Alert Fatigue / Trust Loss

**Mô tả**:
```
Hunting tools trigger on normal behavior:

huntPersistence:
  "Suspicious: svchost.exe" → Normal Windows process
  "Suspicious: Windows Update scheduled task" → System task

huntCredentialDumping:
  "Suspicious: lsass.exe" → Normal process

Result:
→ Analyst ignores alerts
→ Trust in tool decreases
→ Real threats missed
```

**Mitigation**:
- ✅ Test on clean Windows system (Tier 3)
- ✅ Add confidence scoring (Low/Medium/High)
- ✅ Document false positives
- ✅ Add known-good baseline
- ✅ 4 test cases in Tier 2

**Status**: NEEDS TESTING - Tier 2 & 3

---

### R-006: Timeline Integrity Failure

**Mức độ**: HIGH  
**Xác suất**: LOW (but catastrophic)  
**Tác động**: Investigation Invalid / Non-Admissible Evidence

**Mô tả**:
```
Timeline generation:
- Events out of order
- Timestamps incorrect
- Events missing/duplicated
- Time zone handling wrong

Court: "This timeline is unreliable"
Investigation: INVALID

For DFIR work, this is catastrophic.
```

**Mitigation**:
- ✅ Verify event order (ascending timestamp)
- ✅ No future dates in timeline
- ✅ No duplicate events
- ✅ Timezone consistent (UTC)
- ✅ Test in Tier 3 (DFIR E2E)

**Status**: CRITICAL - Tier 3 focus

---

### R-007: Memory Leak on Repeated Execution

**Mức độ**: MEDIUM  
**Xác suất**: LOW  
**Tác影響**: Claude Crash / Server Hang

**Mô tả**:
```
Claude runs same tool 50 times:
- collectEvidence
- timeline
- securityAudit
- eventLogs

Memory usage: +5MB → +10MB → +50MB → +200MB

After 100 runs: Server crashes
Investigation stops
Evidence lost
```

**Mitigation**:
- ✅ Monitor memory per iteration
- ✅ Cleanup resources after each run
- ✅ Close file handles properly
- ✅ Test 50 iterations per high-risk tool
- ✅ Max +50MB increase acceptable

**Status**: NEEDS TESTING - Tier 2

---

## 🟠 MEDIUM RISKS (R-008 to R-012)

### R-008: Special Character Handling

**Mức độ**: MEDIUM  
**Xác suất**: MEDIUM  
**Tác động**: File Not Found / Encoding Errors

**Mô tả**:
```
Non-ASCII paths:
- C:\Users\Nguyễn Văn A\Desktop\file.txt
- C:\Users\José\Downloads\data.json
- C:\Temp\文件.exe

fileMetadata("...Nguyễn...")
→ "Nguyễn?" (Character corruption)
→ File not found error
```

**Mitigation**:
- ✅ UTF-8 encoding everywhere
- ✅ Test with Vietnamese, Chinese, Arabic paths
- ✅ Proper Unicode escaping in JSON

**Status**: Tier 2 testing

---

### R-009: Concurrent Access to Reports Directory

**Mức độ**: MEDIUM  
**Xác suất**: LOW  
**Tác động**: File Lock / Report Not Created

**Mô tả**:
```
Multiple tools write to ./reports/ simultaneously
Report A locking the directory
Report B cannot write
Result: Missing evidence
```

**Mitigation**:
- ✅ Use unique filenames (timestamp + UUID)
- ✅ Separate folders per investigation
- ✅ Test concurrent writes (Tier 2)

**Status**: Tier 2 testing

---

### R-010: Invalid Input Not Validated

**Mức độ**: MEDIUM  
**Xác suất**: MEDIUM  
**Tác động**: Error Message Confusion / Misleading Results

**Mô tả**:
```
processByPid(-1)
→ Result: "Process not found"
→ User: "What does -1 mean?"
→ Not clear: "PID must be positive integer"

scanPort("192.168.1", "not-a-port")
→ Cryptic error message
```

**Mitigation**:
- ✅ Input validation with clear error messages
- ✅ 6 test cases (Tier 2)

**Status**: Tier 2 testing

---

### R-011: Report Format Inconsistency

**Mức độ**: MEDIUM  
**Xác suất**: MEDIUM  
**Tác động**: Dashboard Can't Parse / Manual Analysis

**Mô tả**:
```
Some tools return:
- {"success": true, "data": {...}}

Other tools return:
- {"result": [...]}
- {"items": [...]}
- {"records": [...]}

Dashboard code: complex parsing
Error handling: unclear
```

**Mitigation**:
- ✅ Unified JSON schema (v1.1.0 preparation)
- ✅ All tools same format

**Status**: v1.0.2 testing, v1.1.0 implementation

---

### R-012: Service Unavailability Graceful Degradation

**Mức độ**: MEDIUM  
**Xác suất**: LOW  
**Tác động**: False Negatives / Incomplete Investigation

**Mô tả**:
```
defenderStatus depends on Windows Defender service
User disables Defender for testing
Tool returns: null / empty / error

What should happen?
Clear message: "Windows Defender is not running"
Suggestion: "Start service or re-enable"
```

**Mitigation**:
- ✅ Service availability checks
- ✅ Graceful error messages
- ✅ Helpful suggestions

**Status**: Tier 2 testing

---

## 🟡 LOWER PRIORITY RISKS (R-013 to R-015)

### R-013: Long Path Handling (Windows 260-char limit)

**Mức độ**: LOW  
**Xác suất**: LOW  
**Tác động**: File Not Accessible

**Mitigation**:
- ✅ Use UNC paths when needed
- ✅ Test long paths (Tier 2)

---

### R-014: Missing File Handling

**Mức độ**: LOW  
**Xác suất**: MEDIUM  
**Tác động**: Confusing Error

**Mitigation**:
- ✅ Clear FileNotFound errors
- ✅ 3 test cases (Tier 2)

---

### R-015: Partial Permission Errors

**Mức độ**: LOW  
**Xác suất**: LOW  
**Tác động**: Partial Results

**Mitigation**:
- ✅ Return what we can get
- ✅ Note missing data

---

## 📊 RISK MATRIX

```
Impact
   ↑
   │  R-001  R-002  R-006  R-003  R-004  R-005
   │         HIGH
   │
   │                                 R-007  R-008
   │              MEDIUM
   │
   │                                        R-009 to R-015
   │                      LOW
   └─────────────────────────────────────────────→ Probability
      LOW                MEDIUM              HIGH
```

---

## 🎯 v1.0.2 TEST COVERAGE

### Tier 1: Smoke Test
- Covers: R-002 (serialization), R-004 (timeout checks)

### Tier 2: Stability (45 cases)
- Covers: R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015
- **Focus**: High & Medium risks

### Tier 3: DFIR E2E
- Covers: R-006 (timeline integrity), R-005 (false positives)
- **Focus**: Investigation validity

---

## 📋 MITIGATION TRACKING

### v1.0.2 (QA Phase)
- [ ] R-001: File collision test → Add to Tier 2
- [ ] R-002: Serialization verify → Tier 2 (5 cases)
- [ ] R-003: Access denied test → Tier 2 (5 cases)
- [ ] R-004: Timeout handling → Tier 2 (3 cases)
- [ ] R-005: False positive test → Tier 2 & 3 (4 cases)
- [ ] R-006: Timeline integrity → Tier 3 (CRITICAL)
- [ ] R-007: Memory leak test → Tier 2 (50 iterations)
- [ ] R-008 to R-015: Various → Tier 2

### v1.1.0 (Feature Phase)
- [ ] R-011: Unified JSON schema → Implement

### v2.0.0 (Enterprise Phase)
- [ ] R-012: Service monitoring → Dashboard

---

## 💡 KEY PRINCIPLES

> **Correctness > Features**
>
> If a risk is "correctness" (data, timeline, evidence), it blocks release.
> If a risk is "UX" (error message clarity), it can be addressed after.

---

## SIGN-OFF

**Risk Register Prepared**: 2026-08-21  
**Tech Lead Review**: PENDING  
**Status**: Ready for v1.0.2 testing

---

**Next Action**: 
1. Validate risks with team
2. Map to test cases
3. Execute Tier 1-3 tests
4. Track mitigation status
5. Update after each test phase
