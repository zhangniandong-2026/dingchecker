#!/usr/bin/env python3
"""Helpers for connecting to Chrome over CDP."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.request


def get_cdp_base_url() -> str:
    """Return the configured local CDP endpoint."""
    port = os.environ.get("DINGCHECK_CDP_PORT", "9222")
    host = os.environ.get("DINGCHECK_CDP_HOST", "127.0.0.1")
    return f"http://{host}:{port}"


CDP_BASE_URL = get_cdp_base_url()
CDP_CONNECT_TIMEOUT_SECONDS = 15


def fetch_cdp_browser_info(base_url: str = CDP_BASE_URL) -> dict:
    """Fetch Chrome debug metadata from the local CDP endpoint."""
    version_url = f"{base_url}/json/version"
    with urllib.request.urlopen(version_url, timeout=5) as response:
        payload = json.load(response)

    return {
        "base_url": base_url,
        "browser": payload.get("Browser", "unknown"),
        "protocol_version": payload.get("Protocol-Version", "unknown"),
        "websocket_url": payload.get("webSocketDebuggerUrl", ""),
    }


async def connect_browser_over_cdp(playwright, base_url: str = CDP_BASE_URL, timeout_seconds: int = CDP_CONNECT_TIMEOUT_SECONDS):
    """Connect to Chrome over CDP with an explicit timeout and diagnostics."""
    info = fetch_cdp_browser_info(base_url)
    endpoint = info["websocket_url"] or info["base_url"]

    try:
        browser = await asyncio.wait_for(
            playwright.chromium.connect_over_cdp(endpoint),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        raise RuntimeError(
            "连接 Chrome CDP 超时（>{timeout}s）。Browser={browser} Protocol={protocol} Endpoint={endpoint}".format(
                timeout=timeout_seconds,
                browser=info["browser"],
                protocol=info["protocol_version"],
                endpoint=endpoint,
            )
        ) from exc

    return browser, info
