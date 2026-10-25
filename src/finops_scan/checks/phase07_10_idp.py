"""
Phases 07-10 (Backstage IDP) maturity has no clean AWS-API-only signal —
it needs the Backstage catalog API, not an AWS read call. Stubbed for the
same reason as phase03_05_cluster.py: an honest "not implemented" beats a
check that quietly checks nothing.
"""
from __future__ import annotations

from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import Check, CheckResult, register


@register
class IdpMaturityCheck(Check):
    id = "idp-maturity"
    phase = "phases/07-idp-fundamentals"
    requires_cluster_access = True

    def run(self, ctx: AwsContext) -> CheckResult:
        return CheckResult(
            check_id=self.id, findings=[], ran=False,
            skip_reason="Requires the Backstage catalog API, not just AWS read access. Not implemented in v1 — see phases/07-idp-fundamentals through 10-finops-idp-integration.",
        )
