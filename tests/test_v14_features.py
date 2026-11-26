import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import engine
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_physics_force():
    r = engine.solve('physics force mass=5 acceleration=2')
    assert r['answer_text'] == '10 N' and r['verified']

def test_physics_ohms_law():
    r = engine.solve('physics ohms voltage=12 resistance=4')
    assert r['answer_text'] == '3 A' and r['verified']

def test_physics_kinetic_energy():
    r = engine.solve('physics kinetic energy mass=2 velocity=3')
    assert r['answer_text'] == '9 J' and r['verified']

def test_physics_acceleration_allows_signed_velocity():
    r = engine.solve('physics acceleration initial_velocity=-5 final_velocity=15 time=4')
    assert r['answer_text'] == '5 m/s²' and r['verified']

def test_physics_rejects_zero_denominator():
    r = engine.solve('physics speed distance=10 time=0')
    assert r['answer_text'] == 'unsolved'

def test_exact_answer_verification():
    r = client.post('/api/verify', json={'expected':'1/2','submitted':'0.5'})
    assert r.status_code == 200 and r.json()['correct'] is True

def test_incorrect_answer_verification():
    r = client.post('/api/verify', json={'expected':'7','submitted':'8'})
    assert r.status_code == 200 and r.json()['correct'] is False

def test_practice_generator_topics():
    for topic in ['algebra','calculus','arithmetic','physics','geometry','mixed']:
        r = client.get('/api/practice', params={'topic':topic,'difficulty':'medium'})
        assert r.status_code == 200
        data = r.json()
        assert data['question'] and data['expected'] and data['worked_solution']['verified']

def test_exponent_limit_is_enforced():
    try:
        engine.P('x**1001')
    except ValueError as e:
        assert 'Exponent magnitude' in str(e)
    else:
        raise AssertionError('Large exponent should be rejected')

def test_verification_level_is_explicit():
    r = engine.solve('factor x^2-9')
    assert r['verification_level'] in {'symbolic','numerical','rule-based','failed','unverified'}

def test_physics_remaining_models():
    cases = {
        'physics work force=10 distance=3': '30 J',
        'physics power work=100 time=5': '20 W',
        'physics potential energy mass=2 height=5': '981/10 J',
        'physics momentum mass=2 velocity=3': '6 kg·m/s',
        'physics density mass=10 volume=2': '5 kg/m³',
        'physics pressure force=100 area=5': '20 Pa',
        'physics speed distance=100 time=2': '50 m/s',
    }
    for q, expected in cases.items():
        result = engine.solve(q)
        assert result['answer_text'] == expected, (q, result['answer_text'])
        assert result['verified'] is True
