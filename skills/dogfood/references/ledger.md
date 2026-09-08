# Ledger contract

Resolve `../../../scripts/engine.py` from this reference directory. Use Python 3.10+. Call `python3 ENGINE --db ABSOLUTE_DB_PATH ACTION` with a JSON object on stdin. Output is `{ "ok": true, "result": ... }` or a structured error. Use an input file or quoted heredoc; never interpolate finding text into shell code.

Finding mutations require the current `id` and `revision`. Claimed work also requires `token`. Save the returned revision after every action. SQLite protects the ledger; host tools must separately protect target files and permissions.

| Action | Inputs |
| --- | --- |
| init | owner: stable non-empty label. |
| capture | project, observation, evidence: non-empty array; optional benefit, hypothesis, dedup. Returns finding and duplicate. |
| transition to ready | id, revision, status, reason, scope, destination; personal scope also needs generalization_evidence. |
| start-run | worker, projects: array, trigger: active/background/manual; optional seconds and max_changes. |
| claim | id, revision, run. Returns lease.token and lease.until. |
| heartbeat | id, revision, token. Renew before the five-minute lease expires. |
| record-change | id, revision, token, operation_key, target, before_version, after_version, reversal_ref, evidence_ref; Dogfood scope also needs evaluator_version. |
| transition to verifying | id, revision, token, status, reason. Requires a recorded change. |
| record-check | id, revision, token, name, evidence_ref, integer exit_code, verified_version; Dogfood scope also needs the unchanged evaluator_version. |
| transition to applied | id, revision, token, status, reason, activation: pending/active. All checks must pass for the latest change version. |
| activate | id, revision, evidence_ref proving the version loaded. |
| reuse | id, revision, session, evidence_ref from later relevant work. |
| transition to adopted | id, revision, status, reason. Requires activation and reuse. |
| transition to blocked/deferred | id, revision, token if claimed, status, reason, resume_when. |
| transition to superseded | id, revision, status, reason, replacement. |
| transition to reverted | id, revision, token if claimed, status, reason, reversal_evidence. Reverse the actual target first. |
| recover | id, revision. Moves an expired claim to blocked; does not replay edits. |
| reconcile | id, revision, outcome: unchanged/reverted/applied/diverged, evidence_ref. Only unchanged or reverted permits a new plan. |
| checkpoint | run, summary, optional finished: boolean. Ends the run and expires remaining claims. |
| pause | paused: boolean; optional project. Capture and recovery bookkeeping remain possible. |
| get | id. |
| list | Optional project, status, limit (1–1000). |
| status | Empty object. |
| export | Empty object. Save the inner result object as the portable snapshot. |
| restore | owner, snapshot: exact exported object. Requires a new empty database. |

Use actual commit IDs or content hashes as versions. Inspect real tool output before recording checks. A receipt is an audit record, not independent proof. Store evidence where later runs can read it.

Keep failed checks. Reverse the failed candidate and create a linked finding for a materially different candidate. Multi-file changes use a tree or commit reference and a reversal that covers all files.

An expired worker must not write with its old token. Inspect actual artifacts before recovery. Use a cooperative project lock or isolated worktree to avoid overlapping edits. Recheck later user changes before applying or reversing a patch.
