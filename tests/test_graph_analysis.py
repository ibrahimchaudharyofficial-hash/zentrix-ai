import os, sys
from fastapi.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'backend'))
import main


def test_graph_analysis_finds_roots_derivative_and_minimum():
    client = TestClient(main.app)
    response = client.post('/api/plot/analyze', json={'expr': 'x^2-4*x+3', 'xmin': -2, 'xmax': 6})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['derivative'] == '2*x - 4'
    assert [round(item['x']) for item in data['roots']] == [1, 3]
    assert len(data['critical_points']) == 1
    assert data['critical_points'][0]['kind'] == 'local minimum'
    assert data['critical_points'][0]['x'] == 2.0
    assert data['y_intercept'] == 3.0


def test_graph_analysis_rejects_unsafe_or_invalid_expressions():
    client = TestClient(main.app)
    bad = client.post('/api/plot/analyze', json={'expr': "__import__('os').system('whoami')", 'xmin': -2, 'xmax': 2})
    assert bad.status_code == 400
    bad_bounds = client.post('/api/plot/analyze', json={'expr': 'x', 'xmin': 2, 'xmax': 2})
    assert bad_bounds.status_code == 400


def test_graph_studio_exposes_analysis_action():
    path = os.path.join(ROOT, 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    assert 'Analyse function' in html
    assert '/api/plot/analyze' in html
    assert 'graphAnalysis' in html
