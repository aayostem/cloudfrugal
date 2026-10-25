"""
Phase 01 logic, extracted: are the six required tags actually applied
across EC2, EBS, and RDS? This does NOT check whether the tags are
*activated for cost allocation* (that's an account-level Cost Explorer
setting with no clean read API to verify cheaply) — it checks whether
resources actually carry the tags, which is the gap that costs money.
"""
from __future__ import annotations

from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import Check, CheckResult, Finding, register

REQUIRED_TAGS = {"Environment", "Team", "Service", "ManagedBy", "CostCenter", "Owner"}


def _missing_tags(tags: list[dict] | None) -> set[str]:
    present = {t["Key"] for t in (tags or [])}
    return REQUIRED_TAGS - present


@register
class TaggingCheck(Check):
    id = "tagging"
    phase = "phases/01-finops-fundamentals-unit-economics"
    requires_cluster_access = False

    def run(self, ctx: AwsContext) -> CheckResult:
        findings: list[Finding] = []

        ec2 = ctx.client("ec2")
        rds = ctx.client("rds")

        # --- EC2 instances ---
        instances = []
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                instances.extend(reservation.get("Instances", []))

        untagged_ec2 = [i for i in instances if _missing_tags(i.get("Tags"))]
        if instances:
            pct = round(100 * len(untagged_ec2) / len(instances))
            if untagged_ec2:
                findings.append(Finding(
                    severity="HIGH" if pct >= 50 else "MEDIUM",
                    check_id="tagging.ec2",
                    message=(
                        f"{len(untagged_ec2)} of {len(instances)} EC2 instances "
                        f"({pct}%) are missing at least one required tag — cost "
                        f"cannot be attributed to a team or owner for this compute"
                    ),
                    remediation_phase=self.phase,
                    detail={"untagged_instance_ids": [i["InstanceId"] for i in untagged_ec2]},
                ))

        # --- EBS volumes ---
        volumes = []
        paginator = ec2.get_paginator("describe_volumes")
        for page in paginator.paginate():
            volumes.extend(page.get("Volumes", []))

        untagged_vols = [v for v in volumes if _missing_tags(v.get("Tags"))]
        if untagged_vols:
            findings.append(Finding(
                severity="MEDIUM",
                check_id="tagging.ebs",
                message=(
                    f"{len(untagged_vols)} of {len(volumes)} EBS volumes are "
                    f"missing at least one required tag"
                ),
                remediation_phase=self.phase,
                detail={"untagged_volume_ids": [v["VolumeId"] for v in untagged_vols]},
            ))

        # --- RDS instances ---
        db_instances = []
        paginator = rds.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            db_instances.extend(page.get("DBInstances", []))

        untagged_rds = [
            d for d in db_instances if _missing_tags(d.get("TagList"))
        ]
        if untagged_rds:
            findings.append(Finding(
                severity="HIGH",
                check_id="tagging.rds",
                message=(
                    f"{len(untagged_rds)} of {len(db_instances)} RDS instances "
                    f"are missing at least one required tag — databases are "
                    f"usually the most expensive untagged line item"
                ),
                remediation_phase=self.phase,
                detail={"untagged_db_ids": [d["DBInstanceIdentifier"] for d in untagged_rds]},
            ))

        return CheckResult(check_id=self.id, findings=findings)
