import base64
import io
import json
import main
from fastapi.testclient import TestClient


def _payload(provider='openai'):
    raw = b'\x89PNG\r\n\x1a\n' + b'ZENTRIX-valid-test-image-bytes'
    return {'provider': provider, 'mime_type': 'image/png', 'image_base64': base64.b64encode(raw).decode()}


def test_ai_provider_status_lists_supported_services(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    for key in ('GEMINI_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','OPENROUTER_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    r = TestClient(main.app, base_url='http://127.0.0.1').get('/api/settings/ai')
    assert r.status_code == 200
    assert {x['id'] for x in r.json()['providers']} == {'gemini','openai','anthropic','openrouter'}
    assert not any(x['connected'] for x in r.json()['providers'])


def test_openai_vision_ocr_dispatches_image_and_returns_text(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-' + 'x' * 24)
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4o-mini')
    captured = {}
    class FakeResponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()
    def fake_urlopen(request, timeout):
        captured['body'] = json.loads(request.data.decode())
        captured['timeout'] = timeout
        return FakeResponse(json.dumps({'choices':[{'message':{'content':'Solve x^2 = 9'}}]}).encode())
    monkeypatch.setattr(main.urllib.request, 'urlopen', fake_urlopen)
    r = TestClient(main.app, base_url='http://127.0.0.1').post('/api/ocr/vision', json=_payload())
    assert r.status_code == 200
    assert r.json()['transcription'] == 'Solve x^2 = 9'
    assert r.json()['stored'] is False
    assert captured['body']['model'] == 'gpt-4o-mini'
    assert captured['body']['messages'][0]['content'][1]['type'] == 'image_url'


def test_anthropic_vision_uses_base64_image_block(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key-' + 'x' * 24)
    monkeypatch.setenv('ANTHROPIC_MODEL', 'claude-test')
    captured = {}
    class FakeResponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()
    def fake_urlopen(request, timeout):
        captured['body'] = json.loads(request.data.decode())
        return FakeResponse(json.dumps({'content':[{'type':'text','text':'Integrate 2x'}]}).encode())
    monkeypatch.setattr(main.urllib.request, 'urlopen', fake_urlopen)
    r = TestClient(main.app, base_url='http://127.0.0.1').post('/api/ocr/vision', json=_payload('anthropic'))
    assert r.status_code == 200
    assert r.json()['transcription'] == 'Integrate 2x'
    assert captured['body']['messages'][0]['content'][1]['source']['type'] == 'base64'


def test_provider_vision_requires_connection(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    r = TestClient(main.app, base_url='http://127.0.0.1').post('/api/ocr/vision', json=_payload('openai'))
    assert r.status_code == 400
    assert 'Connect OpenAI' in r.json()['detail']


def test_connected_provider_becomes_selectable_for_photo_ocr():
    from pathlib import Path
    page = (Path(main.__file__).parent / 'static' / 'index.html').read_text(encoding='utf-8')
    assert "[...select.options].forEach(o=>{o.disabled=!connectedVisionProviders.has(o.value)})" in page
    assert "connectedVisionProviders.add(provider);setVisionOcrAvailability()" in page


def test_ai_settings_endpoint_returns_provider_list_shape(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    for key in ('GEMINI_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','OPENROUTER_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    response = TestClient(main.app, base_url='http://127.0.0.1').get('/api/settings/ai')
    assert response.status_code == 200
    providers = response.json()['providers']
    assert len(providers) == 4
    assert all({'id','label','connected','model'} <= set(item) for item in providers)
