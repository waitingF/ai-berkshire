# Weekly Review Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a default, read-only `/weekly-review` workflow that checks all focus-board companies and only actionable non-focus ledger rows, then outputs an evidence-backed P0/P1/P2 to-do list.

**Architecture:** The canonical workflow is one Markdown source at `skills/weekly-review.md`; it describes orchestration, source priority, selection rules, output contract, and strict no-write behavior. Existing generators create the Codex and Cursor adapters. A lightweight contract test prevents accidental expansion beyond the agreed default scope, and the README exposes the new entry point.

**Tech Stack:** Markdown skills; Python `unittest`; existing `scripts/sync-codex-skills.py` and `scripts/sync-cursor-skills.py` generators.

## Global Constraints

- The only supported entry point in v1 is `/weekly-review` without modes or arguments.
- The workflow is read-only: it must not modify reports, the focus board, the ledger, thesis files, or the portfolio file.
- Default coverage is every focus-board company plus only ledger rows that are due, triggered, near a numeric price condition, or qualify for thesis promotion.
- Live data uses company/market primary disclosures first; price/valuation and material numeric facts require two independent sources when feasible.
- Price movement alone cannot change thesis health or be presented as a fundamental change.
- Keep `skills/` canonical and regenerate Codex and Cursor artifacts; do not hand-edit generated skill files.

---

### Task 1: Add a testable weekly-review workflow contract

**Files:**
- Create: `tests/test_weekly_review_skill.py`
- Create: `skills/weekly-review.md`

**Interfaces:**
- Consumes: Markdown at `reports/重点标的看板.md`, `reports/买卖建议跟踪表.md`, and `reports/**/*-thesis*.md`.
- Produces: A chat-only Markdown report with the fixed sections `执行范围与数据截止日`, `本周待办队列`, `重点标的状态`, `非重点台账触发项`, `完整性检查`, and `建议分流`.
- Does not persist: No files are written by `/weekly-review`.

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_weekly_review_skill.py`:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "weekly-review.md"


class WeeklyReviewSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.text = SOURCE.read_text(encoding="utf-8")

    def test_default_scope_and_read_only_boundary_are_explicit(self):
        self.assertIn("重点标的看板", self.text)
        self.assertIn("买卖建议跟踪表", self.text)
        self.assertIn("未来 14 天", self.text)
        self.assertIn("不写入", self.text)
        self.assertIn("不修改", self.text)

    def test_priority_and_output_contract_are_explicit(self):
        for label in ("P0", "P1", "P2", "本周待办队列", "建议分流"):
            with self.subTest(label=label):
                self.assertIn(label, self.text)

    def test_price_is_not_a_fundamental_change(self):
        self.assertIn("价格变化不能单独改变论文健康度", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/test_weekly_review_skill.py`

Expected: FAIL with `FileNotFoundError` because `skills/weekly-review.md` does not yet exist.

- [ ] **Step 3: Write the canonical workflow**

Create `skills/weekly-review.md` with:

```markdown
# 周检：重点优先的研究待办分诊

对 `$ARGUMENTS` 执行默认周检。v1 只支持无参数 `/weekly-review`；如收到参数，说明该版本不支持参数模式后继续按默认范围执行。

本 Skill 只读、联网、重点优先：输出待办清单，不写入或修改任何报告、看板、台账、thesis 或组合文件。
```

Then add these required sections and rules:

1. Start by running `date` and state the data cutoff in the response.
2. Read the focus board, the ledger, every `*-thesis*.md`, and the selected companies’ newest local research/earnings files.
3. Query every focus-board company. Query only ledger rows whose review is due within 14 days, whose state is `已触发待决策` or `已过期`, whose clear price condition is near/reached, or which meet an existing thesis-promotion gate.
4. Give primary disclosures priority; label insufficient or conflicting sources `待人工确认`. Cross-check material prices, valuations, and numbers with two sources where feasible.
5. Classify P0/P1/P2 exactly as in the approved specification. Include the literal sentence `价格变化不能单独改变论文健康度` in the evidence rules.
6. Run the five completeness checks from the specification: thesis absent from board, decision report absent from board/ledger, missing next-check item in thesis, overdue open ledger row, and promotion-eligible ledger row without thesis.
7. Emit the six fixed output sections defined by the interface. Use the existing workflows only as recommendations: `earnings-review`, `news-pulse`, `thesis-tracker`, `thesis-drift`, and `portfolio-review`.
8. Explicitly forbid automatic buy/sell conclusions and file edits.

