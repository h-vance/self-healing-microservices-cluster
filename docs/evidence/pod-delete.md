# Pod deletion

**Fault:** `kubectl delete pod <name>`, the bluntest failure available. Nothing
inside the app is involved.

**Expected recovery:** the ReplicaSet controller notices the observed replica
count no longer matches the desired count and schedules a replacement.

## Run

```
20:27:06 === scenario: pod-delete ===
20:27:15 settled: 3/3 ready, 2 total restarts
20:27:15 injecting: deleting pod node-metrics-app-5db9c776b5-7t6dv
pod "node-metrics-app-5db9c776b5-7t6dv" deleted from default namespace
20:27:15 waiting: the deleted pod to be replaced
20:27:49 recovered after 33s: the deleted pod to be replaced
20:27:49 waiting: all replicas ready again
20:27:49 recovered after 0s: all replicas ready again
```

The 33s is mostly graceful termination: the deleted pod drains before the
replacement reports Ready. By the time the replacement existed, the other two
replicas had already been serving throughout, so the second assertion passed
immediately.

## What this one demonstrates that the others do not

Service continuity. With `replicas: 3` and a PodDisruptionBudget of
`minAvailable: 2`, losing one pod never takes the service to zero. The
liveness and OOM scenarios prove a container comes back; this proves the
service stayed up while it did.
