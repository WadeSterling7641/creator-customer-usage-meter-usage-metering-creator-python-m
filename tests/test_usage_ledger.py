from creator_usage.usage_ledger import UsageEvent, UsageLedger


def test_replayed_delivery_is_billed_once(tmp_path):
    ledger = UsageLedger(tmp_path / "usage.db")
    delivery = UsageEvent(
        event_id="delivery-1042",
        customer_id="creator-42",
        kind="digital_asset_delivery",
        units=3,
    )

    first = ledger.record(delivery)
    replay = ledger.record(delivery)

    assert first.recorded is True
    assert replay.recorded is False
    assert replay.total_units == 3
    assert ledger.totals("creator-42") == {
        "digital_asset_delivery": 3,
        "subscriber_update": 0,
        "content_processing": 0,
    }

