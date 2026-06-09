import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessRunResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class ProcessRunner:
    @staticmethod
    def run(command, *, timeout_seconds, cwd=None, input_text=None):
        start_time = time.monotonic()
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                input=input_text.encode("utf-8") if input_text is not None else None,
                timeout=timeout_seconds,
                creationflags=creationflags,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds") from exc

        duration_ms = int((time.monotonic() - start_time) * 1000)
        return ProcessRunResult(
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
            exit_code=completed.returncode,
            duration_ms=duration_ms,
        )
