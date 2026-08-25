# Deployment & Runtime Hardening Boundary

DataGovOps v0.7 adds a deterministic reference boundary for deployment and runtime-control evidence. It does not deploy workloads, reach a cluster, resolve secrets, inspect a registry, or assert that a production environment is secure.

## Reference controls

The reference model represents:

- immutable OCI image identity through `repository@sha256:<digest>` references;
- non-root runtime identity;
- read-only root filesystem;
- disabled privilege escalation and privileged mode;
- dropped Linux capabilities;
- `RuntimeDefault` seccomp;
- disabled host network/PID/IPC namespaces;
- disabled service-account token automount;
- default-deny ingress and egress;
- external secret references with no embedded secret value;
- metadata-only runtime observations;
- validator identity and an explicit negative-path confirmation.

`assess_deployment` returns only `represented` or `incomplete`. A represented control means the supplied evidence structurally represents that expectation. It is not proof that a production runtime enforced it.

## Reference deployment files

`deployment/Dockerfile.hardened.reference` intentionally provides no default `BASE_IMAGE`; callers must inject a separately verified digest-pinned base image.

`deployment/kubernetes/workload.template.yaml` is a template, not an apply-ready production manifest. `${DATAGOVOPS_IMAGE_DIGEST}` must be replaced by an immutable image reference. The template uses non-root/read-only/no-privilege-escalation/capability-drop/seccomp settings and a CSI external-secret mount reference.

`deployment/kubernetes/default-deny.yaml` provides explicit ingress and egress default-deny NetworkPolicy references. Any production allowlist must be institution-owned and independently reviewed.

## Explicit non-claims

This boundary does not establish:

- production Kubernetes admission/enforcement;
- image vulnerability absence or registry trust;
- base-image provenance or patch status;
- runtime sandbox effectiveness;
- network-policy effectiveness in a real CNI implementation;
- external-secret provider/KMS/HSM effectiveness;
- production observability coverage;
- production readiness, BCBS 239/privacy/security compliance, certification, or supervisory acceptance.
