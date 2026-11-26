import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import main


def test_accepts_google_key_with_printable_punctuation():
    key = "AIzaSy" + "a" * 28 + "-_=+"
    assert main._validate_gemini_key(key) == key


def test_rejects_short_key():
    with pytest.raises(HTTPException) as exc:
        main._validate_gemini_key("too-short")
    assert exc.value.status_code == 400


def test_rejects_embedded_whitespace():
    with pytest.raises(HTTPException) as exc:
        main._validate_gemini_key("a" * 20 + " " + "b" * 10)
    assert exc.value.status_code == 400


def test_rejects_non_ascii_key():
    with pytest.raises(HTTPException) as exc:
        main._validate_gemini_key("a" * 25 + "é")
    assert exc.value.status_code == 400
