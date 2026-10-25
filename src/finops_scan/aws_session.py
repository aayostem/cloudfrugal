"""
Thin wrapper around boto3 sessions for finops-scan.

Hard rule for this whole package: every client built here is used
read-only. No check module may call a mutating API (create_*, delete_*,
modify_*, put_* except for read-only put-config-style calls that don't
exist here). If you're adding a check and reach for a mutating call, stop
— that check belongs in the engagement's runbooks (phases/), not in this
tool. This tool's entire value proposition is "safe to run against a
production account with nothing but a read-only IAM policy."
"""
from __future__ import annotations

import boto3


class AwsContext:
    """Holds one boto3 Session plus lazily-created, read-only clients."""

    def __init__(self, profile: str | None = None, region: str | None = None):
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self._clients: dict[str, object] = {}

    def client(self, service_name: str):
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(service_name)
        return self._clients[service_name]

    @property
    def region(self) -> str:
        return self.session.region_name or "us-east-1"

    def account_id(self) -> str:
        return self.client("sts").get_caller_identity()["Account"]
