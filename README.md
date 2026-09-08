# Dogfood

Dogfood turns findings into checked improvements and retains them for future work. It includes a plugin for Codex and ChatGPT Work, a durable local ledger, and workflows for background work and self-improvement.

**Release status: 0.1.0 development build.** The local engine and hook output are tested. Automatic activation in every Work chat, real unattended execution, and a second user's plugin installation are not verified. No hosted service is included.

## Contents

- `.codex-plugin/plugin.json`: plugin identity and skill discovery.
- `skills/dogfood`: autonomous improvement workflow and platform references.
- `skills/setup`: storage, activation, and schedule setup.
- `skills/status`: pause, resume, inspection, and reversal.
- `hooks/hooks.json`: Codex session-start hook using the default discovery path.
- `scripts/engine.py`: transactional findings, revisions, leases, evidence, budgets, and portable snapshots.
- `scripts/configure.py`: local store setup and a managed instructions block.
- `tests/test_engine.py`: executable regression cases.

Python 3.10 or later is required for local helpers. No third-party Python packages are required by the runtime.

## Installation

Use the supported plugin creation or import flow on the target host with this folder as the plugin source. A marketplace must reference this folder; this build does not register or publish a marketplace automatically. The source repository is [GhostlyGawd/dogfood-plugin](https://github.com/GhostlyGawd/dogfood-plugin). A license and any marketplace registration remain unset.

On Codex, the bundled hook needs the host's hook trust review before it runs. It emits the installed core skill path at session start, resume, and compaction. It does not collect transcripts or change permissions. [Official hook documentation](https://learn.chatgpt.com/docs/hooks).

Start Dogfood setup to select persistent state and configure background work. The local helper can be invoked from this folder:

```bash
python3 scripts/configure.py init --state-dir /absolute/persistent/dogfood-state --owner your-owner-label
```

Use an actual directory owned by the current user. Do not reuse the example path literally. The result identifies settings and database paths. For Work, use the core skill's Work state adapter and exact remote file identities. The bundled core skill provides the Work operating instructions. The attempted separate Work companion installation did not succeed.

Installation alone does not guarantee all-chat activation. Work may need a supported persistent custom instruction entry. Mark activation pending until a fresh chat demonstrates it.

## Background work

This project's daily Improve Dogfood task is enabled and uses `runtime/state.json` on the separate `dogfood-state` branch. The interactive state workflow passed verification; a completed unattended run has not yet been observed. Other users must configure their own state and task. See [Work activation](docs/work-activation.md) for the remaining all-chat setup step.

Use the native scheduler through the setup skill. Save the concrete state identity and skill reference in its prompt. Desktop jobs need the local project and required runtime to remain available. Web jobs need accessible durable context and connected tools. [Official scheduled task documentation](https://learn.chatgpt.com/docs/automations).

Default budgets are one unrelated improvement during active work and three changes or 20 minutes for a background run. User settings can change these limits. A missing scheduler is a reported capability gap.

## Verification

```bash
python3 -m unittest discover -s tests -v
```

See [verification results](docs/verification.md) and the [approved build spec](docs/build-spec.md). The ledger records receipts from host tools; it does not execute project changes or independently authenticate check outputs. The operating skill must inspect actual evidence and apply target-native version checks. Local leases do not create remote transaction guarantees.

## Upgrade and removal

Keep findings outside the package. Update through the host's supported plugin or personal skill flow. Keep a working version and verify a fresh run before marking an instruction change active. A changed hook can require another trust review.

To remove an optional instructions block, use `configure.py remove-instructions` with the same state directory and exact instructions file. Disable the identified native schedule and plugin through host controls. Keep findings unless their deletion is explicitly requested.
