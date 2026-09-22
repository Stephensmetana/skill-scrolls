# The Business Logic Documentation Standard

A portable convention for documenting non-obvious behavior in a codebase, in a way that survives the loss of all conversation context — for a new engineer, or for an AI session that has no memory of why the code was written this way.

---

## 1. The problem it solves

Code says *what* happens. Git history says *when* it changed. Neither reliably says **why the rule is this rule and not the obvious one** — and that "why" is exactly what gets re-derived, expensively, months later.

The failure mode is concrete: someone (human or AI) reads a function that resolves A before B, sees no reason for the order, "cleans it up" by reordering, and silently breaks a case nobody has a test for. Or they reimplement a matching rule as a substring match because the exact-segment match looked needlessly fussy.

The standard exists to make that class of knowledge a durable, greppable artifact instead of tribal memory.

## 2. Folder layout

```
docs/
  business_logic/
    README.md      ← index: one line per doc
    STANDARD.md    ← the format spec (project-local copy, may be adapted)
    <feature>.md   ← one file per cohesive feature or mechanism
```

- **One file per cohesive feature or mechanism**, named descriptively in `snake_case.md` (`blacklist.md`, not `feature_3.md`).
- If two behaviors are tightly coupled and neither makes sense alone — e.g. two functions that must run in a specific order relative to each other — document them **together in one file** rather than splitting them and cross-referencing constantly.
- `README.md` is the index. Every new doc gets a one-line pointer added to it in the same change. The line is a *hook* — what a reader would need to know to decide whether to open the file — not a title restatement:

  ```markdown
  - [unique_names.md](unique_names.md) — per-table (not cross-table) unique names via `ensure_unique_name`:
    case-insensitive matching, highest-suffix+1 numbering with no gap-fill, enforcement on
    create/rename/clone/import (app-level, no DB UNIQUE constraint)
  ```

- `STANDARD.md` inside the folder is what contributors are told to read before adding a doc. Keeping it *in* the folder means it's found by anyone who opens the folder at all.

## 3. What belongs here — and what doesn't

Document **non-obvious behavior**: decisions, rules, and edge cases that aren't self-evident from reading the code, or that would take real effort to reconstruct.

Good candidates:

- A **matching or comparison rule** that isn't the obvious implementation — exact-segment match instead of substring match, case-insensitive instead of exact — and *why*.
- A **processing order** between two pieces of logic where getting it backwards silently breaks things.
- A **deliberate rejection of a simpler-looking approach**, plus what would go wrong with that simpler approach.
- **Deterministic / seeded behavior** — how the seed is derived, what guarantees it provides, and what it explicitly does *not* guarantee.
- **Storage and lifecycle decisions** — what's persisted vs. computed on the fly, and why re-running produces identical or different results.
- **Scope boundaries** — which layer owns a piece of logic, and where it must *not* be added (e.g. "resolution happens only at dispatch time; the frontend passes these through as opaque strings").

Do **not** document here:

- Anything a reader gets for free from well-named code. Don't restate what a function obviously does.
- UI copy, styling choices, or file layout with no behavioral consequence — *unless* the choice is a deliberate exception worth flagging (e.g. "this modal intentionally does not follow the app's design system, because …").
- Anything that drifts out of sync quickly and isn't load-bearing. Prefer documenting the **rule**, not a snapshot of current line numbers or current config values.

The test to apply when unsure: *would a competent engineer reading only the code arrive at the wrong conclusion, or spend more than a few minutes reconstructing this?* If no, skip it — a folder padded with docs that restate self-evident code trains readers to stop opening it.

## 4. Required structure

```markdown
# <Feature Name>

**Code:** <file path> (`function/component names`), <second file path if relevant>

## <Behavior section 1 — usually the core rule>

<Plain-language statement of the rule, followed by a short "why" if the rule
isn't the obvious default.>

<Concrete before/after example(s) where the rule is non-trivial — inputs and
outputs, not abstract description. If a naive or previous implementation got
this wrong, say so and show the failing case.>

## <Behavior section 2, 3, ... as needed>
```

