/**
 * Unit tests for the Host half's request-target resolution.
 *
 * These exercise `fileFor` (the lexical mapping) and `safeTarget` (the mapping
 * plus a real-path containment check) against a throwaway tree in the OS temp
 * directory, so no file inside the repository's `reports/` is touched.
 */
import assert from 'node:assert/strict'
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { after, before, test } from 'node:test'

import {
  buildMonitorPayload, fileFor, monitorCondition, monitorGap, monitorLinkToPath,
  normalizeViewState, safeTarget,
} from '../index.js'

let root
let reportsDir
let outside

before(async () => {
  root = await mkdtemp(path.join(tmpdir(), 'rr-paths-'))
  reportsDir = path.join(root, 'reports')
  outside = path.join(root, 'outside')
  await mkdir(path.join(reportsDir, '腾讯'), { recursive: true })
  await mkdir(path.join(reportsDir, '腾讯', 'assets'), { recursive: true })
  await mkdir(outside, { recursive: true })
  await writeFile(path.join(reportsDir, '腾讯', '腾讯-research-20260101.md'), '# 腾讯\n')
  await writeFile(path.join(reportsDir, '腾讯', 'assets', 'chart.png'), 'png')
  await writeFile(path.join(outside, 'secret.md'), '# secret\n')
  await writeFile(path.join(outside, 'secret.png'), 'png')
  // A symlink placed inside the tree must not become a read primitive.
  await symlink(path.join(outside, 'secret.md'), path.join(reportsDir, '腾讯', 'leak.md'))
  await symlink(path.join(outside, 'secret.png'), path.join(reportsDir, '腾讯', 'leak.png'))
})

after(async () => {
  if (root) await rm(root, { recursive: true, force: true })
})

test('fileFor maps panel paths onto the reports root', () => {
  const target = fileFor(reportsDir, 'reports/腾讯/腾讯-research-20260101.md')
  assert.equal(target.rel, '腾讯/腾讯-research-20260101.md')
  assert.equal(target.path, 'reports/腾讯/腾讯-research-20260101.md')
  assert.equal(target.abs, path.join(reportsDir, '腾讯', '腾讯-research-20260101.md'))
  assert.ok(fileFor(reportsDir, '腾讯/腾讯-research-20260101.md'), 'a bare relative path is accepted too')
})

test('fileFor rejects every traversal shape', () => {
  const payloads = [
    '../../../../etc/passwd.md',
    'reports/../../etc/passwd.md',
    'reports/../../../etc/passwd.md',
    '..%2f..%2fetc/passwd.md',
    '%2e%2e/%2e%2e/etc/passwd.md',
    '/etc/passwd.md',
    '//etc/passwd.md',
    '..\\..\\etc\\passwd.md',
    'reports/腾讯/../../outside/secret.md',
    'reports/腾讯/\u0000leak.md',
    '',
    'reports',
    '   ',
  ]
  for (const payload of payloads) {
    const target = fileFor(reportsDir, payload)
    if (!target) continue
    assert.ok(
      target.abs === reportsDir || target.abs.startsWith(reportsDir + path.sep),
      `escaped the reports root: ${payload} -> ${target.abs}`,
    )
  }
})

test('safeTarget accepts real reports and images', async () => {
  const report = await safeTarget(reportsDir, 'reports/腾讯/腾讯-research-20260101.md')
  assert.ok(report, 'a real report resolves')
  const image = await safeTarget(reportsDir, 'reports/腾讯/assets/chart.png')
  assert.ok(image, 'a real image resolves')
})

test('safeTarget refuses a symlink that leaves the tree', async () => {
  assert.equal(await safeTarget(reportsDir, 'reports/腾讯/leak.md'), null)
  assert.equal(await safeTarget(reportsDir, 'reports/腾讯/leak.png'), null)
})

test('safeTarget refuses missing files and traversal', async () => {
  assert.equal(await safeTarget(reportsDir, 'reports/腾讯/missing.md'), null)
  assert.equal(await safeTarget(reportsDir, 'reports/../../etc/passwd.md'), null)
  assert.equal(await safeTarget(reportsDir, ''), null)
})

test('normalizeViewState keeps only the documented shape', () => {
  const state = normalizeViewState({
    version: 99,
    buckets: {
      公司: { pins: ['腾讯', '腾讯', 7, ''], order: ['茅台', '腾讯'] },
      专题: { pins: 'nope', order: null },
      __proto__: { pins: ['x'] },
      constructor: { pins: ['x'] },
      '  ': { pins: ['x'] },
    },
  })
  assert.deepEqual(state, { version: 1, buckets: { 公司: { pins: ['腾讯'], order: ['茅台'] } } })
  assert.equal({}.pins, undefined, 'Object.prototype must stay clean')
  assert.deepEqual(normalizeViewState(null), { version: 1, buckets: {} })
  assert.deepEqual(normalizeViewState('nope'), { version: 1, buckets: {} })
})

test('monitor zone wording matches the monitor report', () => {
  assert.equal(monitorCondition({ low: 65, high: 90, direction: 'range' }), '[65.00, 90.00]')
  assert.equal(monitorCondition({ high: 160, low: null, direction: 'below' }), '≤ 160.00')
  assert.equal(monitorCondition({ low: 22.2, direction: 'above' }), '≥ 22.20')
  assert.equal(monitorCondition({ low: 22.2 }), '≥ 22.20')
  assert.equal(monitorCondition({ high: null, low: null }), '')
})

