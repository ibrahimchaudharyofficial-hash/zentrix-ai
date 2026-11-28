import io
import json
import sys
import urllib.error
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import main

client = TestClient(main.app)


def _clear_provider_keys(monkeypatch):
    for key in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_offline_tutor_returns_lesson_example_misconception_and_practice(monkeypatch):
    monkeypatch.setenv("ZENTRIX_PUBLIC_MODE", "false")
    _clear_provider_keys(monkeypatch)
    response = client.post("/api/tutor/explain", json={"topic": "calculus", "question": "Why is the power rule used?"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "offline tutor"
    assert data["provider"] is None
    assert "CONCEPT" in data["explanation"]
    assert "WORKED EXAMPLE" in data["explanation"]
    assert "COMMON MISTAKE" in data["explanation"]
    assert "TRY THIS" in data["explanation"]
    assert "Why is the power rule used?" in data["explanation"]
    assert data["stored"] is False


def test_gemini_tutor_uses_connected_provider(monkeypatch):
    monkeypatch.setenv("ZENTRIX_PUBLIC_MODE", "false")
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-" + "x" * 24)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    captured = {}

    class FakeResponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        return FakeResponse(json.dumps({"candidates":[{"content":{"parts":[{"text":"Use the power rule, then simplify."}]}}]}).encode())

    monkeypatch.setattr(main.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/api/tutor/explain", json={"topic":"calculus","question":"Differentiate x^3"})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "Google Gemini"
    assert data["mode"] == "optional AI tutor"
    assert "power rule" in data["explanation"]
    assert "gemini-test:generateContent" in captured["url"]
    assert "never claim" in captured["body"]["contents"][0]["parts"][0]["text"]


def test_openai_tutor_uses_chat_completions(monkeypatch):
    monkeypatch.setenv("ZENTRIX_PUBLIC_MODE", "false")
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-" + "x" * 24)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    captured = {}

    class FakeResponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        return FakeResponse(json.dumps({"choices":[{"message":{"content":"First isolate the variable."}}]}).encode())

    monkeypatch.setattr(main.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/api/tutor/explain", json={"topic":"algebra","question":"Solve 2x=8"})
    assert response.status_code == 200
    assert response.json()["provider"] == "OpenAI"
    assert response.json()["explanation"] == "First isolate the variable."
    assert captured["body"]["model"] == "gpt-test"


def test_tutor_fails_over_to_next_connected_provider(monkeypatch):
    monkeypatch.setenv("ZENTRIX_PUBLIC_MODE", "false")
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-" + "x" * 24)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-" + "x" * 24)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    calls = []

    class FakeResponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if "generativelanguage.googleapis.com" in request.full_url:
            raise urllib.error.HTTPError(request.full_url, 429, "quota", {}, None)
        return FakeResponse(json.dumps({"choices":[{"message":{"content":"A balanced equation stays equal."}}]}).encode())

    monkeypatch.setattr(main.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/api/tutor/explain", json={"topic":"algebra","question":"Explain equations"})
    assert response.status_code == 200
    assert response.json()["provider"] == "OpenAI"
    assert len(calls) == 2
    assert "Gemini: provider quota or rate limit reached" in response.json()["provider_fallbacks"][0]


def test_public_mode_never_uses_server_ai_keys_for_tutor(monkeypatch):
    monkeypatch.setenv("ZENTRIX_PUBLIC_MODE", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-" + "x" * 24)
    def forbidden(*args, **kwargs):
        raise AssertionError("Public mode must not call a server-wide AI key.")
    monkeypatch.setattr(main.urllib.request, "urlopen", forbidden)
    response = client.post("/api/tutor/explain", json={"topic":"algebra","question":"Explain variables"})
    assert response.status_code == 200
    assert response.json()["mode"] == "offline tutor"
    assert response.json()["provider"] is None


def test_tutor_page_exposes_advanced_topics_and_free_fallback():
    page = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    assert "AI & offline tutor" in page
    assert "always has a free offline fallback" in page
    assert "<option>Calculus</option>" in page
    assert "<option>Matrices</option>" in page
    assert "AI TUTOR · " in page
