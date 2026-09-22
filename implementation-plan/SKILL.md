---
name: implementation-plan
description: >
  Generate a structured implementation_plan.md in dev_notes/ that breaks work into
  phases with parallel-safe task annotations. Use this skill whenever the user wants
  to plan out changes to a codebase, feature, or system — especially after a code
  review, architecture discussion, or "what needs to change?" conversation. Trigger on
  phrases like "make an implementation plan", "create a plan for this", "list the tasks",
  "what do we need to do", "plan out the changes", "break this into tasks", "which tasks
  can be done in parallel", or any time the user asks Claude to assess something and
  produce a plan. Also trigger when the user says "is it good, does it need changes" and
  wants tasks written out. Always use this skill when the output is an implementation
  plan file — do not improvise the format.
---

# Implementation Plan Skill

Produces a `dev_notes/implementation_plan.md` that an engineer (or another AI session)
can open and execute phase-by-phase, task-by-task, without needing extra context.

---

## When to use this skill

- After reviewing code, architecture, or a spec and identifying improvements
- When the user asks "what needs to change?" and wants a file they can hand back to AI
- When planning a new feature, refactor, or migration
- Any time tasks need to be sequenced and parallelism called out explicitly

---

## Output file

Always write to: `dev_notes/implementation_plan.md`  
Create `dev_notes/` if it doesn't exist.

---

## Document structure

```markdown
# Implementation Plan: <short title>

> **Status:** Draft | In Progress | Complete  
> **Created:** <date>  
> **Context:** 1–3 sentence summary of what this plan addresses and why.

---

## Phase N — <Phase Name>

> <One sentence describing the goal of this phase and what it unblocks.>
> **Execution:** Group A ∥ Group B → Group C (groups with ∥ run in parallel; → means "then")

---

### 🟦 Group A — <Group Name>
> Copy this entire group and tell AI: "Execute Group A from the implementation plan."

**Step 1 — <Task Name>**  
**What:** One sentence describing what this task does.  
**Why:** One sentence on why it's needed.  
**Files/areas affected:** list them  
**Done when:** Concrete, checkable completion criterion.

**Step 2 — <Task Name>**  
**What:** ...  
**Why:** ...  
**Files/areas affected:** ...  
**Done when:** ...

---

### 🟩 Group B — <Group Name>
> Copy this entire group and tell AI: "Execute Group B from the implementation plan." (runs in parallel with Group A)

**Step 1 — <Task Name>**  
...

---

### 🟨 Group C — <Group Name>  *(waits for Group A and Group B)*
> Copy this entire group and tell AI: "Execute Group C from the implementation plan."

**Step 1 — <Task Name>**  
...

---
```

**Group color convention** (helps scan at a glance):
- 🟦 Blue — first parallel wave
- 🟩 Green — second parallel wave (runs alongside blue)
- 🟨 Yellow — sequential gate (waits for blue + green)
- 🟧 Orange — next parallel wave after the gate
- 🟥 Red — final/cleanup phase

Repeat phases and groups as needed. End with a summary table, then the Q&A section.

---

## Phase design rules

1. **Phases are sequential** — each phase may depend on the previous one being complete.
2. **Groups within a phase may be parallel** — groups that touch different areas run simultaneously; groups that depend on each other run in sequence.
3. **Tasks within a group are always sequential** — each step runs after the previous one inside that group.
4. **Keep groups small** — 2–5 steps per group is ideal. If a group would have 6+ steps, split it into a sub-group or a new sequential gate.
5. **Name phases by outcome**, not process: "Auth System Working" not "Do Auth Stuff".
6. **Foundation before features** — infrastructure, config, and schema changes always come first.
7. **Testing and cleanup last** — unless tests are needed to verify an earlier phase.

Typical phase order for most projects:
- Phase 1: Setup / Infrastructure / Config
- Phase 2: Core data model or schema changes
- Phase 3: Core logic / backend
- Phase 4: UI / integration / API surface
- Phase 5: Tests, polish, cleanup

---

## Group and parallelism rules

A **group** is a self-contained chunk of sequential work that one AI session (or one engineer) can execute start-to-finish by copying it and handing it to an agent.

Two groups run **in parallel** (∥) when:
- They touch different files or subsystems
- Neither depends on the other's output
- Both can be merged independently without conflict

A group is a **sequential gate** (→) when:
- It consumes output from a prior group (a file, schema, or interface that must exist first)
- It modifies files that parallel groups also touched (must wait for merges)
- Its correctness depends on the prior group being complete

