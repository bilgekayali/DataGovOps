from __future__ import annotations

from .models import (
    AuthoritativeSystem,
    DataAssetRecord,
    GovernanceError,
    GovernancePrincipal,
    digest_artifact,
)


class DataAssetRegistry:
    """Institution-scoped immutable governance registry with versioned data assets."""

    def __init__(self) -> None:
        self._principals: dict[tuple[str, str], GovernancePrincipal] = {}
        self._systems: dict[tuple[str, str], AuthoritativeSystem] = {}
        self._assets: dict[tuple[str, str, int], DataAssetRecord] = {}

    def register_principal(self, principal: GovernancePrincipal) -> str:
        key = (principal.institution_id, principal.principal_id)
        existing = self._principals.get(key)
        if existing is not None and existing.artifact_digest != principal.artifact_digest:
            raise GovernanceError("principal_id is already registered with different content")
        self._principals.setdefault(key, principal)
        return principal.artifact_digest

    def register_system(self, system: AuthoritativeSystem) -> str:
        self.principal(system.institution_id, system.owner_id)
        key = (system.institution_id, system.system_id)
        existing = self._systems.get(key)
        if existing is not None and existing.artifact_digest != system.artifact_digest:
            raise GovernanceError("system_id is already registered with different content")
        self._systems.setdefault(key, system)
        return system.artifact_digest

    def register_asset(self, asset: DataAssetRecord) -> str:
        for principal_id in (
            asset.owner_id,
            asset.steward_id,
            asset.classification_decision_owner_id,
            asset.criticality_decision_owner_id,
        ):
            self.principal(asset.institution_id, principal_id)
        if asset.quality_owner_id is not None:
            self.principal(asset.institution_id, asset.quality_owner_id)
        self.system(asset.institution_id, asset.system_of_record_id)

        key = (asset.institution_id, asset.asset_id, asset.asset_version)
        existing = self._assets.get(key)
        if existing is not None:
            if existing.artifact_digest != asset.artifact_digest:
                raise GovernanceError("asset identity/version is already registered with different content")
            return existing.artifact_digest

        history = self.history(asset.institution_id, asset.asset_id)
        expected_version = 1 if not history else history[-1].asset_version + 1
        if asset.asset_version != expected_version:
            raise GovernanceError(
                f"asset_version must be contiguous; expected version {expected_version}"
            )
        self._assets[key] = asset
        return asset.artifact_digest

    def principal(self, institution_id: str, principal_id: str) -> GovernancePrincipal:
        try:
            return self._principals[(institution_id, principal_id)]
        except KeyError as exc:
            raise GovernanceError("unknown accountable principal") from exc

    def system(self, institution_id: str, system_id: str) -> AuthoritativeSystem:
        try:
            return self._systems[(institution_id, system_id)]
        except KeyError as exc:
            raise GovernanceError("unknown authoritative system") from exc

    def asset(self, institution_id: str, asset_id: str, asset_version: int) -> DataAssetRecord:
        try:
            return self._assets[(institution_id, asset_id, asset_version)]
        except KeyError as exc:
            raise GovernanceError("unknown data asset version") from exc

    def latest_asset(self, institution_id: str, asset_id: str) -> DataAssetRecord:
        history = self.history(institution_id, asset_id)
        if not history:
            raise GovernanceError("unknown data asset")
        return history[-1]

    def history(self, institution_id: str, asset_id: str) -> tuple[DataAssetRecord, ...]:
        return tuple(
            sorted(
                (
                    asset
                    for (scope, current_id, _), asset in self._assets.items()
                    if scope == institution_id and current_id == asset_id
                ),
                key=lambda item: item.asset_version,
            )
        )

    def principals_for_institution(self, institution_id: str) -> tuple[GovernancePrincipal, ...]:
        return tuple(
            sorted(
                (
                    principal
                    for (scope, _), principal in self._principals.items()
                    if scope == institution_id
                ),
                key=lambda item: item.principal_id,
            )
        )

    def systems_for_institution(self, institution_id: str) -> tuple[AuthoritativeSystem, ...]:
        return tuple(
            sorted(
                (
                    system
                    for (scope, _), system in self._systems.items()
                    if scope == institution_id
                ),
                key=lambda item: item.system_id,
            )
        )

    def assets_for_institution(self, institution_id: str) -> tuple[DataAssetRecord, ...]:
        return tuple(
            sorted(
                (
                    asset
                    for (scope, _, _), asset in self._assets.items()
                    if scope == institution_id
                ),
                key=lambda item: (item.asset_id, item.asset_version),
            )
        )

    def snapshot_digest(self, institution_id: str) -> str:
        principals = self.principals_for_institution(institution_id)
        systems = self.systems_for_institution(institution_id)
        assets = self.assets_for_institution(institution_id)
        if not principals and not systems and not assets:
            raise GovernanceError("institution has no governed registry evidence")
        return digest_artifact(
            {
                "institution_id": institution_id,
                "principals": [item.artifact_digest for item in principals],
                "systems": [item.artifact_digest for item in systems],
                "assets": [item.artifact_digest for item in assets],
            }
        )

    def assert_registered_asset(self, asset: DataAssetRecord) -> None:
        current = self.asset(asset.institution_id, asset.asset_id, asset.asset_version)
        if current.artifact_digest != asset.artifact_digest:
            raise GovernanceError("data asset content does not match registered version")
