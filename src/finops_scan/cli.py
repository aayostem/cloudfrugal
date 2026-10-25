from __future__ import annotations

import sys

import click

from finops_scan import checks  # noqa: F401 — import registers all check modules
from finops_scan.aws_session import AwsContext
from finops_scan.checks.base import REGISTRY
from finops_scan.report import render_json, render_markdown

DEFAULT_V1_CHECKS = ["tagging", "waste", "s3-lifecycle"]


@click.group()
def main():
    """finops-scan — read-only AWS FinOps gap scanner.

    See phases/00-engagement-kickoff/ in the parent repo for the full
    engagement this tool's checks are extracted from.
    """


@main.command()
@click.option("--region", default=None, help="AWS region (defaults to session default).")
@click.option("--profile", default=None, help="AWS named profile.")
@click.option(
    "--checks", "check_ids", default=",".join(DEFAULT_V1_CHECKS),
    help=f"Comma-separated check IDs to run. Default: {', '.join(DEFAULT_V1_CHECKS)}. "
         f"Available: {', '.join(sorted(REGISTRY))}.",
)
@click.option("--include-cluster-checks", is_flag=True, default=False,
              help="Also attempt checks that require cluster access (not implemented in v1 — see README).")
@click.option("--output", "-o", type=click.Path(), default=None, help="Write report to this file instead of stdout.")
@click.option("--format", "fmt", type=click.Choice(["md", "json"]), default="md")
def run(region, profile, check_ids, include_cluster_checks, output, fmt):
    """Run the scan and produce a report."""
    ids = [c.strip() for c in check_ids.split(",") if c.strip()]

    ctx = AwsContext(profile=profile, region=region)
    try:
        account_id = ctx.account_id()
    except Exception as e:  # noqa: BLE001 — surface any auth/config error plainly
        click.echo(f"Could not authenticate to AWS: {e}", err=True)
        click.echo("Check your credentials / --profile / --region and try again.", err=True)
        sys.exit(1)

    results = []
    for check_id in ids:
        check_cls = REGISTRY.get(check_id)
        if check_cls is None:
            click.echo(f"Unknown check id: {check_id!r} — available: {sorted(REGISTRY)}", err=True)
            sys.exit(1)
        check = check_cls()
        if check.requires_cluster_access and not include_cluster_checks:
            continue
        results.append(check.run(ctx))

    if fmt == "json":
        text = render_json(account_id, ctx.region, results)
    else:
        text = render_markdown(account_id, ctx.region, results)

    if output:
        with open(output, "w") as f:
            f.write(text)
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)


@main.command(name="list-checks")
def list_checks():
    """List every registered check, including ones not run by default."""
    for check_id, cls in sorted(REGISTRY.items()):
        default = "default" if check_id in DEFAULT_V1_CHECKS else (
            "cluster-access required" if cls.requires_cluster_access else "opt-in"
        )
        click.echo(f"{check_id:20s} [{default:24s}] -> {cls.phase}")


if __name__ == "__main__":
    main()
