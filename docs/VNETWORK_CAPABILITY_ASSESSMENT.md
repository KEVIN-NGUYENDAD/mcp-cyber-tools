# VNETWORK Capability Assessment

**Source note (important):** the task asked for Partner Portal
exploration (`partner.vnetwork.vn/services`) with login, screenshots,
and menu evidence. That wasn't possible — this session has no browser
automation tool, no VNETWORK MCP connector, and no stored credentials
or session for the Partner Portal. An unauthenticated fetch of that URL
returns only a bare page title behind a login wall. Per the user's
choice, this assessment is built entirely from **VNETWORK's public
documentation** (`docs.vnetwork.vn`) and the OpenAPI collection already
catalogued in `docs/VNETWORK_API_DISCOVERY.md` /
`docs/VNETWORK_PRODUCT_DISCOVERY.md`.

**What that means for confidence:** every line below is either
`CONFIRMED (docs)` — stated directly in VNETWORK's public
documentation or the Postman collection — or `NOT DOCUMENTED` — absent
from what's publicly published, which is not the same as "doesn't
exist." Nothing here reflects this account's actual plan tier,
provisioned resources, or usage — that data is only visible inside the
authenticated portal, which wasn't reachable. No VNETWORK API endpoint
was called; no resources were provisioned; no credits were spent.

---

## Compute

### Service: Cloud Compute
**Purpose:** OpenNebula-based IaaS — VMs, block volumes, networks,
VPCs, load balancers, security groups, SSH keys, snapshots, backups.
**Logs:** NOT DOCUMENTED (no dedicated compute log endpoint; only
monitoring data points).
**Metrics:** CONFIRMED — `GET /v3/instances/:id/monitoring` (CPU/mem/
network time series), `/summary` (realtime + latest snapshot),
`GET /v3/lbs/:id/monitoring` / `/stats`.
**Alerts:** NOT DOCUMENTED — no alert-rule endpoints anywhere in the
API.
**API:** CONFIRMED — `openapi.vnetwork.vn`, Bearer token, 106
endpoints total for this product family (full catalog in
`docs/VNETWORK_API_DISCOVERY.md`).
**SentinelOps Use Case:** already the foundation of MVP #3/#4's
architecture pattern — instance/LB monitoring + security-group drift
detection, same poll-and-diff shape as security-watch.js.
**ROI (1-10): 9**

### Service: Enterprise Compute
**Purpose:** Dedicated VMs on Private Cloud, HA clustering, VMware
compatibility for on-prem migrations. CONFIRMED (docs).
**Logs:** NOT DOCUMENTED.
**Metrics:** "built-in monitoring" is a listed feature (CONFIRMED it
exists as a capability), but no API surface for it is documented.
**Alerts:** NOT DOCUMENTED.
**API:** NOT DOCUMENTED.
**SentinelOps Use Case:** none buildable today — no confirmed API.
**ROI (1-10): 3**

### Service: Serverless Functions
**Purpose:** Pay-per-invocation code execution behind an API gateway,
for event-driven/webhook workloads. CONFIRMED (docs).
**Logs / Metrics / Alerts:** NOT DOCUMENTED.
**API:** an "API Gateway" is mentioned as a component; no spec
published. **Status: pre-launch, not self-serve** — must contact an
account manager.
**SentinelOps Use Case:** if it ships, this is a plausible *host* for
SentinelOps's own alert-processing logic (running the MCP scoring/
GitHub-issue code at VNETWORK's edge instead of on the home laptop) —
speculative, not buildable now.
**ROI (1-10): 2**

---

## Kubernetes

