# AI Berkshire Codex Guide

This repository contains investment research workflows, reports, and shared
validation tools. Keep compatibility with Claude Code, Codex, Cursor, and
DeepSeek Harness users.

## Project Layout

- `skills/*.md`: Claude Code slash-command source files.
- `codex-skills/*/SKILL.md`: Codex skill packages. Most are generated from
  `skills/*.md`; Codex-only hand-written packages are allowed when clearly
  marked and no same-named `skills/*.md` source exists.
- `codex-prompts/*.md`: generated Codex custom prompts for slash-command
  style entry points. These are a compatibility layer; skills remain preferred.
- `cursor-skills/*/SKILL.md`: Cursor skill packages generated from
  `skills/*.md`.
- `dsh-skills/*/SKILL.md`: DeepSeek Harness skill packages generated from
  `skills/*.md`.
- `tools/*.py`: shared financial validation and data tools used by both systems.
- `reports/`: research outputs. Do not rewrite unrelated reports while changing
  tooling or skills. `reports/daily-monitor/` holds the active unified weekday
  monitor. `reports/weekly-check/` and `reports/trigger-scan/` are historical
  archives and are not updated or composed into the active Pages entry.
- `scripts/sync-codex-skills.py`: regenerates Codex skills from `skills/*.md`.
- `scripts/install-codex-skills.sh` / `scripts/install-codex-skills.bat`:
  installs Codex skills locally.
- `scripts/install-codex-prompts.sh` / `scripts/install-codex-prompts.bat`:
  installs generated Codex slash prompts locally.
- `scripts/install-claude-commands.sh` / `scripts/install-claude-commands.bat`:
  installs Claude Code commands locally.
- `scripts/sync-cursor-skills.py`: regenerates Cursor skills from `skills/*.md`.
- `scripts/install-cursor-skills.sh` / `scripts/install-cursor-skills.bat`:
  installs Cursor skills locally (`~/.cursor/skills` or `.cursor/skills`).
- `scripts/generate-dsh-skills.py`: regenerates DeepSeek Harness skills from
  `skills/*.md` (supports `--check`).
- `scripts/install-dsh-skills.sh` / `scripts/install-dsh-skills.bat`:
  installs DeepSeek Harness skills locally (`<repo>/.dsh/skills` project root
  or `$DSH_HOME/skills` user root).

## Compatibility Rules

- Treat `skills/*.md` as the canonical workflow source.
- After changing any file in `skills/`, run:
  `python3 scripts/sync-codex-skills.py`
  `python3 scripts/sync-cursor-skills.py`
  and `python3 scripts/generate-dsh-skills.py`
- If slash prompt compatibility is needed, also run:
  `python3 scripts/sync-codex-prompts.py`
- Do not manually edit generated `codex-skills/*/SKILL.md`,
  `cursor-skills/*/SKILL.md`, or `dsh-skills/*/SKILL.md` unless also updating
  the corresponding source in `skills/`.
- Do not install generated skills into `~/.cursor/skills-cursor`; that
  directory is reserved by Cursor.
- For Codex-only hand-written packages under `codex-skills/`, keep them clearly
  marked as Codex-only and do not create a same-named `skills/*.md` file unless
  intentionally adopting the workflow for Claude Code too.
- Keep tool paths compatible with the documented checkout path:
  `~/ai-berkshire/tools/...`
- Keep `CLAUDE.md` for Claude Code behavior and this `AGENTS.md` for Codex
  behavior.

## Research Quality Rules

- Before starting any research, run the `date` command to confirm today's
  date. Treat that date as the baseline for "latest" data (prices, market cap,
  most recent filings), and state the data cutoff date in the report header.
  Never assume the current date from training data.
- Financial data must come from at least two independent sources when the skill
  requires verification.
- Use exact arithmetic tools for market cap, valuation, cross-source checks, and
  scenario analysis:
  `python3 tools/financial_rigor.py ...`
- Use report audit tooling before treating generated research as publishable:
  `python3 tools/report_audit.py ...`
- Clearly label low-confidence conclusions, incomplete data, and source gaps.
- This project is for learning and research, not investment advice.

## Trigger Monitoring Rules (标的触发监控)

- Any research report containing an explicit buy/wait/avoid price band or a
  review/earnings checkpoint must register it in `data/triggers.json`
  (zones/events; see `skills/trigger-monitor.md`). **Not registered = not
  monitored.**
- After updating `data/triggers.json`, bump the `updated` field and run
  `python3 tools/trigger_scanner.py --check`.
- Before pushing any change touching `data/triggers.json` or
  `tools/trigger_scanner.py`, run `bash scripts/prepush-check.sh` (local
  validation, no notifications) and get explicit user confirmation to commit.
- Daily monitor: `python3 tools/daily_monitor.py` writes the exact three sections
  `价格监控`, `财报与正式披露监控`, and `其他监控`. GitHub Actions
  `.github/workflows/daily-monitor.yml` runs weekdays at 17:30 Asia/Shanghai.
- Official disclosure scope is CNINFO, HKEXnews, and SEC EDGAR. AKShare is
  fallback-only; do not add general web search to this runtime pipeline.
- `data/triggers.json` remains human-authored configuration while
  `data/monitoring-state.json` is machine-authored runtime state. Do not merge
  them. Do not commit downloaded PDFs, full announcement text, extracted text,
  complete model prompts, or secrets.
- Pages pins `reports/daily-monitor/daily-monitor-latest.md` as "每日监控".
  Historical weekly-check and trigger-scan files remain browsable only as
  archives.

## Editing Rules

- Preserve existing report files unless the task specifically asks to change
  them.
- Keep changes scoped to the requested skill, tool, script, or documentation.
- Before finishing a skill/tool change, run the relevant syntax or generation
  check. For compatibility changes, run:
  `python3 scripts/sync-codex-skills.py`
  `python3 scripts/sync-cursor-skills.py`
  and `python3 scripts/generate-dsh-skills.py`
- To verify generated Codex/Cursor artifacts are current without rewriting
  files, run:
  `python3 scripts/sync-codex-skills.py --check`
  `python3 scripts/sync-cursor-skills.py --check`
  `python3 scripts/generate-dsh-skills.py --check`
  and, when slash prompts are relevant:
  `python3 scripts/sync-codex-prompts.py --check`
