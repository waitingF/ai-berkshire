#!/usr/bin/env python3
"""Generate DeepSeek Harness (DSH) skills from AI Berkshire Claude command files.

DSH discovers local skills through its filesystem provider: directory bundles
`<root>/<name>/SKILL.md` (or flat `<root>/<name>.md`) under the project-dsh root
`<project>/.dsh/skills`, the user-dsh root `<dshHome>/skills`, and friends.
Each SKILL.md must carry YAML frontmatter with a kebab-case `name` and a
`description`; optional DSH fields are `whenToUse`, `metadata`,
`disable-model-invocation`, and `user-invocable`.

This script regenerates `dsh-skills/*/SKILL.md` from the canonical
`skills/*.md` sources, supplying DSH-compatible frontmatter and a DSH adapter
note. Run `--check` to verify generated artifacts are current without writing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILLS = ROOT / "skills"
DSH_SKILLS = ROOT / "dsh-skills"

# Frontmatter keys the DSH skill-filesystem provider interprets. Unknown keys
# are dropped so the generated catalog stays valid and predictable.
KNOWN_FM_KEYS = {
    "name",
    "description",
    "whenToUse",
    "metadata",
    "disable-model-invocation",
    "user-invocable",
}


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :].lstrip("\n")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def dsh_metadata(name: str, source_name: str, source_text: str) -> str:
    """Build DSH frontmatter: required name/description plus passthrough of the
    DSH-understood keys already present in the source frontmatter."""
    existing, body = split_frontmatter(source_text)
    kept: list[str] = []
    if existing:
        for line in existing.splitlines():
            key = line.split(":", 1)[0].strip()
            if key in KNOWN_FM_KEYS:
                kept.append(line)
    has_name = any(re.match(r"^name:\s*", line) for line in kept)
    has_desc = any(re.match(r"^description:\s*", line) for line in kept)
    if not has_name:
        kept.insert(0, f"name: {name}")
    if not has_desc:
        kept.append("description: " + yaml_quote(first_heading(body, name)))
    return "---\n" + "\n".join(kept) + "\n---\n\n"


def dsh_body(name: str, source_name: str, source_text: str) -> str:
    _, body = split_frontmatter(source_text)
    note = (
        "## DeepSeek Harness adapter note\n\n"
        f"This skill is generated from `skills/{source_name}` so Claude Code, "
        "Codex, Cursor, and DeepSeek Harness users share one canonical "
        "workflow.\n\n"
        "- Treat `$ARGUMENTS` as the user's request in the current DeepSeek "
        "Harness session.\n"
        "- When the source mentions Claude-only surfaces such as Task, Agent, "
        "WebSearch, Bash, Read, or Write, use the closest DeepSeek Harness "
        "capability available in this session: `subagent` for parallel "
        "research, `web_search` for web queries, `bash` for local commands, "
        "and the read/write/edit/grep/glob tools for files.\n"
        "- Use shared project tools from `tools/` in this repository. Prefer "
        "running commands from the repository root with paths like\n"
        "`python3 tools/financial_rigor.py ...`; if the current session "
        "starts outside the repo, locate the actual checkout path first "
        "instead of assuming a fixed home-directory path.\n"
        "- Before starting research, run the `date` command to confirm "
        "today's date; treat it as the baseline for \"latest\" data and state "
        "the data cutoff date in the report header. Never assume the current "
        "date from training data.\n"
        "- Preserve the research quality rules from `AGENTS.md`: cross-check "
        "financial data, use exact arithmetic tools for valuation/math, and "
        "clearly label uncertainty and source gaps.\n\n"
    )
    return note + body.rstrip() + "\n"


def main() -> None:
    check = "--check" in sys.argv[1:]
    unknown_args = [arg for arg in sys.argv[1:] if arg != "--check"]
    if unknown_args:
        joined = ", ".join(unknown_args)
        raise SystemExit(f"Unknown argument(s): {joined}")

    if not check:
        DSH_SKILLS.mkdir(exist_ok=True)

    count = 0
    stale: list[str] = []
    for source in sorted(CLAUDE_SKILLS.glob("*.md")):
        name = source.stem
        source_text = source.read_text(encoding="utf-8")
        target_dir = DSH_SKILLS / name
        target = target_dir / "SKILL.md"
        content = dsh_metadata(name, source.name, source_text) + dsh_body(
            name, source.name, source_text
        )
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(str(target.relative_to(ROOT)))
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        count += 1

    if check:
        if stale:
            print("DeepSeek Harness skills are out of date:")
            for path in stale:
                print(f"  {path}")
            raise SystemExit(1)
        print(f"Checked {count} DeepSeek Harness skills in {DSH_SKILLS.relative_to(ROOT)}")
        return

    print(f"Generated {count} DeepSeek Harness skills in {DSH_SKILLS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
