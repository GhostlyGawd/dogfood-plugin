# Dogfood — Build Spec

Version: 0.1 approved · 8 September 2026

Status: Approved by the user. A 0.1.0 development build is included in this repository. See verification.md for tested behavior and outstanding host checks. Approval did not install the plugin or create a live schedule.

## 1. Purpose

Dogfood is an installable plugin for Codex and ChatGPT Work. It turns useful findings into changes that improve future work. It selects an appropriate destination: project files, personal instructions, reusable skills, or the system that runs the agent. That last destination is called the harness in this document.

Dogfood must use available capabilities when they help the work, learn from their results, and make those lessons available to later runs. Success means that an improvement works and is used again when relevant.

## 2. Confirmed requirements

| ID | Requirement |
| --- | --- |
| R1 | Name the plugin Dogfood. Use `dogfood` as its technical identifier. |
| R2 | Target Codex and ChatGPT Work. Other people must be able to install it. |
| R3 | Make the behavior available across chats and projects, without repeated user prompts. |
| R4 | Let Dogfood select and complete useful improvements autonomously. |
| R5 | Include improvements beyond the current task, while still completing that task. |
| R6 | Review past findings and apply unfinished improvements while the user is away. |
| R7 | Save findings and changes so that later work can use them. |
| R8 | Let Dogfood improve its own instructions and skills. |

Full autonomy describes the desired product behavior. Each installation still operates within the user's granted access and the host's permissions. Routine improvement choices must not require repeated confirmation.

## 3. Proposed defaults

These choices make the first build concrete. They are design proposals, not additional answers from the user.

- Each user has separate findings, settings, and access. Do not share lessons between users by default.
- Start with supported host tools, scheduling, and storage. Select a separate service only if a required capability cannot work through those facilities.
- Keep the main task first. Save larger unrelated changes for a background run.
- Select a destination from evidence and relevance. Prefer the smallest scope that solves the problem.
- Keep a version history and a method to reverse each change.
- Show a short report after meaningful work. Keep detailed evidence available on request.
- Set a finite work budget for every run. Proposed starting limits: one unrelated change during active work; three changes or 20 minutes per background run, whichever comes first. The user can change these limits.
- Propose one daily background run in the user's local time. Select the actual time during installation. No schedule is created by this spec.
- Start with a shared code package and separate platform adapters. Do not assume both hosts expose the same tools.

## 4. Platform findings and release conditions

