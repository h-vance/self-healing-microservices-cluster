#!/usr/bin/env bash
# Fault injection and recovery assertions against a live cluster.
#
# Each scenario injects a real fault, then asserts the workload recovers on its
# own. The assertions are the point: if recovery does not happen inside the
# timeout, the script exits non-zero and CI fails. A chaos job that always
# passes proves nothing.
#
# Usage: scripts/chaos.sh <scenario>
#   liveness   force /healthz to 503 and expect a kubelet restart
#   oom        allocate past the memory limit and expect an OOMKilled restart
#   pod-delete delete a pod and expect the Deployment to replace it
set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
DEPLOYMENT="${DEPLOYMENT:-node-metrics-app}"
EVIDENCE_DIR="${EVIDENCE_DIR:-evidence}"
TIMEOUT="${TIMEOUT:-180}"

mkdir -p "$EVIDENCE_DIR"

log() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }

ready_replicas() {
  kubectl -n "$NAMESPACE" get deployment "$DEPLOYMENT" \
    -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo 0
}

total_restarts() {
  kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" \
    -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' 2>/dev/null \
    | awk '{s+=$1} END {print s+0}'
}

pod_names() {
  kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" \
    -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null | sort
}

pod_restarts() {
  kubectl -n "$NAMESPACE" get pod "$1" \
    -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo 0
}

# Wait until every replica is Ready and the aggregate restart count stops
# moving. Without this, a restart still in flight from the previous scenario
# can satisfy the next scenario's assertion and the test passes without the
# injection having done anything.
settle() {
  local stable=0 last=-1 current waited=0
  while (( stable < 3 )); do
    current="$(total_restarts)"
    if [ "$(ready_replicas)" = "3" ] && [ "$current" = "$last" ]; then
      stable=$((stable + 1))
    else
      stable=0
    fi
    last="$current"
    sleep 2
    waited=$((waited + 2))
    if (( waited >= TIMEOUT )); then
      log "FAIL: cluster never settled within ${TIMEOUT}s"
      kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" >&2 || true
      return 1
    fi
  done
  log "settled: 3/3 ready, ${last} total restarts"
}

snapshot() {
  cat <<EOF
{
  "at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ready_replicas": "$(ready_replicas)",
  "total_restarts": $(total_restarts),
  "pods": [$(pod_names | sed 's/.*/"&"/' | paste -sd, -)]
}
EOF
}

# Wait until $1 (a shell predicate) succeeds, or fail after $TIMEOUT seconds.
wait_for() {
  local desc="$1" predicate="$2" waited=0
  log "waiting: $desc"
  while ! eval "$predicate"; do
    if (( waited >= TIMEOUT )); then
      log "FAIL: timed out after ${TIMEOUT}s waiting for: $desc"
      kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" -o wide >&2 || true
      kubectl -n "$NAMESPACE" describe deployment "$DEPLOYMENT" >&2 || true
      return 1
    fi
    sleep 3
    waited=$((waited + 3))
  done
  log "recovered after ${waited}s: $desc"
  LAST_WAIT="$waited"
}

app_exec() {
  # Reach the app from inside the cluster so no ingress is required. A failure
  # here means the fault was never injected, so the scenario must abort rather
  # than fall through to an assertion that could pass for unrelated reasons.
  if ! kubectl -n "$NAMESPACE" run "chaos-curl-$RANDOM" --rm -i --restart=Never \
      --image=curlimages/curl:8.10.1 --quiet -- \
      curl -sS -m 10 -X POST "$@" >/dev/null; then
    log "FAIL: could not reach $* to inject the fault"
    return 1
  fi
}

# Pick one pod and return "name ip". Assertions are made against this exact
# pod so a restart elsewhere in the ReplicaSet cannot satisfy them.
#
# Only Running pods that are Ready are eligible. Selecting .items[0] blindly
# can return a Terminating pod left over from a rollout, whose IP is already
# unroutable, which shows up as a confusing curl timeout rather than a clear
# failure.
pick_target() {
  local line
  line="$(kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" \
    -o jsonpath='{range .items[?(@.status.phase=="Running")]}{.metadata.name} {.status.podIP} {.status.conditions[?(@.type=="Ready")].status} {.metadata.deletionTimestamp}{"\n"}{end}' \
    | awk '$3=="True" && $4=="" {print $1, $2; exit}')"

  if [ -z "$line" ]; then
    log "FAIL: no Running+Ready pod available to target"
    kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOYMENT" >&2 || true
    return 1
  fi
  printf '%s' "$line"
}