### Service: Managed Kubernetes
**Purpose:** Fully-operated K8s (control plane, node pools, ingress,
autoscaling) on VNETWORK's OpenNebula platform. CONFIRMED (docs).
**Logs:** CONFIRMED — cluster console has a dedicated "Logs" section.
**Metrics:** CONFIRMED — cluster console has a dedicated "Metrics"
section.
**Alerts:** NOT DOCUMENTED as a dedicated feature (Healthcheck &
Alerting is referenced as the platform-wide mechanism).
**API:** NOT DOCUMENTED as a VNETWORK-specific REST API — access is
via standard `kubectl`/Helm against a downloadable kubeconfig. This is
a **different integration shape** (Kubernetes API server, not
`openapi.vnetwork.vn`).
**SentinelOps Use Case:** only relevant if this account actually runs
a cluster here (unknown/unverified) — if so, standard K8s audit-log
and metrics-API integration (kubectl/client-go), not VNETWORK-specific
code.
**ROI (1-10): 5** *(conditional on actual usage, which is unverified)*

### Service: Container Registry
**Purpose:** Private container image storage with per-repo access
control and **built-in vulnerability scanning**. CONFIRMED (docs).
**Logs / Metrics / Alerts / API:** NOT DOCUMENTED. **Status: "coming
soon," not yet self-serve.**
**SentinelOps Use Case:** the vulnerability-scanning feature is
genuinely on-mission (CVE findings → GitHub Issue, same pipeline
shape) but the service isn't available yet.
**ROI (1-10): 2** *(high future value, zero current buildability)*

---

## Databases

### Service: Database as a Service (DBaaS)
**Purpose:** Managed MySQL, PostgreSQL, MariaDB, Redis with automated
backups and point-in-time recovery. CONFIRMED (docs).
**Logs / Metrics / Alerts:** "Monitoring" is a listed feature; no
detail on slow-query logs, connection metrics, or backup-alert
mechanics.
**API:** NOT DOCUMENTED. **Status: "coming soon," not self-serve.**
**SentinelOps Use Case:** none buildable today.
**ROI (1-10): 2**

---

## Storage

