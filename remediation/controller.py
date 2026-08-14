#!/usr/bin/env python3
"""Alertmanager webhook receiver that performs scoped Kubernetes remediation.

Alertmanager POSTs a firing alert here; the controller matches it against a
small allowlist of known remediations, captures the deployment state before
and after acting, and writes a JSON evidence record. Capturing both sides is
the point: it is what turns "the alert fired" into "the remediation ran and
the workload came back".

The action allowlist is deliberately closed. An alert naming an unknown
deployment, or carrying an unmapped alertname, is recorded and ignored rather
than triggering a best-guess kubectl command.

Ported from the decision logic in n8n-workflow-as-code's
container-incident-responder workflow, which does the same before/after
capture against a live kind cluster.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

NAMESPACE = os.environ.get("REMEDIATION_NAMESPACE", "default")
EVIDENCE_DIR = Path(os.environ.get("EVIDENCE_DIR", "/tmp/evidence"))

# How long kubectl itself is allowed to wait, e.g. `rollout status --timeout`.
KUBECTL_TIMEOUT = int(os.environ.get("KUBECTL_TIMEOUT", "120"))

# The subprocess must outlive kubectl's own deadline, otherwise the two race
# and Python kills kubectl at the exact moment kubectl would have reported a
# clean timeout. The margin turns that into a readable result instead.
SUBPROCESS_MARGIN = 15

# alertname -> (action, deployment). Anything not listed here is a no-op.
REMEDIATIONS = {
    "NodeAppUnhealthy": ("restart_deployment", "node-metrics-app"),
    "NodeAppCrashLooping": ("restart_deployment", "node-metrics-app"),
}


def kubectl(*args: str) -> tuple[int, str, str]:
    """Run kubectl and return (returncode, stdout, stderr).

    Never raises. A hung kubectl is reported as a normal non-zero result so
    the caller records a failed remediation, rather than an exception
    escaping into the request handler and taking down the response.
    """
    try:
        proc = subprocess.run(
            ["kubectl", "-n", NAMESPACE, *args],
            capture_output=True,
            text=True,
            timeout=KUBECTL_TIMEOUT + SUBPROCESS_MARGIN,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"kubectl {' '.join(args)} exceeded {KUBECTL_TIMEOUT + SUBPROCESS_MARGIN}s"
    except OSError as exc:
        return 127, "", f"could not execute kubectl: {exc}"

    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def capture_state(deployment: str) -> dict:
    """Snapshot what a reviewer would want to see: readiness and restarts."""
    rc, out, err = kubectl(
        "get", "deployment", deployment,
        "-o", "jsonpath={.status.readyReplicas}/{.status.replicas}",
    )
    ready = out if rc == 0 else f"error: {err}"

    rc, out, err = kubectl(
        "get", "pods", "-l", f"app={deployment}",
        "-o", "jsonpath={range .items[*]}{.metadata.name}={.status.containerStatuses[0].restartCount} {end}",
    )
    restarts = {}
    if rc == 0 and out:
        for pair in out.split():
            name, _, count = pair.partition("=")
            if name:
                restarts[name] = int(count) if count.isdigit() else None

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "ready_replicas": ready,
        "restart_counts": restarts,
    }


def restart_deployment(deployment: str) -> dict:
    rc, out, err = kubectl("rollout", "restart", f"deployment/{deployment}")
    if rc != 0:
        return {"ok": False, "step": "rollout restart", "error": err}

    rc, out, err = kubectl(
        "rollout", "status", f"deployment/{deployment}", f"--timeout={KUBECTL_TIMEOUT}s"
    )
    return {
        "ok": rc == 0,
        "step": "rollout status",
        "detail": out or err,
    }


def handle_alert(alert: dict) -> dict:
    labels = alert.get("labels", {})
    alertname = labels.get("alertname", "")
    mapping = REMEDIATIONS.get(alertname)

    record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "alertname": alertname,
        "status": alert.get("status"),
        "labels": labels,
    }

    if alert.get("status") != "firing":
        record.update(action="none", reason="alert is not firing")
        return record

    if mapping is None:
        record.update(action="none", reason=f"no remediation mapped for {alertname!r}")
        return record

    action, deployment = mapping
    record["action"] = action
    record["deployment"] = deployment
    record["before"] = capture_state(deployment)

    started = time.monotonic()
    record["result"] = restart_deployment(deployment)
    record["duration_seconds"] = round(time.monotonic() - started, 2)

    record["after"] = capture_state(deployment)
    record["remediated"] = bool(record["result"].get("ok"))
    return record


def write_evidence(record: dict) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    path = EVIDENCE_DIR / f"remediation-{stamp}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


class Handler(BaseHTTPRequestHandler):
    server_version = "RemediationController/1.0"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/healthz":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "route_not_found"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/alert":
            self._respond(404, {"error": "route_not_found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid_json"})
            return

        records = [handle_alert(a) for a in payload.get("alerts", [])]
        for record in records:
            path = write_evidence(record)
            print(
                f"level=info alertname={record.get('alertname')!r} "
                f"action={record.get('action')} remediated={record.get('remediated')} "
                f"evidence={path}",
                flush=True,
            )

        self._respond(200, {"handled": len(records), "records": records})

    def _respond(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"level=info client={self.client_address[0]} msg={fmt % args}", flush=True)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    print(f"level=info event=controller_started port={port} namespace={NAMESPACE}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
