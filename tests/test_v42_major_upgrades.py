from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
import main

ROOT = Path(__file__).parents[1]
client = TestClient(main.app)


def test_3d_surface_returns_bounded_numeric_grid():
    response = client.post("/api/plot3d", json={
        "expr": "x^2+y^2", "xmin": -1, "xmax": 1, "ymin": -1, "ymax": 1
    })
    assert response.status_code == 200
    result = response.json()
    assert result["samples"] == 25
    assert len(result["x"]) == 25
    assert len(result["y"]) == 25
    assert len(result["z"]) == 25
    assert all(len(row) == 25 for row in result["z"])
    assert result["z"][12][12] == 0
    assert result["z"][0][0] == 2


def test_3d_surface_rejects_invalid_ranges_and_unknown_variables():
    bad_range = client.post("/api/plot3d", json={
        "expr": "x+y", "xmin": 5, "xmax": -5, "ymin": -1, "ymax": 1
    })
    unknown = client.post("/api/plot3d", json={
        "expr": "x+z", "xmin": -1, "xmax": 1, "ymin": -1, "ymax": 1
    })
    assert bad_range.status_code == 400
    assert unknown.status_code == 400



def test_3d_surface_respects_custom_ranges():
    response = client.post("/api/plot3d", json={
        "expr": "x+y", "xmin": -2, "xmax": 2, "ymin": -3, "ymax": 3
    })
    assert response.status_code == 200
    result = response.json()
    assert result["x"][0] == -2
    assert result["x"][-1] == 2
    assert result["y"][0] == -3
    assert result["y"][-1] == 3
    assert result["z"][0][0] == -5
    assert result["z"][-1][-1] == 5

def test_pdf_import_pwa_and_3d_frontend_are_wired():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "backend" / "static" / "zentrix-upgrades.js").read_text(encoding="utf-8")
    assert 'href="/manifest.webmanifest"' in html
    assert 'src="/zentrix-upgrades.js"' in html
    assert "installPdfImporter" in script
    assert "pdfjsLib" in script
    assert "install3DGraph" in script
    assert "/api/plot3d" in script
    assert "zentrix3dPreset" in script
    assert "Download PNG" in script
    assert "Download CSV data" in script
    assert "zentrix3dXmin" in script
    assert "Reset view" in script
    assert "rows.join(" in script
    assert "text/csv;charset=utf-8" in script
    assert "registerOfflineShell" in script
    assert (ROOT / "backend" / "static" / "sw.js").exists()
    assert (ROOT / "backend" / "static" / "manifest.webmanifest").exists()


def test_2d_graph_controls_and_exports_are_installed():
    script = (ROOT / "backend" / "static" / "zentrix-upgrades.js").read_text(encoding="utf-8")
    assert "install2DGraphTools" in script
    assert "zentrix2dYmin" in script
    assert "zentrix2dYmax" in script
    assert "Auto-fit Y" in script
    assert "Download 2D PNG" in script
    assert "Download 2D CSV" in script
    assert "window.plotFunction=plot" in script
    assert "/api/plot" in script
    assert "text/csv;charset=utf-8" in script
