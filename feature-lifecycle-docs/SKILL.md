---
name: feature-lifecycle-docs
description: >
  Runs the full brainstorm → AI notes → Q&A → implementation-plan lifecycle used for
  planning new features or changes in a project. Use this whenever the user wants to
  brainstorm a feature, review an idea before building it, "think through" a change,
  or asks for a written plan that should go through a clarification pass before any
  code gets written. Also trigger when the user says things like "let's brainstorm X",
  "write up a review of this idea", "make a plan for X but ask me questions first",
  "what needs answering before we build this", or references doing a "feature review".
  This is the orchestrating skill for that whole pipeline — it calls the qa-session
  skill for the Q&A step and the implementation-plan skill for the final plan, so
  invoke this one first rather than jumping straight to either of those when the task
  is "plan out a new feature/change" rather than "ask questions about this doc I
  already have" or "just write the plan, no review needed."
---

# Feature Lifecycle Docs

Codifies a four-stage pipeline for taking a feature idea from rough thought to an
executable implementation plan, with a mandatory clarification step in between so the
plan isn't built on unstated assumptions. This is the standard workflow already used
across this project's `dev_notes/` — the skill exists to make it repeatable instead of
reconstructed by feel each time.

The four stages, always in this order:

1. **Brainstorm** — the idea itself, written up
2. **AI notes** — a structured critique appended to the same document
3. **Q&A** — clarifying questions appended and answered inline (may repeat for multiple rounds)
4. **Implementation plan** — a separate document, written only once the Q&A has settled

Stages 1–3 live in **one file** in `dev_notes/brainstorming/`. Stage 4 is a **second
file** in `dev_notes/implementation_plan/`, cross-referenced back to the brainstorm.
Never merge the plan into the brainstorming file, and never skip straight to a plan
without the AI-notes + Q&A pass — the whole point of this pipeline is that the plan
gets written after ambiguity has been resolved, not before.

If a project has its own CLAUDE.md instructions about where brainstorms or plans go
(folder layout, filename convention), those override the defaults below — check for a
project CLAUDE.md first.

---

## Stage 1 — Write the brainstorm

**File:** `dev_notes/brainstorming/YYYYMMDD_short_descriptive_name.md` (use today's actual
date, not a placeholder). If a project convention prefixes differently, follow that instead.

Write up the idea in whatever structure fits the content — this part is not rigidly
templated, because brainstorms range from "diff two workflows node-by-node" to "sketch
a UI feature." What consistently belongs here:

- **Goal** — one or two sentences on what's being built/changed and why
- The substance of the idea: design, comparisons, options considered, files likely
  touched, anything the user has already told you (paths, examples, constraints)
- Reference any source material the user pointed you at (example files, existing
  similar features, prior art in the codebase) by path, so the doc is self-contained
  for someone opening it cold

Keep it concrete — cite real file paths, real function names, real precedent in the
codebase (e.g. "follows the same pattern as X") rather than abstract descriptions. A
brainstorm that just restates the user's request in nicer prose isn't useful; go read
the relevant code first so the brainstorm reflects how the idea actually fits the
existing system.

---

## Stage 2 — Append AI notes

Immediately after writing the brainstorm (same file, appended below a `---`), add a
`## AI notes` section. This is your own critical read of the idea — not a restatement,
a review. Cover:

- **Overall assessment** — does this fit as scoped? Is it bigger or smaller than it looks?
- **Architecture fit** — does it slot into existing patterns, or does something not quite fit?
  Name the specific abstraction that does or doesn't accommodate it.
- **Integration points** — what existing systems does this touch, and what's the
  recommended way to wire it in? Flag the places where "obvious" isn't actually obvious.
- **Edge cases / nuances** — things the brainstorm didn't consider that will matter
  once this is built.
- **What's missing or underspecified** — gaps in the brainstorm itself: undecided
  defaults, unstated scope boundaries, assumptions made without evidence.

Write this the way you'd actually flag concerns to a colleague — specific, grounded in
the code, willing to disagree with the brainstorm's framing where warranted. A note
that just says "looks good" everywhere isn't doing its job; if something is genuinely
fine, say why briefly rather than skipping it.

---

## Stage 3 — Q&A

**STOP. Do not write any `## Q&A` heading, question, or option yourself.** The only
correct action here is a tool call to the Skill tool with `skill: qa-session`. If you
catch yourself typing `## Q&A`, a question number, or `1.`/`A.` option text by hand,
stop and invoke the skill instead — that is the exact mistake this gate exists to catch.

Right after the AI notes, invoke the **qa-session** skill against the same document to
append the `## Q&A Round 1` section. That skill owns the entire format — numbered
options (`1.`, `2.`, `3.`, never letters), the "Other — describe your answer." fallback,
blank `**User answer:**` lines, and the round header. Do not hand-roll any part of it,
even to save a step.

Before moving to the next paragraph, confirm: did this happen as a Skill tool call (not
text you wrote directly)? If not, this stage isn't done yet.

Generate questions from what Stage 2 actually surfaced: the gaps flagged in "what's
missing," the integration points with more than one reasonable approach, and any
scope boundaries the brainstorm left implicit. Don't ask questions the brainstorm
already answered.

Once the user replies with answers:

- Fold the answers back into the document as a **Resolved** section (or update
  existing content directly) so a reader doesn't have to reconstruct decisions by
  reading through the raw Q&A transcript.
- If an answer opens a new question, or the user provides new material (another
  reference file, a correction, more requirements), it's fine to run a **Q&A Round 2**
  the same way — invoke qa-session again; it detects the next round number itself.
- If the user drops in loose additional notes that don't fit as Q&A, capture them
  under a `## More notes` section rather than losing them.

Do not move to Stage 4 until the open questions are answered and the resolved
decisions are written back into the document. A plan built on an unanswered Q&A round
just re-introduces the ambiguity the round existed to remove.

---

## Stage 4 — Implementation plan

Once Stage 3 has settled, invoke the **implementation-plan** skill to produce the plan.
It writes its own file (`dev_notes/implementation_plan/YYYYMMDD_name.md` by default, or
wherever the project's CLAUDE.md redirects it — check that first, since some projects
override the implementation-plan skill's default output location).

Two things this orchestration adds on top of that skill's own output:

- **Match the filename stem** to the brainstorm file where practical (same
  `YYYYMMDD_short_descriptive_name`, just in the `implementation_plan/` folder instead
  of `brainstorming/`) — this makes the pairing obvious from the file listing alone,
  e.g. `20260719_export_pipeline.md` existing in both folders.
- **Cross-reference the brainstorm** in the plan's context/header — link back to the
  brainstorming file path (and the specific reference material it cites) so the plan
  is traceable to the decisions that produced it, not just the feature name.

---

## Why this order, not some other order

The AI-notes-before-Q&A ordering matters: notes are what generate good questions.
Asking the user "any thoughts?" cold produces vague answers; asking specific,
critique-driven questions ("should X be a separate list or share Y's list, given Z
concern") produces decisions. And Q&A-before-plan matters because implementation plans
commit to specific files, functions, and steps — writing one before ambiguity is
resolved means either the plan bakes in a guess that turns out wrong, or it gets
littered with TODO/TBD markers that defeat the point of a plan meant to be handed to
an executor (human or AI) without further back-and-forth.

If the user explicitly wants to skip a stage — e.g. "just write the plan, I already
know what I want, don't bother with Q&A" — that's their call to make; follow the
shorter path rather than insisting on the full pipeline. This skill defines the
default, not a mandatory gate.
