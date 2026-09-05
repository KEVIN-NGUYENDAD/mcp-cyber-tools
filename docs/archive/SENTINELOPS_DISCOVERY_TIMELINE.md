# SentinelOps Discovery Timeline

Historical reconstruction only — no new work proposed. Compiled
2026-09-04 from direct review of `PROJECT_STATUS.md`, `NEXT_STEPS.md`,
and every document in `docs/`. Phases are ordered by the chronology
those documents themselves establish (each phase's own text
references, and is referenced by, the phases around it).

**Context, not a phase:** MVP #1 (Fake Alert Pipeline) and MVP #2
(Windows Defender Real Alert Pipeline) predate every document reviewed
for this timeline and are not discovery passes — they are the shipped
baseline (`score_alert`/`build_issue`/`create_issue`/`assign_issue`,
first proven against Defender) that every phase below either
re-verifies against, extends, or attempts to extend. See
`PROJECT_STATUS.md`'s "Completed" list and commit `8ec96f2`.

---

## Phase 1 — MVP #3 Input Verification: Wazuh Investigation

**Goal:** confirm the originally-scoped MVP #3 input (`Wazuh
alerts.json`) actually exists on the host before writing any
integration code against it.

**Actions:** checked for a Wazuh service/agent (`Get-Service`,
`Program Files` directories, `C:\ossec-agent`, `C:\wazuh-agent`, `sc
query WazuhSvc`, listening ports 1514/1515/55000, WSL/Docker
presence); located and inspected every file named `alerts.json` on the
host; grepped the entire `mcp-cyber-tools` tree for "wazuh"/"ossec".

**Evidence:** zero Wazuh services, directories, or listening ports
found; `sc query WazuhSvc` returned `1060: service does not exist`;
two files named `alerts.json` exist but are unrelated custom schemas,
not Wazuh's JSON-Lines manager output; exactly one incidental,
unrelated grep match project-wide.

**Result:** the input MVP #3 was scoped around does not exist, and
neither does the service that would produce it. Standing up a real
Wazuh manager would be new infrastructure (Linux VM/WSL/Docker), not a
config change.

**Decision:** investigation closed, no code changed. Three unchosen
options recorded for the next step (install real Wazuh / re-scope to
whatever real alert source already exists / defer to Suricata).
Triggered Phase 2 directly.

Source: `docs/MVP3_WAZUH_INVESTIGATION.md`.

---

## Phase 2 — Home-SOC Source Discovery

**Goal:** pick a real, already-running replacement input for MVP #3,
since Wazuh (Phase 1) was ruled out.

**Actions:** re-verified Windows Defender's proven state; inventoried
Windows Event Log record counts and checked for process-creation
telemetry; searched the host for every Home-SOC-shaped
implementation, not just the first one found; checked for Suricata.

**Evidence:** found **two separate, unrelated Home-SOC
implementations** — `home-soc-state` (dormant, last written
2026-08-29, failing scheduled tasks) and `security-watch.js`
(actively scheduled via `HOME-SOC-Scan-And-Export`, last run success
9/3/2026, clean alert schema, 0 open alerts against baseline);
Security Event Log has 34,376 records but no 4688 (process-creation)
events without an `auditpol` change; Suricata confirmed absent, same
method as Phase 1; a previously-closed incident
(`INCIDENT-2026-09-01-STALE-FEED.md`) documenting a 41-hour missed
collection cycle, root-caused as scheduling, not a script defect.

**Result:** `security-watch.js`'s `alerts.json` ranked #1 — real,
live, clean schema, zero new collection code needed, only a mapper.
Defender ranked #2 (already proven). Event Logs, the dormant
implementation, and Suricata ranked below, in that order.

**Decision:** `security-watch.js` chosen as MVP #3's actual data
source, replacing the original Wazuh-based scope. No integration
built in this pass — discovery only, feeding the MVP #3 build recorded
in `PROJECT_STATUS.md`.

Source: `docs/HOME_SOC_SOURCE_DISCOVERY.md`.

---

## Phase 3 — VNETWORK OpenAPI Discovery

**Goal:** catalog VNETWORK's full public API surface and rank
capabilities by ROI, as the first pass of what `PROJECT_STATUS.md`
later names "MVP #4 Discovery."

**Actions:** read the public Postman collection (`postman.vnetwork.dev`
→ its own `documenter.gw.postman.com` data API — never
`openapi.vnetwork.vn` itself) and catalogued every one of its 106
endpoints.

**Evidence:** 106 endpoints total (39 read-only: 37 `GET` + 1 read-only
`POST /v1/bsearch`); Bearer-token auth (`{{OPENAPI_TOKEN}}`) on every
request; zero "Projects" endpoints; zero native alert/webhook
endpoints anywhere in the API.

**Result:** `POST /v1/bsearch` (WAAP/CDN log search) ranked the single
highest-ROI capability in the entire catalog — the only real
security-log source found. A full top-10 ranked list produced.

**Decision:** nothing implemented; this ranking became the reference
priority order every later pass (Phases 4, 5, 7) and `NEXT_STEPS.md`
inherited without contradiction.

Source: `docs/VNETWORK_API_DISCOVERY.md`.

---

## Phase 4 — VNETWORK Product Discovery

**Goal:** check whether Healthcheck & Alerting and Object Storage
exist as separate VNETWORK products with their own documentation,
since Phase 3's Postman collection had no trace of either.

**Actions:** read VNETWORK's public docs site (`docs.vnetwork.vn`) and
the WAAP product page; re-confirmed against the raw Phase-3 collection
JSON with targeted keyword search ("health", "webhook", "alert",
"storage"/"bucket").

**Evidence:** Healthcheck & Alerting confirmed real (beta) — Monitors
→ Alarms → Incidents → Playbooks, with Email/Slack/Teams/
Telegram/**custom webhook** notification channels, but **no REST API
documented**; Object Storage confirmed real, S3-compatible, with a
**separate Access Key/Secret credential model**, no VNETWORK-specific
REST API; zero keyword matches for "health"/"webhook"/"alert" in the
raw OpenAPI collection, confirming no hidden alerting surface exists.

**Result:** `bsearch` reconfirmed as WAAP's only programmatic surface;
Healthcheck & Alerting's webhook channel identified as the single best
strategic fit in the whole ecosystem — but zero percent buildable
today, since no API exists to configure it against.

**Decision:** nothing implemented. Directly seeded Phase 6 (the MVP #5
plan) and reinforced Phase 3's ranking with WAAP still #1.

Source: `docs/VNETWORK_PRODUCT_DISCOVERY.md`.

---

## Phase 5 — VNETWORK Capability Assessment

**Goal:** the originally-requested authenticated Partner Portal
exploration (`partner.vnetwork.vn/services`) across 17 categories,
with login/screenshot evidence.

**Actions:** attempted the Partner Portal directly; when that proved
unreachable, built the assessment instead from VNETWORK's public docs
plus Phases 3–4's findings, marking every fact `CONFIRMED (docs)` or
`NOT DOCUMENTED`.

**Evidence:** an unauthenticated fetch of the Partner Portal URL
returned only a bare page title behind a login wall — confirmed, not
assumed; no browser automation tool, VNETWORK MCP connector, or stored
credential existed in the environment to go further.

**Result:** 18 services assessed across all 17 categories. New
findings beyond Phases 3–4: Multi-CDN Orchestration has a confirmed,
rich metrics API (5xx rates, domain health) ranking as high-ROI as
WAAP; "Projects" is an Organizations-console concept, not an API
resource (explaining Phase 3's zero-Projects-endpoints finding);
Kubernetes/DBaaS/Container Registry/Serverless/Usage-Cost all
confirmed non-buildable today; API keys confirmed account-wide,
unscoped, with no documented rotation or usage-audit mechanism.

**Decision:** nothing implemented. The unscoped-key finding was a pure
documentation observation at this point — it would be independently
realized in practice five phases later (Phase 8).

Source: `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`.

---

## Phase 6 — MVP #5 Healthcheck Webhook Receiver Plan

**Goal:** design (not build) a receiver for VNETWORK Healthcheck's
webhook deliveries, and determine where it should live.

**Actions:** re-checked the webhook-channel claim directly against a
docs page not previously fetched
(`docs.vnetwork.vn/docs/observability/healthcheck/notifications`);
checked both `sentinelops.fyi` and `audit.sentinelops.fyi` directly via
DNS and HTTP rather than assuming from the domain names; searched the
entire local machine (both `mcp-cyber-tools` copies, the Roaming
project tree, `sentinelops-homepage`) for the source behind
`audit.sentinelops.fyi`.

**Evidence:** webhook channel, endpoint URL, optional HMAC secret,
"signed JSON POST," and an `X-Webhook-Signature` header all confirmed
in VNETWORK's docs — but the HMAC algorithm, signing base, payload
schema, and retry behavior are **not documented anywhere**;
`sentinelops.fyi` confirmed fully static (Vite/React only, no server);
`audit.sentinelops.fyi` confirmed real and live, CNAME'd to VNETWORK's
CDN with a Render origin, and — correcting an earlier assumption in
this project — its homepage-repo "WAF case study" content was found to
describe an actually-deployed setup, not marketing copy; its own
source repo/Render service was not found anywhere on this machine.

**Result:** `audit.sentinelops.fyi` recommended as the deployment
target; `sentinelops.fyi` ruled out outright (no server capability at
all); a recommended endpoint path
(`POST /api/webhooks/vnetwork-healthcheck`) and a defensive HMAC
validation strategy (raw-body verification, constant-time comparison,
fail-closed) both designed pending real confirmation.

**Decision:** plan-only — no receiver built, no domain touched, no
VNETWORK Monitor/Channel configured. Two blocking open items recorded
for whenever implementation starts: capturing one real webhook
delivery to confirm the HMAC/payload details, and getting an answer
from Kevin on who owns the `audit.sentinelops.fyi` backend.

Source: `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`.

---

## Phase 7 — WAAP Log Search Schema & MCP Plan (post-freeze)

**Goal:** after the MVP #1–#4 milestone freeze, go one level deeper
than Phase 3's field-name catalog — capture `bsearch`'s full
request/response schema, verbatim sample payloads, and a concrete MCP
integration design, to close out `NEXT_STEPS.md` #1's "the API is
fully understood" claim at the schema level.

**Actions:** re-read the `Bsearch Aggs` Postman item in full —
request-body template comments, the field-reference documentation
table, and both of its saved example responses.

**Evidence:** all 5 originally-requested fields (source IP, URI,
status code, user agent, attack indicator) identified — the first four
in the endpoint's documented field table, the fifth
(`mitigation_result`) found only inside the request template's own
commented-out examples, undocumented in prose; a real contradiction
found between the docs table (`domains` mandatory) and the template
comment (`domains` optional, defaults to all); a second field name,
`mitigate_result`, appears once, textually distinct, unresolved
without a live call.

**Result:** full schema, sample payloads, and an MCP integration plan
(`vnetworkWaapSearch` tool + `scripts/create_waap_incident.py`,
reusing the existing pipeline unchanged) all captured — but explicitly
flagged as doc-sourced, not live-verified.

**Decision:** nothing implemented. At the user's explicit direction,
this pass proceeded directly into a live verification attempt —
becoming Phase 8, within the same document.

Source: `docs/WAAP_LOG_SEARCH_SCHEMA.md` §1–§6.

---

## Phase 8 — WAAP Live Verification Pass

**Goal:** verify Phase 7's doc-sourced schema against real API
responses before implementation — the first live call to
`openapi.vnetwork.vn` anywhere in this project.

**Actions:** attempted `GET /v3/cdn/domains` to determine authorized
domains; tested `GET /v3/instances` as a token-validity diagnostic;
attempted `POST /v1/bsearch` against `audit.sentinelops.fyi`, then
again with `domains` omitted, then again after a full token rotation.

**Evidence:** `GET /v3/cdn/domains` → `404 Service.NotFound`, traced to
a real gap in VNETWORK's own published collection — 3 of 106
endpoints (all under "CDN > Domains") reference an unresolved
`{{URL}}` template variable instead of the hardcoded host the other
103 use; `GET /v3/instances` → `403 Service.AccessDenied` (not `401`
— meaning the token authenticates but lacks entitlement), reproduced
identically after rotation; `POST /v1/bsearch` → `401
Request.Unauthorized`, identical across all three variations tested.
**Process incident, handled correctly:** the first token used was
briefly exposed in the session transcript while being passed into a
shell; treated as compromised immediately, rotated in the VNETWORK
console, and every subsequent call re-verified against the new token.

**Result:** the token is confirmed live and valid; the request schema
is confirmed well-formed (no `400`/malformed-request errors on any
call); but this account has zero working access to WAAP, CDN, or
Compute — none of the 5 requested fields were observed in real
response data.

**Decision:** this pass could not distinguish "wrong domain," "domain
not onboarded to WAAP," or "no WAAP product at all" from outside.
Directly triggered Phase 9's root-cause check via the Partner Portal.

Source: `docs/WAAP_LOG_SEARCH_SCHEMA.md` §7.

---

## Phase 9 — WAAP Root Cause Identification (Onboarding Gap)

**Goal:** determine why Phase 8's calls were denied, using direct
Partner Portal evidence rather than further API guessing.

**Actions:** Kevin checked WAAP's own onboarding flow in the Partner
Portal directly (this project has no portal access of its own).

**Evidence:** WAAP onboarding **Step 2: Domain & Origin** showed no
Website Domain and no Origin Server configured — no WAAP site had ever
been onboarded on this account.

**Result:** root cause identified — not a token problem, not a
request-schema problem. This single finding explained every result in
Phase 8 without further API debugging.

**Decision:** per instruction, no further API debugging at this point.
The blocker was reclassified as a console/onboarding action item for
Kevin. WAAP integration remained plan-only.

Source: `PROJECT_STATUS.md`, "WAAP Log Search — Root Cause Identified"
(cross-referenced in `docs/WAAP_LOG_SEARCH_SCHEMA.md` §7, closing
note).

---

## Phase 10 — WAAP Post-Onboarding Re-Verification

**Goal:** after Kevin completed WAAP onboarding (Website
`www.sentinelops.fyi`, Service ID `95743`), re-run the exact same
three Phase-8 checks to see whether onboarding actually unlocked
access.

**Actions:** re-ran `GET /v3/instances`, `GET /v3/cdn/domains`, and
`POST /v1/bsearch` (this time against the correct, actually-onboarded
domain) using the same token file and request shapes as Phase 8.

**Evidence:** all three results **byte-for-byte identical** to
Phase 8 — `403 Service.AccessDenied`, `404 Service.NotFound`, `401
Request.Unauthorized` respectively, including the exact same error
JSON shape on the `bsearch` call.

**Result:** onboarding, as observed in the portal, has **not** yet
unlocked API-level access for this token, for any of the three checks.
This corrects — not merely reconfirms — Phase 9's root cause: it was
accurate as of that check, but the fix applied since has not resolved
the underlying access problem.

**Decision:** four unconfirmed explanations recorded (propagation
delay, onboarding incomplete beyond Step 2, a domain-string mismatch,
an account/token scope mismatch), none tested further per
"documentation only." This is the most recent state of the WAAP
integration track as of this timeline's compilation — still blocked,
cause still open.

Source: `docs/WAAP_LOG_SEARCH_SCHEMA.md` §8;
`PROJECT_STATUS.md`, "WAAP Log Search — Post-Onboarding
Re-Verification."

---

## Cross-phase dependency map

```
Phase 1 (Wazuh: input doesn't exist)
   └──▶ Phase 2 (Home-SOC source discovery: security-watch.js chosen)
             └──▶ feeds the MVP #3 build recorded in PROJECT_STATUS.md

Phase 3 (VNETWORK API catalog: bsearch ranked #1)
   └──▶ Phase 4 (Product discovery: Healthcheck confirmed, no API)
             └──▶ Phase 5 (Capability assessment: Multi-CDN found,
                            key-scoping risk documented)
                       └──▶ Phase 6 (MVP #5 Healthcheck plan)
   └──▶ Phase 7 (WAAP schema deep dive)
             └──▶ Phase 8 (Live verification: access denied)
                       └──▶ Phase 9 (Root cause: no onboarding)
                                 └──▶ Phase 10 (Re-verify post-fix:
                                                 still denied)
```

## Current end state (as of this timeline)

- Home-SOC alert pipeline (Phases 1–2's outcome): **built, live,
  verified.**
- VNETWORK/WAAP integration (Phases 3–10): **fully designed,
  live-access blocked**, cause unresolved.
- Healthcheck Webhook Receiver (Phases 4, 6): **planned**, blocked on
  an undocumented HMAC spec and an unidentified deployment owner.
- Digital Risk Twin: **not yet in this timeline** — no discovery pass
  has been run for it, per `NEXT_STEPS.md`.

No new work is proposed in this document, per instruction.
