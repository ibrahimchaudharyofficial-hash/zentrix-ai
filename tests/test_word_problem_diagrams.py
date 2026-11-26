import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import engine

def test_ladder_word_problem_generates_verified_diagram():
    q = "A ladder 10 metres long rests against a wall. Its foot is 6 metres away from the wall. Find the height reached by the ladder."
    result = engine.solve(q)
    assert result["answer_text"] == "8 metres"
    assert result["diagram"]["type"] == "right_triangle"
    assert result["diagram"]["base_label"] == "6 metres"
    assert result["diagram"]["height_label"] == "8 metres"
    assert result["diagram"]["hypotenuse_label"] == "10 metres"
    assert result["verified"] is True

def test_ladder_problem_with_non_integer_height():
    q = "A ladder 5 m long leans against a wall, with its foot 3 m from the wall. Find the height."
    result = engine.solve(q)
    assert result["answer_text"] == "4 m"
    assert result["verified"] is True

def test_non_ladder_question_does_not_get_false_diagram():
    result = engine.solve("solve 3x=21")
    assert result["diagram"] is None
    assert result["answer_text"] in ("[7]", "7")


def test_rectangle_area_statement_generates_figure():
    q = "A rectangular garden is 12 metres long and 5 metres wide. Find its area."
    result = engine.solve(q)
    assert result["answer_text"] == "60 metres²"
    assert result["diagram"]["type"] == "rectangle"
    assert result["verified"] is True

def test_rectangle_perimeter_statement_generates_figure():
    q = "A rectangular field is 12 m long and 5 m wide. Find the perimeter."
    result = engine.solve(q)
    assert result["answer_text"] == "34 m"
    assert result["diagram"]["type"] == "rectangle"

def test_triangle_area_statement_generates_figure():
    result = engine.solve('A triangular plot has a base of 10 m and perpendicular height of 6 m. Find its area.')
    assert result['answer_text'] == '30 m²'
    assert result['diagram']['type'] == 'triangle'
    assert result['verified'] is True

def test_circle_area_statement_generates_figure():
    result = engine.solve('A circular pond has a radius of 7 metres. Find its area.')
    assert result['diagram']['type'] == 'circle'
    assert result['answer_text'].startswith('153.938')
    assert result['verified'] is True

def test_circle_circumference_uses_diameter_correctly():
    result = engine.solve('A circle has a diameter of 10 cm. Find its circumference.')
    assert result['diagram']['type'] == 'circle'
    assert result['answer_text'].startswith('31.4159')
    assert result['verified'] is True
