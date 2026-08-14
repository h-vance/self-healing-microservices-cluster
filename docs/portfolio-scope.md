# Portfolio Scope

This repository is a compact cloud/SRE portfolio project. It is meant to show judgment, safety defaults, and validation discipline without expanding into a full platform build.

## Production-Aware Patterns Included

- Health and metrics endpoints for a service.
- Node.js tests for HTTP behavior and Prometheus output.
- Container build using `npm ci` and a pinned Node image family.
- Kubernetes probes, resource requests, limits, and basic security contexts.
- Helm linting and template rendering.
- Terraform provider pinning, variables, outputs, formatting, and validation.
- CI that exercises the core validation path.
- Clear docs for configuration, runbooks, architecture, and limitations.

### Verified against a live cluster

The following are not just declared in YAML. A `kind` cluster is created on
every push, faults are injected, and recovery is asserted. See
[evidence/](evidence/).

- Fault injection for liveness failure, container OOM, and pod deletion, with
  assertions that fail the build if recovery does not occur.
- HorizontalPodAutoscaler, PodDisruptionBudget, and NetworkPolicy applied to a
  running workload.
- A live `kube-prometheus-stack` install, so the ServiceMonitor and
  PrometheusRule manifests are actually consumed by an operator rather than
  sitting inert.
- Alertmanager routing a firing alert to an in-cluster remediation controller,
  which performs a scoped `kubectl rollout restart` and records the deployment
  state before and after acting.
- Least-privilege RBAC for that controller: read pods, patch deployments,
  nothing else.

## Intentionally Out Of Scope

- Full VPC, subnet, NAT, EKS, and IAM module design.
- Remote Terraform state and locking.
- Production secret management with AWS Secrets Manager, SOPS, Sealed Secrets, or External Secrets.
- Persistent MongoDB volumes and backup restore validation.
- Multi-zone availability. The CI cluster is a single-node `kind` cluster, so
  zone-spreading and node-failure recovery are not exercised.
- NetworkPolicy **enforcement**. The policy is applied and schema-valid, but
  kind's default CNI (kindnet) does not enforce NetworkPolicy, so it is not
  proven to block traffic. That needs a policy-capable CNI such as Calico.
- Paging, ticketing, or chat integration. Alertmanager routes to the in-cluster
  remediation controller, not to PagerDuty, Jira, or Slack.

## Chaos Engineering Scope

Fault injection covers three failure modes: liveness failure, container OOM,
and pod deletion. Not covered: node failure, network partition, disk pressure,
dependency (MongoDB or Redis) outage, or cascading multi-service failure.

The remediation controller acts on two alertnames against one deployment. The
action allowlist is deliberately closed, so an unmapped alert is recorded and
ignored rather than triggering a guess.

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
