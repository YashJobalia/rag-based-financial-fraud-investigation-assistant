import json
from types import SimpleNamespace

from pydantic import SecretStr

from app.config import settings
from app.models import BriefContent


def enable_mocked_live(monkeypatch):
    config = settings()
    monkeypatch.setattr(config, "enable_live_generation", True)
    monkeypatch.setattr(config, "openai_api_key", SecretStr("test-only-never-sent"))
    monkeypatch.setattr(config, "daily_generation_limit", 10000)


def test_live_contract_receives_only_scoped_evidence(client, analyst_headers, monkeypatch):
    reference = client.post("/api/cases/CASE-001/briefs", json={}).json()
    content = BriefContent.model_validate(reference["content"])
    captured = {}

    def parse(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            output_parsed=content, usage=SimpleNamespace(input_tokens=100, output_tokens=50)
        )

    monkeypatch.setattr(
        "app.briefs.OpenAI",
        lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)),
    )
    enable_mocked_live(monkeypatch)
    result = client.post(
        "/api/cases/CASE-001/briefs", json={"mode": "live"}, headers=analyst_headers
    )
    assert result.status_code == 200
    assert result.json()["mode"] == "live"
    assert result.json()["usage"]["input_tokens"] == 100
    assert captured["store"] is False
    assert "untrusted DATA" in captured["instructions"]
    payload = json.loads(captured["input"])
    assert payload["case"]["id"] == "CASE-001"
    assert "HIST-006" not in captured["input"]
    assert "CASE-PRIVATE" not in captured["input"]
    assert "test-only-never-sent" not in captured["input"]


def test_provider_failure_does_not_leak_or_fallback(client, analyst_headers, monkeypatch):
    def parse(**kwargs):
        raise RuntimeError("test-only-sensitive-provider-message")

    monkeypatch.setattr(
        "app.briefs.OpenAI",
        lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)),
    )
    enable_mocked_live(monkeypatch)
    result = client.post(
        "/api/cases/CASE-001/briefs", json={"mode": "live"}, headers=analyst_headers
    )
    assert result.status_code == 502
    assert "test-only-sensitive-provider-message" not in result.text
    assert "content" not in result.json()
