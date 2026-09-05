# SentinelOps Status

## 🔒 Milestone Frozen — 2026-09-04

Current milestone (MVP #1–#4 build, plus the VNETWORK discovery/plan
work below) is frozen as of this checkpoint. Canonical naming for the
discovery work, to remove ambiguity between the build-MVP numbering
(#1–#4, all shipped code) and the VNETWORK research track:

- **MVP #4 Discovery** — the research behind **WAAP Log Search
  Integration** (next-steps priority #1). Covers the full VNETWORK
  OpenAPI catalog, the Healthcheck/WAAP/Object Storage product
  discovery, and the 17-category capability assessment. Docs:
  `docs/VNETWORK_API_DISCOVERY.md`, `docs/VNETWORK_PRODUCT_DISCOVERY.md`,
  `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`. Detailed findings in the
  "VNETWORK OpenAPI Discovery" / "VNETWORK Product Discovery" /
  "VNETWORK Capability Assessment" sections below.
- **MVP #5 Discovery** — the research + implementation plan behind the
  **Healthcheck Webhook Receiver** (next-steps priority #2). Doc:
  `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`. Detailed findings in the "MVP
  #5: VNETWORK Healthcheck Webhook Receiver" section below.

Next-step priorities and scope: see `NEXT_STEPS.md`.

**Post-freeze discovery (2026-09-04, same day, after the checkpoint
above):** `docs/WAAP_LOG_SEARCH_SCHEMA.md` — full `POST /v1/bsearch`
request/response schema, verbatim sample payloads, and an MCP
integration design for NEXT_STEPS #1 (WAAP Log Search Integration).
Documentation-only, nothing implemented. Detail in the "WAAP Log
Search — Schema & MCP Plan" section below.

## Completed

✅ MVP #1 - Fake Alert Pipeline
✅ MVP #2 - Windows Defender Real Alert Pipeline
✅ MVP #3 (investigation) - Wazuh Verification
✅ MVP #3 - Live security-watch.js Telemetry Pipeline
✅ MVP #4 - Incident Enrichment (labels + MCP analysis comment)
✅ MVP #4 Discovery — VNETWORK OpenAPI + Product Discovery + Capability Assessment (documentation-only, feeds WAAP Log Search Integration)
✅ MVP #5 Discovery — Healthcheck Webhook Receiver plan (documentation + plan-only, not built)

## Architecture

```
Windows Defender ─┐
security-watch.js ┴→ alerts.json
                       ↓
                      MCP
                       ↓
                   Risk Score
                       ↓
              Duplicate Detection (24h)
                 ↓            ↓
         new alert      existing alert
              ↓                ↓
       GitHub Issue    Update occurrence
              ↓          count + last_seen
              └────────┬───────┘
                        ↓
              Auto Labels + MCP Analysis Comment
                        ↓
              Assign KEVIN-NGUYENDAD
                        ↓
                  GitHub Mobile
                        ↓
                      iPhone
```

## Commits

MVP #1:
d70a085

MVP #2:
8ec96f2

MVP #3:
d5b7819

MVP #4:
5f6a9ea

## Current State

Working:
- GitHub integration
- Issue creation
- Assignment
- Mobile visibility
- Risk scoring
- Live security-watch.js telemetry (real alert source)
- Duplicate detection (24h window, occurrence count + last_seen on the issue itself)
- Auto labels (critical/high/defender/control-drift/firewall, computed per alert)
- MCP analysis comments (risk score, reason, recommendation — posted on create and on duplicate updates)

Not Yet Implemented:
- WAAP integration

Ruled out (see investigation docs):
- Wazuh alerts.json — not installed, will not be built
- Suricata eve.json — not installed, will not be built

## MVP #3: Wazuh Verification

Wazuh verification completed.

Result:
No Wazuh installation found.

Do not build Wazuh integrations. Investigation frozen. No code changed.
See `docs/MVP3_WAZUH_INVESTIGATION.md` for full findings.

## Home-SOC Source Discovery

Completed 2026-09-04. Discovery/verification only, no code changed. See
`docs/HOME_SOC_SOURCE_DISCOVERY.md` for full findings.

Result, ranked (real + already running + closest fit to existing
scoring/GitHub pipeline):

1. **`security-watch.js` → `alerts.json`** (in
   `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`) —
   real, actively scheduled (`HOME-SOC-Scan-And-Export`, last run
   success 9/3/2026), clean alert schema, currently 0 open alerts (5/5
   controls match baseline). **Leading candidate for MVP #3 replacement.**
2. Windows Defender — already proven in MVP #2, still available
3. Windows Event Logs — real and live, but no process-creation telemetry
   without an auditpol change (out of scope)
4. `C:\mcp-cyber-tools\reports\home-soc-state` — a second, separate
   Home-SOC implementation on this host; dormant since 2026-08-29
5. Suricata — not installed, ruled out

## MVP #3: Live security-watch.js Telemetry

Built on the discovery above. Source: `security-watch.js`'s live
`alerts.json` at
`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\alerts.json`
— the endpoint-control watcher already running on this host via the
`HOME-SOC-Scan-And-Export` scheduled task. No new infrastructure was
built; Wazuh and Suricata remain out of scope, per the frozen
investigation.

New script: `scripts/create_securitywatch_incident.py`. Reuses
`score_alert`, `build_issue`, `create_issue`, `assign_issue`, `ASSIGNEE`,
`github_request`, `REPO_OWNER`, `REPO_NAME` from
`create_test_incident.py` unchanged, same pattern as MVP #2's
`create_defender_incident.py`. The only new logic is `to_alert()`
(maps a security-watch.js alert entry onto the existing alert schema)
and 24-hour duplicate detection.

**Duplicate detection:** GitHub itself is the source of truth — no
separate local state file. An open issue is a duplicate if its title
matches (title is stable per alert type: severity + event type + risk
score) and its "Last Seen" is within 24 hours. A duplicate gets its
body's `## Occurrence Tracking` block updated in place (`Occurrences`
+1, `Last Seen` refreshed) instead of a new issue.

**Finding — bug in security-watch.js (not fixed, out of scope):** its
`FIREWALL_DISABLED` and `DEFENDER_DISABLED` rules use
`control: 'firewall'` / `control: 'defender'`, but the actual
baseline/state object keys are `fw` / `def`. `baseline_value` /
`current_value` resolve to `undefined` and are silently dropped by
`JSON.stringify` for just those two rule types (DNS/RDP/SSH are
unaffected — their `control` names match). `to_alert()` in the new
script handles this defensively by omitting the field rather than
printing a misleading "None".

**Verification (2026-09-04):** Windows Firewall (Public profile) was
briefly disabled and immediately re-enabled (exposure window: a few
seconds, admin-run, single guarded command) to produce one real
detection:

```
Before: True → security-watch.js detects FIREWALL_DISABLED → alerts.json updated → After: True
```

Ran the pipeline twice against that one real alert:

| Run | Result |
|---|---|
| 1st | New issue created: **Issue #6** — `[CRITICAL] Firewall Disabled \| Risk 95`, assigned to KEVIN-NGUYENDAD |
| 2nd (same alert, still within 24h) | No new issue — Issue #6 updated: `Occurrences: 2`, `Last Seen` refreshed |

https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/6

Success criteria met: a real alert from security-watch.js created a
GitHub incident, and a repeat of the same real alert updated it instead
of duplicating it.

## MVP #4: Incident Enrichment

Enhances the MVP #3 pipeline in place — same script
(`scripts/create_securitywatch_incident.py`), same source
(`security-watch.js` → `alerts.json`), same GitHub destination. No
dashboards, no databases, no new infrastructure.

**Auto labels** (`compute_labels()`): a subset of `critical` / `high` /
`defender` / `control-drift` / `firewall`, chosen per alert from its
severity, source, and event type. Applied via GitHub's
"add labels" endpoint, which creates labels that don't exist yet — no
separate label-provisioning step needed. Applied on both the new-issue
path and the duplicate-update path (idempotent — re-adding an existing
label is a no-op).

**MCP Analysis Comment** (`build_analysis_comment()`): posted as an
issue comment — Risk Score, Reason (bullets), Recommendation (numbered
list) — sourced from a small per-event-type table
(`ENRICHMENT_RULES`) covering security-watch.js's 5 known alert types,
with a generic fallback for anything else. Posted on every processed
alert, including duplicates (a duplicate's comment adds a
"Recurrence detected — occurrence #N" note), so the issue timeline
carries a running record of each detection.

**Duplicate handling:** unchanged from MVP #3 (GitHub issue is the
source of truth, 24h window) — re-verified still correct with
enrichment layered on top.

**Verification (2026-09-04):** ran the pipeline again against the same
real `FIREWALL_DISABLED` alert from MVP #3 (still within the 24h
window). Result, confirmed directly via `gh issue view 6`:

