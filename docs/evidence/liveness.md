# Liveness failure

**Fault:** `POST /admin/toggle-health` flips the app's internal state so
`/healthz` returns `503`. The route only exists when `CHAOS_ENABLED=true`.

**Expected recovery:** the kubelet's liveness probe fails repeatedly and the
container is restarted in place. No human action, no external controller.

## Run

```
20:24:51 === scenario: liveness ===
20:25:00 settled: 3/3 ready, 0 total restarts
20:25:00 injecting: forcing /healthz to 503 on node-metrics-app-5db9c776b5-7t6dv (10.244.0.23), restarts=0
20:25:03 waiting: node-metrics-app-5db9c776b5-7t6dv restart count to exceed 0
20:26:30 recovered after 84s: node-metrics-app-5db9c776b5-7t6dv restart count to exceed 0
20:26:30 waiting: all replicas ready again
20:26:42 recovered after 12s: all replicas ready again
20:26:42 verified: node-metrics-app-5db9c776b5-7t6dv restarts 0 -> 1
```

## Why 84 seconds

That is the probe configuration, not latency. `node-app.yaml` sets
`initialDelaySeconds: 15` and `periodSeconds: 20`, and the default
`failureThreshold` is 3, so the kubelet needs roughly three failed checks
before it restarts the container. 84s is the expected window, and a materially
shorter time would suggest something other than the liveness probe caused the
restart.

## Negative control

With the `livenessProbe` block removed from the Deployment, this scenario
fails instead of passing:

```
SCRIPT EXIT CODE: 1
```

Nothing restarts the container, the assertion times out, and CI goes red.
That is the check that makes the passing run meaningful.
