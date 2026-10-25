"""
Phases 03 (Kubecost), 04 (Karpenter), 05 (Spot) all need Kubernetes API
access, not just AWS API read access — kubeconfig, a running Kubecost
deployment to query, etc. That's a real setup cost, which is why these
are excluded from finops-scan's default v1 run (see README.md "What it
checks (v1)"). They're registered here, marked `requires_cluster_access`,
so the CLI can still list them as "available with --include-cluster-checks"
once implemented, and so v2 has a slot to drop real logic into without
restructuring the registry.

Deliberately not implemented yet: a stub that pretends to check cluster
state without a working kubeconfig would either fail confusingly or,
worse, report a false "all good" when it silently found nothing to check.
Both are worse than an honest "not implemented."
"""
from __future__ import annotations

from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import Check, CheckResult, register


@register
class KubecostReadinessCheck(Check):
    id = "kubecost-readiness"
    phase = "phases/03-kubecost-eks-visibility"
    requires_cluster_access = True

    def run(self, ctx: AwsContext) -> CheckResult:
        return CheckResult(
            check_id=self.id, findings=[], ran=False,
            skip_reason="Requires a live kubeconfig + running Kubecost deployment. Not implemented in v1 — see phases/03-kubecost-eks-visibility.",
        )


@register
class KarpenterReadinessCheck(Check):
    id = "karpenter-readiness"
    phase = "phases/04-karpenter-autoscaling"
    requires_cluster_access = True

    def run(self, ctx: AwsContext) -> CheckResult:
        return CheckResult(
            check_id=self.id, findings=[], ran=False,
            skip_reason="Requires a live kubeconfig to inspect NodePools/EC2NodeClasses. Not implemented in v1 — see phases/04-karpenter-autoscaling.",
        )


@register
class SpotReadinessCheck(Check):
    id = "spot-readiness"
    phase = "phases/05-spot-instance-engineering"
    requires_cluster_access = True

    def run(self, ctx: AwsContext) -> CheckResult:
        return CheckResult(
            check_id=self.id, findings=[], ran=False,
            skip_reason="Requires a live kubeconfig to inspect Job tolerations/checkpointing config. Not implemented in v1 — see phases/05-spot-instance-engineering.",
        )
