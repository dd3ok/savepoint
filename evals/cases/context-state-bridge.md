# Context State Bridge

## Scenario

A repository contains:

- `AGENTS.md` with build/test rules.
- `PROJECT_STATE.md` with current project goal.
- `TASKS.md` with remaining tasks.
- Dirty working tree with two changed files.
- User says: "PROJECT_STATE.md랑 TASKS.md 참고해서 다음 세션에서 이어갈 HANDOFF.md 만들어줘."

## Expected

- Skill triggers.
- Create mode writes `.new-session-handoff/HANDOFF.md`.
- Handoff records current disk/Git state before summarizing.
- Handoff lists `AGENTS.md`, `PROJECT_STATE.md`, and `TASKS.md` as relevant durable state files with purpose.
- Handoff does not paste entire state files.
- Handoff includes one narrow next action.
- If the user provides a next-session focus, the handoff records it under `Next-session focus`.
- The focus narrows `Remaining Work` to one executable next step.
- The focus does not override disk/Git state, durable state files, validation, or blockers.
- `SAFE_FOR_NEW_SESSION: yes` only if validation status, secret check, changed files, and blockers are honestly recorded.

## Failure Conditions

- Copies full `PROJECT_STATE.md` or `TASKS.md` into `HANDOFF.md`.
- Treats state files as higher priority than current disk/Git state.
- Omits dirty files.
- Sets `SAFE_FOR_NEW_SESSION: yes` with vague next action.
- Omits the provided next-session focus.
- Expands suggested skills into a long generic checklist.
- Lets suggested skills override the smallest executable next step.
