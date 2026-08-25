from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    GovernanceError,
    _bool,
    _digest,
    _enum,
    _positive_int,
    _text,
    _timestamp,
    digest_artifact,
)
from .reporting import (
    AttestationDecision,
    ReportAssuranceAssessment,
    ReportOwnerAttestation,
    ReportingAssessmentState,
    _parse_time,
)
from .reporting_strict import ReportingGovernanceRegistry


class RiskDataDomain(str, Enum):
    CREDIT = "credit"
    MARKET = "market"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"
    CAPITAL = "capital"
    ENTERPRISE = "enterprise"
    OTHER = "other"


class AggregationLevel(str, Enum):
    ENTITY = "entity"
    GROUP = "group"
    BUSINESS_LINE = "business_line"
    PORTFOLIO = "portfolio"


class AggregationAssessmentState(str, Enum):
    MET = "met"
    BREACHED = "breached"
    INCOMPLETE = "incomplete"


def _unique_digests(name: str, values: tuple[str, ...], *, allow_empty: bool = True) -> tuple[str, ...]:
    result = tuple(_digest(name, value) for value in values)
    if not allow_empty and not result:
        raise GovernanceError(f"{name}s must contain at least one digest")
    if len(result) != len(set(result)):
        raise GovernanceError(f"{name}s must be unique")
    return tuple(sorted(result))


