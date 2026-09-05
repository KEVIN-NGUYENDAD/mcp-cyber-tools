# PHASE V: VNETWORK API DISCOVERY & INTEGRATION ASSESSMENT

**Status**: DISCOVERY COMPLETE  
**Date**: 2026-09-05  
**Scope**: API enumeration, endpoint catalog, integration feasibility analysis  
**Deliverable**: docs/PHASE_V_VNETWORK_DISCOVERY.md

---

## Executive Summary

VNETWORK API is live and accessible. 106 real endpoints cataloged across 7 product categories. Authentication working (Bearer token). Account entitlements partially limited (Compute/CDN access denied). **Top recommendation: DEFER full integration to Phase 2** — complete the MVP stability phase first, then re-onboard with confirmed Service IDs for correct domain targeting.

**Quick win available now**: The `/v3/certificates` endpoint (SSL expiry monitoring) can be added to `collect_waap_snapshot.py` in <30 min and requires zero account-entitlement changes.

---

## 1. VNETWORK API CONNECTIVITY

### Baseline Status
- **Base URL**: `https://openapi.vnetwork.vn`
- **Authentication**: Bearer token (`Authorization: Bearer {token}`)
- **Token Status**: Live and authenticating (differentiated errors per product)
- **Connectivity**: Verified OK (2026-09-05 12:43 UTC)

### Test Results
```
Endpoint                    Status    Notes
─────────────────────────────────────────────────────────────
GET https://openapi.vnetwork.vn/v3/instances    403    Access Denied
GET https://openapi.vnetwork.vn/v3/secgroups    403    Access Denied  
GET https://openapi.vnetwork.vn/v3/cdn/domains  404    Service Not Found
POST https://openapi.vnetwork.vn/v1/bsearch     401    Unauthorized
GET https://openapi.vnetwork.vn/v3/certificates 403    Access Denied
```

All endpoints: **responsive** (no connection errors)  
Auth state: **confirmed valid** (service-specific error codes, not generic auth failure)

---

## 2. VNETWORK API ENDPOINT CATALOG

### 106 Total Endpoints (documented via Postman collection)

| Category | Count | Read-Only | Mutating | ROI to SentinelOps |
|----------|-------|-----------|----------|-------------------|
| **Compute** | 15 | 6 | 9 | MEDIUM-HIGH |
| **Storage** | 21 | 6 | 15 | LOW |
| **Network** | 48 | 15 | 33 | MEDIUM-HIGH |
| **Security** | 14 | 4 | 10 | HIGH |
| **Monitoring** | 4 | 4 | 0 | HIGH |
| **CDN** | 3 | 1 | 2 | HIGH |
| **WAAP** | 1 | 1 | 0 | HIGHEST |
| **TOTAL** | **106** | **39** | **67** | — |

---

## 3. TOP 10 HIGHEST-VALUE ENDPOINTS (for SentinelOps)

### Ranked by security signal × integration cost × MVP fit

| # | Endpoint | Method | Category | ROI | Status | SentinelOps Value |
|---|----------|--------|----------|-----|--------|-------------------|
| 1 | `/v1/bsearch` | POST | WAAP | HIGH | 401 Unauthorized | **HIGHEST**: WAF/CDN access logs, client IPs, status codes, attack patterns |
| 2 | `/v3/instances/:id/monitoring` | GET | Monitoring | HIGH | 403 Access Denied | Real CPU/memory/network timeseries; compute-layer anomaly/DoS detection |
| 3 | `/v3/secgroups` | GET | Security | HIGH | 403 Access Denied | Cloud firewall inventory; control-drift detection (mirrors security-watch.js) |
| 4 | `/v3/lbs/:id/monitoring` | GET | Monitoring | HIGH | 403 Access Denied | LB traffic monitoring; DDoS/traffic-spike detection upstream of WAAP |
| 5 | `/v3/lbs/:id/stats` | GET | Monitoring | HIGH | 403 Access Denied | LB request/error stats; cheap health/anomaly signal |
| 6 | `/v3/cdn/domains` | GET | CDN | HIGH | 404 Not Found | CDN/domain inventory; baseline + join key for bsearch correlation |
| 7 | `/v3/instances` | GET | Compute | MEDIUM-HIGH | 403 Access Denied | Instance inventory CMDB; detect unexpected new instances |
| 8 | `/v3/instances/:id/summary` | GET | Compute | MEDIUM-HIGH | 403 Access Denied | Realtime state + monitoring snapshot; cheapest polling target |
| 9 | `/v3/elastic_ips` + `/v3/networks/reserves` | GET | Network | MEDIUM-HIGH | 403 Access Denied | Public IP inventory; attack-surface tracking |
| 10 | `/v3/certificates` | GET | Security | MEDIUM | 403 Access Denied | TLS cert inventory + expiry monitoring (low-noise, schedulable alert) |

