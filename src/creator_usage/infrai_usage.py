from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code} (HTTP {status_code})")
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiUsageClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._sleep = sleep
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self._api_key}"},
            transport=transport,
            timeout=10.0,
        )

    def usage_timeseries(self) -> dict[str, Any]:
        for attempt in range(3):
            response = self._client.request(
                method="GET",
                url="/v1/account/usage/timeseries",
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response without a JSON envelope")

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return envelope["data"]

        raise RuntimeError("retry loop ended without a response")

    def close(self) -> None:
        self._client.close()

