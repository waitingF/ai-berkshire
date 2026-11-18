/**
 * Markdown → render-tree conversion for the research-report reader.
 *
 * The Host half parses a report once and publishes a JSON block tree; the Client
 * half turns that tree into React elements. Parsing here keeps the browser half
 * free of a Markdown engine (the Harness Client bundle has no Markdown module to
 * import) and makes the conversion unit-testable in Node.
 *
 * The tree is deliberately small and fully owned by this package:
 *   block  = {t:'h',level,c} | {t:'p',c} | {t:'ul'|'ol',items} | {t:'quote',blocks}
 *          | {t:'table',align,head,rows} | {t:'code',lang,text} | {t:'hr'}
 *          | {t:'img',src,alt} | {t:'html',text}
 *   inline = {t:'text',v} | {t:'code',v} | {t:'br'} | {t:'b'|'i'|'del'|'link',c,...}
 *
 * Nothing in the output is HTML: the Client only ever creates the elements it
 * names, so a report can never inject markup, script, or a foreign URL scheme.
 *
 * Every input here is a file on disk that nobody vets, so the work performed is
 * bounded independently of the input's shape: the byte cap, the block/inline/cell
 * budgets, the nesting depth and the per-scan window together keep a hostile or
 * merely machine-generated report from stalling the Host's event loop.
 */

/** Characters of Markdown considered per report; the tail is reported as cut. */
export const MAX_INPUT_CHARS = 400 * 1024
/** Hard ceiling on blocks, so one pathological file cannot flood the panel. */
export const MAX_BLOCKS = 6000
/** Inline nodes, table cells and nesting depth get their own ceilings. */
const MAX_INLINE_NODES = 40000
const MAX_CELLS = 20000
const MAX_DEPTH = 40
/** One inline scan may walk this far before it gives up on the closing marker. */
const MAX_SCAN = 4096
/** Total characters the inline scanners may walk for one report. */
const MAX_WORK = 6 * 1024 * 1024
/** Bracket nesting a link label may explore before it is read as plain text. */
const MAX_LABEL_DEPTH = 8

