"""Demo: trip the LoopGuard cycle detector.

Run: python examples/loop.py
"""

import sys

from rivulet_dispatch import LoopGuard


def main() -> None:
    guard = LoopGuard(turn_limit=99, cycle_window=8, cycle_threshold=3)
    for _ in range(3):
        pause = guard.record_agent_message(from_agent_id="a", to_agent_id="b")
    assert pause is not None
    print(pause.reason)
    print(pause.message)
    sys.exit(0)


if __name__ == "__main__":
    main()
