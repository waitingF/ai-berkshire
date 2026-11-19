/**
 * Host half of the research-report browser.
 *
 * Reads the project's `reports/` tree and publishes the browser's data over the
 * browser HTTP carrier:
 *
 *   GET  /plugin/research-reports/data.json    every 标的 with its reports
 *   GET  /plugin/research-reports/report.json  one report, parsed into blocks
 *   GET  /plugin/research-reports/asset        one image referenced by a report
 *   GET  /plugin/research-reports/state.json   the reader's pins and ordering
 *   POST /plugin/research-reports/state.json   persist pins and ordering
 *
 * Indexing is a directory scan: a report counts as soon as its Markdown file
 * exists on disk, independent of `git add` or of a previously generated
 * `reports/index.json`.
 *
 * Rules are the ones this repository already uses for its generated index
 * (`tools/reports_index.py` + `reports/_index/config.json`): front-matter wins
 * over filename, filename wins over directory suffix, and 底稿/证据/审计 style
 * intermediate artifacts are flagged instead of dropped.
 */
import { mkdir, open, readFile, realpath, rename, stat, unlink, readdir, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import path from 'node:path'

import { MAX_INPUT_CHARS, findHeading, normalizePath, parseMarkdown } from './markdown.js'

export const name = 'research-reports'

/** The data routes are served by the browser HTTP carrier. */
export const inject = ['webServer']

const DEFAULT_ROUTE = '/plugin/research-reports/data.json'
const DEFAULT_REPORT_ROUTE = '/plugin/research-reports/report.json'
const DEFAULT_ASSET_ROUTE = '/plugin/research-reports/asset'
const DEFAULT_STATE_ROUTE = '/plugin/research-reports/state.json'
const DEFAULT_MONITOR_ROUTE = '/plugin/research-reports/monitor.json'
/** Files the daily-monitor tool writes beside the reports it renders. */
const MONITOR_DIR = 'daily-monitor'
const MONITOR_JSON_NAME = 'daily-monitor-latest.json'
const MONITOR_MD_NAME = 'daily-monitor-latest.md'
const MAX_MONITOR_BYTES = 16 * 1024 * 1024
const MAX_MONITOR_ROWS = 400
/** How the monitor's own statuses rank when the panel orders them. */
const EVENT_STATUS_RANK = {
  TODAY: 0,
  REVIEW: 1,
  OVERDUE: 2,
  GAP: 3,
  OPEN: 4,
  UPCOMING_7D: 5,
  UPCOMING_14D: 6,
  DONE: 7,
}
const HEAD_BYTES = 32 * 1024
const SKIP_DIRS = new Set(['_index', '__pycache__', 'node_modules', '.git'])
/**
 * Directories that hold operational output rather than a research target. They
 * keep their own section instead of posing as a 标的; `bucketOverrides` in the
 * plugin config extends or replaces this table.
 */
const OPERATIONAL_BUCKETS = { 'daily-monitor': '监控', 'trigger-scan': '归档' }
const SKIP_FILES = new Set(['README.md', 'command-log.jsonl'])
const DATE_IN_NAME = /(20[2-3]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])/
const DATE_IN_BODY = /(20[2-3]\d)[-/年](\d{1,2})[-/月](\d{1,2})/
const DATE_SUFFIX = /-20[2-3]\d[01]\d[0-3]\d$/
const AGGREGATE_GROUP = '综合与横评'

/** Bytes of Markdown read per report request; the rest is reported as cut. */
const DEFAULT_MAX_REPORT_BYTES = 400 * 1024
/** Bytes served per image request. */
const MAX_ASSET_BYTES = 16 * 1024 * 1024
/** Bytes accepted for one view-state write. */
const MAX_STATE_BYTES = 256 * 1024
const MAX_STATE_BUCKETS = 64
const MAX_STATE_NAMES = 2000
const MAX_NAME_CHARS = 200
/** Parsed reports kept in memory, most recently used last. */
const DOC_CACHE_SIZE = 12

const ASSET_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.avif': 'image/avif',
  '.bmp': 'image/bmp',
}

/** Ordered report-type rules: first match wins. */
const TYPE_RULES = [
  ['底稿', ['研究底稿', '核验', '评审', 'verify', '底稿', '对账']],
  ['财报', ['earnings', '财报', '中报', '年报', '季报', '业绩', '电话会', 'q1', 'q2', 'q3', 'q4']],
  ['公众号', ['公众号', 'wechat', '推文']],
  ['深度系列', ['看懂', '深度研究', 'deep-dive', '深度投研']],
  ['横评对比', ['横评', '对比', 'vs', '对决', 'pk', '换仓', '轮动']],
  ['组织管理', ['7s', '管理层', '组织', 'management']],
  ['估值仓位', ['估值', '赔率', '凯利', '仓位', 'valuation', 'fair_value', '终值']],
  ['筛选', ['funnel', '筛选', '召回', 'screen', '候选池']],
]

