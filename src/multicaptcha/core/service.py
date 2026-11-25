import asyncio
from collections.abc import Mapping

from multicaptcha.core.errors import SolveTimeoutError
from multicaptcha.core.models import BaseSolveRequest
from multicaptcha.solvers.base import CaptchaSolver


class SolveService:
    """Dispatches to the right solver, limiting concurrency and total time."""

    def __init__(
        self, solvers: Mapping[str, CaptchaSolver], max_concurrent: int, timeout: float
    ) -> None:
        self._solvers = solvers
        self._slots = asyncio.Semaphore(max_concurrent)
        self._timeout = timeout

    async def solve(self, request: BaseSolveRequest) -> str:
        try:
            # Time spent queueing counts towards the timeout.
            async with asyncio.timeout(self._timeout), self._slots:
                return await self._solvers[request.type].solve(request)
        except TimeoutError as e:
            raise SolveTimeoutError(f"Not solved within {self._timeout:g}s") from e
