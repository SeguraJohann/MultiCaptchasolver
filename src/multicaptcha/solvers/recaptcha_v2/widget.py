"""Page object for the reCAPTCHA v2 widget: all selectors live here."""

import time
from enum import Enum, auto

from playwright.async_api import Page

from multicaptcha.browser.widget_page import open_widget_page
from multicaptcha.core.errors import (
    ChallengeBlockedError,
    InvalidSitekeyError,
    SolverError,
    SolveTimeoutError,
)

STEP_TIMEOUT_MS = 15_000
POLL_MS = 150

HTML = """<!DOCTYPE html><html><head>
<script src="https://www.google.com/recaptcha/api.js?hl=en" async defer></script>
</head><body><div class="g-recaptcha" data-sitekey="{sitekey}"></div></body></html>"""


class State(Enum):
    SOLVED = auto()
    CHALLENGE = auto()
    REJECTED = auto()
    NEW_AUDIO = auto()


class RecaptchaV2Widget:
    def __init__(self, page: Page) -> None:
        self._page = page
        self._anchor = page.frame_locator('iframe[src*="/recaptcha/api2/anchor"]')
        self._bframe = page.frame_locator('iframe[src*="/recaptcha/api2/bframe"]')

    async def load(self, url: str, sitekey: str) -> None:
        await open_widget_page(self._page, url, HTML.format(sitekey=sitekey))
        # An invalid sitekey replaces the checkbox with an error message.
        checkbox = self._anchor.locator("#recaptcha-anchor:visible")
        error = self._anchor.locator(".rc-anchor-error-message:visible")
        await checkbox.or_(error).first.wait_for(timeout=STEP_TIMEOUT_MS)
        if await error.count():
            raise InvalidSitekeyError((await error.first.inner_text()).strip())

    async def click_checkbox(self) -> State:
        await self._anchor.locator("#recaptcha-anchor").click(timeout=STEP_TIMEOUT_MS)
        button = self._bframe.locator("#recaptcha-audio-button")

        async def check() -> State | None:
            if await self.token():
                return State.SOLVED
            await self._raise_if_blocked()
            return State.CHALLENGE if await button.is_visible() else None

        return await self._poll(check, "challenge")

    async def open_audio(self) -> str:
        await self._bframe.locator("#recaptcha-audio-button").click(timeout=STEP_TIMEOUT_MS)
        return await self._wait_audio(previous=None)

    async def reload_audio(self, previous: str) -> str:
        await self._bframe.locator("#recaptcha-reload-button").click(timeout=STEP_TIMEOUT_MS)
        return await self._wait_audio(previous)

    async def download_audio(self, audio_url: str) -> bytes:
        response = await self._page.context.request.get(audio_url, timeout=STEP_TIMEOUT_MS)
        if not response.ok:
            raise SolverError(f"Audio download failed: HTTP {response.status}")
        return await response.body()

    async def submit(self, answer: str, audio_url: str) -> State:
        await self._bframe.locator("#audio-response").fill(answer)
        await self._bframe.locator("#recaptcha-verify-button").click(timeout=STEP_TIMEOUT_MS)
        error = self._bframe.locator(".rc-audiochallenge-error-message")

        async def check() -> State | None:
            if await self.token():
                return State.SOLVED
            await self._raise_if_blocked()
            src = await self.audio_src()
            if src and src != audio_url:
                return State.NEW_AUDIO
            return State.REJECTED if await error.is_visible() else None

        return await self._poll(check, "verification result")

    async def token(self) -> str:
        field = self._page.locator('textarea[name="g-recaptcha-response"]')
        return await field.input_value() if await field.count() else ""

    async def audio_src(self) -> str | None:
        source = self._bframe.locator("#audio-source")
        return await source.get_attribute("src") if await source.count() else None

    async def _wait_audio(self, previous: str | None) -> str:
        async def check() -> str | None:
            await self._raise_if_blocked()
            src = await self.audio_src()
            return src if src and src != previous else None

        return await self._poll(check, "audio challenge")

    async def _raise_if_blocked(self) -> None:
        if await self._bframe.locator(".rc-doscaptcha-header").is_visible():
            raise ChallengeBlockedError("reCAPTCHA refused the audio challenge for this IP/browser")

    async def _poll(self, check, what: str):
        deadline = time.monotonic() + STEP_TIMEOUT_MS / 1000
        while time.monotonic() < deadline:
            if result := await check():
                return result
            await self._page.wait_for_timeout(POLL_MS)
        raise SolveTimeoutError(f"Timed out waiting for {what}")
