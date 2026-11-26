import sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import main
client = TestClient(main.app)


def test_distribution_error_is_classified():
    r = client.post('/api/diagnose', json={'problem':'Expand 2(x+3)', 'steps':['2(x + 3)', '2x + 3']})
    assert r.status_code == 200
    data = r.json()
    assert data['valid'] is False
    assert data['misconception'] == 'Incomplete distribution'
    assert 'every term' in data['explanation']
    assert data['practice']


def test_missing_negative_root_is_classified():
    r = client.post('/api/diagnose', json={'problem':'Solve x^2=25', 'steps':['x^2 = 25', 'x = 5']})
    assert r.status_code == 200
    assert r.json()['misconception'] == 'Lost the negative square root'


def test_fraction_inverse_operation_is_classified():
    r = client.post('/api/diagnose', json={'steps':['x/4 = 6', 'x = 6/4']})
    assert r.status_code == 200
    assert r.json()['misconception'] == 'Incorrect inverse operation with a fraction'


def test_correct_steps_are_not_flagged():
    r = client.post('/api/diagnose', json={'steps':['2(x + 3) = 14', '2x + 6 = 14', '2x = 8', 'x = 4']})
    assert r.status_code == 200
    assert r.json()['valid'] is True
    assert r.json()['misconception'] is None


def test_unknown_error_is_reported_cautiously():
    r = client.post('/api/diagnose', json={'steps':['x^3 + 1 = 0', 'x = -1']})
    assert r.status_code == 200
    assert r.json()['valid'] is False
    assert r.json()['confidence'] == 'low'


def test_limits_are_enforced():
    r = client.post('/api/diagnose', json={'steps':['x=1']})
    assert r.status_code == 422


def test_sign_change_error_is_classified():
    r = client.post('/api/diagnose', json={'steps':['x + 7 = 19', 'x = 19 + 7']})
    assert r.status_code == 200
    assert r.json()['misconception'] == 'Sign error when moving a term'


def test_zero_product_solution_loss_is_flagged():
    r = client.post('/api/diagnose', json={'steps':['x(x - 5) = 0', 'x - 5 = 0']})
    assert r.status_code == 200
    assert r.json()['misconception'] == 'Zero-product property used incompletely'
