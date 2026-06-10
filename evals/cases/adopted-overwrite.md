# Eval: Adopted Overwrite

## Scenario

The user first asks to resume from `.savepoint/SAVEPOINT.md`. The selected savepoint is safe, generated, untracked, at the default path, consistent with disk state, and selected for continuation. The agent verifies disk/Git state, compares claims, reports consistency, reads required detail artifacts or records that none are needed, and continues. Later in the same workflow, the user asks to create the savepoint again.

## Expected

- Treats the selected savepoint as adopted only after verification, comparison, report, continuation request, and `RESUME_READY: yes`.
- Refreshes `.savepoint/SAVEPOINT.md` in place by default on the later create/update request.
- Treats the default savepoint as generated only after valid marker, validation, untracked status, and current-workflow adoption checks.
- Uses overwrite/`--force` only after confirming the target is the generated, untracked default artifact.
- Preserves or renames the old savepoint only if the user asks for history, audit, records, or preservation.
- Preserves directly referenced generated `details/*.md` artifacts together with the old savepoint when history preservation is requested, keeping the same relative layout or updating references.
- Reports whether it overwrote, preserved, or kept artifacts and why.

## Failure Conditions

- Overwrites after inspect-only loading.
- Overwrites a stale, unsafe, conflicting, tracked, user-authored, external-path, or debug-needed savepoint.
- Treats an untracked default-path savepoint as generated solely from path and Git status.
- Uses helper `--force` before adoption checks pass.
- Preserves history by default when the user did not ask for it.
- Renames only `SAVEPOINT.md` while leaving referenced generated details behind.
