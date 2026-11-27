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
