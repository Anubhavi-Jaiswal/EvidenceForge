from pathlib import Path

from evidenceforge import assess, baseline, evaluate, setup_fixtures


def test_security_finding_is_evidence_grounded(tmp_path: Path):
    setup_fixtures(tmp_path)
    result = assess(tmp_path / "harbor")
    assert result["verifier"]["rejected"] == []
    assert any(item["severity"] == "critical" for item in result["findings"])


def test_agent_improves_over_baseline(tmp_path: Path):
    setup_fixtures(tmp_path)
    result = evaluate(tmp_path)
    assert len(result["cases"]) == 10
    assert result["agent_mae"] < result["baseline_mae"]


def test_baseline_is_deliberately_shallow(tmp_path: Path):
    setup_fixtures(tmp_path)
    assert abs(baseline(tmp_path / "atlas")["score"] - baseline(tmp_path / "harbor")["score"]) <= 1
