"""
Scoring module for blockchain vulnerability analysis tools.

- Each tool gets a score from 0 (no issues) to 100 (critical/severe issues found).
- The score is based on the number and severity of issues, tool errors, and warnings.
- If a tool provides severity, use it; otherwise, use the count and type of issues.
- Errors or warnings increase the score (worse security).
- The scoring is pessimistic: higher score = more severe findings.
"""

def mythril_score(result: dict) -> int:
    if not result.get("success"):
        return 100  # Tool failed, treat as critical
    vulns = result.get("vulnerabilities", [])
    if not vulns:
        return 0
    # If severity is available, use it; else, use count
    severity_map = {"High": 30, "Medium": 20, "Low": 10}
    score = 0
    for v in vulns:
        sev = v.get("severity", "Medium")
        score += severity_map.get(sev, 20)
    score = min(score, 100)
    return score

def slither_score(result: dict) -> int:
    if not result.get("success"):
        return 100
    detectors = result.get("results", {}).get("detectors", [])
    if not detectors:
        return 0
    # Use the number of issues found
    issue_count = sum(len(d.get("elements", [])) for d in detectors)
    score = min(issue_count * 5, 100)
    return score

def echidna_score(result: dict) -> int:
    if not result.get("success"):
        return 100
    tests = result.get("results", {}).get("tests", [])
    failed = [t for t in tests if t.get("status") == "error"]
    if not failed:
        return 0
    score = min(len(failed) * 20, 100)
    return score

def maian_score(result: dict) -> int:
    if not result.get("success"):
        return 100
    output = result.get("output", "")
    # Heuristic: if output contains 'vulnerable' or 'bug', score high
    if "vulnerable" in output.lower() or "bug" in output.lower():
        return 80
    if output.strip():
        return 40
    return 0

def smartcheck_score(result: dict) -> int:
    if not result.get("success"):
        return 100
    output = result.get("output", "")
    # Heuristic: count 'WARNING' or 'ERROR' in output
    warn_count = output.lower().count("warning")
    err_count = output.lower().count("error")
    score = min((warn_count + err_count) * 10, 100)
    return score

def manticore_score(result: dict) -> int:
    if not result.get("success"):
        return 100
    output = result.get("output", "")
    # Heuristic: look for 'bug', 'crash', or 'vulnerability' in output
    keywords = ["bug", "crash", "vulnerability", "assertion"]
    score = 0
    for k in keywords:
        if k in output.lower():
            score += 25
    return min(score, 100)

def score_result(tool_name: str, result: dict) -> int:
    """
    Generic scoring interface. Returns a score 0-100 for the given tool result.
    """
    if tool_name == "mythril-analyze":
        return mythril_score(result)
    elif tool_name == "slither-analyze":
        return slither_score(result)
    elif tool_name == "echidna-analyze":
        return echidna_score(result)
    elif tool_name == "maian-analyze":
        return maian_score(result)
    elif tool_name == "smartcheck-analyze":
        return smartcheck_score(result)
    elif tool_name == "manticore-analyze":
        return manticore_score(result)
    else:
        # Unknown tool, fallback: 100 if failed, 0 if success
        return 100 if not result.get("success") else 0 