- [ ] **Step 4: Run the contract test to verify it passes**

Run: `python3 tests/test_weekly_review_skill.py`

Expected: PASS; all three contract tests pass.

- [ ] **Step 5: Commit the canonical workflow and its contract test**

```bash
git add skills/weekly-review.md tests/test_weekly_review_skill.py
git commit -m "feat: add weekly review workflow"
```

### Task 2: Generate compatible skill adapters and document the entry point

**Files:**
- Create: `codex-skills/weekly-review/SKILL.md` (generated)
- Create: `cursor-skills/weekly-review/SKILL.md` (generated)
- Modify: `README.md:17`
- Modify: `README.md:175-212`
- Modify: `README.md:376-380`
- Modify: `README.md:650-667`

**Interfaces:**
- Consumes: `skills/weekly-review.md` generated by Task 1.
- Produces: equivalent Codex and Cursor packages with their generator-provided adapter notes; a README catalog row and examples that link to the canonical source.

- [ ] **Step 1: Extend the failing contract test with generated-artifact and README assertions**

Append to `WeeklyReviewSkillContractTest`:

```python
    def test_generated_adapters_and_readme_expose_the_skill(self):
        codex = ROOT / "codex-skills" / "weekly-review" / "SKILL.md"
        cursor = ROOT / "cursor-skills" / "weekly-review" / "SKILL.md"
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(codex.exists())
        self.assertTrue(cursor.exists())
        self.assertIn("skills/weekly-review.md", codex.read_text(encoding="utf-8"))
        self.assertIn("skills/weekly-review.md", cursor.read_text(encoding="utf-8"))
        self.assertIn("[`/weekly-review`](skills/weekly-review.md)", readme)
```

- [ ] **Step 2: Run the extended test to verify it fails**

Run: `python3 tests/test_weekly_review_skill.py`

Expected: FAIL because neither generated adapter nor the README entry exists.

- [ ] **Step 3: Generate adapters and update README**

Run:

```bash
python3 scripts/sync-codex-skills.py
python3 scripts/sync-cursor-skills.py
```

Update README precisely:

1. Change the table-of-contents anchor text from `Skills 一览20个` to `Skills 一览21个`.
2. Change `## Skills 一览（20个）` to `## Skills 一览（21个）`.
3. Add this row in the 持仓管理类 table after `/thesis-tracker`:

```markdown
| [`/weekly-review`](skills/weekly-review.md) | 重点优先周检 | 只读联网分诊：重点标的全查、台账只查到期/触发项，输出 P0/P1/P2 待办 |
```

4. Add `/weekly-review` to the relevant quick-start command block and the workflow-selection table, described as a weekly to-do-list check rather than a decision or research replacement.

- [ ] **Step 4: Run compatibility and contract checks**

Run:

```bash
python3 tests/test_weekly_review_skill.py
python3 scripts/sync-codex-skills.py --check
python3 scripts/sync-cursor-skills.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all contract and existing tests pass; both generator checks report no stale artifacts.

- [ ] **Step 5: Review generated changes and commit**

Run:

```bash
git diff --check
git status --short
```

Verify generated files are limited to the two `weekly-review/SKILL.md` paths, README changes only expose the documented entry point, and no report files changed. Then commit:

```bash
git add README.md codex-skills/weekly-review/SKILL.md cursor-skills/weekly-review/SKILL.md tests/test_weekly_review_skill.py
git commit -m "docs: expose weekly review skill"
```

## Plan Self-Review

### Spec coverage

- Default focus-board and selective ledger scope: Task 1, workflow sections 2–3.
- Live-data evidence hierarchy and cross-check discipline: Task 1, workflow evidence rules.
- Read-only operation and no automatic investment decision: Task 1, introduction and boundary rules.
- P0/P1/P2 output, fixed sections, and workflow routing: Task 1, classification and output sections.
- Completeness checks: Task 1, completeness section.
- Codex/Cursor compatibility and discoverability: Task 2.

### Placeholder and consistency review

The plan has no deferred implementation markers. Paths, script names, test class/method names, expected failure states, generated artifact paths, and required literal strings are defined in the task steps. Task 2 consumes the canonical source and test fixture created in Task 1; no undefined implementation interface is referenced.
