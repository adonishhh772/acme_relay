from skills.escalation import _score_risk
from skills.triage import PRIORITY_WEIGHT


def test_risk_levels() -> None:
    assert _score_risk([]).value == "Low"
    assert _score_risk([{"priority": "high"}]).value == "High"
    assert (
        _score_risk(
            [{"priority": "medium"}, {"priority": "medium"}, {"priority": "medium"}]
        ).value
        == "Medium"
    )


def test_priority_weights() -> None:
    assert PRIORITY_WEIGHT["critical"] > PRIORITY_WEIGHT["low"]
