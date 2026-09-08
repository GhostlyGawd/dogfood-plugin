---
name: setup
description: Configure Dogfood, connect its persistent findings store, and check supported activation and scheduling for a new installation.
---

# Set up Dogfood

Read [Dogfood](../dogfood/SKILL.md). Determine whether the runtime has persistent local files or a temporary Work workspace. Reuse existing identity and access. Do not alter permission settings to make setup succeed.

For local use, initialize an explicit persistent user-owned state directory with `../../scripts/configure.py init --state-dir ABSOLUTE_PATH --owner OWNER` relative to this skill directory. This writes settings and initializes the ledger. It does not create a schedule or change global instructions.

The plugin bundles `hooks/hooks.json` at the documented default path. Codex requires review and trust of the current hook definition before execution. Use the host hook controls when needed. Dogfood cannot grant that trust itself.

Global or project instructions provide an alternative where supported. Use `configure.py instructions --file ABSOLUTE_INSTRUCTIONS_FILE --state-dir ABSOLUTE_STATE_DIRECTORY` only for an authorized destination. It adds one marked block and preserves other text. Select the effective file after reading override precedence; do not edit system-managed instructions.

For Work, use [the Work adapter](../dogfood/references/work.md). If there is no supported tool for global instructions, prepare this entry for the user's customization settings:

> Use Dogfood during my work. Complete my main task and apply useful broader improvements autonomously within my existing permissions. Load Dogfood's persistent state, honor pause and work budgets, save evidence and unfinished work, and verify later reuse. Use the installed Dogfood skill for setup and operation.

Append the actual state identity once created. Do not claim it is active until a new chat demonstrates it. User action is needed only where the host has no supported write tool.

If installation includes scheduling, use [background instructions](../dogfood/references/background.md). Save the actual schedule ID and test on an isolated fixture. Report activation, state, scheduling, writes, and self-update as separate verified or blocked capabilities. A valid manifest alone does not prove compatibility.
