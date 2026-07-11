"""Tests for the most critical logic in model-eval: answer extraction and
config/CLI validation. A silent extraction bug produces plausible-looking wrong
scores, so these are the tests that matter most (GitHub issue #2)."""

import argparse
import pytest

from benchmark import extract_letter, extract_number
from config import load_config, positive_int, http_url, with_retries, DEFAULTS


# ── extract_letter ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("A", "A"),
    ("B. Paris", "B"),
    ("The answer is C", "C"),
    ("  D  ", "D"),
    ("I think the answer is (C).", "C"),
    ("D) because the others are wrong", "D"),
])
def test_extract_letter_hits(text, expected):
    assert extract_letter(text) == expected


def test_extract_letter_prefers_leading_letter():
    # A leading valid letter wins over a later one — matches how models answer.
    assert extract_letter("B, though some might say D") == "B"


def test_extract_letter_none_when_absent():
    assert extract_letter("The mitochondria is the powerhouse") is None
    assert extract_letter("") is None


def test_extract_letter_respects_choice_set():
    # TruthfulQA can have >4 options; a letter outside the set must not match.
    assert extract_letter("F", "ABCDEFGH") == "F"
    assert extract_letter("F", "ABCD") is None


def test_extract_letter_does_not_match_midword():
    # "Answer" starts with A but must not be read as choice A.
    assert extract_letter("Answer: C") == "C"


# ── extract_number ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("#### 42", "42"),
    ("The total is #### 1,234", "1234"),
    ("... so she has 18 apples left.\n#### 18", "18"),
    ("#### -5", "-5"),
])
def test_extract_number_marker(text, expected):
    assert extract_number(text) == expected


def test_extract_number_falls_back_to_last():
    # No #### marker → last number in the text.
    assert extract_number("First 10, then 20, total is 30") == "30"


def test_extract_number_strips_commas():
    assert extract_number("The answer is 1,000,000") == "1000000"


def test_extract_number_none_when_absent():
    assert extract_number("no digits here") is None
    assert extract_number("") is None


def test_extract_number_marker_beats_trailing_prose():
    # The #### value is authoritative even if prose follows it.
    assert extract_number("#### 7 is the final answer") == "7"


# ── config / CLI validation ───────────────────────────────────────────────────

def test_positive_int_accepts_positive():
    assert positive_int("50") == 50


@pytest.mark.parametrize("bad", ["0", "-5", "abc", "3.5"])
def test_positive_int_rejects(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(bad)


def test_http_url_accepts():
    assert http_url("http://localhost:8010/v1") == "http://localhost:8010/v1"
    assert http_url("https://api.example.com/v1").startswith("https://")


@pytest.mark.parametrize("bad", ["localhost:8010", "ftp://x", "8010/v1", ""])
def test_http_url_rejects(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        http_url(bad)


def test_load_config_has_all_defaults():
    cfg = load_config()
    for key in DEFAULTS:
        assert key in cfg


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("PROXY_URL", "http://example:9999/v1")
    assert load_config()["base_url"] == "http://example:9999/v1"


# ── retry logic ───────────────────────────────────────────────────────────────

def test_with_retries_returns_on_success():
    assert with_retries(lambda: 7, max_retries=3) == 7


def test_with_retries_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "ok"

    assert with_retries(flaky, max_retries=3, base_delay=0) == "ok"
    assert calls["n"] == 3


def test_with_retries_raises_after_exhaustion():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise TimeoutError("down")

    with pytest.raises(TimeoutError):
        with_retries(always_fails, max_retries=2, base_delay=0)
    assert calls["n"] == 3  # initial + 2 retries
