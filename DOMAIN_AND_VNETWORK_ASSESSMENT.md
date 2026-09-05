# DOMAIN_AND_VNETWORK_ASSESSMENT.md

Compiled 2026-09-04. Read-only investigation — no code changed, no
infrastructure touched, no VNETWORK API endpoint called (this pass
used only public DNS resolution and unauthenticated HTTP `HEAD`/`GET`
requests against already-public URLs — the same class of check
`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` already established as this
project's own precedent for domain verification). Evidence sources:
live DNS lookups performed this session (`nslookup`, all record types
checked), live HTTP header fetches performed this session (`curl -I`
against public URLs only), `sentinelops-homepage/src/data/content.js`,
every VNETWORK discovery document in `mcp-cyber-tools/docs/`,
`PROJECT_STATUS.md`, `NEXT_STEPS.md`, `ARCHITECTURE_SUMMARY.md`,
`SENTINELOPS_DISCOVERY_TIMELINE.md`, and `SENTINELOPS_DEEP_CONTEXT.md`.
Findings marked **(new this pass)** were not present in any prior
document reviewed this session; everything else cites its prior
source directly.

---

# Section 1: Domain Inventory

Five hostnames discovered total — the three previously known plus two
found **(new this pass)** inside `content.js`'s contact-links data
(`src/data/content.js` lines 415–421) that no prior discovery document
had checked.

## `sentinelops.fyi`

- **Purpose:** the public portfolio homepage.
- **Current status:** live, `200 OK`.
- **DNS target:** A records `216.24.57.7` / `216.24.57.15`, fronted by
  Cloudflare (confirmed live this pass: `Server: cloudflare`,
  `CF-RAY` present). MX: `fwd1.porkbun.com` (pref 10),
  `fwd2.porkbun.com` (pref 20) — **email is Porkbun forwarding, not a
  dedicated mail service (new this pass).** TXT/SPF:
  `v=spf1 include:_spf.porkbun.com ~all` — confirms **Porkbun as the
  domain's registrar/DNS/email provider (new this pass)**, not
  previously documented anywhere in this project's discovery record.
- **Render service:** `rndr-id` header present, confirming a Render
  origin behind Cloudflare (consistent with
  `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`'s prior finding).
- **WAAP integration status:** none — routed entirely through
  Cloudflare, never touches VNETWORK's network.
- **Known owner/component:** `sentinelops-homepage` repo (static
  Vite/React build, confirmed no server —
  `sentinelops-homepage/README.md`).
- **Current utilization:** high — this is the actual live portfolio.
- **Potential utilization:** could pull real data from
  `home-soc-reports` and GitHub's API instead of the hardcoded
  operational claims flagged in `SENTINELOPS_DEEP_CONTEXT.md` §11.

## `www.sentinelops.fyi`

- **Purpose:** per `content.js`, this is the hostname WAAP onboarding
  was completed against (Service ID `95743`,
  `docs/WAAP_LOG_SEARCH_SCHEMA.md` §8).
- **Current status:** live, but **`301 Moved Permanently` → `https://sentinelops.fyi/`
  (new this pass, confirmed by live HTTP fetch).** This hostname has
  no independent content of its own — it is purely a redirect to the
  apex domain.
- **DNS target (new this pass, full chain resolved):**
  `www.sentinelops.fyi` → CNAME `sentinelops-iygs.onrender.com` →
  CNAME `gcp-us-west1-1.origin.onrender.com` → CNAME
  `gcp-us-west1-1.origin.onrender.com.cdn.cloudflare.net` → A
  `216.24.57.7` / `216.24.57.15` — **the identical IPs as the apex
  domain.** Routed entirely through Cloudflare and Render, exactly
  like the apex — **never touches any VNETWORK hostname or IP range
  at any point in the chain.**
- **Render service:** `sentinelops-iygs` (new this pass — a
  previously undocumented Render service name; likely the same
  deployment as the apex, given the identical resolved IPs and the
  redirect behavior).
- **WAAP integration status:** onboarded in VNETWORK's console
  (Service ID `95743`) but **structurally cannot be WAAP-protected** —
  its DNS never points at VNETWORK's edge, so no traffic for this
  hostname can ever reach VNETWORK's infrastructure regardless of
  console configuration. **This is a directly-provable, not
  hypothesized, explanation for why `bsearch` has zero data/access for
  this domain** — see Section 5.
- **Known owner/component:** same as the apex — the
  `sentinelops-homepage` deployment, or a redirect-only stub pointing
  at it.
- **Current utilization:** effectively zero as an independent asset —
  it is a redirect, not a service.
- **Potential utilization:** none as currently configured; if WAAP
  protection for the `www` hostname specifically is actually desired,
  its DNS would need to be re-pointed at VNETWORK's edge the same way
  `audit.sentinelops.fyi`'s is — a DNS change, not an application
  change.

## `audit.sentinelops.fyi`

- **Purpose:** a public, unauthenticated network-security-audit tool
  (per `content.js`'s `wafCaseStudy` and `liveInfrastructure` entries).
- **Current status:** live, `200 OK` (confirmed live this pass).
- **DNS target:** CNAME chain `audit.sentinelops.fyi` →
  `95715.cdn.vncdn.net` → `edge.vnetwork.gslb.veloceed.com` → A
  `103.162.92.38` / `103.162.92.39` — **genuinely routed through
  VNETWORK's own CDN/edge infrastructure**, reconfirmed live this pass
  (matches `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`'s original finding
  exactly, one month-equivalent later in project time — DNS has not
  changed).
- **Render service:** `rndr-id` header present live this pass,
  confirming a Render origin sits behind VNETWORK's edge. The specific
  Render service name/source repo is **still not documented anywhere
  found** (`PROJECT_STATUS.md`, `SENTINELOPS_DEEP_CONTEXT.md` §11 —
  reconfirmed, not resolved, this pass).
- **WAAP integration status:** DNS/HTTP-level routing through
  VNETWORK is proven. Whether active WAF/mitigation rules are actually
  configured and enforcing on this specific traffic path is **not
  independently verified** by this project's own tooling — see
  Section 5's ASSUMED category. The `Server` response header on this
  domain is masked/redacted (`Server: ******`, observed live this
  pass) — consistent with an edge proxy actively stripping origin
  server identification, itself a mild positive signal that *some*
  proxying/filtering layer is active, though not proof of WAF rule
  enforcement specifically.
- **Known owner/component:** the `wafCaseStudy` content in
  `sentinelops-homepage` describes this deployment in detail; its own
  backend source repo is unknown (§ above).
- **Current utilization:** high as a live public tool; unresolved as
  a WAAP-integration target because its onboarded VNETWORK Service ID
  is unconfirmed (the only confirmed Service ID, `95743`, belongs to
  `www.sentinelops.fyi`, a hostname that structurally cannot carry
  WAAP traffic — see above).
- **Potential utilization:** the correct domain for the WAAP `bsearch`
  integration and the recommended target for the Healthcheck webhook
  receiver (`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`) — but only once its
  actual VNETWORK Service ID/onboarding status is confirmed directly
  (this project has never seen a Service ID specifically tied to
  `audit.sentinelops.fyi`).

## `soc.sentinelops.fyi` **(new this pass — not in any prior discovery document)**

- **Purpose (as described):** `content.js` line 420 labels this "Home-SOC Dashboard" — listed with no `href`, unlike every other entry in that same list.
- **Current status:** resolves, but is a **parked-domain redirect, not a real service.**
- **DNS target:** A records `207.207.210.107` / `207.207.210.229`, alias for `pixie.porkbun.com` — Porkbun's generic domain-parking infrastructure.
- **HTTP response:** `301 Moved Permanently` → `http://sentinelops.fyi`, served by `Server: openresty` (Porkbun's parking-redirect server) — confirmed live this pass.
- **Render service:** none.
- **WAAP integration status:** none — never leaves Porkbun's infrastructure.
- **Known owner/component:** none — no application exists behind this hostname.
- **Current utilization:** zero. It is a label in marketing copy with no backing infrastructure.
- **Potential utilization:** if a real Home-SOC dashboard is ever built, this subdomain is already reserved and would need its DNS re-pointed to wherever that dashboard is actually hosted — currently that would contradict the project's own stated "no dashboards" architectural constraint (`SENTINELOPS_DEEP_CONTEXT.md` §12) unless the intended "dashboard" is just a redirect to a GitHub Issues filtered view, which would be consistent with existing practice.

## `mcp.sentinelops.fyi` **(new this pass — not in any prior discovery document)**

- **Purpose (as described):** `content.js` line 421 labels this "MCP Portal" — same no-`href` pattern as `soc.sentinelops.fyi`.
- **Current status:** identical situation — parked redirect.
- **DNS target:** A records `207.207.210.229` / `207.207.210.107`, alias for `pixie.porkbun.com`.
- **HTTP response:** `301 Moved Permanently` → `http://sentinelops.fyi`, `Server: openresty` — confirmed live this pass.
- **Render service:** none.
- **WAAP integration status:** none.
- **Known owner/component:** none — the MCP server (`server.js`) is a local stdio process invoked by Claude Desktop (`ARCHITECTURE_SUMMARY.md` §5); it has no HTTP-reachable "portal" anywhere in the reviewed source, so this subdomain doesn't correspond to anything that currently exists even locally, let alone publicly.
- **Current utilization:** zero.
- **Potential utilization:** same caveat as `soc.` — building a real "MCP Portal" web surface would be new infrastructure the project's own architectural constraints currently avoid.

## Diagram: domain relationships

```
                         sentinelops.fyi (Porkbun registrar/DNS/email)
                                    │
        ┌───────────────┬──────────┴──────────┬───────────────┐
        │               │                      │               │
 sentinelops.fyi   www.sentinelops.fyi   soc.sentinelops.fyi  mcp.sentinelops.fyi
   (apex, live)      (redirect only)      (parked, redirect)   (parked, redirect)
        │               │                      │               │
        ▼               ▼                      ▼               ▼
   Cloudflare      Cloudflare              pixie.porkbun.com (parking)
        │               │                   → 301 → sentinelops.fyi
        ▼               ▼
     Render          Render
  (sentinelops-   (sentinelops-iygs,
   homepage app)   301→ apex — same
                    resolved IPs as
                    the apex itself)

                                     ── separate chain, NOT connected
                                        to the above at any DNS hop ──

                         audit.sentinelops.fyi
                                    │
                                    ▼
                    VNETWORK edge (edge.vnetwork.gslb.veloceed.com,
                    via 95715.cdn.vncdn.net)
                                    │
                                    ▼
                          Render origin (rndr-id confirmed,
                          specific service unidentified)

  WAAP onboarding (Service ID 95743) is attached to www.sentinelops.fyi
  (top-left branch, Cloudflare/Render only) — NOT to the
  VNETWORK-routed audit.sentinelops.fyi branch (bottom). These two
  facts, both independently confirmed by live DNS/HTTP this pass, do
  not currently connect to each other.
```

---

# Section 2: Domain Strategy

**Which domain should be the center:** `sentinelops.fyi` (the apex) —
it is the only hostname that is simultaneously live, independently
content-bearing, and the actual subject of the project's own stated
mission (§2 of `SENTINELOPS_DEEP_CONTEXT.md`). This matches the
instruction given for the CTO strategy work already produced in that
document.

**Production domains:**
- `sentinelops.fyi` — live, serving real content, real traffic
  (Cloudflare cache-status headers confirm active caching, i.e. real
  requests).
- `audit.sentinelops.fyi` — live, serving a real, distinct application
  (different `etag`/`last-modified` than the homepage), genuinely
  routed through VNETWORK's edge.

**Research/lab domains:** none of the five discovered hostnames are
lab/research-flagged by name or content — but functionally,
`audit.sentinelops.fyi` behaves as the project's de facto
integration-research target (it's the subject of the entire
Healthcheck webhook plan and the intended WAAP protection target),
which makes it the closest thing to a "lab" domain despite being
production-live.

**Underutilized domains, ranked by ROI to fix:**

1. **`www.sentinelops.fyi`** — highest ROI to address, because it is
   actively *misleading the WAAP integration effort itself*, not just
   sitting idle. Its mere existence as the WAAP-onboarded hostname
   (Service ID `95743`) is a live, currently-blocking contributor to
   §5's root-cause question. Fixing this costs nothing (either
   re-point its DNS to VNETWORK's edge, or re-onboard the correct
   domain in the VNETWORK console) and directly unblocks the
   project's #1 stated priority (`NEXT_STEPS.md`).
2. **`soc.sentinelops.fyi` / `mcp.sentinelops.fyi`** — moderate ROI:
   currently pure liability (unbacked claims in public marketing
   copy, §7 of `SENTINELOPS_DEEP_CONTEXT.md`'s narrative-gap finding
   applies directly to these two labels), zero cost to either build
   something real behind them or remove the labels/`href`-less
   mentions from `content.js`.
3. **`audit.sentinelops.fyi`'s actual VNETWORK Service ID** — this
   isn't a domain fix so much as an information gap: nobody has
   confirmed which VNETWORK Service ID (if any) is actually attached
   to this domain, despite it being the domain doing the real work.

---

# Section 3: VNETWORK Inventory

Everything known about the VNETWORK partner account, synthesized from
every discovery document produced this session. No new API calls were
made this pass — this section is a consolidation, not new discovery,
except where marked.

**WAAP.** Console modules: Dashboard, Onboarding, Websites, Analytics,
AI-WAF, API Protection, Bot Management, Programmable Mitigation,
Emergency Mitigation, Business Usage, Logs, Settings
(`docs/VNETWORK_PRODUCT_DISCOVERY.md`). Sole programmatic surface:
`POST /v1/bsearch`. One onboarded site confirmed: **Website
`www.sentinelops.fyi`, Service ID `95743`** — per this session's
Section 1 findings, this specific hostname cannot carry real WAAP
edge traffic given its DNS. No Service ID has ever been confirmed for
`audit.sentinelops.fyi`, the domain that is actually VNETWORK-routed.

**CDN.** `GET /v3/cdn/domains` (+ 2 sibling endpoints) exist in the
API catalog but use an unresolved `{{URL}}` template variable instead
of the hardcoded host every other endpoint uses
(`docs/WAAP_LOG_SEARCH_SCHEMA.md` §7.1) — live call returned `404
Service.NotFound`. Multi-CDN Orchestration is a separate, confirmed
product with a rich metrics API (5xx rates, domain health,
traffic/cache/geo analytics) via the same `openapi.vnetwork.vn`
surface (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`).

**DNS.** VNETWORK's own DNS infrastructure is visible in this
session's live lookups as the GSLB/edge layer fronting
`audit.sentinelops.fyi` (`edge.vnetwork.gslb.veloceed.com`,
`gslb-ns1.veloceed.com`) — but the SentinelOps domain's own
authoritative DNS/registrar is Porkbun (Section 1), not VNETWORK.
VNETWORK does not appear to be the DNS provider for any
`sentinelops.fyi` hostname — it is only the CDN/edge target that one
CNAME record (`audit.sentinelops.fyi`) points at.

**Certificates.** SSL/TLS Certificates is a real, separate VNETWORK
product (beta) — managed cert inventory, free Let's Encrypt issuance
with auto-renewal, upload of third-party certs, reuse across Multi-CDN
and WAAP, plus an organization-wide Activity-feed audit trail (actor,
IP, UA, change payload) distinct from the `GET /v3/certificates` API
endpoint (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`). Never called this
session.

**Analytics.** WAAP's own console "Analytics" tab is confirmed to
exist; no metrics API beyond `bsearch`'s own aggregation capability is
confirmed (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`).

**Logs.** `bsearch` is the only confirmed log-retrieval endpoint
anywhere in the 106-endpoint catalog (`docs/VNETWORK_API_DISCOVERY.md`).

**API capabilities.** 106 total endpoints — 39 read-only (37 GET + the
1 read-only `bsearch` POST), 67 mutating (excluded from all ranking
work). Base host `openapi.vnetwork.vn`, Bearer-token auth on every
request (`docs/VNETWORK_API_DISCOVERY.md`).

**Entitlements.** Live-verified this session (not assumed): `GET
/v3/instances` → `403 Service.AccessDenied`; `GET /v3/cdn/domains` →
`404 Service.NotFound`; `POST /v1/bsearch` → `401
Request.Unauthorized` — all three reproduced identically across two
different tokens and before/after WAAP onboarding
(`docs/WAAP_LOG_SEARCH_SCHEMA.md` §7–§8).

**Service IDs.** Exactly one confirmed: **`95743`**, attached to
`www.sentinelops.fyi` (per Kevin's direct report,
`PROJECT_STATUS.md`). No other Service ID has been observed anywhere
in this project's records.

**Existing onboarded resources.** The one confirmed onboarding action
is the WAAP site for `www.sentinelops.fyi` (Service ID `95743`).
Nothing else — no Compute instance, no CDN domain, no Object Storage
bucket — has been confirmed as provisioned under this account by any
document reviewed. The account's Compute/CDN denials (`403`/`404`)
are consistent with, though not proof of, those products having no
provisioned resources at all under this account.

---

# Section 4: VNETWORK Services Not Fully Explored

| Service | What was found | What was verified | What remains unknown | Estimated strategic value |
|---|---|---|---|---|
| **Healthcheck & Alerting** | Real product (beta): Monitors → Alarms → Incidents → Playbooks, 5 notification channels including custom webhooks | Confirmed via public docs page (`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` §1) — the only VNETWORK product with native outbound push | No REST/webhook-config API exists to configure it programmatically; HMAC algorithm, signing base, and payload schema all undocumented | **High** — the only capability that inverts the project's poll-only architecture to push, but zero percent buildable until VNETWORK publishes an API |
| **Object Storage (OSS)** | Real, S3-compatible product — buckets, objects, versioning, IAM | Confirmed via public docs (`docs/VNETWORK_PRODUCT_DISCOVERY.md`) | Never tested with actual S3 SDK calls; uses a wholly separate Access Key/Secret credential never obtained by this project | **Medium** — public-bucket/ACL misconfiction scanning is a well-known real-world security finding class, but requires a new credential type this project doesn't have |
| **Multi-CDN Orchestration** | Confirmed rich metrics API (5xx rates, domain health, traffic/cache/geo analytics) via the same Bearer-token surface | Confirmed via public docs (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`) — never actually called | Whether this account has any CDN domains provisioned at all (the CDN entitlement check returned `404`/denial) | **High if entitled, unknown until the entitlement question in §5 is resolved** |
| **"Web Application Firewall"** (a separate docs-nav entry from "WAAP") | A distinct-looking navigation page found in VNETWORK's docs site structure | Not fetched — explicitly flagged as unverified in `docs/VNETWORK_CAPABILITY_ASSESSMENT.md` | Whether it's a genuinely separate, narrower product or an alias/legacy page for WAAP | **Unknown — flagged, never resolved** |
| **Kubernetes (Managed)** | Real product, OpenNebula-based | Confirmed via docs | Whether this account runs an actual cluster is unverified; API access is via `kubectl`/kubeconfig, a wholly different integration shape than everything else in this project | **Low today** — conditional on unverified actual usage |
| **Database as a Service (DBaaS)** | Real product (MySQL/PostgreSQL/MariaDB/Redis) | Confirmed via docs | "Coming soon," not self-serve | **Low today**, zero buildability |
| **Container Registry** | Real product with built-in vulnerability scanning | Confirmed via docs | "Coming soon," not self-serve | **Medium future value** (CVE findings feeding the same GitHub pipeline) once GA |
| **Serverless Functions** | Real product, API-gateway-fronted | Confirmed via docs | Pre-launch, requires an account manager | **Low today** |
| **Usage & Cost Management** | Real product — consolidated invoices, per-service usage | Confirmed via docs | Early access, requires an account manager | **Low today**, though cost-anomaly detection is a genuine security signal class if it ever ships |
| **Organizations / Projects** | Real console concept (multi-tenant workspaces, Activity audit log of membership/role changes) | Confirmed via docs | No API — privilege-escalation detection here is a manual console-review process only | **Medium** — a real, actionable security-review process, just not automatable today |

---

# Section 5: WAAP Reality Check

## PROVEN

- The `POST /v1/bsearch` endpoint, its Bearer-token auth, and its full
  request/response schema are correctly documented
  (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §1–§6) — no call this project has
  ever made against it was rejected as malformed.
- The VNETWORK API token is live and authenticates (differentiated,
  service-specific errors across every product tested, not a uniform
  failure).
- `audit.sentinelops.fyi` genuinely routes through VNETWORK's own
  edge infrastructure — reconfirmed by live DNS this pass, identical
  to the finding in `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`.
- **`www.sentinelops.fyi` — the domain actually WAAP-onboarded
  (Service ID `95743`) — does not route through VNETWORK at any point
  in its DNS chain (new this pass).** It resolves via Cloudflare to a
  Render service and 301-redirects to the apex domain. No traffic for
  this hostname can reach VNETWORK's edge, regardless of any console
  configuration.
- `soc.sentinelops.fyi` and `mcp.sentinelops.fyi` are Porkbun-parked
  redirects with no backing application (new this pass).
- Access to Compute (`403`), CDN (`404`), and WAAP (`401`) has been
  denied identically across two different API tokens and before/after
  the WAAP onboarding action.

## ASSUMED (stated in the project's narrative or plan documents, not
independently verified by this project's own tooling)

- That `audit.sentinelops.fyi` has active WAF/mitigation rules
  actually enforcing — DNS/HTTP routing through VNETWORK's edge is
  proven; whether specific rules are configured and blocking traffic
  is not directly confirmed (the masked `Server` header is a mild,
  indirect positive signal, not proof).
- The `wafCaseStudy`'s specific operational claims — "100% traffic
  routed," "0 direct-to-origin requests," "2 attack classes blocked" —
  none independently reproduced or measured by this project.
- `Threat Report #001`'s specific figures (6 malicious requests, all
  blocked) — this project has never had working WAAP API access to
  generate or verify such a report.
- That the domain-DNS mismatch (this section's PROVEN findings) is
  the complete explanation for the post-onboarding access denial —
  it plausibly explains why `bsearch` would have no data for
  `www.sentinelops.fyi` specifically, but does **not** explain the
  parallel Compute/CDN denials, which have no relationship to any
  domain's DNS at all. Both the domain-mismatch finding and the
  previously-identified account/token-scope-mismatch hypothesis
  (`SENTINELOPS_DEEP_CONTEXT.md` §8) can be true simultaneously, and
  the evidence does not yet distinguish "fix only the domain and
  access returns" from "the account itself needs a broader
  entitlement fix regardless."

## DISPROVEN

- That WAAP onboarding of `www.sentinelops.fyi` could plausibly
  unlock `bsearch` access for that hostname — disproven by DNS/HTTP:
  the hostname never sends traffic to VNETWORK's network at all.
- `soc.sentinelops.fyi` / `mcp.sentinelops.fyi` as real "Dashboard"/
  "Portal" services — disproven; both are unconfigured parked
  redirects.
- (Carried forward, previously disproven, restated for completeness:)
  a Wazuh SIEM on this host (`docs/MVP3_WAZUH_INVESTIGATION.md`);
  Suricata/Zeek sensors (`docs/HOME_SOC_SOURCE_DISCOVERY.md`); TheWall
  as a security-visualization tool (confirmed GDScript/Godot game via
  `gh api`).

---

# Section 6: External Telemetry Opportunities

Given the stated goal (AI Security Operations Platform) and existing
assets only, prioritized by (1) existing ownership, (2) existing
deployment, (3) lowest implementation effort, (4) highest learning
value:

1. **VNETWORK `bsearch` WAAP logs, once access is resolved and pointed
   at `audit.sentinelops.fyi`'s correct Service ID.** Already owned
   (account exists), already deployed (the domain is live and
   VNETWORK-routed), effort is now entitlement-resolution not new
   engineering (`SENTINELOPS_DEEP_CONTEXT.md` §8), and it's the only
   source that teaches genuine edge/WAF-layer detection engineering —
   the project's stated learning mission (§2). **Highest priority.**
2. **VNETWORK Multi-CDN metrics / Compute+LB monitoring** (once
   entitlement is confirmed) — same ownership/deployment profile as
   #1, moderate effort (already-documented endpoints,
   `docs/VNETWORK_API_DISCOVERY.md`), teaches infrastructure-health
   correlation alongside security signal.
3. **Home-SOC's already-integrated sources, extended** — Windows
   Event Logs beyond what's currently used (requires only an
   `auditpol` config change, already identified as the specific
   blocker — `docs/HOME_SOC_SOURCE_DISCOVERY.md`). Already owned,
   already deployed, lowest possible effort of any item on this list.
4. **VNETWORK SSL/TLS certificate expiry monitoring** — already
   cataloged (`GET /v3/certificates`), low effort, teaches a "boring
   but critical" alert class the pipeline currently has zero coverage
   of.
5. **VNETWORK attack-surface inventory** (elastic IPs, reserved IPs,
   CDN domains, security groups) — already cataloged, low effort once
   entitlement resolves, directly feeds the already-documented
   Digital Risk Twin concept (`NEXT_STEPS.md`).
6. **GitHub itself as a telemetry source** — not currently used as
   one anywhere in the pipeline, but GitHub already provides an audit
   log / webhook surface for the very repositories this project
   already owns (e.g. unexpected collaborator changes, unusual
   push/force-push activity). Zero new ownership required, low
   effort, directly on-mission (privilege-escalation-style detection,
   the same class of signal `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`
   already flagged as valuable for VNETWORK's own Organizations
   product).
7. **VNETWORK Object Storage misconfiguration scanning** — real
   value (public-bucket exposure is a top real-world breach class),
   but requires a new credential type (Access Key/Secret) this
   project has never obtained — higher effort than everything above.
8. **GitHub Mobile / iPhone** — **not a telemetry source**, a
   notification/triage channel (`ARCHITECTURE_SUMMARY.md` §3). Listed
   here only to explicitly rule it out as a "source" per the
   instruction to consider it — it has no data to contribute, only a
   place to receive alerts already generated elsewhere.

---

# Section 7: Asset Utilization Score

| Asset | Current utilization | Potential utilization | Most valuable next step |
|---|---|---|---|
| `sentinelops.fyi` | 60% — live, real traffic, but its own content contains unverified/disproven claims undermining its purpose | 95% | Reconcile marketing copy with verified reality (`SENTINELOPS_DEEP_CONTEXT.md` §11/§16) |
| `audit.sentinelops.fyi` | 40% — genuinely live and VNETWORK-routed, but its backend is unowned/unauditable from this project and its actual WAAP Service ID is unconfirmed | 90% | Confirm its VNETWORK Service ID and locate its backend source repo |
| WAAP | 15% — fully designed, zero live data, and the one confirmed onboarding action was attached to the wrong domain | 90% | Re-onboard (or DNS-repoint) the correct, VNETWORK-routed domain, then resolve the account-entitlement question |
| VNETWORK partner account | 20% — one product (WAAP) partially configured against the wrong domain; Compute/CDN entitlement status unresolved; several real products (Multi-CDN, Certificates, Healthcheck) never touched at all | 85% | A single entitlement/Service-ID audit across the whole account, not just WAAP |
| Home-SOC | 75% — live, working, verified against a real event, currently reporting a clean baseline | 90% | Extend with the already-identified `auditpol` change for process-creation telemetry |
| MCP | 55% — 95 real tools, but most (hunting, forensics, persistence) are manually-invoked only, never wired into automation; the incident scripts don't even call through MCP | 85% | Wire the incident-creation pipeline through MCP tool calls instead of duplicating logic in standalone scripts |
| GitHub | 85% — the entire incident system's backbone, actively used, near-fully realized for its role | 90% | Use its own audit/webhook surface as a telemetry source (Section 6, item 6) |
| GitHub Mobile | 80% — already the de facto SOC console, as intended | 85% | No change needed; already close to the project's own stated ideal |
| iPhone | 80% — the terminal endpoint of the whole notification chain, working as designed | 80% | N/A — this is an endpoint, not a capability to extend |

---

# Section 8: What Another CTO Would Miss

- **The WAAP-onboarded domain doesn't — and structurally can't —
  carry WAAP traffic.** Every prior document in this project's
  history treated the post-onboarding access denial as purely an
  entitlement/timing question. Live DNS this pass shows a simpler,
  provable, independent cause specific to that one domain: it never
  routes through VNETWORK at all. A CTO reading only the prior
  discovery documents would keep chasing account-entitlement theories
  indefinitely without ever checking whether the onboarded hostname
  itself was even capable of producing WAAP data in the first place.
- **Two subdomains (`soc.`, `mcp.`) are named and described in public
  marketing copy but were never provisioned at all** — not "not yet
  built," but pointed at the domain registrar's generic parking page.
  This is a cheaper, more concrete version of the narrative/reality
  gap already identified in `SENTINELOPS_DEEP_CONTEXT.md` — cheaper
  because fixing it is a single DNS decision (build something real, or
  remove the unlinked labels), not a research project.
- **`audit.sentinelops.fyi` — the one domain doing genuinely real
  security work — has no confirmed VNETWORK Service ID of its own.**
  Every VNETWORK Service ID this project has ever observed (`95743`)
  belongs to the *other*, non-functional domain. This means the
  actual, working, WAAP-relevant asset may not even be visible to this
  project's own API token in any enumerable way — worth checking
  directly rather than assuming it's "just" a data/access problem.
- **Porkbun, not VNETWORK or Render, is the actual root of trust for
  the entire domain (registrar, DNS, and email).** Every other finding
  in this document is downstream of Porkbun's DNS records. A future
  operator locked out of Porkbun account access would be unable to
  fix any of the findings in this document, regardless of GitHub or
  Render access — an ownership/access dependency not previously
  documented anywhere in this project.
- **The two "parked" subdomains cost nothing and currently return
  negative value** — they exist only as unlinked text in a contact
  list, adding two more unverifiable claims to the same credibility
  surface already flagged as the project's largest hidden risk
  (`SENTINELOPS_DEEP_CONTEXT.md` §11), for zero corresponding benefit.
  Removing two lines of `content.js` is the single cheapest risk
  reduction available anywhere in this entire assessment.
