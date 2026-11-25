import logging
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from multicaptcha.browser.manager import BrowserManager
from multicaptcha.config import Settings
from multicaptcha.core.errors import SolverError
from multicaptcha.core.models import SolveFailure, SolveRequest, SolveSuccess
from multicaptcha.core.service import SolveService
from multicaptcha.solvers.registry import build_solvers
from multicaptcha.transcribers.registry import build_transcribers

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, service: SolveService | None = None) -> FastAPI:
    """`service` can be injected for tests; otherwise it is built at startup."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if service is not None:
            app.state.service = service
            yield
            return
        logging.basicConfig(level=settings.log_level.upper())
        browser = BrowserManager(settings.browser_headless)
        transcribers = build_transcribers(settings)
        try:
            await browser.start()
            for transcriber in transcribers.values():
                await transcriber.start()
            app.state.service = SolveService(
                build_solvers(browser, transcribers),
                settings.max_concurrent_solves,
                settings.solve_timeout_seconds,
            )
            yield
        finally:
            for transcriber in transcribers.values():
                await transcriber.stop()
            await browser.stop()

    app = FastAPI(title="MultiCaptchasolver", lifespan=lifespan)

    def require_api_key(x_api_key: str = Header(default="")) -> None:
        expected = settings.api_key
        if expected and not secrets.compare_digest(x_api_key.encode(), expected.encode()):
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.exception_handler(SolverError)
    async def on_solver_error(_: Request, error: SolverError) -> JSONResponse:
        log.warning("Solve failed [%s]: %s", error.code, error)
        body = SolveFailure(code=error.code, message=str(error))
        return JSONResponse(status_code=error.status, content=body.model_dump())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/solve", dependencies=[Depends(require_api_key)])
    async def solve(payload: SolveRequest, request: Request) -> SolveSuccess:
        started = time.monotonic()
        token = await request.app.state.service.solve(payload)
        elapsed = round(time.monotonic() - started, 2)
        log.info("Solved %s in %.2fs", payload.type, elapsed)
        return SolveSuccess(type=payload.type, token=token, elapsed_seconds=elapsed)

    return app
