#!/usr/bin/env python3
"""Diagnose whether Playwright can attach to the local Chrome CDP endpoint."""

from __future__ import annotations

import argparse
import asyncio
import sys

from playwright.async_api import async_playwright

from cdp_helper import connect_browser_over_cdp, fetch_cdp_browser_info


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    base_url = args.base_url

    try:
        info = fetch_cdp_browser_info(base_url=base_url) if base_url else fetch_cdp_browser_info()
    except Exception as exc:
        if not args.quiet:
            print(f"CDP元数据获取失败: {exc}")
        return 1

    if not args.quiet:
        print(f"Browser: {info['browser']}")
        print(f"Protocol: {info['protocol_version']}")
        print(f"Endpoint: {info['websocket_url'] or info['base_url']}")

    try:
        async with async_playwright() as playwright:
            browser, info = (
                await connect_browser_over_cdp(playwright, base_url=base_url)
                if base_url
                else await connect_browser_over_cdp(playwright)
            )
            contexts = len(browser.contexts)
            pages = len(browser.contexts[0].pages) if browser.contexts else 0
            if not args.quiet:
                print(f"CDP连接成功: contexts={contexts} pages={pages}")
    except Exception as exc:
        if not args.quiet:
            print(f"CDP连接失败: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
