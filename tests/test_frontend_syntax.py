import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "relative_path",
    ["backend/static/index.html", "backend/static/checkout.html"],
)
def test_inline_javascript_parses(relative_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed in this test environment")

    html = (ROOT / relative_path).read_text(encoding="utf-8")
    scripts = re.findall(r"<script\b([^>]*)>([\s\S]*?)</script>", html, flags=re.I)
    inline_scripts = [
        script for attributes, script in scripts
        if script.strip()
        and not re.search(r'application/(?:ld[+]json|json)', attributes, flags=re.I)
    ]
    assert inline_scripts, f"No inline JavaScript found in {relative_path}"

    for script in inline_scripts:
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as tmp:
            tmp.write(script)
            tmp.flush()
            result = subprocess.run(
                [node, "--check", tmp.name],
                capture_output=True,
                text=True,
                check=False,
            )
        assert result.returncode == 0, result.stderr


def test_zentrix_upgrade_javascript_parses():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed in this test environment")
    script = ROOT / "backend" / "static" / "zentrix-upgrades.js"
    result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
