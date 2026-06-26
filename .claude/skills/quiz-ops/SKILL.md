---
name: quiz-ops
description: Orchestrates all quiz app work: importing new question sets from .doc/.docx files, modifying the quiz engine (quiz.html), and validating quiz data. Triggers on: add quiz, import quiz, new question set, thêm bộ câu hỏi, parse docx, add subject, fix quiz, update quiz engine, improve UX, modify quiz.html, quiz bug, validate, check quizzes, kiểm tra, run again, re-run, update again. NOT for: general web development outside this project, or non-quiz static site work.
---

# quiz-ops · Quiz App Orchestrator

Routes and coordinates all work across the three quiz specialists. Every quiz task flows through this skill.

## Agents

| Agent | Role | Model |
|---|---|---|
| `quiz-importer` | Parse .docx → `data/<name>.json` + wire `index.html` | sonnet |
| `quiz-validator` | Run `node test/validate-quizzes.mjs` | haiku |
| `quiz-engine` | Modify `quiz.html` state model / UX | sonnet |

## Phase 0: Context Check

Before routing, check for in-progress work:
- `_workspace/<name>_draft.json` exists → likely mid-import; ask the user if they want to resume or start fresh.
- `_workspace/` absent or empty → fresh run.

## Phase 1: Route

Classify the request and pick the right flow:

| Request | Flow | Gate? |
|---|---|---|
| Add / import a quiz set | Import flow (Phase 2) | Yes |
| Fix / update quiz.html / UX | Engine flow (Phase 3) | No |
| Validate / check data | Validate flow (Phase 4) | No |

## Phase 2: Import Flow

Source .docx files typically carry no answer key — correct answers must be filled from domain knowledge. A mandatory gate prevents committing uncertain answers.

```
[quiz-importer — Phase A: Draft]
  Parse .docx, write _workspace/<name>_draft.json
  Flag uncertain answers with _todo: true
  Print summary + list of TODO questions

↓ GATE: User reviews and corrects uncertain answers ↓

[quiz-importer — Phase B: Finalize]
  Apply corrections, strip _todo fields
  Write data/<name>.json
  Append TESTS[] entry to index.html

[quiz-validator]
  Run node test/validate-quizzes.mjs
  Report PASS or FAIL with fix guidance
```

**Presenting the gate:** Show each TODO question with its text and options. Ask the user to confirm or correct by replying with something like "Q3→B, Q7→C" (letter) or "Q3→1, Q7→2" (0-based index). Convert letters to 0-based before passing to Phase B.

## Phase 3: Engine Flow

```
[quiz-engine]
  Implement the requested change in quiz.html
  Preserve state model invariants

[quiz-validator] — only if data loading was touched
  Run node test/validate-quizzes.mjs
```

## Phase 4: Validate Flow

```
[quiz-validator]
  Run node test/validate-quizzes.mjs
  Report results
```

## Execution Mode

**Subagent** — all phases are sequential and data-dependent. Each agent is spawned with the `Agent` tool after the previous step completes (or after the gate). No parallel execution.

## Data Passing

- Draft files: `_workspace/<name>_draft.json` (intermediate, not committed)
- Final quiz files: `data/<name>.json`
- Validator results: relayed directly from the agent's return

## Error Handling

| Error | Action |
|---|---|
| quiz-importer cannot parse .docx | Stop; report error; ask user to verify file path |
| quiz-validator FAIL after import | Relay failures with fix suggestions; do NOT mark import complete |
| quiz-engine change breaks validation | Relay failures; recommend reverting the change |
| Question count < 10 after parse | Warn before proceeding; likely a parse failure |

## Test Scenarios

**Normal — add new quiz set:**
1. User provides path to a `.docx` file
2. quiz-importer Phase A: parses, produces draft with 5 TODOs
3. Gate: user reviews, corrects answers ("Q3→B, Q12→A, Q45→C, Q67→B, Q89→D")
4. quiz-importer Phase B: finalizes `data/new-subject.json`, wires `index.html`
5. quiz-validator: PASS — reports new set name and count

**Error — unparseable docx:**
1. quiz-importer cannot extract XML
2. Reports the error with the raw exception
3. Asks user to confirm file path or provide a different file

**Normal — fix quiz engine:**
1. User asks to change auto-advance delay from 0.85s to 1.2s
2. quiz-engine reads quiz.html, finds the timer constant, updates it
3. quiz-validator: skipped (data loading not touched)
4. Reports the changed line

**Normal — validate only:**
1. quiz-validator runs `node test/validate-quizzes.mjs`
2. Reports PASS with all set names and question counts
