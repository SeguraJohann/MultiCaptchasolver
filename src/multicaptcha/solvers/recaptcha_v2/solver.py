import logging
from collections.abc import Mapping

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from multicaptcha.browser.manager import BrowserManager
from multicaptcha.core.errors import AttemptsExhaustedError, SolverError, SolveTimeoutError
from multicaptcha.core.models import RecaptchaV2Request
from multicaptcha.solvers.base import CaptchaSolver
from multicaptcha.solvers.recaptcha_v2.answer import normalize_answer
from multicaptcha.solvers.recaptcha_v2.widget import RecaptchaV2Widget, State
from multicaptcha.transcribers.base import Transcriber, TranscriberName

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 4


class RecaptchaV2Solver(CaptchaSolver[RecaptchaV2Request]):
    def __init__(
        self, browser: BrowserManager, transcribers: Mapping[TranscriberName, Transcriber]
    ) -> None:
        self._browser = browser
        self._transcribers = transcribers

    async def solve(self, request: RecaptchaV2Request) -> str:
        transcriber = self._transcribers[request.transcriber]
        try:
            async with self._browser.page(request.proxy) as page:
                widget = RecaptchaV2Widget(page)
                await widget.load(request.url, request.sitekey)
                if await widget.click_checkbox() is State.SOLVED:
                    return await widget.token()
                return await self._solve_audio(widget, transcriber)
        except PlaywrightTimeoutError as e:
            raise SolveTimeoutError("Timed out interacting with the reCAPTCHA widget") from e
        except PlaywrightError as e:
            raise SolverError(f"Browser error: {e.message}") from e

    async def _solve_audio(self, widget: RecaptchaV2Widget, transcriber: Transcriber) -> str:
        audio_url = await widget.open_audio()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            audio = await widget.download_audio(audio_url)
            answer = normalize_answer(await transcriber.transcribe(audio))
            log.info("Attempt %d/%d: %r", attempt, MAX_ATTEMPTS, answer)
            state = await widget.submit(answer, audio_url) if answer else State.REJECTED
            if state is State.SOLVED:
                return await widget.token()
            if attempt == MAX_ATTEMPTS:
                break
            if state is State.NEW_AUDIO:
                audio_url = await widget.audio_src() or audio_url
            else:
                audio_url = await widget.reload_audio(audio_url)
        raise AttemptsExhaustedError(f"Not solved after {MAX_ATTEMPTS} attempts")
