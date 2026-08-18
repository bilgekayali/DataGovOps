"""Strict public boundary for access/retention/privacy governance."""

from .access_retention import (
    AccessGrant,
    AccessRetentionPrivacyRegistry as _AccessRetentionPrivacyRegistry,
)
from .models import GovernanceError


class AccessRetentionPrivacyRegistry(_AccessRetentionPrivacyRegistry):
    """Harden grant creation against superseded access-purpose approvals."""

    def register_grant(self, grant: AccessGrant) -> str:
        approval = self._approval_by_digest(grant.institution_id, grant.approval_digest)
        latest = self.latest_access_approval(
            institution_id=grant.institution_id,
            subject_kind=grant.subject_kind,
            subject_id=grant.subject_id,
            asset_id=grant.asset_id,
            purpose_id=grant.purpose_id,
        )
        if latest.artifact_digest != approval.artifact_digest:
            raise GovernanceError("access grant requires the latest access-purpose approval")
        return super().register_grant(grant)
