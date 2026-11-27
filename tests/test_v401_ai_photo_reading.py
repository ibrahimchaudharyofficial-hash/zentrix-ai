from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ai_photo_reader_has_image_preparation_helper():
    page = (ROOT / 'backend' / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'async function photoForGemini(file)' in page
    assert "canvas.toBlob(resolve,'image/jpeg',quality)" in page
    assert 'return {mime_type:\'image/jpeg\',image_base64:btoa(binary)}' in page
    assert 'const payload=await photoForGemini(file)' in page


def test_ai_photo_reader_surfaces_actual_error():
    page = (ROOT / 'backend' / 'static' / 'index.html').read_text(encoding='utf-8')
    assert "notify('AI scan failed; using local OCR: '+(e.message||'Unknown error'))" in page


def test_backend_photo_payload_limit_matches_compression_limit():
    main = (ROOT / 'backend' / 'main.py').read_text(encoding='utf-8')
    assert 'len(image_bytes) > 975_000' in main


def test_ai_photo_reader_retries_connected_providers_before_local_ocr():
    page = (ROOT / 'backend' / 'static' / 'index.html').read_text(encoding='utf-8')
    assert "filter(id=>connectedVisionProviders.has(id))" in page
    assert 'for(const provider of providers)' in page
    assert 'await recognisePhotoLocally()' in page
    assert 'Photo selection changed. Please try again.' in page
