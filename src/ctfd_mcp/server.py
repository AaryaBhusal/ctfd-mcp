from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import anyio
from mcp.server.fastmcp import FastMCP

from .config import ConfigError, load_config
from .ctfd_client import (
    AuthError,
    CTFdClient,
    CTFdClientError,
    NotFoundError,
    RateLimitError,
)

_client: CTFdClient | None = None


def _format_error(exc: Exception) -> RuntimeError:
    if isinstance(exc, ConfigError):
        message = f"Configuration error: {exc}"
    elif isinstance(exc, AuthError):
        message = f"Auth failed: {exc}"
    elif isinstance(exc, NotFoundError):
        message = f"Not found: {exc}"
    elif isinstance(exc, RateLimitError):
        retry = (
            f" Retry-After={exc.retry_after}."
            if getattr(exc, "retry_after", None)
            else ""
        )
        message = f"Rate limited.{retry}".strip()
    elif isinstance(exc, CTFdClientError):
        message = f"CTFd API error: {exc}"
    else:
        message = f"Unexpected error: {exc}"
    return RuntimeError(message)


async def _close_client() -> None:
    global _client
    if _client is None:
        return
    try:
        await _client.aclose()
    finally:
        _client = None


@asynccontextmanager
async def _lifespan(_: FastMCP):
    try:
        yield
    finally:
        await _close_client()


mcp = FastMCP("ctfd-mcp", lifespan=_lifespan)


async def _get_client() -> CTFdClient:
    global _client
    if _client is None:
        config = load_config()
        _client = CTFdClient(config)
    return _client


@mcp.tool(
    description="List visible challenges. Optional filter by category and unsolved only."
)
async def list_challenges(category: str | None = None, only_unsolved: bool = False):
    client = await _get_client()
    try:
        return await client.list_challenges(
            category=category, only_unsolved=only_unsolved
        )
    except Exception as exc:  # noqa: BLE001 - map to user-friendly MCP error
        raise _format_error(exc)


@mcp.tool(description="Get challenge details (description, files, meta) by ID.")
async def challenge_details(challenge_id: int):
    client = await _get_client()
    try:
        return await client.get_challenge(challenge_id)
    except Exception as exc:  # noqa: BLE001 - map to user-friendly MCP error
        raise _format_error(exc)


@mcp.tool(description="Submit a flag for a challenge ID.")
async def submit_flag(challenge_id: int, flag: str):
    client = await _get_client()
    try:
        return await client.submit_flag(challenge_id, flag)
    except Exception as exc:  # noqa: BLE001 - map to user-friendly MCP error
        raise _format_error(exc)


@mcp.tool(
    description="Unified start: detects plugin (whale/ctfd-owl/k8s) and starts container."
)
async def start_container(challenge_id: int):
    client = await _get_client()
    try:
        return await client.start_container(challenge_id)
    except Exception as exc:  # noqa: BLE001
        raise _format_error(exc)


@mcp.tool(
    description="Unified stop: whale requires container_id; ctfd-owl/k8s require challenge_id."
)
async def stop_container(
    container_id: int | None = None, challenge_id: int | None = None
):
    client = await _get_client()
    try:
        return await client.stop_container(
            container_id=container_id, challenge_id=challenge_id
        )
    except Exception as exc:  # noqa: BLE001
        raise _format_error(exc)


@mcp.resource(
    "resource://ctfd/challenges/{challenge_id}",
    name="ctfd-challenge",
    title="CTFd challenge details",
    description="Challenge description plus attachment URLs.",
    mime_type="text/markdown",
)
async def challenge_resource(challenge_id: int):
    client = await _get_client()
    try:
        details = await client.get_challenge(challenge_id)
    except Exception as exc:  # noqa: BLE001
        raise _format_error(exc)
    return _challenge_markdown(details)


def _challenge_markdown(details: dict[str, Any]) -> str:
    """Render a chat-friendly markdown snapshot of a challenge."""
    lines: list[str] = []
    title = details.get("name") or f"Challenge {details.get('id')}"
    lines.append(f"# {title}")
    subtitle: list[str] = []
    if details.get("id") is not None:
        subtitle.append(f"ID: {details['id']}")
    if details.get("category"):
        subtitle.append(f"Category: {details['category']}")
    if details.get("value") is not None:
        subtitle.append(f"Points: {details['value']}")
    if details.get("solved") is not None:
        subtitle.append("Solved" if details["solved"] else "Unsolved")
    if subtitle:
        lines.append(" / ".join(subtitle))

    desc = (details.get("description_text") or details.get("description") or "").strip()
    if desc:
        lines.append("")
        lines.append("## Description")
        lines.append(desc)

    conn = details.get("connection_info")
    if conn:
        lines.append("")
        lines.append("## Connection")
        lines.append(str(conn))

    files = details.get("files") or []
    if files:
        lines.append("")
        lines.append("## Files")
        lines.extend(f"- {url}" for url in files)

    return "\n".join(lines).strip() or "No challenge details available."


def run(transport: str = "stdio") -> None:
    """Start the MCP server."""
    if transport == "stdio":
        anyio.run(_run_stdio_with_lifecycle)
        return
    mcp.run(transport=transport)


async def _run_stdio_with_lifecycle() -> None:
    async with _lifespan(mcp):
        await mcp.run_stdio_async()