const IMAGE_EXT = new Set(['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif', '.bmp'])
const EXTERNAL_RE = /^(?:https?:\/\/|mailto:)/i
const AUTOLINK_RE = /^<(https?:\/\/[^\s>]+|mailto:[^\s>]+)>/
const BR_RE = /^<br\s*\/?>/i
const FENCE_RE = /^\s{0,3}(`{3,}|~{3,})\s*([^`\s]*)/
const HEADING_RE = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/
const HR_RE = /^\s{0,3}((?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$/
const QUOTE_RE = /^\s{0,3}>\s?/
const LIST_RE = /^(\s*)([-*+]|\d{1,9}[.)])(\s+)(.*)$/
const TASK_RE = /^\[([ xX])\]\s+(.*)$/
const SETEXT_RE = /^\s{0,3}(=+|-+)\s*$/
const HTML_BLOCK_RE = /^\s{0,3}<(?:div|details|summary|figure|figcaption|table|tbody|tr|td|p|center|span|a)\b/i

/** Punctuation an escape may neutralize, per CommonMark. */
const ESCAPABLE = '\\`*_{}[]()#+-.!|>~<"\''

function asText(value) {
  return value === undefined || value === null ? '' : String(value)
}

/** Split a table row into cell source strings, honouring escaped pipes and code spans. */
function splitRow(line) {
  const cells = []
  let current = ''
  let i = 0
  const text = line.trim().replace(/^\|/, '').replace(/\|$/, '')
  while (i < text.length) {
    const ch = text[i]
    if (ch === '\\' && text[i + 1] === '|') {
      current += '|'
      i += 2
      continue
    }
    if (ch === '`') {
      let run = 0
      while (text[i + run] === '`') run += 1
      const marker = '`'.repeat(run)
      const close = text.indexOf(marker, i + run)
      // No closing run of the same length: keep the backticks and move on past
      // the whole run, so a line of backticks cannot be rescanned quadratically.
      if (close < 0) {
        current += text.slice(i, i + run)
        i += run
        continue
      }
      current += text.slice(i, close + run)
      i = close + run
      continue
    }
    if (ch === '|') {
      cells.push(current.trim())
      current = ''
      i += 1
      continue
    }
    current += ch
    i += 1
  }
  cells.push(current.trim())
  return cells
}

function alignmentOf(cell) {
  const left = cell.startsWith(':')
  const right = cell.endsWith(':')
  if (left && right) return 'center'
  if (right) return 'right'
  if (left) return 'left'
  return null
}

/** Cheap check: the next line is a table delimiter row, so this one is a header. */
function isDelimiterRow(line) {
  if (line === undefined || !line.includes('-')) return false
  const trimmed = line.trim()
  return /^[|\s:-]+$/.test(trimmed) && trimmed.includes('-')
}

function isTableStart(lines, i) {
  const header = lines[i]
  if (header === undefined || !header.includes('|')) return false
  const next = lines[i + 1]
  if (next === undefined) return false
  if (!next.includes('|') && !/^\s*\|?\s*:?-{1,}:?\s*\|?\s*$/.test(next)) return false
  const sep = next.trim()
  if (!/^[|\s:-]+$/.test(sep)) return false
  if (!/-/.test(sep)) return false
  const headerCells = splitRow(header)
  const sepCells = splitRow(next)
  return headerCells.length === sepCells.length && sepCells.every(cell => /^:?-+:?$/.test(cell))
}

/** True when the line starts a block that interrupts a paragraph. */
function interruptsParagraph(line, lines, i) {
  if (FENCE_RE.test(line)) return true
  if (HEADING_RE.test(line)) return true
  if (HR_RE.test(line)) return true
  if (QUOTE_RE.test(line)) return true
  if (LIST_RE.test(line)) return true
  if (isTableStart(lines, i)) return true
  return false
}

/** A `---`/`===` line under a single-line paragraph turns it into a heading. */
function isSetextUnderline(line) {
  return SETEXT_RE.test(line) && line.trim().length >= 1
}

/**
 * Parse Markdown into the render tree.
 *
 * @param {string} source report text
 * @param {{ docPath?: string }} options docPath is the report path the links are
 *   resolved against, e.g. `reports/腾讯/腾讯-research-20260408.md`.
 * @returns {{ blocks: object[], truncated: boolean, cut: boolean }}
 */
export function parseMarkdown(source, options = {}) {
  const docPath = asText(options.docPath)
  const text = asText(source).replace(/\r\n?/g, '\n').replace(/\t/g, '    ')
  const cut = text.length > MAX_INPUT_CHARS
  const input = cut ? text.slice(0, MAX_INPUT_CHARS) : text
  const ctx = { docPath, blocks: 0, inline: 0, cells: 0, work: 0, spent: false }
  const blocks = parseBlocks(input.split('\n'), ctx, 0)
  return { blocks, truncated: ctx.spent || ctx.blocks >= MAX_BLOCKS, cut }
}

/** Headline of a report: first level-1 heading text, else the first heading. */
export function findHeading(blocks) {
  let first = ''
  for (const block of blocks) {
    if (block.t !== 'h') continue
    const text = inlineText(block.c)
    if (!first) first = text
    if (block.level === 1) return text
  }
  return first
}

function inlineText(nodes) {
  let out = ''
  for (const node of nodes || []) {
    if (node.t === 'text' || node.t === 'code') out += node.v
    else if (node.t === 'br') out += ' '
    else if (Array.isArray(node.c)) out += inlineText(node.c)
  }
  return out.trim()
}

/** Charge work to the report's budget; false once the budget is gone. */
function spend(ctx, amount) {
  ctx.work += amount
  if (ctx.work > MAX_WORK) {
    ctx.spent = true
    return false
  }
  return true
}

/** Reserve one block slot; false when the document is already full. */
function push(blocks, block, ctx) {
  if (ctx.blocks >= MAX_BLOCKS) {
    ctx.spent = true
    return false
  }
  ctx.blocks += 1
  blocks.push(block)
  return true
}

function parseBlocks(lines, ctx, depth) {
  const blocks = []
  if (depth > MAX_DEPTH) {
    // Pathological nesting: keep the text, stop expanding structure.
    push(blocks, { t: 'html', text: lines.join('\n') }, ctx)
    return blocks
  }
  let i = 0
  while (i < lines.length && ctx.blocks < MAX_BLOCKS) {
    const line = lines[i]
    if (!line.trim()) {
      i += 1
      continue
    }

    const fence = FENCE_RE.exec(line)
    if (fence) {
      const marker = fence[1]
      const lang = fence[2] || ''
      const body = []
      i += 1
      while (i < lines.length && !isFenceClose(lines[i], marker)) {
        body.push(lines[i])
        i += 1
      }
      if (i < lines.length) i += 1
      push(blocks, { t: 'code', lang: lang.toLowerCase(), text: body.join('\n') }, ctx)
      continue
    }

    const heading = HEADING_RE.exec(line)
    if (heading) {
      push(blocks, { t: 'h', level: heading[1].length, c: parseInline(heading[2], ctx, depth + 1) }, ctx)
      i += 1
      continue
    }

    if (HR_RE.test(line) && !line.includes('|')) {
      push(blocks, { t: 'hr' }, ctx)
      i += 1
      continue
    }

    if (QUOTE_RE.test(line)) {
      const body = []
      while (i < lines.length && (QUOTE_RE.test(lines[i]) || (lines[i].trim() && body.length && !interruptsParagraph(lines[i], lines, i)))) {
        body.push(lines[i].replace(QUOTE_RE, ''))
        i += 1
      }
      // Reserve the container before its children spend the block budget, so a
      // truncated quote shows its beginning instead of vanishing.
      const quote = { t: 'quote', blocks: [] }
      if (push(blocks, quote, ctx)) quote.blocks = parseBlocks(body, ctx, depth + 1)
      continue
    }

    if (isTableStart(lines, i)) {
      const head = splitRow(lines[i]).map(cell => parseInline(cell, ctx, depth + 1))
      const align = splitRow(lines[i + 1]).map(alignmentOf)
      const table = { t: 'table', align, head, rows: [] }
      const reserved = push(blocks, table, ctx)
      i += 2
      while (i < lines.length && lines[i].trim() && lines[i].includes('|') && !isDelimiterRow(lines[i + 1])) {
        if (!reserved || ctx.cells >= MAX_CELLS) {
          ctx.spent = true
          break
        }
        const cells = splitRow(lines[i])
        ctx.cells += cells.length
        table.rows.push(align.map((_, index) => parseInline(cells[index] === undefined ? '' : cells[index], ctx, depth + 1)))
        i += 1
      }
      continue
    }

    if (LIST_RE.test(line)) {
      const block = { t: 'ul', items: [] }
      const reserved = push(blocks, block, ctx)
      const next = parseList(lines, i, ctx, depth + 1, block, reserved)
      i = next
      continue
    }

    if (HTML_BLOCK_RE.test(line)) {
      // Raw HTML is preserved as inert text: the Client never injects markup.
      const body = []
      while (i < lines.length && lines[i].trim()) {
        body.push(lines[i])
        i += 1
      }
      push(blocks, { t: 'html', text: body.join('\n') }, ctx)
      continue
    }

    // Paragraph (possibly a one-line setext heading). Trailing spaces are kept
    // because two of them are this parser's hard-break marker.
    const body = [line.replace(/^\s+/, '')]
    i += 1
    if (i < lines.length && isSetextUnderline(lines[i]) && body.length === 1) {
      const level = lines[i].trim().startsWith('=') ? 1 : 2
      push(blocks, { t: 'h', level, c: parseInline(body[0], ctx, depth + 1) }, ctx)
      i += 1
      continue
    }
    while (i < lines.length && lines[i].trim() && !interruptsParagraph(lines[i], lines, i)) {
      body.push(lines[i].replace(/^\s+/, ''))
      i += 1
    }
    push(blocks, { t: 'p', c: parseInline(body.join('\n'), ctx, depth + 1) }, ctx)
  }
  return blocks
}

function isFenceClose(line, marker) {
  const trimmed = line.trim()
  if (!trimmed) return false
  if (trimmed[0] !== marker[0]) return false
  return trimmed.length >= marker.length && /^(`+|~+)$/.test(trimmed)
}

/**
 * Fill one list block that the caller already reserved.
 *
 * @returns {number} the index of the first line after the list
 */
function parseList(lines, start, ctx, depth, block, reserved) {
  const first = LIST_RE.exec(lines[start])
  const baseIndent = first[1].length
  const ordered = /\d/.test(first[2][0])
  const startNumber = ordered ? Number.parseInt(first[2], 10) : 1
  block.t = ordered ? 'ol' : 'ul'
  if (ordered && startNumber !== 1) block.start = startNumber
  const items = block.items
  let i = start
  while (i < lines.length) {
    const match = LIST_RE.exec(lines[i])
    if (!match || match[1].length !== baseIndent) break
    const markerOrdered = /\d/.test(match[2][0])
    if (markerOrdered !== ordered) break
    if (!reserved || ctx.blocks >= MAX_BLOCKS) {
      ctx.spent = true
      // Keep consuming the list so the caller does not re-read it as paragraphs.
      while (i < lines.length) {
        const nextMatch = LIST_RE.exec(lines[i])
        if (nextMatch ? nextMatch[1].length !== baseIndent : (lines[i].trim() && indentOf(lines[i]) <= baseIndent)) break
        i += 1
      }
      break
    }
    const contentIndent = baseIndent + match[1].length + match[2].length + match[3].length
    const itemLines = [match[4]]
    i += 1
    while (i < lines.length) {
      const line = lines[i]
      if (!line.trim()) {
        // A blank line continues the item unless the next line starts a new item.
        let lookahead = i + 1
        while (lookahead < lines.length && !lines[lookahead].trim()) lookahead += 1
        if (lookahead >= lines.length) {
          i = lookahead
          break
        }
        const nextMatch = LIST_RE.exec(lines[lookahead])
        if (nextMatch && nextMatch[1].length === baseIndent && /\d/.test(nextMatch[2][0]) === ordered) {
          i = lookahead
          break
        }
        if (indentOf(lines[lookahead]) <= baseIndent && !LIST_RE.test(lines[lookahead])) {
          i = lookahead
          break
        }
        itemLines.push('')
        i += 1
        continue
      }
      const nextMatch = LIST_RE.exec(line)
      if (nextMatch && nextMatch[1].length === baseIndent && /\d/.test(nextMatch[2][0]) === ordered) break
      if (indentOf(line) <= baseIndent) break
      itemLines.push(dedent(line, Math.min(contentIndent, baseIndent + 2)))
      i += 1
    }
    const item = { blocks: [] }
    const task = TASK_RE.exec(itemLines[0] || '')
    if (task) {
      item.checked = task[1].toLowerCase() === 'x'
      itemLines[0] = task[2]
    }
    item.blocks = parseBlocks(itemLines, ctx, depth)
    items.push(item)
    // Blank lines between items belong to the list; anything else ends it here
    // and is re-read by the caller.
    let probe = i
    while (probe < lines.length && !lines[probe].trim()) probe += 1
    const following = probe < lines.length ? LIST_RE.exec(lines[probe]) : null
    if (following && following[1].length === baseIndent && /\d/.test(following[2][0]) === ordered) i = probe
  }
  return i
}

function indentOf(line) {
  return /^\s*/.exec(line)[0].length
}

function dedent(line, width) {
  let removed = 0
  let index = 0
  while (index < line.length && removed < width && (line[index] === ' ' || line[index] === '\t')) {
    removed += line[index] === '\t' ? 4 : 1
    index += 1
  }
  return line.slice(index)
}

/** Inline scanner: code spans, links, images, emphasis, escapes, hard breaks. */
function parseInline(source, ctx, depth) {
  const text = asText(source)
  const nodes = []
  if (depth > MAX_DEPTH) {
    return text ? [{ t: 'text', v: text }] : []
  }
  let buffer = ''
  /**
   * The last two characters of `buffer`, tracked separately: indexing into the
   * accumulated string would force V8 to flatten the rope on every newline,
   * which turns a long paragraph quadratic.
   */
  let textTail = ''
  let i = 0
  const add = (str) => {
    buffer += str
    textTail = (textTail + str).slice(-2)
  }
  const flush = () => {
    if (buffer) {
      nodes.push({ t: 'text', v: buffer })
      buffer = ''
      textTail = ''
    }
  }
  const room = () => ctx.inline < MAX_INLINE_NODES

  while (i < text.length) {
    if (!room() || ctx.work > MAX_WORK) {
      // Out of inline budget: keep the rest as text, which is bounded by input.
      add(text.slice(i))
      ctx.spent = true
      break
    }
    const ch = text[i]

    if (ch === '\\' && i + 1 < text.length && ESCAPABLE.includes(text[i + 1])) {
      add(text[i + 1])
      i += 2
      continue
    }

    if (ch === '\n') {
      // Two trailing spaces (or a backslash) are the hard-break marker. Testing
      // the tail directly keeps a long paragraph linear instead of running a
      // regex over the whole buffer at every newline.
      const hardBreak = textTail === '  ' || textTail.endsWith('\\')
      if (hardBreak) {
        let end = buffer.length
        while (end > 0 && buffer[end - 1] === ' ') end -= 1
        if (end === buffer.length) end -= 1
        buffer = buffer.slice(0, end)
        flush()
        ctx.inline += 1
        nodes.push({ t: 'br' })
      } else {
        add(' ')
      }
      i += 1
      continue
    }

    if (ch === '`') {
      let run = 0
      while (text[i + run] === '`') run += 1
      const marker = '`'.repeat(run)
      const close = findCodeClose(text, i + run, marker, ctx)
      if (close > -1) {
        flush()
        const code = text.slice(i + run, close)
        ctx.inline += 1
        nodes.push({ t: 'code', v: code.replace(/^ (.*) $/, '$1') })
        i = close + run
        continue
      }
      add(marker)
      i += run
      continue
    }

    if (ch === '!' && text[i + 1] === '[') {
      const image = matchLink(text, i + 1, ctx)
      if (image) {
        flush()
        const target = resolveTarget(image.href, ctx)
        ctx.inline += 1
        if (target && target.kind === 'asset') nodes.push({ t: 'img', src: target.path, alt: image.label })
        else nodes.push({ t: 'text', v: image.raw })
        i = image.end
        continue
      }
    }

    if (ch === '[') {
      const link = matchLink(text, i, ctx)
      if (link) {
        flush()
        const target = resolveTarget(link.href, ctx)
        const children = parseInline(link.label, ctx, depth + 1)
        ctx.inline += 1 + children.length
        if (target && target.kind === 'external') nodes.push({ t: 'link', href: target.href, c: children })
        else if (target && target.kind === 'doc') nodes.push({ t: 'link', doc: target.path, c: children })
        else nodes.push({ t: 'text', v: link.label })
        i = link.end
        continue
      }
    }

    if (ch === '<') {
      const rest = text.slice(i)
      const br = BR_RE.exec(rest)
      if (br) {
        flush()
        ctx.inline += 1
        nodes.push({ t: 'br' })
        i += br[0].length
        continue
      }
      const auto = AUTOLINK_RE.exec(rest)
      if (auto) {
        flush()
        ctx.inline += 1
        const href = auto[1]
        nodes.push({ t: 'link', href, c: [{ t: 'text', v: href.replace(/^mailto:/, '') }] })
        i += auto[0].length
        continue
      }
    }

    if (ch === '*' || ch === '_' || ch === '~') {
      const emphasis = matchEmphasis(text, i, ctx, depth)
      if (emphasis) {
        flush()
        ctx.inline += 1
        nodes.push(emphasis.node)
        i = emphasis.end
        continue
      }
    }

    add(ch)
    i += 1
  }
  flush()
  return nodes
}