- Duplicate detected correctly — Issue #6 updated (`Occurrences: 3`),
  no new issue created
- Labels applied: `critical`, `control-drift`, `firewall`
- Comment posted, exact format:
  ```
  ## MCP Analysis

  _Recurrence detected -- occurrence #3._

  **Risk Score:** 95

  **Reason:**
  - Firewall disabled
  - Security control drift detected

  **Recommendation:**
  1. Re-enable firewall
  2. Check recent changes
  3. Review related events
  ```
- Assignee unchanged: KEVIN-NGUYENDAD

https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/6

The new-issue path calls the identical `compute_labels()` /
`build_analysis_comment()` / `add_labels()` / `add_comment()` functions
(without the recurrence note) — not re-triggered separately in this
pass to avoid an unnecessary second real firewall toggle; the create
path itself (issue creation + assignment) was already verified in
MVP #3.

## VNETWORK OpenAPI Discovery

Completed 2026-09-04. Documentation-only — no VNETWORK API endpoint was
called, no resources provisioned, no credits spent. Read the public
Postman collection behind `https://postman.vnetwork.dev/view/4429080/2sBY4Qqyts`
(via its own data API, `documenter.gw.postman.com` — never
`openapi.vnetwork.vn`). Full catalog, every one of the 106 endpoints
ranked by ROI, and integration sketches:
`docs/VNETWORK_API_DISCOVERY.md`.

