# EvidenceForge

EvidenceForge helps a technical buyer make an initial, repeatable quality assessment of an unfamiliar Python repository. A buyer can be misled by a polished README or demo while missing unsafe execution, hidden failure handling, missing tests, or code that cannot run.

The workflow produces evidence for a qualified human reviewer, not an acquisition decision. It uses public synthetic repositories only and never executes code from the assessed repository.

## Workflow

- `baseline`: a fair, intentionally simple README-and-file-count heuristic.
- `assess`: architecture, reliability, and security reviewers, followed by an evidence verifier.
- `evaluate`: a fixed ten-repository benchmark with synthetic expert-quality labels.

Every advanced finding includes a repository-relative file and line. The verifier rejects claims that cannot be traced to an existing source location.

## Reproduction guide

Requires Python 3.11+. No third-party packages, credentials, API calls, or network access are required. Runtime is under one second and cost is $0.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m evidenceforge setup-fixtures fixtures/repos
python -m evidenceforge baseline fixtures/repos/harbor
python -m evidenceforge assess fixtures/repos/harbor
python -m evidenceforge evaluate fixtures/repos
python -m pytest
```

Expected: `harbor` has a critical, file-and-line-linked shell-execution finding; evaluation prints ten cases plus MAE for baseline and final workflow.

## Agent instructions

Architecture: inspect static Python syntax and documentation; report parse errors, absent docs, oversized functions with locations. Reliability: inspect tests and source; report missing tests, broad exceptions, incomplete behavior. Security: statically report shell execution, dynamic evaluation, apparent embedded credentials. Do not execute target code.

Verifier: accept only a finding whose cited repository-relative location exists. A qualified human reviews accepted evidence before any consequential decision.

## Improvement changelog

| Stage | What changed | Evidence | Decision |
| --- | --- | --- | --- |
| Baseline | README + visible test heuristic | Evaluation output | Starting point |
| Iteration 1 | Specialized static reviewers | Different risk categories across fixtures | Kept |
| Iteration 2 | Evidence verifier | `verifier.rejected` checked in tests | Kept |
| Iteration 3 | Tried target test execution | Unsafe/non-deterministic for untrusted repos | Removed |
| Final | Specialized review + verification | Lower MAE than baseline | Kept |

## Main failure mode and hot take

Static inspection can miss semantic business-logic bugs. Hot take: reliable agents come less from adding agents than from making every claim cheaply falsifiable by a human.


