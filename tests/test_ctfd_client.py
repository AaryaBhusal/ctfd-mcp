"""CTFd client tests (ruff: ignore E402 for sys.path adjustment)."""

# ruff: noqa: E402

import asyncio
import json
import os
import sys
import types
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (SRC, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Avoid optional dependency issues in the test runner (python-dotenv).
if "dotenv" not in sys.modules:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *_, **__: None)

from ctfd_mcp.config import Config  # type: ignore
from ctfd_mcp.ctfd_client import AuthError, CTFdClient, CTFdClientError  # type: ignore

CTFD_URL = os.getenv("CTFD_URL")
CTFD_USERNAME = os.getenv("CTFD_USERNAME")
CTFD_PASSWORD = os.getenv("CTFD_PASSWORD")
CTFD_TOKEN = os.getenv("CTFD_TOKEN")

CTFD_LIVE = os.getenv("CTFD_LIVE", "")
CTFD_LIVE_CHALLENGE_ID = os.getenv("CTFD_LIVE_CHALLENGE_ID")
CTFD_LIVE_FLAG = os.getenv("CTFD_LIVE_FLAG")


def _has_creds() -> bool:
    # Accept either token or username/password for real CTFd instance.
    return bool(CTFD_URL and (CTFD_TOKEN or (CTFD_USERNAME and CTFD_PASSWORD)))

def _truthy(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class TestCTFdClientLive(unittest.TestCase):
    """Lightweight live tests against the provided CTFd instance."""

    @unittest.skipUnless(
        _truthy(CTFD_LIVE) and _has_creds(),
        "Live tests disabled (set CTFD_LIVE=1 plus CTFD_URL/credentials to enable)",
    )
    def test_list_and_get_challenge(self):
        """Ensure we can reach CTFd and fetch challenge details.

        This is intentionally parameterized to avoid hard-coding a specific CTFd instance,
        challenge id, or flag. For flag submission, provide CTFD_LIVE_CHALLENGE_ID and
        CTFD_LIVE_FLAG.
        """

        async def _run():
            cfg = Config(
                base_url=CTFD_URL,
                token=CTFD_TOKEN,
                username=CTFD_USERNAME,
                password=CTFD_PASSWORD,
            )
            client = CTFdClient(cfg, timeout=None)
            try:
                challenges = await client.list_challenges()
                self.assertIsInstance(challenges, list)
                self.assertGreater(len(challenges), 0, "Expected at least one challenge")

                if CTFD_LIVE_CHALLENGE_ID:
                    challenge_id = int(CTFD_LIVE_CHALLENGE_ID)
                else:
                    # Default to the first challenge returned by the API.
                    challenge_id = int(challenges[0]["id"])

                detail = await client.get_challenge(challenge_id)
                self.assertEqual(detail.get("id"), challenge_id)

                # Optional end-to-end submission (requires knowing a valid flag).
                if CTFD_LIVE_FLAG:
                    result = await client.submit_flag(challenge_id, CTFD_LIVE_FLAG)
                    self.assertIsInstance(result, dict)
                    self.assertIn("status", result)
                    status = result.get("status")
                    self.assertTrue(
                        status is None or isinstance(status, str),
                        f"Unexpected status type: {type(status)}",
                    )
            except AuthError as exc:
                self.fail(f"Auth should not fail with provided creds: {exc}")
            finally:
                await client.aclose()

        asyncio.run(_run())


class TestCTFdClientHelpers(unittest.TestCase):
    def test_k8s_type_detection(self):
        cfg = Config(base_url="https://ctfd.example.com", token="placeholder")
        client = CTFdClient(cfg, timeout=None)
        self.assertTrue(client._is_k8s_type("k8s"))
        self.assertTrue(client._is_k8s_type("dynamic_kubernetes"))
        self.assertFalse(client._is_k8s_type("dynamic_docker"))


class TestStopContainerValidation(unittest.TestCase):
    def test_dynamic_docker_requires_container_id(self):
        cfg = Config(base_url="https://ctfd.example.com", token="placeholder")
        client = CTFdClient(cfg, timeout=None)

        async def fake_get_challenge(self, challenge_id: int):
            return {"type": "dynamic_docker"}

        client.get_challenge = types.MethodType(fake_get_challenge, client)

        async def _run():
            with self.assertRaises(CTFdClientError):
                await client.stop_container(challenge_id=123)

        asyncio.run(_run())


class TestCsrfTokenEnsure(unittest.TestCase):
    def test_submit_flag_ensures_csrf_for_session_cookie(self):
        calls: list[tuple[str, str, str | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(
                (
                    request.method,
                    request.url.path,
                    request.headers.get("CSRF-Token"),
                )
            )
            if request.url.path == "/api/v1/csrf_token":
                return httpx.Response(
                    200, json={"success": True, "data": {"csrf_token": "api-token"}}
                )
            if request.url.path == "/challenges":
                html = '<input type="hidden" name="nonce" value="page-nonce">'
                return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})
            if request.url.path == "/api/v1/challenges/attempt":
                if request.headers.get("CSRF-Token") != "page-nonce":
                    return httpx.Response(403, json={"success": False, "message": "CSRF"})
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": {"status": "correct", "message": "ok"},
                    },
                )
            return httpx.Response(404, json={"success": False, "message": "not found"})

        transport = httpx.MockTransport(handler)
        cfg = Config(
            base_url="https://ctfd.example.com",
            session_cookie="session",
        )
        client = CTFdClient(cfg, timeout=None)

        async def _run():
            await client._client.aclose()
            client._client = httpx.AsyncClient(
                base_url=cfg.base_url,
                headers=client._client.headers,
                cookies=client._client.cookies,
                transport=transport,
                follow_redirects=True,
                http2=False,
            )
            try:
                result = await client.submit_flag(1, "flag{test}")
            finally:
                await client.aclose()
            self.assertEqual(result.get("status"), "correct")

        asyncio.run(_run())

        paths = [p for _, p, _ in calls]
        self.assertIn("/api/v1/csrf_token", paths)
        self.assertIn("/challenges", paths)
        self.assertEqual(paths[-1], "/api/v1/challenges/attempt")
        self.assertEqual(calls[-1][2], "page-nonce")

    def test_submit_flag_refreshes_csrf_on_403_for_session_cookie(self):
        calls: list[tuple[str, str, str | None]] = []
        state = {"refreshed": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(
                (
                    request.method,
                    request.url.path,
                    request.headers.get("CSRF-Token"),
                )
            )
            if request.url.path == "/api/v1/csrf_token":
                state["refreshed"] += 1
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": {"csrf_token": f"api-token-{state['refreshed']}"},
                    },
                )
            if request.url.path == "/challenges":
                html = (
                    '<input type="hidden" name="nonce" '
                    f'value="page-nonce-{state["refreshed"]}">'
                )
                return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})
            if request.url.path == "/api/v1/challenges/attempt":
                if request.headers.get("CSRF-Token") != "page-nonce-1":
                    return httpx.Response(403, json={"success": False, "message": "CSRF"})
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": {"status": "correct", "message": "ok"},
                    },
                )
            return httpx.Response(404, json={"success": False, "message": "not found"})

        transport = httpx.MockTransport(handler)
        cfg = Config(
            base_url="https://ctfd.example.com",
            session_cookie="session",
        )
        client = CTFdClient(cfg, timeout=None)
        client._csrf_token = "stale"

        async def _run():
            await client._client.aclose()
            client._client = httpx.AsyncClient(
                base_url=cfg.base_url,
                headers=client._client.headers,
                cookies=client._client.cookies,
                transport=transport,
                follow_redirects=True,
                http2=False,
            )
            try:
                result = await client.submit_flag(1, "flag{test}")
            finally:
                await client.aclose()
            self.assertEqual(result.get("status"), "correct")

        asyncio.run(_run())

        # Two POSTs: first with stale token, second after refresh.
        post_tokens = [t for m, p, t in calls if m == "POST" and p.endswith("/attempt")]
        self.assertEqual(post_tokens[0], "stale")
        self.assertEqual(post_tokens[-1], "page-nonce-1")