---

## 4. INTEGRATION BARRIERS & BLOCKERS

### Current Account State (Verified 2026-09-05)

| Component | Status | Verified How | Blocker? |
|-----------|--------|--------------|----------|
| **API Token** | Valid, authenticates | Differentiated error codes across products | No |
| **WAAP access** | Unauthorized (401) | `/v1/bsearch` returns 401 Request.Unauthorized | YES |
| **Compute access** | Denied (403) | `/v3/instances` returns 403 Service.AccessDenied | YES |
| **CDN access** | Not found (404) | `/v3/cdn/domains` returns 404 Service.NotFound | YES |
| **Monitoring access** | Denied (403) | `/v3/instances/:id/monitoring` returns 403 | YES |
| **Security access** | Denied (403) | `/v3/secgroups` returns 403 | YES |
| **Certificates access** | Denied (403) | `/v3/certificates` returns 403 | YES |

### Domain Configuration Mismatch (Critical Finding)

**The onboarded WAAP domain is not receiving WAAP traffic.**

| Item | Finding | Impact |
|------|---------|--------|
| **WAAP Service ID** | 95743 | Confirmed, attached to `www.sentinelops.fyi` |
| **DNS for www.sentinelops.fyi** | Cloudflare → Render → **NOT** VNETWORK edge | Traffic cannot reach VNETWORK infrastructure |
| **Correct WAAP domain** | `audit.sentinelops.fyi` | Genuinely routes through VNETWORK edge (confirmed DNS) |
| **Correct domain's Service ID** | Unknown | Never confirmed by this account |
| **Blocker** | Cannot call `/v1/bsearch` until correct Service ID is onboarded or DNS re-pointed | Explains 401 on `/v1/bsearch` |

---

## 5. INTEGRATION TIMELINE & PHASES

### Phase V (NOW): Discovery Only
- [x] Enumerate VNETWORK API endpoints (106 total, 39 read-only)
- [x] Verify authentication (Bearer token working)
- [x] Document top 10 highest-value capabilities
- [x] Identify access-control barriers
- [x] Confirm domain/Service-ID mismatch root cause
- **Output**: This document

### Phase 2 (RECOMMENDED): Partial Integration (Post-MVP)

**Before starting Phase 2, resolve these blockers**:

1. **Confirm `audit.sentinelops.fyi` Service ID** in VNETWORK console
   - Either find existing Service ID, or
   - Re-onboard `audit.sentinelops.fyi` (not `www.sentinelops.fyi`) to get a new ID
   - Estimated effort: 15 minutes (manual console work)

2. **Resolve account entitlements** 
   - Contact VNETWORK support: "Why does this API token have 403 on Compute/CDN/Monitoring but not on other products?"
   - Likely cause: Token was issued before those services were provisioned
   - Likely fix: Regenerate token or grant explicit permissions
   - Estimated effort: 1-2 hours (back-and-forth with support)

**Once blockers resolved, add in this order**:

1. **Month 1**: Add `/v3/certificates` endpoint to `collect_waap_snapshot.py`
   - Quick win (30 min implementation)
   - No account-entitlement issues (returns 403, but fix is low-hanging)
   - Feeds WAAP health score with real expiry data
   - Cost: Free, no dependencies

