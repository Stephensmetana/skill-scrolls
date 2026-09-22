---
name: mini-brainstorm
description: >
  Writes a short brainstorm document — a one-paragraph goal summary plus a bullet list
  of the important details — and then immediately appends a Q&A round via the qa-session
  skill. This is the lightweight sibling of feature-lifecycle-docs: use it when the user
  wants to get to clarifying questions fast without the full brainstorm → AI notes →
  Q&A → implementation-plan pipeline. Trigger whenever a message starts with (or is
  essentially) "mini-brainstorm ..." or "mini brainstorm ...", e.g. "mini-brainstorm a
  tag-merging feature". Also trigger on "quick brainstorm X", "short brainstorm X", or
  "brainstorm X but keep it short / skip the AI notes". If the user just says
  "brainstorm X" with no qualifier, that's feature-lifecycle-docs instead, not this skill.
---

# Mini-Brainstorm

A condensed brainstorm doc for when the goal is clarifying questions, not a full written
review. Where `feature-lifecycle-docs` produces four stages (brainstorm, AI notes, Q&A,
implementation plan), this skill produces exactly two things in one file:

1. A short **summary + bullet list** — no AI-notes critique section, no exhaustive analysis
2. A **Q&A round**, via the `qa-session` skill

That's the whole pipeline. If the user later wants the full treatment (AI notes,
implementation plan), point them at `feature-lifecycle-docs` rather than bolting those
stages on here by hand.

If a project has its own CLAUDE.md instructions about where brainstorm documents go
(folder layout, filename convention), those override the default below — check for a
project CLAUDE.md first, the same way `feature-lifecycle-docs` does.

---

## Step 1 — Write the summary + bullets

**File:** `dev_notes/brainstorming/YYYYMMDD_short_descriptive_name.md` (use today's actual
date, not a placeholder). If a project convention prefixes or locates this differently,
follow that instead.

Keep the file to two things:

- **Goal** — one or two sentences on what's being built or changed and why.
- **Details** — a bullet list of the important facts, constraints, and considerations:
  relevant file paths, existing precedent in the codebase, options the user has already
  named, anything that would change what gets asked in the Q&A. Skip anything that's
  restating the obvious or padding — if a bullet doesn't inform a decision, leave it out.

This is deliberately not templated further than that. Don't add an AI-notes-style
critique section, don't write exhaustive prose, and don't pad the bullet list to look
thorough — the doc exists to get to the Q&A quickly, not to stand alone as a full review.
Ground the bullets in the actual codebase where it matters (real paths, real function or
component names) rather than describing the idea in the abstract, but keep each bullet to
a line or two.

---

## Step 2 — Q&A

**STOP. Do not write any `## Q&A` heading, question, or option yourself.** The only
correct action here is a tool call to the Skill tool with `skill: qa-session`. If you
catch yourself typing `## Q&A`, a question number, or `1.`/`A.` option text by hand,
stop and invoke the skill instead — that is the exact mistake this gate exists to catch.

Immediately after writing the file, invoke the **qa-session** skill against the same
document to append the `## Q&A Round 1` section. That skill owns the entire format —
numbered options (`1.`, `2.`, `3.`, never letters), the "Other — describe your answer."
fallback, blank `**User answer:**` lines, and the round header. Do not hand-roll any
part of it, even to save a step.

Base the questions on the bullet list from Step 1: scope boundaries left open, any bullet
that names a constraint without resolving it, or a choice between two approaches the
bullets didn't settle. Don't ask about anything the bullets already answered.

Before moving on, confirm: did Step 2 actually happen as a Skill tool call (not text you
wrote directly)? If not, this step isn't done yet.

Once the user replies, fold the answers back into the document (update the bullets
directly, or add a short **Resolved** section) so the doc reflects the decisions rather
than leaving them buried in the raw Q&A transcript. If answers open a new question, a
Q&A Round 2 is fine — invoke qa-session again; it detects the round number itself.

---

## Why this exists alongside feature-lifecycle-docs

`feature-lifecycle-docs` is the right tool when the user wants a real review — critique,
integration points, edge cases — before questions get asked. This skill skips straight
from "here's the idea" to "here's what I need to know," for cases where the user already
has a clear picture and just wants the ambiguities surfaced. If mid-session the scope
turns out bigger than expected, it's fine to suggest expanding into the full
`feature-lifecycle-docs` pipeline rather than forcing the mini version to cover it.
