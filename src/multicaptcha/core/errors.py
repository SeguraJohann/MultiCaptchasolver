class SolverError(Exception):
    """Base error. `code` is the stable identifier returned to API clients."""

    code = "solver_error"
    status = 502


class InvalidSitekeyError(SolverError):
    code = "invalid_sitekey"
    status = 422


class ChallengeBlockedError(SolverError):
    """The provider refused to serve a challenge to this browser/IP."""

    code = "challenge_blocked"
    status = 503


class AttemptsExhaustedError(SolverError):
    code = "attempts_exhausted"


class TranscriptionError(SolverError):
    code = "transcription_failed"


class SolveTimeoutError(SolverError):
    code = "timeout"
    status = 504
