---
name: business-logic-docs
description: >
  Set up or maintain a docs/business_logic/ folder that documents non-obvious
  behavior (matching rules, processing order, deliberate rejection of a simpler
  approach, seeded/deterministic behavior, storage/lifecycle decisions, scope
  boundaries) so it survives the loss of conversation context. Use this whenever
  the user wants to document business logic, add or update a doc describing why
  some code behaves a non-obvious way, or set up this documentation convention in
  a new project. Also trigger proactively — without being asked — in any
  project that already has a docs/business_logic/ folder, whenever: significant or
  non-obvious logic is added or changed (write/update the doc in the same change);
  answering a question required real investigation across multiple files or a call
  chain (write the answer down, not just the chat reply); or the user asks whether
  documentation exists for some behavior and it doesn't (create it). Always use
  this skill for that documentation instead of freehand writing a business-logic
  doc — the format (title, **Code:** line, ## sections, examples-over-prose) is
  specific and this skill is the source of truth for it.
---

# Business Logic Docs

Implements the portable "Business Logic Documentation Standard": a convention for
capturing *why a rule is the rule it is*, not just what the code does — the kind of
knowledge that normally lives only in a conversation and gets expensively
re-derived months later.

The full spec — problem statement, folder layout, what belongs/doesn't, required
doc structure, style rules, triggers, maintenance, bootstrapping steps — lives in
[references/standard.md](references/standard.md). Read it before writing or editing
any doc under this convention; don't rely on this summary alone for formatting details.

## Which mode applies

Check whether the target project already has `docs/business_logic/STANDARD.md`.

- **Exists** → **Maintain mode**. That file is authoritative for *this* project —
  it may have been adapted from the generic standard, so its wording wins over
  `references/standard.md` where they differ. Follow it, keep `README.md`'s index
  updated, and apply the §6 triggers (significant logic added/changed, a question
  that took real investigation, someone asking if docs exist for something).
- **Doesn't exist** → **Bootstrap mode**. Follow §8 of `references/standard.md`:
  create the folder, an adapted `STANDARD.md`, an indexed `README.md`, wire the §6
  triggers into the project's contributor instructions file, then seed 2–3
  full-quality docs from the highest-value existing candidates (non-obvious
  comments, ordering dependencies, seed/hash logic, rejected-simpler-approach
  notes, explanatory bug-fix commits) before waiting for new features to justify more.

## Working on a single doc

1. **Verify against real code first** — never write from memory or from the
   conversation alone, even if the conversation already explained the behavior.
   Re-read the implementation and confirm the rule still holds.
2. **Follow the required structure** exactly (§4 of the standard): title as a
   feature name (not a task description), a `**Code:**` line naming files and
   function/component names (no line numbers — they drift), then `##` sections.
   Use examples/tables over prose wherever the rule has a "does this match or not"
   quality.
3. **Decide new file vs. new section** — one file per cohesive feature; only merge
   two behaviors into one file if neither makes sense without the other.
4. **Update `README.md`** with a one-line index hook in the same change — what a
   reader needs to decide whether to open the file, not a title restatement.
5. **If this doc replaces/updates an existing one**, edit it in place rather than
   leaving the old version to go stale — a stale doc is worse than none, since
   readers trust it by default.

## Judgment call: does this even qualify?

Not everything is worth documenting here. Apply the test from §3: would a
competent engineer reading only the code reach the wrong conclusion, or spend more
than a few minutes reconstructing this? If the answer is no — it's self-evident
from well-named code, or it's a styling/layout choice with no behavioral
consequence — skip it and say why, rather than padding the folder. A folder full of
docs that just restate the code trains people to stop opening it.
