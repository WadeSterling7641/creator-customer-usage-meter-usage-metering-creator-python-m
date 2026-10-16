from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

UsageKind = Literal[
    "digital_asset_delivery",
    "subscriber_update",
    "content_processing",
]


@dataclass(frozen=True)
class UsageEvent:
    event_id: str
    customer_id: str
    kind: UsageKind
    units: int


@dataclass(frozen=True)
class MeterResult:
    event_id: str
    customer_id: str
    recorded: bool
    total_units: int


class UsageLedger:
    def __init__(self, database_path: str | Path) -> None:
        self._database_path = str(database_path)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    units INTEGER NOT NULL CHECK (units > 0),
                    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def record(self, event: UsageEvent) -> MeterResult:
        if event.units <= 0:
            raise ValueError("units must be greater than zero")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO usage_events
                    (event_id, customer_id, kind, units)
                VALUES (?, ?, ?, ?)
                """,
                (event.event_id, event.customer_id, event.kind, event.units),
            )
            recorded = cursor.rowcount == 1
            total_units = connection.execute(
                """
                SELECT COALESCE(SUM(units), 0) AS total
                FROM usage_events
                WHERE customer_id = ?
                """,
                (event.customer_id,),
            ).fetchone()["total"]

        return MeterResult(
            event_id=event.event_id,
            customer_id=event.customer_id,
            recorded=recorded,
            total_units=total_units,
        )

    def totals(self, customer_id: str) -> dict[str, int]:
        totals = {
            "digital_asset_delivery": 0,
            "subscriber_update": 0,
            "content_processing": 0,
        }
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT kind, SUM(units) AS units
                FROM usage_events
                WHERE customer_id = ?
                GROUP BY kind
                """,
                (customer_id,),
            ).fetchall()
        for row in rows:
            totals[row["kind"]] = row["units"]
        return totals

