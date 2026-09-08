---
name: status
description: Inspect Dogfood findings and changes, pause or resume its work, or reverse an identified improvement.
---

# Dogfood controls

Resolve the configured store using [the ledger](../dogfood/references/ledger.md) or [Work adapter](../dogfood/references/work.md).

- Show checked changes, pending activation, later reuse, blockers, and run checkpoints with status, list, and get.
- Pause or resume with pause and a boolean paused value; optionally scope it to a project. Save remote state before confirming success. A full pause should also pause the known native scheduled task where supported. Resume only the requested scope.
- Before reversal, compare the target with the recorded changed version. Reverse only Dogfood's change. Preserve later user edits. If they overlap, record the conflict. Save actual reversal evidence before marking reverted.
- For removal, use host controls to disable the identified schedule and plugin. Remove only the marked Dogfood instruction block. Keep findings unless the user explicitly requests deletion.

Pause stops new writes. If an external atomic operation is already in flight, record its result and stop the next operation. Do not claim pause can cancel an accepted external request.
