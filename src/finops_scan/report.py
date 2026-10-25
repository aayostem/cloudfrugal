"""
Turns a list of CheckResult objects into founder-readable output.
No check module formats its own findings — this is the only place output
shape gets decided, so the report stays consistent as checks are added.
"""
from __future__ import annotations

import json
from datetime import date

from finops_scan.checks.base import CheckResult

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def render_markdown(account_id: str, region: str, results: list[CheckResult]) -> str:
    all_findings = [f for r in results for f in r.findings]
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    ran = [r for r in results if r.ran]
    skipped = [r for r in results if not r.ran]

    lines: list[str] = []
    lines.append(f"# finops-scan report — account {account_id} — {region} — {date.today().isoformat()}")
    lines.append("")
    lines.append(f"{len(ran)} checks run. {len(all_findings)} finding(s).")
    if skipped:
        lines.append(f"{len(skipped)} check(s) skipped (see bottom of report).")
    lines.append("")

    if not all_findings:
        lines.append("No findings from the checks that ran. Either this account is clean on "
                      "these specific checks, or it's a good sign to run "
                      "`--include-cluster-checks` once that's available — see README.")
    else:
        total_monthly = sum(
            f.monthly_cost_estimate for f in all_findings if f.monthly_cost_estimate
        )
        for f in all_findings:
            cost_str = f" — est. ${f.monthly_cost_estimate:,.2f}/month recoverable" if f.monthly_cost_estimate else ""
            lines.append(f"**{f.severity}** `[{f.check_id}]` {f.message}{cost_str}")
            if f.remediation_phase:
                lines.append(f"  Fix: `{f.remediation_phase}`")
            lines.append("")
        if total_monthly:
            lines.append(f"**Estimated recoverable waste from this scan: ${total_monthly:,.2f}/month "
                          f"(${total_monthly * 12:,.2f}/year)**")
            lines.append("")
            lines.append("_Estimates use approximate list pricing for triage — treat as a "
                          "starting point for prioritization, not an invoice._")

    if skipped:
        lines.append("")
        lines.append("## Skipped checks")
        for r in skipped:
            lines.append(f"- `{r.check_id}`: {r.skip_reason}")

    return "\n".join(lines)


def render_json(account_id: str, region: str, results: list[CheckResult]) -> str:
    payload = {
        "account_id": account_id,
        "region": region,
        "date": date.today().isoformat(),
        "results": [
            {
                "check_id": r.check_id,
                "ran": r.ran,
                "skip_reason": r.skip_reason,
                "findings": [
                    {
                        "severity": f.severity,
                        "check_id": f.check_id,
                        "message": f.message,
                        "monthly_cost_estimate": f.monthly_cost_estimate,
                        "remediation_phase": f.remediation_phase,
                        "detail": f.detail,
                    }
                    for f in r.findings
                ],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)
