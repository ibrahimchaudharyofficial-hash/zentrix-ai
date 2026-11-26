from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_research_calculus_analysis():
    r = client.post('/api/research/analyze', json={
        'expression': 'x^2', 'variable': 'x', 'point': 2,
        'interval_start': 0, 'interval_end': 2, 'precision': 30
    })
    assert r.status_code == 200
    data = r.json()
    assert data['derivative'] == '2*x'
    assert data['value'] == '4.00000000000000000000000000000'
    assert data['definite_integral'].startswith('2.')
    assert len(data['samples']) == 41

def test_identity_symbolic_verification():
    r = client.post('/api/proof/identity', json={
        'left': 'sin(x)^2+cos(x)^2', 'right': '1', 'variable': 'x'
    })
    assert r.status_code == 200
    assert r.json()['valid'] is True
    assert r.json()['symbolic_check'] is True

def test_identity_false_statement_not_proven():
    r = client.post('/api/proof/identity', json={
        'left': 'x^2', 'right': 'x', 'variable': 'x'
    })
    assert r.status_code == 200
    assert r.json()['valid'] is False

def test_knowledge_topics_endpoint():
    r = client.get('/api/knowledge/topics')
    assert r.status_code == 200
    assert len(r.json()['topics']) >= 5

def test_learning_profile_endpoint():
    r = client.get('/api/learning/profile')
    assert r.status_code == 200
    data = r.json()
    assert 'overall_accuracy' in data
    assert 'method_note' in data

def test_api_response_security_headers_and_no_store():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.headers['x-content-type-options'] == 'nosniff'
    assert r.headers['x-frame-options'] == 'SAMEORIGIN'
    assert r.headers['cache-control'] == 'no-store'


def test_diagnostics_exposes_bounded_solver_cache():
    r = client.get('/api/diagnostics')
    assert r.status_code == 200
    data = r.json()
    assert data['solver_cache']['capacity'] == 384
    assert data['solver_concurrency_limit'] == 2
    assert data['plot_samples'] == 640


def test_plot_uses_bounded_sample_count_and_handles_singularity():
    r = client.post('/api/plot', json={'expr': '1/x', 'xmin': -2, 'xmax': 2})
    assert r.status_code == 200
    data = r.json()
    assert len(data['x']) == len(data['y']) == 640
    assert all(value is None or isinstance(value, (int, float)) for value in data['y'])


def test_invalid_research_variable_is_rejected():
    r = client.post('/api/research/analyze', json={'expression': 'x^2', 'variable': 'x+y'})
    assert r.status_code == 400


def test_identity_reports_cancelled_factor_domain_restriction():
    r = client.post('/api/proof/identity', json={
        'left': '(x^2-1)/(x-1)', 'right': 'x+1', 'variable': 'x'
    })
    assert r.status_code == 200
    data = r.json()
    assert data['valid'] is True
    assert any('x - 1' in item['denominator'] for item in data['domain_restrictions'])
    assert 'common domain' in data['caution']


def test_answer_verifier_reports_domain_restrictions():
    r = client.post('/api/verify', json={'expected': '(x^2-1)/(x-1)', 'submitted': 'x+1'})
    assert r.status_code == 200
    data = r.json()
    assert data['correct'] is True
    assert data['domain_restrictions']
    assert 'common domain' in data['domain_note']


def test_partial_checks_are_not_reported_as_fully_verified():
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'backend'))
    import engine
    result = engine.Res('test')
    result.check('exact check', True)
    result.check('optional numerical check', None)
    output = result.out()
    assert output['verified'] is False
    assert output['verification_status'] == 'partially-verified'
