from fastapi.testclient import TestClient
import main

def test_arcade_stats_and_attempt_persistence():
    client = TestClient(main.app)
    before = client.get('/api/arcade/stats').json()
    response = client.post('/api/arcade/attempt', json={
        'subject': 'Algebra', 'difficulty': 'Intermediate', 'game': 'quick',
        'correct': True, 'seconds': 12
    })
    assert response.status_code == 200
    after = client.get('/api/arcade/stats').json()
    assert after['attempts'] == before['attempts'] + 1
    assert after['correct'] == before['correct'] + 1
    assert after['accuracy'] >= 0
    assert any(row['subject'] == 'Algebra' for row in after['subjects'])

def test_arcade_attempt_validation():
    client = TestClient(main.app)
    response = client.post('/api/arcade/attempt', json={
        'subject': 'Algebra', 'difficulty': 'Pro', 'game': 'quick',
        'correct': True, 'seconds': -1
    })
    assert response.status_code == 422

def test_offline_tutor_returns_local_explanation(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    client = TestClient(main.app)
    response = client.post('/api/tutor/explain', json={'topic': 'calculus', 'question': 'Explain the power rule'})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'offline tutor'
    assert 'power rule' in data['explanation'].lower()
    assert data['verified_calculation'] is False

def test_release_health_and_static_arcade_page():
    client = TestClient(main.app)
    assert client.get('/api/health').json()['version'] == '4.1.1'
    page = client.get('/')
    assert page.status_code == 200
    assert 'Math Arcade' in page.text
    assert 'Adaptive (automatic)' in page.text
    assert 'Show About ZENTRIX in Settings' in page.text
