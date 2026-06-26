#!/usr/bin/env python3
"""
validate_harness.py — structural validator for a harness.

Enforces the rules the harness skill itself prescribes, so a generated harness
(or this plugin's own skill) can be checked deterministically instead of by eye.

Checks (per SKILL.md Phase 6-1 + the skill-writing guide):
  - every SKILL.md has YAML frontmatter with non-empty `name` and `description`
  - a skill's `name` matches its directory name
  - the `description` carries a should-NOT-trigger boundary (heuristic: "NOT for" / "Not for")
  - reference files >= 300 lines contain a "Table of Contents"
  - a SKILL.md body over 500 lines is flagged (the skill targets < 500)
  - no `.claude/commands/` directory is generated (the skill never creates commands)

Usage:
  validate_harness.py [PATH ...]      # default PATH: the skills/ dir next to this script's repo

Exit code 0 = all checks pass, 1 = at least one error. Warnings never fail the run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOC_RE = re.compile(r"^#{1,3}\s+(Table of Contents|Contents|ToC)\b", re.IGNORECASE | re.MULTILINE)
TOC_LINE_THRESHOLD = 300
SKILL_BODY_SOFT_LIMIT = 500

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Minimal YAML-frontmatter reader: top-level `key: value` pairs only."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def check_skill(skill_md: Path) -> None:
    text = skill_md.read_text(encoding="utf-8")
    rel = skill_md
    fm = parse_frontmatter(text)
    if fm is None:
        err(f"{rel}: missing or malformed YAML frontmatter")
        return

    name = fm.get("name", "")
    desc = fm.get("description", "")

    if not name:
        err(f"{rel}: frontmatter `name` is missing or empty")
    elif name != skill_md.parent.name:
        err(f"{rel}: `name: {name}` does not match its directory `{skill_md.parent.name}`")

    if not desc:
        err(f"{rel}: frontmatter `description` is missing or empty")
    elif not re.search(r"\bnot for\b", desc, re.IGNORECASE):
        warn(f"{rel}: `description` has no should-NOT-trigger boundary (add a \"NOT for ...\" clause)")

    body_lines = len(text.splitlines())
    if body_lines > SKILL_BODY_SOFT_LIMIT:
        warn(f"{rel}: {body_lines} lines exceeds the {SKILL_BODY_SOFT_LIMIT}-line target — move detail into references/")


def check_agent(agent_md: Path) -> None:
    text = agent_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        err(f"{agent_md}: missing or malformed YAML frontmatter")
        return

    name = fm.get("name", "")
    desc = fm.get("description", "")

    if not name:
        err(f"{agent_md}: frontmatter `name` is missing or empty")
    elif name != agent_md.stem:
        err(f"{agent_md}: `name: {name}` does not match its filename `{agent_md.stem}`")

    if not desc:
        err(f"{agent_md}: frontmatter `description` is missing or empty")


def check_reference(ref_md: Path) -> None:
    text = ref_md.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if line_count >= TOC_LINE_THRESHOLD and not TOC_RE.search(text):
        err(f"{ref_md}: {line_count} lines (>= {TOC_LINE_THRESHOLD}) but has no Table of Contents")


def check_no_commands(root: Path) -> None:
    for commands_dir in root.rglob(".claude/commands"):
        if commands_dir.is_dir() and any(commands_dir.iterdir()):
            err(f"{commands_dir}: the harness must not generate commands (.claude/commands should be absent/empty)")


def discover_targets(path: Path) -> tuple[list[Path], list[Path], list[Path]]:
    """Return (skill_md_files, reference_md_files, agent_md_files) under path."""
    skills = sorted(path.rglob("SKILL.md"))
    refs = sorted(p for p in path.rglob("references/*.md"))
    agents = sorted(path.rglob("agents/*.md"))
    return skills, refs, agents


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a harness structure.")
    parser.add_argument("paths", nargs="*", help="directories to validate (default: <repo>/skills)")
    args = parser.parse_args(argv)

    if args.paths:
        roots = [Path(p) for p in args.paths]
    else:
        # default: the skills/ dir of the repo this script lives in
        repo_skills = Path(__file__).resolve().parents[3] / "skills"
        roots = [repo_skills]

    all_md: list[Path] = []
    for root in roots:
        if not root.exists():
            err(f"{root}: path does not exist")
            continue
        skills, refs, agents = discover_targets(root)
        if not skills and not agents:
            warn(f"{root}: no SKILL.md or agents/*.md found under this path")
        for s in skills:
            check_skill(s)
        for r in refs:
            check_reference(r)
        for a in agents:
            check_agent(a)
        check_no_commands(root)
        all_md.extend(skills + refs + agents)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    checked = len(all_md)
    if errors:
        print(f"\n✗ {len(errors)} error(s), {len(warnings)} warning(s) across {checked} file(s)")
        return 1
    print(f"\n✓ all checks passed ({len(warnings)} warning(s)) across {checked} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
