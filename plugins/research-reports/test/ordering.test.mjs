/**
 * Unit tests for the panel's ordering rules: pinning, manual order and the drag
 * bookkeeping behind them.
 *
 * These call the pure helpers the browser bundle exposes for testing. Nothing is
 * rendered and no DOM is involved: the assertions are about the name lists the
 * Client sends to the Host and reads back.
 */
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = await readFile(path.join(here, '../client.js'), 'utf8')

/**
 * The browser bundle is `window.__ModuleLoader__.load({id, factory})`. Loading it
 * in Node only needs that hook plus the single module the factory imports.
 */
function internals() {
  const captured = {}
  const fakeWindow = { __ModuleLoader__: { load(definition) { Object.assign(captured, definition) } } }
  new Function('window', source)(fakeWindow)
  const plugin = captured.factory(() => ({ createElement: () => null, Fragment: 'fragment' }))
  assert.ok(plugin && plugin.__internals, 'bundle exposes ordering helpers')
  return plugin.__internals
}

const {
  orderBucket, bucketLists, sectionsOf,
  moveWithin, moveAcross, moveToListEdge, togglePinLists,
} = internals()

function group(name, bucket = '公司', latest = '2026-01-01') {
  return {
    name,
    bucket,
    ticker: '',
    rows: [{
      title: `${name} 报告`,
      path: `reports/${name}/${name}-research-20260101.md`,
      date: latest,
      dateSource: '文件名',
      type: '研究',
      draft: false,
    }],
    hidden: 0,
    latest,
    approxLatest: '',
  }
}

const companies = [group('腾讯', '公司', '2026-02-01'), group('茅台', '公司', '2026-01-20'), group('德明利', '公司', '2026-01-10')]

test('no saved preference keeps the incoming order', () => {
  const ordered = orderBucket(companies, undefined)
  assert.deepEqual(ordered.map(item => item.name), ['腾讯', '茅台', '德明利'])
  assert.deepEqual(ordered.map(item => item.pinned), [false, false, false])
})

test('pinned names float to the top in pin order', () => {
  const ordered = orderBucket(companies, { pins: ['德明利', '腾讯'], order: [] })
  assert.deepEqual(ordered.map(item => item.name), ['德明利', '腾讯', '茅台'])
  assert.deepEqual(ordered.map(item => item.pinned), [true, true, false])
})

test('manual order wins for unpinned names, unknown entries fall to the end', () => {
  const ordered = orderBucket(companies, { pins: [], order: ['德明利', '不存在的标的', '茅台'] })
  assert.deepEqual(ordered.map(item => item.name), ['德明利', '茅台', '腾讯'])
})

test('a saved name that no longer exists is ignored', () => {
  const ordered = orderBucket(companies, { pins: ['已删除'], order: ['已删除'] })
  assert.deepEqual(ordered.map(item => item.name), ['腾讯', '茅台', '德明利'])
})

test('bucketLists splits one bucket at the pin boundary', () => {
  const lists = bucketLists('公司', companies, { buckets: { 公司: { pins: ['茅台'], order: ['德明利'] } } })
  assert.deepEqual(lists.pinned, ['茅台'])
  assert.deepEqual(lists.rest, ['德明利', '腾讯'])
})

test('bucketLists ignores groups of other buckets', () => {
  const mixed = companies.concat([group('综合与横评', '专题', '2026-03-01')])
  const lists = bucketLists('公司', mixed, { buckets: {} })
  assert.deepEqual(lists.rest, ['腾讯', '茅台', '德明利'])
})

test('moveWithin reorders both directions and keeps the list length', () => {
  const list = ['A', 'B', 'C']
  assert.deepEqual(moveWithin(list, 'A', 'C', true), ['B', 'C', 'A'])
  assert.deepEqual(moveWithin(list, 'C', 'A', false), ['C', 'A', 'B'])
  assert.deepEqual(moveWithin(list, 'B', 'A', true), ['A', 'B', 'C'])
  assert.deepEqual(moveWithin(list, 'A', 'B', false), list)
  assert.deepEqual(list, ['A', 'B', 'C'], 'input list must not be mutated')
})

test('moveAcross pins a name by inserting it in the pin list', () => {
  const moved = moveAcross(['B', 'C'], ['A'], 'C', 'A', false)
  assert.deepEqual(moved.source, ['B'])
  assert.deepEqual(moved.target, ['C', 'A'])
})

test('moveAcross unpins a name by inserting it among the rest', () => {
  const moved = moveAcross(['A', 'B'], ['C', 'D'], 'A', 'C', true)
  assert.deepEqual(moved.source, ['B'])
  assert.deepEqual(moved.target, ['C', 'A', 'D'])
})

test('moveAcross appends when the drop target left the zone', () => {
  const moved = moveAcross(['A'], ['B', 'C'], 'B', '已离开', false)
  assert.deepEqual(moved.source, ['A'])
  assert.deepEqual(moved.target, ['C', 'B'])
})

test('pinning prepends and leaves the rest of the category alone', () => {
  // No manual order yet: the rest list stays empty, so dates keep floating.
  assert.deepEqual(togglePinLists([], [], '腾讯', false), { pinned: ['腾讯'], rest: [] })
  assert.deepEqual(togglePinLists(['腾讯'], [], '茅台', false), { pinned: ['茅台', '腾讯'], rest: [] })
  // Pinning a 标的 that a manual order mentioned removes it from that order.
  assert.deepEqual(togglePinLists([], ['茅台', '德明利'], '德明利', false), {
    pinned: ['德明利'],
    rest: ['茅台'],
  })
})

