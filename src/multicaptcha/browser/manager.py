from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page, Playwright, async_playwright

from multicaptcha.core.models import ProxyConfig


class BrowserManager:
    """One Chromium process; one isolated context per solve."""

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            channel="chromium",  # full browser, also when headless
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = self._playwright = None

    @asynccontextmanager
    async def page(self, proxy: ProxyConfig | None = None) -> AsyncIterator[Page]:
        if self._browser is None:
            raise RuntimeError("BrowserManager not started")
        context = await self._browser.new_context(
            locale="en-US",
            proxy=proxy.model_dump(exclude_none=True) if proxy else None,
        )
        try:
            yield await context.new_page()
        finally:
            await context.close()
