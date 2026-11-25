import asyncio

import pytest
from fastapi.testclient import TestClient

from multicaptcha.api.app import create_app
from multicaptcha.config import Settings
from multicaptcha.core.errors import ChallengeBlockedError
from multicaptcha.core.service import SolveService
from multicaptcha.solvers.base import CaptchaSolver

BODY = {"type": "recaptcha_v2", "url": "https://example.com", "sitekey": "a" * 40}


class FakeSolver(CaptchaSolver):
    def __init__(self, error=None, delay=0):
        self.error, self.delay = error, delay

    async def solve(self, request):
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return "TOKEN"


def client(solver=None, api_key="", timeout=5):
    service = SolveService({"recaptcha_v2": solver or FakeSolver()}, 1, timeout)
    return TestClient(create_app(Settings(_env_file=None, api_key=api_key), service))


def test_success():
    with client() as c:
        r = c.post("/solve", json=BODY)
    assert r.status_code == 200 and r.json()["token"] == "TOKEN"


@pytest.mark.parametrize(
    "change",
    [{"type": "nope"}, {"transcriber": "nope"}, {"url": "file:///x"}, {"sitekey": '"><script>'}],
)
def test_validation(change):
    with client() as c:
        assert c.post("/solve", json=BODY | change).status_code == 422


def test_api_key():
    with client(api_key="k") as c:
        assert c.post("/solve", json=BODY).status_code == 401
        assert c.post("/solve", json=BODY, headers={"X-API-Key": "k"}).status_code == 200


def test_solver_error_mapping():
    with client(FakeSolver(error=ChallengeBlockedError("no"))) as c:
        r = c.post("/solve", json=BODY)
    assert r.status_code == 503 and r.json()["code"] == "challenge_blocked"


def test_timeout():
    with client(FakeSolver(delay=1), timeout=0.05) as c:
        r = c.post("/solve", json=BODY)
    assert r.status_code == 504 and r.json()["code"] == "timeout"
