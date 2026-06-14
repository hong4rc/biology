# Trắc Nghiệm Y Khoa

A dependency-free, build-free static web app of Vietnamese medical multiple-choice quizzes. No framework, no bundler, no install step — just static files.

## Run it (serve locally)

`quiz.html` loads question data with `fetch()`, which browsers **block over `file://`**. So you cannot just double-click `index.html` — you must serve the folder over HTTP. Pick any one:

```bash
# Python 3 (already on macOS/Linux) — recommended, zero setup
python3 -m http.server 8000

# Node (no install — npx downloads it on first run)
npx serve .

# PHP
php -S localhost:8000
```

Then open the printed URL in a browser:

- Python / PHP → **http://localhost:8000/**
- `npx serve` → **http://localhost:3000/**

Stop the server with `Ctrl+C`. After editing a file, **hard-refresh** the browser (Cmd/Ctrl+Shift+R) to bypass cache.

> No server? You can also use the VS Code **Live Server** extension (right-click `index.html` → "Open with Live Server") — same effect.

## Using a quiz

Open the landing page, pick a quiz card, then answer. Features:

- **Progress is saved automatically** in the browser (`localStorage`) — close the tab and resume later.
- **Trộn** — shuffle the order questions are presented in (your answers/score stay intact).
- **Tự chuyển** — auto-advance to the next question shortly after you answer (on by default).
- **Bookmark (🔖)** any question, then use the **Đánh dấu** filter to revisit flagged ones.
- **Question map** — jump to any question; filter by Chưa làm / Sai / Đúng / Đánh dấu; search by number.
- **Completion summary** — score and % appear when you finish; jump straight to your wrong answers.
- **Xuất** — export your results as a JSON file.
- **Keyboard:** `←` / `→` previous/next, `1`–`4` pick an option, `S` toggle shuffle.

## Project structure

```
index.html              Landing page — lists quizzes (the TESTS[] array)
quiz.html               The quiz engine (shared by every quiz)
data/<name>.json        One question set per file
test/validate-quizzes.mjs   Schema + wiring validator
```

`quiz.html` is generic: it reads `?data=<name>` from the URL and fetches `data/<name>.json`. You never edit it to add a quiz.

## Adding a new quiz

1. Create `data/<name>.json`:

   ```json
   {
     "title": "Trắc Nghiệm Ví Dụ",
     "storageKey": "vidu_quiz_progress",
     "questions": [
       { "id": 1, "text": "Câu hỏi?", "options": ["A", "B", "C", "D"], "answer": 0 }
     ]
   }
   ```

   `answer` is the **0-based index** of the correct option (`0` = first option, not the letter "A"). Save as **UTF-8** to keep Vietnamese diacritics.

2. Add a card to the `TESTS[]` array in `index.html` (keep `<name>` consistent across all three):

   ```js
   {
     title: 'Ví Dụ',
     subtitle: 'Mô tả ngắn',
     url: 'quiz.html?data=vidu',
     dataUrl: 'data/vidu.json',
     storageKey: 'vidu_quiz_progress',
     icon: 'science',          // any Material Icons Round name
     accent: '#10b981',
     accentLight: '#ecfdf5',
   },
   ```

3. Validate:

   ```bash
   node test/validate-quizzes.mjs
   ```

   It checks every `data/*.json` for a valid schema (unique ids, non-empty options, in-range `answer`) and confirms each set is wired into `index.html`. Run it before serving.