### Service: Block Storage (Volumes) — part of Cloud Compute
**Purpose:** Attachable block volumes for instances, OS images,
snapshots, backups. CONFIRMED (docs/API — already fully catalogued
under Compute's OpenAPI collection).
**Logs / Alerts:** NOT DOCUMENTED.
**Metrics:** NOT DOCUMENTED (no volume-level monitoring endpoint).
**API:** CONFIRMED — `GET /v3/volumes`, `/v3/backups`, etc.
**SentinelOps Use Case:** low — CMDB completeness only, already noted
LOW/MEDIUM in the prior catalog.
**ROI (1-10): 3**

### Service: Object Storage (OSS)
**Purpose:** S3-compatible object storage — buckets, objects,
versioning, object lock, public-access controls, IAM. CONFIRMED
(docs).
**Logs / Metrics / Alerts:** NOT DOCUMENTED (no VNETWORK-specific
equivalent of S3 server-access-logging, CloudTrail, or event
notifications confirmed).
**API:** CONFIRMED to exist, but as the **generic S3 protocol**
(`ListBuckets`, `ListObjectsV2`, `GetBucketAcl`, `GetBucketVersioning`,
etc. via any S3 SDK), not a VNETWORK-specific REST API. Uses a
**separate Access Key/Secret credential**, not the Bearer token.
**SentinelOps Use Case:** public-bucket/ACL misconfiguration scanning
— one of the most common real-world cloud security findings. Distinct
integration (e.g. `boto3`) from everything else in this assessment.
**ROI (1-10): 6**

---

## Networking & CDN

### Service: Multi-CDN Orchestration
**Purpose:** Single control plane steering traffic across multiple CDN
backends (failover/weighted/latency routing), plus caching, TLS, and
WAF policy management from one dashboard. CONFIRMED (docs).
**Logs:** CONFIRMED indirectly — the WAAP `bsearch` endpoint queries
this traffic.
**Metrics:** CONFIRMED, and rich — total requests/volume/peak
bandwidth/cache-hit ratio (24h/7d/30d), geographic distribution,
per-backend traffic splits, domain-performance ranking, **domain
health status and 5xx error rates**, per-domain egress/bandwidth
billing.
**Alerts:** NOT DOCUMENTED as a dedicated alert-rule API, but the 5xx
error-rate and domain-status data is exactly the kind of signal
SentinelOps could threshold itself.
**API:** CONFIRMED — the docs explicitly reference "the OpenAPI
endpoint and your account ID for automating the same actions, with
links to Manage API keys and the API documentation" — the same unified
`openapi.vnetwork.vn` surface (`/v3/cdn/domains` etc., already
catalogued).
**SentinelOps Use Case:** edge-layer health/anomaly monitoring —
domain going unhealthy or a 5xx spike is an actionable GitHub Issue,
using data already reachable today.
**ROI (1-10): 9**

---

## Media & Streaming

### Service: FastChannel / Live Media / Cloud Encoding / On-Demand
### Transcoding / AES Gateway (product family)
**Purpose:** Linear-channel automation, live streaming, encoding,
transcoding, and DRM-adjacent delivery (AES Gateway). CONFIRMED (docs,
FastChannel checked directly; siblings listed in the docs nav but not
individually verified this pass).
**Logs / Metrics / Alerts / API:** NOT DOCUMENTED for FastChannel; not
checked for the sibling services.
**SentinelOps Use Case:** none identified — outside SentinelOps's
security-operations mission, and no security-relevant signal was found
in what's documented.
**ROI (1-10): 1**

---

## Security

### Service: WAAP (Web Application & API Protection)
**Purpose:** AI-WAF, bot management, API protection, DDoS/emergency
mitigation, at the edge. CONFIRMED (docs + product page).
**Logs:** CONFIRMED — `POST /v1/bsearch` (client IP, URI, status code,
user agent, upstream latency, regex/exact-match filtering,
aggregation). The richest real security-log source found in this
entire assessment.
**Metrics:** console "Analytics" tab is CONFIRMED to exist; no metrics
API confirmed beyond `bsearch` aggregation.
**Alerts:** NOT DOCUMENTED as a self-service API; the premium tier
offers a **human** "Dedicated SOC" / "Expert SOC" monitoring service
(CONFIRMED, but that's VNETWORK's staff, not an integration point).
**API:** CONFIRMED (`bsearch`).
**SentinelOps Use Case:** the leading candidate for an MVP #5 — same
alert → score → GitHub Issue pattern as MVP #3/#4.
**ROI (1-10): 10**

### Service: "Web Application Firewall" (listed separately from WAAP in docs nav)
**Purpose:** UNKNOWN — appears as its own nav entry
(`/docs/security/web-application-firewall`) alongside WAAP in the docs
site structure, but this page was **not fetched this pass**. Whether
it's a distinct, narrower product or just an alternate name/legacy
page for WAAP is **not verified** — flagging as an open question
rather than assuming either answer.
**Logs / Metrics / Alerts / API:** UNKNOWN.
**SentinelOps Use Case:** UNKNOWN pending verification.
**ROI (1-10): N/A — insufficient evidence**

### Service: SSL/TLS Certificates
**Purpose:** Managed certificate inventory — issue free Let's Encrypt
certs (auto-renewed ~30 days before expiry), upload third-party certs,
reuse across Multi-CDN and WAAP. CONFIRMED (docs). **Status: beta.**
**Logs:** CONFIRMED — an organization-wide **Activity feed** audit
trail (issued/uploaded/renewed/re-checked/downloaded/revoked, with
actor, IP, user agent, and change payload).
**Metrics:** NOT DOCUMENTED.
**Alerts:** NOT DOCUMENTED as an explicit expiry-alert feature (though
auto-renewal reduces the need).
**API:** the docs overview page for this specific product doesn't
mention an API — **but** `GET /v3/certificates` already exists in the
catalogued OpenAPI collection and is very likely this same product's
backend, even though the two docs sources don't cross-reference each
other.
**SentinelOps Use Case:** expiry monitoring via `/v3/certificates`
(already ranked #7/#10 in prior passes) plus the Activity-feed audit
trail as a genuine security-review artifact, if it's ever exposed
programmatically.
**ROI (1-10): 7**

---

## Observability

### Service: Healthcheck & Alerting
**Purpose:** HTTP/TCP/DNS/TLS monitors → alarms → incidents →
automated-remediation playbooks. CONFIRMED (docs). **Status: beta.**
**Logs:** NOT DOCUMENTED (no log-retrieval API/UI element described).
**Metrics:** CONFIRMED — uptime and latency tracking, console-only.
**Alerts:** CONFIRMED as the core feature — Email, Slack, Microsoft
Teams, Telegram, **and custom webhooks**.
**API:** NOT DOCUMENTED. Console/Partner-Portal configuration only.
**SentinelOps Use Case:** the single best **strategic fit** in this
entire assessment — native outbound webhooks would let VNETWORK push
alerts directly into a SentinelOps receiver, inverting the
poll-and-diff architecture used everywhere else. Not buildable until
an API or webhook-payload spec is published.
**ROI (1-10): 8** *(value is very high; buildability today is zero —
score reflects the blended reality, not pure potential)*

---

## Management

### Service: Organizations
**Purpose:** Multi-tenant structure — Projects (isolated workspaces,
e.g. prod/staging separation), Teams, and Owner/Member RBAC.
CONFIRMED (docs).
**Logs:** CONFIRMED — an "Activity" audit log of membership/role/
resource changes, with actor and timestamp.
**Metrics / Alerts:** NOT DOCUMENTED.
**API:** NOT DOCUMENTED.
**SentinelOps Use Case:** privilege-escalation detection (e.g. "user X
was made Owner") is a real, on-mission security signal — but with no
API, it's a manual console-review process today, not an automatable
one.
**ROI (1-10): 4**

### Service: Projects (within Organizations)
**Purpose:** Scoped sub-workspaces within an Organization for resource
and access isolation. CONFIRMED (docs) — this is the answer to why
the earlier OpenAPI collection had **no "Projects" endpoints**: Projects
is an Organizations-console concept, not a resource type in the
compute API.
**Logs / Metrics / Alerts / API:** same as Organizations — covered by
the same Activity log, no dedicated API.
**SentinelOps Use Case:** none additional beyond Organizations.
**ROI (1-10): 3**

### Service: API Keys / Account
**Purpose:** Account-wide Bearer-token credential management. CONFIRMED
(docs) — "Create new key," name, creation date, last-used date shown
in console.
**Logs:** the "last-used date" field is CONFIRMED to exist in the
console; whether it's queryable via API is NOT DOCUMENTED.
**Metrics / Alerts:** NOT DOCUMENTED.
**API:** this **is** the API — `Authorization: Bearer <key>` against
`https://openapi.vnetwork.vn/v1` (base for the whole catalogued
collection).
**Security finding (confirmed, not assumed):** "A key grants full
programmatic access to your account" — **no per-service scoping, no
documented rotation policy, no documented usage audit log.** A single
leaked key is account-wide compromise across every product in this
assessment.
**SentinelOps Use Case:** a lightweight recurring manual review
(console check: any key not created/used recently that should be
revoked) is the only mitigation available today, given no API exists
to automate the check.
**ROI (1-10): 5** *(the finding itself is valuable; the mitigation is
currently a process, not code)*

### Service: Usage & Cost Management
**Purpose:** Consolidated invoices, payment methods, per-service usage
reporting. CONFIRMED (docs). **Status: early access, not self-serve**
— requires an account manager.
**Logs / Metrics / Alerts / API:** NOT DOCUMENTED.
**SentinelOps Use Case:** cost-anomaly detection (a sudden spend spike
can indicate a compromised/abused resource) is a real and often
under-used security signal — not available yet.
**ROI (1-10): 2**

---

## OpenAPI (meta)

### Service: The unified `openapi.vnetwork.vn` REST API
**Purpose:** The one Bearer-token REST surface underlying Cloud
Compute, Volumes/Backups, Networking, Security Groups, Certificates,
CDN domains, and WAAP log search. CONFIRMED — 106 endpoints, fully
catalogued in `docs/VNETWORK_API_DISCOVERY.md`.
**Logs:** CONFIRMED (WAAP `bsearch` only).
**Metrics:** CONFIRMED (Compute/LB monitoring).
**Alerts:** NOT DOCUMENTED anywhere in this API.
**API:** this is the API.
**SentinelOps Use Case:** the foundation everything else in this
report builds on — already proven with MVP #3/#4's
`create_securitywatch_incident.py` pattern.
**ROI (1-10): 10**

---

# Top 10 Opportunities

Ranked by impact (value × buildability today, per the "no
provisioning, no credits, discovery only" scope):

1. **Opportunity:** WAAP log-based alerting (`bsearch` → GitHub
   Issue). **Estimated Effort:** Low — reuse the exact MVP #3/#4
   pattern, one new mapper. **Estimated Value:** High. **Why it
   matters:** the richest real security-log source found across the
   entire assessment (both sessions), available today with the
   existing credential.
2. **Opportunity:** Multi-CDN health/error-rate alerting (domain
   status, 5xx rate, traffic anomalies). **Estimated Effort:** Low-
   Medium. **Estimated Value:** High. **Why it matters:** confirmed
   rich metrics API, catches edge-layer outages/attacks that predate
   or accompany a WAAP log signal.
3. **Opportunity:** Compute instance monitoring + security-group drift
   detection. **Estimated Effort:** Low. **Estimated Value:** High.
   **Why it matters:** proven pattern (security-watch.js), applied one
   layer up at the cloud-firewall level.
4. **Opportunity:** SSL/TLS certificate expiry monitoring +
   Activity-feed audit trail. **Estimated Effort:** Low. **Estimated
   Value:** Medium-High. **Why it matters:** a classic "boring but
   critical" alert class (expired cert = outage) that nothing else in
   the pipeline covers; audit trail is a real security-review artifact
   if ever exposed via API.
5. **Opportunity:** Object Storage public-bucket/ACL misconfiguration
   scanning. **Estimated Effort:** Medium — new credential type (S3
   Access Key/Secret), new SDK (`boto3`). **Estimated Value:**
   Medium-High. **Why it matters:** public-bucket exposure is one of
   the most common real-world breach classes; well-trodden integration
   pattern even though it's a different shape from everything else.
6. **Opportunity:** Attack-surface inventory baseline (CDN domains +
   Elastic/Reserved IPs). **Estimated Effort:** Low. **Estimated
   Value:** Medium. **Why it matters:** answers "what do we even
   expose," and gives every other alert a target to correlate against.
7. **Opportunity:** API-key hygiene review (process, not code).
   **Estimated Effort:** Low (a recurring checklist, not a build).
   **Estimated Value:** Medium. **Why it matters:** confirmed finding
   — keys are full-access, unscoped, with no documented rotation or
   usage-audit API. The mitigation available today is manual, but it's
   real and free.
8. **Opportunity:** Organizations/Projects privilege-change review
   (process, not code). **Estimated Effort:** Low. **Estimated
   Value:** Medium. **Why it matters:** the Activity audit log is real
   (membership/role changes with actor+timestamp); no API yet, but a
   recurring console check catches privilege escalation.
9. **Opportunity:** Healthcheck & Alerting webhook receiver
   (future-watch). **Estimated Effort:** Medium, but **blocked**
   until VNETWORK ships an API/webhook spec. **Estimated Value:** Very
   High. **Why it matters:** the only product in this whole assessment
   with native outbound webhooks — would flip the architecture from
   polling to push. Worth checking back on periodically.
10. **Opportunity:** Container Registry vulnerability-scan ingestion
    (future-watch). **Estimated Effort:** Medium, blocked until GA
    (currently "coming soon"). **Estimated Value:** Medium. **Why it
    matters:** built-in CVE scanning feeding the same GitHub Issue
    pipeline the moment the service and its API exist.

---

# Crazy But Realistic Ideas

Using only: SentinelOps, MCP, GitHub, GitHub Mobile, iPhone, WAAP,
VNETWORK services already discovered, and existing domains. No new
paid services, nothing provisioned.

1. **SOC-in-your-pocket incident commander.** A WAAP `bsearch` anomaly
   opens a GitHub Issue → GitHub Mobile pushes it to the iPhone →
   replying on the issue with a structured comment (e.g.
   `/note investigated, false positive`) is read back by an MCP poll
   and turned into a follow-up analysis comment or a label change.
   Nothing mutating is ever called against VNETWORK — the loop stays
   human-approved, but the whole triage-and-acknowledge cycle happens
   from a phone, using only pieces that already exist.

2. **Attack-surface diff bot.** A scheduled task (same Task Scheduler
   mechanism `security-watch.js` already uses) polls
   `/v3/cdn/domains`, `/v3/elastic_ips`, `/v3/certificates`, and
   `/v3/secgroups`, diffs against yesterday's snapshot (same JSON
   state-file pattern the dormant ARP-based Home-SOC collector already
   uses), and opens **one** daily digest GitHub Issue only when
   something actually changed. This is a direct re-application of the
   `nightly-security-brief-trigger.js` / `home-soc-brief.js` scripts
   already sitting unused in the Roaming project tree — same shape,
   new data source.

3. **Host-to-edge correlation.** When `security-watch.js` or Defender
   fires a host-level alert (e.g. a suspicious outbound connection),
   automatically run a `bsearch` query for that host's public IP in
   the same time window. A hit against a WAAP-fronted domain with
   anomalous URIs upgrades the GitHub Issue with a
   `confirmed-outbound` label — two independently weak signals (host +
   edge) become one strong one, using only read-only calls already
   catalogued.

4. **Live cert countdown, one issue, forever.** Instead of opening a
   new issue per certificate, maintain **one** pinned "Certificate
   Status" GitHub Issue and update its body in place (the exact
   occurrence-tracking pattern MVP #4 already built) with
   days-to-expiry per domain from `/v3/certificates` — always current,
   always one tap away on GitHub Mobile, zero marginal cost per run.

5. **GitHub Mobile as the SOC console.** No budget exists for a
   dashboard — so don't build one. Extend the label taxonomy already
   built in MVP #4 (`critical`/`high`/`defender`/`control-drift`/
   `firewall`) with `waap`/`cdn`/`cert`, and use a saved GitHub Mobile
   search (`is:open label:critical`) as the de facto SOC view. Free,
   and it already exists the moment the labels do.

---

# If I were CTO of SentinelOps, what would be the next 3 projects I would build and why?

1. **MVP #5: WAAP `bsearch` → GitHub Issue.** It's the highest-ROI
   item found across both discovery passes — real security-log data,
   available today, and it's a direct extension of the exact pattern
   already proven twice (MVP #3, MVP #4). This is the obvious next
   build, not a judgment call.

2. **The attack-surface diff bot (Crazy Idea #2).** SentinelOps
   currently knows a lot about *this laptop* (Defender, control drift)
   and nothing about *what VNETWORK-side surface is exposed to the
   internet* — domains, IPs, certs, firewall rules. A daily digest
   that only speaks up when something changes closes that gap cheaply,
   and it's not a new architecture — it's the same brief-generation
   code already written for the LAN layer, pointed at a new data
   source.

3. **A standing "watch list," not code — a monthly 10-minute check on
   the two capabilities that would change everything the moment they
   ship: Healthcheck & Alerting's API/webhook spec, and Container
   Registry GA.** The former inverts the whole architecture from
   polling to push; the latter adds CVE findings to the pipeline for
   free. Neither is buildable today, and no amount of eagerness
   changes that — but both are worth revisiting on a cadence instead
   of forgetting about, because they're the two highest-strategic-fit
   items this assessment found.

---

## Explicitly not done in this pass

- Did not log into the Partner Portal (no browser session/credentials
  available)
- No screenshots, menus, or account-specific data were captured or
  fabricated
- No VNETWORK API endpoint was called
- No resources were provisioned
- No credits were spent
- No infrastructure was created
- No code was written or changed
