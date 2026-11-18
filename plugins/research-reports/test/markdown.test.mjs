/**
 * Unit tests for the package's Markdown parser.
 *
 * The parser is the Host half's only non-trivial transformation: it turns a
 * report into the block tree the Client renders. These tests assert on that tree
 * directly (no rendering, no DOM), including a scan of the real `reports/` tree
 * when this package is checked out beside it.
 */
import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

import {
  MAX_INPUT_CHARS,
  findHeading,
  normalizePath,
  parseMarkdown,
  resolveTarget,
} from '../markdown.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const reportsDir = path.resolve(here, '../../../reports')

function blocks(source, docPath = 'reports/测试/测试-research-20260101.md') {
  return parseMarkdown(source, { docPath }).blocks
}

function kinds(tree) {
  return tree.map(block => block.t)
}

test('headings, paragraphs and rules', () => {
  const tree = blocks('# 标题\n\n正文一段。\n\n## 二级\n\n---\n\n### 三级 *斜体*\n')
  assert.deepEqual(kinds(tree), ['h', 'p', 'h', 'hr', 'h'])
  assert.equal(tree[0].level, 1)
  assert.equal(tree[2].level, 2)
  assert.equal(tree[4].level, 3)
  assert.deepEqual(tree[4].c[0], { t: 'text', v: '三级 ' })
  assert.equal(tree[4].c[1].t, 'i')
})

test('setext heading becomes level 1 or 2', () => {
  const tree = blocks('标题一\n===\n\n标题二\n---\n')
  assert.deepEqual(tree.map(block => [block.t, block.level]), [['h', 1], ['h', 2]])
})

test('bold, italic, strike, inline code, escape and hard break', () => {
  const tree = blocks('**粗**、*斜*、~~删~~、`码`、\\*非斜\\*、行尾  \n下一行')
  const [first] = tree
  const tags = first.c.filter(node => node.t !== 'text').map(node => node.t)
  assert.deepEqual(tags, ['b', 'i', 'del', 'code', 'br'])
  assert.ok(first.c.some(node => node.t === 'text' && node.v.includes('*非斜*')))
})

test('gfm table keeps alignment and cell inline markup', () => {
  const tree = blocks('| 左 | 中 | 右 |\n|:---|:---:|---:|\n| a | **b** | `c` |\n')
  assert.equal(tree.length, 1)
  const [table] = tree
  assert.equal(table.t, 'table')
  assert.deepEqual(table.align, ['left', 'center', 'right'])
  assert.equal(table.head.length, 3)
  assert.equal(table.rows.length, 1)
  assert.equal(table.rows[0][1][0].t, 'b')
  assert.equal(table.rows[0][2][0].t, 'code')
})

test('escaped pipe inside a table stays in one cell', () => {
  const [table] = blocks('| a | b |\n|---|---|\n| x \\| y | z |\n')
  assert.equal(table.rows[0].length, 2)
  assert.equal(table.rows[0][0][0].v, 'x | y')
})

test('task list items carry their checked state', () => {
  const [list] = blocks('- [x] 完成\n- [ ] 未完成\n- 普通\n')
  assert.equal(list.t, 'ul')
  assert.deepEqual(list.items.map(item => item.checked), [true, false, undefined])
})

test('nested ordered list stays nested', () => {
  const [list] = blocks('1. 第一\n2. 第二\n   1. 子项\n3. 第三\n')
  assert.equal(list.t, 'ol')
  assert.equal(list.items.length, 3)
  assert.equal(list.items[1].blocks[1].t, 'ol')
  assert.equal(list.items[1].blocks[1].items.length, 1)
})

test('fenced code keeps markdown-looking text literal', () => {
  const tree = blocks('```text\n# 不是标题\n| 不是表格 |\n```\n\n段落\n')
  assert.equal(tree[0].t, 'code')
  assert.equal(tree[0].lang, 'text')
  assert.equal(tree[0].text, '# 不是标题\n| 不是表格 |')
  assert.equal(tree[1].t, 'p')
})

test('blockquote carries its own blocks', () => {
  const [quote] = blocks('> 引用\n>\n> - 列表项\n')
  assert.equal(quote.t, 'quote')
  assert.deepEqual(kinds(quote.blocks), ['p', 'ul'])
})

