"""Deterministic routing rule types and matching.

- keyword: trigger if the message contains any of `pattern` (case-insensitive)
- regex: trigger if the message matches `pattern`
- semantic: trigger if the message contains any of `pattern` trigger phrases
  (a cheap substring heuristic today; upgradeable to embedding similarity
  without changing the Rule shape)
- always: the agent responds to every *human* message (e.g. a generalist
  or orchestrator). Recursive re-dispatch of another agent's reply does
  not rematch `always`. That would bounce forever.
- mention_only: the agent only responds to an explicit @mention, never via
  dispatch matching
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class RuleType(StrEnum):
    KEYWORD = "keyword"
    REGEX = "regex"
    SEMANTIC = "semantic"
    ALWAYS = "always"
    MENTION_ONLY = "mention_only"


@dataclass(frozen=True, slots=True)
class Rule:
    rule_type: RuleType
    # Unused for ALWAYS/MENTION_ONLY, hence the default.
    pattern: list[str] | str = ""
    priority: int = 0


def is_valid_regex(pattern: str) -> bool:
    """True iff `pattern` compiles as a Python regex."""
    try:
        re.compile(pattern)
    except re.error:
        return False
    return True


# Everyday / garbage messages a specialist must not claim. A generated
# regex that hits any of these is a catch-all (Writer's "word + number"
# landmine matched `xqzplm wibble-frob 9f3k`).
_BROAD_REGEX_PROBES: tuple[str, ...] = (
    "xqzplm wibble-frob 9f3k",
    "How are you all doing today?",
    "ok thanks",
    "hello",
    "yes",
)


def is_overly_broad_regex(pattern: str) -> bool:
    """True when `pattern` compiles but would fire on ordinary chat or nonsense."""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return False
    if compiled.search(""):
        return True
    return any(compiled.search(probe) is not None for probe in _BROAD_REGEX_PROBES)


def rule_matches(rule: Rule, message: str) -> bool:
    """Evaluate a single rule against a message. Pure and side-effect free."""
    match rule.rule_type:
        case RuleType.ALWAYS:
            return True
        case RuleType.MENTION_ONLY:
            return False
        case RuleType.KEYWORD:
            keywords = rule.pattern if isinstance(rule.pattern, list) else [rule.pattern]
            lowered = message.lower()
            return any(kw.lower() in lowered for kw in keywords)
        case RuleType.REGEX:
            pattern = rule.pattern if isinstance(rule.pattern, str) else rule.pattern[0]
            try:
                return re.search(pattern, message) is not None
            except re.error:
                logger.warning(
                    "Invalid regex routing rule pattern %r; treating as no-match", pattern
                )
                return False
        case RuleType.SEMANTIC:
            phrases = rule.pattern if isinstance(rule.pattern, list) else [rule.pattern]
            lowered = message.lower()
            return any(phrase.lower() in lowered for phrase in phrases)
