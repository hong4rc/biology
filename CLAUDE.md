# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A dependency-free, build-free static web app of Vietnamese medical multiple-choice quizzes (trắc nghiệm y khoa). Three files do everything: `index.html` (landing page), `quiz.html` (the quiz engine), and `data/*.json` (question sets). There is no framework, no bundler, and no `package.json`.

## Commands

```bash
# Serve locally — REQUIRED to test. quiz.html uses fetch() for the JSON,
# which browsers block over file://, so opening index.html directly fails.
python3 -m http.server 8000        # then open http://localhost:8000/

# Validate all question sets + that they are wired into index.html
node test/validate-quizzes.mjs
```

`test/validate-quizzes.mjs` is the only test. It checks every `data/*.json` for schema validity (id/text/options/answer, in-range answer index, unique ids) and verifies `index.html` references each set's `data/<name>.json`, `quiz.html?data=<name>` link, and `storageKey`. Run it after any change to a JSON set or to the `TESTS[]` array.

## Architecture

**Adding a quiz is a three-part contract that spans files** — this is the main thing to understand:

1. `data/<name>.json` — shape: `{ title, storageKey, questions: [{ id, text, options: [...], answer }] }`. `answer` is the **0-based index** into `options` of the correct choice (NOT a letter). `id` is the real question number shown only in exported results.
2. `index.html` — append an entry to the `TESTS[]` array (`url: 'quiz.html?data=<name>'`, `dataUrl: 'data/<name>.json'`, matching `storageKey`, plus `icon`/`accent`/`accentLight` for the card).
3. The `<name>` in the URL, the JSON filename, and the card must all agree. `quiz.html` reads `?data=<name>` and fetches `data/<name>.json` generically — it is never edited to add a quiz.

**quiz.html state model** (all persisted to `localStorage` under the set's `storageKey`):
- `answers` and `flags` are keyed by **original question index** (stable regardless of shuffle).
- `order` is a permutation: display-position → original index. `current` is a **display position**, so the live question is always `questions[order[current]]`. Identity order when shuffle is off; Fisher–Yates when on.
- The UI shows **play position** (Câu 1, 2, 3… and grid 1..N), never the shuffled real `id`, so navigation reads sequentially. Keep this invariant when touching `render`/`renderGrid`/`searchQuestion`/the card badge.
- Other state: `shuffleEnabled`, `autoAdvance` (default on; auto-jumps to next question ~0.85s after answering), `activeFilter` (all/unanswered/wrong/correct/flagged). Completion summary fires from `pick()` when every question is answered.

**Encoding:** all content is Vietnamese UTF-8 — preserve diacritics in every JSON edit. `fmt()` in quiz.html converts Unicode sub/superscripts (e.g. CO₂) to `<sub>`/`<sup>`.

## Importing questions from a .docx

Source question docs (e.g. `Câu hỏi ôn tập ....docx`) are unzipped and parsed in throwaway Python scripts; only the resulting `data/<name>.json` is committed. The Word docs are messy: mixed `Câu N.` and bare `N.` numbering, option A occasionally glued into the stem, True/False (2-option) questions, and gaps/duplicates in source numbering — so questions are re-`id`'d sequentially 1..N. **Source docs typically carry no answer key**; correct answers are filled from domain knowledge and should be flagged for review when uncertain.
