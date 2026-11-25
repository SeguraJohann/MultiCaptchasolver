"""Maps a request `type` to its solver. New captcha types are registered here."""

from collections.abc import Mapping

from multicaptcha.browser.manager import BrowserManager
from multicaptcha.solvers.base import CaptchaSolver
from multicaptcha.solvers.recaptcha_v2.solver import RecaptchaV2Solver
from multicaptcha.transcribers.base import Transcriber, TranscriberName


def build_solvers(
    browser: BrowserManager, transcribers: Mapping[TranscriberName, Transcriber]
) -> dict[str, CaptchaSolver]:
    return {"recaptcha_v2": RecaptchaV2Solver(browser, transcribers)}
