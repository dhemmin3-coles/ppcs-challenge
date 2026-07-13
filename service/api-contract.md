# PPCS API Contract

This is the canonical schema reference for the Promotional Pricing Compliance
Service. Before adding a new endpoint, new request field, or new response field,
read this document and keep it updated in the same PR.

The `/validate` endpoint is **stable**. Its request and response shape is
pinned by the contract tests in `tests/`. Do not change it without also updating
the tests and this document.

---

## Stable contract

### `POST /validate`

Validate one promotional price change against the current compliance rules.

**Request** (`application/json`)

```json
{
  "sku":       "<string, required>",
  "was_price": "<number, required, > 0>",
  "now_price": "<number, required, > 0>"
}
```

| Field       | Type   | Constraints       |
|-------------|--------|-------------------|
| `sku`       | string | non-empty         |
| `was_price` | number | > 0               |
| `now_price` | number | > 0, ≤ `was_price`|

**Response 200** (`application/json`)

```json
{
  "sku":              "<string>",
  "discount_pct":     "<number — whole percent, display only>",
  "was_now_compliant":"<bool>"
}
```

`discount_pct` is the rounded display value. Compliance decisions use the
unrounded markdown internally; do not use `discount_pct` as the threshold gate.

**Error responses**

| Status | Condition |
|--------|-----------|
| `422`  | Missing or wrong-type fields (FastAPI/Pydantic default) |

PPCS-004 adds explicit `400` rejections for invalid price relationships
(`was_price ≤ 0`, `now_price < 0`, `now_price > was_price`). Once that ticket
is implemented, document the error body shape here.

---

### `GET /`

Serves the PPCS workbench (`text/html`). No request parameters.

### `GET /static/app.js`, `GET /static/styles.css`

Static assets. No request parameters.

---

## Planned extensions

These fields and endpoints are added by backlog tickets. The shape is not yet
implemented — do not invent a conflicting shape before the relevant ticket is
dispatched.

### `/validate` response — `failures` array (PPCS-024, PPCS-040)

When a promo fails one or more rules, the response may include a `failures`
array of structured reason objects:

```json
{
  "sku": "SKU-1",
  "discount_pct": 5,
  "was_now_compliant": false,
  "failures": [
    { "rule_id": "was_now", "reason_code": "discount_below_threshold" }
  ]
}
```

Rules:
- `failures` is present **only** when at least one rule fails; omit it for
  passing promos.
- `rule_id` is a stable machine-readable identifier, not prose.
- `reason_code` is a stable machine-readable code; human-readable text is
  optional and separate.
- The existing `was_now_compliant` field must remain unchanged.

### `/validate` request — duration fields (PPCS-006) — IMPLEMENTED

```json
{
  "sku":        "SKU-1",
  "was_price":  10.00,
  "now_price":  9.00,
  "start_date": "2026-07-13",
  "end_date":   "2026-07-20"
}
```

`start_date` and `end_date` are optional ISO-8601 dates. When absent, the
duration rule is not evaluated and the response shape is unchanged (no
`duration_compliant` key). When **both** are present, a promo must span at
least 7 calendar days, counted **inclusively** of both endpoints, to pass the
duration rule; the response then adds a `duration_compliant` boolean alongside
`was_now_compliant`.

Duration counting is inclusive: `days = (end_date - start_date).days + 1`. So
`2026-07-13 .. 2026-07-19` is 7 days (compliant) and `2026-07-13 .. 2026-07-18`
is 6 days (non-compliant). The two rules are independent — a promo can pass
was/now and fail duration, or fail both.