/** Find the closing code-span run within the scan window. */
function findCodeClose(text, from, run, ctx) {
  const limit = Math.min(text.length, from + MAX_SCAN)
  if (!spend(ctx, limit - from)) return -1
  let index = from
  while (index < limit) {
    const found = text.indexOf(run, index)
    if (found < 0 || found >= limit) return -1
    // A closing run must be exactly as long as the opening one.
    if (text[found + run.length] === run[0]) {
      let end = found
      while (text[end] === run[0]) end += 1
      index = end
      continue
    }
    return found
  }
  return -1
}

/**
 * `[label](destination "title")` starting at `at`; returns null when it is not a
 * complete link within the scan window.
 *
 * Destinations may be wrapped in `<…>`; a trailing quoted segment is a title and
 * is dropped; any other embedded space stays part of the destination, because
 * this repository links to file names that contain spaces.
 */
function matchLink(text, at, ctx) {
  if (text[at] !== '[') return null
  const scanEnd = Math.min(text.length, at + MAX_SCAN)
  if (!spend(ctx, Math.min(MAX_SCAN, text.length - at))) return null
  let depth = 0
  let index = at
  let label = ''
  for (; index < scanEnd; index += 1) {
    const ch = text[index]
    if (ch === '\\' && index + 1 < scanEnd) {
      label += text.slice(index, index + 2)
      index += 1
      continue
    }
    if (ch === '[') {
      depth += 1
      if (depth > MAX_LABEL_DEPTH) return null
      if (depth === 1) continue
    }
    if (ch === ']') {
      depth -= 1
      if (depth === 0) break
    }
    if (ch === '\n' && depth === 1) return null
    label += ch
  }
  if (index >= scanEnd || text[index] !== ']') return null
  if (text[index + 1] !== '(') return null
  let cursor = index + 2
  let inner = ''
  let quote = ''
  let parens = 0
  for (; cursor < scanEnd; cursor += 1) {
    const ch = text[cursor]
    if (quote) {
      // Keep the quotes: cleanDestination needs them to recognise a title.
      inner += ch
      if (ch === quote) quote = ''
      continue
    }
    if (ch === '\\' && cursor + 1 < scanEnd) {
      inner += text[cursor + 1]
      cursor += 1
      continue
    }
    if (ch === '"' || ch === "'") {
      quote = ch
      inner += ch
      continue
    }
    if (ch === '(') {
      parens += 1
      inner += ch
      continue
    }
    if (ch === ')') {
      if (parens === 0) break
      parens -= 1
      inner += ch
      continue
    }
    inner += ch
  }
  if (cursor >= scanEnd || text[cursor] !== ')') return null
  const href = cleanDestination(inner)
  if (!href) return null
  return { label, href, end: cursor + 1, raw: text.slice(at, cursor + 1) }
}

