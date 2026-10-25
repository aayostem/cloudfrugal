"""
Phase 02 logic, extracted: gp2 volumes, unattached EIPs, stopped
instances still billing for their attached EBS. These three are the
highest-return, lowest-risk findings in the whole engagement — see
phases/02-cloud-cost-audit/README.md for why they're checked first.

Pricing constants below are us-east-1 on-demand list prices as of this
tool's last update — they're estimates for triage, not a bill. The tool
says so in every message that uses one; never present an estimate as an
exact figure.
"""
from __future__ import annotations

from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import Check, CheckResult, Finding, register

# us-east-1 approximate list prices, for triage-level estimates only
GP2_GB_MONTHLY = 0.10
GP3_GB_MONTHLY = 0.08
EIP_UNATTACHED_MONTHLY = 3.65


@register
class WasteCheck(Check):
    id = "waste"
    phase = "phases/02-cloud-cost-audit"
    requires_cluster_access = False

    def run(self, ctx: AwsContext) -> CheckResult:
        findings: list[Finding] = []
        ec2 = ctx.client("ec2")

        # --- gp2 volumes ---
        gp2_volumes = []
        paginator = ec2.get_paginator("describe_volumes")
        for page in paginator.paginate(Filters=[{"Name": "volume-type", "Values": ["gp2"]}]):
            gp2_volumes.extend(page.get("Volumes", []))

        if gp2_volumes:
            total_gb = sum(v["Size"] for v in gp2_volumes)
            monthly_delta = round(total_gb * (GP2_GB_MONTHLY - GP3_GB_MONTHLY), 2)
            findings.append(Finding(
                severity="MEDIUM",
                check_id="waste.gp2-volumes",
                message=(
                    f"{len(gp2_volumes)} EBS volumes ({total_gb} GB total) are still "
                    f"on gp2 — migrating to gp3 is zero-downtime and typically ~20% "
                    f"cheaper for the same performance"
                ),
                monthly_cost_estimate=monthly_delta,
                remediation_phase=self.phase,
                detail={"volume_ids": [v["VolumeId"] for v in gp2_volumes]},
            ))

        # --- unattached Elastic IPs ---
        addresses = ec2.describe_addresses().get("Addresses", [])
        unattached = [a for a in addresses if not a.get("AssociationId")]
        if unattached:
            monthly = round(len(unattached) * EIP_UNATTACHED_MONTHLY, 2)
            findings.append(Finding(
                severity="LOW",
                check_id="waste.unattached-eips",
                message=(
                    f"{len(unattached)} Elastic IP(s) are allocated but not attached "
                    f"to anything — AWS bills these even when idle"
                ),
                monthly_cost_estimate=monthly,
                remediation_phase=self.phase,
                detail={"allocation_ids": [a.get("AllocationId") for a in unattached]},
            ))

        # --- stopped instances still billing for attached EBS ---
        stopped = []
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
        ):
            for reservation in page.get("Reservations", []):
                stopped.extend(reservation.get("Instances", []))

        if stopped:
            findings.append(Finding(
                severity="LOW",
                check_id="waste.stopped-instances",
                message=(
                    f"{len(stopped)} instance(s) are stopped but their attached EBS "
                    f"volumes are still billing — review whether these should be "
                    f"snapshotted and terminated"
                ),
                remediation_phase=self.phase,
                detail={"instance_ids": [i["InstanceId"] for i in stopped]},
            ))

        return CheckResult(check_id=self.id, findings=findings)