**Execution notation** at the top of each phase:
- `Group A ∥ Group B` — run simultaneously
- `Group A ∥ Group B → Group C` — A and B run simultaneously, then C starts
- `Group A → Group B ∥ Group C → Group D` — A first, then B and C simultaneously, then D

Each group header must include a one-line copy prompt so the user knows exactly what to paste to an AI agent.

---

## Summary table (always include at the end)

```markdown
## Summary

| Phase | Execution order | Groups | Steps total |
|-------|----------------|--------|-------------|
| 1 — Setup | Group A ∥ Group B → Group C | 3 | 7 |
| 2 — Core Logic | Group D ∥ Group E → Group F | 3 | 9 |
| 3 — UI | Group G ∥ Group H | 2 | 5 |
| 4 — Tests | Group I | 1 | 3 |

**To run a group:** Copy the entire group block and tell AI: "Execute [Group Name] from the implementation plan."  
**To run a phase:** Tell AI "Execute Phase N of the implementation plan in dev_notes/implementation_plan.md"  
**Parallel groups:** Start both AI sessions at the same time, each with their own group block.  
**Sequential gates:** Wait for all parallel groups to finish before starting the next group.
```

Always include this usage tip at the bottom — it reminds the user how to hand plan groups to AI.

---

## Assumptions & Risks section (always include before Q&A)

After the summary table and before the Q&A section, append an Assumptions & Risks section. List things you assumed while writing the plan (tech choices, scope boundaries, existing state) and risks that could derail a phase — especially tasks that are depended on by many others.

```markdown
## Assumptions & Risks

- [Assumption made during planning — e.g. "assumes auth middleware already exists"]
- [Risk or uncertainty — e.g. "schema migration may require downtime; confirm with ops"]
- [Critical-path note — e.g. "Task 2.1 blocks all of Phase 3; prioritize it"]
```

Keep it to 3–6 bullets. If you have no genuine risks or assumptions, omit the section rather than padding it with boilerplate.

---

## Quality checklist before writing the file

- [ ] Every step has a concrete "Done when" criterion (not vague like "is complete")
- [ ] No group has more than 5 steps (split if needed)
- [ ] Every phase has an execution notation line (e.g. `Group A ∥ Group B → Group C`)
- [ ] Every group header has a one-line copy prompt for handing to AI
- [ ] Groups that are truly independent are marked as parallel (∥)
- [ ] Groups that depend on prior output are marked as sequential gates (→)
- [ ] Phase names describe outcomes, not actions
- [ ] The summary table is present with execution order column
- [ ] Context section explains *why* this work is happening
- [ ] Foundation/infrastructure comes before feature work
- [ ] No time estimates anywhere in the plan
- [ ] Assumptions & Risks section is present (or omitted if genuinely none)
- [ ] Q&A section is present with 3–6 plan-specific questions
- [ ] Every question ends with an "Other" option and a blank `**User answer:**`

---

## Tone and length

- Groups should be self-contained enough for an AI session that hasn't read this conversation to execute them cold
- Be specific about file paths and component names when known
- Don't pad — if a plan is genuinely 2 phases and 5 tasks, don't invent more
- **No time estimates** — never include hours, days, or complexity ratings anywhere in the plan
- Use `**Done when:**` as a forcing function for clarity — if you can't write a crisp criterion, the task is under-defined and should be split or clarified

---

## Q&A section (always include at the end of the generated file)

After the summary table, append a Q&A section to the generated `implementation_plan.md`. This section surfaces open decisions and ambiguities the user should resolve before or during execution.

Generate 3–6 questions that are **specific to this plan** — not generic boilerplate. Good questions surface real unknowns: technology choices, scope boundaries, dependency risks, rollback strategies, ownership, or anything where the wrong assumption would derail a phase.

Use this exact format for every question:

```markdown
---

## Q&A

> Answer these before handing the plan to AI for execution. Reply with the question number and your choice (e.g. "2. Yes" or "3. Use Postgres").

---

**Question 1:**
<Question text>
   1. <Option A>
   2. <Option B>
   3. Other — describe your answer.
**User answer:**

---

**Question 2:**
<Question text>
   1. <Option A>
   2. <Option B>
   3. <Option C>
   4. Other — describe your answer.
**User answer:**
```

### Q&A question guidelines

- **Yes/No decisions** → 2 options + "Other"
- **Multiple valid choices** → list each concrete option, always end with "Other — describe your answer."
- **Don't pad** — if there are only 3 real unknowns, write 3 questions. Don't manufacture extras.
- Questions should be answerable with a number. The user can say "1", "2", or "3. We'll use Redis."
- Always leave `**User answer:**` blank — it's for the user to fill in.
- Phrase each question so that answering it would change *what gets built or how* — not just clarifying trivia.
