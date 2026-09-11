from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from engine import Conflict, Ledger


class RunChangeBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / "state.db", clock=lambda: 1000.0)
        self.ledger.dispatch("init", {"owner": "test-owner"})
        f = self.ledger.dispatch("capture", {
            "project": "test-project", "observation": "bounded work", "evidence": ["fixture"]
        })["finding"]
        f = self.ledger.dispatch("transition", {
            "id": f["id"], "revision": f["revision"], "status": "ready", "reason": "fixture",
            "scope": "project", "destination": "fixture"
        })
        self.run = self.ledger.dispatch("start-run", {
            "worker": "test-worker", "projects": ["test-project"], "max_changes": 1
        })
        self.finding = self.ledger.dispatch("claim", {
            "id": f["id"], "revision": f["revision"], "run": self.run["id"]
        })

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def record(self, operation):
        f = self.ledger.finding(self.finding["id"])
        return self.ledger.dispatch("record-change", {
            "id": f["id"], "revision": f["revision"], "token": f["lease"]["token"],
            "operation_key": operation, "target": operation, "before_version": "before",
            "after_version": "after", "reversal_ref": "fixture:reverse", "evidence_ref": "fixture:change"
        })

    def test_budget_counts_change_operations_not_only_claims(self):
        self.record("change-one")
        with self.assertRaises(Conflict):
            self.record("change-two")

    def test_idempotent_repeat_does_not_consume_another_change(self):
        first = self.record("change-one")
        repeated = self.record("change-one")
        self.assertEqual(repeated["revision"], first["revision"])
        run = self.ledger.run(self.run["id"])
        self.assertEqual(run["changes_used"], 1)


if __name__ == "__main__":
    unittest.main()
