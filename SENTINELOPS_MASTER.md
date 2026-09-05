[1mdiff --git a/NEXT_STEPS.md b/NEXT_STEPS.md[m
[1mdeleted file mode 100644[m
[1mindex 99b4804..0000000[m
[1m--- a/NEXT_STEPS.md[m
[1m+++ /dev/null[m
[36m@@ -1,100 +0,0 @@[m
[31m-# Next Steps[m
[31m-[m
[31m-Milestone frozen 2026-09-04 (see `PROJECT_STATUS.md`). Priority order[m
[31m-for what gets built next, in order.[m
[31m-[m
[31m-## 1. WAAP Log Search Integration[m
[31m-[m
[31m-**Status:** researched, not built. Backed by MVP #4 Discovery[m
[31m-(`docs/VNETWORK_API_DISCOVERY.md`, `docs/VNETWORK_PRODUCT_DISCOVERY.md`,[m
[31m-`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`).[m
[31m-[m
[31m-**What it is:** `POST /v1/bsearch` against `openapi.vnetwork.vn` — a[m
[31m-real, callable, Bearer-token-authenticated log search/aggregation[m
[31m-endpoint over WAF+CDN access logs (client IP, URI, status code, user[m
[31m-agent, upstream latency). Ranked the single highest-ROI VNETWORK[m
[31m-capability across all three discovery passes.[m
[31m-[m
[31m-**Shape of the build:** same reuse pattern as MVP #3/#4 —[m
[31m-`scripts/create_waap_incident.py`, a new `to_alert()` mapper over[m
[31m-`bsearch` results, thresholding on something concrete (e.g. 4xx/5xx[m
[31m-rate spike, or a `query_string`/`match_phrase` match against a known[m
[31m-bad pattern), feeding the same `score_alert` / `build_issue` /[m
[31m-`create_issue` / `assign_issue` / `compute_labels` /[m
[31m-`build_analysis_comment` / duplicate-detection chain unchanged. One new[m
[31m-label (`waap`) and one new `ENRICHMENT_RULES` entry.[m
[31m-[m
[31m-**Open before starting:** what specific threshold/query defines "alert[m
[31m--worthy" — needs a decision, not a discovery (the API itself is fully[m
[31m-understood).[m
[31m-[m
[31m-## 2. Healthcheck Webhook Receiver[m
[31m-[m
[31m-**Status:** planned, not built. Backed by MVP #5 Discovery[m
[31m-(`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`).[m
[31m-[m
[31m-**What it is:** VNETWORK Healthcheck & Alerting's custom-webhook[m
[31m-notification channel (confirmed: endpoint URL + optional HMAC secret,[m
[31m-signed JSON POST, `X-Webhook-Signature` header) delivering directly[m
[31m-into a new MCP-side receiver, which feeds the same GitHub incident[m
[31m-pipeline. The only capability discovered so far that lets VNETWORK[m
[31m-*push* rather than SentinelOps *poll*.[m
[31m-[m
[31m-**Shape of the build:** `POST /api/webhooks/vnetwork-healthcheck` on[m
[31m-`audit.sentinelops.fyi`, raw-body HMAC verification (algorithm assumed[m
[31m-HMAC-SHA256 pending confirmation) with constant-time comparison, fail[m
[31m-closed, secret in a platform env var. Full detail and reasoning in the[m
[31m-plan doc.[m
[31m-[m
[31m-**Open before starting (blocking, not optional):**[m
[31m-1. The HMAC algorithm, signing base, and payload schema are not[m
[31m-   published anywhere — must be captured from one real test delivery[m
[31m-   (configure a temporary Monitor against a logging-only endpoint)[m
[31m-   before the mapper can be trusted.[m
[31m-2. The source repo/Render service actually running at[m
[31m-   `audit.sentinelops.fyi` was not found on this machine — need to[m
[31m-   know whether this is "add a route to an existing backend" or[m
[31m-   "stand up a new minimal service," which is a materially different[m
[31m-   scope.[m
[31m-[m
[31m-## 3. Digital Risk Twin[m
[31m-[m
[31m-**Status:** concept sketch only — unlike #1 and #2, this has not gone[m
[31m-through a discovery pass. Nothing below is verified against real[m
[31m-VNETWORK capabilities or scoped against real effort; treat it as a[m
[31m-starting hypothesis for the next discovery round, not a plan.[m
[31m-[m
[31m-**Working idea:** a single, continuously-maintained model of[m
[31m-everything SentinelOps actually knows about the organization's real[m
[31m-exposure and posture — built by aggregating data sources this project[m
[31m-has *already* discovered and, in several cases, already integrates,[m
[31m-rather than inventing a new one:[m
[31m-[m
[31m-- Cloud attack surface: `GET /v3/cdn/domains`, `/v3/elastic_ips`,[m
[31m-  `/v3/networks/reserves`, `/v3/secgroups`, `/v3/certificates` (all[m
[31m-  already catalogued, ROI-ranked, available today)[m
[31m-- Edge signal: WAAP `bsearch` log aggregates (once #1 above exists)[m
[31m-- Host signal: `security-watch.js` control state, Windows Defender[m
[31m-  detections (already live via MVP #2/#3/#4)[m
[31m-- Push signal: Healthcheck & Alerting webhook deliveries (once #2[m
[31m-  above exists)[m
[31m-[m
[31m-The "twin" would be the merged, queryable state across all of these —[m
[31m-not a new alert type, but a standing answer to "what do we actually[m
[31m-expose and what's its current state," that every individual alert[m
[31m-pipeline (WAAP, Healthcheck, security-watch.js) could enrich against[m
[31m-instead of each one starting cold. Closest existing precedent in this[m
[31m-codebase: the same JSON-state-file + diff pattern `security-watch.js`[m
[31m-and the dormant ARP-based Home-SOC collector already use, generalized[m
[31m-across every source above instead of just one.[m
[31m-[m
[31m-**Why it's #3, not #1:** it's a synthesis of the other two (and[m
[31m-existing) sources, not a new capability — it only becomes buildable[m
[31m-once #1 and #2 exist to feed it, and it needs its own discovery pass[m
[31m-(what "twin" state actually helps triage a real incident, what storage[m
[31m-shape, what refresh cadence) before it's a plan rather than an idea.[m
[31m-[m
[31m-**No dashboards, no databases, no new infrastructure** implied by[m
[31m-default — if a "twin" ends up needing persistent state beyond what a[m
[31m-JSON file can hold, that's a decision for its own discovery pass, not[m
[31m-assumed here.[m
[1mdiff --git a/PROJECT_STATUS.md b/PROJECT_STATUS.md[m
[1mdeleted file mode 100644[m
[1mindex 0822cc7..0000000[m
[1m--- a/PROJECT_STATUS.md[m
[1m+++ /dev/null[m
[36m@@ -1,444 +0,0 @@[m
[31m-# SentinelOps Status[m
[31m-[m
[31m-## 🔒 Milestone Frozen — 2026-09-04[m
[31m-[m
[31m-Current milestone (MVP #1–#4 build, plus the VNETWORK discovery/plan[m
[31m-work below) is frozen as of this checkpoint. Canonical naming for the[m
[31m-discovery work, to remove ambiguity between the build-MVP numbering[m
[31m-(#1–#4, all shipped code) and the VNETWORK research track:[m
[31m-[m
[31m-- **MVP #4 Discovery** — the research behind **WAAP Log Search[m
[31m-  Integration** (next-steps priority #1). Covers the full VNETWORK[m
[31m-  OpenAPI catalog, the Healthcheck/WAAP/Object Storage product[m
[31m-  discovery, and the 17-category capability assessment. Docs:[m
[31m-  `docs/VNETWORK_API_DISCOVERY.md`, `docs/VNETWORK_PRODUCT_DISCOVERY.md`,[m
[31m-  `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`. Detailed findings in the[m
[31m-  "VNETWORK OpenAPI Discovery" / "VNETWORK Product Discovery" /[m
[31m-  "VNETWORK Capability Assessment" sections below.[m
[31m-- **MVP #5 Discovery** — the research + implementation plan behind the[m
[31m-  **Healthcheck Webhook Receiver** (next-steps priority #2). Doc:[m
[31m-  `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`. Detailed findings in the "MVP[m
[31m-  #5: VNETWORK Healthcheck Webhook Receiver" section below.[m
[31m-[m
[31m-Next-step priorities and scope: see `NEXT_STEPS.md`.[m
[31m-[m
[31m-## Completed[m
[31m-[m
[31m-✅ MVP #1 - Fake Alert Pipeline[m
[31m-✅ MVP #2 - Windows Defender Real Alert Pipeline[m
[31m-✅ MVP #3 (investigation) - Wazuh Verification[m
[31m-✅ MVP #3 - Live security-watch.js Telemetry Pipeline[m
[31m-✅ MVP #4 - Incident Enrichment (labels + MCP analysis comment)[m
[31m-✅ MVP #4 Discovery — VNETWORK OpenAPI + Product Discovery + Capability Assessment (documentation-only, feeds WAAP Log Search Integration)[m
[31m-✅ MVP #5 Discovery — Healthcheck Webhook Receiver plan (documentation + plan-only, not built)[m
[31m-[m
[31m-## Architecture[m
[31m-[m
[31m-```[m
[31m-Windows Defender ─┐[m
[31m-security-watch.js ┴→ alerts.json[m
[31m-                       ↓[m
[31m-                      MCP[m
[31m-                       ↓[m
[31m-                   Risk Score[m
[31m-                       ↓[m
[31m-              Duplicate Detection (24h)[m
[31m-                 ↓            ↓[m
[31m-         new alert      existing alert[m
[31m-              ↓                ↓[m
[31m-       GitHub Issue    Update occurrence[m
[31m-              ↓          count + last_seen[m
[31m-              └────────┬───────┘[m
[31m-                        ↓[m
[31m-              Auto Labels + MCP Analysis Comment[m
[31m-                        ↓[m
[31m-              Assign KEVIN-NGUYENDAD[m
[31m-                        ↓[m
[31m-                  GitHub Mobile[m
[31m-                        ↓[m
[31m-                      iPhone[m
[31m-```[m
[31m-[m
[31m-## Commits[m
[31m-[m
[31m-MVP #1:[m
[31m-d70a085[m
[31m-[m
[31m-MVP #2:[m
[31m-8ec96f2[m
[31m-[m
[31m-MVP #3:[m
[31m-d5b7819[m
[31m-[m
[31m-MVP #4:[m
[31m-5f6a9ea[m
[31m-[m
[31m-## Current State[m
[31m-[m
[31m-Working:[m
[31m-- GitHub integration[m
[31m-- Issue creation[m
[31m-- Assignment[m
[31m-- Mobile visibility[m
[31m-- Risk scoring[m
[31m-- Live security-watch.js telemetry (real alert source)[m
[31m-- Duplicate detection (24h window, occurrence count + last_seen on the issue itself)[m
[31m-- Auto labels (critical/high/defender/control-drift/firewall, computed per alert)[m
[31m-- MCP analysis comments (risk score, reason, recommendation — posted on create and on duplicate updates)[m
[31m-[m
[31m-Not Yet Implemented:[m
[31m-- WAAP integration[m
[31m-[m
[31m-Ruled out (see investigation docs):[m
[31m-- Wazuh alerts.json — not installed, will not be built[m
[31m-- Suricata eve.json — not installed, will not be built[m
[31m-[m
[31m-## MVP #3: Wazuh Verification[m
[31m-[m
[31m-Wazuh verification completed.[m
[31m-[m
[31m-Result:[m
[31m-No Wazuh installation found.[m
[31m-[m
[31m-Do not build Wazuh integrations. Investigation frozen. No code changed.[m
[31m-See `docs/MVP3_WAZUH_INVESTIGATION.md` for full findings.[m
[31m-[m
[31m-## Home-SOC Source Discovery[m
[31m-[m
[31m-Completed 2026-09-04. Discovery/verification only, no code changed. See[m
[31m-`docs/HOME_SOC_SOURCE_DISCOVERY.md` for full findings.[m
[31m-[m
[31m-Result, ranked (real + already running + closest fit to existing[m
[31m-scoring/GitHub pipeline):[m
[31m-[m
[31m-1. **`security-watch.js` → `alerts.json`** (in[m
[31m-   `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`) —[m
[31m-   real, actively scheduled (`HOME-SOC-Scan-And-Export`, last run[m
[31m-   success 9/3/2026), clean alert schema, currently 0 open alerts (5/5[m
[31m-   controls match baseline). **Leading candidate for MVP #3 replacement.**[m
[31m-2. Windows Defender — already proven in MVP #2, still available[m
[31m-3. Windows Event Logs — real and live, but no process-creation telemetry[m
[31m-   without an auditpol change (out of scope)[m
[31m-4. `C:\mcp-cyber-tools\reports\home-soc-state` — a second, separate[m
[31m-   Home-SOC implementation on this host; dormant since 2026-08-29[m
[31m-5. Suricata — not installed, ruled out[m
[31m-[m
[31m-## MVP #3: Live security-watch.js Telemetry[m
[31m-[m
[31m-Built on the discovery above. Source: `security-watch.js`'s live[m
[31m-`alerts.json` at[m
[31m-`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\alerts.json`[m
[31m-— the endpoint-control watcher already running on this host via the[m
[31m-`HOME-SOC-Scan-And-Export` scheduled task. No new infrastructure was[m
[31m-built; Wazuh and Suricata remain out of scope, per the frozen[m
[31m-investigation.[m
[31m-[m
[31m-New script: `scripts/create_securitywatch_incident.py`. Reuses[m
[31m-`score_alert`, `build_issue`, `create_issue`, `assign_issue`, `ASSIGNEE`,[m
[31m-`github_request`, `REPO_OWNER`, `REPO_NAME` from[m
[31m-`create_test_incident.py` unchanged, same pattern as MVP #2's[m
[31m-`create_defender_incident.py`. The only new logic is `to_alert()`[m
[31m-(maps a security-watch.js alert entry onto the existing alert schema)[m
[31m-and 24-hour duplicate detection.[m
[31m-[m
[31m-**Duplicate detection:** GitHub itself is the source of truth — no[m
[31m-separate local state file. An open issue is a duplicate if its title[m
[31m-matches (title is stable per alert type: severity + event type + risk[m
[31m-score) and its "Last Seen" is within 24 hours. A duplicate gets its[m
[31m-body's `## Occurrence Tracking` block updated in place (`Occurrences`[m
[31m-+1, `Last Seen` refreshed) instead of a new issue.[m
[31m-[m
[31m-**Finding — bug in security-watch.js (not fixed, out of scope):** its[m
[31m-`FIREWALL_DISABLED` and `DEFENDER_DISABLED` rules use[m
[31m-`control: 'firewall'` / `control: 'defender'`, but the actual[m
[31m-baseline/state object keys are `fw` / `def`. `baseline_value` /[m
[31m-`current_value` resolve to `undefined` and are silently dropped by[m
[31m-`JSON.stringify` for just those two rule types (DNS/RDP/SSH are[m
[31m-unaffected — their `control` names match). `to_alert()` in the new[m
[31m-script handles this defensively by omitting the field rather than[m
[31m-printing a misleading "None".[m
[31m-[m
[31m-**Verification (2026-09-04):** Windows Firewall (Public profile) was[m
[31m-briefly disabled and immediately re-enabled (exposure window: a few[m
[31m-seconds, admin-run, single guarded command) to produce one real[m
[31m-detection:[m
[31m-[m
[31m-```[m
[31m-Before: True → security-watch.js detects FIREWALL_DISABLED → alerts.json updated → After: True[m
[31m-```[m
[31m-[m
[31m-Ran the pipeline twice against that one real alert:[m
[31m-[m
[31m-| Run | Result |[m
[31m-|---|---|[m
[31m-| 1st | New issue created: **Issue #6** — `[CRITICAL] Firewall Disabled \| Risk 95`, assigned to KEVIN-NGUYENDAD |[m
[31m-| 2nd (same alert, still within 24h) | No new issue — Issue #6 updated: `Occurrences: 2`, `Last Seen` refreshed |[m
[31m-[m
[31m-https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/6[m
[31m-[m
[31m-Success criteria met: a real alert from security-watch.js created a[m
[31m-GitHub incident, and a repeat of the same real alert updated it instead[m
[31m-of duplicating it.[m
[31m-[m
[31m-## MVP #4: Incident Enrichment[m
[31m-[m
[31m-Enhances the MVP #3 pipeline in place — same script[m
[31m-(`scripts/create_securitywatch_incident.py`), same source[m
[31m-(`security-watch.js` → `alerts.json`), same GitHub destination. No[m
[31m-dashboards, no databases, no new infrastructure.[m
[31m-[m
[31m-**Auto labels** (`compute_labels()`): a subset of `critical` / `high` /[m
[31m-`defender` / `control-drift` / `firewall`, chosen per alert from its[m
[31m-severity, source, and event type. Applied via GitHub's[m
[31m-"add labels" endpoint, which creates labels that don't exist yet — no[m
[31m-separate label-provisioning step needed. Applied on both the new-issue[m
[31m-path and the duplicate-update path (idempotent — re-adding an existing[m
[31m-label is a no-op).[m
[31m-[m
[31m-**MCP Analysis Comment** (`build_analysis_comment()`): posted as an[m
[31m-issue comment — Risk Score, Reason (bullets), Recommendation (numbered[m
[31m-list) — sourced from a small per-event-type table[m
[31m-(`ENRICHMENT_RULES`) covering security-watch.js's 5 known alert types,[m
[31m-with a generic fallback for anything else. Posted on every processed[m
[31m-alert, including duplicates (a duplicate's comment adds a[m
[31m-"Recurrence detected — occurrence #N" note), so the issue timeline[m
[31m-carries a running record of each detection.[m
[31m-[m
[31m-**Duplicate handling:** unchanged from MVP #3 (GitHub issue is the[m
[31m-source of truth, 24h window) — re-verified still correct with[m
[31m-enrichment layered on top.[m
[31m-[m
[31m-**Verification (2026-09-04):** ran the pipeline again against the same[m
[31m-real `FIREWALL_DISABLED` alert from MVP #3 (still within the 24h[m
[31m-window). Result, confirmed directly via `gh issue view 6`:[m
[31m-[m
[31m-- Duplicate detected correctly — Issue #6 updated (`Occurrences: 3`),[m
[31m-  no new issue created[m
[31m-- Labels applied: `critical`, `control-drift`, `firewall`[m
[31m-- Comment posted, exact format:[m
[31m-  ```[m
[31m-  ## MCP Analysis[m
[31m-[m
[31m-  _Recurrence detected -- occurrence #3._[m
[31m-[m
[31m-  **Risk Score:** 95[m
[31m-[m
[31m-  **Reason:**[m
[31m-  - Firewall disabled[m
[31m-  - Security control drift detected[m
[31m-[m
[31m-  **Recommendation:**[m
[31m-  1. Re-enable firewall[m
[31m-  2. Check recent changes[m
[31m-  3. Review related events[m
[31m-  ```[m
[31m-- Assignee unchanged: KEVIN-NGUYENDAD[m
[31m-[m
[31m-https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/6[m
[31m-[m
[31m-The new-issue path calls the identical `compute_labels()` /[m
[31m-`build_analysis_comment()` / `add_labels()` / `add_comment()` functions[m
[31m-(without the recurrence note) — not re-triggered separately in this[m
[31m-pass to avoid an unnecessary second real firewall toggle; the create[m
[31m-path itself (issue creation + assignment) was already verified in[m
[31m-MVP #3.[m
[31m-[m
[31m-## VNETWORK OpenAPI Discovery[m
[31m-[m
[31m-Completed 2026-09-04. Documentation-only — no VNETWORK API endpoint was[m
[31m-called, no resources provisioned, no credits spent. Read the public[m
[31m-Postman collection behind `https://postman.vnetwork.dev/view/4429080/2sBY4Qqyts`[m
[31m-(via its own data API, `documenter.gw.postman.com` — never[m
[31m-`openapi.vnetwork.vn`). Full catalog, every one of the 106 endpoints[m
[31m-ranked by ROI, and integration sketches:[m
[31m-`docs/VNETWORK_API_DISCOVERY.md`.[m
[31m-[m
[31m-**Auth:** Bearer token (`Authorization: Bearer {{OPENAPI_TOKEN}}`) on[m
[31m-every request. Base: `https://openapi.vnetwork.vn`.[m
[31m-[m
[31m-**Totals:** 106 endpoints — 39 read-only (37 GET + 1 read-only POST[m
[31m-query), 67 mutating (excluded from ranking). No "Projects" category[m
[31m-exists in this API. No native alert/webhook endpoints exist anywhere —[m
[31m-alerting has to be built client-side by polling + diffing, which is[m
[31m-exactly SentinelOps' existing security-watch.js shape.[m
[31m-[m
[31m-**Top 10 highest-value capabilities for SentinelOps** (full rationale[m
[31m-and full 106-endpoint ranked table in the doc):[m
[31m-[m
[31m-1. `POST /v1/bsearch` — WAAP/CDN log search & aggregation (client IPs,[m
[31m-   URIs, status codes, UA) — the only real security-log source in the[m
[31m-   API[m
[31m-2. `GET /v3/instances/:id/monitoring` — instance CPU/memory/network[m
[31m-   time series[m
[31m-3. `GET /v3/secgroups` (+ `:id`) — cloud firewall rule inventory,[m
[31m-   control-drift detection (mirrors security-watch.js)[m
[31m-4. `GET /v3/lbs/:id/monitoring` — load-balancer traffic monitoring[m
[31m-5. `GET /v3/lbs/:id/stats` — LB request/error statistics[m
[31m-6. `GET /v3/cdn/domains` — CDN surface inventory, join key for #1[m
[31m-7. `GET /v3/instances` (v3) / `GET /v1/instances` — instance inventory[m
[31m-   / CMDB baseline[m
[31m-8. `GET /v3/instances/:id/summary` — realtime state + latest[m
[31m-   monitoring snapshot in one call[m
[31m-9. `GET /v3/elastic_ips` / `GET /v3/networks/reserves` — public IP /[m
[31m-   attack-surface inventory[m
[31m-10. `GET /v3/certificates` — TLS cert inventory, expiry alerting[m
[31m-[m
[31m-Nothing implemented yet — discovery and ranking only, per instruction.[m
[31m-[m
[31m-## VNETWORK Product Discovery (Healthcheck & Alerting, WAAP, OpenAPI, Object Storage)[m
[31m-[m
[31m-Completed 2026-09-04. Documentation-only, no VNETWORK API endpoint[m
[31m-called, no resources/credits used. Follow-up to the discovery above —[m
[31m-checked whether Healthcheck & Alerting and Object Storage exist as[m
[31m-separate VNETWORK products (they weren't in the Postman collection).[m
[31m-Full detail: `docs/VNETWORK_PRODUCT_DISCOVERY.md`.[m
[31m-[m
[31m-**Findings:**[m
[31m-- **Healthcheck & Alerting** (beta) — real product: HTTP/TCP/DNS/TLS[m
[31m-  monitors → alarms → incidents → playbooks, with notification[m
[31m-  channels Email/Slack/Teams/Telegram/**custom webhooks**. The only[m
[31m-  place native webhook support exists anywhere in VNETWORK's stack —[m
[31m-  but **no REST API is documented**, console/Partner-Portal only.[m
[31m-- **WAAP** — console has AI-WAF, Bot Management, API Protection,[m
[31m-  Emergency Mitigation, and a "Logs" module; no rule-management or[m
[31m-  alert-config API documented beyond the `bsearch` log-search endpoint[m
[31m-  already catalogued.[m
[31m-- **Object Storage (OSS)** — real, S3-compatible product (buckets,[m
[31m-  objects, versioning, IAM). Uses a **separate credential model**[m
[31m-  (Access Key/Secret, not the Bearer token). No VNETWORK-specific REST[m
[31m-  API — integrate via the standard S3 protocol instead. No[m
[31m-  logging/metrics/notifications documented.[m
[31m-- Re-confirmed against the raw Postman collection: zero matches for[m
[31m-  "health", "webhook", "alert" anywhere in `openapi.vnetwork.vn`; the[m
[31m-  only "storage"/"bucket" mentions are incidental prose, not an object-[m
[31m-  storage feature.[m
[31m-[m
[31m-**Top 10 SentinelOps integrations, ranked by ROI** (full rationale in[m
[31m-the doc):[m
[31m-[m
[31m-1. `POST /v1/bsearch` (WAAP log search) — available now[m
[31m-2. `GET /v3/instances/:id/monitoring` / `/summary` — available now[m
[31m-3. `GET /v3/secgroups` (+`:id`) — available now[m
[31m-4. `GET /v3/lbs/:id/monitoring` / `/stats` — available now[m
[31m-5. `GET /v3/cdn/domains` — available now[m
[31m-6. `GET /v3/instances` / `GET /v1/instances` — available now[m
[31m-7. `GET /v3/certificates` — available now[m
[31m-8. Healthcheck & Alerting webhook channel — **not buildable yet** (no[m
[31m-   API), but the best strategic fit on the list — VNETWORK could push[m
[31m-   alerts instead of SentinelOps polling. Revisit when an API ships.[m
[31m-9. Object Storage via the standard S3 API — available now, but a[m
[31m-   separate credential/integration shape (S3 SDK, not Bearer token)[m
[31m-10. `GET /v3/elastic_ips` / `GET /v3/networks/reserves` — available now[m
[31m-[m
[31m-Nothing implemented — discovery and ranking only, per instruction.[m
[31m-[m
[31m-## VNETWORK Capability Assessment (Partner Portal exploration attempt)[m
[31m-[m
[31m-Completed 2026-09-04. Task asked for authenticated Partner Portal[m
[31m-exploration (`partner.vnetwork.vn/services`) with login/screenshot[m
[31m-evidence. **That access does not exist in this environment** — no[m
[31m-browser automation tool, no VNETWORK MCP connector, no stored[m
[31m-credentials. An unauthenticated fetch of that URL returns only a bare[m
[31m-page title behind a login wall — confirmed, not assumed. Per the[m
[31m-user's choice, the full capability assessment was built instead from[m
[31m-VNETWORK's public documentation (`docs.vnetwork.vn`) plus the two[m
[31m-discovery passes above. Full per-service breakdown (18 services across[m
[31m-all 17 requested categories, each fact marked CONFIRMED (docs) or NOT[m
[31m-DOCUMENTED): `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`.[m
[31m-[m
[31m-**New findings this pass (beyond the two discoveries above):**[m
[31m-- **Multi-CDN Orchestration** has a confirmed, rich metrics API (5xx[m
[31m-  error rates, domain health, traffic/cache/geo analytics) via the[m
[31m-  same `openapi.vnetwork.vn` surface — ranks as high-ROI as WAAP.[m
[31m-- **"Projects"** exists as an Organizations-console concept (isolated[m
[31m-  workspaces), not a compute-API resource — explains why the OpenAPI[m
[31m-  catalog has zero Projects endpoints.[m
[31m-- **Security finding:** API keys are account-wide, unscoped, with no[m
[31m-  documented rotation or usage-audit API — a single leaked key[m
[31m-  compromises every product in this assessment. Mitigation today is a[m
[31m-  manual console review, not code.[m
[31m-- Kubernetes, Databases, Container Registry, Serverless Functions, and[m
[31m-  Usage & Cost Management are all either not self-serve yet[m
[31m-  ("coming soon"/early access) or use a different integration shape[m
[31m-  (kubectl, not the Bearer-token API) — none buildable today.[m
[31m-- SSL/TLS Certificates has a real Activity-feed audit trail (actor,[m
[31m-  IP, UA, change payload) separate from the `/v3/certificates` API[m
[31m-  endpoint already catalogued.[m
[31m-[m
[31m-**Top 10 Opportunities and Crazy But Realistic Ideas:** full detail in[m
[31m-the doc. Headline picks — WAAP log alerting (#1, same as before),[m
[31m-Multi-CDN health/5xx alerting (new, #2), an "attack-surface diff bot"[m
[31m-daily-digest idea that reuses the already-built (but unused)[m
[31m-`nightly-security-brief-trigger.js`/`home-soc-brief.js` pattern from[m
[31m-the Roaming project tree, pointed at VNETWORK data instead of the LAN.[m
[31m-[m
[31m-**If CTO, next 3 projects:** (1) MVP #5 — WAAP `bsearch` → GitHub[m
[31m-Issue, (2) the attack-surface diff bot, (3) a standing monthly check[m
[31m-on Healthcheck & Alerting's API/webhook spec and Container Registry[m
[31m-GA — the two highest-strategic-fit capabilities that simply aren't[m
[31m-buildable yet.[m
[31m-[m
[31m-Nothing implemented — discovery and assessment only, per instruction.[m
[31m-[m
[31m-## MVP #5: VNETWORK Healthcheck Webhook Receiver (plan only)[m
[31m-[m
[31m-Completed 2026-09-04. Plan only — nothing implemented, no domain[m
[31m-touched, no VNETWORK Monitor/Channel configured. Full plan:[m
[31m-`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`.[m
[31m-[m
[31m-```[m
[31m-VNETWORK Healthcheck & Alerting -> Webhook -> MCP -> Risk Score +[m
[31m-Duplicate Detection -> GitHub Issue -> Auto Labels + MCP Analysis[m
[31m-Comment -> Assign KEVIN-NGUYENDAD -> GitHub Mobile[m
[31m-```[m
[31m-[m
[31m-**Verified the claim, didn't just take it:** re-checked directly[m
[31m-against `docs.vnetwork.vn/docs/observability/healthcheck/notifications`[m
[31m-(a page not fetched in the earlier discovery passes). Confirmed:[m
[31m-custom webhook channel, configurable endpoint URL, optional HMAC[m
[31m-secret, "signed JSON POST," `X-Webhook-Signature` header. **Not[m
[31m-documented anywhere:** the HMAC algorithm, the signing base, and the[m
[31m-payload schema — these need to be captured from one real test[m
[31m-delivery before implementation, not assumed.[m
[31m-[m
[31m-**Deployment location — checked both domains directly (DNS + HTTP),[m
[31m-not assumed from names:**[m
[31m-- `sentinelops.fyi` — confirmed static (this homepage repo:[m
[31m-  `vite`/`react` only, no server). **Ruled out** — cannot run[m
[31m-  signature-verifying server code at all.[m
[31m-- `audit.sentinelops.fyi` — confirmed **real and live**, CNAME'd to[m
[31m-  VNETWORK's own CDN with a Render origin behind it. This corrects an[m
[31m-  earlier assumption in this project: the `wafCaseStudy` content in[m
[31m-  `sentinelops-homepage/src/data/content.js` describing "Hardening[m
[31m-  audit.sentinelops.fyi with VNetwork WAAP" is not narrative/marketing[m
[31m-  copy — it describes an actually-deployed setup.[m
[31m-- **Recommended: `audit.sentinelops.fyi`.** Open question that needs[m
[31m-  an answer from Kevin before implementation: the source repo/Render[m
[31m-  service actually running there wasn't found anywhere on this[m
[31m-  machine — need to know whether a route can be added to an existing[m
[31m-  backend there, or whether a new minimal service needs to be stood[m
[31m-  up and pointed at that subdomain.[m
[31m-[m
[31m-**Endpoint path:** `POST /api/webhooks/vnetwork-healthcheck`[m
[31m-(namespaced for future providers, e.g. a WAAP webhook later).[m
[31m-[m
[31m-**HMAC validation strategy:** verify against the *raw* request body[m
[31m-before JSON parsing; HMAC-SHA256 as the default assumption (unconfirmed[m
[31m-— first thing to verify against a real delivery); constant-time[m
[31m-comparison (`hmac.compare_digest` / `timingSafeEqual`) against[m
[31m-`X-Webhook-Signature`; fail closed (401) on missing/invalid signature;[m
[31m-secret in a platform env var, never committed; log rejections without[m
[31m-logging the secret.[m
[31m-[m
[31m-**Pipeline reuse:** no new pipeline logic — only a new HTTP receiver +[m
[31m-`to_alert()` mapper feed into the exact MVP #3/#4 chain unchanged[m
[31m-(`score_alert`, `build_issue`, `create_issue`, `assign_issue`, the 24h[m
[31m-duplicate-detection functions, `compute_labels`,[m
[31m-`build_analysis_comment`), extended with one new label[m
[31m-(`vnetwork-healthcheck`) and one new `ENRICHMENT_RULES` entry.[m
[31m-[m
[31m-## Next Task[m
[31m-[m
[31m-Milestone frozen — see `NEXT_STEPS.md` for the prioritized build order[m
[31m-(WAAP Log Search Integration → Healthcheck Webhook Receiver → Digital[m
[31m-Risk Twin) and scope for each.[m
