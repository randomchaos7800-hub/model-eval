"""Shared configuration for model-eval tools.

Resolution order (highest wins):
  1. CLI arguments
  2. Environment variables (PROXY_URL, MODEL_EVAL_CONFIG)
  3. config.yaml next to this file (or $MODEL_EVAL_CONFIG path)
  4. Built-in defaults

No secrets belong in config.yaml — the judge API key resolves at runtime from
CLI/env/secret command (see `judge_key_command`).
"""

import os
from pathlib import Path

DEFAULTS = {
    "base_url": "http://localhost:8010/v1",
    "model": "local",
    "api_key": "local",
    "output_dir": "./results",
    "request_timeout": 30,       # seconds; probe.py overrides for long generations
    "probe_request_timeout": 180,
    "max_retries": 3,            # exponential backoff: 1s, 2s, 4s
    "judge_key_command": "~/.vault/vault.sh get anthropic_api_key",
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    path = os.environ.get("MODEL_EVAL_CONFIG") or (Path(__file__).parent / "config.yaml")
    path = Path(path).expanduser()
    if path.exists():
        try:
            import yaml
            loaded = yaml.safe_load(path.read_text()) or {}
            if not isinstance(loaded, dict):
                raise ValueError("config.yaml must contain a mapping")
            cfg.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except ImportError:
            pass  # pyyaml not installed — defaults + env + CLI still work
    if os.environ.get("PROXY_URL"):
        cfg["base_url"] = os.environ["PROXY_URL"]
    return cfg


def positive_int(value: str) -> int:
    """argparse type: strictly positive integer."""
    import argparse
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {value!r}")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be > 0, got {n}")
    return n


def http_url(value: str) -> str:
    """argparse type: http(s) URL."""
    import argparse
    if not (value.startswith("http://") or value.startswith("https://")):
        raise argparse.ArgumentTypeError(f"not an http(s) URL: {value!r}")
    return value


def with_retries(fn, max_retries: int = 3, base_delay: float = 1.0):
    """Call fn(); on transient failure retry with exponential backoff (1s, 2s, 4s)."""
    import time
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
    raise last_exc
