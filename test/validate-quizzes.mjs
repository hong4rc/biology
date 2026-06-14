#!/usr/bin/env node
// Self-contained validator for the quiz app — no dependencies.
// Checks every data/*.json question set for a valid schema and verifies
// that index.html wires each set in (dataUrl + storageKey).
// Run:  node test/validate-quizzes.mjs

import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = join(root, 'data');

let failures = 0;
const fail = (msg) => { console.error('  ✗ ' + msg); failures++; };
const ok = (msg) => console.log('  ✓ ' + msg);

const indexHtml = readFileSync(join(root, 'index.html'), 'utf8');
const files = readdirSync(dataDir).filter((f) => f.endsWith('.json'));

if (files.length === 0) fail('no question-set JSON files found in data/');

for (const file of files) {
  console.log(`\n${file}`);
  let doc;
  try {
    doc = JSON.parse(readFileSync(join(dataDir, file), 'utf8'));
  } catch (e) {
    fail(`invalid JSON: ${e.message}`);
    continue;
  }

  if (typeof doc.title !== 'string' || !doc.title.trim()) fail('missing/empty "title"');
  if (typeof doc.storageKey !== 'string' || !doc.storageKey.trim()) fail('missing/empty "storageKey"');
  if (!Array.isArray(doc.questions) || doc.questions.length === 0) {
    fail('"questions" must be a non-empty array');
    continue;
  }

  const seenIds = new Set();
  let badQ = 0;
  for (const q of doc.questions) {
    const tag = `Q${q && q.id}`;
    if (!q || typeof q !== 'object') { fail(`${tag}: not an object`); badQ++; continue; }
    if (!Number.isInteger(q.id)) { fail(`${tag}: "id" must be an integer`); badQ++; }
    if (seenIds.has(q.id)) { fail(`${tag}: duplicate id`); badQ++; }
    seenIds.add(q.id);
    if (typeof q.text !== 'string' || !q.text.trim()) { fail(`${tag}: missing/empty "text"`); badQ++; }
    if (!Array.isArray(q.options) || q.options.length < 2) { fail(`${tag}: needs >= 2 options`); badQ++; continue; }
    if (q.options.some((o) => typeof o !== 'string' || !o.trim())) { fail(`${tag}: has empty option`); badQ++; }
    if (!Number.isInteger(q.answer) || q.answer < 0 || q.answer >= q.options.length) {
      fail(`${tag}: "answer" (${q.answer}) out of range 0..${q.options.length - 1}`); badQ++;
    }
  }
  if (badQ === 0) ok(`${doc.questions.length} questions, schema valid`);

  // wiring: derive dataParam from filename and confirm index.html references it
  const param = file.replace(/\.json$/, '');
  if (!indexHtml.includes(`data/${file}`)) fail(`index.html does not reference data/${file}`);
  else if (!indexHtml.includes(`quiz.html?data=${param}`)) fail(`index.html missing quiz.html?data=${param} link`);
  else if (!indexHtml.includes(doc.storageKey)) fail(`index.html missing storageKey "${doc.storageKey}"`);
  else ok('wired into index.html');
}

console.log('');
if (failures > 0) {
  console.error(`FAIL — ${failures} problem(s) found`);
  process.exit(1);
}
console.log('PASS — all question sets valid and wired in');
