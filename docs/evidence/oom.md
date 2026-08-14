# Out of memory

**Fault:** `POST /admin/exhaust-memory?chunk_mb=16` allocates 16MB buffers in a
loop until the container breaches its `memory: 128Mi` limit.

**Expected recovery:** the kernel OOM-kills the process, the kubelet records
`OOMKilled` and restarts the container.

## Run

```
20:26:42 === scenario: oom ===
20:26:51 settled: 3/3 ready, 1 total restarts
20:26:51 injecting: allocating past the 128Mi limit on node-metrics-app-5db9c776b5-7t6dv (10.244.0.23), restarts=1
20:26:54 waiting: node-metrics-app-5db9c776b5-7t6dv to be OOM-killed and restarted
20:26:54 recovered after 0s: node-metrics-app-5db9c776b5-7t6dv to be OOM-killed and restarted
20:26:54 waiting: all replicas ready again
20:27:06 recovered after 12s: all replicas ready again
20:27:06 verified: node-metrics-app-5db9c776b5-7t6dv lastState.terminated.reason=OOMKilled
```

## On the "0s"

The allocation loop pushes past 128Mi in well under the script's three-second
poll interval, so the restart is already visible at the first check. This is
the one place a fast result could hide a false positive, which is why the
scenario does not stop at "the restart count went up". It also asserts:

```
.status.containerStatuses[0].lastState.terminated.reason == OOMKilled
```

A restart from any other cause fails that check. The `settle()` call before
injection also guarantees the count was stable beforehand, so the increment is
attributable to this fault.

## Note

The starting restart count is 1 because the liveness scenario ran immediately
before against the same pod. `settle()` confirmed the cluster was quiet at that
count before injecting, and the assertion is `> 1`, not `> 0`.