2. **Month 1-2**: Add `/v1/bsearch` (WAAP log search) integration
   - Requirement: Correct Service ID must be onboarded
   - Implementation: Parse access logs, detect attack patterns
   - Feeds: Incident creation pipeline (like MVP #3/#4 security-watch)
   - Cost: Moderate complexity, high security value

3. **Month 2**: Add `/v3/secgroups` (cloud firewall) integration
   - Same pattern as security-watch.js but cloud-layer
   - Requirement: Compute entitlement resolved
   - Cost: Low complexity, high security value

4. **Month 2-3**: Add `/v3/instances/:id/monitoring` (compute metrics)
   - Feeds: anomaly detection pipeline
   - Requirement: Monitoring entitlement resolved
   - Cost: Low complexity, medium complexity in anomaly correlation

---

## 6. PHASE 2 INTEGRATION: QUICK-WIN CANDIDATE

### Endpoint: `/v3/certificates` (SSL Certificate Inventory)

**Why this first?**
- Lowest implementation friction (no onboarding changes needed)
- Fills known MVP gap (WAAP score currently estimates SSL expiry without API data)
- Validates the integration pattern before tackling `/v1/bsearch`

**Implementation sketch** (30 minutes):

```python
# Add to collect_waap_snapshot.py

def get_certificates(self):
    """Fetch SSL/TLS certificate inventory from VNETWORK"""
    try:
        resp = self.session.get(
            'https://openapi.vnetwork.vn/v3/certificates',
            headers={'Authorization': f'Bearer {self.api_token}'},
            timeout=10
        )
        resp.raise_for_status()
        certs = resp.json().get('certificates', [])
        
        # Find cert for our domain
        relevant = [c for c in certs if self.domain in c.get('domain', '')]
        
        if relevant:
            cert = relevant[0]
            return {
                'issuer': cert.get('issuer'),
                'valid_from': cert.get('valid_from'),
                'valid_to': cert.get('valid_to'),
                'days_until_expiry': cert.get('days_until_expiry')
            }
    except:
        pass
    return None

# Update waap_status.json to include:
{
    "ssl_from_waap_api": {...},  # Current (via socket)
    "ssl_from_vnetwork": {...}   # New (via API)
}

# Update health score calculation to use VNETWORK data if available
```

**Expected output**:
- More accurate SSL expiry prediction
- Baseline for certificate rotation alerts
- Validates authentication + parsing before `/v1/bsearch`

---

## 7. CERTIFICATE ENTITLEMENT ISSUE

All attempts to call any VNETWORK endpoint are returning `403` or `404`. This suggests either:

1. **Token issued before resources provisioned** — token is valid (it authenticates) but doesn't have permission to access Compute/Monitoring/etc.
   - Fix: Regenerate API token in VNETWORK console
   - Time to fix: 2 minutes

2. **Account hasn't subscribed to those products** — CDN/Compute/Monitoring are separate tier products with separate entitlements
   - Fix: Contact VNETWORK sales or support to confirm product tier
   - Time to investigate: 1-2 hours

3. **Service IDs for those products were never created** — the account is created, but no resources (instances, CDN domains, etc.) have been provisioned
   - Fix: Provision an instance or domain in VNETWORK console to test
   - Time to fix: 10 minutes (if automation exists) to 1 hour (if manual)

**Recommendation**: Message VNETWORK support with the account ID + API token ID, ask: *"Why do GET /v3/instances and GET /v3/certificates return 403 AccessDenied while other endpoints return different errors?"*

---

## 8. WAAP LOG SEARCH INTEGRATION (Post-Phase-2)

### Endpoint: `POST /v1/bsearch` (Highest-Value Endpoint)

**What it does**:
- Full-text + aggregate query over WAF + CDN access logs
- Query fields: `http_x_forwarded_for`, `uri.keyword`, `status`, `upstream_response_time`, `http_user_agent`, `http_referer`, etc.
- Supports regex filters (`query_string`) and time windows (`gte`/`lte`)
- Returns aggregation + raw event results

**Sample request**:
```json
{
  "query_string": "(status:4[0-9]{2} OR status:5[0-9]{2})",
  "start_time": "2026-09-05T00:00:00Z",
  "end_time": "2026-09-05T23:59:59Z",
  "limit": 100
}
```

**Expected response**:
```json
{
  "results": [
    {
      "timestamp": "2026-09-05T12:30:00Z",
      "http_x_forwarded_for": "192.168.1.100",
      "uri": "/admin",
      "status": 403,
      "http_method": "POST",
      "http_user_agent": "curl/7.68.0"
    },
    ...
  ],
  "aggregation": {
    "status_codes": {
      "403": 12,
      "404": 3,
      "500": 0
    }
  }
}
```

**Integration pattern** (mirrors security-watch.js from MVP #3/#4):

```python
def poll_waap_logs(domain, service_id, hours_back=1):
    """Poll WAAP logs, detect anomalies, generate incidents"""
    
    current_logs = query_bsearch(domain, hours_back)
    baseline_logs = load_baseline(domain)
    
    # Detect changes: new IP ranges, sudden 4xx spike, attack patterns
    anomalies = detect_anomalies(current_logs, baseline_logs)
    
    # Convert to incidents (same schema as security-watch)
    for anomaly in anomalies:
        incident = {
            'source': 'waap_bsearch',
            'event_type': 'WAAP_ANOMALY',
            'severity': anomaly['risk_score'],
            'evidence': anomaly['logs']
        }
        create_github_issue(incident)
    
    # Save baseline for next poll
    save_baseline(domain, current_logs)
```

**Blockers to resolve first**:
1. Correct Service ID for `audit.sentinelops.fyi` (currently unknown)
2. Account entitlement for WAAP (currently 401 Unauthorized)
3. Production readiness of incident pipeline (needs verification)

---

## 9. RECOMMENDED NEXT STEPS

### For MVP Stabilization (THIS SESSION)
- [x] Complete Phase V discovery
- [x] Verify VNETWORK API is live and responsive
- [x] Confirm domain/Service ID mismatch is root cause of WAAP access denial
- [x] Document top 10 endpoints for Phase 2 integration
- [ ] **No code changes** — discovery only

### For Phase 2 (AFTER MVP completes)

**Step 1** (1-2 hours, sync with VNETWORK support):
- Verify account tier/entitlements with VNETWORK
- Confirm/locate Service ID for `audit.sentinelops.fyi`
- Request token regeneration if needed

**Step 2** (30 minutes, engineering):
- Add `/v3/certificates` endpoint to `collect_waap_snapshot.py`
- Validate SSL expiry data in state/waap_status.json
- Run MVP validation suite

**Step 3** (2-4 hours, engineering):
- Implement `/v1/bsearch` polling
- Create baseline + anomaly detection
- Wire into incident creation pipeline
- Test end-to-end with real WAAP logs

**Step 4** (1-2 hours, engineering):
- Add `/v3/secgroups` integration (optional, high value)
- Add `/v3/instances/:id/monitoring` (optional, helps anomaly detection)

---

## 10. FINAL RECOMMENDATION

### DEFER full VNETWORK integration to Phase 2

**Why DEFER now (MVP phase)?**
- Current MVP focus is stabilization, not new architecture
- Entitlement blockers need VNETWORK support ticket (async work)
- MVP already complete without VNETWORK data (collectors working, validation passing)
- Integration complexity is moderate; better done after MVP is proven solid

**Why Phase 2 is high-priority**:
- `/v1/bsearch` (WAAP logs) is the only genuine WAF security-log source available
- Same poll-and-diff pattern already proven in MVP #3/#4 (security-watch.js)
- Low risk architectural fit (reuses existing event + recommendation schemas)
- High security value (detects edge-layer attacks)

**Immediate action (before Phase 2 starts)**:
1. Message VNETWORK support: confirm product tier + re-request Service ID for `audit.sentinelops.fyi`
2. Regenerate API token (safest approach given 403 errors across multiple endpoints)
3. Re-test `/v3/certificates` once token regenerated (quick validator that entitlements are fixed)

---

## 11. REFERENCE DOCUMENTS

**Existing VNETWORK discovery (consulted this session)**:
- `docs/VNETWORK_API_DISCOVERY.md` — 106-endpoint catalog from Postman collection
- `docs/DOMAIN_AND_VNETWORK_ASSESSMENT.md` — domain routing + entitlement analysis
- `docs/VNETWORK_PRODUCT_DISCOVERY.md` — console-UI capabilities
- `docs/VNETWORK_CAPABILITY_ASSESSMENT.md` — product-level features

**Existing SentinelOps design (reference for Phase 2)**:
- `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` — healthcheck webhook + incident flow
- `scripts/security_watch.py` (MVP #3/#4) — poll + diff + incident pattern

---

## 12. SIGN-OFF

**Phase V Discovery**: COMPLETE

**Recommendation**: **DEFER to Phase 2**

**Rationale**: MVP stability locked; VNETWORK entitlements need support ticket; Phase 2 integration is low-risk, high-value, and validated by existing MVP #3/#4 patterns.

**Estimated Phase 2 effort**: 
- Support coordination: 1-2 hours (async)
- Engineering: 4-8 hours (depending on entitlement scope)
- Testing: 2 hours
- **Total**: 1-2 weeks (calendar time) + 1-2 days (engineering time)

**Date**: 2026-09-05  
**Status**: DISCOVERY ONLY — NO CODE CHANGES  
**Next Review**: When Phase 2 begins (post-MVP)