A promo window must be well-formed. The endpoint rejects these with `400`
(mirroring PPCS-004's price-relationship rejections) rather than silently
skipping the rule or coercing a nonsensical window to non-compliant:

| Status | Condition |
|--------|-----------|
| `400`  | Only one of `start_date` / `end_date` supplied (half-specified window) |
| `400`  | `end_date` is before `start_date` (inverted window) |

`start_date == end_date` is a valid one-day window (returns `200`,
`duration_compliant: false`). A malformed date string is a `422` (Pydantic).

### `/validate` request — multi-buy fields (PPCS-010)

```json
{
  "sku":          "SKU-1",
  "was_price":    10.00,
  "now_price":    9.00,
  "multibuy_qty": 3,
  "bundle_price": 10.00
}
```

`multibuy_qty` and `bundle_price` are optional. When present, the response adds
`effective_unit_price` (number, currency-rounded). Invalid quantity or bundle
price is rejected with a `400`.

### `/validate` request — member pricing fields (PPCS-009)

```json
{
  "sku":          "SKU-1",
  "was_price":    10.00,
  "now_price":    9.00,
  "member_only":  true,
  "display_channel": "public"
}
```

`member_only` and `display_channel` are optional. When `member_only=true` and
`display_channel` indicates a general public context, the promo is
non-compliant for the member pricing rule. The response adds
`member_price_compliant`.

### `/validate` response — `was_price_verified` field (PPCS-056)

When the service can look up the SKU in the team's price history, the response
includes a verification flag:

```json
{
  "sku":               "SKU-1",
  "discount_pct":      5,
  "was_now_compliant": false,
  "was_price_verified": true
}
```

Rules:
- `was_price_verified: true` — the supplied `was_price` matches a recorded
  price for this SKU within the agreed tolerance.
- `was_price_verified: false` — either no price history exists for the SKU, or
  the supplied price does not match the record.
- A `false` value does **not** change `was_now_compliant`. Verification failure
  is informational; it does not make a passing promo fail.
- The tolerance and lookup strategy must be documented in the PR.

### Rule threshold source (PPCS-055)

After PPCS-055 is accepted, the `min_discount_pct` and `min_days` thresholds
are read from `ppcs_rule_config` in Lakebase rather than from hardcoded
constants. The API contract does not change. The implementation must:
- Keep the rule logic injectable/testable without a live database.
- Document the fallback behaviour if the config row is missing.

### `GET /violations`

Returns recent non-compliant validations from the app's local state.

**Response 200** (`application/json`)

```json
[
  {
    "sku":       "<string>",
    "rule_ids":  ["<string>", ...],
    "reason":    "<string, human-readable>",
    "timestamp": "<ISO-8601 datetime>"
  }
]
```

Rules:
- Returns only non-compliant validations; compliant promos are excluded.
- Empty list `[]` when there are no violations.
- Must be testable without live Lakebase credentials; use a local repository
  abstraction or in-memory fixture.
- The existing `app.js` reads `violation.sku` and `violation.reason` — do not
  rename those fields.

### `POST /validate/batch` (PPCS-029, PPCS-046)

Accepts multiple promos in one request and returns per-promo results. One
malformed or non-compliant row does not suppress results for the rest.

Shape is not yet pinned. Propose it in the ticket brief before implementing.

---

## Constraints that apply to all endpoints

- **Return type must be a Pydantic model or a typed dict**, not a bare `dict`,
  so FastAPI generates a schema in `/docs`.
- **Do not log request payloads** (sku, prices, member fields) into OTel spans,
  application logs, or trace metadata. Log only event id, rule id, and redacted
  reason code.
- **Do not add outbound HTTP calls** to external URLs from any endpoint
  handler. Governed egress through an approved MCP tool is the approved path.
- **Preserve the existing `/validate` field names** when adding new fields.
  Agents working on later tickets must not rename `was_now_compliant`,
  `discount_pct`, or `sku`.
- **Platform diagnostic endpoints** (`/platform/uc-check`,
  `/platform/lakebase-check`) are facilitator/ops tooling. Do not add business
  logic to them and do not depend on them in tests.

---

## How to use this document

**Before dispatching an agent on any ticket that touches the API or data
model**, add to your brief:

```
Context:
- Approved schema reference: service/api-contract.md
- Stable contract must not change: POST /validate request/response shape
- Relevant extension section: <paste the relevant "Planned extensions" block>
```

**After the agent opens a draft PR**, check:
- Does the PR update this document if a new field or endpoint was added?
- Are the new field names consistent with the shapes described here?
- Does the existing contract test (`tests/test_api_contract.py`) still pass without modification?
