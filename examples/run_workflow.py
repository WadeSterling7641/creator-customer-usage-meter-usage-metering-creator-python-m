from pathlib import Path
from tempfile import TemporaryDirectory

from creator_usage.usage_ledger import UsageEvent, UsageLedger


def main() -> None:
    with TemporaryDirectory() as directory:
        ledger = UsageLedger(Path(directory) / "usage.db")
        events = [
            UsageEvent("delivery-1042", "creator-42", "digital_asset_delivery", 3),
            UsageEvent("subscriber-208", "creator-42", "subscriber_update", 1),
            UsageEvent("render-91", "creator-42", "content_processing", 12),
        ]
        for event in events:
            result = ledger.record(event)
            print(result)
        print(ledger.totals("creator-42"))


if __name__ == "__main__":
    main()