test('unpinning returns to the date order, or to the front of a manual one', () => {
  assert.deepEqual(togglePinLists(['腾讯'], [], '腾讯', true), { pinned: [], rest: [] })
  assert.deepEqual(togglePinLists(['腾讯', '茅台'], ['德明利'], '茅台', true), {
    pinned: ['腾讯'],
    rest: ['茅台', '德明利'],
  })
})

test('moveToListEdge sends a name to either end of its own zone', () => {
  const list = ['A', 'B', 'C', 'D']
  assert.deepEqual(moveToListEdge(list, 'C', 'first'), ['C', 'A', 'B', 'D'])
  assert.deepEqual(moveToListEdge(list, 'B', 'last'), ['A', 'C', 'D', 'B'])
  assert.deepEqual(list, ['A', 'B', 'C', 'D'], 'input list must not be mutated')
})

test('moveToListEdge is a no-op at the edge and for unknown names', () => {
  assert.deepEqual(moveToListEdge(['A', 'B'], 'A', 'first'), ['A', 'B'])
  assert.deepEqual(moveToListEdge(['A', 'B'], 'B', 'last'), ['A', 'B'])
  assert.deepEqual(moveToListEdge(['A', 'B'], '已删除', 'first'), ['A', 'B'])
})

test('the right-click move never changes the pin state', () => {
  // Unpinned zone: the pins stay exactly as they were, only the order changes.
  const lists = bucketLists('公司', companies, { buckets: { 公司: { pins: ['茅台'], order: [] } } })
  assert.deepEqual(lists.pinned, ['茅台'])
  const rest = moveToListEdge(lists.rest, '德明利', 'first')
  assert.deepEqual(rest, ['德明利', '腾讯'])
  assert.deepEqual(lists.pinned, ['茅台'], 'pins are untouched by a move')
})

test('a drop sequence survives pin, unpin and reorder round trips', () => {
  let lists = bucketLists('公司', companies, { buckets: {} })
  assert.deepEqual(lists, { pinned: [], rest: ['腾讯', '茅台', '德明利'] })

  // Drag 德明利 into the pin zone (the zone is empty, so it becomes the only pin).
  let moved = moveAcross(lists.rest, lists.pinned, '德明利', '', false)
  lists = { pinned: moved.target, rest: moved.source }
  assert.deepEqual(lists, { pinned: ['德明利'], rest: ['腾讯', '茅台'] })

  // Drag 茅台 in front of 德明利.
  moved = moveAcross(lists.rest, lists.pinned, '茅台', '德明利', false)
  lists = { pinned: moved.target, rest: moved.source }
  assert.deepEqual(lists, { pinned: ['茅台', '德明利'], rest: ['腾讯'] })

  // Drag 德明利 back out, dropping it after 腾讯.
  moved = moveAcross(lists.pinned, lists.rest, '德明利', '腾讯', true)
  lists = { pinned: moved.source, rest: moved.target }
  assert.deepEqual(lists, { pinned: ['茅台'], rest: ['腾讯', '德明利'] })

  // Reorder inside the remaining pins: nothing to do, but it must stay stable.
  assert.deepEqual(moveWithin(lists.pinned, '茅台', '茅台', true), ['茅台'])
})

test('sections follow the bucket order and mark pinned groups', () => {
  const mixed = [
    group('综合与横评', '专题', '2026-03-01'),
    group('腾讯', '公司', '2026-02-01'),
    group('茅台', '公司', '2026-01-20'),
  ]
  const sections = sectionsOf(mixed, '', { buckets: { 公司: { pins: ['茅台'], order: [] } } })
  assert.deepEqual(sections.map(section => section.bucket), ['公司', '专题'])
  assert.deepEqual(sections[0].groups.map(item => item.name), ['茅台', '腾讯'])
  assert.deepEqual(sections[0].groups.map(item => item.pinned), [true, false])
})

test('search narrows rows, not the saved order', () => {
  const mixed = [
    { ...group('腾讯', '公司', '2026-02-01'), rows: [{ title: '腾讯-research', path: 'reports/腾讯/a.md', date: '2026-02-01', dateSource: '文件名', type: '研究', draft: false }] },
    { ...group('茅台', '公司', '2026-01-20'), rows: [{ title: '茅台-research', path: 'reports/茅台/b.md', date: '2026-01-20', dateSource: '文件名', type: '研究', draft: false }] },
  ]
  const sections = sectionsOf(mixed, '茅台', { buckets: { 公司: { pins: ['腾讯'], order: [] } } })
  assert.deepEqual(sections[0].groups.map(item => item.name), ['茅台'])
  assert.deepEqual(sections[0].groups[0].shown.map(row => row.path), ['reports/茅台/b.md'])
})

test('a bucket holding only hidden drafts still shows its empty row', () => {
  const draftOnly = [{
    ...group('空标的', '公司', '2026-01-01'),
    rows: [],
    hidden: 2,
  }]
  const [section] = sectionsOf(draftOnly, '', { buckets: {} })
  assert.equal(section.bucket, '公司')
  assert.equal(section.groups.length, 1)
  assert.equal(section.groups[0].shown.length, 0)
  assert.equal(section.groups[0].hidden, 2)
})