**Auth:** Bearer token (`Authorization: Bearer {{OPENAPI_TOKEN}}`) on
every request. Base: `https://openapi.vnetwork.vn`.

**Totals:** 106 endpoints — 39 read-only (37 GET + 1 read-only POST
query), 67 mutating (excluded from ranking). No "Projects" category
exists in this API. No native alert/webhook endpoints exist anywhere —
alerting has to be built client-side by polling + diffing, which is
exactly SentinelOps' existing security-watch.js shape.

**Top 10 highest-value capabilities for SentinelOps** (full rationale
and full 106-endpoint ranked table in the doc):

1. `POST /v1/bsearch` — WAAP/CDN log search & aggregation (client IPs,
   URIs, status codes, UA) — the only real security-log source in the
   API
2. `GET /v3/instances/:id/monitoring` — instance CPU/memory/network
   time series
3. `GET /v3/secgroups` (+ `:id`) — cloud firewall rule inventory,
   control-drift detection (mirrors security-watch.js)
4. `GET /v3/lbs/:id/monitoring` — load-balancer traffic monitoring
5. `GET /v3/lbs/:id/stats` — LB request/error statistics
6. `GET /v3/cdn/domains` — CDN surface inventory, join key for #1
7. `GET /v3/instances` (v3) / `GET /v1/instances` — instance inventory
   / CMDB baseline
8. `GET /v3/instances/:id/summary` — realtime state + latest
   monitoring snapshot in one call
9. `GET /v3/elastic_ips` / `GET /v3/networks/reserves` — public IP /
   attack-surface inventory
10. `GET /v3/certificates` — TLS cert inventory, expiry alerting

Nothing implemented yet — discovery and ranking only, per instruction.

## VNETWORK Product Discovery (Healthcheck & Alerting, WAAP, OpenAPI, Object Storage)