/** Strip `<…>` and a trailing quoted title from a link destination. */
function cleanDestination(inner) {
  let value = inner.trim()
  if (value.startsWith('<') && value.endsWith('>')) {
    value = value.slice(1, -1).trim()
  } else {
    const titled = /^([\s\S]*?)\s+["']([\s\S]*)["']$/.exec(value)
    if (titled) value = titled[1].trim()
  }
  return value
}

function matchEmphasis(text, at, ctx, depth) {
  const mark = text[at]
  if (mark === '~' && text[at + 1] !== '~') return null
  // Only the run's width matters (1..3); counting the whole run would make a
  // line of thousands of delimiters quadratic.
  let size = 0
  while (size < 4 && text[at + size] === mark) size += 1
  if (mark === '~' && size < 2) return null
  const width = mark === '~' ? 2 : Math.min(size, 3)
  if (width === 1 && mark === '_' && isWordChar(text[at - 1])) return null
  const open = text.slice(at, at + width)
  const from = at + width
  if (from >= text.length) return null
  if (/\s/.test(text[from])) return null
  const limit = Math.min(text.length, from + MAX_SCAN)
  if (!spend(ctx, limit - from)) return null
  let cursor = from
  while (cursor < limit) {
    const found = text.indexOf(open, cursor)
    if (found < 0 || found >= limit) return null
    if (text[found - 1] === '\\') {
      cursor = found + open.length
      continue
    }
    const before = text[found - 1]
    const after = text[found + open.length]
    if (width === 1 && /\s/.test(before || '')) {
      cursor = found + open.length
      continue
    }
    if (width === 1 && mark === '_' && isWordChar(after)) {
      cursor = found + open.length
      continue
    }
    if (found === from) {
      cursor = found + open.length
      continue
    }
    const inner = text.slice(from, found)
    if (!inner.trim()) {
      cursor = found + open.length
      continue
    }
    const children = parseInline(inner, ctx, depth + 1)
    const tag = width === 2 ? (mark === '~' ? 'del' : 'b') : width === 3 ? 'bi' : 'i'
    const node = tag === 'bi'
      ? { t: 'b', c: [{ t: 'i', c: children }] }
      : { t: tag, c: children }
    return { node, end: found + open.length }
  }
  return null
}

function isWordChar(ch) {
  return typeof ch === 'string' && /[A-Za-z0-9]/.test(ch)
}

/**
 * Resolve one link target against the report that contains it.
 *
 * Only three outcomes are possible, which is what keeps the reader inert:
 * an external http(s)/mailto URL, another report inside the tree (`.md`), or an
 * image inside the tree. Anything else degrades to plain text.
 */
export function resolveTarget(href, ctx) {
  const raw = asText(href).trim()
  if (!raw) return null
  if (EXTERNAL_RE.test(raw)) return { kind: 'external', href: raw }
  if (raw.startsWith('#')) return null
  let decoded = raw
  try {
    decoded = decodeURIComponent(raw)
  } catch {
    return null
  }
  if (decoded.startsWith('//')) return null
  const base = asText(ctx && ctx.docPath)
  const dir = base.includes('/') ? base.slice(0, base.lastIndexOf('/')) : ''
  const joined = decoded.startsWith('/')
    ? normalizePath(`reports${decoded}`)
    : normalizePath(dir ? `${dir}/${decoded}` : decoded)
  if (!joined || !joined.startsWith('reports/')) return null
  if (/\.md$/i.test(joined)) return { kind: 'doc', path: joined }
  const dot = joined.lastIndexOf('.')
  const ext = dot > 0 ? joined.slice(dot).toLowerCase() : ''
  if (IMAGE_EXT.has(ext)) return { kind: 'asset', path: joined }
  return null
}

/** Collapse `.`/`..` segments without touching the filesystem. */
export function normalizePath(input) {
  const parts = asText(input).split('/')
  const out = []
  for (const part of parts) {
    if (!part || part === '.') continue
    if (part === '..') {
      if (!out.length) return ''
      out.pop()
      continue
    }
    out.push(part)
  }
  return out.join('/')
}
