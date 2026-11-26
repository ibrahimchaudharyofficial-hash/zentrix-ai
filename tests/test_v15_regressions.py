import os, sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import engine
import main


def test_previously_misread_algebra_word_problem():
    result = engine.solve('word problem: A number increased by 7 is three times the difference between the number and 5. Find the number.')
    assert result['answer_text'] == '11'
    assert result['verified'] is True
    assert any('Translate the statement' in step['title'] for step in result['steps'])


def test_ambiguous_increase_word_problem_is_not_guessed():
    result = engine.solve('word problem: the number increased and decreased by some amount, find the new number')
    assert result['answer_text'] == 'unsolved'
    assert result['verified'] is False
    assert result['verification_level'] == 'unverified'


def test_ambiguous_number_relationship_is_not_assumed():
    result = engine.solve('word problem: A number increased by 7 is three times the number decreased by 5. Find the number.')
    assert result['answer_text'] == 'unsolved'
    assert result['verified'] is False


def test_ambiguous_word_problem_never_falls_through_to_gemini(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key-that-must-not-be-used')
    monkeypatch.setattr(engine, 'llm_command', lambda _q: 'solve x=11')
    result = engine.solve('word problem: A number increased by 7 is three times the number decreased by 5. Find the number.')
    assert result['answer_text'] == 'unsolved'
    assert result['verified'] is False


def test_matrix_inverse_step_is_not_false():
    result = engine.solve('inverse of [[2,1],[5,3]]')
    assert result['answer_text'] == 'Matrix([[3, -1], [-5, 2]])'
    assert any(step['title'] == 'Inverse' and 'False' not in step['latex'] for step in result['steps'])


def test_eigenvalues_and_eigenvectors_are_shown():
    result = engine.solve('eigenvalues of [[4,1],[2,3]]')
    titles = [step['title'] for step in result['steps']]
    assert 'Characteristic equation' in titles
    assert 'Solve the characteristic equation' in titles
    assert 'Eigenvectors' in titles
    assert 'False' not in result['steps'][-1]['latex']


def test_statistics_keeps_duplicate_observations():
    result = engine.solve('standard deviation of 2,4,4,4,5,5,7,9')
    observations = next(step['latex'] for step in result['steps'] if 'Observations' in step['title'])
    assert observations.count('4') >= 3
    assert 'n=8' in observations


def test_two_sided_limit_display():
    result = engine.solve('limit (x^2-1)/(x-1) as x->1')
    first = result['steps'][0]['latex']
    assert r'1^{+}' not in first
    assert 'One-sided limits' in [step['title'] for step in result['steps']]


def test_binomial_probability_with_working():
    result = engine.solve('probability exactly 2 heads in 5 fair coin tosses')
    assert result['answer_text'] == '5/16'
    assert len(result['steps']) >= 4
    assert 'binom' in result['formula']


def test_proof_auditor_valid_and_invalid_steps():
    client = TestClient(main.app)
    good = client.post('/api/audit', json={'steps':['3x + 6 = 0','3x = -6','x = -2']})
    assert good.status_code == 200, good.text
    assert good.json()['valid'] is True
    bad = client.post('/api/audit', json={'steps':['x + 2 = 5','x + 2 = 6','x = 4']})
    assert bad.status_code == 200, bad.text
    assert bad.json()['valid'] is False
    assert bad.json()['first_issue']['from_line'] == 1


def test_core_api_and_graph_smoke():
    client = TestClient(main.app)
    assert client.get('/api/health').json()['version'] == '4.1.1'
    solved = client.post('/api/solve', json={'question':'solve x^2-5*x+6=0'})
    assert solved.status_code == 200 and '[2, 3]' in solved.json()['answer_text']
    plot = client.post('/api/plot', json={'expr':'x^2-4*x+3','xmin':-5,'xmax':5})
    assert plot.status_code == 200 and len(plot.json()["x"]) == 640
    practice = client.get('/api/practice?topic=algebra&difficulty=hard')
    assert practice.status_code == 200 and practice.json()['worked_solution']['steps']
