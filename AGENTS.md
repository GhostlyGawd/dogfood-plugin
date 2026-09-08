# Dogfood project instructions

Use `skills/dogfood/SKILL.md` as this repository's continuous-improvement workflow. Complete the user's main task and apply useful broader improvements within existing permissions and the configured work budget.

Read the current project state through `skills/dogfood/references/github.md` when the connected GitHub tools are available. Live findings are in `runtime/state.json` on branch `dogfood-state`, not in the source branch. Honor pause state, claims, and current versions before improvement writes. If access is unavailable, complete independent main-task work and state the exact persistence limit.

Keep findings derived from this public project's code and documentation in its state branch. Do not put private chats, personal preferences, secrets, or another project's data there. Keep runtime state outside the distributable plugin source.

Use `python3 -m unittest discover -s tests -v` for changes to the Python engine or setup helpers. Record actual check evidence and reversal references. Follow the core skill's fixed-evaluator procedure for changes to Dogfood's behavior.

Distinguish source saved, plugin installed, instructions loaded, scheduled task enabled, and unattended run verified. Do not claim one from evidence of another. Existing explicit user instructions and host permissions remain authoritative.
