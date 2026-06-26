# Portfolio Scope

This repository is a compact cloud/SRE portfolio project. It is meant to show judgment, safety defaults, and validation discipline without expanding into a full platform build.

## Production-Aware Patterns Included

- Health and metrics endpoints for a service.
- Node.js tests for HTTP behavior and Prometheus output.
- Container build using `npm ci` and a pinned Node image family.
- Kubernetes probes, resource requests, limits, and basic security contexts.
- Helm linting and template rendering.
- Terraform provider pinning, variables, outputs, formatting, and validation.
- AWS scripts that default to dry-run behavior.
- CI that exercises the core validation path.
- Clear docs for configuration, runbooks, architecture, and limitations.

## Intentionally Out Of Scope

- Full VPC, subnet, NAT, EKS, and IAM module design.
- Remote Terraform state and locking.
- Production secret management with AWS Secrets Manager, SOPS, Sealed Secrets, or External Secrets.
- Persistent MongoDB volumes and backup restore validation.
- NetworkPolicy, PodDisruptionBudget, HPA, and multi-zone availability.
- Live Kubernetes end-to-end tests.
- Real alert routing to incident tooling.
- Automated remediation triggered directly from Alertmanager.

## Why This Scope Works

The repo demonstrates the controls a reviewer expects to see:

- Observability entry points.
- Safe automation defaults.
- Infrastructure validation.
- Kubernetes runtime hygiene.
- Honest documentation about limitations.

That is enough for a portfolio artifact. Expanding this into production would require a separate platform design with account structure, IAM boundaries, environment promotion, state management, secrets, and operational ownership.

## Review Checklist

A reviewer should be able to answer these questions quickly:

- What does the service expose?
- How is it monitored?
- How are manifests validated?
- How are cloud actions made safe?
- What is intentionally not production-ready?
- How would this evolve into a real platform?
