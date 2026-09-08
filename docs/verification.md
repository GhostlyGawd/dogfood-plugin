# Dogfood verification

Build: 0.1.0 · 8 September 2026

## Automated checks

21 automated cases pass. Coverage includes competing claims, stale revisions, owner mismatch, pause and project scope, time and change budgets, expired-worker recovery, failed or mismatched check versions, activation before adoption, fixed self-evaluation versions, snapshot recovery, a fresh process reading saved state, managed instruction preservation, and hook output from a different directory.

The plugin manifest and all three bundled skill entrypoints pass their format validators. These checks establish file structure, not automatic host invocation.

## Platform status

An independent agent used the packaged core skill on an isolated invoice project. It corrected empty-order shipping and the exact free-shipping threshold, added two regression tests covering ten cases, and recorded the finding as applied. The ledger retained actual content hashes, check output references, and reversal instructions. The run finished without claiming later adoption or a live schedule. The source and resulting ledger were inspected after the run.

| Capability | Result |
| --- | --- |
| Durable local ledger | Verified by independent process read and snapshot round trip. |
| Codex hook payload | Verified locally against the documented output shape. |
| Real Codex session activation | Not tested: no Codex executable in this build environment. |
| Work skill selection | Bundled Work instructions prepared; separate companion installation failed. |
| Work activation in every chat | Unverified: no supported global instruction write route established here. |
| Remote Work state | GitHub state branch passed an interactive read, restore, SHA-guarded claim, source write, and checkpoint. A separate scheduled Work run remains unverified. |
| Native background execution | Daily Improve Dogfood task enabled for this project. No completed unattended run observed yet. |
| Self-improvement | Fixed evaluator receipt check verified. Actual update and fresh-model behavior require host evaluation. |
| Second user's installation | Package prepared; no second account used. |

Codex documents default `hooks/hooks.json` discovery and `PLUGIN_ROOT`. The build omits a manifest hooks field to remain compatible with the local manifest validator. It uses the documented default discovery route. [Official plugin packaging](https://developers.openai.com/plugins/build/plugins).

## Limits

The host agent executes edits, checks, and reversals. The engine records their evidence and protects ledger state. It does not grant access, cancel an in-flight external write, or provide an authenticated multi-user server. Owner labels and separate local stores are not a substitute for server authentication.

Remote state needs a real expected-version write guard and separate protection for the project target. Do not enable unattended external changes with an unguarded snapshot upload. A database export retains all findings; default list output is limited to keep prompts small.

The first build is usable for controlled local work and skill-driven workflows. It does not yet pass every release condition in the approved spec.

The GitHub adapter change passed the unchanged 21-test regression suite and core skill format validation. Evidence is retained at `runtime/evidence/github-adapter.json` on `dogfood-state`. Root project instructions are configured; actual loading in a new Codex session still needs observation.
