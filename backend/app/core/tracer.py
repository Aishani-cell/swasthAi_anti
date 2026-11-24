"""
SwasthAI Centralized Pipeline Tracer
====================================

Emits structured, timestamped execution events to the operator terminal
(stdout, i.e. the VS Code terminal) so the entire multi-agent clinical
pipeline can be observed in real time.

Design rules:
- One line per event: [HH:MM:SS] [TRACER] <encounter_id> <component> <stage> <STATUS>
- STATUS is one of: STARTED, COMPLETED, FAILED
- Duration is reported in milliseconds where practical.
- Exceptions are recorded with type and message on FAILED.
- NEVER log patient names, phone numbers, passwords, or raw medical records
  (PII-free by design).
"""
import logging
import sys
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger("swasthai.tracer")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("[%(asctime)s] [TRACER] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_handler)


class Tracer:
    """Centralized tracer utility shared by every pipeline component."""

    def __init__(self) -> None:
        self._start_times: dict[str, float] = {}

    def event(
        self,
        encounter_id: str,
        component: str,
        stage: str,
        status: str,
        detail: str = "",
        duration_ms: Optional[float] = None,
        exception: Optional[BaseException] = None,
    ) -> None:
        """Emit a single tracer event."""
        parts = [
            f"Encounter: {encounter_id or '—'}",
            f"Component: {component}",
            f"Stage: {stage}",
            f"Status: {status}",
        ]
        if detail:
            parts.append(f"Detail: {detail}")
        if duration_ms is not None:
            parts.append(f"Duration: {duration_ms:.0f}ms")
        if exception is not None:
            parts.append(f"Exception: {type(exception).__name__}: {exception}")
        logger.info(" | ".join(parts))

    @contextmanager
    def stage(self, encounter_id: str, component: str, stage_name: str):
        """Context manager that logs STARTED/COMPLETED (or FAILED) around a block."""
        start = time.perf_counter()
        self.event(encounter_id, component, stage_name, "STARTED")
        try:
            yield
        except BaseException as exc:  # noqa: BLE001 - surface every component failure
            self.event(
                encounter_id,
                component,
                stage_name,
                "FAILED",
                duration_ms=(time.perf_counter() - start) * 1000.0,
                exception=exc,
            )
            raise
        self.event(
            encounter_id,
            component,
            stage_name,
            "COMPLETED",
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )


# Shared tracer instance used by all SwasthAI components.
tracer = Tracer()
