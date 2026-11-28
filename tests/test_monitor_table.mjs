import test from "node:test";
import assert from "node:assert/strict";
import { compareResearchDates, matchesMonitorFilters } from "../scripts/pages/monitor-table.mjs";

const rows = [
  { index: 0, date: "2026-08-25", market: "H", text: "腾讯 hk00700 h" },
  { index: 1, date: "2026-11-27", market: "US", text: "alphabet googl us" },
  { index: 2, date: "2026-11-27", market: "TW", text: "winbond 2344.tw tw" },
  { index: 3, date: "", market: "H", text: "无日期港股 h" },
  { index: 4, date: "2026-09-01", market: "UK", text: "chemring chg.l uk" },
  { index: 5, date: "", market: "US", text: "无日期美股 us" },
];
const order = (sort, input = rows) => [...input].sort((a, b) => compareResearchDates(a, b, sort)).map((row) => row.index);

test("newest first keeps equal dates stable and missing dates last", () => {
  assert.deepEqual(order("newest"), [1, 2, 4, 0, 3, 5]);
});

test("oldest first also keeps missing dates last", () => {
  assert.deepEqual(order("oldest"), [0, 4, 1, 2, 3, 5]);
});

test("default restores original priority order after a date sort", () => {
  const sorted = [...rows].sort((a, b) => compareResearchDates(a, b, "newest"));
  assert.deepEqual(order("default", sorted), [0, 1, 2, 3, 4, 5]);
});

test("multiple markets intersect with every search term", () => {
  const selected = new Set(["H", "US"]);
  assert.deepEqual(rows.filter((row) => matchesMonitorFilters(row, selected, ["无日期"])).map((row) => row.index), [3, 5]);
  assert.deepEqual(rows.filter((row) => matchesMonitorFilters(row, selected, ["alphabet", "googl"])).map((row) => row.index), [1]);
  assert.equal(matchesMonitorFilters(rows[1], selected, ["alphabet", "missing"]), false);
});

test("market selection uses exact values and an empty selection shows no rows", () => {
  assert.equal(matchesMonitorFilters(rows[4], new Set(["H"]), []), false);
  assert.deepEqual(rows.filter((row) => matchesMonitorFilters(row, new Set(), [])), []);
});

test("selecting all markets and clearing search restores every row", () => {
  const selected = new Set(rows.map((row) => row.market));
  assert.deepEqual(rows.filter((row) => matchesMonitorFilters(row, selected, [])), rows);
});
