#!/usr/bin/env python3
"""Dogfood durable ledger. Python 3.10+, standard library only.

All requests are JSON objects on stdin. Output is JSON. The ledger records
agent changes; it does not grant permissions or execute arbitrary commands.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import uuid

VERSION = "0.1.0"
SCHEMA = 1
TERMINAL = {"adopted", "rejected", "superseded", "reverted"}
TRANSITIONS = {
    "captured": {"ready", "deferred", "blocked", "rejected", "superseded"},
    "ready": {"deferred", "blocked", "rejected", "superseded"},
    "in_progress": {"verifying", "deferred", "blocked"},
    "verifying": {"applied", "blocked", "reverted"},
    "applied": {"adopted", "reverted", "superseded"},
    "adopted": {"reverted", "superseded"},
    "deferred": {"ready", "rejected", "superseded"},
    "blocked": {"ready", "rejected", "superseded", "reverted"},
    "rejected": set(), "superseded": set(), "reverted": set(),
}


class Conflict(ValueError):
    pass


def required(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Ledger:
    def __init__(self, path, clock=time.time):
        self.path = Path(path).resolve()
        self.clock = clock
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY, project TEXT NOT NULL, dedup TEXT NOT NULL,
            revision INTEGER NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL,
            UNIQUE(project,dedup));
          CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
            kind TEXT NOT NULL, entity TEXT NOT NULL, body TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    @contextlib.contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value)))

    def event(self, kind, entity, body):
        self.db.execute("INSERT INTO events(at,kind,entity,body) VALUES (?,?,?,?)",
                        (self.clock(), kind, entity, json.dumps(body)))

    def finding(self, fid):
        row = self.db.execute("SELECT body FROM findings WHERE id=?", (fid,)).fetchone()
        if not row:
            raise ValueError("finding does not exist")
        return json.loads(row[0])

    def save(self, f):
        f["revision"] += 1
        f["updated_at"] = self.clock()
        self.db.execute("UPDATE findings SET revision=?,status=?,body=? WHERE id=?",
                        (f["revision"], f["status"], json.dumps(f), f["id"]))

    def run(self, rid):
        row = self.db.execute("SELECT body FROM runs WHERE id=?", (rid,)).fetchone()
        if not row:
            raise ValueError("run does not exist")
        return json.loads(row[0])

    def save_run(self, r):
        self.db.execute("INSERT OR REPLACE INTO runs VALUES (?,?)", (r["id"], json.dumps(r)))

    def writable(self, project):
        if self.meta("paused", False) or project in self.meta("paused_projects", []):
            raise Conflict("Dogfood is paused")

    def active(self, r, project):
        self.writable(project)
        if r["state"] != "running" or r["deadline"] <= self.clock():
            raise Conflict("run ended or budget expired; checkpoint and start a new run")
        if project not in r["projects"]:
            raise Conflict("run is not scoped to this project")

    def edit(self, data, leased=False):
        f = self.finding(required(data, "id"))
        if data.get("revision") != f["revision"]:
            raise Conflict("revision changed; reload the finding")
        self.writable(f["project"])
        if leased:
            lease = f.get("lease") or {}
            if lease.get("token") != data.get("token") or lease.get("until", 0) <= self.clock():
                raise Conflict("lease missing, expired, or owned by another worker")
            r = self.run(lease["run"])
            self.active(r, f["project"])
        return f

    def init(self, data):
        owner = required(data, "owner")
        if self.meta("owner") not in (None, owner):
            raise Conflict("this store belongs to another owner")
        self.set_meta("owner", owner)
        self.set_meta("schema", SCHEMA)
        if self.meta("installation") is None:
            self.set_meta("installation", str(uuid.uuid4()))
            self.set_meta("paused", False)
            self.set_meta("paused_projects", [])
        return {"owner": owner, "installation": self.meta("installation"), "version": VERSION}

    def capture(self, data):
        project, observation = required(data, "project"), required(data, "observation")
        evidence = data.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("evidence must contain at least one source reference")
        dedup = data.get("dedup") or digest((observation.strip().lower()).encode())
        if not isinstance(dedup, str) or not dedup:
            raise ValueError("invalid duplicate key")
        old = self.db.execute("SELECT id FROM findings WHERE project=? AND dedup=?", (project, dedup)).fetchone()
        if old:
            return {"duplicate": True, "finding": self.finding(old[0])}
        fid = str(uuid.uuid4())
        f = {"id": fid, "project": project, "owner": self.meta("owner"),
             "dedup": dedup, "observation": observation, "evidence": evidence,
             "hypothesis": bool(data.get("hypothesis", True)), "benefit": data.get("benefit", ""),
             "status": "captured", "revision": 0, "created_at": self.clock(),
             "updated_at": self.clock(), "lease": None, "changes": [], "checks": [],
             "activation": "not_applied", "reuse": [], "recovery_required": False}
        self.db.execute("INSERT INTO findings VALUES (?,?,?,?,?,?)",
                        (fid, project, dedup, 0, "captured", json.dumps(f)))
        self.event("captured", fid, {"project": project})
        return {"duplicate": False, "finding": f}

    def start_run(self, data):
        projects = data.get("projects")
        if not isinstance(projects, list) or not projects or not all(isinstance(x, str) and x for x in projects):
            raise ValueError("projects must be a non-empty list")
        trigger = data.get("trigger", "active")
        if trigger not in {"active", "background", "manual"}:
            raise ValueError("invalid trigger")
        seconds = data.get("seconds", 1200)
        maximum = data.get("max_changes", 1 if trigger == "active" else 3)
        if type(seconds) is not int or not 1 <= seconds <= 86400 or type(maximum) is not int or not 1 <= maximum <= 100:
            raise ValueError("invalid finite run budget")
        for project in projects:
            self.writable(project)
        r = {"id": str(uuid.uuid4()), "worker": required(data, "worker"), "projects": projects,
             "trigger": trigger, "state": "running", "deadline": self.clock() + seconds,
             "max_changes": maximum, "claimed": [], "checkpoint": None}
        self.save_run(r)
        self.event("run_started", r["id"], {"trigger": trigger})
        return r

    def claim(self, data):
        f = self.edit(data)
        r = self.run(required(data, "run"))
        self.active(r, f["project"])
        if f["status"] != "ready":
            raise Conflict("only ready findings can be claimed")
        if len(r["claimed"]) >= r["max_changes"]:
            raise Conflict("run change budget exhausted")
        if f.get("lease") and f["lease"]["until"] > self.clock():
            raise Conflict("finding is already claimed")
        f["lease"] = {"run": r["id"], "token": str(uuid.uuid4()), "until": min(self.clock() + 300, r["deadline"])}
        f["status"] = "in_progress"
        r["claimed"].append(f["id"])
        self.save_run(r)
        self.save(f)
        self.event("claimed", f["id"], {"run": r["id"]})
        return f

    def heartbeat(self, data):
        f = self.edit(data, leased=True)
        r = self.run(f["lease"]["run"])
        f["lease"]["until"] = min(self.clock() + 300, r["deadline"])
        self.save(f)
        return f

    def transition(self, data):
        before = self.finding(required(data, "id"))
        f = self.edit(data, leased=before["status"] in {"in_progress", "verifying"})
        target = required(data, "status")
        if target not in TRANSITIONS[f["status"]]:
            raise Conflict(f"cannot move {f['status']} to {target}")
        reason = required(data, "reason")
        if target == "ready":
            if f["recovery_required"]:
                raise Conflict("recovery must be resolved first")
            scope = data.get("scope", f.get("scope"))
            if scope not in {"project", "personal", "harness", "dogfood"}:
                raise ValueError("scope is required")
            f.update(scope=scope, destination=required(data, "destination"), scope_reason=reason)
            if scope == "personal" and not data.get("generalization_evidence"):
                raise ValueError("personal scope needs evidence beyond the source project")
            f["generalization_evidence"] = data.get("generalization_evidence")
        if target == "verifying" and not f["changes"]:
            raise ValueError("record a change before verification")
        if target == "applied":
            if not f["checks"] or any(c["exit_code"] != 0 for c in f["checks"]):
                raise ValueError("all recorded checks must pass")
            if not all(c.get("verified_version") == f["changes"][-1]["after_version"] for c in f["checks"]):
                raise ValueError("checks do not match the latest change version")
            f["activation"] = data.get("activation", "pending")
            if f["activation"] not in {"pending", "active"}:
                raise ValueError("invalid activation status")
        if target == "adopted":
            if f["activation"] != "active" or not f["reuse"]:
                raise ValueError("adoption needs activation and later use evidence")
        if target == "reverted" and not data.get("reversal_evidence"):
            raise ValueError("reversal evidence is required")
        if target in {"deferred", "blocked"} and not data.get("resume_when"):
            raise ValueError("resume_when is required")
        if target == "superseded" and not data.get("replacement"):
            raise ValueError("replacement finding or artifact is required")
        previous = f["status"]
        f.update(status=target, reason=reason, resume_when=data.get("resume_when"),
                 replacement=data.get("replacement"), reversal_evidence=data.get("reversal_evidence"))
        if target not in {"in_progress", "verifying"}:
            f["lease"] = None
        self.save(f)
        self.event("transition", f["id"], {"from": previous, "to": target, "reason": reason})
        return f

    def record_change(self, data):
        f = self.edit(data, leased=True)
        if f["status"] != "in_progress":
            raise Conflict("changes must be recorded during in_progress")
        change = {key: required(data, key) for key in
                  ("operation_key", "target", "before_version", "after_version", "reversal_ref", "evidence_ref")}
        if f.get("scope") == "dogfood":
            change["evaluator_version"] = required(data, "evaluator_version")
        for existing in f["changes"]:
            if existing["operation_key"] == change["operation_key"]:
                if existing != change:
                    raise Conflict("operation key already has different content")
                return f
        f["changes"].append(change)
        if f["checks"]:
            f.setdefault("check_history", []).extend(f["checks"])
        f["checks"] = []
        self.save(f)
        self.event("change_recorded", f["id"], change)
        return f

    def record_check(self, data):
        f = self.edit(data, leased=True)
        if f["status"] != "verifying":
            raise Conflict("finding is not in verification")
        check = {key: required(data, key) for key in ("name", "evidence_ref", "verified_version")}
        code = data.get("exit_code")
        if type(code) is not int:
            raise ValueError("exit_code must be an integer from actual tool output")
        check["exit_code"] = code
        if f.get("scope") == "dogfood":
            ev = required(data, "evaluator_version")
            if ev != f["changes"][-1]["evaluator_version"]:
                raise Conflict("the evaluator changed during this candidate")
            check["evaluator_version"] = ev
        f["checks"].append(check)
        self.save(f)
        return f

    def activate(self, data):
        f = self.edit(data)
        if f["status"] not in {"applied", "adopted"}:
            raise Conflict("only applied changes can be activated")
        f["activation_evidence"] = required(data, "evidence_ref")
        f["activation"] = "active"
        self.save(f)
        return f

    def reuse(self, data):
        f = self.edit(data)
        if f["status"] not in {"applied", "adopted"}:
            raise Conflict("only applied improvements can be reused")
        evidence = required(data, "evidence_ref")
        session = required(data, "session")
        f["reuse"].append({"session": session, "evidence_ref": evidence, "at": self.clock()})
        self.save(f)
        return f

    def recover(self, data):
        f = self.finding(required(data, "id"))
        if data.get("revision") != f["revision"]:
            raise Conflict("revision changed")
        if f["status"] not in {"in_progress", "verifying"}:
            raise Conflict("no interrupted work to recover")
        lease = f.get("lease") or {}
        if lease.get("until", 0) > self.clock():
            raise Conflict("the worker still owns the lease")
        f.update(status="blocked", lease=None, recovery_required=True,
                 reason="Worker lease expired. Inspect the target before retrying.",
                 resume_when="Reconcile actual artifact versions with recorded changes.")
        self.save(f)
        self.event("recovery_required", f["id"], {})
        return f

    def reconcile(self, data):
        f = self.edit(data)
        if not f["recovery_required"]:
            raise Conflict("finding does not require recovery")
        outcome = data.get("outcome")
        if outcome not in {"unchanged", "reverted", "applied", "diverged"}:
            raise ValueError("invalid reconciliation outcome")
        f["reconciliation"] = {"outcome": outcome, "evidence_ref": required(data, "evidence_ref")}
        # An already-applied or diverged target cannot be blindly retried.
        f["recovery_required"] = outcome in {"applied", "diverged"}
        f["resume_when"] = "Inspect and reverse or complete the partial change" if f["recovery_required"] else "Plan against the current target version"
        self.save(f)
        return f

    def checkpoint(self, data):
        r = self.run(required(data, "run"))
        r["checkpoint"] = required(data, "summary")
        r["state"] = "finished" if data.get("finished") else "checkpointed"
        self.save_run(r)
        for fid in r["claimed"]:
            f = self.finding(fid)
            if f.get("lease") and f["lease"]["run"] == r["id"]:
                f["lease"]["until"] = self.clock()
                self.save(f)
        self.event("checkpoint", r["id"], {"summary": r["checkpoint"]})
        return r

    def pause(self, data):
        if type(data.get("paused")) is not bool:
            raise ValueError("paused must be a boolean")
        project = data.get("project")
        if project:
            values = set(self.meta("paused_projects", []))
            values.add(project) if data["paused"] else values.discard(project)
            self.set_meta("paused_projects", sorted(values))
        else:
            self.set_meta("paused", data["paused"])
        self.event("pause", project or "installation", {"paused": data["paused"]})
        return {"paused": self.meta("paused"), "paused_projects": self.meta("paused_projects")}

    def list_findings(self, data):
        result = [json.loads(x[0]) for x in self.db.execute("SELECT body FROM findings ORDER BY rowid")]
        if data.get("project"):
            result = [x for x in result if x["project"] == data["project"]]
        if data.get("status"):
            result = [x for x in result if x["status"] == data["status"]]
        limit = data.get("limit", 50)
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        return result[:limit]

    def status(self, data):
        return {"version": VERSION, "owner": self.meta("owner"), "installation": self.meta("installation"),
                "paused": self.meta("paused", False), "paused_projects": self.meta("paused_projects", []),
                "counts": {r[0]: r[1] for r in self.db.execute("SELECT status,count(*) FROM findings GROUP BY status")},
                "runs": [json.loads(x[0]) for x in self.db.execute("SELECT body FROM runs ORDER BY rowid DESC LIMIT 10")]}

    def export(self, data):
        return {"schema": SCHEMA,
                "meta": {r[0]: json.loads(r[1]) for r in self.db.execute("SELECT key,value FROM meta")},
                "findings": [json.loads(x[0]) for x in self.db.execute("SELECT body FROM findings ORDER BY rowid")],
                "runs": [json.loads(x[0]) for x in self.db.execute("SELECT body FROM runs")],
                "events": [dict(x) for x in self.db.execute("SELECT * FROM events ORDER BY seq")]}

    def restore(self, data):
        if self.meta("owner") is not None or self.db.execute("SELECT count(*) FROM findings").fetchone()[0]:
            raise Conflict("restore requires a new empty database")
        snapshot = data.get("snapshot")
        if not isinstance(snapshot, dict) or snapshot.get("schema") != SCHEMA:
            raise ValueError("unsupported snapshot schema")
        metadata = snapshot.get("meta", {})
        if metadata.get("owner") != required(data, "owner"):
            raise Conflict("snapshot owner does not match")
        for key, value in metadata.items():
            self.set_meta(key, value)
        for f in snapshot.get("findings", []):
            if f.get("owner") != metadata["owner"] or f.get("status") not in TRANSITIONS:
                raise ValueError("invalid finding owner or status")
            if type(f.get("revision")) is not int or f["revision"] < 0:
                raise ValueError("invalid finding revision")
            self.db.execute("INSERT INTO findings VALUES (?,?,?,?,?,?)",
                            (required(f, "id"), required(f, "project"), required(f, "dedup"),
                             f["revision"], f["status"], json.dumps(f)))
        for r in snapshot.get("runs", []):
            self.save_run(r)
        for e in snapshot.get("events", []):
            self.db.execute("INSERT INTO events VALUES (?,?,?,?,?)",
                            (e["seq"], e["at"], e["kind"], e["entity"], e["body"]))
        return self.status({})

    def dispatch(self, action, data):
        methods = {"init": self.init, "capture": self.capture, "start-run": self.start_run,
                   "claim": self.claim, "heartbeat": self.heartbeat, "transition": self.transition,
                   "record-change": self.record_change, "record-check": self.record_check,
                   "activate": self.activate, "reuse": self.reuse, "recover": self.recover,
                   "reconcile": self.reconcile, "checkpoint": self.checkpoint, "pause": self.pause,
                   "list": self.list_findings, "status": self.status, "export": self.export, "restore": self.restore,
                   "get": lambda d: self.finding(required(d, "id"))}
        if action not in methods:
            raise ValueError("unknown action")
        with self.transaction():
            if action not in {"init", "restore"} and self.meta("owner") is None:
                raise ValueError("initialize the store first")
            return methods[action](data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Explicit durable SQLite database path")
    parser.add_argument("action")
    args = parser.parse_args()
    ledger = None
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("request must be a JSON object")
        parent = Path(args.db).expanduser().resolve().parent
        parent.mkdir(parents=True, exist_ok=True)
        ledger = Ledger(Path(args.db).expanduser())
        result = ledger.dispatch(args.action, data)
        os.chmod(ledger.path, 0o600)
        print(json.dumps({"ok": True, "result": result}))
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "type": type(exc).__name__}))
        return 1
    finally:
        if ledger:
            ledger.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
