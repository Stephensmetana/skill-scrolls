# Token Waste Checklist

Use this during REVIEW mode to systematically identify every source of waste.
Work through each section in order. Note findings as Critical / Yellow / Quick Win.

---

## Section 1: Skill Body (SKILL.md)

### 1.1 Routing description
- [ ] Is the description focused on *when to trigger* (routing signal)?
      Or is it explaining *what the skill does* (educational)?
      **Cost:** Educational descriptions add tokens to every skill selection decision.
      Estimate: 50–300 extra tokens per session.

- [ ] Does the description include examples of trigger phrases?
      Good: `"Triggers on .py files, import errors, pytest failures"`
      Bad: `"This skill helps you with Python development"`

- [ ] Does the description duplicate content already in the skill body?
      Duplication means those tokens appear twice in context.

### 1.2 Skill body length and loading
- [ ] Is the body under 500 lines?
      Over 500 lines = almost certainly has content that belongs in reference files.

- [ ] Is there content that only applies to some tasks but always loads?
      Example: "When working with PostgreSQL..." in a skill that also handles MySQL/SQLite.
      This content should be in a conditional reference file.

- [ ] Does the body contain inline code snippets, full API responses as examples,
      or large tables that repeat the same pattern many times?
      These should be in reference files, not the body.

- [ ] Does the body contain linter rules, code style guides, or formatting standards?
      **Critical:** Use a linter instead. These consume hundreds of tokens and
      degrade instruction-following on every invocation.

### 1.3 Reference file handling
- [ ] Are reference files listed with unconditional instructions to read them?
      BAD: `"Read ./reference/api-docs.md before beginning any task"`
      GOOD: `"./reference/api-docs.md — load if task involves API payloads"`

- [ ] Do any reference files exceed 300 lines without a table of contents?
      Large files need a ToC so the agent can navigate to relevant sections
      without loading the whole thing into context.

- [ ] Are executable scripts inlined as code blocks instead of executed?
      **Critical:** If you see a Python/bash script pasted into SKILL.md,
      it should be in `scripts/` and executed — the source code adds tokens
      for zero benefit. Only the output needs to reach the LLM.

### 1.4 Tool name format
- [ ] Do tool names use underscores, dashes, or dots?
      `read_config` → `ReadConfig` (each separator = extra token)

---

## Section 2: Tool / Function Design

### 2.1 Return value shape
- [ ] Does the tool return raw file contents without summarization?
      **Critical waste.** Even a 100-line Python file = 600–1,000 tokens.
      A JSON config = 500–5,000 tokens. A SQL query result = unbounded.

- [ ] Does the tool return all fields from an API response?
      Most API responses have 20–200 fields. The agent typically needs 5–10.
      Extra fields = silent token tax on every call.

- [ ] Does the tool return any data as raw text that could be structured?
      Raw text forces the LLM to parse; structured summaries let it route.

- [ ] Does the tool return a reference ID (pointer) the agent can use later?
      Without a pointer, the agent has no way to refer back to the data without
      re-fetching it into context.

### 2.2 Caps and pagination
- [ ] Does the tool have a `max_results` parameter or equivalent cap?
      Without a cap: a search tool might return 10,000 matches at 5 tokens each = 50,000 tokens.
      With a cap of 20: 100 tokens. Same task completed.

- [ ] Does the tool provide an offset/pagination mechanism for getting more?
      Without it: the agent either re-fetches everything or gives up.
      With it: agent can descend into data only when needed.

- [ ] For list/search tools, does the return group results meaningfully?
      BAD: 500 individual line matches from grep
      GOOD: matches grouped by file, top 10 files by match count, line numbers only

### 2.3 Companion fetch tools
- [ ] For every tool that returns a pointer/summary, is there a targeted fetch tool?
      The pointer pattern only works if the agent has a way to retrieve specific data.
      `ReadConfig()` → needs a companion `GetConfigValue(key)`
      `SearchCodebase()` → needs a companion `ReadFileLines(path, start, end)`

### 2.4 Tool set coherence
- [ ] Are there any two tools with overlapping functionality?
      Overlap forces the LLM to reason about which one to use — consuming tokens
      in uncertainty. If a human engineer can't immediately decide, the LLM can't.

- [ ] Does the tool set have a discovery mechanism for large surfaces (10+ tools)?
      Without discovery: all tool descriptions load upfront for every call.
      With discovery: agent calls `ListTools(category)` → reads 3 descriptions → acts.

---

## Section 3: Code / Pipeline Design

### 3.1 Data handling
- [ ] Does the code pass entire file contents to the LLM?
      Red flag: `return open(path).read()` or `content = file.read(); llm.call(content)`

- [ ] Does the code pass entire API responses to the LLM?
      Red flag: `response = requests.get(url); llm.call(response.text)`

- [ ] Does the code pass database query results as full row dumps?
      Red flag: `rows = db.fetchall(); llm.call(str(rows))`

- [ ] Is chunking used, and if so, is a summary passed rather than each raw chunk?
      Passing all chunks defeats the point. The LLM should receive summaries.

- [ ] If LLM-based summarization is used, is there a note about API access requirements?
      `call_llm_lightweight()` style functions require direct API access — not available
      in claude.ai chat interface without an API key.

### 3.2 Session / conversation management
- [ ] Does the code include the full conversation history in every LLM call?
      In a 30-turn session, turn 30 includes all 29 previous turns' tokens.
      This compounds aggressively.

- [ ] Is there any compression or compaction trigger?
      Without it: context grows unboundedly until the window overflows.
      With it: agent triggers a structured summarization at 50–70% capacity.

- [ ] Is state maintained inside the conversation (message history) or outside it?
      Inside = state re-sent in full on every turn.
      Outside (a file, dict, DB) = state loaded selectively, not always.

- [ ] Does the code use observation masking for stale tool results?
      Old tool outputs from early turns are often carried verbatim into turn 20+.
      After the agent acts on a result, it should be collapsed to a one-liner.

### 3.3 Subagent design (if applicable)
- [ ] Do subagents receive the full parent context?
      They should receive only what they need for their specific task.
      A code-editing subagent needs: the file, the edit instruction. Nothing else.

- [ ] Do subagents return full results or targeted summaries?
      Subagents should return: the specific output + a brief summary.
      Not: everything they read, every intermediate step.

---

## Token Cost Reference Table

Use these estimates when communicating impact to users:

| Content type | Typical token range |
|-------------|-------------------|
| 50-line Python file | 400–700 |
| 200-line Python file | 1,500–2,500 |
| Small JSON config (20 keys) | 200–500 |
| Large JSON config (100+ keys) | 1,000–5,000 |
| REST API response (full) | 500–3,000 |
| REST API response (5 key fields) | 50–150 |
| SQL result (100 rows × 10 cols) | 5,000–15,000 |
| SQL result (5 rows × 3 cols) | 200–500 |
| grep output (100 matches) | 1,000–3,000 |
| grep output (grouped, top 10 files) | 200–400 |
| Verbose SKILL.md body | 2,000–8,000 |
| Lean SKILL.md body | 300–800 |
| Tool definition (verbose prose) | 200–500 each |
| Tool definition (tight routing signal) | 50–100 each |
| Full conversation (30 turns) | 20,000–100,000+ |
| Structured working memory summary | 500–1,500 |
