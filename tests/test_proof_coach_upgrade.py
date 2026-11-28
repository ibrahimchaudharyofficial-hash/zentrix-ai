import os, sys
from fastapi.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'backend'))
import main


def test_proof_auditor_adds_cautious_misconception_diagnosis():
    client = TestClient(main.app)
    response = client.post('/api/diagnose', json={'steps':['x + 7 = 19', 'x = 19 + 7']})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['diagnosed'] is True
    assert data['misconception'] == 'Sign error when moving a term'
    assert data['confidence'] == 'medium'
    assert data['practice']


def test_proof_auditor_reports_when_no_misconception_is_detected():
    client = TestClient(main.app)
    response = client.post('/api/diagnose', json={'steps':['3x + 6 = 0', '3x = -6', 'x = -2']})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['diagnosed'] is False
    assert data['valid'] is True
    assert data['confidence'] == 'limited'


def test_proof_auditor_ui_shows_possible_misconception_without_overclaiming():
    path = os.path.join(ROOT, 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    assert "fetch('/api/diagnose'" in html
    assert 'Possible misconception' in html
    assert 'diagnosis.confidence' in html
