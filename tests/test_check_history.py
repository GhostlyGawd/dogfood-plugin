import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from engine import Ledger


class CheckHistoryTests(unittest.TestCase):
    def test_retry_preserves_failed_check_and_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory) / "state.db")
            self.addCleanup(ledger.close)
            call = ledger.dispatch
            call("init", {"owner": "test-owner"})
            f = call("capture", {"project": "test-project", "observation": "retry", "evidence": ["fixture"]})["finding"]

            def move(status, **extra):
                nonlocal f
                args = dict(id=f["id"], revision=f["revision"], status=status, reason="fixture")
                if f.get("lease"):
                    args["token"] = f["lease"]["token"]
                f = call("transition", dict(args, **extra))

            def claim_and_record(version):
                nonlocal f
                move("ready", scope="project", destination="fixture")
                run = call("start-run", {"worker": "test-worker", "projects": ["test-project"]})
                f = call("claim", {"id": f["id"], "revision": f["revision"], "run": run["id"]})
                f = call("record-change", dict(id=f["id"], revision=f["revision"], token=f["lease"]["token"],
                    operation_key=version, target="fixture", before_version="base", after_version=version,
                    reversal_ref="fixture:reverse", evidence_ref="fixture:change"))

            claim_and_record("candidate-one")
            move("verifying")
            f = call("record-check", dict(id=f["id"], revision=f["revision"], token=f["lease"]["token"],
                name="failure", evidence_ref="fixture:failure", exit_code=1, verified_version="candidate-one"))
            failed_check = dict(f["checks"][0])
            move("blocked", resume_when="candidate reversed and a new plan is checked")
            claim_and_record("candidate-two")
            self.assertEqual(f["checks"], [])
            self.assertIn(failed_check, f.get("check_history", []))
            restored = Ledger(Path(directory) / "restored.db")
            self.addCleanup(restored.close)
            restored.dispatch("restore", {"owner": "test-owner", "snapshot": call("export", {})})
            self.assertIn(failed_check, restored.finding(f["id"])["check_history"])


if __name__ == "__main__":
    unittest.main()
