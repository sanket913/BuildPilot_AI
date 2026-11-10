import asyncio
import json

from app import ai
from app.config import settings
from app.schemas import TextOut


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def post(self, url, **kwargs):
        self.request = (url, kwargs)
        return self.response


def test_configured_provider_uses_server_key_and_validates_schema(monkeypatch):
    fake = FakeClient(FakeResponse(json.dumps({"content": "A generated README"})))
    monkeypatch.setattr(settings, "ai_api_key", "test-secret-key")
    monkeypatch.setattr(ai.httpx, "AsyncClient", lambda **_: fake)

    result = asyncio.run(ai.ask("Write docs", {"content": "fallback"}, TextOut))

    assert result == {"mode": "ai", "result": {"content": "A generated README"}}
    assert fake.request[0] == "https://api.openai.com/v1/chat/completions"
    assert fake.request[1]["headers"]["Authorization"] == "Bearer test-secret-key"


def test_invalid_provider_output_returns_labeled_schema_valid_fallback(monkeypatch):
    fake = FakeClient(FakeResponse("{}"))
    monkeypatch.setattr(settings, "ai_api_key", "test-secret-key")
    monkeypatch.setattr(ai.httpx, "AsyncClient", lambda **_: fake)

    result = asyncio.run(ai.ask("Write docs", {"content": "fallback"}, TextOut))

    assert result["mode"] == "demo"
    assert result["result"] == {"content": "fallback"}
    assert "warning" in result
