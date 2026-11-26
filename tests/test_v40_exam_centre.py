from pathlib import Path
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / 'backend'))
import main

HTML = (Path(__file__).parents[1] / 'backend' / 'static' / 'index.html').read_text(encoding='utf-8')

def test_v40_health_version_and_home_page():
    client = TestClient(main.app)
    assert client.get('/api/health').json()['version'] == '4.1.1'
    page = client.get('/')
    assert page.status_code == 200
    assert 'Think clearly.' in page.text

def test_exam_centre_is_navigable_and_has_working_controls():
    for item in ['id="page-exam"', 'data-page="exam"', 'id="examSubject"', 'id="examLength"', 'id="examLevel"', 'function startExam()', 'function answerExam(', 'function nextExamQuestion()']:
        assert item in HTML
    assert 'zentrix_exam_stats' in HTML

def test_matrix_and_definitions_are_preserved():
    assert 'id="page-matrix"' in HTML and 'data-page="matrix"' in HTML
    assert 'id="page-definitions"' in HTML and 'const schoolDefinitions=' in HTML
