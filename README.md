# finops-scan

A read-only CLI that runs the diagnostic core of the FinOps + IDP
engagement (`../../phases/`) against your own AWS account and produces a
founder-readable gap report — dollar figures, not raw JSON — in under ten
minutes, with no cluster access and no write permissions required.

This is the engagement's Phase 11 deliverable, extracted so it's useful
standalone. It is also, deliberately, the free front door: run it, see
what it finds, then decide whether the rest of the engagement is worth
paying for.

## What it checks (v1)

| Check | Maps to | Needs |
|---|---|---|
| Cost-allocation tag coverage (the six required tags) | Phase 01 | `ce:*`, `ec2:DescribeInstances`, `ec2:DescribeVolumes`, `rds:DescribeDBInstances` (all read-only) |
| Immediate waste — gp2 volumes, unattached EIPs, stopped instances still billing EBS | Phase 02 | `ec2:Describe*` (read-only) |
| S3 buckets with no lifecycle policy | Phase 06 | `s3:ListAllMyBuckets`, `s3:GetLifecycleConfiguration` (read-only) |

**Deliberately out of scope for v1:** Kubecost/Karpenter/Spot readiness
(Phases 03–05) and IDP maturity (Phases 07–10). Those need cluster access,
not just AWS API read access — adding them would push setup time well
past the ten-minute bar this tool is built around. They're scaffolded in
`checks/` as clearly-marked stubs so v2 can add them without restructuring
anything.

## Install

```bash
pip install -e .
# or, once published:
pip install finops-scan
```

Requires Python 3.10+, `boto3`, and AWS credentials with the read-only
permissions listed above. **The tool never calls a write or delete API —
verify this yourself in `src/finops_scan/aws_session.py` before pointing
it at anything you care about.**

## Use

```bash
finops-scan run --region us-east-1 --output report.md
```

```bash
finops-scan run --profile my-aws-profile --checks tagging,waste --format json
```

Flags:
- `--region` — defaults to the session's configured region
- `--profile` — AWS named profile (defaults to the default credential chain)
- `--checks` — comma-separated subset (`tagging`, `waste`, `s3-lifecycle`); default is all v1 checks
- `--output` — file path; defaults to stdout
- `--format` — `md` (default, founder-readable) or `json` (machine-readable, for CI or a follow-up tool)

## Sample output shape

```
finops-scan report — account ${ACCOUNT_ID} — us-east-1 — 2027-01-14

3 checks run. 2 findings.

HIGH   [waste]    7 EBS volumes still on gp2 — est. $41.30/month recoverable
                  (migrate to gp3, zero downtime — see phases/02-cloud-cost-audit)
MEDIUM [tagging]  12 of 40 EC2 instances missing the Team tag — cost cannot
                  be attributed to an owner for ~30% of compute spend

Estimated recoverable waste this scan: $41.30/month ($495.60/year)
Estimated attribution gap: 30% of EC2 spend untagged

Full detail: report.md
```

The numbers are computed from what the check actually finds in your
account — this tool has no hardcoded dollar figures anywhere. See
`src/finops_scan/report.py`.

## Why this exists

See `phases/11-capstone-cto-report/README.md` for the full reasoning.
Short version: everything in this engagement's first six phases is
already "run a read-only check, report a dollar figure, decide what to
fix." This tool is that loop, packaged for someone else's account.
