# Next Steps

Milestone frozen 2026-09-04 (see `PROJECT_STATUS.md`). Priority order
for what gets built next, in order.

## 1. WAAP Log Search Integration

**Status:** researched, not built. Backed by MVP #4 Discovery
(`docs/VNETWORK_API_DISCOVERY.md`, `docs/VNETWORK_PRODUCT_DISCOVERY.md`,
`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`) plus a 2026-09-04 schema-level
follow-up, `docs/WAAP_LOG_SEARCH_SCHEMA.md` — full request/response
schema, verbatim sample payloads, and an MCP integration design.

**What it is:** `POST /v1/bsearch` against `openapi.vnetwork.vn` — a
real, callable, Bearer-token-authenticated log search/aggregation
endpoint over WAF+CDN access logs (client IP, URI, status code, user
agent, upstream latency). Ranked the single highest-ROI VNETWORK
capability across all three discovery passes.

**Shape of the build:** same reuse pattern as MVP #3/#4 —
`scripts/create_waap_incident.py`, a new `to_alert()` mapper over
`bsearch` results, thresholding on something concrete (e.g. 4xx/5xx
rate spike, or a `query_string`/`match_phrase` match against a known
bad pattern), feeding the same `score_alert` / `build_issue` /
`create_issue` / `assign_issue` / `compute_labels` /
`build_analysis_comment` / duplicate-detection chain unchanged. One new
label (`waap`) and one new `ENRICHMENT_RULES` entry.

**Open before starting:** what specific threshold/query defines "alert
-worthy" — needs a decision, not a discovery (the API itself is fully
understood, schema included). Three candidate shapes are now on the
table: (a) a `status`/`upstream_status` terms-agg threshold on 4xx/5xx
rate, (b) a `query_string` match against a known-bad URI pattern, or
(c) `mitigation_result` being non-empty / not `"ACL-WHITE"` — though
(c) needs one live test call first to see what other values that field
actually takes (not documented anywhere). Also open: the `domains`
list to query (needs `GET /v3/cdn/domains`, not yet called) and the
`mitigation_result`/`mitigate_result` naming ambiguity found in the
endpoint's own request template — see `docs/WAAP_LOG_SEARCH_SCHEMA.md`
§4/§6 for full detail.

## 2. Healthcheck Webhook Receiver

**Status:** planned, not built. Backed by MVP #5 Discovery
(`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`).

**What it is:** VNETWORK Healthcheck & Alerting's custom-webhook
notification channel (confirmed: endpoint URL + optional HMAC secret,
signed JSON POST, `X-Webhook-Signature` header) delivering directly
into a new MCP-side receiver, which feeds the same GitHub incident
pipeline. The only capability discovered so far that lets VNETWORK
*push* rather than SentinelOps *poll*.

**Shape of the build:** `POST /api/webhooks/vnetwork-healthcheck` on
`audit.sentinelops.fyi`, raw-body HMAC verification (algorithm assumed
HMAC-SHA256 pending confirmation) with constant-time comparison, fail
closed, secret in a platform env var. Full detail and reasoning in the
plan doc.

**Open before starting (blocking, not optional):**
1. The HMAC algorithm, signing base, and payload schema are not
   published anywhere — must be captured from one real test delivery
   (configure a temporary Monitor against a logging-only endpoint)
   before the mapper can be trusted.
2. The source repo/Render service actually running at
   `audit.sentinelops.fyi` was not found on this machine — need to
   know whether this is "add a route to an existing backend" or
   "stand up a new minimal service," which is a materially different
   scope.

## 3. Digital Risk Twin

**Status:** concept sketch only — unlike #1 and #2, this has not gone
through a discovery pass. Nothing below is verified against real
VNETWORK capabilities or scoped against real effort; treat it as a
starting hypothesis for the next discovery round, not a plan.

**Working idea:** a single, continuously-maintained model of
everything SentinelOps actually knows about the organization's real
exposure and posture — built by aggregating data sources this project
has *already* discovered and, in several cases, already integrates,
rather than inventing a new one:

- Cloud attack surface: `GET /v3/cdn/domains`, `/v3/elastic_ips`,
  `/v3/networks/reserves`, `/v3/secgroups`, `/v3/certificates` (all
  already catalogued, ROI-ranked, available today)
- Edge signal: WAAP `bsearch` log aggregates (once #1 above exists)
- Host signal: `security-watch.js` control state, Windows Defender
  detections (already live via MVP #2/#3/#4)
- Push signal: Healthcheck & Alerting webhook deliveries (once #2
  above exists)

The "twin" would be the merged, queryable state across all of these —
not a new alert type, but a standing answer to "what do we actually
expose and what's its current state," that every individual alert
pipeline (WAAP, Healthcheck, security-watch.js) could enrich against
instead of each one starting cold. Closest existing precedent in this
codebase: the same JSON-state-file + diff pattern `security-watch.js`
and the dormant ARP-based Home-SOC collector already use, generalized
across every source above instead of just one.

**Why it's #3, not #1:** it's a synthesis of the other two (and
existing) sources, not a new capability — it only becomes buildable
once #1 and #2 exist to feed it, and it needs its own discovery pass
(what "twin" state actually helps triage a real incident, what storage
shape, what refresh cadence) before it's a plan rather than an idea.

**No dashboards, no databases, no new infrastructure** implied by
default — if a "twin" ends up needing persistent state beyond what a
JSON file can hold, that's a decision for its own discovery pass, not
assumed here.
