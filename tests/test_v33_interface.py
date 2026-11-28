from pathlib import Path
import main
from fastapi.testclient import TestClient


def test_release_version_is_380():
    response = TestClient(main.app).get('/api/health')
    assert response.status_code == 200
    assert response.json()['version'] == '4.1.1'


def test_dashboard_includes_active_usage_tracker_and_privacy_copy():
    page = TestClient(main.app).get('/')
    assert page.status_code == 200
    assert 'Your time in ZENTRIX' in page.text
    assert 'Last 7 days' in page.text
    assert 'Saved on this device' in page.text
    assert 'zentrix_active_usage_v1' in page.text
    assert 'USAGE_IDLE_MS=75000' in page.text


def test_school_level_navigation_removes_university_math_pages():
    page = TestClient(main.app).get('/')
    assert page.status_code == 200
    for label in ('Start here', 'Math tools', 'Learn & improve', 'Your work',
                  'Verify solutions', 'Fix mistakes', 'School Mathematics'):
        assert label in page.text
    for removed in ('Advanced maths', 'Differential Equations'):
        assert removed not in page.text
    assert 'data-page="calculus"' not in page.text
    assert 'id="page-calculus"' not in page.text
    for page_id in ('page-graph', 'page-learn', 'page-arcade', 'page-auditor',
                    'page-coach', 'page-history'):
        assert f'id="{page_id}"' in page.text
    assert 'id="page-matrix"' in page.text
    assert 'Matrix Lab' in page.text
    assert 'id="page-research"' not in page.text
    assert 'Outside the school-level scope' in page.text


def test_light_theme_uses_soft_blush_palette_and_dark_theme_is_preserved():
    page = TestClient(main.app).get('/').text
    assert '--bg:#fff9fc' in page
    assert '--accent:#9e6485' in page
    assert '[data-theme=dark]' in page
    assert 'rgba(244,190,218,.20)' in page
