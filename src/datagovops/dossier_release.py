from __future__ import annotations

from typing import Any

from .dossier import (
    DOSSIER_SCHEMA_VERSION,
    RELEASE_VERSION,
    DossierException,
    DossierState,
    DomainSnapshot,
    GovernanceDossier,
    GovernanceDossierBuilder as _BaseGovernanceDossierBuilder,
    _artifact,
    _assurance_snapshot,
    _control_snapshot,
    _institution_values,
    _inventory_snapshot,
    _lineage_snapshot,
    _parse_time,
    _quality_snapshot,
    _semantic_snapshot,
)
from .models import GovernanceError, GovernancePolicy, _text, _timestamp
from .quality import FindingResolutionState, QualityEvaluationState
from .validation import DataAssetValidator


class GovernanceDossierBuilder(_BaseGovernanceDossierBuilder):
    """Supported v0.1 release builder with exact domain ownership for artifacts."""

    def build(
        self,
        institution_id: str,
        *,
        generated_at: str,
        source_revision: str,
        quality_policy_id: str | None = None,
        control_policy_id: str | None = None,
        exceptions: tuple[DossierException, ...] = (),
    ) -> GovernanceDossier:
        institution_id = _text("institution_id", institution_id)
        generated_at = _timestamp("generated_at", generated_at)
        _text("source_revision", source_revision, limit=256)
        self.asset_registry.snapshot_digest(institution_id)

        gap_findings: set[str] = set()
        revalidation: set[str] = set()
        assurance = []

        policy = self.governance_policy or GovernancePolicy(institution_id=institution_id)
        if policy.institution_id != institution_id:
            raise GovernanceError("governance policy uses different institution")
        validator = DataAssetValidator()
        latest_assets: dict[str, Any] = {}
        for asset in self.asset_registry.assets_for_institution(institution_id):
            latest_assets[asset.asset_id] = asset
        for asset_id in sorted(latest_assets):
            report = validator.validate(latest_assets[asset_id], policy, self.asset_registry, validated_at=generated_at)
            assurance.append(_artifact("assurance", report))
            for code in report.error_codes:
                gap_findings.add(f"inventory:{asset_id}:{code}")

        for decision in _institution_values(self.semantic_registry._classifications, institution_id):
            latest = latest_assets.get(decision.asset_id)
            if latest is not None and decision.asset_version == latest.asset_version:
                try:
                    self.semantic_registry.assert_classification_current(decision)
                except GovernanceError as exc:
                    revalidation.add(f"semantic:classification:{decision.artifact_digest}:{exc}")
        for designation in _institution_values(self.semantic_registry._cde_designations, institution_id):
            latest = latest_assets.get(designation.asset_id)
            if latest is not None and designation.asset_version == latest.asset_version:
                try:
                    self.semantic_registry.assert_cde_current(designation)
                except GovernanceError as exc:
                    revalidation.add(f"semantic:cde:{designation.artifact_digest}:{exc}")
        for binding in _institution_values(self.semantic_registry._purpose_bindings, institution_id):
            latest = latest_assets.get(binding.asset_id)
            if latest is None or binding.asset_version != latest.asset_version:
                continue
            try:
                latest_purpose = self.semantic_registry.latest_purpose(institution_id, binding.purpose_id)
                if binding.purpose_version == latest_purpose.purpose_version:
                    self.semantic_registry.assert_purpose_binding_current(binding)
            except GovernanceError as exc:
                revalidation.add(f"semantic:purpose_binding:{binding.artifact_digest}:{exc}")

        requirements = self.lineage_registry.requirements_for_institution(institution_id)
        if requirements:
            try:
                report = self.lineage_registry.evaluate_completeness(institution_id, evaluated_at=generated_at)
                assurance.append(_artifact("assurance", report))
                for requirement_id in report.missing_requirement_ids:
                    gap_findings.add(f"lineage:missing:{requirement_id}")
                for requirement_id in report.stale_requirement_ids:
                    revalidation.add(f"lineage:stale:{requirement_id}")
            except GovernanceError as exc:
                revalidation.add(f"lineage:revalidation:{exc}")
        else:
            gap_findings.add("lineage:no_completeness_requirements")

        latest_rules: dict[str, Any] = {}
        for rule in _institution_values(self.quality_registry._rules, institution_id):
            current = latest_rules.get(rule.rule_id)
            if current is None or rule.rule_version > current.rule_version:
                latest_rules[rule.rule_id] = rule
        quality_policy, quality_policy_error = self._select_latest(
            self.quality_registry._policies,
            institution_id,
            "policy_id",
            "policy_version",
            quality_policy_id,
        )
        if not latest_rules:
            gap_findings.add("quality:no_rules_configured")
        elif quality_policy_error == "missing":
            gap_findings.add("quality:no_evaluation_policy")
        elif quality_policy_error == "ambiguous":
            gap_findings.add("quality:policy_selection_required")
        else:
            for rule_id in sorted(latest_rules):
                try:
                    evaluation = self.quality_registry.evaluate_rule(
                        latest_rules[rule_id], quality_policy, evaluated_at=generated_at
                    )
                    # Evaluation belongs to QualityRegistry and therefore stays in the quality domain.
                    if evaluation.state is QualityEvaluationState.BREACHED:
                        gap_findings.add(f"quality:breached:{rule_id}")
                    elif evaluation.state is QualityEvaluationState.INCOMPLETE:
                        gap_findings.add(f"quality:incomplete:{rule_id}:{evaluation.reason_code}")
                except GovernanceError as exc:
                    revalidation.add(f"quality:rule:{rule_id}:{exc}")

        for finding in sorted(_institution_values(self.quality_registry._findings, institution_id), key=lambda x: x.finding_id):
            try:
                resolution = self.quality_registry.resolve_finding(finding, resolved_at=generated_at)
                assurance.append(_artifact("assurance", resolution))
                if resolution.state is not FindingResolutionState.CLOSED:
                    gap_findings.add(f"quality:finding_open:{finding.finding_id}:{resolution.state.value}")
            except GovernanceError as exc:
                revalidation.add(f"quality:finding:{finding.finding_id}:{exc}")

        control_policy, control_policy_error = self._select_latest(
            self.control_registry._policies,
            institution_id,
            "policy_id",
            "policy_version",
            control_policy_id,
        )
        if control_policy_error == "missing":
            gap_findings.add("control:no_governance_control_policy")
        elif control_policy_error == "ambiguous":
            gap_findings.add("control:policy_selection_required")
        else:
            try:
                report = self.control_registry.evaluate_control_gaps(
                    institution_id, control_policy.policy_id, evaluated_at=generated_at
                )
                assurance.append(_artifact("assurance", report))
                for gap in report.gaps:
                    suffix = f":{gap.reference_id}" if gap.reference_id is not None else ""
                    gap_findings.add(f"control:{gap.code.value}:{gap.asset_id}{suffix}")
            except GovernanceError as exc:
                revalidation.add(f"control:revalidation:{exc}")

        when = _parse_time(generated_at)
        for grant in _institution_values(self.control_registry._grants, institution_id):
            if _parse_time(grant.valid_from) > when:
                continue
            if grant.expires_at is not None and _parse_time(grant.expires_at) <= when:
                continue
            try:
                self.control_registry.assert_grant_current(grant, as_of=generated_at)
            except GovernanceError as exc:
                revalidation.add(f"access:grant:{grant.grant_id}:{exc}")

        for exception in exceptions:
            if exception.institution_id != institution_id:
                raise GovernanceError("dossier exception uses different institution")
            self.asset_registry.principal(institution_id, exception.owner_id)

        registry_artifacts = self._collect_registry_artifacts(institution_id)
        artifact_ids = {item.artifact_id for item in registry_artifacts}
        if any(item.artifact_id in artifact_ids for item in assurance):
            raise GovernanceError("assurance artifact collides with registry-owned artifact")
        artifacts = sorted(registry_artifacts + assurance, key=lambda x: (x.domain, x.artifact_type, x.artifact_id))

        inventory_artifacts = [x for x in artifacts if x.domain == "inventory"]
        semantic_artifacts = [x for x in artifacts if x.domain == "semantic"]
        lineage_artifacts = [x for x in artifacts if x.domain == "lineage"]
        quality_artifacts = [x for x in artifacts if x.domain == "quality"]
        control_artifacts = [x for x in artifacts if x.domain == "access_retention_privacy"]
        assurance_artifacts = [x for x in artifacts if x.domain == "assurance"]

        inventory_digest = _inventory_snapshot(institution_id, inventory_artifacts)
        semantic_digest = _semantic_snapshot(institution_id, inventory_digest, semantic_artifacts)
        lineage_digest = _lineage_snapshot(institution_id, inventory_digest, semantic_digest, lineage_artifacts)
        quality_digest = _quality_snapshot(institution_id, inventory_digest, semantic_digest, quality_artifacts)
        control_digest = _control_snapshot(institution_id, inventory_digest, semantic_digest, control_artifacts)
        assurance_digest = _assurance_snapshot(institution_id, assurance_artifacts)

        expected_runtime = {
            "inventory": self.asset_registry.snapshot_digest(institution_id),
            "semantic": self.semantic_registry.snapshot_digest(institution_id),
            "lineage": self.lineage_registry.snapshot_digest(institution_id),
            "quality": self.quality_registry.snapshot_digest(institution_id),
            "access_retention_privacy": self.control_registry.snapshot_digest(institution_id),
        }
        recomputed = {
            "inventory": inventory_digest,
            "semantic": semantic_digest,
            "lineage": lineage_digest,
            "quality": quality_digest,
            "access_retention_privacy": control_digest,
        }
        if expected_runtime != recomputed:
            raise GovernanceError("embedded dossier artifacts do not reproduce governed registry snapshots")

        domain_snapshots = tuple(sorted((
            DomainSnapshot("inventory", inventory_digest, tuple(sorted(x.digest for x in inventory_artifacts))),
            DomainSnapshot("semantic", semantic_digest, tuple(sorted(x.digest for x in semantic_artifacts))),
            DomainSnapshot("lineage", lineage_digest, tuple(sorted(x.digest for x in lineage_artifacts))),
            DomainSnapshot("quality", quality_digest, tuple(sorted(x.digest for x in quality_artifacts))),
            DomainSnapshot("access_retention_privacy", control_digest, tuple(sorted(x.digest for x in control_artifacts))),
            DomainSnapshot("assurance", assurance_digest, tuple(sorted(x.digest for x in assurance_artifacts))),
        ), key=lambda x: x.domain))

        active_exceptions = tuple(sorted(
            exception.artifact_digest
            for exception in exceptions
            if _parse_time(exception.approved_at) <= when < _parse_time(exception.expires_at)
        ))
        covered: set[str] = set()
        for exception in exceptions:
            if exception.artifact_digest in active_exceptions:
                covered.update(exception.finding_codes)

        all_findings = tuple(sorted(gap_findings | revalidation))
        revalidation_findings = tuple(sorted(revalidation))
        uncovered_gaps = gap_findings - covered
        if revalidation:
            state = DossierState.REVALIDATION_REQUIRED
        elif uncovered_gaps:
            state = DossierState.WITH_GAPS
        elif gap_findings:
            state = DossierState.WITH_EXCEPTIONS
        else:
            state = DossierState.CURRENT

        coverage: dict[str, int] = {}
        for artifact in artifacts:
            coverage[artifact.domain] = coverage.get(artifact.domain, 0) + 1

        return GovernanceDossier(
            schema_version=DOSSIER_SCHEMA_VERSION,
            release_version=RELEASE_VERSION,
            institution_id=institution_id,
            generated_at=generated_at,
            source_revision=source_revision,
            state=state,
            findings=all_findings,
            revalidation_findings=revalidation_findings,
            active_exception_digests=active_exceptions,
            coverage=dict(sorted(coverage.items())),
            domain_snapshots=domain_snapshots,
            artifacts=tuple(artifacts),
            exceptions=tuple(sorted(exceptions, key=lambda x: x.exception_id)),
        )
