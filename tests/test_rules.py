from rivulet_dispatch.rules import (
    Rule,
    RuleType,
    is_overly_broad_regex,
    is_valid_regex,
    rule_matches,
)

_BAD_REGEX = r"\b(https?://[\w-]+(\.[\w-]+)+(\/[\w- ./?%&=]*)?)"


def test_regex_rule_matches() -> None:
    rule = Rule(RuleType.REGEX, r"ORD-\d+")
    assert rule_matches(rule, "status of ORD-4821?") is True
    assert rule_matches(rule, "no order number here") is False


def test_invalid_regex_rule_never_raises_and_treated_as_no_match() -> None:
    rule = Rule(RuleType.REGEX, _BAD_REGEX)
    assert rule_matches(rule, "check out https://example.com/path") is False
    assert rule_matches(rule, "hello") is False


def test_is_valid_regex() -> None:
    assert is_valid_regex(r"ORD-\d+") is True
    assert is_valid_regex(_BAD_REGEX) is False


def test_is_overly_broad_regex() -> None:
    writer_catchall = r"(?i)(\d{5}-\d{4}|[a-zA-Z]{2,}\s?\d{1,3})"
    assert is_overly_broad_regex(writer_catchall) is True
    assert is_overly_broad_regex(r".*") is True
    assert is_overly_broad_regex(r"ORD-\d+") is False
    assert is_overly_broad_regex(r"https?://[^\s]+") is False
    assert is_overly_broad_regex(_BAD_REGEX) is False


def test_mention_only_rule_never_matches_via_rule_matching() -> None:
    rule = Rule(RuleType.MENTION_ONLY)
    assert rule_matches(rule, "hey can you help me?") is False
    assert rule_matches(rule, "") is False


def test_semantic_rule_matches_any_configured_phrase() -> None:
    rule = Rule(RuleType.SEMANTIC, ["order status", "where is my package"])
    assert rule_matches(rule, "Can you tell me my order status please?") is True
    assert rule_matches(rule, "WHERE IS MY PACKAGE") is True
    assert rule_matches(rule, "what's the weather like") is False


def test_semantic_rule_accepts_a_single_string_pattern_too() -> None:
    rule = Rule(RuleType.SEMANTIC, "refund")
    assert rule_matches(rule, "I'd like a refund please") is True
    assert rule_matches(rule, "hello") is False
