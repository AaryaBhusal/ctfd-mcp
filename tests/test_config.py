"""Config loading tests (ruff: ignore E402 for sys.path adjustment)."""

# ruff: noqa: E402

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (SRC, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ctfd_mcp.config import load_config


def _load_with_env(env: dict[str, str]):
    """Load config with isolated env and no .env side effects."""
    with patch("ctfd_mcp.config.load_dotenv", return_value=None):
        with patch.dict(os.environ, env, clear=True):
            return load_config()


class ConfigPrecedenceTests(unittest.TestCase):
    def test_username_password_take_priority(self):
        env = {
            "CTFD_URL": "https://ctfd.example.com",
            "CTFD_USERNAME": "user1",
            "CTFD_PASSWORD": "pw1",
            "CTFD_TOKEN": "token-should-be-ignored",
            "CTFD_SESSION": "session-should-be-ignored",
            "CTFD_CSRF_TOKEN": "csrf-should-be-ignored",
        }
        cfg = _load_with_env(env)
        self.assertEqual(cfg.username, "user1")
        self.assertEqual(cfg.password, "pw1")
        self.assertIsNone(cfg.token)
        self.assertIsNone(cfg.session_cookie)
        self.assertIsNone(cfg.csrf_token)

    def test_token_beats_session_cookie(self):
        env = {
            "CTFD_URL": "https://ctfd.example.com",
            "CTFD_TOKEN": "use-this-token",
            "CTFD_SESSION": "drop-this-session",
            "CTFD_CSRF_TOKEN": "csrf-should-be-ignored",
        }
        cfg = _load_with_env(env)
        self.assertEqual(cfg.token, "use-this-token")
        self.assertIsNone(cfg.session_cookie)
        self.assertIsNone(cfg.csrf_token)

    def test_session_cookie_when_no_other_creds(self):
        env = {
            "CTFD_URL": "https://ctfd.example.com",
            "CTFD_SESSION": "session-only",
        }
        cfg = _load_with_env(env)
        self.assertEqual(cfg.session_cookie, "session-only")
        self.assertIsNone(cfg.token)
        self.assertIsNone(cfg.username)
        self.assertIsNone(cfg.password)


if __name__ == "__main__":
    unittest.main()
