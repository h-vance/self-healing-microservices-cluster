# Evidence

Captured output from real chaos runs against a live `kind` cluster. Every
number below came from an actual execution of `scripts/chaos.sh`, not from a
description of what the script is supposed to do.

The same three scenarios run in CI on every push via
[`.github/workflows/chaos.yml`](../../.github/workflows/chaos.yml), which
uploads a `chaos-evidence` artifact containing the JSON records and the
remediation controller's logs.

| Scenario | Fault injected | Recovery mechanism | Observed |
|---|---|---|---|
| [liveness](liveness.md) | `/healthz` forced to 503 | kubelet restarts container on liveness failure | restart after 84s, ready 12s later |
| [oom](oom.md) | allocate past the 128Mi limit | kubelet OOM-kills and restarts | restart under 3s, ready 12s later |
| [pod-delete](pod-delete.md) | `kubectl delete pod` | Deployment controller replaces the pod | replacement Ready after 33s |
| [remediation-loop](remediation-loop.md) | same liveness fault | Prometheus alert routed to the controller, which restarts the deployment | remediated in 40.9s |

The first three show Kubernetes healing itself. The fourth shows the alerting
path wired to an actuator, which is the part that does not come for free.

## Why the assertions are trustworthy

Three properties keep these from being theatre:

1. **The script fails the build when healing does not happen.** Verified by
   deleting the `livenessProbe` from the Deployment and re-running: the
   liveness scenario exited non-zero. Restoring the probe made it pass again.
2. **Assertions are scoped to one named pod.** `pick_target` selects a single
   Running and Ready pod, and recovery is asserted against that pod's own
   `restartCount`. A restart elsewhere in the ReplicaSet cannot satisfy it.
3. **Each scenario starts from a settled cluster.** `settle()` waits for 3/3
   Ready with a stable restart count before injecting, so a restart still in
   flight from a previous scenario cannot be miscredited to this one.

The OOM scenario additionally asserts
`lastState.terminated.reason == OOMKilled`, distinguishing a real kernel OOM
kill from the process merely exiting.

A fourth property was added the hard way. The workflow now asserts that
Alertmanager adopted the remediation route and that the controller wrote a
record, because an earlier build passed all three scenarios while the
remediation loop silently never fired. See
[remediation-loop.md](remediation-loop.md) for what broke and why the
assertion exists.