@dataclass(frozen=True, slots=True)
class ReportTaxonomyEntry:
    institution_id: str
    taxonomy_id: str
    taxonomy_version: int
    report_digest: str
    risk_domain: RiskDataDomain
    aggregation_level: AggregationLevel
    material: bool
    owner_id: str
    rationale: str
    registered_at: str
    bcbs239_applicability_determined: bool = False
    schema_version: str = "datagovops.bcbs239-report-taxonomy.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "taxonomy_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        _positive_int("taxonomy_version", self.taxonomy_version)
        _digest("report_digest", self.report_digest)
        _enum("risk_domain", self.risk_domain, RiskDataDomain)
        _enum("aggregation_level", self.aggregation_level, AggregationLevel)
        _bool("material", self.material)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))
        if _bool("bcbs239_applicability_determined", self.bcbs239_applicability_determined):
            raise GovernanceError("report taxonomy does not determine BCBS 239 applicability")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class RiskDataPortfolio:
    institution_id: str
    portfolio_id: str
    portfolio_version: int
    name: str
    owner_id: str
    report_digests: tuple[str, ...]
    taxonomy_digests: tuple[str, ...]
    required_risk_domains: tuple[RiskDataDomain, ...]
    registered_at: str
    schema_version: str = "datagovops.bcbs239-risk-data-portfolio.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "portfolio_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        object.__setattr__(self, "name", _text("name", self.name, limit=512))
        _positive_int("portfolio_version", self.portfolio_version)
        object.__setattr__(
            self,
            "report_digests",
            _unique_digests("report_digest", self.report_digests, allow_empty=False),
        )
        object.__setattr__(
            self,
            "taxonomy_digests",
            _unique_digests("taxonomy_digest", self.taxonomy_digests, allow_empty=False),
        )
        domains = tuple(self.required_risk_domains)
        if not domains:
            raise GovernanceError("required_risk_domains must be non-empty")
        for value in domains:
            _enum("required_risk_domain", value, RiskDataDomain)
        if len(domains) != len(set(domains)):
            raise GovernanceError("required_risk_domains must be unique")
        object.__setattr__(self, "required_risk_domains", tuple(sorted(domains, key=lambda item: item.value)))
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class RiskDataAggregationAssessment:
    institution_id: str
    portfolio_digest: str
    period_id: str
    report_assessment_digests: tuple[str, ...]
    report_attestation_digests: tuple[str, ...]
    portfolio_report_count: int
    represented_assessment_count: int
    met_report_count: int
    breached_report_count: int
    incomplete_report_count: int
    missing_assessment_count: int
    missing_attestation_count: int
    nonapproved_attestation_count: int
    state: AggregationAssessmentState
    gaps: tuple[str, ...]
    assessed_at: str
    bcbs239_compliance_determined: bool = False
    risk_data_accuracy_determined: bool = False
    supervisory_acceptance_determined: bool = False
    schema_version: str = "datagovops.bcbs239-aggregation-assessment.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "period_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("portfolio_digest", self.portfolio_digest)
        object.__setattr__(
            self,
            "report_assessment_digests",
            _unique_digests("report_assessment_digest", self.report_assessment_digests),
        )
        object.__setattr__(
            self,
            "report_attestation_digests",
            _unique_digests("report_attestation_digest", self.report_attestation_digests),
        )
        counts = (
            "portfolio_report_count",
            "represented_assessment_count",
            "met_report_count",
            "breached_report_count",
            "incomplete_report_count",
            "missing_assessment_count",
            "missing_attestation_count",
            "nonapproved_attestation_count",
        )
        for field in counts:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise GovernanceError(f"{field} must be a non-negative integer")
        if self.portfolio_report_count < 1:
            raise GovernanceError("portfolio_report_count must be positive")
        if (
            self.met_report_count + self.breached_report_count + self.incomplete_report_count
            != self.represented_assessment_count
        ):
            raise GovernanceError("aggregation assessment report-state counts are inconsistent")
        if (
            self.represented_assessment_count + self.missing_assessment_count
            != self.portfolio_report_count
        ):
            raise GovernanceError("aggregation assessment represented/missing counts are inconsistent")
        if self.missing_attestation_count > self.represented_assessment_count:
            raise GovernanceError("missing attestation count exceeds represented assessments")
        if self.nonapproved_attestation_count > self.represented_assessment_count:
            raise GovernanceError("nonapproved attestation count exceeds represented assessments")
        _enum("state", self.state, AggregationAssessmentState)
        gaps = tuple(self.gaps)
        if gaps != tuple(sorted(set(gaps))):
            raise GovernanceError("aggregation assessment gaps must be sorted and unique")
        object.__setattr__(self, "assessed_at", _timestamp("assessed_at", self.assessed_at))
        for field in (
            "bcbs239_compliance_determined",
            "risk_data_accuracy_determined",
            "supervisory_acceptance_determined",
        ):
            if _bool(field, getattr(self, field)):
                raise GovernanceError(f"aggregation assessment cannot set {field}=true")
        expected = AggregationAssessmentState.MET
        if self.missing_assessment_count or self.incomplete_report_count or self.missing_attestation_count:
            expected = AggregationAssessmentState.INCOMPLETE
        elif self.breached_report_count or self.nonapproved_attestation_count:
            expected = AggregationAssessmentState.BREACHED
        if self.state is not expected:
            raise GovernanceError("aggregation assessment state is inconsistent with evidence counts")
        if self.state is AggregationAssessmentState.MET and gaps:
            raise GovernanceError("met aggregation assessment cannot carry gaps")
        if self.state is not AggregationAssessmentState.MET and not gaps:
            raise GovernanceError("non-met aggregation assessment must explain gaps")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ExecutiveAssuranceAttestation:
    institution_id: str
    attestation_id: str
    aggregation_assessment_digest: str
    owner_id: str
    decision: AttestationDecision
    rationale: str
    evidence_digest: str
    attested_at: str
    bcbs239_compliance_determined: bool = False
    schema_version: str = "datagovops.bcbs239-executive-attestation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "attestation_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("aggregation_assessment_digest", self.aggregation_assessment_digest)
        _enum("decision", self.decision, AttestationDecision)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "attested_at", _timestamp("attested_at", self.attested_at))
        if _bool("bcbs239_compliance_determined", self.bcbs239_compliance_determined):
            raise GovernanceError("executive attestation does not determine BCBS 239 compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class BCBS239AssuranceRegistry:
    """Institution-scoped multi-report assurance over the strict v0.2 reporting registry."""

    def __init__(self, reporting_registry: ReportingGovernanceRegistry) -> None:
        if not isinstance(reporting_registry, ReportingGovernanceRegistry):
            raise GovernanceError("BCBS 239 assurance requires strict public ReportingGovernanceRegistry")
        self.reporting_registry = reporting_registry
        self.asset_registry = reporting_registry.asset_registry
        self._taxonomy: dict[tuple[str, str, int], ReportTaxonomyEntry] = {}
        self._portfolios: dict[tuple[str, str, int], RiskDataPortfolio] = {}
        self._assessments: dict[str, RiskDataAggregationAssessment] = {}
        self._attestations: dict[tuple[str, str], ExecutiveAssuranceAttestation] = {}

    def register_taxonomy(self, entry: ReportTaxonomyEntry) -> str:
        report = self.reporting_registry._report_by_digest(entry.report_digest)
        self.reporting_registry._assert_report_current(report)
        if report.institution_id != entry.institution_id:
            raise GovernanceError("report taxonomy uses different institution")
        self.asset_registry.principal(entry.institution_id, entry.owner_id)
        key = (entry.institution_id, entry.taxonomy_id, entry.taxonomy_version)
        existing = self._taxonomy.get(key)
        if existing is not None:
            if existing.artifact_digest != entry.artifact_digest:
                raise GovernanceError("taxonomy identity/version already exists with different content")
            return existing.artifact_digest
        history = self.taxonomy_history(entry.institution_id, entry.taxonomy_id)
        expected = 1 if not history else history[-1].taxonomy_version + 1
        if entry.taxonomy_version != expected:
            raise GovernanceError(f"taxonomy_version must be contiguous; expected version {expected}")
        self._taxonomy[key] = entry
        return entry.artifact_digest

    def taxonomy_history(self, institution_id: str, taxonomy_id: str) -> tuple[ReportTaxonomyEntry, ...]:
        return tuple(
            sorted(
                (
                    value
                    for (scope, current, _), value in self._taxonomy.items()
                    if scope == institution_id and current == taxonomy_id
                ),
                key=lambda item: item.taxonomy_version,
            )
        )

    def latest_taxonomy(self, institution_id: str, taxonomy_id: str) -> ReportTaxonomyEntry:
        history = self.taxonomy_history(institution_id, taxonomy_id)
        if not history:
            raise GovernanceError("unknown report taxonomy")
        return history[-1]

    def assert_taxonomy_current(self, entry: ReportTaxonomyEntry) -> None:
        registered = self._taxonomy.get((entry.institution_id, entry.taxonomy_id, entry.taxonomy_version))
        if registered is None or registered.artifact_digest != entry.artifact_digest:
            raise GovernanceError("report taxonomy is not exact registered evidence")
        if self.latest_taxonomy(entry.institution_id, entry.taxonomy_id).artifact_digest != entry.artifact_digest:
            raise GovernanceError("report taxonomy is stale")
        report = self.reporting_registry._report_by_digest(entry.report_digest)
        self.reporting_registry._assert_report_current(report)

    def register_portfolio(self, portfolio: RiskDataPortfolio) -> str:
        self.asset_registry.principal(portfolio.institution_id, portfolio.owner_id)
        for digest in portfolio.report_digests:
            report = self.reporting_registry._report_by_digest(digest)
            self.reporting_registry._assert_report_current(report)
            if report.institution_id != portfolio.institution_id:
                raise GovernanceError("risk-data portfolio uses report from different institution")
        taxonomy = tuple(self._taxonomy_by_digest(value) for value in portfolio.taxonomy_digests)
        if len(taxonomy) != len(portfolio.report_digests):
            raise GovernanceError("risk-data portfolio requires exactly one taxonomy entry per report")
        for entry in taxonomy:
            self.assert_taxonomy_current(entry)
            if entry.institution_id != portfolio.institution_id:
                raise GovernanceError("risk-data portfolio uses taxonomy from different institution")
        if {item.report_digest for item in taxonomy} != set(portfolio.report_digests):
            raise GovernanceError("risk-data portfolio taxonomy/report manifest mismatch")
        represented_domains = {item.risk_domain for item in taxonomy}
        if not set(portfolio.required_risk_domains).issubset(represented_domains):
            raise GovernanceError("risk-data portfolio is missing required risk-domain taxonomy coverage")
        key = (portfolio.institution_id, portfolio.portfolio_id, portfolio.portfolio_version)
        existing = self._portfolios.get(key)
        if existing is not None:
            if existing.artifact_digest != portfolio.artifact_digest:
                raise GovernanceError("portfolio identity/version already exists with different content")
            return existing.artifact_digest
        history = self.portfolio_history(portfolio.institution_id, portfolio.portfolio_id)
        expected = 1 if not history else history[-1].portfolio_version + 1
        if portfolio.portfolio_version != expected:
            raise GovernanceError(f"portfolio_version must be contiguous; expected version {expected}")
        self._portfolios[key] = portfolio
        return portfolio.artifact_digest

    def portfolio_history(self, institution_id: str, portfolio_id: str) -> tuple[RiskDataPortfolio, ...]:
        return tuple(
            sorted(
                (
                    value
                    for (scope, current, _), value in self._portfolios.items()
                    if scope == institution_id and current == portfolio_id
                ),
                key=lambda item: item.portfolio_version,
            )
        )

    def latest_portfolio(self, institution_id: str, portfolio_id: str) -> RiskDataPortfolio:
        history = self.portfolio_history(institution_id, portfolio_id)
        if not history:
            raise GovernanceError("unknown risk-data portfolio")
        return history[-1]

    def assert_portfolio_current(self, portfolio: RiskDataPortfolio) -> None:
        registered = self._portfolios.get(
            (portfolio.institution_id, portfolio.portfolio_id, portfolio.portfolio_version)
        )
        if registered is None or registered.artifact_digest != portfolio.artifact_digest:
            raise GovernanceError("risk-data portfolio is not exact registered evidence")
        if self.latest_portfolio(portfolio.institution_id, portfolio.portfolio_id).artifact_digest != portfolio.artifact_digest:
            raise GovernanceError("risk-data portfolio is stale")
        for digest in portfolio.report_digests:
            report = self.reporting_registry._report_by_digest(digest)
            self.reporting_registry._assert_report_current(report)
        for digest in portfolio.taxonomy_digests:
            self.assert_taxonomy_current(self._taxonomy_by_digest(digest))

    def evaluate_portfolio(
        self,
        portfolio: RiskDataPortfolio,
        period_id: str,
        *,
        assessed_at: str,
    ) -> RiskDataAggregationAssessment:
        self.assert_portfolio_current(portfolio)
        period_id = _text("period_id", period_id)
        assessed_at = _timestamp("assessed_at", assessed_at)
        assessment_digests: list[str] = []
        attestation_digests: list[str] = []
        met = breached = incomplete = missing_assessment = missing_attestation = nonapproved = 0
        gaps: set[str] = set()

        for report_digest in portfolio.report_digests:
            report = self.reporting_registry._report_by_digest(report_digest)
            assessment = self._latest_report_assessment(report_digest, period_id, assessed_at)
            if assessment is None:
                missing_assessment += 1
                gaps.add(f"assessment_missing:{report.report_id}")
                continue
            assessment_digests.append(assessment.artifact_digest)
            if assessment.state is ReportingAssessmentState.MET:
                met += 1
            elif assessment.state is ReportingAssessmentState.BREACHED:
                breached += 1
                gaps.add(f"assessment_breached:{report.report_id}")
            else:
                incomplete += 1
                gaps.add(f"assessment_incomplete:{report.report_id}")

            attestation = self._latest_report_attestation(assessment.artifact_digest, assessed_at)
            if attestation is None:
                missing_attestation += 1
                gaps.add(f"owner_attestation_missing:{report.report_id}")
            else:
                attestation_digests.append(attestation.artifact_digest)
                if attestation.decision is not AttestationDecision.APPROVED:
                    nonapproved += 1
                    gaps.add(f"owner_attestation_{attestation.decision.value}:{report.report_id}")

        state = AggregationAssessmentState.MET
        if missing_assessment or incomplete or missing_attestation:
            state = AggregationAssessmentState.INCOMPLETE
        elif breached or nonapproved:
            state = AggregationAssessmentState.BREACHED

        result = RiskDataAggregationAssessment(
            institution_id=portfolio.institution_id,
            portfolio_digest=portfolio.artifact_digest,
            period_id=period_id,
            report_assessment_digests=tuple(assessment_digests),
            report_attestation_digests=tuple(attestation_digests),
            portfolio_report_count=len(portfolio.report_digests),
            represented_assessment_count=len(assessment_digests),
            met_report_count=met,
            breached_report_count=breached,
            incomplete_report_count=incomplete,
            missing_assessment_count=missing_assessment,
            missing_attestation_count=missing_attestation,
            nonapproved_attestation_count=nonapproved,
            state=state,
            gaps=tuple(sorted(gaps)),
            assessed_at=assessed_at,
        )
        self._assessments[result.artifact_digest] = result
        return result

    def assert_assessment_current(self, assessment: RiskDataAggregationAssessment) -> None:
        registered = self._assessments.get(assessment.artifact_digest)
        if registered is None or registered != assessment:
            raise GovernanceError("unknown risk-data aggregation assessment")
        portfolio = self._portfolio_by_digest(assessment.portfolio_digest)
        current = self.evaluate_portfolio(
            portfolio,
            assessment.period_id,
            assessed_at=assessment.assessed_at,
        )
        if current.artifact_digest != assessment.artifact_digest:
            raise GovernanceError("risk-data aggregation assessment is stale")

    def register_executive_attestation(self, attestation: ExecutiveAssuranceAttestation) -> str:
        assessment = self._assessment(attestation.aggregation_assessment_digest)
        self.assert_assessment_current(assessment)
        if assessment.institution_id != attestation.institution_id:
            raise GovernanceError("executive assurance attestation uses different institution")
        portfolio = self._portfolio_by_digest(assessment.portfolio_digest)
        self.asset_registry.principal(attestation.institution_id, attestation.owner_id)
        if attestation.owner_id != portfolio.owner_id:
            raise GovernanceError("executive assurance attestation must use the accountable portfolio owner")
        if _parse_time(attestation.attested_at) < _parse_time(assessment.assessed_at):
            raise GovernanceError("executive assurance attestation cannot predate aggregation assessment")
        if (
            attestation.decision is AttestationDecision.APPROVED
            and assessment.state is not AggregationAssessmentState.MET
        ):
            raise GovernanceError("non-met aggregation assessment cannot be approved")
        key = (attestation.institution_id, attestation.attestation_id)
        existing = self._attestations.get(key)
        if existing is not None and existing.artifact_digest != attestation.artifact_digest:
            raise GovernanceError("executive attestation_id already exists with different content")
        self._attestations.setdefault(key, attestation)
        return attestation.artifact_digest

    def snapshot_digest(self, institution_id: str) -> str:
        self.asset_registry.snapshot_digest(institution_id)
        return digest_artifact(
            {
                "institution_id": institution_id,
                "reporting_registry_snapshot_digest": self.reporting_registry.snapshot_digest(institution_id),
                "taxonomy": sorted(
                    item.artifact_digest
                    for item in self._taxonomy.values()
                    if item.institution_id == institution_id
                ),
                "portfolios": sorted(
                    item.artifact_digest
                    for item in self._portfolios.values()
                    if item.institution_id == institution_id
                ),
                "assessments": sorted(
                    item.artifact_digest
                    for item in self._assessments.values()
                    if item.institution_id == institution_id
                ),
                "executive_attestations": sorted(
                    item.artifact_digest
                    for item in self._attestations.values()
                    if item.institution_id == institution_id
                ),
            }
        )

    def _latest_report_assessment(
        self,
        report_digest: str,
        period_id: str,
        assessed_at: str,
    ) -> ReportAssuranceAssessment | None:
        candidates = tuple(
            item
            for item in self.reporting_registry._assessments.values()
            if item.report_digest == report_digest
            and item.period_id == period_id
            and _parse_time(item.assessed_at) <= _parse_time(assessed_at)
        )
        if not candidates:
            return None
        latest_time = max(_parse_time(item.assessed_at) for item in candidates)
        latest = tuple(item for item in candidates if _parse_time(item.assessed_at) == latest_time)
        if len({item.artifact_digest for item in latest}) > 1:
            raise GovernanceError("conflicting latest report assurance assessments fail closed")
        assessment = latest[0]
        self.reporting_registry.assert_assessment_current(assessment)
        return assessment

    def _latest_report_attestation(
        self,
        assessment_digest: str,
        assessed_at: str,
    ) -> ReportOwnerAttestation | None:
        candidates = tuple(
            item
            for item in self.reporting_registry._attestations.values()
            if item.assessment_digest == assessment_digest
            and _parse_time(item.attested_at) <= _parse_time(assessed_at)
        )
        if not candidates:
            return None
        latest_time = max(_parse_time(item.attested_at) for item in candidates)
        latest = tuple(item for item in candidates if _parse_time(item.attested_at) == latest_time)
        if len({item.artifact_digest for item in latest}) > 1:
            raise GovernanceError("conflicting latest report owner attestations fail closed")
        return latest[0]

    def _taxonomy_by_digest(self, digest: str) -> ReportTaxonomyEntry:
        for item in self._taxonomy.values():
            if item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown report taxonomy digest")

    def _portfolio_by_digest(self, digest: str) -> RiskDataPortfolio:
        for item in self._portfolios.values():
            if item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown risk-data portfolio digest")

    def _assessment(self, digest: str) -> RiskDataAggregationAssessment:
        try:
            return self._assessments[digest]
        except KeyError as exc:
            raise GovernanceError("unknown risk-data aggregation assessment") from exc
