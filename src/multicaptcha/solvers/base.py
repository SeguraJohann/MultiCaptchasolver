from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from multicaptcha.core.models import BaseSolveRequest

R = TypeVar("R", bound=BaseSolveRequest)


class CaptchaSolver(ABC, Generic[R]):
    @abstractmethod
    async def solve(self, request: R) -> str:
        """Return the response token or raise SolverError."""
