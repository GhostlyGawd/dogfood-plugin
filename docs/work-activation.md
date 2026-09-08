# Work activation

The project now has a native daily task and a GitHub state branch. This setup covers `GhostlyGawd/dogfood-plugin`. The separate Work companion installation has not succeeded. It does not activate Dogfood in unrelated chats.

For Work across chats, the account needs a persistent instruction that loads the workflow. If the host does not expose a supported tool for that setting, the user must add it through their customization controls. Use this text:

> Use my Dogfood workflow for continuous improvement during my work. Load the current operating instructions from `https://github.com/GhostlyGawd/dogfood-plugin/blob/main/skills/dogfood/SKILL.md` using the connected GitHub tools. Complete my main task, apply useful broader improvements within my existing permissions, save evidence and unfinished work to the appropriate private or project store, and verify later reuse. Honor pause state and finite budgets. The public dogfood-plugin state branch is only for findings derived from that repository; do not store private chats or other projects there. If a required tool or durable store is unavailable, state that limit and continue independent work.

This is a source-loading instruction. It is not proof that the native plugin is installed. Verify it in a fresh Work chat without naming Dogfood: check whether the workflow is loaded and whether the appropriate state is read. If it is not, keep all-chat activation marked unverified.

For Codex sessions opened in this repository, the root `AGENTS.md` supplies project guidance. For other local projects, the setup helper can add a managed entry to an authorized effective instructions file. The user must select the applicable global or project scope. Do not alter managed instructions or bypass hook trust.

The daily task loads source directly from GitHub and does not depend on the separate companion installation. Its exact task ID is private installation metadata. Pause or change the task through the host's Scheduled controls. Other users must create their own state and schedule.
