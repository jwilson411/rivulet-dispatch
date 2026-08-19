"""Loop prevention: turn limits, cycle detection, timeout.

In-memory. One LoopGuard instance per conversation. A human message
should call reset(). Thresholds default to the Rivulets workspace
settings: turn_limit=10, cycle_window=8, cycle_threshold=3,
timeout_minutes=30.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, slots=True)
class Pause:
    reason: str
    message: str


TURN_LIMIT_MESSAGE = "Agent conversation has reached the turn limit. Waiting for human input."


@dataclass
class LoopGuard:
    turn_limit: int = 10
    cycle_window: int = 8
    cycle_threshold: int = 3
    timeout_minutes: int = 30
    agent_exchange_count: int = 0
    recent_pairs: list[tuple[str, str]] = field(default_factory=list)
    agent_active_since: datetime | None = None
    paused: bool = False
    pause_reason: str | None = None

    def reset(self) -> None:
        """Any human message resets counters and resumes a paused thread."""
        self.agent_exchange_count = 0
        self.recent_pairs = []
        self.agent_active_since = None
        self.paused = False
        self.pause_reason = None

    def record_agent_message(
        self,
        *,
        from_agent_id: str | None,
        to_agent_id: str,
        now: datetime | None = None,
    ) -> Pause | None:
        """Update counters after an agent is about to speak.

        `from_agent_id` is the previous speaker. None if the triggering
        message was from a human (no agent-to-agent pair to record).
        Returns a Pause if a limit just tripped. The caller must stop
        dispatching further once it gets one back.
        """
        if self.paused:
            return Pause(
                reason=self.pause_reason or "paused",
                message="Thread is already paused. Waiting for human input.",
            )

        clock = now or datetime.now(UTC)
        self.agent_exchange_count += 1
        if self.agent_active_since is None:
            self.agent_active_since = clock

        if from_agent_id is not None:
            self.recent_pairs.append((from_agent_id, to_agent_id))
            self.recent_pairs = self.recent_pairs[-self.cycle_window :]
            if self.recent_pairs.count((from_agent_id, to_agent_id)) >= self.cycle_threshold:
                return self._pause(
                    "cycle_detected",
                    f"Detected a repeating loop between {from_agent_id} and {to_agent_id}; "
                    "pausing until a human responds.",
                )

        if self.agent_exchange_count >= self.turn_limit:
            return self._pause("turn_limit", TURN_LIMIT_MESSAGE)

        if clock - self.agent_active_since > timedelta(minutes=self.timeout_minutes):
            return self._pause(
                "timeout",
                f"Agents have been active for over {self.timeout_minutes} minutes without "
                "human input; pausing until a human responds.",
            )
        return None

    def _pause(self, reason: str, message: str) -> Pause:
        self.paused = True
        self.pause_reason = reason
        return Pause(reason=reason, message=message)
