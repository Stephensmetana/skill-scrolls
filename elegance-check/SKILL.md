---
name: elegance-check
description: >
  Pause before implementing a solution to run an "elegance check" — a structured
  moment of reflection on whether the proposed approach is truly the best one.
  Use this skill whenever you're about to write code, design a system, choose a
  framework or library, plan an architecture, or propose any non-trivial technical
  solution. Trigger it especially when: (1) the first solution that came to mind
  feels "good enough", (2) a framework or external dependency is being introduced,
  (3) the solution involves more than ~50 lines of code, (4) the user asks you to
  "build", "implement", "design", or "architect" something, or (5) you sense you
  might be over-engineering or under-engineering. The check must happen BEFORE
  writing implementation code, not after.
---

# Elegance Check

A structured pause before implementation. Run this before writing non-trivial code
or proposing an architecture. The goal is to surface better options early — when
changing course is cheap — rather than after code is written.

---

## When to Run

Run the elegance check **before implementation** whenever:

- You're about to choose a framework, library, language, or architecture pattern
- The solution will be >~50 lines of code
- You're introducing a new dependency
- The problem has multiple valid approaches
- You notice yourself reaching for a "familiar" tool out of habit
- The user says things like: build, implement, design, architect, create, make, write

Skip it for: trivial fixes, single-function utilities, copy/paste tasks, or when
the user explicitly just wants a quick draft.

---

## The Check

Work through these questions silently (or briefly aloud if it adds value). Don't
just tick boxes — actually reason through each one. If any answer is "no" or
"I'm not sure", treat that as a signal to reconsider before proceeding.

### 1. Elegance
- Is this solution simple enough that a reasonably experienced developer could
  understand it in 5 minutes without explanation?
- Am I solving the *actual* problem, or a generalized version of it?
- Does this solution feel "clever" in a way that might be hard to follow later?
  (Clever is a warning sign, not a compliment.)
- Is there a 10-line version of this that would do 90% of the job?

### 2. Best Tool for the Job
- Is this the right **language** for the task? (e.g., don't reach for Python if
  a shell one-liner would do; don't use JS if the user's stack is Go)
- Is this the right **framework**? Would the standard library suffice? Is the
  framework's overhead (learning curve, bundle size, abstraction cost) worth it?
- Is this the right **design pattern**? Am I using a pattern because it fits,
  or because it's familiar?
- Am I introducing a **dependency** that I could avoid? Every dependency is a
  future maintenance burden. Is this one earning its keep?
- What would a senior engineer with no attachment to any particular tool choose?

### 3. Maintainability & Extensibility
- If I left this project for 6 months and came back, could I understand it?
- Could a new team member make changes without fully understanding the whole system?
- Is responsibility clearly separated? (Each function/class/module does one thing)
- Am I violating **DRY** (Don't Repeat Yourself)? Is logic duplicated?
- Am I violating **YAGNI** (You Aren't Gonna Need It)? Am I building for a
  hypothetical future requirement instead of the actual current one?
- Is this **KISS** (Keep It Simple)? The simplest solution is almost always
  better — but simplicity requires effort, it's not the lazy path.
- Where does this accrue **tech debt**? Name it explicitly, even if you proceed.

### 4. Robustness & Scale (right-size this to the problem)
- What breaks first if usage grows 10x?
- What are the obvious edge cases? Are they handled or explicitly deferred?
- Is error handling present where it matters?
- Is this secure by default, or does it require the user to "use it correctly"?

### 5. The Alternatives Test
- What are 2–3 completely different approaches to this problem?
- What would the *minimal viable* version look like? Could I propose that first?
- Am I defaulting to a tool or pattern I've used before when a better fit exists?

---

## Output Format

After running the check, briefly surface what you found before writing code:

```
**Elegance Check**
✅ Approach: [what you're going with and why]
⚠️  Trade-offs: [what you're accepting / tech debt being knowingly incurred]
🔀 Alternatives considered: [what you ruled out and why]
```

Keep this brief — 3–6 lines total. Then proceed with implementation.

If the check surfaces a serious concern (wrong tool, over-engineered, better
approach exists), **say so clearly** and propose the better path before writing
any code. Don't proceed with a solution you've identified as suboptimal just
to avoid friction.

---

## Principles Reference

| Principle | Question to ask |
|-----------|----------------|
| **KISS** | Is this the simplest thing that could work? |
| **DRY** | Is any logic duplicated that should be shared? |
| **YAGNI** | Am I building this for a real, current need? |
| **SOLID** | Does each piece have one clear responsibility? Can I extend without modifying? |
| **SINE** | Did I do the work to make this *genuinely* simple, or just short? |

> "Simplicity is not the absence of complexity — it's the result of working through it."

---

## Anti-Patterns to Watch For

- **Familiar tool bias**: Reaching for React/Redux/Django/etc. because you know it,
  not because it's the right fit.
- **Speculative generality**: Building abstractions for use cases that don't exist yet.
- **Dependency creep**: Adding a library to avoid writing 20 lines of code.
- **Premature optimization**: Adding caching, queues, or microservices before
  there's evidence they're needed.
- **Gold-plating**: Making something more polished/complete than the task requires.
- **Abstraction inversion**: Wrapping something simple in unnecessary layers.