const FALLBACK_CONFIG = {
  aliases: {},
  companies: [],
  themes: [],
  masters: [],
  screens: [],
  other: [],
  tickers: {},
  drafts: { dirs: [], dir_suffixes: [], file_patterns: [] },
}

function normalizeConfig(config) {
  const raw = config && typeof config === 'object' ? config : {}
  const reportsDir = typeof raw.reportsDir === 'string' && raw.reportsDir.trim()
    ? path.resolve(raw.reportsDir.trim())
    : path.join(homedir(), 'stock', 'ai-berkshire', 'reports')
  const route = (value, fallback) => (typeof value === 'string' && value.startsWith('/')
    ? value.replace(/\/+$/, '')
    : fallback)
  const overrides = { ...OPERATIONAL_BUCKETS }
  if (raw.bucketOverrides && typeof raw.bucketOverrides === 'object') {
    for (const [dir, bucket] of Object.entries(raw.bucketOverrides)) {
      if (typeof dir === 'string' && typeof bucket === 'string' && bucket) overrides[dir] = bucket
    }
  }
  const statePath = typeof raw.statePath === 'string' && raw.statePath.trim()
    ? path.resolve(raw.statePath.trim())
    : path.join(homedir(), '.dsh', 'storages', 'research-reports', 'ui-state.json')
  const maxReportBytes = Number.isFinite(raw.maxReportBytes) && raw.maxReportBytes > 0
    ? Math.min(Math.floor(raw.maxReportBytes), 8 * 1024 * 1024)
    : DEFAULT_MAX_REPORT_BYTES
  const monitorDir = typeof raw.monitorDir === 'string' && raw.monitorDir.trim()
    ? raw.monitorDir.trim().replace(/^\.\//, '')
    : MONITOR_DIR
  return {
    reportsDir,
    routePath: route(raw.routePath, DEFAULT_ROUTE),
    reportRoutePath: route(raw.reportRoutePath, DEFAULT_REPORT_ROUTE),
    assetRoutePath: route(raw.assetRoutePath, DEFAULT_ASSET_ROUTE),
    stateRoutePath: route(raw.stateRoutePath, DEFAULT_STATE_ROUTE),
    monitorRoutePath: route(raw.monitorRoutePath, DEFAULT_MONITOR_ROUTE),
    bucketOverrides: overrides,
    statePath,
    monitorDir,
    maxReportBytes: Math.min(maxReportBytes, MAX_INPUT_CHARS * 4),
  }
}

/** Strip a trailing `-YYYYMMDD` so a dated directory reads like a name. */
function displayName(name) {
  return name.replace(DATE_SUFFIX, '') || name
}

function asDate(year, month, day) {
  const y = Number(year)
  const m = Number(month)
  const d = Number(day)
  if (!y || m < 1 || m > 12 || d < 1 || d > 31) return null
  const iso = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  const probe = new Date(`${iso}T00:00:00Z`)
  if (Number.isNaN(probe.getTime())) return null
  return probe.toISOString().slice(0, 10) === iso ? iso : null
}

function parseFrontMatter(lines) {
  if (!lines.length || lines[0].trim() !== '---') return {}
  const meta = {}
  for (const line of lines.slice(1)) {
    if (line.trim() === '---') return meta
    const at = line.indexOf(':')
    if (at > 0) meta[line.slice(0, at).trim().toLowerCase()] = line.slice(at + 1).trim().replace(/^["']|["']$/g, '')
  }
  return {}
}

function firstHeading(lines) {
  for (const line of lines) {
    const match = /^#\s+(.+?)\s*$/.exec(line)
    if (match) return match[1].replace(/[*`]/g, '').trim()
  }
  return ''
}

function guessType(fileName, relPath) {
  const hay = `${fileName} ${relPath}`.toLowerCase()
  for (const [label, keys] of TYPE_RULES) {
    for (const key of keys) if (hay.includes(key)) return label
  }
  return '研究'
}

function isDraft(relPath, drafts) {
  const parts = relPath.split('/')
  const stem = parts[parts.length - 1].replace(/\.md$/i, '')
  if (stem.includes('公众号')) return false
  const dirs = parts.slice(0, -1)
  const draftDirs = new Set((drafts.dirs || []).map(d => d.toLowerCase()))
  if (dirs.some(d => draftDirs.has(d.toLowerCase()))) return true
  const suffixes = drafts.dir_suffixes || []
  if (dirs.some(d => suffixes.some(suffix => displayName(d).endsWith(suffix)))) return true
  const cleaned = displayName(stem).toLowerCase()
  return (drafts.file_patterns || []).some(pattern => {
    try { return new RegExp(pattern).test(cleaned) } catch { return false }
  })
}

async function readHead(absPath) {
  let handle
  try {
    handle = await open(absPath, 'r')
    const buffer = Buffer.alloc(HEAD_BYTES)
    const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0)
    return buffer.toString('utf8', 0, bytesRead)
  } catch {
    return ''
  } finally {
    if (handle) await handle.close().catch(() => {})
  }
}

/** Read at most `limit` bytes as text; a multi-byte character cut in half is dropped. */
async function readText(absPath, limit) {
  let handle
  try {
    handle = await open(absPath, 'r')
    const buffer = Buffer.alloc(limit)
    const { bytesRead } = await handle.read(buffer, 0, limit, 0)
    return { text: buffer.toString('utf8', 0, bytesRead).replace(/\uFFFD+$/, ''), bytesRead }
  } finally {
    if (handle) await handle.close().catch(() => {})
  }
}

/** Read a request body as text, refusing anything above `limit` bytes. */
async function readBody(request, limit) {
  const chunks = []
  let size = 0
  for await (const chunk of request) {
    size += chunk.length
    if (size > limit) {
      const error = new Error('状态过大')
      error.status = 413
      throw error
    }
    chunks.push(chunk)
  }
  return Buffer.concat(chunks).toString('utf8')
}

/** Collect every Markdown file under the reports root, skipping bookkeeping dirs. */
async function collectMarkdown(root) {
  const found = []
  async function walk(dir, prefix, depth) {
    let entries
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      return
    }
    for (const entry of entries) {
      if (entry.name.startsWith('.')) continue
      const abs = path.join(dir, entry.name)
      const rel = prefix ? `${prefix}/${entry.name}` : entry.name
      if (entry.isDirectory()) {
        if (SKIP_DIRS.has(entry.name) || depth >= 3) continue
        await walk(abs, rel, depth + 1)
      } else if (entry.isFile() && /\.md$/i.test(entry.name) && !SKIP_FILES.has(entry.name)) {
        found.push({ abs, rel })
      }
    }
  }
  await walk(root, '', 0)
  return found
}

/** bucket_of: project config decides whether a top-level name is a company, theme, pool or master. */
function bucketOf(top, config) {
  const name = config.aliases[top] || top
  if (config.screens.includes(name)) return { bucket: '筛选池', group: name }
  if (config.themes.includes(name)) return { bucket: '专题', group: name }
  if (config.masters.includes(name)) return { bucket: '大师研究', group: name }
  if (config.other.includes(name)) return { bucket: '其他', group: name }
  return { bucket: '公司', group: name }
}

async function loadProjectConfig(root) {
  try {
    const text = await readHead(path.join(root, '_index', 'config.json'))
    const parsed = JSON.parse(text)
    return { ...FALLBACK_CONFIG, ...parsed, drafts: { ...FALLBACK_CONFIG.drafts, ...(parsed.drafts || {}) } }
  } catch {
    return FALLBACK_CONFIG
  }
}

function isInside(root, target) {
  return target === root || target.startsWith(root + path.sep)
}

/** Resolve the reports root once, so symlinked parents compare correctly. */
async function realRootOf(dir, cache) {
  if (!cache.value) cache.value = await realpath(dir).catch(() => dir)
  return cache.value
}

/**
 * Resolve one request target and prove it really lives inside the reports tree:
 * the lexical check alone would accept a symlink placed inside `reports/`.
 */
export async function safeTarget(dir, raw, cache = { value: null }) {
  const target = fileFor(dir, raw)
  if (!target) return null
  const [root, real] = await Promise.all([
    realRootOf(dir, cache),
    realpath(target.abs).catch(() => null),
  ])
  if (!real || real === root || !isInside(root, real)) return null
  return { ...target, real }
}

/**
 * Map a `reports/...` path from the panel onto a file inside the reports root.
 * Exported for the package's Node test; the routes call `safeTarget` instead.
 */
export function fileFor(reportsDir, raw) {
  if (typeof raw !== 'string' || !raw.trim()) return null
  let rel = normalizePath(raw.trim())
  if (!rel) return null
  if (rel.startsWith('reports/')) rel = rel.slice('reports/'.length)
  if (!rel || rel.startsWith('..')) return null
  const abs = path.resolve(reportsDir, rel)
  if (!isInside(reportsDir, abs) || abs === reportsDir) return null
  return { abs, rel, path: `reports/${rel}` }
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    },
  })
}

function failure(message, status) {
  return jsonResponse({ error: message }, status)
}

function readOnlyMethod(method) {
  return method === 'GET' || method === 'HEAD'
}

/** One clean name list from a posted state document. */
function cleanNames(value) {
  if (!Array.isArray(value)) return []
  const seen = new Set()
  const out = []
  for (const item of value) {
    if (typeof item !== 'string') continue
    const name = item.trim()
    if (!name || name.length > MAX_NAME_CHARS || seen.has(name)) continue
    seen.add(name)
    out.push(name)
    if (out.length >= MAX_STATE_NAMES) break
  }
  return out
}

/** Names that would collide with object internals when used as a bucket key. */
const RESERVED_KEYS = new Set(['__proto__', 'constructor', 'prototype'])

/** Accept only the documented shape; anything else is dropped, not trusted. */
export function normalizeViewState(raw) {
  const state = { version: 1, buckets: {} }
  const buckets = raw && typeof raw === 'object' && raw.buckets && typeof raw.buckets === 'object'
    ? raw.buckets
    : {}
  let count = 0
  for (const [bucket, value] of Object.entries(buckets)) {
    if (count >= MAX_STATE_BUCKETS) break
    const name = typeof bucket === 'string' ? bucket.trim() : ''
    if (!name || name.length > MAX_NAME_CHARS || RESERVED_KEYS.has(name)) continue
    if (!value || typeof value !== 'object') continue
    const pins = cleanNames(value.pins)
    const order = cleanNames(value.order).filter(item => !pins.includes(item))
    if (!pins.length && !order.length) continue
    state.buckets[name] = { pins, order }
    count += 1
  }
  return state
}

/** One finite number from a monitor payload field, or null. */
function asNumber(value) {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

/** Prices keep the monitor's own two-decimal form. */
export function formatMonitorPrice(value) {
  const number = asNumber(value)
  return number === null ? '' : number.toFixed(2)
}

/** The zone in words: `[65.00, 90.00]`, `≤ 60.00`, `≥ 22.20`, or empty. */
export function monitorCondition(metadata) {
  const source = metadata && typeof metadata === 'object' ? metadata : {}
  const low = asNumber(source.low)
  const high = asNumber(source.high)
  const direction = typeof source.direction === 'string' ? source.direction : 'range'
  if (direction === 'below' && high !== null) return `≤ ${high.toFixed(2)}`
  if (direction === 'above' && low !== null) return `≥ ${low.toFixed(2)}`
  if (low !== null && high !== null) return `[${low.toFixed(2)}, ${high.toFixed(2)}]`
  if (low !== null) return `≥ ${low.toFixed(2)}`
  if (high !== null) return `≤ ${high.toFixed(2)}`
  return ''
}

/** Distance to the condition, worded the way the monitor report words it. */
export function monitorGap(item) {
  const source = item && typeof item === 'object' ? item : {}
  const metadata = source.metadata && typeof source.metadata === 'object' ? source.metadata : {}
  const status = typeof source.status === 'string' ? source.status : ''
  const price = asNumber(metadata.price)
  const low = asNumber(metadata.low)
  const high = asNumber(metadata.high)
  const direction = typeof metadata.direction === 'string' ? metadata.direction : 'range'
  if (status === 'WARN') return '已越警戒线'
  if (status === 'TRIGGERED') {
    if (direction === 'range' && price !== null && low !== null && low > 0 && price < low) {
      return `低于下界 ${(((low - price) / low) * 100).toFixed(1)}%`
    }
    return '区间内'
  }
  let boundary = null
  if (direction === 'below') boundary = high
  else if (direction === 'above') boundary = low
  else if (price !== null) {
    if (low !== null && price < low) boundary = low
    else if (high !== null && price > high) boundary = high
    else boundary = high === null ? low : high
  }
  if (price === null || boundary === null || boundary <= 0) return ''
  return `${((Math.abs(price - boundary) / boundary) * 100).toFixed(1)}%`
}

/**
 * The monitor links to research reports relative to its own directory, e.g.
 * `../拼多多/拼多多-research-20261031.md`; the panel needs `reports/...`.
 */
export function monitorLinkToPath(link, monitorDir = MONITOR_DIR) {
  const raw = typeof link === 'string' ? link.trim() : ''
  if (!raw) return ''
  if (/^[a-z][a-z0-9+.-]*:/i.test(raw) || raw.startsWith('//')) return ''
  let decoded = raw
  try {
    decoded = decodeURIComponent(raw)
  } catch {
    return ''
  }
  const dir = String(monitorDir || MONITOR_DIR).replace(/^\/+|\/+$/g, '')
  const joined = decoded.startsWith('reports/')
    ? normalizePath(decoded)
    : normalizePath(`reports/${dir}/${decoded}`)
  if (!joined || !joined.startsWith('reports/') || !/\.md$/i.test(joined)) return ''
  return joined
}

function monitorRow(item, monitorDir) {
  const metadata = item && item.metadata && typeof item.metadata === 'object' ? item.metadata : {}
  return {
    name: String(item.name || item.target_id || ''),
    targetId: String(item.target_id || ''),
    priority: String(item.priority || ''),
    status: String(item.status || ''),
    resolved: Boolean(item.resolved),
    needsHumanReview: Boolean(item.needs_human_review),
    researchPath: monitorLinkToPath(metadata.research_link, monitorDir),
    researchDate: String(metadata.research_date || ''),
  }
}

/**
 * Reduce the daily monitor's JSON document to what the panel shows: the price
 * zones that are triggered or near, and the events still waiting on a human.
 */
export function buildMonitorPayload(raw, options = {}) {
  const monitorDir = options.monitorDir || MONITOR_DIR
  const payload = {
    ok: false,
    date: '',
    timezone: '',
    status: '',
    summary: '',
    sources: [],
    reportPath: options.reportPath || '',
    counts: { triggered: 0, near: 0, far: 0, warn: 0, events: 0, today: 0, overdue: 0, review: 0 },
    price: [],
    events: [],
  }
  if (!raw || typeof raw !== 'object' || !Array.isArray(raw.items)) return payload
  payload.ok = true
  payload.date = String(raw.date || '')
  payload.timezone = String(raw.timezone || '')
  payload.status = String(raw.status || '')
  payload.summary = String(raw.summary || '')
  if (Array.isArray(raw.source_health)) {
    payload.sources = raw.source_health
      .filter(row => row && typeof row === 'object')
      .map(row => ({ source: String(row.source || ''), status: String(row.status || '') }))
      .filter(row => row.source)
  }

  for (const item of raw.items) {
    if (!item || typeof item !== 'object') continue
    const metadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {}
    const status = String(item.status || '')
    if (item.section === 'price') {
      // The monitor's ascending price warnings live on their own sheet; the
      // reader shows the zones that are reached or nearly reached.
      if (metadata.direction === 'above') continue
      if (status === 'TRIGGERED') payload.counts.triggered += 1
      else if (status === 'NEAR') payload.counts.near += 1
      else if (status === 'WARN') payload.counts.warn += 1
      else payload.counts.far += 1
      if (payload.price.length >= MAX_MONITOR_ROWS) continue
      payload.price.push({
        ...monitorRow(item, monitorDir),
        market: String(metadata.market || ''),
        zoneLabel: String(metadata.zone_label || item.title || ''),
        condition: monitorCondition(metadata),
        price: formatMonitorPrice(metadata.price),
        gap: monitorGap(item),
        whyNow: String(item.why_now || ''),
        note: String(metadata.note || ''),
      })
      continue
    }
    if (status === 'DONE') continue
    if (item.resolved) continue
    payload.counts.events += 1
    if (status === 'TODAY') payload.counts.today += 1
    else if (status === 'OVERDUE') payload.counts.overdue += 1
    else if (status === 'REVIEW') payload.counts.review += 1
    if (payload.events.length >= MAX_MONITOR_ROWS) continue
    const sources = Array.isArray(item.source_urls) ? item.source_urls : []
    payload.events.push({
      ...monitorRow(item, monitorDir),
      kind: item.section === 'disclosures' ? 'disclosure' : 'event',
      title: String(item.title || ''),
      date: String(metadata.date || metadata.published_at || ''),
      url: typeof sources[0] === 'string' ? sources[0] : '',
    })
  }

  const priceRank = { TRIGGERED: 0, WARN: 1, NEAR: 2, FAR: 3 }
  payload.price.sort((a, b) => {
    const left = priceRank[a.status] === undefined ? 9 : priceRank[a.status]
    const right = priceRank[b.status] === undefined ? 9 : priceRank[b.status]
    if (left !== right) return left - right
    const priority = a.priority.localeCompare(b.priority)
    return priority === 0 ? a.name.localeCompare(b.name, 'zh-Hans-CN') : priority
  })
  payload.events.sort((a, b) => {
    const left = EVENT_STATUS_RANK[a.status] === undefined ? 9 : EVENT_STATUS_RANK[a.status]
    const right = EVENT_STATUS_RANK[b.status] === undefined ? 9 : EVENT_STATUS_RANK[b.status]
    if (left !== right) return left - right
    const priority = a.priority.localeCompare(b.priority)
    return priority === 0 ? a.name.localeCompare(b.name, 'zh-Hans-CN') : priority
  })
  return payload
}

export function apply(ctx, config) {
  const options = normalizeConfig(config)
  /** Parsed head per absolute path, reused while the file keeps its mtime and size. */
  const headCache = new Map()
  /** Parsed Markdown per absolute path, most recently used last. */
  const docCache = new Map()
  let cached = null
  let monitorCache = null
  let stateCache = null
  let stateWriteChain = Promise.resolve()
  /** Real path of the reports root, resolved once per plugin instance. */
  const realRoot = { value: null }

  async function parseReport(file, config, cache, bucketOverrides) {
    let info
    try {
      info = await stat(file.abs)
    } catch {
      return null
    }
    const stamp = `${info.mtimeMs}:${info.size}`
    const key = file.abs
    let entry = cache.get(key)
    if (!entry || entry.stamp !== stamp) {
      const head = await readHead(file.abs)
      // Keep enough lines for a title that is not on line 1, but never the raw
      // 32 KB head: one cached entry per report is retained for the process.
      entry = { stamp, lines: head.split('\n').slice(0, 200) }
      cache.set(key, entry)
    }
    const meta = parseFrontMatter(entry.lines)
    const segments = file.rel.split('/')
    const fileName = segments[segments.length - 1]
    const parent = segments.length > 1 ? segments[segments.length - 2] : ''

    let date = ''
    let dateSource = ''
    const fromMeta = (meta.date || '').replace(/\//g, '-')
    if (/^20\d\d-\d\d-\d\d$/.test(fromMeta)) {
      date = fromMeta
      dateSource = 'front-matter'
    }
    if (!date) {
      for (const source of [fileName, parent]) {
        const match = DATE_IN_NAME.exec(source)
        if (match) {
          date = asDate(match[1], match[2], match[3]) || ''
          dateSource = '文件名'
          break
        }
      }
    }
    if (!date) {
      for (const line of entry.lines.slice(0, 15)) {
        const match = DATE_IN_BODY.exec(line)
        if (match) {
          date = asDate(match[1], match[2], match[3]) || ''
          dateSource = '正文'
          break
        }
      }
    }
    if (!date) {
      date = new Date(info.mtimeMs).toISOString().slice(0, 10)
      dateSource = '文件时间'
    }

    const top = segments.length > 1 ? segments[0] : ''
    const override = top ? bucketOverrides[top] : undefined
    const { bucket, group } = top
      ? (override ? { bucket: override, group: top } : bucketOf(top, config))
      : { bucket: '专题', group: AGGREGATE_GROUP }
    const stem = fileName.replace(/\.md$/i, '')
    const rawType = typeof meta.type === 'string' && meta.type ? meta.type : ''
    const type = rawType || (isDraft(file.rel, config.drafts) ? '底稿' : guessType(fileName, file.rel))
    const title = (meta.title || firstHeading(entry.lines) || displayName(stem)).trim() || displayName(stem)

    return {
      title,
      path: `reports/${file.rel}`,
      date,
      dateSource,
      type,
      draft: type === '底稿',
      bucket,
      group,
      series: segments.length > 2 ? segments[1] : '',
    }
  }

  async function buildSnapshot() {
    const reportsDir = options.reportsDir
    const config = await loadProjectConfig(reportsDir)
    const files = await collectMarkdown(reportsDir)
    const liveKeys = new Set(files.map(f => f.abs))
    for (const key of headCache.keys()) if (!liveKeys.has(key)) headCache.delete(key)

    const reports = []
    for (const file of files) {
      const row = await parseReport(file, config, headCache, options.bucketOverrides)
      if (row) reports.push(row)
    }

    const byGroup = new Map()
    for (const row of reports) {
      let group = byGroup.get(row.group)
      if (!group) {
        group = { name: row.group, bucket: row.bucket, ticker: config.tickers[row.group] || '', reports: [] }
        byGroup.set(row.group, group)
      }
      group.reports.push(row)
    }

    let draftCount = 0
    for (const group of byGroup.values()) {
      group.reports.sort((a, b) => (a.date === b.date ? a.path.localeCompare(b.path) : a.date < b.date ? 1 : -1))
      group.latest = group.reports[0].date
      group.count = group.reports.filter(row => !row.draft).length
      group.draftCount = group.reports.length - group.count
      draftCount += group.draftCount
    }

    const groups = [...byGroup.values()].sort((a, b) => {
      if (a.latest !== b.latest) return a.latest < b.latest ? 1 : -1
      return a.name.localeCompare(b.name, 'zh-Hans-CN')
    })

    const rows = new Map()
    for (const group of groups) {
      for (const row of group.reports) {
        if (!rows.has(row.path)) rows.set(row.path, { ...row, ticker: group.ticker })
      }
    }

    return {
      generatedAt: new Date().toISOString(),
      reportsDir,
      totals: {
        groups: groups.length,
        reports: reports.length,
        drafts: draftCount,
        latest: groups[0] ? groups[0].latest : '',
      },
      rows,
      groups,
    }
  }

  async function snapshot() {
    if (cached && Date.now() - cached.at < 2000) return cached.value
    const value = await buildSnapshot()
    cached = { at: Date.now(), value }
    return value
  }

  /** One parsed report, reused while the file is unchanged. */
  async function loadReport(target) {
    const info = await stat(target.abs).catch(() => null)
    if (!info || !info.isFile()) return null
    const stamp = `${info.mtimeMs}:${info.size}`
    const hit = docCache.get(target.abs)
    if (hit && hit.stamp === stamp) {
      docCache.delete(target.abs)
      docCache.set(target.abs, hit)
      return hit.doc
    }
    const limit = Math.min(options.maxReportBytes, Math.max(info.size, 1))
    const { text, bytesRead } = await readText(target.abs, limit)
    const cut = info.size > bytesRead
    const parsed = parseMarkdown(text, { docPath: target.path })
    const doc = {
      path: target.path,
      blocks: parsed.blocks,
      cut: cut || parsed.cut,
      truncated: parsed.truncated,
      size: info.size,
      shownBytes: bytesRead,
    }
    docCache.set(target.abs, { stamp, doc })
    while (docCache.size > DOC_CACHE_SIZE) docCache.delete(docCache.keys().next().value)
    return doc
  }

  /** The reader's pins and ordering, cached until the file's mtime moves. */
  async function readViewState() {
    let info = null
    try {
      info = await stat(options.statePath)
    } catch {
      return { version: 1, buckets: {}, updatedAt: null, stored: false }
    }
    const stamp = `${info.mtimeMs}:${info.size}`
    if (stateCache && stateCache.stamp === stamp) return stateCache.value
    let state
    try {
      if (info.size > MAX_STATE_BYTES * 4) throw new Error('state file too large')
      const text = await readFile(options.statePath, 'utf8')
      const parsed = JSON.parse(text)
      state = { ...normalizeViewState(parsed), updatedAt: new Date(info.mtimeMs).toISOString(), stored: true }
    } catch {
      state = { version: 1, buckets: {}, updatedAt: null, stored: false, broken: true }
    }
    stateCache = { stamp, value: state }
    return state
  }

  async function writeViewState(raw) {
    const state = normalizeViewState(raw)
    const text = `${JSON.stringify({ version: state.version, buckets: state.buckets, updatedAt: new Date().toISOString() }, null, 2)}\n`
    const dir = path.dirname(options.statePath)
    await mkdir(dir, { recursive: true })
    const temp = `${options.statePath}.${process.pid}.tmp`
    try {
      await writeFile(temp, text, { mode: 0o600 })
      await rename(temp, options.statePath)
    } catch (error) {
      await unlink(temp).catch(() => {})
      throw error
    }
    stateCache = null
    const saved = await readViewState()
    return saved
  }

  async function handleReport(request) {
    const url = new URL(request.url)
    const target = await safeTarget(options.reportsDir, url.searchParams.get('path'), realRoot)
    if (!target || !/\.md$/i.test(target.abs)) return failure('报告路径无效', 400)
    let doc
    try {
      doc = await loadReport(target)
    } catch (error) {
      return failure(error && error.message ? error.message : String(error), 500)
    }
    if (!doc) return failure('报告不存在', 404)
    const view = await snapshot()
    const row = view.rows.get(doc.path) || null
    const payload = {
      ...doc,
      title: row ? row.title : (findHeading(doc.blocks) || displayName(path.basename(doc.path, '.md'))),
      date: row ? row.date : '',
      dateSource: row ? row.dateSource : '',
      type: row ? row.type : '',
      draft: row ? row.draft : false,
      group: row ? row.group : '',
      bucket: row ? row.bucket : '',
    }
    return jsonResponse(payload)
  }

  async function handleAsset(request) {
    const url = new URL(request.url)
    const target = await safeTarget(options.reportsDir, url.searchParams.get('path'), realRoot)
    if (!target) return failure('资源路径无效', 400)
    const ext = path.extname(target.abs).toLowerCase()
    const type = ASSET_TYPES[ext]
    if (!type) return failure('不支持的资源类型', 415)
    const info = await stat(target.abs).catch(() => null)
    if (!info || !info.isFile()) return failure('资源不存在', 404)
    if (info.size > MAX_ASSET_BYTES) return failure('资源过大', 413)
    const headers = {
      'content-type': type,
      'content-length': String(info.size),
      'last-modified': info.mtime.toUTCString(),
      'cache-control': 'private, no-cache',
      'x-content-type-options': 'nosniff',
    }
    if (ext === '.svg') {
      // Rendered through <img> this is safe; navigated to directly it would be a
      // same-origin document, so it gets a sandbox and a download disposition.
      headers['content-security-policy'] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
      headers['content-disposition'] = 'attachment'
    }
    if (request.method === 'HEAD') return new Response(null, { headers })
    const buffer = await readFile(target.abs)
    headers['content-length'] = String(buffer.length)
    return new Response(buffer, { headers })
  }

  /**
   * The state route must accept a write, and the carrier only forwards GET/HEAD
   * to `resource` routes, so this one is a plain Node handler that owns its
   * response for every method.
   */
  /** The daily monitor's own summary document, cached until its file moves. */
  async function loadMonitor() {
    const dir = path.join(options.reportsDir, options.monitorDir)
    const mdInfo = await stat(path.join(dir, MONITOR_MD_NAME)).catch(() => null)
    const reportPath = mdInfo && mdInfo.isFile()
      ? `reports/${options.monitorDir}/${MONITOR_MD_NAME}`
      : ''
    const info = await stat(path.join(dir, MONITOR_JSON_NAME)).catch(() => null)
    const missing = { ...buildMonitorPayload(null, { monitorDir: options.monitorDir, reportPath }), exists: false }
    if (!info || !info.isFile()) return missing
    const stamp = `${info.mtimeMs}:${info.size}`
    if (monitorCache && monitorCache.stamp === stamp) return monitorCache.value
    if (info.size > MAX_MONITOR_BYTES) return { ...missing, exists: true, error: '监控数据过大' }
    let raw
    try {
      raw = JSON.parse(await readFile(path.join(dir, MONITOR_JSON_NAME), 'utf8'))
    } catch (error) {
      return { ...missing, exists: true, error: '监控数据无法解析' }
    }
    const value = {
      ...buildMonitorPayload(raw, { monitorDir: options.monitorDir, reportPath }),
      exists: true,
      generatedAt: new Date(info.mtimeMs).toISOString(),
    }
    monitorCache = { stamp, value }
    return value
  }

  async function handleState(req, res) {
    const send = (status, payload, extra) => {
      const body = JSON.stringify(payload)
      res.writeHead(status, {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
        'content-length': Buffer.byteLength(body),
        ...(extra || {}),
      })
      res.end(req.method === 'HEAD' ? undefined : body)
    }

    try {
      if (req.method === 'GET' || req.method === 'HEAD') {
        send(200, await readViewState())
        return
      }
      if (req.method !== 'POST') {
        send(405, { error: 'Method Not Allowed' }, { allow: 'GET, HEAD, POST' })
        return
      }
      // A browser always sends Origin for a same-origin POST; anything else —
      // including the `null` origin of a sandboxed page — is a foreign writer.
      const origin = req.headers.origin
      if (origin !== undefined) {
        let originHost = ''
        try {
          originHost = new URL(origin).host
        } catch {
          originHost = ''
        }
        if (!originHost || originHost !== req.headers.host) {
          send(403, { error: '跨站写入被拒绝' })
          return
        }
      }
      const fetchSite = req.headers['sec-fetch-site']
      if (fetchSite && fetchSite !== 'same-origin' && fetchSite !== 'none') {
        send(403, { error: '跨站写入被拒绝' })
        return
      }
      if (!String(req.headers['content-type'] || '').toLowerCase().startsWith('application/json')) {
        send(415, { error: '只接受 application/json' })
        return
      }
      const body = await readBody(req, MAX_STATE_BYTES)
      let parsed
      try {
        parsed = JSON.parse(body || '{}')
      } catch {
        send(400, { error: '状态不是合法 JSON' })
        return
      }
      stateWriteChain = stateWriteChain.then(
        () => writeViewState(parsed),
        () => writeViewState(parsed),
      )
      send(200, await stateWriteChain)
    } catch (error) {
      const message = error && error.message ? error.message : String(error)
      send(error && error.status ? error.status : 500, { error: message })
    }
  }

  function route(routePath, resource) {
    ctx.effect(
      () => ctx.webServer.register({ kind: 'exact', path: routePath, resource }),
      `research-reports: ${routePath}`,
    )
  }

  function routeHandler(routePath, handler) {
    ctx.effect(
      () => ctx.webServer.register({ kind: 'exact', path: routePath, handler }),
      `research-reports: ${routePath}`,
    )
  }

  route(options.routePath, async (request) => {
    if (!readOnlyMethod(request.method)) {
      return new Response('Method Not Allowed', { status: 405, headers: { allow: 'GET, HEAD' } })
    }
    try {
      const view = await snapshot()
      const body = JSON.stringify({
        generatedAt: view.generatedAt,
        reportsDir: view.reportsDir,
        totals: view.totals,
        groups: view.groups,
      })
      return new Response(request.method === 'HEAD' ? null : body, {
        headers: {
          'content-type': 'application/json; charset=utf-8',
          'cache-control': 'no-store',
          'x-content-type-options': 'nosniff',
        },
      })
    } catch (error) {
      const message = error && error.message ? error.message : String(error)
      return jsonResponse({ error: message, reportsDir: options.reportsDir }, 500)
    }
  })

  route(options.reportRoutePath, async (request) => {
    if (!readOnlyMethod(request.method)) {
      return new Response('Method Not Allowed', { status: 405, headers: { allow: 'GET, HEAD' } })
    }
    try {
      const response = await handleReport(request)
      if (request.method !== 'HEAD') return response
      return new Response(null, { status: response.status, headers: response.headers })
    } catch (error) {
      return failure(error && error.message ? error.message : String(error), 500)
    }
  })

  route(options.assetRoutePath, async (request) => {
    if (!readOnlyMethod(request.method)) {
      return new Response('Method Not Allowed', { status: 405, headers: { allow: 'GET, HEAD' } })
    }
    try {
      return await handleAsset(request)
    } catch (error) {
      return failure(error && error.message ? error.message : String(error), 500)
    }
  })

  route(options.monitorRoutePath, async (request) => {
    if (!readOnlyMethod(request.method)) {
      return new Response('Method Not Allowed', { status: 405, headers: { allow: 'GET, HEAD' } })
    }
    try {
      const body = JSON.stringify(await loadMonitor())
      return new Response(request.method === 'HEAD' ? null : body, {
        headers: {
          'content-type': 'application/json; charset=utf-8',
          'cache-control': 'no-store',
          'x-content-type-options': 'nosniff',
        },
      })
    } catch (error) {
      return failure(error && error.message ? error.message : String(error), 500)
    }
  })

  routeHandler(options.stateRoutePath, (req, res) => handleState(req, res))

  ctx.effect(() => () => {
    cached = null
    monitorCache = null
    headCache.clear()
    docCache.clear()
    stateCache = null
    realRoot.value = null
  }, 'research-reports: cache')
}
