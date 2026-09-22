---
name: qa-session
description: >
  Append a Q&A round to the open document (or any document in context) when the user
  invites questions or wants to clarify understanding. Trigger on phrases like "does this
  make sense?", "do you have any questions?", "Q&A", "Q and A", "qa session",
  "document qa", "any questions?", "what questions do you have?", "ask me anything",
  "clarify anything?", or any phrasing where the user is opening the floor for Claude
  to ask questions about a document or topic. Always use this skill — do not improvise
  the Q&A format.
---

# Q&A Session Skill

Appends a structured Q&A block to the current document so that questions and answers
are captured in-file across multiple rounds, creating a permanent record of clarifications.

---

## Trigger phrases (non-exhaustive)

- "does this make sense?"
- "do you have any questions?"
- "Q&A" / "Q and A" / "qa session" / "document qa" / "qa review" 
- "any questions?"
- "what questions do you have?"
- "ask me anything"
- "clarify anything?"
- "what's unclear?"

---

## Step 1 — Find the target document

Check the conversation for an open or referenced document:
- A file path mentioned by the user (e.g. `dev_notes/implementation_plan.md`)
- A file uploaded or pasted into the conversation
- The most recently discussed document if multiple exist

If no document is identifiable, ask the user: "Which document should I append the Q&A to?"

---

## Step 2 — Determine the round number

Read the target document and count existing `## Q&A Round` sections.

- If **none exist** → this is **Round 1**
- If **one exists** → this is **Round 2**
- And so on

---

## Step 3 — Generate questions

Read the full document carefully. Generate **3–6 questions** that are:

- **Specific to this document** — not generic boilerplate
- **Decision-relevant** — answering them would change what gets built, written, or decided
- **Genuinely unclear** — things that are ambiguous, underspecified, or assumed without evidence
- **Not already answered** in an earlier Q&A round in the same document

Good question types:
- Scope boundaries ("Does X include Y or just Z?")
- Technology / approach choices ("Is Redis acceptable here or must it be Postgres?")
- Priority / sequencing ("Should A ship before B, or can they go together?")
- Ownership ("Who is responsible for the migration script?")
- Edge cases ("What happens if the user has no prior data?")

---

## Step 4 — Append to the document

Use `str_replace` (or equivalent file-edit tool) to append the Q&A block to the **end** of the document. Never insert it in the middle of existing content.

Use this exact format:

```markdown
---

## Q&A Round N

> Reply with the question number and your answer (e.g. "1. Yes" or "3. Use Postgres").  
> You can answer multiple questions in one message.

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

### Format rules

- **Options are always numbered `1.`, `2.`, `3.` — never lettered (`A.`, `B.`, `C.`).**
  This is non-negotiable regardless of what format a similar-looking document elsewhere
  in the project uses; older files may predate this skill and are not a template to copy.
- **Yes/No decisions** → 2 options + "Other — describe your answer."
- **Multiple concrete choices** → list each option, always end with "Other — describe your answer."
- **Open-ended questions** (no good fixed options) → just 1 option: `1. Other — describe your answer.`
- Always leave `**User answer:**` blank — it is for the user to fill in
- Put `---` between every question for visual separation
- The round header must be exactly `## Q&A Round N` (with that number) — not `## Q&A`,
  not `## Q&A round N` (lowercase), not any other variant

---

## Step 5 — Confirm to the user

After writing the file, tell the user:

> "I've appended **Q&A Round N** to `<filename>` with X questions. Reply with the number(s) to answer (e.g. `1. Yes`, `2. Postgres`)."

Keep it short — don't re-list the questions in chat if they're already in the file.

---

## Quality checklist before writing

- [ ] Round number is correct (counted existing rounds in the document)
- [ ] Questions are specific to *this* document, not generic
- [ ] Every question uses numbered options (`1.`, `2.`, `3.`) — not letters
- [ ] Every question ends with an "Other" option
- [ ] `**User answer:**` is blank on every question
- [ ] Block is appended at the end, not inserted mid-document
- [ ] The intro callout tells the user how to respond
- [ ] The round header reads exactly `## Q&A Round N`
