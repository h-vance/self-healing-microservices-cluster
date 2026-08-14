"""Tests for the remediation controller's decision logic.

kubectl is stubbed so these run anywhere, including in the validation CI job
that has no cluster. The live path is exercised separately by the chaos
workflow against a real kind cluster.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import controller  # noqa: E402


class HandleAlertTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(controller, "kubectl", return_value=(0, "3/3", ""))
        self.kubectl = patcher.start()
        self.addCleanup(patcher.stop)

    def test_ignores_resolved_alerts(self) -> None:
        record = controller.handle_alert(
            {"status": "resolved", "labels": {"alertname": "NodeAppUnhealthy"}}
        )

        self.assertEqual(record["action"], "none")
        self.assertNotIn("result", record)
        self.kubectl.assert_not_called()

    def test_ignores_unmapped_alertname(self) -> None:
        record = controller.handle_alert(
            {"status": "firing", "labels": {"alertname": "SomethingElse"}}
        )

        self.assertEqual(record["action"], "none")
        self.assertIn("no remediation mapped", record["reason"])
        self.kubectl.assert_not_called()

    def test_firing_mapped_alert_restarts_and_captures_both_sides(self) -> None:
        record = controller.handle_alert(
            {"status": "firing", "labels": {"alertname": "NodeAppUnhealthy"}}
        )

        self.assertEqual(record["action"], "restart_deployment")
        self.assertEqual(record["deployment"], "node-metrics-app")
        self.assertTrue(record["remediated"])
        self.assertIn("before", record)
        self.assertIn("after", record)
        self.assertIn("duration_seconds", record)

        called = [c.args for c in self.kubectl.call_args_list]
        self.assertIn(("rollout", "restart", "deployment/node-metrics-app"), called)

    def test_failed_restart_is_reported_not_swallowed(self) -> None:
        self.kubectl.side_effect = [
            (0, "3/3", ""),           # before: ready replicas
            (0, "", ""),              # before: restart counts
            (1, "", "connection refused"),  # rollout restart fails
            (0, "1/3", ""),           # after: ready replicas
            (0, "", ""),              # after: restart counts
        ]

        record = controller.handle_alert(
            {"status": "firing", "labels": {"alertname": "NodeAppUnhealthy"}}
        )

        self.assertFalse(record["remediated"])
        self.assertEqual(record["result"]["error"], "connection refused")


class KubectlTests(unittest.TestCase):
    """A hung or missing kubectl must never escape as an exception."""

    def test_timeout_returns_result_not_exception(self) -> None:
        import subprocess as sp

        with mock.patch.object(
            controller.subprocess, "run",
            side_effect=sp.TimeoutExpired(cmd="kubectl", timeout=135),
        ):
            rc, out, err = controller.kubectl("rollout", "status", "deployment/x")

        self.assertEqual(rc, 124)
        self.assertIn("exceeded", err)

    def test_subprocess_deadline_exceeds_kubectl_deadline(self) -> None:
        # If these are equal, Python kills kubectl at the moment kubectl would
        # have reported a clean timeout, which is what crashed the handler.
        self.assertGreater(controller.SUBPROCESS_MARGIN, 0)

        captured = {}

        def fake_run(cmd, **kwargs):
            captured.update(kwargs)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(controller.subprocess, "run", side_effect=fake_run):
            controller.kubectl("get", "pods")

        self.assertGreater(captured["timeout"], controller.KUBECTL_TIMEOUT)

    def test_missing_binary_returns_result(self) -> None:
        with mock.patch.object(
            controller.subprocess, "run", side_effect=OSError("No such file")
        ):
            rc, _, err = controller.kubectl("get", "pods")

        self.assertEqual(rc, 127)
        self.assertIn("could not execute", err)


class CaptureStateTests(unittest.TestCase):
    def test_parses_restart_counts(self) -> None:
        with mock.patch.object(
            controller,
            "kubectl",
            side_effect=[(0, "2/3", ""), (0, "pod-a=1 pod-b=0 ", "")],
        ):
            state = controller.capture_state("node-metrics-app")

        self.assertEqual(state["ready_replicas"], "2/3")
        self.assertEqual(state["restart_counts"], {"pod-a": 1, "pod-b": 0})

    def test_surfaces_kubectl_error(self) -> None:
        with mock.patch.object(
            controller, "kubectl", side_effect=[(1, "", "NotFound"), (1, "", "NotFound")]
        ):
            state = controller.capture_state("missing")

        self.assertIn("NotFound", state["ready_replicas"])


class EvidenceTests(unittest.TestCase):
    def test_writes_readable_json(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(controller, "EVIDENCE_DIR", Path(tmp)):
                path = controller.write_evidence({"alertname": "NodeAppUnhealthy"})

            self.assertTrue(path.exists())
            self.assertEqual(
                json.loads(path.read_text())["alertname"], "NodeAppUnhealthy"
            )


if __name__ == "__main__":
    unittest.main()
