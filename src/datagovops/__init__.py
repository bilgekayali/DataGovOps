"""DataGovOps governed-data core."""

from .models import (
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetValidationReport,
    DataClassification,
    DataCriticality,
    GovernanceError,
    GovernancePolicy,
    GovernancePrincipal,
    PrincipalType,
    canonical_json,
    digest_artifact,
)
from .registry import DataAssetRegistry
from .validation import DataAssetValidator, assert_validation_report_current

__all__ = [
    "AuthoritativeSystem",
    "DataAssetRecord",
    "DataAssetRegistry",
    "DataAssetValidationReport",
    "DataAssetValidator",
    "DataClassification",
    "DataCriticality",
    "GovernanceError",
    "GovernancePolicy",
    "GovernancePrincipal",
    "PrincipalType",
    "assert_validation_report_current",
    "canonical_json",
    "digest_artifact",
]

__version__ = "0.1.0.dev1"