Completed 2026-09-04. Documentation-only, no VNETWORK API endpoint
called, no resources/credits used. Follow-up to the discovery above —
checked whether Healthcheck & Alerting and Object Storage exist as
separate VNETWORK products (they weren't in the Postman collection).
Full detail: `docs/VNETWORK_PRODUCT_DISCOVERY.md`.

**Findings:**
- **Healthcheck & Alerting** (beta) — real product: HTTP/TCP/DNS/TLS
  monitors → alarms → incidents → playbooks, with notification
  channels Email/Slack/Teams/Telegram/**custom webhooks**. The only
  place native webhook support exists anywhere in VNETWORK's stack —
  but **no REST API is documented**, console/Partner-Portal only.
- **WAAP** — console has AI-WAF, Bot Management, API Protection,
  Emergency Mitigation, and a "Logs" module; no rule-management or
  alert-config API documented beyond the `bsearch` log-search endpoint
  already catalogued.
- **Object Storage (OSS)** — real, S3-compatible product (buckets,
  objects, versioning, IAM). Uses a **separate credential model**
  (Access Key/Secret, not the Bearer token). No VNETWORK-specific REST
  API — integrate via the standard S3 protocol instead. No
  logging/metrics/notifications documented.
- Re-confirmed against the raw Postman collection: zero matches for
  "health", "webhook", "alert" anywhere in `openapi.vnetwork.vn`; the
  only "storage"/"bucket" mentions are incidental prose, not an object-
  storage feature.

**Top 10 SentinelOps integrations, ranked by ROI** (full rationale in
the doc):

1. `POST /v1/bsearch` (WAAP log search) — available now
2. `GET /v3/instances/:id/monitoring` / `/summary` — available now
3. `GET /v3/secgroups` (+`:id`) — available now
4. `GET /v3/lbs/:id/monitoring` / `/stats` — available now
5. `GET /v3/cdn/domains` — available now
6. `GET /v3/instances` / `GET /v1/instances` — available now
7. `GET /v3/certificates` — available now
8. Healthcheck & Alerting webhook channel — **not buildable yet** (no
   API), but the best strategic fit on the list — VNETWORK could push
   alerts instead of SentinelOps polling. Revisit when an API ships.
9. Object Storage via the standard S3 API — available now, but a
   separate credential/integration shape (S3 SDK, not Bearer token)
10. `GET /v3/elastic_ips` / `GET /v3/networks/reserves` — available now

Nothing implemented — discovery and ranking only, per instruction.

## VNETWORK Capability Assessment (Partner Portal exploration attempt)

Completed 2026-09-04. Task asked for authenticated Partner Portal
exploration (`partner.vnetwork.vn/services`) with login/screenshot
evidence. **That access does not exist in this environment** — no
browser automation tool, no VNETWORK MCP connector, no stored
credentials. An unauthenticated fetch of that URL returns only a bare
page title behind a login wall — confirmed, not assumed. Per the
user's choice, the full capability assessment was built instead from
VNETWORK's public documentation (`docs.vnetwork.vn`) plus the two
discovery passes above. Full per-service breakdown (18 services across
all 17 requested categories, each fact marked CONFIRMED (docs) or NOT
DOCUMENTED): `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`.

**New findings this pass (beyond the two discoveries above):**
- **Multi-CDN Orchestration** has a confirmed, rich metrics API (5xx
  error rates, domain health, traffic/cache/geo analytics) via the
  same `openapi.vnetwork.vn` surface — ranks as high-ROI as WAAP.
- **"Projects"** exists as an Organizations-console concept (isolated
  workspaces), not a compute-API resource — explains why the OpenAPI
  catalog has zero Projects endpoints.
- **Security finding:** API keys are account-wide, unscoped, with no
  documented rotation or usage-audit API — a single leaked key
  compromises every product in this assessment. Mitigation today is a
  manual console review, not code.
- Kubernetes, Databases, Container Registry, Serverless Functions, and
  Usage & Cost Management are all either not self-serve yet
  ("coming soon"/early access) or use a different integration shape
  (kubectl, not the Bearer-token API) — none buildable today.
- SSL/TLS Certificates has a real Activity-feed audit trail (actor,
  IP, UA, change payload) separate from the `/v3/certificates` API
  endpoint already catalogued.

**Top 10 Opportunities and Crazy But Realistic Ideas:** full detail in
the doc. Headline picks — WAAP log alerting (#1, same as before),
Multi-CDN health/5xx alerting (new, #2), an "attack-surface diff bot"
daily-digest idea that reuses the already-built (but unused)
`nightly-security-brief-trigger.js`/`home-soc-brief.js` pattern from
the Roaming project tree, pointed at VNETWORK data instead of the LAN.

**If CTO, next 3 projects:** (1) MVP #5 — WAAP `bsearch` → GitHub
Issue, (2) the attack-surface diff bot, (3) a standing monthly check
on Healthcheck & Alerting's API/webhook spec and Container Registry
GA — the two highest-strategic-fit capabilities that simply aren't
buildable yet.

Nothing implemented — discovery and assessment only, per instruction.

## MVP #5: VNETWORK Healthcheck Webhook Receiver (plan only)

Completed 2026-09-04. Plan only — nothing implemented, no domain
touched, no VNETWORK Monitor/Channel configured. Full plan:
`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`.

```
VNETWORK Healthcheck & Alerting -> Webhook -> MCP -> Risk Score +
Duplicate Detection -> GitHub Issue -> Auto Labels + MCP Analysis
Comment -> Assign KEVIN-NGUYENDAD -> GitHub Mobile
```

**Verified the claim, didn't just take it:** re-checked directly
against `docs.vnetwork.vn/docs/observability/healthcheck/notifications`
(a page not fetched in the earlier discovery passes). Confirmed:
custom webhook channel, configurable endpoint URL, optional HMAC
secret, "signed JSON POST," `X-Webhook-Signature` header. **Not
documented anywhere:** the HMAC algorithm, the signing base, and the
payload schema — these need to be captured from one real test
delivery before implementation, not assumed.

**Deployment location — checked both domains directly (DNS + HTTP),
not assumed from names:**
- `sentinelops.fyi` — confirmed static (this homepage repo:
  `vite`/`react` only, no server). **Ruled out** — cannot run
  signature-verifying server code at all.
- `audit.sentinelops.fyi` — confirmed **real and live**, CNAME'd to
  VNETWORK's own CDN with a Render origin behind it. This corrects an
  earlier assumption in this project: the `wafCaseStudy` content in
  `sentinelops-homepage/src/data/content.js` describing "Hardening
  audit.sentinelops.fyi with VNetwork WAAP" is not narrative/marketing
  copy — it describes an actually-deployed setup.
- **Recommended: `audit.sentinelops.fyi`.** Open question that needs
  an answer from Kevin before implementation: the source repo/Render
  service actually running there wasn't found anywhere on this
  machine — need to know whether a route can be added to an existing
  backend there, or whether a new minimal service needs to be stood
  up and pointed at that subdomain.

**Endpoint path:** `POST /api/webhooks/vnetwork-healthcheck`
(namespaced for future providers, e.g. a WAAP webhook later).

**HMAC validation strategy:** verify against the *raw* request body
before JSON parsing; HMAC-SHA256 as the default assumption (unconfirmed
— first thing to verify against a real delivery); constant-time
comparison (`hmac.compare_digest` / `timingSafeEqual`) against
`X-Webhook-Signature`; fail closed (401) on missing/invalid signature;
secret in a platform env var, never committed; log rejections without
logging the secret.

**Pipeline reuse:** no new pipeline logic — only a new HTTP receiver +
`to_alert()` mapper feed into the exact MVP #3/#4 chain unchanged
(`score_alert`, `build_issue`, `create_issue`, `assign_issue`, the 24h
duplicate-detection functions, `compute_labels`,
`build_analysis_comment`), extended with one new label
(`vnetwork-healthcheck`) and one new `ENRICHMENT_RULES` entry.

## WAAP Log Search — Schema & MCP Plan

Completed 2026-09-04, post-freeze. Documentation-only follow-up to the
VNETWORK OpenAPI/Product/Capability discovery passes above, closing out
`NEXT_STEPS.md` #1's "the API itself is fully understood" claim at the
field-schema level instead of just the endpoint-catalog level. No
VNETWORK API endpoint was called. Full detail:
`docs/WAAP_LOG_SEARCH_SCHEMA.md`.

**Confirmed the 5 requested fields against `POST /v1/bsearch`'s own
docs table:** source IP (`http_x_forwarded_for`), URI (`uri.keyword`),
status code (`status` for the WAF/edge response, `upstream_status` for
the origin), user agent (`http_user_agent`). The fifth — attack
indicators — is **not** in the endpoint's documented field table, but
a real field for it (`mitigation_result`, one confirmed value
`"ACL-WHITE"` = allow-listed) was found inside the request template's
own commented-out examples — undocumented in prose, but genuinely
present and usable. A second, textually distinct field name
(`mitigate_result`) also appears once; whether that's a real second
field or a typo in VNETWORK's own template is unresolved without a
live test call.

**Full request/response schema captured verbatim** (top-level fields,
the `Query`/`Term`/`Order`/`Filter` sub-objects, the documented `Key`
field list) plus the collection's own saved example request and both
saved example responses (200 success, 401 invalid-domain) — all
reproduced exactly in the doc, nothing paraphrased into an assumed
shape.

**One real contradiction found and flagged, not resolved:** the docs
table marks `domains` as Mandatory; the request template's own comment
says it's optional and defaults to all authorized domains if omitted.

**MCP integration plan (design only):** a new read-only tool
`vnetworkWaapSearch` (name already sketched in
`docs/VNETWORK_API_DISCOVERY.md`) plus `scripts/create_waap_incident.py`
following the exact `create_securitywatch_incident.py` structure —
same `to_alert()` → `score_alert` → `build_issue` → `create_issue` →
`assign_issue` → `compute_labels` → `build_analysis_comment` →
duplicate-detection chain, unchanged. New env var
`VNETWORK_OPENAPI_TOKEN` (same pattern as the existing `GITHUB_TOKEN`
guard in every `scripts/*.py`), new `waap` label, one new
`ENRICHMENT_RULES` entry.

**Still open before building (decisions for Kevin, not discovery
gaps):** the alert-worthy threshold (now three candidate shapes:
4xx/5xx rate, a bad-URI `query_string` match, or a non-`"ACL-WHITE"`
`mitigation_result`), the actual `domains` list to query (needs
`GET /v3/cdn/domains`, itself not yet called), and one live test call
to resolve the `mitigation_result`/`mitigate_result` naming ambiguity
and see the undocumented `date_histogram`/`raw:true` response shapes.

## WAAP Log Search — Live Verification Pass

Completed 2026-09-04, same day, after the schema doc above. **Not
documentation-only — this pass made real, read-only calls against
`https://openapi.vnetwork.vn`** with a live Bearer token, at the
user's explicit request, specifically to verify the 5 fields against
actual response data before implementation. Full detail, every
request/response body: `docs/WAAP_LOG_SEARCH_SCHEMA.md` §7.

**Result: verification did not reach a `200` response.** Three calls,
all denied, all with structured/service-specific errors rather than a
uniform failure:
- `GET /v3/instances` (Compute) → `403 Service.AccessDenied`
- `GET /v3/cdn/domains` (CDN) → `404 Service.NotFound` — traced to a
  real gap in the published Postman collection: this endpoint (and 2
  siblings) use an unresolved `{{URL}}` template variable instead of
  the hardcoded `openapi.vnetwork.vn` host all 103 other endpoints use
- `POST /v1/bsearch` against `audit.sentinelops.fyi` → `401
  Request.Unauthorized` — reproduced identically 3 times: with the
  domain specified, with `domains` omitted entirely (testing the
  schema doc's "optional, defaults to all domains" claim), and again
  after a full token rotation

**The 403/404/401 spread, reproduced after rotating to a brand-new
token, is itself the finding:** the token is live and authenticates,
but this account currently has no provisioned/authorized access to
WAAP, CDN, or Compute reachable from here — not a bad-credential
problem. **None of the 5 requested fields (source IP, URI, status
code, user agent, mitigation result) were observed in real response
data.** Every claim about them stays doc-sourced (§1–§4 of the schema
doc), not live-verified. What *did* get verified live: the request
bodies sent were well-formed enough to reach real authorization logic
(no `400`/malformed-request errors), and the error-response envelope
matches the collection's own documented shape.

**Security incident, handled correctly:** the first token used was
briefly exposed in this session's chat transcript while being passed
into a shell. Treated as compromised immediately; the user rotated the
key in the VNETWORK console and revoked the old one before any further
calls were trusted. All calls (including the retest) used a token read
from a local, non-committed file, never printed by any script.

**Next step for this integration:** either the correct onboarded
domain name, a token scoped to a provisioned account, or a decision to
proceed with the doc-sourced schema as sufficient — the threshold and
`domains`-list open items from the section above are unaffected either
way. **Integration code was not written** — still plan-only per
`docs/WAAP_LOG_SEARCH_SCHEMA.md` §6.

## WAAP Log Search — Root Cause Identified (Onboarding, Not Token/Code)

Confirmed 2026-09-04, later same day, via direct Partner Portal
evidence (Kevin checked the console — this project has no browser/
portal access, so this is Kevin's observation, reported here, not
independently re-verified by this session). WAAP's own onboarding flow
— **Step 2: Domain & Origin** — shows:

- No Website Domain configured
- No Origin Server configured

**Root cause: no WAAP site has ever been onboarded on this account —
not a token problem, not a code/request-schema problem.** This
directly explains every result in the Live Verification Pass above
without needing any further API debugging:

- `POST /v1/bsearch` → `401 Request.Unauthorized` for
  `audit.sentinelops.fyi`, and identically with `domains` omitted —
  consistent with zero domains ever having been onboarded into
  `Elastic.LogComposer`, exactly as the collection's own detailed 401
  example describes ("domain(s) not belong to your
  Elastic.LogComposer").
- The token itself was already independently confirmed live/valid
  (structured, service-specific 403/404/401 errors, reproduced
  identically across two different tokens) — this finding narrows
  "why" without contradicting that.
- `audit.sentinelops.fyi` being CNAME'd to VNETWORK's CDN at the DNS
  level (confirmed in the MVP #5 plan doc) does not imply it was ever
  registered as a protected site inside WAAP's own onboarding flow —
  those are two different steps, and this account only completed
  (or is mid-) the DNS-pointing one.

**Per instruction: no further API debugging** (at the time this section
was written — see the update directly below; onboarding has since been
completed and re-checked). The blocker identified here was a
console/onboarding action item for Kevin (complete Step 2: Domain &
Origin, and whatever steps follow it, for the intended domain), not
something resolvable from this session by retrying calls, rotating
tokens again, or changing the request shape. WAAP Log Search
Integration remains plan-only; nothing implemented.

## WAAP Log Search — Post-Onboarding Re-Verification

Completed 2026-09-04, later same day. Kevin completed WAAP onboarding
— **Website: `www.sentinelops.fyi`, Service ID: `95743`**. Per
instruction, re-ran the exact same 3 read-only checks from the Live
Verification Pass above (same token file, same endpoints) to check
whether API accessibility, WAAP log search access, or analytics
availability changed. Documentation only. Full detail, byte-for-byte
responses, and a before/after table: `docs/WAAP_LOG_SEARCH_SCHEMA.md`
§8.

**Result: no change on any of the 3 checks.**
- `GET /v3/instances` (Compute) — still `403 Service.AccessDenied`
- `GET /v3/cdn/domains` (CDN) — still `404 Service.NotFound`
- `POST /v1/bsearch` against `www.sentinelops.fyi` (the actual
  onboarded domain, not the `audit.sentinelops.fyi` guess used
  earlier) — still `401 Request.Unauthorized`, byte-for-byte the same
  error shape as before onboarding

**Analytics availability was not separately testable:** per
`docs/VNETWORK_PRODUCT_DISCOVERY.md`, `bsearch` is the only API surface
behind WAAP's console Analytics/Logs tabs — no separate analytics
endpoint exists — so the same `401` covers both "log search access"
and "analytics availability" together; they did not diverge.

**This corrects, not just reconfirms, the prior root-cause section
above:** "no WAAP site onboarded" may have been accurate as of that
check, but the fix applied since then has **not yet unlocked API-level
access**. Four plausible explanations are recorded, unconfirmed, in
`docs/WAAP_LOG_SEARCH_SCHEMA.md` §8 — propagation delay, onboarding
incomplete beyond Step 2, a domain-string mismatch between what was
queried and what the portal actually registered, or an account/token
scope mismatch (consistent with Compute/CDN also staying unchanged,
though a WAAP-only onboarding wouldn't be expected to fix those
anyway). None were tested further this pass — documentation only, per
instruction.

## Next Task

Milestone frozen — see `NEXT_STEPS.md` for the prioritized build order
(WAAP Log Search Integration → Healthcheck Webhook Receiver → Digital
Risk Twin) and scope for each. WAAP Log Search Integration's schema is
now fully captured (`docs/WAAP_LOG_SEARCH_SCHEMA.md`) — the remaining
blocker to starting the build is the threshold/domains decisions
above, not further discovery.
