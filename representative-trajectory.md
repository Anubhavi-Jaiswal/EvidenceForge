# Representative trajectory: `harbor`

**Shared guardrail:** Inspect static files only. Do not execute repository code. Cite each claim with a relative path and line.

1. Coordinator assigns architecture, reliability, and security review over `harbor`.
2. Architecture agent reads `README.md` and parses `service.py`; response: no architecture finding.
3. Reliability agent finds `test_service.py`; response: no missing-test finding.
4. Security agent scans `service.py`; tool response includes `service.py:4: os.system(value)`. It returns a critical finding citing that line.
5. Verifier opens the cited file and confirms the fourth line exists. Response: accepted; no rejected claims.
6. Human checkpoint receives the score and cited evidence, then decides whether to investigate, approve, or reject. EvidenceForge makes no external change.

Retry example: if a reviewer returns `missing.py:9`, the verifier rejects it before the result reaches the human reviewer.
