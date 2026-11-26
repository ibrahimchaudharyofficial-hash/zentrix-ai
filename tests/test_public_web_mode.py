import main
from fastapi.testclient import TestClient


def test_public_config_exposes_only_public_supabase_values(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'true')
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'public-anon-placeholder')
    result = TestClient(main.app).get('/api/public-config').json()
    assert result == {
        'public_mode': True,
        'supabase_url': 'https://example.supabase.co',
        'supabase_anon_key': 'public-anon-placeholder',
        'auth_enabled': True,
    }
    assert 'service_role' not in str(result).lower()


def test_public_mode_does_not_expose_shared_progress(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'true')
    client = TestClient(main.app)
    attempt = {'subject': 'Algebra', 'difficulty': 'Easy', 'game': 'number', 'correct': True, 'seconds': 12}
    saved = client.post('/api/arcade/attempt', json=attempt)
    assert saved.status_code == 200
    assert saved.json()['saved'] is False
    assert client.get('/api/arcade/stats').json()['attempts'] == 0
    assert client.get('/api/learning/profile').json()['total_attempts'] == 0


def test_public_mode_disables_shared_server_ai_key_settings(monkeypatch):
    monkeypatch.setenv('ZENTRIX_PUBLIC_MODE', 'true')
    monkeypatch.setenv('GEMINI_API_KEY', 'a-test-global-secret-that-must-not-be-used')
    client = TestClient(main.app)
    assert client.get('/api/settings/ai').status_code == 404
    assert client.post('/api/settings/gemini', json={'api_key': 'a-test-global-secret-that-must-not-be-used'}).status_code == 404
    assert client.get('/api/health').json()['online_ai_configured'] is False
