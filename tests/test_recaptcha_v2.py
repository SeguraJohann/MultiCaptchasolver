import pytest

from multicaptcha.core.errors import AttemptsExhaustedError
from multicaptcha.solvers.recaptcha_v2 import solver as mod
from multicaptcha.solvers.recaptcha_v2.answer import normalize_answer
from multicaptcha.solvers.recaptcha_v2.widget import State


def test_normalize_answer():
    assert normalize_answer("  Hello, World!\n It's 5. ") == "hello world its 5"


class FakeTranscriber:
    async def transcribe(self, audio):
        return audio.decode()


class FakeWidget:
    def __init__(self, states):
        self.states, self.n, self.submitted = list(states), 0, []

    async def open_audio(self):
        return "audio0"

    async def reload_audio(self, previous):
        self.n += 1
        return f"audio{self.n}"

    async def audio_src(self):
        self.n += 1
        return f"audio{self.n}"

    async def download_audio(self, url):
        return url.encode()

    async def submit(self, answer, url):
        self.submitted.append(answer)
        return self.states.pop(0)

    async def token(self):
        return "TOKEN"


async def solve(widget):
    return await mod.RecaptchaV2Solver(None, {})._solve_audio(widget, FakeTranscriber())


async def test_uses_fresh_audio_after_each_round():
    widget = FakeWidget([State.REJECTED, State.NEW_AUDIO, State.SOLVED])
    assert await solve(widget) == "TOKEN"
    assert widget.submitted == ["audio0", "audio1", "audio2"]


async def test_gives_up():
    with pytest.raises(AttemptsExhaustedError):
        await solve(FakeWidget([State.REJECTED] * mod.MAX_ATTEMPTS))