pod_exists() {
  kubectl -n "$NAMESPACE" get pod "$1" >/dev/null 2>&1
}

scenario_liveness() {
  local name ip before
  read -r name ip <<<"$(pick_target)"
  before="$(pod_restarts "$name")"

  log "injecting: forcing /healthz to 503 on $name ($ip), restarts=$before"
  app_exec "http://${ip}:3000/admin/toggle-health"

  # Two mechanisms race to fix this, and either one is a valid recovery:
  #
  #   kubelet     restarts the container in place once the liveness probe has
  #               failed failureThreshold times (~84s with this probe config)
  #   controller  Alertmanager fires NodeAppUnhealthy at 30s and the
  #               remediation controller restarts the whole deployment,
  #               which replaces this pod outright
  #
  # The controller is usually faster, so asserting only on this pod's
  # restartCount fails once the remediation loop is working. Accept either and
  # record which one won.
  wait_for "$name to restart in place, or be replaced by a rollout" \
    "[ \"\$(pod_restarts $name)\" -gt $before ] || ! pod_exists $name" || return 1

  wait_for "all replicas ready again" "[ \"\$(ready_replicas)\" = \"3\" ]" || return 1

  if pod_exists "$name"; then
    local after
    after="$(pod_restarts "$name")"
    [ "$after" -gt "$before" ] || { log "FAIL: $name neither restarted nor was replaced"; return 1; }
    RECOVERY_MECHANISM="kubelet_restart"
    log "verified: kubelet restarted $name in place, restarts $before -> $after"
  else
    RECOVERY_MECHANISM="deployment_rollout"
    log "verified: $name was replaced by a rollout, 3/3 ready"
  fi
}

scenario_oom() {
  local name ip before
  read -r name ip <<<"$(pick_target)"
  before="$(pod_restarts "$name")"

  log "injecting: allocating past the 128Mi limit on $name ($ip), restarts=$before"
  app_exec "http://${ip}:3000/admin/exhaust-memory?chunk_mb=16" || true

  wait_for "$name to be OOM-killed and restarted" \
    "[ \"\$(pod_restarts $name)\" -gt $before ]" || return 1

  wait_for "all replicas ready again" "[ \"\$(ready_replicas)\" = \"3\" ]" || return 1

  # Distinguish a real kernel OOM kill from the process merely exiting.
  local reason
  reason="$(kubectl -n "$NAMESPACE" get pod "$name" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null || true)"
  if [ "$reason" = "OOMKilled" ]; then
    RECOVERY_MECHANISM="kubelet_oom_restart"
    log "verified: $name lastState.terminated.reason=OOMKilled"
  else
    log "FAIL: expected OOMKilled, got '${reason:-<empty>}'"
    return 1
  fi
}

scenario_pod_delete() {
  local victim before_pods
  before_pods="$(pod_names)"
  victim="$(echo "$before_pods" | head -1)"

  log "injecting: deleting pod $victim"
  kubectl -n "$NAMESPACE" delete pod "$victim" --wait=false

  wait_for "the deleted pod to be replaced" \
    "! pod_names | grep -qx '$victim'" || return 1

  wait_for "all replicas ready again" \
    "[ \"\$(ready_replicas)\" = \"3\" ]" || return 1

  RECOVERY_MECHANISM="replicaset_replacement"
}

main() {
  local scenario="${1:?usage: chaos.sh <liveness|oom|pod-delete>}"

  log "=== scenario: $scenario ==="
  # Always start from a quiet cluster so the assertions below can only be
  # satisfied by this scenario's own injection.
  settle || exit 1

  local before after
  before="$(snapshot)"

  case "$scenario" in
    liveness)   scenario_liveness ;;
    oom)        scenario_oom ;;
    pod-delete) scenario_pod_delete ;;
    *) log "unknown scenario: $scenario"; exit 2 ;;
  esac

  after="$(snapshot)"

  cat > "${EVIDENCE_DIR}/${scenario}.json" <<EOF
{
  "scenario": "$scenario",
  "deployment": "$DEPLOYMENT",
  "namespace": "$NAMESPACE",
  "recovery_mechanism": "${RECOVERY_MECHANISM:-kubernetes_controller}",
  "before": $before,
  "after": $after,
  "recovered": true
}
EOF

  log "=== scenario $scenario recovered, evidence written ==="
}

main "$@"
