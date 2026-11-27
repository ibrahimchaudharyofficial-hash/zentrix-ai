from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_interface_theme_and_accessibility_upgrade_is_loaded():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    script_path = ROOT / "backend" / "static" / "zentrix-interface.js"
    assert 'src="/zentrix-interface.js"' in html
    assert script_path.exists()
    source = script_path.read_text(encoding="utf-8")
    for theme in ("lavender", "ocean", "sage", "rose"):
        assert theme in source
    assert "zentrix_density" in source
    assert "prefers-reduced-motion" in source
    assert "focus-visible" in source
    assert "toggleTheme" in source



def test_navigation_refinement_is_loaded():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    script_path = ROOT / "backend" / "static" / "zentrix-navigation.js"
    assert 'src="/zentrix-navigation.js"' in html
    assert script_path.exists()


def test_navigation_refinement_has_keyboard_and_accessible_controls():
    js = (ROOT / "backend" / "static" / "zentrix-navigation.js").read_text(encoding="utf-8")
    assert "zentrixSidebarToggle" in js
    assert "aria-expanded" in js
    assert "zentrix_sidebar" in js
    assert "event.altKey" in js
    assert "event.ctrlKey" in js
    assert "prefers-reduced-motion" in js


def test_navigation_refinement_supports_responsive_sidebar():
    js = (ROOT / "backend" / "static" / "zentrix-navigation.js").read_text(encoding="utf-8")
    assert "min-width:721px" in js
    assert "max-width:720px" in js
    assert "window.addEventListener('resize'" in js
