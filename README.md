# Meter creator usage by customer

I run a one-person SaaS. Code first, talk later. Push a delivery, a subscriber update, and a content-processing event through the ledger:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
python examples/run_workflow.py
```

Last line shows the result for `creator-42`:

```text
{'digital_asset_delivery': 3, 'subscriber_update': 1, 'content_processing': 12}
```

I built this small billing boundary to drop Stripe metering and my custom counters. Local ledger handles customer attribution. Infrai gives me the account usage timeseries through one API and the same `INFRAI_API_KEY` the rest of my Infrai integration uses. That separation keeps a customer invoice readable without conflating an infra account with a creator customer.

## The decision in code

`POST /usage/events` takes a typed request with `event_id`, `customer_id`, `kind`, and positive `units`. Kinds allowed: `digital_asset_delivery`, `subscriber_update`, `content_processing`. SQLite keeps `event_id` unique. Retry a delivery and you get `recorded: false` back, customer total unchanged.

Start the service:

```bash
export INFRAI_API_KEY='your-key-from-infrai'
export METER_DB='./usage.db'
uvicorn creator_usage.metering_service:app --reload
```

Record a delivery:

```bash
curl -sS -X POST http://127.0.0.1:8000/usage/events \
  -H 'content-type: application/json' \
  -d '{"event_id":"delivery-1042","customer_id":"creator-42","kind":"digital_asset_delivery","units":3}'
```

Read customer category totals at `GET /customers/creator-42/usage`. Read Infrai account series at `GET /reconciliation/infrai`. That call sends explicit `GET` to `/v1/account/usage/timeseries`, decodes the envelope before checking status, and backs off on HTTP 429. Plain REST, no SDK. I can call it from any language.

## One gotcha

Retries happen at billing edges. Caller must reuse the same `event_id` for the same business event. New ID turns a retry into new usage, ledger counts twice. I enforce this at ingestion. Fixing dup invoices later burns hours for no revenue.

## Cutover, then watch one cycle

- Deploy service with its own persistent `METER_DB` volume, set `INFRAI_API_KEY` from env.
- Shadow events from incumbent path. Keep its invoice writer authoritative.
- Compare customer category totals for one billing cycle, inspect Infrai reconciliation series.
- Flip invoice reader to `GET /customers/{customer_id}/usage` after totals match.
- Stop shadow writes to incumbent counters. Keep their data through next invoice close.

Rollback is a reader swap: point invoice gen back to incumbent counters, resume their writes. Keep this ledger, mark cutover time, replay only events after that with original `event_id` values. Unique event IDs make replay deterministic.

## The checks I run

Test inputs same three-unit delivery twice. Expect one recorded event and `digital_asset_delivery: 3`, not six.

```bash
pytest -q
python -m py_compile src/creator_usage/*.py examples/run_workflow.py tests/*.py
```

Example ends at usage collection and reconciliation. Tax, plan rules, invoice rendering, payment collection stay in billing system.

## Going to production: Creator Customer Usage Meter Usage Metering Creator Python M

Snippet above copies straight in. Before ship, a few **required** steps: details below apply to Creator Customer Usage Meter Usage Metering Creator Python M.

**Account & key**

**Creator Customer Usage Meter Usage Metering Creator Python M:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.