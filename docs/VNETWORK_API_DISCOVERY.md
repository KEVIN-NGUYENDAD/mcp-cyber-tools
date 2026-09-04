# VNETWORK OpenAPI Discovery

Documentation-only pass: no VNETWORK API endpoints were called, no
resources were provisioned, no credits were spent. The only network
request made was to Postman's own public documentation API
(`documenter.gw.postman.com`, part of the postman.vnetwork.dev vanity
page) to read the published collection JSON — never `openapi.vnetwork.vn`
itself.

## Source

- Postman doc page: `https://postman.vnetwork.dev/view/4429080/2sBY4Qqyts`
  (a JS-rendered Postman Documenter page — its content isn't in the
  static HTML)
- Underlying data API the page itself calls client-side, and that this
  pass read directly:
  `https://documenter.gw.postman.com/api/collections/4429080/2sBY4Qqyts?segregateAuth=true&versionTag=latest`
- Collection: **VNETWORK OpenAPI** (`_postman_id`
  `da6a1e22-8dde-4080-a382-487322584431`), published 2026-07-22,
  schema v2.0.0
- API base: `https://openapi.vnetwork.vn` (a few CDN requests use a
  `{{URL}}` collection variable pointing at the same base)

## Authentication

Bearer token on every request, inherited from the collection level:

```
Authorization: Bearer {{OPENAPI_TOKEN}}
```

