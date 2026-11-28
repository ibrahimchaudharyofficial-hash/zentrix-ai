import os


def test_exam_centre_has_timed_mode_and_answer_review():
    path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    assert 'examTiming' in html
    assert 'examTimer' in html
    assert 'function renderExamTimer()' in html
    assert 'function finishExam(timeExpired=false)' in html
    assert 'examReview.push' in html
    assert 'Review all answers' in html
    assert 'Time is up' in html


def test_exam_timer_is_cleaned_up_when_restarting_or_finishing():
    path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    assert "if(examClock){clearInterval(examClock);examClock=null}" in html
    assert "if(examRemaining===0)finishExam(true)" in html
