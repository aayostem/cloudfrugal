"""
Shared data model every check module reports through.

A Check finds Findings. A Finding is deliberately founder-readable, not a
raw API response: a severity, a one-line description, an optional dollar
estimate, and which engagement phase has the fix. report.py turns a list
of these into the markdown/JSON report — no check module formats output
itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from finops_scan.aws_session import AwsContext


@dataclass
class Finding:
    severity: str          # "HIGH" | "MEDIUM" | "LOW"
    check_id: str          # e.g. "waste.gp2-volumes"
    message: str           # one line, founder-readable
    monthly_cost_estimate: float | None = None  # USD, None if not quantifiable
    remediation_phase: str = ""  # e.g. "phases/02-cloud-cost-audit"
    detail: dict = field(default_factory=dict)  # raw supporting data, for --format json


@dataclass
class CheckResult:
    check_id: str
    findings: list[Finding]
    ran: bool = True
    skip_reason: str = ""


class Check:
    """Base class every phase-derived check subclasses."""

    id: str = "base"
    phase: str = ""
    requires_cluster_access: bool = False  # True => excluded from v1 default run

    def run(self, ctx: AwsContext) -> CheckResult:
        raise NotImplementedError


REGISTRY: dict[str, type[Check]] = {}


def register(cls: type[Check]) -> type[Check]:
    REGISTRY[cls.id] = cls
    return cls