No API-key-header scheme was found in this collection (despite "API
Keys supported" in the original brief) — every request in this
collection specifically uses Postman's `bearer` auth type with a
`{{OPENAPI_TOKEN}}` variable. If VNETWORK also offers a separate API-key
scheme, it isn't represented here.

## Catalog by category

106 total endpoints across 4 top-level Postman folders (Infrastructure →
Compute, a separate legacy `Instances (1.0.7)` folder, Content Delivery
Network, and Secure Content Delivery Network). Mapped onto the requested
categories:

| Category | Endpoints | Read-only (GET) | Mutating |
|---|---|---|---|
| Compute | 15 | 6 (1 excluded — see below) | 9 |
| Storage | 21 | 6 | 15 |
| Network | 48 | 15 | 33 |
| Security | 14 | 4 | 10 |
| Monitoring | 4 | 4 | 0 |
| CDN | 3 | 1 | 2 |
| WAAP | 1 | 1 (POST, but a read-only log query — no side effects) | 0 |
| **Projects** | **0** | — | — |
| **Total** | **106** | **39 read-only** (37 GET + 1 read-only POST) | **67 mutating** |

**Gap found:** there is no "Projects" group at all — no
tenancy/organization/project-scoping endpoints anywhere in this
collection. Everything is scoped implicitly to the authenticated
account.

**Gap found:** there is no native alert/webhook/subscription endpoint
anywhere (no `POST /alerts`, no webhook registration). The closest
things to "alerting" are the monitoring/stats endpoints (poll and
threshold yourself) and the WAAP log-search endpoint (query and diff
yourself) — this actually matches SentinelOps' existing architecture
exactly: security-watch.js already works by polling and diffing
locally rather than subscribing to a push feed, so this is a
compatible integration shape, not a blocker.

Full endpoint-by-endpoint catalog with ROI tier, generated from the raw
collection (every one of the 106 endpoints, not just the top 10):

### Compute (15 endpoints)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| HIGH | GET | `/v3/instances` | List instances | Instance inventory — CMDB baseline, detect unexpected new instances. |
| HIGH | GET | `/v1/instances` | List | Instance inventory — CMDB baseline, detect unexpected new instances (legacy/read-only sibling API). |
| MEDIUM | GET | `/v3/instances/:id` | Get instance | Single-instance detail lookup — enrichment for an already-flagged instance. |
| MEDIUM | GET | `/v1/instances/:id` | Show | Single-instance detail lookup — enrichment for an already-flagged instance. |
| LOW | GET | `/v3/instances/:id/schedules` | List schedules | CMDB completeness, no direct alerting signal today. |
| LOW | GET | `/v3/configurations/:type` | Provisioning config | CMDB completeness, no direct alerting signal today. |
| LOW | GET | `/v3/marketplaces` | List marketplaces | CMDB completeness, no direct alerting signal today. |
| EXCLUDE | GET | `/v3/instances/:id/vnc` | Get VNC console | GET but side-effecting (issues a live console session/token) — treat as mutating, security-sensitive. |
| EXCLUDE | POST/PUT/DELETE | *(7 endpoints)* | Create/resize/terminate instance, run action, create/update/delete schedule | Mutating — out of scope. |

### Storage (21 endpoints)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| MEDIUM | GET | `/v3/backups` | List backups | Backup existence/freshness — ransomware-readiness signal. |
| MEDIUM | GET | `/v3/backups/:id` | Get backup | Backup existence/freshness — ransomware-readiness signal. |
| LOW | GET | `/v3/instances/:id/volumes` | List attached volumes | CMDB completeness. |
| LOW | GET | `/v3/instances/:id/snapshots` | List snapshots | CMDB completeness. |
| LOW | GET | `/v3/volumes` | List volumes | CMDB completeness. |
| LOW | GET | `/v3/volumes/images` | List OS images | CMDB completeness. |
| LOW | GET | `/v3/volumes/:id` | Get volume | CMDB completeness. |
| EXCLUDE | POST/DELETE | *(14 endpoints)* | Create/resize/attach/detach/delete volume, snapshot, backup | Mutating — out of scope. |

### Network (48 endpoints)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| MEDIUM | GET | `/v3/networks/reserves` | List reserved IPs | Public IP inventory — attack-surface tracking. |
| MEDIUM | GET | `/v3/elastic_ips` | List elastic IPs | Public IP inventory — attack-surface tracking. |
| LOW | GET | *(13 endpoints)* | List/get networks, routers, static routes, VPCs, peering subnets/groups, load balancers, LB forwards | CMDB completeness, no direct alerting signal today. |
| EXCLUDE | POST/PUT/PATCH/DELETE | *(33 endpoints)* | Create/attach/detach/delete/update across networks, routers, VPCs, peering, load balancers | Mutating — out of scope. |

### Security (14 endpoints)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| HIGH | GET | `/v3/secgroups` | List security groups | Firewall rule inventory — cloud-level control-drift detection, mirrors the security-watch.js pattern from MVP #3/#4. |
| HIGH | GET | `/v3/secgroups/:id` | Get security group | Same — rule-level detail for a flagged group. |
| MEDIUM | GET | `/v3/keys` | List SSH keys | Access-credential inventory — an unexpected key is an access-drift signal. |
| MEDIUM | GET | `/v3/certificates` | List certificates | TLS cert inventory — expiry monitoring is a clean, schedulable alert. |
| EXCLUDE | POST/PUT/DELETE | *(10 endpoints)* | Create/update/delete/attach/detach security groups, SSH keys, certificates | Mutating — out of scope. |

### Monitoring (4 endpoints — all high value)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| HIGH | GET | `/v3/instances/:id/summary` | Get summary | Realtime state + latest monitoring snapshot in one call — cheapest polling target. |
| HIGH | GET | `/v3/instances/:id/monitoring` | Get monitoring | CPU/memory/network time series — anomaly & DoS detection at compute layer. |
| HIGH | GET | `/v3/lbs/:id/stats` | Get statistics | LB request/error stats — cheap health+anomaly signal. |
| HIGH | GET | `/v3/lbs/:id/monitoring` | Get monitoring | LB traffic monitoring — DDoS/traffic-spike detection at the edge. |

### CDN (3 endpoints)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| HIGH | GET | `/v3/cdn/domains` | List | CDN surface inventory — baseline, and correlates with WAAP log results by domain name. |
| EXCLUDE | POST | `/v3/cdn/domains/:id/prefetch` | Prefetch | Mutating — out of scope. |
| EXCLUDE | POST | `/v3/cdn/domains/:id/purge` | Purge Cache | Mutating — out of scope. |

### WAAP (1 endpoint — the single highest-value capability in the API)

| ROI | Method | Endpoint | Name | Note |
|---|---|---|---|---|
| HIGH | POST | `/v1/bsearch` | Bsearch Aggs | Full-text/aggregate query over WAF+CDN access logs. Fields include `http_x_forwarded_for` (client IP), `uri.keyword`, `http_user_agent`, `http_referer`, `status`, `upstream_status`, `upstream_addr`, `upstream_response_time`. Supports regex (`query_string`) and exact-match (`match_phrase`) filters, term aggregation with ordering/size limits, and a `gte`/`lte` time window. This is a read-only *query* despite the POST verb — no resource is created or modified, only a search is executed. |

## Read-only / Metrics / Logging / Alert / Inventory identification (task item 3)

- **Read-only endpoints:** 39 of 106 (37 `GET` + the `bsearch` `POST` query) — every one of them cataloged above with a method of `GET` or the `bsearch` row.
- **Metrics endpoints:** the 4 endpoints in the Monitoring category — `Get summary`, `Get monitoring` (instance), `Get statistics` (LB), `Get monitoring` (LB).
- **Logging endpoints:** exactly one — `POST /v1/bsearch` (WAAP/CDN access-log search & aggregation). No other log-retrieval endpoint exists anywhere in the collection.
- **Alert endpoints:** none exist. No webhook registration, no alert-rule CRUD, no push-subscription mechanism anywhere in the API. Alerting has to be built on the client side by polling Monitoring + WAAP and diffing/thresholding — the same shape SentinelOps already uses for security-watch.js.
- **Resource inventory endpoints:** the "List X" GET endpoints across every category — instances (v1 and v3), volumes, OS images, backups, networks, reserved IPs, elastic IPs, routers, VPCs, peering subnets/groups, load balancers, SSH keys, certificates, security groups, marketplaces, CDN domains. 25 such list endpoints total.

## Top 10 highest-value VNETWORK capabilities for SentinelOps

Ranked by real security signal × low integration cost × fit with the
existing poll-and-diff architecture proven in MVP #3/#4:

1. **`POST /v1/bsearch`** (WAAP log search) — the only genuine security
   log source in the whole API. Client IPs, URIs, status codes, user
   agents, upstream latency, with regex/exact-match filtering and
   aggregation. Directly analogous to what a WAF/CDN "alerts.json"
   would look like if VNETWORK had one — the strongest single
   candidate for a future MVP #5.
2. **`GET /v3/instances/:id/monitoring`** — real CPU/memory/network
   time series per instance; anomaly and DoS detection at the compute
   layer.
3. **`GET /v3/secgroups` / `GET /v3/secgroups/:id`** — cloud firewall
   rule inventory; enables the exact same control-drift detection
   pattern security-watch.js already proved valuable for
   (open-port/rule-change alerting), but at the cloud-network layer
   instead of the host layer.
4. **`GET /v3/lbs/:id/monitoring`** — load-balancer traffic monitoring;
   DDoS/traffic-spike detection upstream of the WAAP.
5. **`GET /v3/lbs/:id/stats`** — LB request/error-rate statistics;
   cheap complementary health+anomaly signal to #4.
6. **`GET /v3/cdn/domains`** — CDN/domain inventory; baseline of the
   protected surface, and the join key to correlate `bsearch` log
   results back to a specific domain.
7. **`GET /v3/instances` (v3) and `GET /v1/instances`** — instance
   inventory; CMDB baseline, detects unexpected new instances (the
   same "new-device" pattern already built — currently dormant — in
   the ARP-based Home-SOC collector).
8. **`GET /v3/instances/:id/summary`** — realtime state + latest
   monitoring snapshot in a single call; the cheapest useful polling
   target for a lightweight periodic health/security check.
9. **`GET /v3/elastic_ips` / `GET /v3/networks/reserves`** — public IP
   inventory; attack-surface tracking, and a future join key for
   threat-intel correlation.
10. **`GET /v3/certificates`** — TLS certificate inventory; expiry
    monitoring is a clean, schedulable, low-noise security alert that
    nothing else in the current SentinelOps pipeline covers.

## Integration opportunities (MCP / GitHub Issues / incident automation)

Sketch only — nothing below was built or called in this pass.

- **MCP tool surface:** each HIGH-tier endpoint above maps cleanly to
  one read-only MCP tool (`vnetworkSecgroups`, `vnetworkWaapSearch`,
  `vnetworkInstanceMonitoring`, `vnetworkLbMonitoring`,
  `vnetworkCdnDomains`, `vnetworkCertificates`) — same shape as the
  existing `modules/*.js` tools (`defenderThreats`, etc.) in this repo.
- **GitHub Issues / incident automation:** the same
  `create_securitywatch_incident.py` pattern from MVP #3/#4
  generalizes directly — normalize a detection into the existing alert
  schema (`source`, `event_type`, `severity`, evidence fields), reuse
  `score_alert` / `build_issue` / `create_issue` / `assign_issue` /
  `compute_labels` / `build_analysis_comment` unchanged, add one new
  `to_alert()`-style mapper per VNETWORK source. Concretely:
  - A `bsearch` poll that thresholds on 4xx/5xx rate or a specific
    `query_string` match → alert type `WAAP_ANOMALY`
  - A `secgroups` baseline/diff (same shape as security-watch.js's own
    baseline.json) → alert type `SECGROUP_DRIFT`
  - A `certificates` expiry check (days-until-expiry below a threshold)
    → alert type `CERT_EXPIRING`
- All three would need a new label (e.g. `vnetwork`, `waap`, `cert`)
  added to `compute_labels()`'s vocabulary and a new row in
  `ENRICHMENT_RULES` — small, additive changes to the existing MVP #4
  code, not a rewrite.

## Explicitly not done in this pass

- No VNETWORK API endpoint was called (only Postman's own public
  documentation API was read)
- No resources were provisioned
- No credits were spent
- No mutating endpoint was called or even attempted
- No code was written or changed