test('raw html is preserved inertly', () => {
  const tree = blocks('<div class="x">\n<b>粗</b>\n</div>\n')
  assert.equal(tree[0].t, 'html')
  assert.ok(tree[0].text.includes('<b>'))
})

test('links resolve to the three destinations the reader supports', () => {
  const docPath = 'reports/腾讯/腾讯-research-20260408.md'
  assert.deepEqual(resolveTarget('https://example.com/a', { docPath }), {
    kind: 'external',
    href: 'https://example.com/a',
  })
  assert.deepEqual(resolveTarget('腾讯-research-20260101.md', { docPath }), {
    kind: 'doc',
    path: 'reports/腾讯/腾讯-research-20260101.md',
  })
  assert.deepEqual(resolveTarget('../快手/快手-research-20260101.md', { docPath }), {
    kind: 'doc',
    path: 'reports/快手/快手-research-20260101.md',
  })
  assert.deepEqual(resolveTarget('assets/chart-20260101.png', { docPath }), {
    kind: 'asset',
    path: 'reports/腾讯/assets/chart-20260101.png',
  })
  assert.deepEqual(resolveTarget('%2E%2E/%E5%BF%AB%E6%89%8B/x.md', { docPath }), {
    kind: 'doc',
    path: 'reports/快手/x.md',
  })
})

test('unsafe or unknown targets degrade instead of leaking a path', () => {
  const docPath = 'reports/腾讯/腾讯-research-20260408.md'
  assert.equal(resolveTarget('../../../../etc/passwd.md', { docPath }), null)
  assert.equal(resolveTarget('javascript:alert(1)', { docPath }), null)
  assert.equal(resolveTarget('//evil.example/x.md', { docPath }), null)
  assert.equal(resolveTarget('#section', { docPath }), null)
  assert.deepEqual(resolveTarget('mailto:a@b.c', { docPath }), { kind: 'external', href: 'mailto:a@b.c' })
  const tree = blocks('见[危险链接](../../../../etc/passwd.md)与[锚点](#x)与![图](../../x.png)\n', docPath)
  const types = tree[0].c.map(node => node.t)
  assert.ok(!types.includes('link'), 'unsafe links must not become anchors')
  assert.ok(!types.includes('img'), 'escaping images must not become img')
})

test('inline image inside a paragraph becomes an img node', () => {
  const [para] = blocks('![图注](assets/a.png)\n')
  assert.equal(para.c[0].t, 'img')
  assert.equal(para.c[0].src, 'reports/测试/assets/a.png')
  assert.equal(para.c[0].alt, '图注')
})

test('normalizePath collapses dot segments without touching disk', () => {
  assert.equal(normalizePath('reports/a/./b/../c.md'), 'reports/a/c.md')
  assert.equal(normalizePath('../x.md'), '')
  assert.equal(normalizePath('reports//a.md'), 'reports/a.md')
})

test('oversized input is cut and reported', () => {
  const source = `${'# 标题\n\n正文\n\n'.repeat(Math.ceil(MAX_INPUT_CHARS / 8))}`
  const result = parseMarkdown(source, { docPath: 'reports/x/y.md' })
  assert.equal(result.cut, true)
  assert.ok(result.blocks.length > 0)
})

test('findHeading prefers the first level-1 heading', () => {
  assert.equal(findHeading(blocks('## 二级\n\n# 一级\n')), '一级')
  assert.equal(findHeading(blocks('## 只有二级\n')), '只有二级')
  assert.equal(findHeading(blocks('正文\n')), '')
})

test('link destinations keep spaces, drop a quoted title and accept <…>', () => {
  const docPath = 'reports/跟踪/跟踪-20260101.md'
  const titled = blocks('[a](https://ok.example/p "提示文字")\n', docPath)
  assert.equal(titled[0].c[0].t, 'link')
  assert.equal(titled[0].c[0].href, 'https://ok.example/p')

  const spaced = blocks('[b](Novo Nordisk/Novo Nordisk-research-20260908.md)\n', docPath)
  assert.equal(spaced[0].c[0].t, 'link')
  assert.equal(spaced[0].c[0].doc, 'reports/跟踪/Novo Nordisk/Novo Nordisk-research-20260908.md')

  const angled = blocks('[c](<Planet Labs/Planet Labs-research-20260908.md>)\n', docPath)
  assert.equal(angled[0].c[0].t, 'link')
  assert.equal(angled[0].c[0].doc, 'reports/跟踪/Planet Labs/Planet Labs-research-20260908.md')
})