class TestCTFdClientTokenAuthOffline(unittest.TestCase):
    def test_get_and_submit_do_not_require_csrf_for_token_auth(self):
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            self.assertEqual(request.headers.get("Authorization"), "Token test-token")
            self.assertIsNone(request.headers.get("CSRF-Token"))

            if request.url.path == "/api/v1/challenges/123":
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": {
                            "id": 123,
                            "name": "Example",
                            "category": "misc",
                            "value": 100,
                            "description": "<p>hi</p>",
                            "type": "standard",
                            "tags": [],
                            "files": [],
                        },
                    },
                )

            if request.url.path == "/api/v1/challenges/attempt":
                body = json.loads(request.content.decode("utf-8"))
                self.assertEqual(body["challenge_id"], 123)
                self.assertEqual(body["submission"], "flag{test}")
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": {"status": "correct", "message": "ok"},
                    },
                )

            return httpx.Response(404, json={"success": False, "message": "not found"})

        transport = httpx.MockTransport(handler)
        cfg = Config(base_url="https://ctfd.example.com", token="test-token")
        client = CTFdClient(cfg, timeout=None)

        async def _run():
            await client._client.aclose()
            client._client = httpx.AsyncClient(
                base_url=cfg.base_url,
                headers=client._client.headers,
                cookies=client._client.cookies,
                transport=transport,
                follow_redirects=True,
                http2=False,
            )
            try:
                detail = await client.get_challenge(123)
                self.assertEqual(detail.get("id"), 123)
                result = await client.submit_flag(123, "flag{test}")
                self.assertEqual(result.get("status"), "correct")
            finally:
                await client.aclose()

        asyncio.run(_run())

        paths = [p for _, p in calls]
        self.assertEqual(paths, ["/api/v1/challenges/123", "/api/v1/challenges/attempt"])


if __name__ == "__main__":
    unittest.main()
