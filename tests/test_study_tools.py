from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_study_tools_are_loaded_and_have_spaced_repetition():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    script = ROOT / "backend" / "static" / "zentrix-study-tools.js"
    assert 'src="/zentrix-study-tools.js"' in html
    assert script.exists()
    source = script.read_text(encoding="utf-8")
    assert "Formula flashcards" in source
    assert "Again" in source and "Hard" in source and "Good" in source and "Easy" in source
    assert "zentrix_study_tools_v1" in source
    assert "Focus · 25 min" in source and "Break · 5 min" in source
    assert "setInterval(tick,250)" in source
    assert "localStorage" in source


def test_study_deck_contains_multiple_math_disciplines():
    source = (ROOT / "backend" / "static" / "zentrix-study-tools.js").read_text(encoding="utf-8")
    for subject in ("Algebra", "Geometry", "Trigonometry", "Calculus", "Statistics", "Probability"):
        assert "['" + subject + "'" in source
