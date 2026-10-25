"""
Phase 06 logic, extracted: which S3 buckets have no lifecycle policy at
all. This does not compute actual storage-class savings (that needs
per-bucket size and access-pattern data this tool deliberately doesn't
pull, to keep the read footprint small) — it flags the buckets where
100% of stored data is sitting in Standard with no automatic tiering,
which is the finding that matters for triage.
"""
from __future__ import annotations

from botocore.exceptions import ClientError

from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import Check, CheckResult, Finding, register


@register
class S3LifecycleCheck(Check):
    id = "s3-lifecycle"
    phase = "phases/06-storage-database-controls"
    requires_cluster_access = False

    def run(self, ctx: AwsContext) -> CheckResult:
        findings: list[Finding] = []
        s3 = ctx.client("s3")

        buckets = s3.list_buckets().get("Buckets", [])
        no_lifecycle = []
        for bucket in buckets:
            name = bucket["Name"]
            try:
                s3.get_bucket_lifecycle_configuration(Bucket=name)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code == "NoSuchLifecycleConfiguration":
                    no_lifecycle.append(name)
                # Any other error (access denied, wrong region for this
                # client, etc.) is skipped rather than mis-reported as
                # "no lifecycle policy" — a false positive here is worse
                # than a missed bucket.

        if no_lifecycle:
            findings.append(Finding(
                severity="MEDIUM",
                check_id="s3-lifecycle.no-policy",
                message=(
                    f"{len(no_lifecycle)} of {len(buckets)} S3 buckets have no "
                    f"lifecycle policy — all stored data stays in Standard "
                    f"storage indefinitely unless moved manually"
                ),
                remediation_phase=self.phase,
                detail={"bucket_names": no_lifecycle},
            ))

        return CheckResult(check_id=self.id, findings=findings)
