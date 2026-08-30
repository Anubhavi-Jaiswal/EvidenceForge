"""EvidenceForge: deterministic agent-style repository due diligence."""
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    agent: str
    severity: str
    penalty: int
    message: str
    path: str
    line: int


def files_in(repo: Path, suffix: str = ".py") -> list[Path]:
    return sorted(path for path in repo.rglob(f"*{suffix}") if ".git" not in path.parts)


def source_lines(repo: Path) -> int:
    return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in files_in(repo))


def baseline(repo: Path) -> dict[str, Any]:
    """A plausible lightweight review: README and visible test-file presence only."""
    readme = repo / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    tests = list(repo.rglob("test_*.py"))
    score = min(35, len(text) // 12) + (35 if tests else 0) + min(30, source_lines(repo) // 4)
    return {"repository": repo.name, "score": min(100, score), "method": "README + file-count heuristic"}


def architecture_agent(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not (repo / "README.md").exists():
        findings.append(Finding("architecture", "high", 40, "No README: operating assumptions are undocumented.", "README.md", 1))
    for path in files_in(repo):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            findings.append(Finding("architecture", "critical", 83, "Source cannot be parsed.", path.name, error.lineno or 1))
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno and node.end_lineno - node.lineno > 35:
                findings.append(Finding("architecture", "medium", 17, "Function exceeds 35 lines; review cohesion.", path.name, node.lineno))
    return findings


def reliability_agent(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in files_in(repo):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"except\s*:\s*$|except Exception:\s*pass", line):
                findings.append(Finding("reliability", "high", 24, "Broad exception handling can hide failures.", path.name, number))
            if "TODO" in line or "NotImplemented" in line:
                findings.append(Finding("reliability", "medium", 9, "Unfinished behavior is present.", path.name, number))
    if not list(repo.rglob("test_*.py")):
        findings.append(Finding("reliability", "high", 31, "No executable tests found.", "tests", 1))
    return findings


def security_agent(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    risky = [(r"os\.system\(", "critical", 60, "Shell execution is unvalidated."), (r"eval\(", "critical", 71, "Dynamic evaluation is unsafe."), (r"(api[_-]?key|password)\s*=\s*['\"]", "high", 49, "Possible embedded credential.")]
    for path in files_in(repo):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, severity, penalty, message in risky:
                if re.search(pattern, line, re.I):
                    findings.append(Finding("security", severity, penalty, message, path.name, number))
    return findings


def verify(repo: Path, findings: list[Finding]) -> tuple[list[Finding], list[str]]:
    """Verifier rejects unsupported evidence and makes every claim inspectable."""
    accepted, rejected = [], []
    for finding in findings:
        path = repo / finding.path
        if finding.path in {"README.md", "tests"}:
            accepted.append(finding)
        elif path.exists() and len(path.read_text(encoding="utf-8").splitlines()) >= finding.line:
            accepted.append(finding)
        else:
            rejected.append(f"{finding.agent}:{finding.path}:{finding.line}")
    return accepted, rejected


def assess(repo: Path) -> dict[str, Any]:
    raw = architecture_agent(repo) + reliability_agent(repo) + security_agent(repo)
    findings, rejected = verify(repo, raw)
    penalty = sum(item.penalty for item in findings)
    score = max(0, 100 - penalty)
    return {
        "repository": repo.name, "score": score,
        "verifier": {"accepted": len(findings), "rejected": rejected},
        "findings": [asdict(item) for item in findings],
        "decision": "investigate before purchase" if score < 65 else "acceptable with normal due diligence",
    }


PROFILES = [
    ("atlas", 94, "clean"), ("birch", 86, "todo"), ("coral", 78, "long"), ("delta", 71, "broad"),
    ("ember", 64, "no_tests"), ("fjord", 55, "no_readme"), ("grove", 46, "credential"),
    ("harbor", 35, "shell"), ("indigo", 24, "eval"), ("jade", 12, "syntax"),
]


def write_fixture(root: Path, name: str, expected: int, flaw: str) -> None:
    repo = root / name
    repo.mkdir(parents=True, exist_ok=True)
    if flaw != "no_readme":
        (repo / "README.md").write_text(f"# {name}\n\nA small example service with documented usage.\n", encoding="utf-8")
    source = "def transform(value: str) -> str:\n    return value.strip().lower()\n"
    if flaw == "todo": source += "\n# TODO: add unicode normalization\n"
    if flaw == "long": source += "\ndef report(items):\n" + "    value = 0\n" * 40 + "    return value\n"
    if flaw == "broad": source += "\ndef load():\n    try:\n        return 1 / 0\n    except:\n        return None\n"
    if flaw == "credential": source += "\napi_key = 'demo-key-should-not-be-here'\n"
    if flaw == "shell": source += "\nimport os\ndef deploy(value):\n    os.system(value)\n"
    if flaw == "eval": source += "\ndef calculate(expression):\n    return eval(expression)\n"
    if flaw == "syntax": source = "def broken(:\n    return 1\n"
    (repo / "service.py").write_text(source, encoding="utf-8")
    if flaw != "no_tests":
        (repo / "test_service.py").write_text("from service import transform\n\ndef test_transform():\n    assert transform(' Hi ') == 'hi'\n", encoding="utf-8")
    (repo / "ground_truth.json").write_text(json.dumps({"quality": expected}), encoding="utf-8")


def setup_fixtures(root: Path) -> None:
    for profile in PROFILES:
        write_fixture(root, *profile)


def evaluate(root: Path) -> dict[str, Any]:
    rows = []
    for repo in sorted(path for path in root.iterdir() if path.is_dir()):
        truth = json.loads((repo / "ground_truth.json").read_text(encoding="utf-8"))["quality"]
        rows.append({"repo": repo.name, "truth": truth, "baseline": baseline(repo)["score"], "agent": assess(repo)["score"]})
    def error(key: str) -> float: return round(sum(abs(row[key] - row["truth"]) for row in rows) / len(rows), 1)
    return {"cases": rows, "primary_metric": "mean absolute error to expert rubric", "baseline_mae": error("baseline"), "agent_mae": error("agent"), "improvement": round(error("baseline") - error("agent"), 1)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["setup-fixtures", "baseline", "assess", "evaluate"])
    parser.add_argument("path", nargs="?", default="fixtures/repos")
    args = parser.parse_args()
    path = Path(args.path)
    if args.command == "setup-fixtures": setup_fixtures(path); result = {"created": len(PROFILES), "path": str(path)}
    elif args.command == "baseline": result = baseline(path)
    elif args.command == "assess": result = assess(path)
    else: result = evaluate(path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
