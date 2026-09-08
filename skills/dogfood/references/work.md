# Work state adapter

Use the ledger's JSON snapshot in a durable store with version-checked replacement. ChatGPT Library is a candidate when its tools are available. Follow the host's Library skill. This adapter is an agent workflow, not a bundled remote service.

Setup must create a new store, export the inner result object, save it as a durable JSON file, and retain its exact file ID, owner, and remote version. Keep that identity in supported persistent instructions and the saved task prompt. Do not store user findings in a shared skill package.

If the host cannot read that exact file or replace it with an expected-version condition, mark autonomous Work execution blocked. Do not weaken the version condition. A file attached to one chat does not establish access from all chats.

For each run:

1. Read only the configured file and retain its remote version. Restore the snapshot into a new local database.
2. Start a run and claim a ready finding. Export the snapshot and replace the same remote file with the actual expected version. Retain the new returned version.
3. If the version check fails, discard the local candidate state and reload. Do not change the project after a failed claim save.
4. Before every external write, reread remote state. Check pause, token, lease, project, and run budget. Renew and persist the lease if needed. Do not act from an old local snapshot after another worker changes it.
5. Use target-native version checks or an isolated checkout for the actual change. A ledger lease does not make external tools transactional. If no safe write route exists, record a blocked item.
6. Persist actual changes, check evidence, and checkpoints with expected-version replacement. If saving fails after a target write, stop further writes and preserve target versions for reconciliation.

Remote leases are cooperative; they do not fence external services. Full unattended operation needs a real independent-run test. Current Library replacement offers library_file_id, file, and expected_current_version. Use the actual exposed schema and known identifiers. Do not read unrelated files or another user's Library to test isolation.