test('pathological nesting stays linear and never throws', () => {
  const inputs = [
    `${'>'.repeat(12000)}x`,
    `${'- '.repeat(4000)}x`,
    `${'['.repeat(20000)}x${']'.repeat(20000)}(y)`,
    `${'*a '.repeat(24000)}`,
    `${'_'.repeat(200000)}x`,
    `${'`'.repeat(40000)}|x`,
    `${'a b\n'.repeat(60000)}`,
    `${'a  \n'.repeat(30000)}`,
  ]
  for (const source of inputs) {
    const started = Date.now()
    const result = parseMarkdown(source, { docPath: 'reports/x/y.md' })
    assert.ok(Array.isArray(result.blocks), 'blocks must be an array')
    assert.ok(Date.now() - started < 2000, 'pathological input must parse in bounded time')
  }
})

test('a truncated document keeps its containers instead of dropping them', () => {
  const longList = parseMarkdown(`${'- item\n'.repeat(6001)}`, { docPath: 'reports/x/y.md' })
  assert.equal(longList.truncated, true)
  const list = longList.blocks.find(block => block.t === 'ul')
  assert.ok(list, 'the list container must survive the block cap')
  assert.ok(list.items.length > 0, 'the list must keep the beginning of its items')

  const longQuote = parseMarkdown(`${'> line\n'.repeat(6001)}`, { docPath: 'reports/x/y.md' })
  const quote = longQuote.blocks.find(block => block.t === 'quote')
  assert.ok(quote, 'the quote container must survive the block cap')
})

test('table rows and inline nodes are capped, output stays proportional', () => {
  const table = parseMarkdown(`x | y\n--- | ---\n${'a | b\n'.repeat(60000)}`, { docPath: 'reports/x/y.md' })
  const tableBlock = table.blocks.find(block => block.t === 'table')
  assert.ok(tableBlock)
  assert.ok(tableBlock.rows.length <= 20000, 'table rows are capped by the cell budget')
  assert.ok(JSON.stringify(table.blocks).length < 2 * 1024 * 1024)

  const bold = parseMarkdown(`${'**a** '.repeat(80000)}`, { docPath: 'reports/x/y.md' })
  assert.ok(JSON.stringify(bold.blocks).length < 3 * 1024 * 1024)
})

test('every report in the checkout parses into well-formed blocks', async () => {
  let files
  try {
    files = await collect(reportsDir, '')
  } catch {
    return // No checkout beside this package: nothing to scan.
  }
  assert.ok(files.length > 100, 'expected a populated reports tree')
  const allowed = new Set(['h', 'p', 'ul', 'ol', 'quote', 'table', 'code', 'hr', 'img', 'html'])
  let blockCount = 0
  for (const rel of files) {
    const text = await readFile(path.join(reportsDir, rel), 'utf8')
    const tree = parseMarkdown(text, { docPath: `reports/${rel}` }).blocks
    blockCount += tree.length
    for (const block of tree) {
      assert.ok(allowed.has(block.t), `${rel}: unexpected block type ${block.t}`)
      if (block.t === 'h' || block.t === 'p') assert.ok(Array.isArray(block.c), `${rel}: ${block.t} without inline content`)
      if (block.t === 'table') assert.ok(block.head.length > 0 && Array.isArray(block.rows), `${rel}: malformed table`)
      if (block.t === 'ul' || block.t === 'ol') assert.ok(Array.isArray(block.items), `${rel}: list without items`)
    }
  }
  assert.ok(blockCount > files.length, 'expected at least one block per report')
})

async function collect(dir, prefix) {
  const found = []
  const entries = await readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === '_index') continue
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name
    if (entry.isDirectory()) {
      found.push(...await collect(path.join(dir, entry.name), rel))
    } else if (entry.name.endsWith('.md') && entry.name !== 'README.md') {
      found.push(rel)
    }
  }
  return found
}
