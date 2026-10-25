"""
Smoke tests. These prove the checks import cleanly, run against a mocked
AWS account without crashing, and that the registry/report plumbing
works end-to-end — not that the dollar estimates are perfectly accurate.
Real-account validation happens in Phase 11 against the two demo stacks.
"""
from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from finops_scan import checks  # noqa: F401 — registers checks
from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import REGISTRY
from finops_scan.report import render_json, render_markdown


@pytest.fixture
def aws_ctx():
    with mock_aws():
        # Minimal fixture data so each check has something to find.
        ec2 = boto3.client("ec2", region_name="us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")

        # An untagged EC2 instance
        ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro")

        # A gp2 volume
        ec2.create_volume(AvailabilityZone="us-east-1a", Size=10, VolumeType="gp2")

        # An unattached Elastic IP
        ec2.allocate_address(Domain="vpc")

        # A bucket with no lifecycle policy
        s3.create_bucket(Bucket="finops-scan-test-bucket")

        yield AwsContext(region="us-east-1")


def test_registry_has_v1_checks():
    assert {"tagging", "waste", "s3-lifecycle"}.issubset(REGISTRY.keys())


def test_all_checks_run_without_crashing(aws_ctx):
    for check_id, cls in REGISTRY.items():
        if cls.requires_cluster_access:
            result = cls().run(aws_ctx)
            assert result.ran is False
            assert result.skip_reason
            continue
        result = cls().run(aws_ctx)
        assert result.check_id == check_id


def test_tagging_check_finds_untagged_instance(aws_ctx):
    result = REGISTRY["tagging"]().run(aws_ctx)
    assert any(f.check_id == "tagging.ec2" for f in result.findings)


def test_waste_check_finds_gp2_and_eip(aws_ctx):
    result = REGISTRY["waste"]().run(aws_ctx)
    ids = {f.check_id for f in result.findings}
    assert "waste.gp2-volumes" in ids
    assert "waste.unattached-eips" in ids


def test_s3_lifecycle_check_finds_bucket(aws_ctx):
    result = REGISTRY["s3-lifecycle"]().run(aws_ctx)
    assert any(f.check_id == "s3-lifecycle.no-policy" for f in result.findings)


def test_report_renders_markdown_and_json(aws_ctx):
    results = [REGISTRY[c]().run(aws_ctx) for c in ("tagging", "waste", "s3-lifecycle")]
    md = render_markdown("123456789012", "us-east-1", results)
    js = render_json("123456789012", "us-east-1", results)
    assert "finops-scan report" in md
    assert '"account_id": "123456789012"' in js
