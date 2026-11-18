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

import { fileFor, normalizeViewState, safeTarget } from '../index.js'

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
