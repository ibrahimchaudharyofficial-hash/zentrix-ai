import os


def test_exam_centre_includes_university_level_subject_banks():
    path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    for subject in ('Calculus', 'Matrices', 'Probability'):
        assert 'value="'+subject+'"' in html
        assert "subject:'"+subject+"'" in html
    assert "q.o.forEach" in html
    assert "examQuestions=pool.sort" in html
