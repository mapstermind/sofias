# wip/

Disposable scaffolding for work in progress. Everything in this folder is a
working artifact for one branch — a change brief, an implementation plan — and
is **deleted when that branch merges**.

Nothing here is a source of truth. The live feature docs are the files in
`docs/platform/`; a reader looking for how the platform behaves should never end
up in this folder.

Two files per feature, both named after it:

| File | What it holds |
|---|---|
| `<feature>-change.md` | The change brief: what changes, why, and which parts of the live feature doc it makes wrong |
| `<feature>-tasks.md` | The ordered implementation plan, as a checkbox list |

`main` should always show this folder holding nothing but this README. If it
holds anything else, a branch was merged without its cleanup step — see
[`docs/internal/prompting-workflow.md`](../../internal/prompting-workflow.md)
Step 10.
