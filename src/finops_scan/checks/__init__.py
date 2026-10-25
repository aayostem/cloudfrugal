"""
Importing this package registers every check module against
`finops_scan.checks.base.REGISTRY`. cli.py imports this package once,
at startup, and never imports individual check modules directly.
"""
from finops_scan.checks import (  # noqa: F401
    phase01_tagging,
    phase02_waste,
    phase06_storage,
    phase03_05_cluster,   # stubs — require_cluster_access = True
    phase07_10_idp,       # stubs — require_cluster_access = True
)
