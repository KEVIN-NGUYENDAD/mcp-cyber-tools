# ROADMAP.md - Feature Development Timeline

**Project**: SentinelOps MCP Cyber Tools  
**Planning Horizon**: 2026-2027  
**Last Updated**: 2026-09-10

---

## 📅 Release Timeline

```
2026-Q3 (CURRENT)           2026-Q4           2027-Q1          2027-Q2+
├─ v1.1.1 ALPHA           ├─ v1.2 STABLE    ├─ v2.0 PROD    └─ v2.1+ SCALE
│  (Foundation)           │  (Validation)    │  (Dashboard)     (Advanced)
└─ Phase 1: Approval      └─ Phase 2: Dash  └─ Phase 3: Cloud
```

---

## 🎯 Version Roadmap

### ✅ v1.1.1 - ALPHA Foundation (2026-08-22) **DELIVERED**

**Focus**: Event-sourced architecture, intelligent decision engine, validation framework

**Features Completed**:
- [x] Event-Sourced Case Engine with audit trails
- [x] Trust Engine (source credibility scoring)
- [x] Shadow Asset Detection module
- [x] Threat Intelligence Correlation
- [x] Incident Triage & Classification
- [x] Playbook Registry (reusable procedures)
- [x] Cross-Case Learning (knowledge transfer)
- [x] Recommendation Engine
- [x] KPI Measurement (5-tier scorecard)
- [x] Approval Layer (Case → Findings → Approval → Execution)
- [x] Persistence Detection patterns (9 hunt engines)

**Test Coverage**: 85%+ validation suite passing  
**Docs**: Complete architecture, playbooks, API reference

---

### 🔄 v1.2 - STABLE Validation (2026-10 to 2026-12) **IN PROGRESS**

**Focus**: Accuracy validation, gate assessment, production hardening

**Planned Features**:
- [ ] 90% Decision Accuracy validation (hard gate)
- [ ] Registry Rule optimization (+40% improvement over baseline)
- [ ] Cross-system event correlation enhancements
- [ ] Large-scale dataset handling (1M+ events)
- [ ] Mobile device detection expansion
- [ ] Performance optimization (sub-1s response times)
- [ ] Extended test coverage (95%+)
- [ ] Security hardening & penetration testing
- [ ] Compliance audit (SOC 2 Type II readiness)

**Success Criteria**:
```
✓ Decision Accuracy ≥ 90% for 3+ consecutive months
✓ False Positive Rate < 5%
✓ Investigation time saved ≥ 30 minutes (average)
✓ All playbooks tested in 50+ real investigations
✓ Zero security incidents in test environment
```

**Release Date**: Early 2027 (pending gate passage)

---

### 🚀 v2.0 - PRODUCTION Dashboard (2027-01 to 2027-03) **BLOCKED UNTIL v1.2 GATE**

**Prerequisites**: ❌ Requires v1.2 accuracy gate (90%+)

**Focus**: User interface, visualization, operational dashboards

**Planned Features**:
- [ ] React-based SOC Dashboard
- [ ] Real-time incident visualization
- [ ] KPI trending & analytics
- [ ] Custom alerting rules builder
- [ ] Team collaboration features (comments, assignments)
- [ ] Integration with SIEM platforms (Splunk, ELK)
- [ ] Mobile app (iOS/Android)
- [ ] Advanced threat hunting UI
- [ ] Automated playbook creation assistant

**Blocked Features** (until accuracy ≥ 90%):
- ❌ AI CISO Assistant (would operate on unreliable decisions)
- ❌ Autonomous response automation (too risky at <90% accuracy)
- ❌ Horizontal scaling (premature optimization)

**Estimated Dev Time**: 8-12 weeks (if gate passed)

---

### 🌐 v2.1+ - SCALE & ADVANCED (2027-Q2+) **CONTINGENT**

**Prerequisites**: ✓ v2.0 production + 6+ months operational stability

**Planned Features**:
- [ ] Cloud deployment (AWS, Azure, GCP)
- [ ] Multi-tenant architecture
- [ ] Advanced ML/AI reasoning layer
- [ ] Automated playbook generation
- [ ] Threat prediction models
- [ ] Supply chain risk assessment
- [ ] OT/ICS security focus
- [ ] Industry-specific bundles (Healthcare, Finance, Gov)

