import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engine import Ledger, Conflict
from configure import instructions


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.db"
        self.now = [1000.0]
        self.ledger = Ledger(self.path, clock=lambda: self.now[0])
        self.ledger.dispatch("init", {"owner": "test-user"})

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def call(self, action, **data):
        return self.ledger.dispatch(action, data)

    def capture(self, observation="Missing input check", project="project-a"):
        return self.call("capture", project=project, observation=observation, evidence=["fixture:failure"])['finding']

    def move(self, f, status, **extra):
        data = dict(id=f["id"], revision=f["revision"], status=status, reason="fixture evidence")
        if f.get("lease"):
            data["token"] = f["lease"]["token"]
        data.update(extra)
        return self.call("transition", **data)

    def ready(self, **extra):
        return self.move(self.capture(), "ready", scope="project", destination="project-a/check.py", **extra)

    def claim(self, f=None, **run_options):
        f = f or self.ready()
        run = self.call("start-run", worker="worker-a", projects=[f["project"]], **run_options)
        return self.call("claim", id=f["id"], revision=f["revision"], run=run["id"])

    def edit_args(self, f):
        return dict(id=f["id"], revision=f["revision"], token=f["lease"]["token"])

    def changed(self, f=None):
        f = f or self.claim()
        data = dict(operation_key="change-1", target="project-a/check.py", before_version="sha-before",
                    after_version="sha-after", reversal_ref="fixture:reverse", evidence_ref="fixture:diff")
        if f.get("scope") == "dogfood":
            data["evaluator_version"] = "fixed-evaluator-v1"
        f = self.call("record-change", **self.edit_args(f), **data)
        return self.move(f, "verifying")

    def test_duplicate_findings_are_project_scoped(self):
        f = self.capture()
        self.assertEqual(self.capture()["id"], f["id"])
        self.assertNotEqual(self.capture(project="project-b")["id"], f["id"])

    def test_owner_cannot_change(self):
        with self.assertRaises(Conflict):
            self.call("init", owner="another-user")

    def test_stale_revision_rejected(self):
        f = self.capture()
        self.move(f, "deferred", resume_when="new evidence")
        with self.assertRaises(Conflict):
            self.move(f, "rejected")

    def test_only_one_concurrent_worker_claims(self):
        f = self.ready()
        runs = [self.call("start-run", worker=str(i), projects=["project-a"]) for i in range(2)]
        def claim(run):
            ledger = Ledger(self.path, clock=lambda: self.now[0])
            try:
                ledger.dispatch("claim", {"id": f["id"], "revision": f["revision"], "run": run["id"]})
                return True
            except Conflict:
                return False
            finally:
                ledger.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(claim, runs)), 1)

    def test_project_scope_enforced(self):
        f = self.ready()
        run = self.call("start-run", worker="worker", projects=["another-project"])
        with self.assertRaises(Conflict):
            self.call("claim", id=f["id"], revision=f["revision"], run=run["id"])

    def test_pause_stops_claims_and_changes(self):
        f = self.claim()
        self.call("pause", paused=True)
        with self.assertRaises(Conflict):
            self.call("heartbeat", **self.edit_args(f))
        self.call("pause", paused=False)
        self.assertEqual(self.call("heartbeat", **self.edit_args(f))["status"], "in_progress")

    def test_project_pause_does_not_pause_other_project(self):
        self.call("pause", project="project-a", paused=True)
        self.assertEqual(self.call("start-run", worker="w", projects=["project-b"])["state"], "running")

    def test_budget_expires_and_old_worker_is_rejected(self):
        f = self.claim(seconds=5)
        self.now[0] += 6
        with self.assertRaises(Conflict):
            self.call("heartbeat", **self.edit_args(f))

    def test_change_count_budget_enforced(self):
        f = self.claim(max_changes=1)
        other = self.move(self.capture("Another finding"), "ready", scope="project", destination="project-a/other.py")
        with self.assertRaises(Conflict):
            self.call("claim", id=other["id"], revision=other["revision"], run=f["lease"]["run"])

    def test_expired_work_requires_reconciliation(self):
        f = self.claim()
        self.now[0] += 301
        f = self.call("recover", id=f["id"], revision=f["revision"])
        self.assertTrue(f["recovery_required"])
        with self.assertRaises(Conflict):
            self.move(f, "ready", scope="project", destination="project-a/check.py")
        f = self.call("reconcile", id=f["id"], revision=f["revision"], outcome="unchanged", evidence_ref="fixture:current-hash")
        self.assertEqual(self.move(f, "ready", scope="project", destination="project-a/check.py")["status"], "ready")

    def test_applied_recovery_cannot_blindly_retry(self):
        f = self.claim()
        self.now[0] += 301
        f = self.call("recover", id=f["id"], revision=f["revision"])
        f = self.call("reconcile", id=f["id"], revision=f["revision"], outcome="applied", evidence_ref="fixture:target")
        self.assertTrue(f["recovery_required"])

    def test_failed_checks_prevent_application(self):
        f = self.changed()
        f = self.call("record-check", **self.edit_args(f), name="regression", evidence_ref="fixture:output", exit_code=1, verified_version="sha-after")
        with self.assertRaises(ValueError):
            self.move(f, "applied", activation="active")

    def test_wrong_version_cannot_pass(self):
        f = self.changed()
        f = self.call("record-check", **self.edit_args(f), name="test", evidence_ref="fixture:output", exit_code=0, verified_version="another-version")
        with self.assertRaises(ValueError):
            self.move(f, "applied", activation="active")

    def test_complete_lifecycle_requires_activation_and_reuse(self):
        f = self.changed()
        f = self.call("record-check", **self.edit_args(f), name="test", evidence_ref="fixture:output", exit_code=0, verified_version="sha-after")
        f = self.move(f, "applied", activation="pending")
        with self.assertRaises(ValueError):
            self.move(f, "adopted")
        f = self.call("activate", id=f["id"], revision=f["revision"], evidence_ref="fresh-run:loaded")
        f = self.call("reuse", id=f["id"], revision=f["revision"], session="later-session", evidence_ref="later:success")
        self.assertEqual(self.move(f, "adopted")["status"], "adopted")

    def test_self_change_cannot_change_evaluator(self):
        f = self.move(self.capture(), "ready", scope="dogfood", destination="skills/dogfood/SKILL.md")
        f = self.changed(self.claim(f))
        with self.assertRaises(Conflict):
            self.call("record-check", **self.edit_args(f), name="test", evidence_ref="fixture:output", exit_code=0,
                      verified_version="sha-after", evaluator_version="weakened-v2")

    def test_personal_promotion_requires_evidence(self):
        f = self.capture()
        with self.assertRaises(ValueError):
            self.move(f, "ready", scope="personal", destination="global instructions")

    def test_snapshot_round_trip_and_owner_isolation(self):
        f = self.claim()
        snapshot = self.call("export")
        restored = Ledger(Path(self.tmp.name) / "restored.db", clock=lambda: self.now[0])
        try:
            with self.assertRaises(Conflict):
                restored.dispatch("restore", {"owner": "other", "snapshot": snapshot})
            restored.dispatch("restore", {"owner": "test-user", "snapshot": snapshot})
            self.assertEqual(restored.finding(f["id"]), f)
            with self.assertRaises(Conflict):
                restored.dispatch("restore", {"owner": "test-user", "snapshot": snapshot})
        finally:
            restored.close()

    def test_fresh_process_reads_durable_state(self):
        f = self.capture()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/engine.py"), "--db", str(self.path), "get"],
                                input=json.dumps({"id": f["id"]}), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["result"]["id"], f["id"])

    def test_checkpoint_revokes_remaining_claims(self):
        f = self.claim()
        self.call("checkpoint", run=f["lease"]["run"], summary="save unfinished work")
        f = self.call("get", id=f["id"])
        with self.assertRaises(Conflict):
            self.call("heartbeat", **self.edit_args(f))

    def test_instruction_setup_is_idempotent_and_preserves_text(self):
        target = Path(self.tmp.name) / "AGENTS.md"
        target.write_text("Keep my existing rule.\n")
        self.assertTrue(instructions(target, self.tmp.name)["changed"])
        self.assertFalse(instructions(target, self.tmp.name)["changed"])
        self.assertTrue(instructions(target, self.tmp.name, remove=True)["changed"])
        self.assertIn("Keep my existing rule.", target.read_text())
        self.assertNotIn("dogfood:start", target.read_text())

    def test_hook_emits_valid_context_from_another_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / "hooks/session_start.py")], cwd=self.tmp.name,
                                text=True, capture_output=True, check=True)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn(str(ROOT / "skills/dogfood/SKILL.md"), output["additionalContext"])


if __name__ == "__main__":
    unittest.main()
