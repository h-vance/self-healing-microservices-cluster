# Alertmanager remediation loop

The other three scenarios prove Kubernetes recovers a workload on its own.
This one proves the alerting path is wired to an actuator: a metric crosses a
threshold, an alert fires, Alertmanager routes it, and something acts.

**Path:** app exports `app_health_status` -> Prometheus scrapes it ->
`NodeAppUnhealthy` fires after 30s -> Alertmanager matches
`remediation=restart_deployment` -> POST to the controller -> scoped
`kubectl rollout restart` -> state captured before and after.

## Captured record

Written by the controller during the liveness scenario and collected as part of
the `chaos-evidence` artifact:

```json
{
  "alertname": "NodeAppUnhealthy",
  "action": "restart_deployment",
  "deployment": "node-metrics-app",
  "remediated": true,
  "duration_seconds": 40.9,
  "before": { "ready_replicas": "3/4" },
  "after":  { "ready_replicas": "3/3" }
}
```

`3/4` before and `3/3` after is the rollout in progress: the restart had begun
and a replacement ReplicaSet was scaling up when the "before" snapshot was
taken. The controller waits on `kubectl rollout status` before recording
`remediated: true`, so the flag reflects a completed rollout rather than a
command that merely returned zero.

## The failure that made this worth asserting

The first green run of `chaos.yml` was misleading. All three chaos scenarios
passed, and `remediation-records.json` in the artifact was **0 bytes**. The
controller log showed only health probes. The loop had never fired, and
nothing in the workflow noticed, because recovery was asserted but the
alert-to-action path was not.

Root cause took three wrong guesses to find. It was not the selectors:

```
msg="skipping alertmanagerconfig"
error="unable to get secret \"smtp-secret\": secrets \"smtp-secret\" not found"
reason=InvalidConfiguration
```

The repo shipped an AlertmanagerConfig containing an email receiver pointing at
`smtp.example.com`, whose `authPassword` referenced a Secret that was never
created. prometheus-operator validates the object as a whole, so it refused to
adopt any of it, and the working webhook route in the same file was rejected
alongside the broken email one. `amtool config routes show` confirmed the
routing tree contained only the default route and `Watchdog`.

Two changes came out of it. The placeholder email receiver was deleted, since a
fake receiver is not worth breaking a real one. And the workflow now asserts
both that Alertmanager adopted the route at deploy time and that the controller
wrote a record, so this specific silence cannot recur.
