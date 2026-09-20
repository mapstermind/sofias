# wip/

Disposable scaffolding for work in progress. Everything in this folder is a
working artifact for one branch and is **deleted when that branch merges**.

Nothing here is a source of truth. The live feature docs are the files in
`docs/platform/`; a reader looking for how the platform behaves should never end
up in this folder.

One file per feature, named after it: `<feature>-tasks.md`.

| Section | What it holds |
|---|---|
| `## What changes` | The change brief: what changes, why, and which sections of the live feature doc it makes wrong. Written before the plan; absent when the feature doc itself is new. |
| The task list below it | The ordered implementation plan, as a checkbox list, ending in the documentation task |

`main` should always show this folder holding nothing but this README. If it
holds anything else, a branch was merged without its landing step — see
[`docs/internal/prompting-workflow.md`](../../internal/prompting-workflow.md)
Step 7.