test('monitor distance wording matches the monitor report', () => {
  assert.equal(monitorGap({ status: 'TRIGGERED', metadata: { price: 77.39, low: 65, high: 90 } }), '区间内')
  assert.equal(monitorGap({ status: 'TRIGGERED', metadata: { price: 38.59, low: 45, high: 55 } }), '低于下界 14.2%')
  assert.equal(monitorGap({ status: 'NEAR', metadata: { price: 166.67, high: 160, direction: 'below' } }), '4.2%')
  assert.equal(monitorGap({ status: 'FAR', metadata: { price: 120, low: 90, high: 110 } }), '9.1%')
  assert.equal(monitorGap({ status: 'WARN', metadata: { price: 200, low: 150, direction: 'above' } }), '已越警戒线')
  assert.equal(monitorGap({ status: 'FAR', metadata: {} }), '')
})

test('monitor research links resolve into the reports tree', () => {
  assert.equal(
    monitorLinkToPath('../%E6%8B%BC%E5%A4%9A%E5%A4%9A/%E6%8B%BC%E5%A4%9A%E5%A4%9A-research-20261031.md'),
    'reports/拼多多/拼多多-research-20261031.md',
  )
  assert.equal(monitorLinkToPath('../Qualcomm/Qualcomm-earnings-FY2026Q3.md'), 'reports/Qualcomm/Qualcomm-earnings-FY2026Q3.md')
  assert.equal(monitorLinkToPath('reports/x/y.md'), 'reports/x/y.md')
  assert.equal(monitorLinkToPath('https://example.com/x.md'), '')
  assert.equal(monitorLinkToPath('../x/y.txt'), '')
  assert.equal(monitorLinkToPath('../../etc/passwd.md'), '')
  assert.equal(monitorLinkToPath(''), '')
})

test('the monitor payload keeps zones and events, and counts them', () => {
  const raw = {
    schema: 1,
    date: '2026-11-18',
    timezone: 'Asia/Shanghai',
    status: 'DEGRADED',
    summary: 'P0 4 · P1 13',
    source_health: [{ source: 'quotes', status: 'OK', safe_message: null }],
    items: [
      {
        section: 'price', priority: 'P0', name: 'PDD Holdings', target_id: '拼多多', status: 'TRIGGERED',
        title: '65—90美元条件式研究分批带：TRIGGERED', why_now: '现价 77.39 ≤ 区间上界 90.00',
        metadata: { price: 77.39, market: 'US', zone_label: '65—90美元', low: 65, high: 90, direction: 'range', research_link: '../%E6%8B%BC%E5%A4%9A%E5%A4%9A/x.md', research_date: '2026-10-31' },
      },
      {
        section: 'price', priority: 'P1', name: 'Qualcomm', target_id: 'Qualcomm', status: 'NEAR',
        title: '理想买入带：NEAR', why_now: '现价 166.67，距触发线 160.00 5% 内',
        metadata: { price: 166.67, market: 'US', zone_label: '理想买入带', low: null, high: 160, direction: 'below', research_link: '../Qualcomm/y.md' },
      },
      {
        section: 'price', priority: 'P2', name: 'Far Co', target_id: 'Far', status: 'FAR',
        metadata: { price: 300, low: 100, high: 200, direction: 'range' },
      },
      {
        section: 'price', priority: 'P0', name: 'Warning Co', target_id: 'Warn', status: 'WARN',
        metadata: { price: 500, low: 400, direction: 'above' },
      },
      {
        section: 'disclosures', priority: 'P0', name: '腾讯控股', target_id: '腾讯', status: 'TODAY',
        title: '2026Q3正式业绩：今天到期', metadata: { date: '2026-11-18', research_link: '../腾讯/z.md' },
        source_urls: ['https://example.com/a.pdf'],
      },
      {
        section: 'other', priority: 'P1', name: 'Accenture', target_id: 'Accenture', status: 'DONE',
        title: '已完成', metadata: { date: '2026-11-13' },
      },
    ],
  }
  const payload = buildMonitorPayload(raw, { monitorDir: 'daily-monitor', reportPath: 'reports/daily-monitor/daily-monitor-latest.md' })
  assert.equal(payload.ok, true)
  assert.equal(payload.date, '2026-11-18')
  assert.equal(payload.reportPath, 'reports/daily-monitor/daily-monitor-latest.md')
  assert.deepEqual(payload.sources, [{ source: 'quotes', status: 'OK' }])
  assert.equal(payload.counts.triggered, 1)
  assert.equal(payload.counts.near, 1)
  assert.equal(payload.counts.far, 1)
  assert.equal(payload.counts.events, 1, 'only unfinished events are counted')
  assert.deepEqual(payload.price.map(row => row.status), ['TRIGGERED', 'NEAR', 'FAR'], 'warnings are left out and statuses rank')
  assert.equal(payload.price[0].researchPath, 'reports/拼多多/x.md')
  assert.equal(payload.price[0].condition, '[65.00, 90.00]')
  assert.equal(payload.price[1].gap, '4.2%')
  assert.equal(payload.events[0].status, 'TODAY')
  assert.equal(payload.events[0].url, 'https://example.com/a.pdf')
  assert.equal(payload.events[0].researchPath, 'reports/腾讯/z.md')
})

test('a monitor payload without items is reported as missing', () => {
  const payload = buildMonitorPayload(null, {})
  assert.equal(payload.ok, false)
  assert.deepEqual(payload.price, [])
  assert.deepEqual(payload.events, [])
  assert.equal(payload.counts.triggered, 0)
})
