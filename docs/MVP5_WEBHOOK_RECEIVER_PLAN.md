# MVP #5: VNETWORK Healthcheck Webhook Receiver — Implementation Plan

Planning only, per instruction — **nothing in this document has been
implemented.** No code was written, no domain was touched, no
resources were provisioned.

```
VNETWORK Healthcheck & Alerting (Monitor -> Alarm -> Incident)
  |
  v
Webhook  (signed JSON POST)
  |
  v
MCP  (new webhook receiver -- this plan)
  |
  v
Risk Score + Duplicate Detection   <- reused unchanged from MVP #3/#4
  |
  v
GitHub Issue (new) / occurrence update (duplicate)
  |
  v
Auto Labels + MCP Analysis Comment  <- reused unchanged from MVP #4
  |
  v
Assign KEVIN-NGUYENDAD
  |
  v
GitHub Mobile
```

## 1. What's confirmed vs. what still needs verification

Before designing the payload mapping, I re-checked the claim directly
against VNETWORK's docs (a page this project hadn't fetched before:
`docs.vnetwork.vn/docs/observability/healthcheck/notifications`) rather
than taking it as given. Result: **the claim holds**, with real gaps
that a plan-only pass can't close.

| Claim | Status | Source |
|---|---|---|
| Webhook notification channel exists | **CONFIRMED** | Notifications page: "a custom webhook" is one of five channel types |
| Custom endpoint URL | **CONFIRMED** | "Set the **endpoint URL**..." |
| Optional HMAC secret | **CONFIRMED** | "...optionally set an **HMAC secret**" |
| Signed JSON POST | **CONFIRMED** (as a label) | Delivery is described as "signed JSON POST" |
| Signature header | **CONFIRMED** | `X-Webhook-Signature` |
| HMAC **algorithm** (SHA-256? SHA-1?) | **NOT DOCUMENTED** | absent from the page |
| Signing base (raw body? body+timestamp?) | **NOT DOCUMENTED** | absent |
| Payload **schema** (field names, example) | **NOT DOCUMENTED** | absent |
| Retry / timeout behavior | **NOT DOCUMENTED** | absent |

**Implication for this plan:** the receiver's signature-verification
and payload-mapping code can be designed defensively (see §5 and §2)
but the exact algorithm and field names must be confirmed empirically
— by configuring one real test Monitor against a temporary logging
endpoint and capturing an actual delivery — before this goes live.
That step is implementation, not planning, so it's listed as the first
task of the *next* phase, not done here.

## 2. Webhook payload mapping (best-effort schema, to be confirmed)

No schema is published, so this mapping is a **defensive best guess**
based on the product's own vocabulary (Monitors → Alarms → Incidents,
confirmed in `docs/VNETWORK_PRODUCT_DISCOVERY.md`), written to degrade
safely if real field names differ:

```python
def to_alert(payload: dict) -> dict:
    """Normalize a VNETWORK Healthcheck webhook delivery onto the
    existing alert schema. Field names are best-guess pending a real
    captured payload -- every .get() has a safe fallback so an unknown
    shape produces a low-fidelity-but-non-crashing alert instead of an
    exception."""
    monitor = payload.get("monitor", {})
    alarm = payload.get("alarm", {})
    incident = payload.get("incident", payload)  # some providers put fields at top level

    severity = str(alarm.get("severity", incident.get("severity", "high"))).lower()

    return {
        "source": "vnetwork_healthcheck",
        "event_type": str(alarm.get("type", incident.get("type", "monitor_alarm"))).lower(),
        "severity": severity if severity in {"critical", "high", "medium", "low"} else "high",
        "ip": "unknown",
        "threat_signature": incident.get("message") or alarm.get("description") or "VNETWORK Healthcheck alarm",
        "process": None,
        "file": f"monitor={monitor.get('name', 'unknown')} target={monitor.get('target', 'unknown')}",
        "detection_time": incident.get("triggered_at") or incident.get("created_at"),
        "_raw": payload,  # kept for the first N deliveries only, see 5.3
    }
```

The `_raw` field is deliberate: for the first real deliveries, log the
full untrusted-but-signature-verified payload so the actual schema can
be read back and this mapper corrected — the same "verify before you
build on it" discipline used throughout this project.

## 3. Deployment location: `audit.sentinelops.fyi` vs `sentinelops.fyi`

Checked both directly (DNS + HTTP) rather than assuming from the
domain names alone:

| | `sentinelops.fyi` | `audit.sentinelops.fyi` |
|---|---|---|
| DNS | A record → `216.24.57.7` / `216.24.57.15` | CNAME → `edge.vnetwork.gslb.veloceed.com` → `95715.cdn.vncdn.net` (**VNETWORK's own CDN**) |
| HTTP response | `rndr-id` header present (Render), fronted by Cloudflare | `rndr-id` header present (Render origin) **behind** VNETWORK's edge, Cloudflare also present in the chain |
| What's actually running there | **Confirmed static** — this is the `sentinelops-homepage` repo: `package.json` has only `vite`/`react`, no server framework, no API routes. A Vite static build has **no server-side code execution** — it cannot verify an HMAC signature or process a POST body at all. | **Confirmed live**, and — per `src/data/content.js`'s `wafCaseStudy` content in this repo, which I'd previously (incorrectly) treated as narrative/marketing copy — this is a **real deployment already sitting behind VNETWORK WAAP with a Render origin**, matching exactly what the DNS/HTTP check shows. |
| Source repo | This repo (`sentinelops-homepage`) | **Not found on this machine.** Searched `mcp-cyber-tools` (both copies), the Roaming project tree, and `sentinelops-homepage` — no matching Render config, no matching domain string, nothing that builds to this origin. |

**Recommendation: `audit.sentinelops.fyi`.** `sentinelops.fyi` is ruled
out outright — it's confirmed static with zero backend, and mixing a
webhook receiver into the marketing homepage's build would be the
wrong shape even if it were technically possible (unrelated concerns,
unrelated deploy cadence). `audit.sentinelops.fyi` is thematically and
architecturally correct — it's already the security/audit-branded
subdomain, already sitting behind VNETWORK's own WAAP, which is a
fitting place for VNETWORK's own alert delivery to land.

**Open question this plan cannot resolve:** I cannot find the source
code or Render service behind `audit.sentinelops.fyi` anywhere on this
machine. Before implementation starts, this needs to come from you:
- Is there an existing Render web service (with a server, not a static
  site) already deployed there that a new route can be added to?
- Or does a small new backend need to be stood up and pointed at that
  subdomain?
This determines whether MVP #5 is "add one route to an existing
service" or "provision a new minimal service" — a meaningfully
different amount of work, and not something to guess.

## 4. Recommended endpoint path

```
POST /api/webhooks/vnetwork-healthcheck
```

Reasoning: namespaced under `/api/webhooks/` (room for future
providers — e.g. a WAAP webhook later, per the MVP #4 discovery
findings — without a path collision), provider-specific suffix (not
just `/webhook`, which becomes ambiguous the moment a second source is
added), no trailing resource ID (this is a single fixed sink, not a
per-resource endpoint), and no version prefix (`/v1/...`) since nothing
here is a public API contract — it's a private delivery target only
VNETWORK calls.

## 5. Recommended HMAC validation strategy

1. **Read the raw request body before any JSON parsing.** The
   signature must be verified against the exact bytes VNETWORK sent —
   parsing to an object and re-serializing changes whitespace/key
   order and silently breaks verification. This is the single most
   common webhook-receiver bug industry-wide, and worth stating
   explicitly since the algorithm itself is still unconfirmed.
2. **Compute `HMAC-SHA256(secret, raw_body)`** as the default
   assumption (the industry-standard choice, and what most providers
   with this exact "endpoint URL + optional HMAC secret" phrasing use)
   — but treat this as the first thing to confirm empirically (§1),
   not as settled.
3. **Compare against `X-Webhook-Signature` using a constant-time
   comparison** (e.g. Python's `hmac.compare_digest`, Node's
   `crypto.timingSafeEqual`) — never `==` / `===`, which leaks timing
   information an attacker can use to forge a valid signature
   byte-by-byte.
4. **Reject (401) if the header is missing, malformed, or doesn't
   match** — fail closed. Do not process the payload before signature
   verification succeeds.
5. **Store the HMAC secret as a platform environment variable**
   (Render env var), never committed to the repo — the same pattern
   already used for `GITHUB_TOKEN` throughout MVP #1–#4.
6. **Log rejected/unsigned requests** (source IP, timestamp, reason)
   without ever logging the secret itself — gives visibility into
   misconfiguration or probing without creating a new leak surface.
7. **Return quickly** (2xx immediately after signature check +
   enqueue, not after the full GitHub-issue round trip) if VNETWORK's
   webhook delivery has any retry-on-timeout behavior — unconfirmed
   (§1), but a safe default regardless.

## 6. Reuse of the existing GitHub incident pipeline

No new pipeline logic — this is a new **front door**
(`to_alert()` mapper + HTTP receiver) onto the exact chain MVP #3/#4
already built and verified:

- `score_alert()`, `build_issue()`, `create_issue()`, `assign_issue()`
  — from `create_test_incident.py`, unchanged
- `find_open_issues()`, `find_duplicate()`, `with_tracking_block()`,
  `update_issue_body()` — the 24h GitHub-is-source-of-truth duplicate
  logic from `create_securitywatch_incident.py`, unchanged
- `compute_labels()`, `build_analysis_comment()`, `ENRICHMENT_RULES`
  — from MVP #4, extended with one new label (`vnetwork-healthcheck`)
  and one new `ENRICHMENT_RULES` entry (reason/recommendation text for
  a monitor-down alarm), following the exact same extension pattern
  used for the five security-watch.js rule types

The only genuinely new code is the HTTP receiver itself (route +
signature verification) and the `to_alert()` mapper in §2 — everything
downstream is a straight function call into what already exists and is
already proven with real GitHub issues (#5, #6).

## Explicitly not done in this pass

- No webhook receiver was built
- No domain, DNS record, or hosting service was touched
- No VNETWORK Monitor/Alarm/Channel was configured
- No test payload was captured
- No resources were provisioned, no credits spent