The official plugin documentation describes skills, connectors, MCP tools, hooks, and scheduled task templates. It also describes distribution through marketplace sources. Installation makes capabilities available; it does not establish that Dogfood will execute in every chat. [Official plugin documentation](https://learn.chatgpt.com/docs/plugins).

Codex reads global and project `AGENTS.md` instructions at run startup. This provides a candidate route for persistent Dogfood guidance. Existing overrides, instruction limits, and project rules must be respected. A change to these files is not proof that an existing session has loaded it. [Official AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Scheduled tasks can use skills and plugins. Desktop tasks that need local files require the computer and app to remain running. Web tasks can use accessible uploads and connected tools, but do not retain a local project folder between runs. Availability depends on the host and account settings. [Official scheduled task documentation](https://learn.chatgpt.com/docs/automations).

| Capability | Proposed implementation | Required proof |
| --- | --- | --- |
| Codex activation | Small global instruction entry, with project guidance where appropriate | A fresh session starts Dogfood without a named invocation. |
| Work activation | Supported persistent instructions or lifecycle integration | A fresh Work chat starts Dogfood without a named invocation. Exact route remains open. |
| Durable state | Versioned store accessible to the chosen runtime | A later independent run reads the saved finding and its current status. |
| Background work | Native scheduled task plus Dogfood skill | Run while the user is absent, using the correct identity and project access. |
| Work project changes | Connected repository or other supported write destination | A web run can change and verify the intended artifact. |
| Self-improvement | Versioned skill or instruction change through a supported update route | A fresh run loads the new version; reversal loads the earlier version. |
| Installation by others | Validated plugin package and a supported distribution source | A second user can install and complete setup without the author's private files. |

These are release conditions. If a host cannot provide automatic activation or background execution, report that limitation and leave the corresponding requirement unmet. Do not describe manual invocation as full compliance.

The local Plugin Creator guidance requires `.codex-plugin/plugin.json`. Its validator currently rejects a `hooks` manifest field even though a reference sample includes that field. Keep the base manifest within the validated schema. Investigate hook packaging separately before selecting it as an activation dependency.

## 5. Improvement process

1. **Load context.** Read applicable instructions, current task state, relevant saved findings, and the available capabilities. Read only sources the runtime can access.
2. **Find useful work.** Observe errors, user corrections, repeated manual steps, missing checks, unused useful capabilities, and stale guidance. During background work, also inspect pending findings.
3. **Record evidence.** Save the observation, source reference, expected benefit, and conditions in which it applies. Mark an untested idea as a hypothesis.
4. **Select the change.** Check for duplicates, conflicting rules, current versions, access, cost, and main task needs. Record why the selected destination fits.
5. **Apply the change.** Use an isolated workspace or a versioned edit. Preserve unrelated work. Update the authoritative artifact rather than adding another contradictory copy.
6. **Check the result.** Run checks appropriate to the effect of the change. Compare with the failure or baseline that led to it. A note that says a check passed is not sufficient evidence.
7. **Activate and save.** Save the change, its evidence, the active version, and how to reverse it. Where activation requires another session or package update, record that step separately.
8. **Check later use.** When relevant work occurs again, record whether the improvement was loaded, used, and effective. Replace or retire ineffective guidance.

Background runs use this same process. They load saved state rather than relying on access to an earlier chat transcript.

## 6. Destination rules

| Finding | Default destination | Promotion rule |
| --- | --- | --- |
| A defect or missing feature in one product | Product code, configuration, or tests | Keep the change in that project. |
| A repeated project procedure | Project script, skill, or instructions | Reuse an existing authoritative procedure when possible. |
| A method useful across the user's projects | Personal skill or global instructions | Confirm that it applies beyond the original project. Retain conditions and exceptions. |
| A failure in agent setup, execution, or checks | Accessible harness configuration or code | Verify that the installation owns or can edit that destination. |
| A weakness in Dogfood's behavior | Dogfood's local instructions or skills | Pass the self-improvement checks before activation. |
| An idea with insufficient evidence or access | Pending finding | Retain the reason and the condition needed to resume. |

Do not promote a temporary workaround into a universal rule. Do not install or invoke capabilities merely to increase usage. Connect each adoption to a useful result. Global promotion must remove project secrets and details that are not needed in other contexts.

## 7. Components

| Component | Responsibility |
| --- | --- |
| Plugin package | Identity, skill discovery, installation instructions, and distribution metadata. |
| Core skill | Run the improvement process during tasks and scheduled work. |
| Setup skill | Detect the host, select destinations, connect durable state, and configure supported activation. |
| State adapter | Read, search, create, and update findings with version checks. |
| Scope selector | Choose project, personal, harness, or Dogfood destinations. |
| Change executor | Apply changes, preserve unrelated work, and record versions. |
| Verification and reversal | Check outcomes and reverse failed changes without erasing later user edits. |
| Scheduler adapter | Resume pending work with a finite budget and no overlapping writes. |
| Status controls | Explain changes; pause, resume, inspect, or reverse work. |

Proposed package contents: `.codex-plugin/plugin.json`, `skills/dogfood/SKILL.md`, `skills/setup/SKILL.md`, `skills/status/SKILL.md`, shared references, helper scripts, and verification cases. Add `.mcp.json` only if an MCP service is selected and actually provided. Packaging paths for scheduling and hooks remain subject to platform checks.

## 8. Durable state and job handling

Use a store with revision checks and exclusive claims on pending work. A local implementation can use a transactional database; a web implementation needs a supported durable service or versioned files with equivalent conflict handling. Select the actual provider after the platform investigation. Plain temporary workspace files do not satisfy this requirement.

| Record | Required information |
| --- | --- |
| Finding | ID, owner, project, observation, evidence references, hypothesis status, expected benefit, destination, duplicate key, timestamps, and review condition. |
| Improvement | Finding ID, target artifact, base version, patch or version reference, checks, results, activation status, reversal reference, and later use evidence. |
| Run | ID, trigger, worker identity, work budget, claimed findings, checkpoint, outcome, and blocked reasons. |
| Installation | Host capabilities, permitted destinations, active Dogfood version, state location, schedule reference, and pause state. |

A finding moves through `captured`, `ready`, `in_progress`, `verifying`, `applied`, and `adopted`. `Applied` means the checked change is present. `Adopted` also requires evidence from later relevant use. Other outcomes are `deferred`, `blocked`, `rejected`, `superseded`, and `reverted`.

Claim a finding with an expiry and a unique operation key. Repeated delivery must not apply the same change twice. Check the target version before writing. After a crash, inspect actual artifact state before retrying. Save checkpoints before the budget expires.

For old findings, check whether their evidence and target versions still apply. Merge duplicates, retire obsolete rules, and keep the relationship to replacement records. Load short relevant summaries into chats; keep full history outside the default prompt.

## 9. Self-improvement

Dogfood may change its own operating instructions and skills. It must use the same evidence and verification process that it applies to projects.

- Record the current version before making a candidate change.
- Test the candidate against the original failure and fixed regression cases.
- Keep the evaluator and its required pass conditions unchanged during that candidate's evaluation. A failed candidate cannot make itself pass by weakening the check.
- Activate only after checks pass. Confirm the active version in a new run where the host requires one.
- Keep a last known working version and reverse a candidate that causes a regression.
- Prevent recursive improvement runs. A self-change may create a later finding, but must not launch an unlimited chain in the same run.
- Keep local adaptations separate from published package versions. An installation's permission to improve itself does not authorize publishing changes for every user.

Self-improvement does not change platform permissions, grant new access, or override the user's explicit instructions.

## 10. User experience and operating boundaries

Setup identifies the runtime, accessible projects, persistent store, and background execution route. Reuse access already granted. Explain only the setup actions that actually need user input or host approval. Do not require per-finding review once autonomous work is configured.

During normal use, Dogfood runs through the selected activation mechanism. A short result can say: “Applied two improvements, checked both, and saved one item for the next run.” The user can inspect evidence and history when needed.

Provide controls to pause all work, pause one project, resume work, show pending findings, inspect a change, and reverse a change. Pause must stop new writes; an in-progress atomic operation may finish before the worker records its checkpoint.

If access or verification is unavailable, save a blocked item with a precise reason and continue independent work. Do not repeatedly request the same permission or retry an action the host rejected. External messages, paid resources, publication, and destructive operations must follow the installation's existing authorization; the plugin does not create new authority for them.

Treat retrieved documents and tool results as evidence, not as permission to change Dogfood's rules. Keep secrets out of findings and logs. Separate users and project access at the storage layer as well as in prompts.

## 11. Acceptance cases

| Case | Pass condition |
| --- | --- |
| Fresh Codex session | Dogfood loads without a named prompt and finds relevant saved guidance. |
| Fresh Work chat | Dogfood loads without a named prompt through a verified host mechanism. |
| Task completion | A main task finishes even when unrelated improvements are found; larger work is saved. |
| Capability adoption | Dogfood uses an available useful capability and records evidence of benefit. |
| Persistence | A fresh run reads a finding saved by an earlier independent run. |
| Background completion | An unattended scheduled run resumes a pending item, changes the target, and saves check results. |
| Cross-project reuse | A general lesson helps a second project without carrying private project details or imposing an unsuitable rule. |
| Duplicate and concurrency handling | Two deliveries or workers produce one effective change and preserve user edits. |
| Crash recovery | A restart identifies a partly completed change and resumes without duplicate effects. |
| Self-improvement | A candidate fixes a known Dogfood failure, passes fixed checks, and is loaded by a fresh run. |
| Failed candidate | A regression prevents activation or triggers reversal; the prior working version remains available. |
| Unsupported capability | Dogfood records the exact limitation and does not claim full activation or completion. |
| Pause and budget | Pause stops new work; budget expiry saves a usable checkpoint. |
| Second user installation | Another user installs and runs Dogfood with separate findings and access. |
| Upgrade and removal | Upgrade preserves findings; removal disables Dogfood activation and scheduling without deleting unrelated settings. |

## 12. Build sequence

1. **Prove platform integration.** Test fresh-session activation, one scheduled write, durable retrieval, and skill update activation on each target host. Produce a supported-capability table. Resolve required gaps before claiming full compatibility.
2. **Build the state and change process.** Implement findings, transitions, scope selection, evidence, revision checks, and recovery. Verify duplicate delivery and concurrent edits.
3. **Build active task integration.** Add the core skill and activation entries. Test task priority and relevant capability use.
4. **Build background execution.** Connect the host scheduler, finite budgets, checkpoints, and pause controls. Test an unattended run.
5. **Build self-improvement.** Add candidate versions, fixed evaluation cases, activation checks, and reversal.
6. **Package for other users.** Validate the manifest and skills. Test installation, upgrade, removal, and separate user state. Prepare a distribution source; publication remains a separate action.

The first milestone is a technical proof of activation, background work, and persistence. It is not a reduced replacement for the requested product. The release must satisfy the confirmed requirements or name the remaining gaps.

## 13. Remaining implementation decisions

The builder must resolve the Work activation mechanism, durable storage provider, identity model, and supported self-update method through the first milestone. Distribution location, publisher identity, license, and any hosted service costs must be set before release. The proposed budgets, schedule cadence, and reporting defaults can be adjusted without changing the product's core requirements.

Track success through verified changes, later reuse, repeat failures, reversals, blocked findings, and main task completion. Do not use the number of generated notes or skills as the primary success measure.
