# VNETWORK Product Discovery (Healthcheck & Alerting, WAAP, OpenAPI, Object Storage)

Follow-up to `docs/VNETWORK_API_DISCOVERY.md` (which fully catalogued
the one published `openapi.vnetwork.vn` Postman collection). That pass
found no Healthcheck/Alerting, no Object Storage, and no webhook
endpoints anywhere in that collection. This pass checks whether those
capabilities exist as *separate* VNETWORK products with their own
docs, in the priority order requested: Healthcheck & Alerting → WAAP →
OpenAPI → Object Storage.

Documentation-only. No VNETWORK API endpoint was called, no resources
provisioned, no credits spent. Sources: VNETWORK's public docs site
(`docs.vnetwork.vn`), the WAAP product page (`vnetwork.vn`), and the
previously-catalogued Postman collection — all found via web search or
already in hand, none guessed.

## 1. Healthcheck & Alerting — `docs.vnetwork.vn/docs/observability/healthcheck/overview`

The dedicated alerting product, and structurally the closest thing
VNETWORK has to what security-watch.js already does:

- **Monitors** — individual watchpoints: HTTP URL check, TCP port
  check, DNS record check, TLS certificate check, or a custom
  "data-driven signal" check, on a schedule
- **Alarms** — rules attached to a monitor (trigger condition +
  severity)
- **Incidents** — opened automatically when an alarm condition fires;
  acknowledged/resolved by a user
- **Playbooks** — automated remediation runbooks that can run when a
  linked alarm fires
- **Notification channels:** Email (SMTP), Slack, Microsoft Teams,
  Telegram, **and custom webhooks**

This is the only VNETWORK product with documented native outbound
webhook support anywhere in this discovery.

**No REST API is documented.** The overview page describes web
console / Partner Portal configuration only — no endpoints, no
request/response examples, no API reference link. The service is
explicitly marked **beta** ("features and limits may still change").

**Implication:** if/when this ships an API (or even just a webhook
payload spec), it would let VNETWORK push alerts directly into a
SentinelOps receiver — inverting the poll-and-diff shape
security-watch.js uses today. Not buildable yet; worth revisiting.

## 2. WAAP — `docs.vnetwork.vn/docs/security/waap/overview` + `vnetwork.vn/en-US/products/waap/`

Console modules: Dashboard, Onboarding, Websites, Analytics, AI-WAF,
API Protection, Bot Management, Programmable Mitigation, Emergency
Mitigation, Business Usage, **Logs**, Settings.

