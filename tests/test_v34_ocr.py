import base64
import io
import json
from pathlib import Path

import main
from fastapi.testclient import TestClient


def _valid_png_payload():
    # The route validates the PNG signature and transcription request; Google is mocked.
    raw = b'\x89PNG\r\n\x1a\n' + (b'zentrix-test-image' * 8)
    return {'mime_type': 'image/png', 'image_base64': base64.b64encode(raw).decode('ascii')}


def test_release_version_is_340():
    response = TestClient(main.app, base_url='http://127.0.0.1').get('/api/health')
    assert response.status_code == 200
    assert response.json()['version'] == '4.1.1'


def test_gemini_vision_ocr_requires_a_saved_key(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    response = TestClient(main.app, base_url='http://127.0.0.1').post('/api/ocr/vision', json=_valid_png_payload())
    assert response.status_code == 400
    assert 'Connect Gemini' in response.json()['detail']


def test_gemini_vision_ocr_is_local_only(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.setenv('GEMINI_API_KEY', 'x' * 30)
    response = TestClient(main.app, base_url='http://example.com').post('/api/ocr/vision', json=_valid_png_payload())
    assert response.status_code == 403


def test_gemini_vision_ocr_sends_only_requested_image_and_returns_transcription(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.setenv('GEMINI_API_KEY', 'x' * 30)
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-test-model')
    payload = _valid_png_payload()
    captured = {}

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['headers'] = dict(request.header_items())
        captured['timeout'] = timeout
        captured['body'] = json.loads(request.data.decode('utf-8'))
        return FakeResponse(json.dumps({'candidates': [{'content': {'parts': [{'text': 'Solve 2x + 5 = 17'}]}}]}).encode())

    monkeypatch.setattr(main.urllib.request, 'urlopen', fake_urlopen)
    response = TestClient(main.app, base_url='http://127.0.0.1').post('/api/ocr/vision', json=payload)

    assert response.status_code == 200
    result = response.json()
    assert result['transcription'] == 'Solve 2x + 5 = 17'
    assert result['sent_to_provider'] is True
    assert result['stored'] is False
    parts = captured['body']['contents'][0]['parts']
    assert parts[1]['inlineData']['mimeType'] == 'image/png'
    assert parts[1]['inlineData']['data'] == payload['image_base64']
    assert 'Do NOT solve it' in parts[0]['text']
    assert captured['timeout'] == 25


def test_ocr_frontend_has_cdn_fallback_retry_and_memory_bounds():
    page = (Path(main.__file__).parent / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'cdn.jsdelivr.net/npm/tesseract.js@5' in page
    assert 'unpkg.com/tesseract.js@5' in page
    assert 'ocrLibraryPromise=null' in page
    assert 'ocrWorkerPromise=null' in page
    assert 'maxEdge=2400,maxPixels=4000000' in page
    assert 'OCR pass ${i+1} of ${variants.length}' in page
    assert 'visionOcrBtn' in page
    assert "T.createWorker('eng',1,{logger:ocrLogger,errorHandler:e=>console.warn('ZENTRIX OCR worker:',e)},config)" in page
    assert 'visionProvider' in page
    assert 'readPhotoWithAI' in page
    assert 'AI math reading sends a compressed copy to ' in page


def test_vision_route_rejects_fake_image_bytes(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'false')
    monkeypatch.setenv('GEMINI_API_KEY', 'x' * 30)
    response = TestClient(main.app, base_url='http://127.0.0.1').post(
        '/api/ocr/vision', json={'mime_type': 'image/png', 'image_base64': base64.b64encode(b'not-a-png-file').decode()}
    )
    assert response.status_code == 400
    assert 'format' in response.json()['detail']
