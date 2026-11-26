from pathlib import Path

HTML = (Path(__file__).parents[1] / "backend" / "static" / "index.html").read_text(encoding="utf-8")

def test_definitions_page_and_navigation_exist():
    assert 'id="page-definitions"' in HTML
    assert 'data-page="definitions"' in HTML
    assert 'Mathematics definitions' in HTML

def test_definition_search_and_categories_exist():
    assert 'id="definitionSearch"' in HTML
    assert 'id="definitionCategory"' in HTML
    assert 'function renderDefinitions()' in HTML
    assert 'const schoolDefinitions=' in HTML

def test_key_geometry_definitions_and_matrix_lab_retained():
    for term in ['Circle', 'Radius', 'Line segment', 'Diameter', 'Circumference', 'Triangle', 'Perimeter', 'Area']:
        assert f'"term": "{term}"' in HTML
    assert 'id="page-matrix"' in HTML
    assert 'data-page="matrix"' in HTML