---

## 📊 Feature Status Matrix

| Feature | v1.1.1 | v1.2 | v2.0 | v2.1+ | Priority |
|---------|--------|------|------|-------|----------|
| Core Investigation | ✅ | ✅ | ✅ | ✅ | CRITICAL |
| Accuracy Validation | ✅ | 🔄 | ✅ | ✅ | CRITICAL |
| Playbook Registry | ✅ | 🔄 | ✅ | ✅ | HIGH |
| Dashboard UI | ❌ | ❌ | 🔄 | ✅ | MEDIUM |
| AI CISO | ❌ | ❌ | ❌ | 🔄 | LOW (BLOCKED) |
| Cloud Deployment | ❌ | ❌ | ❌ | 🔄 | LOW (DEFERRED) |
| Mobile App | ❌ | ❌ | 🔄 | ✅ | LOW |

**Legend**: ✅ Done | 🔄 In Progress | ❌ Backlog

---

## 🎲 Current Backlog (Prioritized)

### P0 - BLOCKING (prevents v1.2 release)
```
[ ] Decision Accuracy < 90% - Need 2+ months improvement work
[ ] Edge cases in Shadow Asset Detection
[ ] Cross-system event correlation accuracy
[ ] Performance bottleneck in event parsing (>100K events)
```

### P1 - HIGH (v1.2 target)
```
[ ] Registry Rule optimization sprint
[ ] Mobile device hunt patterns
[ ] Compliance audit preparation
[ ] Security hardening (pen test)
[ ] Extended playbook library (50+ playbooks)
```

### P2 - MEDIUM (v2.0 candidate)
```
[ ] React dashboard components
[ ] SIEM integrations
[ ] Custom alert rules
[ ] Team collaboration features
```

### P3 - LOW (v2.1+ or parking lot)
```
[ ] Supply chain risk module
[ ] OT/ICS-specific hunting
[ ] Multi-tenant architecture
[ ] Autonomous response system
```

---

## 🚦 Gate Criteria & Milestones

### GATE 1: v1.2 Accuracy (CURRENT - BLOCKING ALL PROGRESS)
**Status**: 🟡 IN ASSESSMENT (60% accuracy, needs 90%)

**Requirements**:
```
✓ Decision Accuracy ≥ 90% (validated over 200+ cases)
✓ FP Rate < 5% (false positives)
✓ Investigation time delta ≥ 30 min (documented)
✓ All 9 hunt engines passing validation
✓ Registry improvements verified (+40% baseline)
✓ No critical security issues found
```

**Timeline**: Estimated 2-3 months of improvement work  
**Owner**: Security Architect + Data Science team

---

### GATE 2: v2.0 Production Readiness (AFTER GATE 1)
**Status**: 🔴 BLOCKED (depends on v1.2 passing)

**Requirements**:
```
✓ Accuracy gate passed (≥90% for 3 months)
✓ SOC 2 Type II audit passed
✓ Dashboard UI fully tested
✓ Zero critical bugs in v1.2
✓ Team training completed
✓ Runbooks documented
```

**Estimated Date**: Early 2027 (if GATE 1 passed by Nov 2026)

---

## 📝 Known Constraints

### ⛓️ Hard Constraints (Not negotiable)
- **NO feature expansion** until accuracy ≥ 90%
- **NO autonomous response** without human approval layer
- **NO horizontal scaling** until v2.0 production
- **NO breaking API changes** after v1.2 release

### ⚠️ Risk Areas
- **Large dataset handling** (1M+ events) - needs optimization
- **Cross-system correlation accuracy** - data quality dependent
- **Performance at scale** - current benchmarks at 100K events
- **Compliance requirements** - SOC 2 Type II in progress

---

## 🔗 Related Documents

- **PROJECT_STATE.md** - Current phase details
- **IMPROVEMENT_METHODOLOGY.md** - How improvements are validated
- **/docs/ARCHITECTURE.md** - System design & components
- **/docs/PLAYBOOKS/** - Hunt patterns & procedures

---

**Next Review Date**: 2026-10-10  
**Owner**: Kevin (Tam) Nguyen - Security Architect  
**Last Modified**: 2026-09-10
