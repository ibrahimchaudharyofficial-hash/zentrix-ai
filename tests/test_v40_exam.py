from pathlib import Path

ROOT = Path(__file__).parents[1]
HTML = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
MAIN = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")

def test_v40_release_version_and_exam_navigation():
    assert "version=\'4.1.1\'" in MAIN
    assert 'id="page-exam"' in HTML
    assert 'data-page="exam"' in HTML
    assert "function startExam()" in HTML

def test_exam_has_subject_levels_feedback_and_local_progress():
    for token in ["examSubject", "examLength", "examLevel", "answerExam", "examStats", "zentrix_exam_stats"]:
        assert token in HTML

def test_matrix_and_definitions_remain_available():
    for token in ['id="page-matrix"', 'data-page="matrix"', 'id="page-definitions"', 'data-page="definitions"']:
        assert token in HTML