Neither the product page nor the docs overview mentions a rule-
management API, a metrics API, an alert-configuration API, or webhook
support specific to WAAP. The one confirmed programmatic surface is
the endpoint already found in the previous discovery pass —
`POST /v1/bsearch` (under "Secure Content Delivery Network > Fetch
Logs" in the Postman collection) — which is almost certainly the API
behind the console's "Logs" module: it queries exactly the fields a
WAF access log would have (client IP, URI, status code, upstream
status, user agent).

## 3. OpenAPI (the general REST API) — `openapi.vnetwork.vn`

This is the collection fully catalogued last pass: 106 endpoints,
Bearer token auth, covering Compute / block Storage (Volumes) /
Network / Security Groups / CDN / the one WAAP log-search endpoint.
Re-confirmed directly against the raw collection JSON this pass with
targeted keyword search:

| Keyword | Matches in the full collection |
|---|---|
| `health` | 0 |
| `webhook` | 0 |
| `alert` | 0 |
| `storage` / `bucket` | 3 — all incidental (generic "storage" in prose, and Elasticsearch aggregation "buckets" in the `bsearch` response schema — not an object-storage feature) |

So: this API has **no Healthcheck/Alerting endpoints, no webhook
endpoints, and no Object Storage endpoints**. Web search independently
confirms VNETWORK is still building out API coverage ("VNETWORK is
currently building comprehensive API documentation for all
services") — consistent with Healthcheck & Alerting and Object Storage
each having product docs but no published REST API yet.

## 4. Object Storage (OSS) — `docs.vnetwork.vn/docs/storage/object-storage/overview`

**S3-compatible** — "any S3 tool or SDK works against it." Supports
buckets (create/configure, versioning, public-access controls, object
lock) and objects (browse/upload/download/version/delete, addressed by
key with prefix-as-folder). Access control via bucket/object
permissions and IAM policies/roles.

**Different credential model than everything else in this API
surface:** Access Key ID + Secret pair (S3-standard), not the Bearer
`{{OPENAPI_TOKEN}}` used by `openapi.vnetwork.vn`. This is a separate
trust boundary to manage if integrated.

**No VNETWORK-specific REST API is documented for OSS** — you use the
standard S3 protocol itself (e.g. `boto3`, `aws s3api`) against
VNETWORK's S3-compatible endpoint, not a custom VNETWORK endpoint. No
mention of logging, metrics, or event notifications (the S3-native
equivalent of bucket notifications) anywhere in the docs found.

## Search results by dimension (as requested)

- **Logs:** only one real source — WAAP's `POST /v1/bsearch` (access
  logs: IP, URI, status, UA, upstream latency). Healthcheck &
  Alerting, Object Storage: no documented log retrieval.
- **Metrics:** the Monitoring endpoints already catalogued
  (`/v3/instances/:id/monitoring`, `/summary`, `/v3/lbs/:id/monitoring`,
  `/stats`) are real and callable today. Healthcheck & Alerting tracks
  uptime/latency but exposes it through the console only, no API.
  WAAP has an "Analytics" console tab, no API. Object Storage: none
  found.
- **Alerting:** Healthcheck & Alerting is the dedicated product for
  this (Alarms → Incidents model) but has no API. The general OpenAPI
  has zero alert-rule endpoints, confirmed again this pass.
- **Webhook support:** confirmed to exist in exactly one place —
  Healthcheck & Alerting's notification channels — and even there,
  it's configured through the console, not an API. No webhook support
  found in WAAP, Object Storage, or the general OpenAPI.
- **API support:** one fully published, endpoint-level REST API exists
  today (`openapi.vnetwork.vn`, Bearer token, 106 endpoints). Object
  Storage is reachable via the generic S3 protocol instead. Healthcheck
  & Alerting and WAAP rule/alert management have no published API.

## Top 10 SentinelOps integrations, ranked by ROI

ROI here = security/ops value × buildability today (per instruction:
discovery only, nothing provisioned or called). Items 1–7 and 10 are
buildable right now with the existing Bearer token, following the
exact `create_securitywatch_incident.py` pattern from MVP #3/#4. Items
8–9 use a different shape and are flagged accordingly.

1. **WAAP log search — `POST /v1/bsearch`.** Available now. The
   richest real security-log data in the whole discovery: client IPs,
   URIs, status codes, user agents. Directly portable into an MVP #5
   using the existing alert → score → GitHub Issue pipeline.
2. **Instance monitoring — `GET /v3/instances/:id/monitoring` /
   `/summary`.** Available now. Real CPU/memory/network metrics;
   anomaly/DoS detection at the compute layer.
3. **Security Groups — `GET /v3/secgroups` (+ `:id`).** Available now.
   Cloud firewall inventory; the same control-drift pattern
   security-watch.js already proved out, one layer up.
4. **Load Balancer monitoring/stats — `GET /v3/lbs/:id/monitoring`,
   `/stats`.** Available now. Traffic/DDoS anomaly signal at the edge.
5. **CDN domain inventory — `GET /v3/cdn/domains`.** Available now.
   Baseline of the protected surface; join key to correlate WAAP log
   results by domain.
6. **Instance inventory — `GET /v3/instances`, `GET /v1/instances`.**
   Available now. CMDB baseline / unexpected-new-instance detection.
7. **Certificate inventory — `GET /v3/certificates`.** Available now.
   TLS expiry alerting — no other source in the pipeline covers this.
8. **Healthcheck & Alerting webhook channel.** Not buildable today —
   console-only, beta, no API. Ranked this high anyway because it is
   the single best strategic fit on this entire list: a purpose-built
   Monitors → Alarms → Incidents model with native outbound webhooks
   would let VNETWORK *push* into a SentinelOps receiver instead of
   SentinelOps polling it. Revisit the moment an API or webhook-config
   endpoint ships.
9. **Object Storage inventory via the standard S3 API** (`ListBuckets`,
   `ListObjectsV2`, `GetBucketAcl`, `GetBucketVersioning`, etc.).
   Available now, but through the generic S3 protocol with a separate
   Access Key/Secret credential, not the Bearer-token OpenAPI — a
   distinct integration (e.g. `boto3`), not a drop-in extension of the
   existing pipeline. Value: public-bucket/ACL misconfiguration is one
   of the most common real-world cloud findings, and nothing else here
   covers it.
10. **Elastic IPs / Reserved IPs — `GET /v3/elastic_ips`,
    `GET /v3/networks/reserves`.** Available now. Public
    attack-surface inventory.

## Explicitly not done in this pass

- No VNETWORK API endpoint was called (Postman documentation API and
  public docs pages only)
- No resources were provisioned
- No credits were spent
- No infrastructure was created
- No code was written or changed