- **Title** — the feature or mechanism name, not a task description. `Blacklist: Exact-Match Removal + Tag Picker Modal`, not `Blacklist Fix`.
- **`**Code:**` line** — always the second line of the file, immediately after the title. Point at file paths plus the specific function/component names involved; this is what lets a reader jump straight to the implementation. **Do not include line numbers** — they drift within weeks. Function and component names are stable enough to grep for.
- **Sections** — use `##` headers for distinct rules or sub-behaviors. A short feature may need only one section; that's fine. Don't pad to fill a template.

## 5. Style rules

- **Write for a reader with zero conversation context** — someone opening the file cold, months later, with no memory of the discussion that produced the feature. This is the single rule that most changes how the doc reads.
- **Examples over prose.** Whenever a rule has a "does this match or not" quality — matching logic, boundary conditions, ordering — show at least one concrete input → output example. With 2+ examples, prefer a small table or a fenced block over a paragraph:

  | Existing rows | Save `foo` → result |
  |---|---|
  | *(none)* | `foo` |
  | `foo` | `foo_001` |
  | `foo`, `foo_005` | `foo_006` — gap at 001–004 is **not** filled |

- **State the "why" when the rule is surprising.** If the behavior isn't the first thing a reasonable engineer would guess, explain the reasoning or the failure mode it avoids. If the rule *is* the obvious default, just state it — no justification needed.
- **Tables for side-by-side comparisons** instead of long paragraphs enumerating differences between two things.
- **Cross-reference related docs** with a relative markdown link rather than re-explaining shared context.
- **No changelog framing.** No time estimates, no ticket references, no "recently added" or "new in v2". These describe *current behavior*; history belongs in commits and `CHANGELOG.md`. A doc written as a changelog becomes misleading the moment the next change lands.
- **No unexplained jargon.** Spell out internal shorthand the first time it appears in each file.
- **"This was deliberately chosen over X because Y" is welcome** — that rationale is what the folder exists for, and is usually the single most valuable sentence in the doc.

## 6. When to write or update one

Wire these triggers into the project's contributor instructions (`CLAUDE.md`, `CONTRIBUTING.md`, or equivalent) so they fire without being asked:

- **Significant logic added** → create or update a doc describing it.
- **Existing logic changed** → update the corresponding doc **in the same change**. Never leave it describing old behavior.
- **A question required real investigation to answer** — reading through several files, tracing a call chain, reconstructing a rule not obvious from any single function → write the answer into the folder as well as replying. The effort spent reconstructing the behavior is precisely what the folder exists to prevent repeating. Skip this for one-line lookups, "where does X live", or anything an existing doc already covers (link to it instead).
- **Someone asks whether documentation exists for something and it doesn't** → treat that as a request to create it. Say what's missing, then write it. If the subject genuinely doesn't qualify under §3, say so and explain why rather than padding the folder.

Not every change qualifies. Trivial UI tweaks, styling, and behavior-preserving refactors don't. Judge by §3.

## 7. Maintenance

**A stale business-logic doc is worse than no doc**, because it actively misleads the next reader — who has no way to know it's stale and every reason to trust it.

- Update the doc in the same commit as the behavior change, not as a follow-up.
- Verify against the actual code before writing, not from memory or from the conversation alone. This applies especially to AI sessions: re-read the implementation and confirm the rule still holds.
- When a documented feature is deleted, delete its doc and its `README.md` line.

## 8. Bootstrapping this in a new project

In order:

1. Create `docs/business_logic/` with a `STANDARD.md` containing §3–§7 above, adapted to that project's language and file layout.
2. Create `README.md` with the one-line-per-doc index format from §2, and a lead paragraph stating that STANDARD.md is required reading before adding a doc.
3. Add the §6 triggers to the project's contributor instructions file (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, or equivalent) so the convention self-sustains instead of depending on someone remembering it.
4. Seed the folder from what already exists — don't wait for new features. Look for the highest-value candidates first: comments that start with "note:", "careful:", or "do not"; functions with a non-obvious ordering dependency; anything with a hash/seed/modulo formula; anywhere a comment explains why the simpler approach was rejected; and bug-fix commits whose message explains a subtlety the code itself doesn't. Each of those is a doc waiting to be written.
5. Write the first two or three docs to full standard rather than many thin ones. The examples in the folder become the de facto template that everything afterward is written against, so the initial quality bar propagates.
