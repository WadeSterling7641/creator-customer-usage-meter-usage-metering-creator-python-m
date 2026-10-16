import httpx
from creator_usage.infrai_usage import InfraiUsageClient


def test_rate_limit_honors_retry_after_then_reads_envelope():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.method == "GET"
        assert request.url.path == "/v1/account/usage/timeseries"
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"ok": False, "data": None, "error": {}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"points": []}, "error": None, "metadata": {}},
        )

    delays: list[float] = []
    client = InfraiUsageClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
        sleep=delays.append,
    )
    result = client.usage_timeseries()
    client.close()

    assert result == {"points": []}
    assert calls == 2
    assert delays == [2.0]
