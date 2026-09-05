# WAAP Log Search — API Schema, Auth, Payloads, MCP Integration Plan

Follow-up to `docs/VNETWORK_API_DISCOVERY.md` (which catalogued `POST
/v1/bsearch` at the field-name level: `http_x_forwarded_for`,
`uri.keyword`, `http_user_agent`, `status`, etc.) and
`docs/VNETWORK_PRODUCT_DISCOVERY.md` / `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`
(which ranked it the #1 SentinelOps opportunity). This pass goes one
level deeper — full request/response schema, verbatim example
payloads, and an MCP integration design — to close out **NEXT Steps
#1: WAAP Log Search Integration**.

**Original pass (§1–§6): documentation-only.** No VNETWORK API endpoint
was called, no resources provisioned, no credits spent. The only
network request made was to Postman's own documentation data API
(`documenter.gw.postman.com`, the same source as the prior two
passes) to pull the raw collection JSON and read the `Bsearch Aggs`
item in full — including its request template, its field-reference
table, and its two saved example responses. Nothing here was inferred
or invented; every field, example, and quote below is copied from that
one item in the published collection.

**§7 is a later, separate pass: one real, read-only, credential-bearing
verification against `openapi.vnetwork.vn` itself** — the first actual
call to the live API anywhere in this project's VNETWORK research.
Result: the token authenticates, but this account currently has no
authorized access to WAAP, CDN, or Compute from here, so **the 5 fields
below remain doc-sourced, not live-verified** — read §7 before treating
anything in §1 as "confirmed against real data." Full detail, all
request/response bodies, in §7.

## 1. Does it cover the 5 requested fields?

| Requested | Field(s) | Status |
|---|---|---|
| Source IP | `http_x_forwarded_for` | CONFIRMED (docs table): "Remote IP Address". **Not yet live-verified — see §7.** |
| URI | `uri.keyword` | CONFIRMED (docs table): "Request URI in logs". **Not yet live-verified — see §7.** |
| Status code | `status` (edge/WAF response) and `upstream_status` (origin response) | CONFIRMED (docs table) — both are separate, queryable fields. **Not yet live-verified — see §7.** |
| User agent | `http_user_agent` | CONFIRMED (docs table): "Request with header User-Agent". **Not yet live-verified — see §7.** |
| Attack indicators | `mitigation_result` (and a second, textually distinct `mitigate_result`) | CONFIRMED TO EXIST, but **not documented in the endpoint's prose field table** — see §4 below for why and what's still unknown. **Not yet live-verified — see §7.** |

Two bonus fields also confirmed in the docs table: `http_referer`
(Referer header) and `upstream_addr` (origin IP), plus
`upstream_response_time` (origin TTFB). The docs table ends with an
explicit "..." row: *"and another keys you can extract from raw logs
response with payload **raw: true**"* — i.e. the documented field list
is a curated subset, not the full schema. The complete field set is
only discoverable by making one live `raw: true` call, which this pass
did not do (documentation-only).

## 2. Authentication

- **Scheme:** Bearer token, inherited from the collection root (this
  endpoint's own `auth` block has `"isInherited": true`, sourced from
  the `VNETWORK OpenAPI` collection):
  ```
  Authorization: Bearer {{OPENAPI_TOKEN}}
  ```
- **Base URL:** `https://openapi.vnetwork.vn`
- **Full endpoint:** `POST https://openapi.vnetwork.vn/v1/bsearch`
- No separate API-key header scheme, no per-endpoint auth override —
  same single Bearer token as every other endpoint catalogued in
  `docs/VNETWORK_API_DISCOVERY.md`.
- **New nuance this pass:** the account-wide-key finding from
  `docs/VNETWORK_CAPABILITY_ASSESSMENT.md` ("a single leaked key
  compromises every product") still holds, but the saved 401 example
  below shows there **is** a server-side authorization boundary
  specific to this endpoint: it rejects domains the account doesn't
  own, independent of whether the Bearer token itself is valid. That
  narrows — but does not eliminate — the blast radius of a leaked key
  for this specific endpoint (still full access to every domain the
  account *does* own).

## 3. Request schema

Reconstructed directly from the endpoint's request-body template
comments and its own field-reference table (both quoted verbatim
below). **One real discrepancy exists between the two sources** —
flagged, not resolved, since resolving it needs a live test call:

| Field | Docs table says | Request template comment says | Verdict |
|---|---|---|---|
| `domains` | **Mandatory**, `String[]` | *"Supports fetching all domains as the standard behavior. However, if you provide a list of specific domains, these will be used for the query instead."* (i.e. optional, defaults to all authorized domains) | **Unresolved contradiction.** Docs table and template disagree. Must send `domains` explicitly until verified live. |
| `must_not` | Not in the docs table at all | Present, commented-out, in the template (`match`-style exclusion, e.g. excluding `mitigation_result.keyword: "ACL-WHITE"`) | Real, usable field per the template author, just undocumented in prose. |

Top-level request body:

| Field | Required (per docs table) | Type | Notes |
|---|---|---|---|
| `gte` | Optional | Datetime, format `YYYY-MM-DDThh:mm:ssZ` | Default: `now - 1h`. Template also accepts relative strings like `"now-1h"`. |
| `lte` | Optional | Datetime, same format | Default: `now` |
| `raw` | Optional | Boolean | Default: `false`. Set `true` to get raw log rows instead of aggregated buckets — this is also how additional, undocumented fields become visible. |
| `domains` | Mandatory (docs) / apparently optional (template) — see contradiction above | `String[]` | e.g. `["domain.com"]` |
| `query` | Mandatory | `Query` object | See below |

`query` object:

| Field | Required | Type | Notes |
|---|---|---|---|
| `aggs` | Mandatory | object of named `Term`/`date_histogram` specs | Key = your chosen label for the aggregation (e.g. `"uri"`, `"logs"`, `"mitigation"`). Aggregations can nest (a `terms` agg can contain its own `aggs` for a sub-breakdown, as shown in the template's `mitigation` → `domain` example). |
| `filters` | Mandatory | `Filter[]` | See below |
| `must_not` | Not in docs table; present in template | array of term-exclusion objects | Undocumented — exists in the template as `{ "term": { "<field>.keyword": "<value>" } }` |

`Term` (an aggregation spec):

| Field | Required | Type | Notes |
|---|---|---|---|
| `field` | Mandatory | Key (one of the field-table names, `.keyword` suffix for exact/terms aggs) | |
| `order` | Optional | `Order` (`{"_count": "desc"\|"asc"}`) | |
| `size` | Optional | Integer | Caps bucket count for a `terms` agg. The `gte`/`lte` comment separately notes a **hard maximum of 500 buckets** — for a higher record count you're told to shrink `date_histogram`'s `fixed_interval` instead of raising `size`. |

Also seen in the template (not in the prose table, but a standard
Elasticsearch-style spec): `date_histogram` — `{"field":
"@timestamp", "fixed_interval": "1m", "time_zone": "Asia/Saigon",
"min_doc_count": 1}` — this is how you'd bucket by time instead of by
a terms field (e.g. for "requests per minute" style thresholding).

`Filter` (an entry in the `filters` array):

| Variant | Required sub-fields | Purpose |
|---|---|---|
| `query_string` | `fields: Key[]`, `query: String` | Regex-style pattern match, e.g. `fields: ["uri.keyword"], query: "\\/api*"` to match all URIs starting with `/api` |
| `match_phrase` | `key: String` → value (exact match) | Exact match, e.g. `{"status": 403}` or `{"upstream_status": 0}` |

Documented field names (the `Key` table, verbatim) — these are the
fields legal inside `aggs.field`, `query_string.fields`, and
`match_phrase`:

- `uri.keyword` — Request URI in logs
- `http_user_agent` — Request with header User-Agent
- `http_x_forwarded_for` — Remote IP Address
- `http_referer` — Request with header Referer
- `status` — Response HTTP Status code
- `upstream_status` — Upstream (Origin) HTTP Status Code
- `upstream_addr` — Upstream (Origin) IP Address
- `upstream_response_time` — Upstream TTFB (includes content download time from origin to WAF)
- *(and other keys, extractable from raw log rows with `raw: true` — not enumerated in the docs)*

## 4. Attack-indicator field — what's confirmed and what isn't

The docs table (§3 above) does **not** list a mitigation/attack-result
field. But the request template — the same JSON block a user pastes
into Postman to build a request — has two commented-out examples that
use one:

```jsonc
// aggregation example:
"mitigation": {
    "terms": { "field": "mitigation_result.keyword" },
    "aggs": {
        "domain": { "terms": { "field": "request_host.keyword", "size": 10 } }
    }
}

// exclusion example:
"must_not": [
    { "term": { "mitigate_result.keyword": "" } },
    { "term": { "mitigation_result.keyword": "ACL-WHITE" } }
]
```

Findings:

- **`mitigation_result`** is a real, aggregatable/filterable keyword
  field — this is the closest thing to an "attack indicator" the API
  exposes. One concrete value is confirmed: `"ACL-WHITE"` (used in the
  example as something to *exclude*, implying it means
  allow-listed/benign traffic — everything else in this field is
  presumably a mitigation action VNETWORK's WAF/bot-management/edge
  layer took, e.g. block, challenge, rate-limit — **but no other value
  is documented anywhere**, so this is inference, not a confirmed
  enum).
- **`request_host`** is also confirmed usable (seen in the nested
  `domain` sub-aggregation) — useful for a multi-domain deployment to
  break results down per site.
- **`mitigate_result`** appears once, textually distinct from
  `mitigation_result` (missing the `-ion`). Could be: (a) a second,
  genuinely different field, (b) a typo of `mitigation_result` in the
  template's own example, or (c) a deprecated/aliased name. **Not
  resolvable from documentation alone** — needs one live `raw: true`
  test call to see which field name(s) actually appear on real log
  rows.
- No dedicated "attack type," "rule ID," "CVE," "bot score," or
  "threat category" field is documented or hinted at anywhere in this
  item. If VNETWORK's AI-WAF/Bot Management/API Protection modules
  produce that kind of classification, it isn't exposed through this
  endpoint's documented or template-hinted surface.

**Bottom line:** attack-indicator signal exists (`mitigation_result`,
possibly `mitigate_result`), but its value set is unconfirmed beyond
one benign marker. This is a real gap for the "alert-worthy" threshold
decision `NEXT_STEPS.md` already flags as open — that decision now has
one more concrete option (`mitigation_result` != `"ACL-WHITE"` /
non-empty, i.e. "WAF took mitigating action") in addition to the
4xx/5xx-rate and `query_string`-pattern options already noted there,
but confirming what values `mitigation_result` actually takes requires
a real call, which this discovery pass deliberately did not make.

## 5. Sample payloads (verbatim from the collection)

### Request — annotated template (as shipped in the collection; comments are the collection author's, not this pass's)

```jsonc
{
    "gte": "now-1h", // Datetime default: Time.now - 1.hours
    "lte": "now", // Datetime default: Time.now
    "raw": false, // Boolean default: false
    // Supports fetching all domains as the standard behavior. However,
    // if you provide a list of specific domains, these will be used for the query instead.
    // "domains": [],
    "query": { // KQL bool queries are natively supported.
        // "size": 500, // For a higher record count, adjust the fixed_interval to a smaller value. Keep in mind the maximum bucket limit of 500.
        // "sort": [ { "@timestamp": { "order": "desc", "unmapped_type": "boolean" } } ],
        "aggs": {
            "logs": {
                "date_histogram": {
                    "field": "@timestamp",
                    "fixed_interval": "1m",
                    "time_zone": "Asia/Saigon",
                    "min_doc_count": 1
                }
            }
            // "mitigation": {
            //     "terms": { "field": "mitigation_result.keyword" },
            //     "aggs": { "domain": { "terms": { "field": "request_host.keyword", "size": 10 } } }
            // }
        },
        "filters": [
            // { "query_string": { "fields": ["uri.keyword"], "query": "*" } },
            // { "query_string": { "fields": ["uri.keyword"], "query": "\\/api*" } },
            // { "match_phrase": { "uri.keyword": "/api/path/to/filter" } },
            // { "match_phrase": { "status": 403 } },
            // { "match_phrase": { "upstream_status": 0 } }
        ]
        // "must_not": [
        //     { "term": { "mitigate_result.keyword": "" } },
        //     { "term": { "mitigation_result.keyword": "ACL-WHITE" } }
        // ]
    }
}
```

### Request — the collection's own saved example (used for both saved responses below)

```json
{
    "domains": ["domain.com"],
    "query": {
        "aggs": {
            "uri": { "terms": { "field": "uri.keyword" } }
        },
        "filters": [
            { "query_string": { "fields": ["uri.keyword"], "query": "\\/api*" } }
        ]
    }
}
```

### Response — 200 OK (saved example, "Response Success")

```json
{
    "status": 200,
    "data": {
        "result": {
            "uri": {
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 16,
                "buckets": [
                    { "key": "/api/resources", "doc_count": 1943 },
                    { "key": "/api/assets", "doc_count": 1818 }
                ]
            }
        }
    }
}
```

Shape notes:
- `data.result.<aggName>` mirrors whatever key you chose in
  `query.aggs` (here, `"uri"`).
- This is a standard Elasticsearch `terms` aggregation envelope
  (`doc_count_error_upper_bound`, `sum_other_doc_count`, `buckets[]`
  with `key`/`doc_count`) — consistent with VNETWORK's log backend
  being Elasticsearch, as the request template's own "KQL bool
  queries are natively supported" comment implies.
- **Not captured in the collection, and therefore not documented
  here:** what a `date_histogram` aggregation's response looks like,
  what a nested aggregation's response looks like (the `mitigation` →
  `domain` example), and what a `raw: true` response looks like (raw
  log rows). Only the single `terms`-on-`uri.keyword` shape was saved
  as an example. All three would need a live test call to confirm.

### Response — 401 Unauthorized (saved example, "Response Invalid Domain(s)")

```json
{
    "status": 401,
    "errors": [
        {
            "message": "Request.Unauthorized: Can't executive domain(s) not belong to your Elastic.LogComposer.",
            "code": 401,
            "request_id": "4d9ba139-1a24-4d45-b5c9-b5469a46a527"
        }
    ]
}
```

Note the (source's) grammar — `"executive"` — quoted exactly as
published; this is VNETWORK's own error string, not a transcription
error in this doc. This example is saved against the *same* request
body as the 200 example above (`domains: ["domain.com"]`), meaning it
is a template placeholder value in the collection, not proof that a
literal `domain.com` is rejected for every account — the 401 fires
when the caller's account isn't provisioned for the requested domain,
confirming the domain-level authorization boundary noted in §2.

## 6. MCP integration plan (design only — nothing below is implemented)

Same reuse pattern as MVP #3/#4 and the MVP #5 webhook-receiver plan:
one new mapper feeding the existing, unchanged incident pipeline
(`score_alert` → `build_issue` → `create_issue` → `assign_issue` →
`compute_labels` → `build_analysis_comment` → 24h duplicate detection).

**New MCP tool (read-only):** `vnetworkWaapSearch` — matches the tool
name already sketched in `docs/VNETWORK_API_DISCOVERY.md`'s
integration-opportunities section, and the naming/shape of this repo's
existing `modules/*.js` tools (e.g. `defenderThreats`).

- **Inputs:** `domains: string[]` (send explicitly — see §3's
  documented-vs-optional contradiction), `gte`/`lte` (default to a
  rolling window matching the polling cadence, e.g. `now-5m`/`now`),
  a `filters` passthrough (so callers can use `query_string` or
  `match_phrase` per the schema above), and an `aggs` passthrough
  (terms on `status`, `mitigation_result`, `uri.keyword`, or
  `http_x_forwarded_for`; or `date_histogram` for a request-rate time
  series).
- **Auth:** same pattern as every existing script in `scripts/`
  (`os.environ.get("GITHUB_TOKEN")` today) — a new
  `VNETWORK_OPENAPI_TOKEN` environment variable, never committed,
  with the same "missing token → clear error + how to set it" guard
  those scripts already use.
- **New script:** `scripts/create_waap_incident.py`, following
  `create_securitywatch_incident.py`'s structure exactly: a
  `to_alert()` mapper turning a `bsearch` result bucket into the
  existing alert schema (`source`, `event_type`, `severity`, evidence
  fields), reusing `score_alert`, `build_issue`, `create_issue`,
  `assign_issue`, `ASSIGNEE`, `github_request`, `REPO_OWNER`,
  `REPO_NAME`, `compute_labels`, `build_analysis_comment`, and the
  24h duplicate-detection logic **unchanged**.
- **Polling shape:** same Task Scheduler pattern as
  `HOME-SOC-Scan-And-Export` / `security-watch.js` — a scheduled run
  every N minutes, `gte`/`lte` set to that window, comparing against a
  local high-water-mark/state file (same JSON-state-diff pattern as
  `security-watch.js`'s `baseline.json`) so the same window isn't
  re-scored twice.
- **New label:** `waap`, added to `compute_labels()`'s existing
  vocabulary (alongside `critical`/`high`/`defender`/`control-drift`/
  `firewall`).
- **New `ENRICHMENT_RULES` entry:** one new alert type (e.g.
  `WAAP_ANOMALY`), following the existing 5-entry table's
  Risk/Reason/Recommendation shape.

**Still blocking before this can be built (carried over from
`NEXT_STEPS.md`, sharpened by this pass — these are decisions for
Kevin, not discovery gaps):**

1. The alert-worthy threshold/query — now has three concrete candidate
   shapes instead of two: (a) a `status`/`upstream_status` terms agg
   thresholded on 4xx/5xx rate, (b) a `query_string` match against a
   known-bad URI pattern, or (c) `mitigation_result` being non-empty /
   not `"ACL-WHITE"` — but (c) can't be trusted until a live call shows
   what other values that field actually takes.
2. The `domains` list to query — required per the docs table; this
   repo has no captured inventory of which domain(s) are actually
   provisioned under this VNETWORK account (that's what
   `GET /v3/cdn/domains`, already catalogued as HIGH-ROI, would supply
   — itself not yet called).
3. The `mitigation_result` vs `mitigate_result` field-name ambiguity
   (§4) and the undocumented response shapes for `date_histogram` and
   `raw: true` (§5) both need one real test call each to resolve — the
   smallest possible "spend one real query" step, deliberately not
   taken in this documentation-only pass.

## 7. Live verification pass (2026-09-04, later same day)

Unlike §1–§6, this section reports **real calls made against
`https://openapi.vnetwork.vn`** with a live Bearer token, at the
user's explicit request, before implementation. Read-only calls only
(`GET`/`POST /v1/bsearch`, which is a query, not a write) — no
mutating endpoint was called, no resource was created/changed/deleted.

**Credential handling note (process, not a technical finding):** the
first token used in this pass was accidentally pasted into the chat
transcript while getting it into a shell my tooling could read from.
It was treated as compromised immediately, the user rotated it in the
VNETWORK console, and all calls below were re-run against the new
token before being trusted. Every call in this section (and its
predecessor) reads the token from a local file
(`C:\Users\tamng\vnetwork_token.txt`, outside the repo, never
committed, never printed by any script) rather than an inline value,
specifically to avoid repeating that mistake.

### 7.1 Attempt: determine exact domains via `GET /v3/cdn/domains`

```
GET https://openapi.vnetwork.vn/v3/cdn/domains
Authorization: Bearer <token>
```

Result: `404`

```json
{"status":404,"errors":[{"message":"Service.NotFound","code":404,"request_id":"..."}]}
```

**New finding, root-caused, not just observed:** re-checked this
endpoint's exact entry in the raw Postman collection JSON. Of all 106
endpoints, **103 hardcode the literal host `openapi.vnetwork.vn`** in
their URL — but the 3 endpoints under "Content Delivery Network >
Domains" (`List` = this one, `Prefetch`, `Purge Cache`) use an
unresolved Postman template variable instead:

```
{{URL}}/v3/cdn/domains
{{URL}}/v3/cdn/domains/:id/prefetch
{{URL}}/v3/cdn/domains/:id/purge
```

`{{URL}}` is not defined anywhere in the exported collection (no
collection-level `variable` array, `data.variable` is `undefined`) —
it only exists in whatever private Postman environment VNETWORK's own
docs team uses, and isn't published. This call assumed `{{URL}}` ==
`openapi.vnetwork.vn` (the same host as everything else) since that's
the only reasonable guess — the `404 Service.NotFound` may mean that
guess is wrong, or it may mean the host guess was right but this
account/token isn't entitled to the CDN product. Not distinguishable
from outside without VNETWORK's real environment file. **This is a
genuine, previously-undocumented gap in the published collection**,
not an error in this project's work.

### 7.2 Diagnostic: is the token valid at all?

To separate "bad token" from "bad domain/entitlement," tested a
well-formed, always-hardcoded-host endpoint outside WAAP/CDN:

```
GET https://openapi.vnetwork.vn/v3/instances
Authorization: Bearer <token>
```

Result: `403`

```json
{"status":403,"errors":[{"message":"Service.AccessDenied","code":403,"request_id":"..."}]}
```

A `403 Service.AccessDenied` (not `401`) on a basic, correctly-routed
endpoint is meaningful: the token authenticates (a truly invalid/
expired token would be expected to fail the same way everywhere,
typically `401`), but this specific account isn't entitled to the
Compute product. **Reproduced identically after the token rotation**
(see below) — ruling out "the first token was simply bad" as the
explanation.

### 7.3 Attempt: `bsearch` against `audit.sentinelops.fyi`

```
POST https://openapi.vnetwork.vn/v1/bsearch
Authorization: Bearer <token>
Content-Type: application/json

{
  "gte": "now-24h",
  "lte": "now",
  "domains": ["audit.sentinelops.fyi"],
  "query": {
    "aggs": {
      "source_ip": {"terms": {"field": "http_x_forwarded_for", "size": 5}},
      "uri": {"terms": {"field": "uri.keyword", "size": 5}},
      "status_code": {"terms": {"field": "status", "size": 5}},
      "user_agent": {"terms": {"field": "http_user_agent", "size": 5}},
      "mitigation_result": {"terms": {"field": "mitigation_result.keyword", "size": 5}}
    },
    "filters": []
  }
}
```

Result (original token): `401`

```json
{"status":401,"errors":[{"message":"Request.Unauthorized","code":401,"request_id":"..."}]}
```

Note this is a **plainer** 401 than the one saved in the collection's
own example (§5 above), which included a detailed message ("Can't
executive domain(s) not belong to your Elastic.LogComposer."). Same
status code, less detail — consistent with a real backend giving a
generic error for one rejection class and a more specific one for
another, but not something this pass can fully distinguish from
outside.

**Re-ran after the token rotation** (new token, old one revoked in the
VNETWORK console) — identical result:

```json
{"status":401,"errors":[{"message":"Request.Unauthorized","code":401,"request_id":"..."}]}
```

**Re-ran a third time with `domains` omitted entirely**, to test the
request template's own claim (§3) that it's optional and defaults to
"all authorized domains":

```json
{"status":401,"errors":[{"message":"Request.Unauthorized","code":401,"request_id":"..."}]}
```

Identical `401` whether `domains` is `["audit.sentinelops.fyi"]` or
omitted. This doesn't cleanly resolve the mandatory-vs-optional
contradiction at the API-contract level (both shapes were *accepted*
as well-formed requests — neither produced a validation/malformed-body
error — so the contradiction may be real and simply moot for an
account with zero authorized domains either way), but it does add a
third independent confirmation of the same underlying fact: **this
account currently has no WAAP-authorized domain reachable via this
token**, tested three ways (explicit domain, no domain, and — via
§7.2 — a completely different product).

### 7.4 What this run *does* and *doesn't* verify

**Verified (positive findings, not assumptions):**
- The token is live and authenticates (403/401/404 with structured,
  service-specific error bodies — not a raw connection failure or a
  uniform "invalid credentials" response).
- The **request schema documented in §3 is well-formed enough to be
  accepted for authorization evaluation** — none of the three
  `bsearch` calls above were rejected as a malformed/invalid request
  body (no `400`, no schema-validation error). That's indirect but
  real evidence the request shape captured from the Postman template
  is correct, even though no `200` was obtained.
- The **error-response envelope** (`{"status": <code>, "errors":
  [{"message", "code", "request_id"}]}`) matches, structurally, the
  collection's own saved 401 example in §5 — confirmed live, not just
  from the saved Postman example, across all four calls in this
  section (404, 403, 401×3).
- The `{{URL}}`-variable gap on the 3 CDN-domains endpoints (§7.1) is
  a newly confirmed, real gap in the published collection.

**Not verified — still open, and this is the actual headline result
of this pass:**
- **None of the 5 requested fields** (source IP, URI, status code,
  user agent, mitigation result) were observed in a real `200`
  response. Every claim about them in §1–§4 remains doc-sourced
  (the endpoint's own field table and request-template comments),
  not confirmed against live data.
- Whether `audit.sentinelops.fyi` is even the right domain for this
  account's WAAP product is still unknown — the `401` is consistent
  with "wrong domain name," "right domain, not yet onboarded to WAAP,"
  or "this token/account has no WAAP product at all," and this pass
  cannot distinguish between those three from outside.
- The `date_histogram` and `raw: true` response shapes (flagged
  undocumented in §5) remain unverified — never reached, since no call
  in this pass got past authorization.
- The `mitigation_result` vs `mitigate_result` naming question (§4)
  remains unresolved for the same reason.

**Bottom line:** this pass is a real, honest verification attempt, not
a rubber stamp — and its honest result is "the schema is well-formed
and the token is live, but this account currently has no reachable
WAAP/CDN/Compute data to verify field-level claims against." That's a
legitimate, useful finding on its own (it surfaces a real blocker
before implementation), it just isn't the field-confirmation the task
asked for. Continuing this verification needs one of: the correct
onboarded domain name, a different token scoped to a provisioned
account, or accepting the doc-sourced schema as sufficient to start
building against (with the threshold/`domains` decisions in §6 still
open regardless).

**Root cause identified — see `PROJECT_STATUS.md` "WAAP Log Search —
Root Cause Identified" for full detail:** Kevin checked the Partner
Portal directly; WAAP's own onboarding flow (Step 2: Domain & Origin)
showed no Website Domain and no Origin Server configured at the time
of the original verification pass above. Not independently re-verified
by this session at the time (no portal access here) — reported as
Kevin's direct observation.

## 8. Post-onboarding re-verification (2026-09-04, later same day)

Kevin completed WAAP onboarding — **Website: `www.sentinelops.fyi`,
Service ID: `95743`**. Per instruction, this section re-runs the exact
same 3 read-only checks from §7 (same token file, same endpoints, same
request bodies except the domain), to check whether onboarding changed
API accessibility, WAAP log search access, or analytics availability.
Documentation only — no integration code touched.

| Check | Before onboarding (§7) | After onboarding (this pass) | Changed? |
|---|---|---|---|
| `GET /v3/instances` (Compute) | `403 Service.AccessDenied` | `403 Service.AccessDenied` | **No** |
| `GET /v3/cdn/domains` (CDN) | `404 Service.NotFound` | `404 Service.NotFound` | **No** |
| `POST /v1/bsearch` (WAAP log search / analytics, `domains: ["www.sentinelops.fyi"]`) | `401 Request.Unauthorized` (tested against `audit.sentinelops.fyi`) | `401 Request.Unauthorized` (same request shape, correct onboarded domain this time) | **No** |

Full `bsearch` response, byte-for-byte:

```json
{"status":401,"errors":[{"message":"Request.Unauthorized","code":401,"request_id":"d889685c95908484ec099ce69fd6d2b4"}]}
```

**Finding: onboarding, as observed in the portal, has not yet changed
API-level access for this token, for any of the three checks.**
Analytics availability was not separately testable — per the product
discovery in `docs/VNETWORK_PRODUCT_DISCOVERY.md`, `bsearch` *is* the
API surface behind WAAP's console "Analytics"/"Logs" tabs (no separate
analytics endpoint exists), so the same `401` covers both "WAAP log
search access" and "analytics availability" — they did not diverge.

**Plausible explanations — none confirmed, no further live testing
was performed to distinguish them (documentation only, per
instruction):**
1. **Propagation delay.** Portal-side onboarding may take time (minutes
   to hours) to propagate into the API-facing `Elastic.LogComposer`
   index that `bsearch` checks against.
2. **Onboarding may be incomplete beyond Step 2.** "Domain & Origin"
   being filled in doesn't necessarily mean the WAAP onboarding wizard
   is fully finished (e.g. SSL/cert provisioning, DNS validation, or a
   final "go live"/"activate" step could remain) — this session has no
   portal visibility to check remaining steps.
3. **Domain-string mismatch.** The API was queried with exactly
   `www.sentinelops.fyi` per the value given; if the portal registered
   a different exact string (e.g. the apex `sentinelops.fyi`, or a
   different casing/format), `bsearch`'s domain-ownership check could
   still reject it.
4. **Account/key scope mismatch.** The onboarding action and this API
   token may not belong to the same VNETWORK account/sub-account —
   consistent with Compute and CDN also remaining unchanged, which
   onboarding a WAAP site alone would not be expected to fix anyway,
   but is a data point toward a broader scope question.

**Bottom line:** the root cause identified in `PROJECT_STATUS.md`
("no WAAP site onboarded") may have been correct as of that check, but
the fix applied since then has **not yet resolved API-level access**
as of this re-verification. This is a new, distinct finding from the
original root cause, not a re-confirmation of it.

## Explicitly not done in this pass

- No VNETWORK API endpoint was called in §1–§6 (Postman's own
  documentation data API only — same source, same method as the prior
  two discovery passes)
- §7's live calls were all read-only (`GET`, or `POST /v1/bsearch`
  which only queries, never writes); no mutating endpoint was called,
  no resource was created, changed, or deleted
- No decision was made on the alert-worthy threshold, the domains
  list, or the `mitigation_result` value enum — all three are flagged
  above as open, not resolved, and §7 did not resolve them either
- No integration code was written — `scripts/create_waap_incident.py`
  and the `vnetworkWaapSearch` MCP tool in §6 remain a plan, not code
