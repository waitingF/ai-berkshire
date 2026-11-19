/**
 * Client half of the research-report browser.
 *
 * Adds one global panel to the sidebar (id `research-reports`) and renders its
 * page into the `main` keyed seat: every 标的 of this project with its reports,
 * newest first. The data comes from this package's Host half through the routes
 * the Host registers under `/plugin/research-reports/`.
 *
 * Three behaviours live here on top of the list: pinning a 标的 to the top of its
 * own category, dragging 标的 to change that order (the Host persists both), and
 * opening a report into a reader view inside the same panel.
 *
 * Plain JavaScript, no JSX: the browser bundle resolves React from the shared
 * module table and registers a lazy factory.
 */
window.__ModuleLoader__.load({
  id: '@local/research-reports',
  factory(require) {
    const React = require('react')
    const h = React.createElement

    const NS = 'research-reports'
    const PANEL_ID = 'research-reports'
    const DATA_URL = '/plugin/research-reports/data.json'
    const REPORT_URL = '/plugin/research-reports/report.json'
    const ASSET_URL = '/plugin/research-reports/asset'
    const STATE_URL = '/plugin/research-reports/state.json'
    const MONITOR_URL = '/plugin/research-reports/monitor.json'
    /** Monitor status → locale key, and the tone its chip is drawn in. */
    const STATUS_LABEL = {
      TRIGGERED: 'statusTriggered',
      NEAR: 'statusNear',
      FAR: 'statusFar',
      WARN: 'statusWarn',
      TODAY: 'statusToday',
      OVERDUE: 'statusOverdue',
      REVIEW: 'statusReview',
      GAP: 'statusGap',
      OPEN: 'statusOpen',
      UPCOMING_7D: 'statusUpcoming7',
      UPCOMING_14D: 'statusUpcoming14',
      DONE: 'statusDone',
    }
    const STATUS_TONE = {
      TRIGGERED: 'error',
      OVERDUE: 'error',
      WARN: 'error',
      NEAR: 'warn',
      TODAY: 'warn',
      GAP: 'warn',
      REVIEW: 'brand',
      OPEN: 'muted',
      UPCOMING_7D: 'muted',
      UPCOMING_14D: 'muted',
      FAR: 'muted',
      DONE: 'success',
    }
    /** How many events the monitor view lists before pointing at the report. */
    const MONITOR_EVENT_ROWS = 20
    const APPROX_SOURCE = '文件时间'
    const BUCKET_ORDER = ['公司', '专题', '大师研究', '筛选池', '监控', '归档', '其他']
    const BUCKET_LABEL = {
      公司: 'bucketCompany',
      专题: 'bucketTheme',
      大师研究: 'bucketMaster',
      筛选池: 'bucketScreen',
      监控: 'bucketMonitor',
      归档: 'bucketArchive',
      其他: 'bucketOther',
    }
    /** Saved ordering is written after this quiet period, so a drag writes once. */
    const SAVE_DELAY = 320

    const ZH = {
      panel: '研究报告',
      title: '研究报告',
      subtitle: '按标的汇总，时间降序',
      search: '搜索标的或报告标题',
      showDrafts: '显示底稿',
      refresh: '刷新',
      refreshing: '刷新中',
      loading: '正在读取报告目录…',
      retry: '重试',
      groups: '标的',
      reports: '篇',
      drafts: '篇底稿',
      hiddenDrafts: '篇底稿已隐藏',
      showThem: '打开「显示底稿」即可查看',
      latest: '最新',
      copyPath: '复制路径',
      copied: '已复制',
      copyFailed: '复制失败',
      emptySearch: '没有匹配的标的',
      emptySelection: '从左侧选择一个标的',
      emptyDir: '报告目录里没有报告',
      emptyDirHint: '确认 reportsDir 指向存放 .md 报告的目录，然后重试。',
      errorTitle: '读取报告目录失败',
      staleNote: '刷新失败，仍显示上次读取的结果',
      source: '来源：本地 reports/ 目录',
      generated: '读取于',
      none: '暂无报告',
      approx: '文件时间（文件名与正文都没有日期）',
      bucketCompany: '公司',
      bucketTheme: '专题',
      bucketMaster: '大师研究',
      bucketScreen: '筛选池',
      bucketMonitor: '监控',
      bucketArchive: '归档',
      bucketOther: '其他',
      pin: '置顶',
      unpin: '取消置顶',
      pinHint: '置顶在本分类最前',
      rowMenuHint: '右键更多操作',
      menuLabel: '标的操作',
      moveTop: '移到最前',
      moveBottom: '移到最后',
      moveTopInPins: '移到置顶块最前',
      moveBottomInPins: '移到置顶块最后',
      movedTop: '已移到最前',
      movedBottom: '已移到最后',
      monitor: '每日监控',
      monitorHint: '进入或接近价格区间的标的，以及待处理的正式披露',
      backToReports: '返回报告',
      backToMonitor: '返回监控',
      monitorLoading: '正在读取监控数据…',
      monitorStale: '数据截至',
      monitorDaysAgo: '天前',
      monitorDisclaimer: '价格达到条件只触发研究复核；优先级表示研究处理顺序，不代表交易信号，也不构成投资建议。',
      monitorLegend: 'P0=到达或进入条件 · P1=距对应边界≤5% · P2=其他价格区间',
      monitorPinnedOnly: '只看置顶',
      monitorMatch: '匹配',
      monitorSearchAllHint: '搜索时显示全部价格区间',
      monitorKindDisclosure: '披露',
      monitorKindOther: '其他',
      monitorOpenAnnouncement: '打开公告',
      monitorViewReport: '打开完整监控报告',
      monitorPrice: '价格区间',
      monitorTriggered: '进入区间',
      monitorNear: '接近',
      monitorEvents: '财报与正式披露',
      monitorSources: '数据源',
      monitorAttentionOnly: '只看进入与接近',
      monitorAll: '显示全部',
      monitorNoData: '未找到每日监控数据',
      monitorNoDataHint: '确认 reports/daily-monitor/daily-monitor-latest.json 存在（由每日监控任务生成）；仍可直接打开最新监控报告。',
      monitorEmpty: '当前没有进入或接近价格区间的标的',
      monitorEmptySearch: '没有匹配的监控项',
      monitorError: '读取监控数据失败',
      monitorTarget: '标的',
      monitorMarket: '市场',
      monitorCondition: '条件',
      monitorPriceLabel: '现价',
      monitorGap: '距边界',
      monitorStatus: '状态',
      monitorToday: '今天到期',
      monitorOverdue: '逾期',
      monitorReview: '待复核',
      monitorEventsTotal: '共',
      monitorMoreEvents: '其余 {n} 条见完整报告',
      monitorResearchDate: '研究日期',
      statusTriggered: '进入区间',
      statusNear: '接近',
      statusFar: '未接近',
      statusWarn: '越警戒线',
      statusToday: '今天到期',
      statusOverdue: '逾期',
      statusReview: '待复核',
      statusGap: '缺口',
      statusOpen: '待处理',
      statusUpcoming7: '7 天内',
      statusUpcoming14: '14 天内',
      statusDone: '已完成',
      reorderHint: '拖拽标的或按 Alt+↑/↓ 调整顺序，置顶的排在本分类最前',
      reorderHintOffSearch: '清空搜索后可拖拽排序',
      reorderHintOffReader: '阅读中：Alt+↑/↓ 仍可调整顺序',
      reorderHintTouch: '触屏：图钉可置顶，排序请用桌面端或外接键盘 Alt+↑/↓',
      resetOrder: '恢复默认排序',
      resetConfirm: '再点一次确认恢复',
      orderReset: '已恢复默认排序',
      orderSaved: '排序已保存',
      orderLoadFailed: '读取置顶与排序失败',
      orderSaving: '保存排序中',
      manualOrder: '手工顺序',
      manualOrderHint: '这个分类拖动过，未置顶的标的按手工顺序排列',
      openReport: '查看报告',
      reading: '正在读取报告…',
      readFailed: '读取报告失败',
      backToList: '返回报告列表',
      backToPrevious: '返回上一篇',
      docTruncated: '文件较大，仅显示前',
      docBlocksCut: '段落过多，只渲染了前一部分',
      docEmpty: '这篇报告没有可显示的正文',
      docRaw: '原始内容（未解析的 HTML）',
      externalLink: '在新窗口打开外链',
      taskDone: '已完成',
      taskOpen: '未完成',
      savedPins: '置顶与排序已保存在本机',
      saveFailed: '保存失败',
    }

    const EN = {
      panel: 'Research reports',
      title: 'Research reports',
      subtitle: 'Every target with its reports, newest first',
      search: 'Search a target or a report title',
      showDrafts: 'Show drafts',
      refresh: 'Refresh',
      refreshing: 'Refreshing',
      loading: 'Reading the report tree…',
      retry: 'Retry',
      groups: 'targets',
      reports: 'reports',
      drafts: 'drafts',
      hiddenDrafts: 'drafts hidden',
      showThem: 'Turn on “Show drafts” to see them',
      latest: 'latest',
      copyPath: 'Copy path',
      copied: 'Copied',
      copyFailed: 'Copy failed',
      emptySearch: 'No matching target',
      emptySelection: 'Pick a target on the left',
      emptyDir: 'No report in this directory',
      emptyDirHint: 'Check that reportsDir points at the directory holding the .md reports, then retry.',
      errorTitle: 'Could not read the report tree',
      staleNote: 'Refresh failed; showing the previous result',
      source: 'Source: local reports/ directory',
      generated: 'Read at',
      none: 'No report yet',
      approx: 'File time (neither filename nor body carries a date)',
      bucketCompany: 'Companies',
      bucketTheme: 'Themes',
      bucketMaster: 'Masters',
      bucketScreen: 'Screens',
      bucketMonitor: 'Monitoring',
      bucketArchive: 'Archive',
      bucketOther: 'Other',
      pin: 'Pin to top',
      unpin: 'Unpin',
      pinHint: 'Pinned to the top of this section',
      rowMenuHint: 'Right-click for more',
      menuLabel: 'Target actions',
      moveTop: 'Move to the front',
      moveBottom: 'Move to the end',
      moveTopInPins: 'Move to the front of the pinned block',
      moveBottomInPins: 'Move to the end of the pinned block',
      movedTop: 'Moved to the front',
      movedBottom: 'Moved to the end',
      monitor: 'Daily monitor',
      monitorHint: 'Targets that reached or approach their price zone, plus formal disclosures awaiting review',
      backToReports: 'Back to reports',
      backToMonitor: 'Back to the monitor',
      monitorLoading: 'Reading the monitor data…',
      monitorStale: 'Data as of',
      monitorDaysAgo: 'days ago',
      monitorDisclaimer: 'A reached price triggers a research review only; priority orders the review work, not a trading signal, and this view is not investment advice.',
      monitorLegend: 'P0=condition reached · P1=within 5% of the boundary · P2=other zones',
      monitorPinnedOnly: 'Pinned only',
      monitorMatch: 'match',
      monitorSearchAllHint: 'A search always shows every price zone',
      monitorKindDisclosure: 'Disclosure',
      monitorKindOther: 'Other',
      monitorOpenAnnouncement: 'Open the announcement',
      monitorViewReport: 'Open the full monitor report',
      monitorPrice: 'Price zones',
      monitorTriggered: 'In zone',
      monitorNear: 'Near',
      monitorEvents: 'Earnings and formal disclosures',
      monitorSources: 'Sources',
      monitorAttentionOnly: 'Only reached or near',
      monitorAll: 'Show all',
      monitorNoData: 'No daily-monitor data found',
      monitorNoDataHint: 'Check that reports/daily-monitor/daily-monitor-latest.json exists (written by the daily-monitor run); the latest monitor report can still be opened.',
      monitorEmpty: 'No target has reached or approached its zone',
      monitorEmptySearch: 'No matching monitoring item',
      monitorError: 'Could not read the monitor data',
      monitorTarget: 'Target',
      monitorMarket: 'Market',
      monitorCondition: 'Condition',
      monitorPriceLabel: 'Price',
      monitorGap: 'Distance',
      monitorStatus: 'Status',
      monitorToday: 'due today',
      monitorOverdue: 'overdue',
      monitorReview: 'to review',
      monitorEventsTotal: 'total',
      monitorMoreEvents: '{n} more in the full report',
      monitorResearchDate: 'Research date',
      statusTriggered: 'In zone',
      statusNear: 'Near',
      statusFar: 'Not near',
      statusWarn: 'Above warning',
      statusToday: 'Due today',
      statusOverdue: 'Overdue',
      statusReview: 'To review',
      statusGap: 'Gap',
      statusOpen: 'Open',
      statusUpcoming7: 'Within 7 days',
      statusUpcoming14: 'Within 14 days',
      statusDone: 'Done',
      reorderHint: 'Drag a target or press Alt+↑/↓ to reorder; pinned ones stay on top of their section',
      reorderHintOffSearch: 'Clear the search to reorder',
      reorderHintOffReader: 'Reading: Alt+↑/↓ still reorders',
      reorderHintTouch: 'Touch: pin with the pin button; reorder on desktop or with Alt+↑/↓',
      resetOrder: 'Reset ordering',
      resetConfirm: 'Click again to confirm',
      orderReset: 'Ordering reset',
      orderSaved: 'Ordering saved',
      orderLoadFailed: 'Could not read the saved pins and ordering',
      orderSaving: 'Saving ordering',
      manualOrder: 'manual order',
      manualOrderHint: 'This section was reordered by hand; unpinned targets follow that order',
      openReport: 'Read report',
      reading: 'Reading the report…',
      readFailed: 'Could not read the report',
      backToList: 'Back to the report list',
      backToPrevious: 'Back to the previous report',
      docTruncated: 'Large file; showing the first',
      docBlocksCut: 'Too many blocks; only the first part is rendered',
      docEmpty: 'This report has no readable body',
      docRaw: 'Raw content (HTML left unparsed)',
      externalLink: 'Open the external link in a new window',
      taskDone: 'Done',
      taskOpen: 'Not done',
      savedPins: 'Pins and ordering are stored on this machine',
      saveFailed: 'Save failed',
    }

    const CSS = `
.rr-root {
  display: flex; flex-direction: column;
  width: 100%; height: 100%; min-width: 0; min-height: 0; overflow: hidden;
  background: var(--dsw-alias-bg-base); color: var(--dsw-alias-label-primary);
  font: inherit; font-size: 14px; line-height: 1.6;
}
.rr-root :focus-visible { outline: 2px solid var(--dsw-alias-brand-primary); outline-offset: 2px; border-radius: 8px; }
.rr-header {
  display: flex; flex-direction: column; gap: 10px;
  padding: 18px 20px 12px; border-bottom: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-titleline { display: flex; align-items: baseline; gap: 10px; min-width: 0; flex-wrap: wrap; }
.rr-title { margin: 0; font-size: 20px; line-height: 28px; font-weight: 500; }
.rr-subtitle { font-size: 12px; color: var(--dsw-alias-label-secondary); }
.rr-meta { margin-left: auto; font-size: 12px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; }
.rr-toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.rr-search {
  flex: 1 1 240px; min-width: 160px; height: 30px; padding: 0 10px; border-radius: 8px;
  border: 1px solid var(--dsw-alias-border-l2, var(--dsw-alias-border-l1));
  background: var(--dsw-alias-bg-layer-1);
  color: var(--dsw-alias-label-primary); font: inherit; font-size: 13px;
}
.rr-search:focus-visible { outline: 2px solid var(--dsw-alias-brand-primary); outline-offset: 1px; }
.rr-toggle { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--dsw-alias-label-secondary); cursor: pointer; }
.rr-toggle input { width: 14px; height: 14px; accent-color: var(--dsw-alias-brand-primary); cursor: pointer; }
.rr-button {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  height: 30px; padding: 0 12px; border-radius: 8px; cursor: pointer; font: inherit; font-size: 13px;
  border: 1px solid var(--dsw-alias-border-l2, var(--dsw-alias-border-l1));
  background: var(--dsw-alias-bg-layer-1);
  color: var(--dsw-alias-label-primary);
}
.rr-button:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-2)); }
.rr-button-danger { border-color: var(--dsw-alias-state-warn-primary); color: var(--dsw-alias-state-warn-primary); }
.rr-button-active { border-color: var(--dsw-alias-brand-primary); color: var(--dsw-alias-brand-primary); }
.rr-button:disabled { opacity: .55; cursor: default; }
.rr-button-quiet { border-color: transparent; background: transparent; color: var(--dsw-alias-label-secondary); }
.rr-button-quiet:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-2)); color: var(--dsw-alias-label-primary); }
.rr-notice {
  display: flex; align-items: center; gap: 10px; padding: 8px 20px;
  font-size: 12px; color: var(--dsw-alias-state-warn-primary);
  background: var(--dsw-alias-bg-layer-1);
  border-bottom: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-notice-text { flex: 1 1 auto; min-width: 0; }
.rr-body { display: flex; flex: 1 1 auto; min-height: 0; }
.rr-main { display: flex; flex: 1 1 auto; min-height: 0; flex-direction: column; }
.rr-nav {
  flex: 0 0 236px; display: flex; flex-direction: column; min-width: 0; min-height: 0;
  border-right: 1px solid var(--dsw-alias-border-l2, var(--dsw-alias-border-l1));
  background: var(--dsw-alias-bg-layer-1);
}
.rr-groups {
  flex: 1 1 auto; min-width: 0; min-height: 0; overflow-y: auto; padding: 8px;
  scrollbar-gutter: stable;
  --dsh-scrollbar-width: 9px;
  --dsh-scrollbar-thumb-border: 2px;
}
.rr-section + .rr-section { margin-top: 10px; }
.rr-section-label {
  display: flex; align-items: center; gap: 6px; padding: 4px 10px;
  font-size: 11px; letter-spacing: .04em;
  color: var(--dsw-alias-label-secondary); text-transform: uppercase;
}
.rr-section-note {
  padding: 0 5px; border: 0.5px solid var(--dsw-alias-border-l1); border-radius: 999px;
  font-size: 10px; letter-spacing: 0; text-transform: none;
}
.rr-group {
  display: flex; align-items: center; gap: 6px; width: 100%; padding: 7px 8px 7px 4px;
  border: 0; border-radius: 8px; background: transparent; color: inherit; font: inherit;
  font-size: 13px; text-align: left; cursor: pointer; position: relative;
  user-select: none;
}
.rr-group:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-2)); }
.rr-group[aria-current='true'] {
  background: var(--dsw-alias-interactive-bg-active, var(--dsw-alias-bg-layer-2));
  color: var(--dsw-alias-brand-primary); font-weight: 600;
}
.rr-group[draggable='true'] { cursor: grab; }
.rr-group.rr-dragging { opacity: .45; }
.rr-group.rr-drop-before { box-shadow: inset 0 2px 0 0 var(--dsw-alias-brand-primary); }
.rr-group.rr-drop-after { box-shadow: inset 0 -2px 0 0 var(--dsw-alias-brand-primary); }
.rr-grip {
  flex: 0 0 auto; width: 10px; font-size: 10px; letter-spacing: -1px; line-height: 1;
  color: var(--dsw-alias-label-secondary); opacity: .32; cursor: grab;
}
.rr-group:hover .rr-grip, .rr-group:focus-visible .rr-grip, .rr-group.is-pinned .rr-grip { opacity: .85; }
.rr-group-name { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rr-group-count { flex: 0 0 auto; font-size: 12px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; }
.rr-group[aria-current='true'] .rr-group-count { color: inherit; }
.rr-group-count-hidden { color: var(--dsw-alias-state-warn-primary); }
.rr-pin {
  flex: 0 0 auto; display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; padding: 0; border: 0; border-radius: 6px; cursor: pointer;
  background: transparent; color: var(--dsw-alias-label-secondary); opacity: 0;
}
.rr-group:hover .rr-pin, .rr-pin:focus-visible, .rr-pin[aria-pressed='true'] { opacity: 1; }
.rr-pin:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-2)); color: var(--dsw-alias-label-primary); }
.rr-pin[aria-pressed='true'] { color: var(--dsw-alias-brand-primary); }
.rr-pin-sep { margin: 4px 10px; border-top: 1px dashed var(--dsw-alias-border-l2); }
.rr-groups-hint {
  flex: 0 0 auto; padding: 7px 10px; font-size: 11px; line-height: 1.45;
  color: var(--dsw-alias-label-secondary); border-top: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-reports {
  flex: 1 1 auto; min-width: 0; overflow-y: auto; padding: 14px 20px 24px;
  scrollbar-gutter: stable;
  --dsh-scrollbar-width: 9px;
  --dsh-scrollbar-thumb-border: 2px;
}
.rr-reports-head { display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.rr-reports-name { font-size: 14px; font-weight: 600; }
.rr-reports-meta { font-size: 12px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; }
.rr-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
.rr-item {
  display: flex; align-items: center; gap: 12px; width: 100%; padding: 8px 10px;
  border: 0; border-radius: 10px; background: transparent; color: inherit; font: inherit;
  text-align: left; cursor: pointer;
}
.rr-item:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-1)); }
.rr-date {
  flex: 0 0 auto; font-size: 12px; color: var(--dsw-alias-label-secondary);
  font-variant-numeric: tabular-nums; letter-spacing: .01em;
}
.rr-date-approx { color: var(--dsw-alias-state-warn-primary); }
.rr-item-title {
  flex: 1 1 auto; min-width: 0; font-size: 13px;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden;
  overflow-wrap: anywhere;
}
.rr-chip {
  flex: 0 0 auto; padding: 1px 7px; border-radius: 999px; font-size: 11px;
  border: 0.5px solid var(--dsw-alias-border-l1); color: var(--dsw-alias-label-secondary);
}
.rr-chip-draft { border-color: var(--dsw-alias-state-warn-primary); color: var(--dsw-alias-state-warn-primary); }
.rr-copy {
  flex: 0 0 auto; font: inherit; font-size: 11px; padding: 2px 6px; border: 0; border-radius: 6px;
  background: transparent; color: var(--dsw-alias-label-secondary); opacity: 0; cursor: pointer;
}
.rr-item:hover .rr-copy, .rr-item:focus-visible .rr-copy, .rr-copy.rr-copy-done, .rr-copy.rr-copy-failed { opacity: 1; }
.rr-copy:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-2)); color: var(--dsw-alias-label-primary); }
.rr-copy-done { color: var(--dsw-alias-state-success-primary); }
.rr-copy-failed { color: var(--dsw-alias-state-error-primary); }
/* Right-click actions for one 标的 */
.rr-menu {
  position: fixed; z-index: 40; display: flex; flex-direction: column; gap: 2px;
  padding: 4px; border-radius: 10px;
  border: 1px solid var(--dsw-alias-border-l2, var(--dsw-alias-border-l1));
  background: var(--dsw-alias-bg-overlay, var(--dsw-alias-bg-layer-2));
  box-shadow: 0 8px 24px rgba(0, 0, 0, .16);
}
.rr-menu-item {
  display: flex; align-items: center; width: 100%; height: 30px; padding: 0 10px;
  border: 0; border-radius: 8px; background: transparent; color: inherit; font: inherit;
  font-size: 13px; text-align: left; white-space: nowrap; cursor: pointer;
}
.rr-menu-item:hover:not(:disabled), .rr-menu-item:focus-visible {
  background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-1));
}
.rr-menu-item:disabled { opacity: .45; cursor: default; }

@media (hover: none) {
  .rr-copy, .rr-pin { opacity: 1; }
  .rr-grip { display: none; }
}
.rr-hint { padding: 4px 0 0; font-size: 12px; color: var(--dsw-alias-label-secondary); }
.rr-note { padding: 8px 20px; font-size: 12px; color: var(--dsw-alias-label-secondary); border-top: 0.5px solid var(--dsw-alias-border-l1); }
.rr-state { display: flex; flex: 1 1 auto; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 32px; }
.rr-state-title { font-size: 14px; font-weight: 400; }
.rr-state-text { max-width: 560px; font-size: 12px; color: var(--dsw-alias-label-secondary); text-align: center; line-height: 1.6; overflow-wrap: anywhere; }
.rr-state-path { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; color: var(--dsw-alias-label-secondary); overflow-wrap: anywhere; text-align: center; }
.rr-error .rr-state-title { color: var(--dsw-alias-state-error-primary); }

/* Daily monitor */
.rr-monitor-head {
  display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; margin-bottom: 14px;
  border: 0.5px solid var(--dsw-alias-border-l1); border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
}
.rr-monitor-titleline { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.rr-monitor-title { margin: 0; font-size: 16px; font-weight: 600; }
.rr-monitor-date { font-size: 12px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; }
.rr-monitor-summary { font-size: 12px; color: var(--dsw-alias-label-secondary); }
.rr-monitor-sources { font-size: 11px; color: var(--dsw-alias-label-secondary); overflow-wrap: anywhere; }
.rr-monitor-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.rr-monitor-card { margin-bottom: 16px; }
.rr-monitor-cardhead { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.rr-monitor-cardtitle { margin: 0; font-size: 14px; font-weight: 600; }
.rr-monitor-cardhead .rr-button { margin-left: auto; }
.rr-status {
  display: inline-flex; align-items: center; padding: 0 7px; height: 20px; border-radius: 999px;
  font-size: 11px; border: 0.5px solid var(--dsw-alias-border-l1); color: var(--dsw-alias-label-secondary);
  white-space: nowrap;
}
.rr-status-error { border-color: var(--dsw-alias-state-error-primary); color: var(--dsw-alias-state-error-primary); }
.rr-status-warn { border-color: var(--dsw-alias-state-warn-primary); color: var(--dsw-alias-state-warn-primary); }
.rr-status-success { border-color: var(--dsw-alias-state-success-primary); color: var(--dsw-alias-state-success-primary); }
.rr-status-brand { border-color: var(--dsw-alias-brand-primary); color: var(--dsw-alias-brand-primary); }
.rr-monitor-table { font-size: 12.5px; }
.rr-monitor-table td { vertical-align: top; }
.rr-monitor-target { display: flex; align-items: baseline; gap: 6px; }
.rr-monitor-priority {
  flex: 0 0 auto; padding: 0 5px; border-radius: 5px; font-size: 10px;
  color: var(--dsw-alias-label-secondary); border: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-link-button {
  padding: 0; border: 0; background: transparent; font: inherit; font-size: 13px; font-weight: 600;
  color: var(--dsw-alias-brand-primary); cursor: pointer; text-align: left;
}
.rr-link-button:hover { text-decoration: underline; }
.rr-monitor-zone { margin-top: 2px; font-size: 11px; color: var(--dsw-alias-label-secondary); }
.rr-monitor-num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.rr-monitor-counts { display: flex; gap: 6px; flex-wrap: wrap; }
.rr-monitor-disclaimer { font-size: 11px; line-height: 1.5; color: var(--dsw-alias-label-secondary); }
.rr-monitor-legend { margin: -2px 0 8px; font-size: 11px; color: var(--dsw-alias-label-secondary); }
.rr-monitor-pinned { display: inline-flex; color: var(--dsw-alias-brand-primary); }
.rr-monitor-kind {
  flex: 0 0 auto; padding: 0 5px; border-radius: 5px; font-size: 10px;
  color: var(--dsw-alias-label-secondary); border: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-monitor-event-link { flex: 0 0 auto; font-size: 12px; }
.rr-monitor-more { margin: 6px 0 0; font-size: 12px; font-weight: 400; }
.rr-monitor-counts-inline { display: inline-flex; margin-left: 4px; }
.rr-monitor-counts-inline .rr-status { height: 18px; padding: 0 6px; }
.rr-monitor-events { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
.rr-monitor-event {
  display: flex; align-items: baseline; gap: 8px; padding: 6px 8px; border-radius: 8px;
  font-size: 12.5px;
}
.rr-monitor-event:hover { background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-1)); }
.rr-monitor-event-name { flex: 0 0 auto; font-weight: 600; }
.rr-monitor-event-title {
  flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--dsw-alias-label-secondary);
}
.rr-monitor-event-date { flex: 0 0 auto; font-size: 11px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; }

/* Reader */
.rr-doc { display: flex; flex-direction: column; min-height: 100%; }
.rr-doc-head {
  position: sticky; top: 0; z-index: 1; display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; background: var(--dsw-alias-bg-base);
  border-bottom: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-doc-headline { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1 1 auto; }
.rr-doc-title {
  font-size: 15px; font-weight: 600; line-height: 1.4; overflow-wrap: anywhere;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden;
}
.rr-doc-meta { font-size: 11px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.rr-doc-actions { display: flex; align-items: center; gap: 6px; flex: 0 0 auto; }
.rr-doc-note {
  margin: 12px 0 0; padding: 6px 10px; border-radius: 8px; font-size: 12px;
  background: var(--dsw-alias-bg-layer-1); color: var(--dsw-alias-state-warn-primary);
  border: 0.5px solid var(--dsw-alias-border-l1);
}
.rr-doc-body {
  max-width: 860px; margin: 0 auto; padding: 18px 20px 40px; width: 100%;
  overflow-wrap: anywhere;
}
.rr-doc-body p { margin: 0 0 12px; }
.rr-doc-body h1, .rr-doc-body h2, .rr-doc-body h3, .rr-doc-body h4, .rr-doc-body h5, .rr-doc-body h6 {
  margin: 24px 0 10px; line-height: 1.4; font-weight: 600; scroll-margin-top: 64px;
}
.rr-doc-body h1 { font-size: 22px; margin-top: 8px; }
.rr-doc-body h2 { font-size: 18px; }
.rr-doc-body h3 { font-size: 15px; }
.rr-doc-body h4, .rr-doc-body h5, .rr-doc-body h6 { font-size: 14px; }
.rr-doc-body ul, .rr-doc-body ol { margin: 0 0 12px; padding-left: 22px; }
.rr-doc-body li { margin: 2px 0; }
.rr-doc-body li > p { margin: 0 0 6px; }
.rr-doc-task { list-style: none; margin-left: -20px; display: flex; align-items: flex-start; gap: 6px; }
.rr-doc-task-mark { flex: 0 0 auto; color: var(--dsw-alias-state-success-primary); }
.rr-doc-task-mark.rr-doc-task-open { color: var(--dsw-alias-label-secondary); }
.rr-doc-quote {
  margin: 0 0 12px; padding: 6px 12px; border-left: 2px solid var(--dsw-alias-border-l2);
  background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-1));
  border-radius: 0 8px 8px 0;
  color: var(--dsw-alias-label-secondary);
}
.rr-doc-quote > :last-child { margin-bottom: 0; }
.rr-doc-tablewrap { overflow-x: auto; margin: 0 0 14px; border: 0.5px solid var(--dsw-alias-border-l1); border-radius: 10px; }
.rr-doc-table { border-collapse: collapse; width: 100%; font-size: 13px; }
.rr-doc-table th, .rr-doc-table td {
  padding: 6px 10px; border-bottom: 0.5px solid var(--dsw-alias-border-l2, var(--dsw-alias-border-l1));
  text-align: left; vertical-align: top; min-width: 60px;
}
.rr-doc-table th {
  background: var(--dsw-alias-interactive-bg-hover, var(--dsw-alias-bg-layer-1));
  font-weight: 600; white-space: nowrap;
}
.rr-doc-table tr:last-child td { border-bottom: 0; }
.rr-doc-code {
  padding: 1px 5px; border-radius: 5px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: .92em; background: var(--dsw-alias-markdown-inline-code, var(--dsw-alias-bg-layer-2));
}
.rr-doc-pre {
  margin: 0 0 14px; padding: 10px 12px; overflow-x: auto; border-radius: 10px;
  background: var(--dsw-alias-markdown-code-block, var(--dsw-alias-bg-layer-1));
  border: 0.5px solid var(--dsw-alias-border-l1);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; line-height: 1.55;
}
.rr-doc-pre code { font: inherit; }
.rr-doc-raw { white-space: pre-wrap; word-break: break-word; }
.rr-doc-hr { margin: 20px 0; border: 0; border-top: 0.5px solid var(--dsw-alias-border-l1); }
.rr-doc-link { color: var(--dsw-alias-brand-primary); text-decoration: none; }
.rr-doc-link:hover { text-decoration: underline; }
.rr-doc-doclink { text-decoration: underline dotted; }
.rr-doc-figure { margin: 0 0 14px; }
.rr-doc-img {
  display: block; max-width: 100%; height: auto; margin: 0 auto;
  border-radius: 10px; border: 0.5px solid var(--dsw-alias-border-l1); background: var(--dsw-alias-bg-layer-1);
}
.rr-doc-figcaption { margin-top: 6px; font-size: 12px; color: var(--dsw-alias-label-secondary); text-align: center; }

@media (max-width: 767px) {
  .rr-nav { flex-basis: 168px; }
  .rr-header { padding: 14px 14px 10px; }
  .rr-reports { padding: 12px 14px 20px; }
  .rr-item { gap: 8px; }
  .rr-chip { display: none; }
  .rr-doc-head { padding: 8px 12px; }
  .rr-doc-body { padding: 14px 14px 32px; }
}
@media (pointer: coarse) {
  .rr-search { font-size: 16px; }
}
`

    function count(value) {
      return typeof value === 'number' ? value.toLocaleString('zh-CN') : '0'
    }

    function bytes(value) {
      const size = typeof value === 'number' ? value : 0
      if (size >= 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
      if (size >= 1024) return Math.round(size / 1024) + ' KB'
      return size + ' B'
    }

    function isApprox(row) {
      return row && row.dateSource === APPROX_SOURCE
    }

    function byDateDesc(a, b) {
      if (a.date !== b.date) return a.date < b.date ? 1 : -1
      return a.path < b.path ? 1 : -1
    }

    /** Dated rows first, newest first; file-time-derived rows follow, newest first. */
    function sortRows(rows) {
      const dated = []
      const approx = []
      for (const row of rows) (isApprox(row) ? approx : dated).push(row)
      dated.sort(byDateDesc)
      approx.sort(byDateDesc)
      return dated.concat(approx)
    }

    /**
     * One visible set decides counts, the newest date, the group order and the
     * header totals, so hiding drafts can never contradict a row on screen.
     */
    function buildView(data, showDrafts) {
      const source = data && Array.isArray(data.groups) ? data.groups : []
      let visibleReports = 0
      let hiddenDrafts = 0
      const groups = []
      for (const group of source) {
        const all = Array.isArray(group.reports) ? group.reports : []
        const visible = (showDrafts ? all : all.filter(row => !row.draft)).map(row => ({
          ...row,
          title: String(row && row.title ? row.title : ''),
          path: String(row && row.path ? row.path : ''),
          type: String(row && row.type ? row.type : ''),
          date: String(row && row.date ? row.date : ''),
        }))
        const rows = sortRows(visible)
        const hidden = all.length - rows.length
        hiddenDrafts += hidden
        visibleReports += rows.length
        const known = rows.filter(row => !isApprox(row))
        groups.push({
          name: String(group.name || ''),
          bucket: String(group.bucket || '公司'),
          ticker: String(group.ticker || ''),
          rows,
          hidden,
          latest: known.length ? known[0].date : '',
          approxLatest: rows.length ? rows[0].date : '',
        })
      }
      groups.sort((a, b) => {
        const left = a.latest || a.approxLatest
        const right = b.latest || b.approxLatest
        if (left !== right) return left < right ? 1 : -1
        if (a.latest && !b.latest) return -1
        if (b.latest && !a.latest) return 1
        return a.name.localeCompare(b.name, 'zh-Hans-CN')
      })
      const latest = groups.reduce((acc, group) => (group.latest > acc ? group.latest : acc), '')
      return { groups, visibleReports, hiddenDrafts, latest }
    }

    /** Saved pins and manual order for one bucket, restricted to groups that exist. */
    function orderBucket(list, bucketPrefs) {
      const prefs = bucketPrefs && typeof bucketPrefs === 'object' ? bucketPrefs : {}
      const byName = new Map(list.map(group => [group.name, group]))
      const pins = (Array.isArray(prefs.pins) ? prefs.pins : []).filter(name => byName.has(name))
      const pinSet = new Set(pins)
      const index = new Map()
      for (const [position, name] of (Array.isArray(prefs.order) ? prefs.order : []).entries()) {
        if (!index.has(name)) index.set(name, position)
      }
      const rest = list.filter(group => !pinSet.has(group.name))
      rest.sort((a, b) => {
        const left = index.has(a.name) ? index.get(a.name) : Number.MAX_SAFE_INTEGER
        const right = index.has(b.name) ? index.get(b.name) : Number.MAX_SAFE_INTEGER
        return left === right ? 0 : (left < right ? -1 : 1)
      })
      return pins.map(name => ({ ...byName.get(name), pinned: true }))
        .concat(rest.map(group => ({ ...group, pinned: false })))
    }

    /** Every 标的 of one bucket in display order, split by the pin boundary. */
    function bucketLists(bucket, groups, prefs) {
      const bucketPrefs = prefs && prefs.buckets ? prefs.buckets[bucket] : undefined
      const ordered = orderBucket(groups.filter(group => group.bucket === bucket), bucketPrefs)
      return {
        pinned: ordered.filter(group => group.pinned).map(group => group.name),
        rest: ordered.filter(group => !group.pinned).map(group => group.name),
      }
    }

    /**
     * Left navigation sections in a fixed bucket order, then any unknown bucket.
     * Inside a section the saved order wins and pinned 标的 come first.
     */
    function sectionsOf(groups, needle, prefs) {
      const buckets = new Map()
      for (const group of groups) {
        const nameMatches = !needle || group.name.toLowerCase().includes(needle)
        const rows = !needle || nameMatches
          ? group.rows
          : group.rows.filter(row => row.title.toLowerCase().includes(needle))
        if (needle && !nameMatches && rows.length === 0) continue
        if (!needle && group.rows.length === 0 && group.hidden === 0) continue
        if (!buckets.has(group.bucket)) buckets.set(group.bucket, [])
        buckets.get(group.bucket).push({ ...group, shown: rows })
      }
      const ordered = []
      for (const bucket of BUCKET_ORDER) {
        if (buckets.has(bucket)) {
          const bucketPrefs = prefs && prefs.buckets ? prefs.buckets[bucket] : undefined
          ordered.push({ bucket, groups: orderBucket(buckets.get(bucket), bucketPrefs) })
          buckets.delete(bucket)
        }
      }
      for (const [bucket, list] of buckets) {
        const bucketPrefs = prefs && prefs.buckets ? prefs.buckets[bucket] : undefined
        ordered.push({ bucket, groups: orderBucket(list, bucketPrefs) })
      }
      return ordered
    }

    function bucketLabel(t, bucket) {
      const key = BUCKET_LABEL[bucket]
      return key ? t(key) : bucket
    }

    /** Move one name to the start or the end of a list, without changing pin state. */
    function moveToListEdge(list, name, edge) {
      const from = list.indexOf(name)
      if (from < 0) return list.slice()
      const next = list.slice()
      next.splice(from, 1)
      if (edge === 'first') next.unshift(name)
      else next.push(name)
      return next
    }

    /**
     * Pin or unpin one 标的. Pinning only touches the pin list, so the rest of the
     * category keeps its date order; unpinning returns to the natural date order
     * unless that category already has a manual order, where it goes first.
     */
    function togglePinLists(pins, order, name, unpin) {
      const rest = (order || []).filter(item => item !== name)
      if (unpin) {
        return {
          pinned: (pins || []).filter(item => item !== name),
          rest: (order || []).length ? [name].concat(rest) : rest,
        }
      }
      return { pinned: [name].concat((pins || []).filter(item => item !== name)), rest }
    }

    /** Move one name inside a list, placing it at the target's position. */
    function moveWithin(list, name, targetName, after) {
      const from = list.indexOf(name)
      if (from < 0) return list.slice()
      const next = list.slice()
      next.splice(from, 1)
      let at = next.indexOf(targetName)
      if (at < 0) at = next.length
      else if (after) at += 1
      next.splice(at, 0, name)
      return next
    }

    /** Move one name into another list, placing it at the target's position. */
    function moveAcross(source, target, name, targetName, after) {
      const nextSource = source.filter(item => item !== name)
      const nextTarget = target.filter(item => item !== name)
      let at = nextTarget.indexOf(targetName)
      if (at < 0) at = nextTarget.length
      else if (after) at += 1
      nextTarget.splice(at, 0, name)
      return { source: nextSource, target: nextTarget }
    }

    /** Inline request for one rendered Markdown tree. */
    function textOf(nodes) {
      let out = ''
      for (const node of nodes || []) {
        if (!node || typeof node !== 'object') continue
        if (node.t === 'text' || node.t === 'code') out += node.v
        else if (node.t === 'br') out += ' '
        else if (Array.isArray(node.c)) out += textOf(node.c)
      }
      return out.trim()
    }

    function assetUrl(path) {
      return ASSET_URL + '?path=' + encodeURIComponent(path)
    }

    /** One Markdown block tree into React elements; only the tags named here exist. */
    function renderInline(nodes, ctx) {
      const out = []
      let index = 0
      for (const node of nodes || []) {
        const key = 'i' + index
        index += 1
        if (!node || typeof node !== 'object') continue
        switch (node.t) {
          case 'text':
            if (node.v) out.push(node.v)
            break
          case 'code':
            out.push(h('code', { key, className: 'rr-doc-code' }, node.v))
            break
          case 'br':
            out.push(h('br', { key }))
            break
          case 'b':
            out.push(h('strong', { key }, renderInline(node.c, ctx)))
            break
          case 'i':
            out.push(h('em', { key }, renderInline(node.c, ctx)))
            break
          case 'del':
            out.push(h('del', { key }, renderInline(node.c, ctx)))
            break
          case 'link':
            if (node.doc) {
              out.push(h('a', {
                key,
                href: '#',
                className: 'rr-doc-link rr-doc-doclink',
                title: node.doc,
                onClick: (event) => {
                  event.preventDefault()
                  ctx.openDoc(node.doc)
                },
              }, renderInline(node.c, ctx)))
            } else {
              out.push(h('a', {
                key,
                href: node.href,
                className: 'rr-doc-link',
                title: ctx.t('externalLink'),
                target: '_blank',
                rel: 'noreferrer noopener',
              }, renderInline(node.c, ctx)))
            }
            break
          case 'img':
            out.push(h('img', {
              key,
              className: 'rr-doc-img',
              src: assetUrl(node.src),
              alt: node.alt || '',
              loading: 'lazy',
            }))
            break
          default:
            if (node.v) out.push(node.v)
        }
      }
      return out
    }

    /** Blocks of one report into React elements. */
    function renderBlocks(blocks, ctx) {
      const out = []
      let index = 0
      for (const block of blocks || []) {
        const key = 'b' + index
        index += 1
        if (!block || typeof block !== 'object') continue
        switch (block.t) {
          case 'h': {
            const level = Math.min(Math.max(block.level || 2, 1), 6)
            out.push(h('h' + level, { key, className: 'rr-doc-h rr-doc-h' + level }, renderInline(block.c, ctx)))
            break
          }
          case 'p':
            out.push(h('p', { key }, renderInline(block.c, ctx)))
            break
          case 'ul':
          case 'ol':
            out.push(h(block.t === 'ol' ? 'ol' : 'ul', {
              key,
              start: block.t === 'ol' && block.start ? block.start : undefined,
            }, (block.items || []).map((item, itemIndex) => {
              const boxed = typeof item.checked === 'boolean'
              return h('li', {
                key: 'li' + itemIndex,
                className: boxed ? 'rr-doc-task' : undefined,
              },
              boxed
                ? h('span', {
                  className: 'rr-doc-task-mark' + (item.checked ? '' : ' rr-doc-task-open'),
                  'aria-label': item.checked ? ctx.t('taskDone') : ctx.t('taskOpen'),
                  title: item.checked ? ctx.t('taskDone') : ctx.t('taskOpen'),
                }, item.checked ? '☑' : '☐')
                : null,
              h('div', null, renderBlocks(item.blocks, ctx)))
            })))
            break
          case 'quote':
            out.push(h('blockquote', { key, className: 'rr-doc-quote' }, renderBlocks(block.blocks, ctx)))
            break
          case 'table':
            out.push(h('div', { key, className: 'rr-doc-tablewrap' },
              h('table', { className: 'rr-doc-table' },
                h('thead', null, h('tr', null, (block.head || []).map((cell, cellIndex) => h('th', {
                  key: 'th' + cellIndex,
                  style: block.align && block.align[cellIndex] ? { textAlign: block.align[cellIndex] } : undefined,
                }, renderInline(cell, ctx))))),
                h('tbody', null, (block.rows || []).map((row, rowIndex) => h('tr', { key: 'tr' + rowIndex },
                  (row || []).map((cell, cellIndex) => h('td', {
                    key: 'td' + cellIndex,
                    style: block.align && block.align[cellIndex] ? { textAlign: block.align[cellIndex] } : undefined,
                  }, renderInline(cell, ctx)))))))))
            break
          case 'code':
            out.push(h('pre', { key, className: 'rr-doc-pre' }, h('code', null, block.text || '')))
            break
          case 'hr':
            out.push(h('hr', { key, className: 'rr-doc-hr' }))
            break
          case 'img':
            out.push(h('figure', { key, className: 'rr-doc-figure' },
              h('img', { className: 'rr-doc-img', src: assetUrl(block.src), alt: block.alt || '', loading: 'lazy' }),
              block.alt ? h('figcaption', { className: 'rr-doc-figcaption' }, block.alt) : null))
            break
          case 'html':
            out.push(h('pre', { key, className: 'rr-doc-pre rr-doc-raw', title: ctx.t('docRaw') }, block.text || ''))
            break
          default:
            break
        }
      }
      return out
    }

    /** State container shared by the panel; the Host answers one document per refresh. */
    function useReportData() {
      const [state, setState] = React.useState({ status: 'loading', data: null, error: '' })
      const [nonce, setNonce] = React.useState(0)
      const refresh = React.useCallback(() => setNonce(n => n + 1), [])

      React.useEffect(() => {
        const controller = new AbortController()
        let alive = true
        setState(previous => (previous.data
          ? { ...previous, status: 'refreshing', error: '' }
          : { status: 'loading', data: null, error: '' }))
        fetch(DATA_URL, { cache: 'no-store', signal: controller.signal, headers: { accept: 'application/json' } })
          .then(async (response) => {
            if (!response.ok) throw new Error('HTTP ' + response.status)
            const payload = await response.json()
            if (payload && payload.error) throw new Error(payload.error)
            return payload
          })
          .then((payload) => {
            if (alive) setState({ status: 'ready', data: payload, error: '' })
          })
          .catch((error) => {
            if (!alive || (error && error.name === 'AbortError')) return
            const message = error && error.message ? error.message : String(error)
            setState(previous => ({ status: 'error', data: previous.data, error: message }))
          })
        return () => {
          alive = false
          controller.abort()
        }
      }, [nonce])

      return { state, refresh }
    }

    /** One monitor status as a chip; only the tones this panel names are drawn. */
    function statusChip(t, status) {
      if (!status) return null
      const labelKey = STATUS_LABEL[status]
      const tone = STATUS_TONE[status] || 'muted'
      return h('span', { className: 'rr-status rr-status-' + tone, title: status },
        labelKey ? t(labelKey) : status)
    }

    /** The daily monitor's own summary document, fetched once per open/refresh. */
    function useMonitorData() {
      const [state, setState] = React.useState({ status: 'loading', data: null, error: '' })
      const [nonce, setNonce] = React.useState(0)
      const refresh = React.useCallback(() => setNonce(n => n + 1), [])

      React.useEffect(() => {
        const controller = new AbortController()
        let alive = true
        setState(previous => (previous.data
          ? { ...previous, status: 'refreshing', error: '' }
          : { status: 'loading', data: null, error: '' }))
        fetch(MONITOR_URL, { cache: 'no-store', signal: controller.signal, headers: { accept: 'application/json' } })
          .then(async (response) => {
            if (!response.ok) throw new Error('HTTP ' + response.status)
            return response.json()
          })
          .then((payload) => {
            if (alive) setState({ status: 'ready', data: payload, error: '' })
          })
          .catch((error) => {
            if (!alive || (error && error.name === 'AbortError')) return
            setState(previous => ({
              status: 'error',
              data: previous.data,
              error: error && error.message ? error.message : String(error),
            }))
          })
        return () => {
          alive = false
          controller.abort()
        }
      }, [nonce])

      return { state, refresh }
    }

    /**
     * The daily monitor, in the same form the project's Pages site shows it: the
     * price zones that are reached or nearly reached, then the disclosures still
     * waiting on a human. Every 标的 links to its research report.
     */
    function MonitorView(props) {
      const { t, state, refresh, openReport, needle, pinned } = props
      const [filter, setFilter] = React.useState('auto')
      const [pinnedOnly, setPinnedOnly] = React.useState(false)
      const payload = state.data
      const matches = (value) => !needle || String(value || '').toLowerCase().includes(needle)

      if (state.status === 'loading') {
        return h('section', { className: 'rr-reports rr-monitor' },
          h('div', { className: 'rr-state' }, h('div', { className: 'rr-state-title' }, t('monitorLoading'))))
      }

      if (state.status === 'error' && !payload) {
        return h('section', { className: 'rr-reports rr-monitor' },
          h('div', { className: 'rr-state rr-error' },
            h('div', { className: 'rr-state-title' }, t('monitorError')),
            h('div', { className: 'rr-state-text' }, state.error),
            h('button', { type: 'button', className: 'rr-button', onClick: refresh }, t('retry'))))
      }

      if (!payload || !payload.ok) {
        return h('section', { className: 'rr-reports rr-monitor' },
          h('div', { className: 'rr-state' },
            h('div', { className: 'rr-state-title' }, t('monitorNoData')),
            h('div', { className: 'rr-state-text' }, payload && payload.error ? payload.error : t('monitorNoDataHint')),
            h('div', { className: 'rr-monitor-actions' },
              payload && payload.reportPath
                ? h('button', {
                  type: 'button',
                  className: 'rr-button',
                  onClick: () => openReport(payload.reportPath),
                }, t('monitorViewReport'))
                : null,
              h('button', { type: 'button', className: 'rr-button rr-button-quiet', onClick: refresh }, t('refresh')))))
      }

      const counts = payload.counts || {}
      const priceRows = Array.isArray(payload.price) ? payload.price : []
      const events = Array.isArray(payload.events) ? payload.events : []
      const pinnedSet = new Set(Array.isArray(pinned) ? pinned : [])
      /** The 标的 a monitor row belongs to, taken from its research link. */
      const targetDir = (row) => {
        const parts = String(row.researchPath || '').split('/')
        return parts.length > 2 ? parts[1] : ''
      }
      const isPinned = (row) => {
        const dir = targetDir(row)
        return Boolean((dir && pinnedSet.has(dir)) || pinnedSet.has(row.name) || pinnedSet.has(row.targetId))
      }
      const matchesZone = (row) => matches(row.name) || matches(row.targetId)
        || matches(row.zoneLabel) || matches(row.market)
      const matchesEvent = (row) => matches(row.name) || matches(row.targetId) || matches(row.title)

      const attention = priceRows.filter(row => row.status === 'TRIGGERED' || row.status === 'NEAR')
      // Default to the zones that matter; a search always looks at every zone.
      const attentionOnly = filter === 'auto' ? attention.length > 0 : filter === 'attention'
      const showAll = Boolean(needle) || !attentionOnly
      let visible = pinnedOnly ? priceRows.filter(isPinned) : (showAll ? priceRows : attention)
      visible = visible.filter(matchesZone)
      if (!pinnedOnly) {
        // Pinned 标的 first; the sort is stable, so the monitor's own order holds.
        visible = visible.slice().sort((a, b) => (isPinned(b) ? 1 : 0) - (isPinned(a) ? 1 : 0))
      }

      const eventRows = events.filter(matchesEvent)
      const shownEvents = eventRows.slice(0, MONITOR_EVENT_ROWS)
      const hiddenEvents = eventRows.length - shownEvents.length
      const sources = Array.isArray(payload.sources) ? payload.sources : []

      // How far the monitor run is behind today: the view answers "today", so a
      // run from an earlier day must say so instead of looking current.
      const staleDays = (() => {
        const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(payload.date || ''))
        if (!match) return 0
        const runAt = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
        const now = new Date()
        const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        const days = Math.round((midnight - runAt) / 86400000)
        return Number.isFinite(days) && days > 0 ? days : 0
      })()

      const head = h('div', { className: 'rr-monitor-head' },
        h('div', { className: 'rr-monitor-titleline' },
          h('h2', { className: 'rr-monitor-title' }, t('monitor')),
          payload.date
            ? h('span', { className: 'rr-monitor-date' },
              payload.date + (payload.timezone ? ' · ' + payload.timezone : ''))
            : null,
          payload.status
            ? h('span', {
              className: 'rr-status ' + (payload.status === 'OK' ? 'rr-status-success' : 'rr-status-warn'),
              title: payload.generatedAt ? t('generated') + ' ' + payload.generatedAt.slice(0, 16).replace('T', ' ') : undefined,
            }, payload.status)
            : null,
          staleDays
            ? h('span', {
              className: 'rr-status rr-status-warn',
              title: t('monitorStale') + ' ' + payload.date + ' · ' + t('refresh'),
            }, t('monitorStale') + ' ' + staleDays + ' ' + t('monitorDaysAgo'))
            : null,
        ),
        payload.summary ? h('div', { className: 'rr-monitor-summary' }, payload.summary) : null,
        h('div', { className: 'rr-monitor-disclaimer' }, t('monitorDisclaimer')),
        sources.length
          ? h('div', { className: 'rr-monitor-sources' },
            t('monitorSources') + '：' + sources.map(row => row.source + ' ' + row.status).join(' · '))
          : null,
        h('div', { className: 'rr-monitor-actions' },
          payload.reportPath
            ? h('button', {
              type: 'button',
              className: 'rr-button',
              onClick: () => openReport(payload.reportPath),
            }, t('monitorViewReport'))
            : null,
          h('button', {
            type: 'button',
            className: 'rr-button rr-button-quiet',
            onClick: refresh,
            disabled: state.status === 'refreshing',
          }, state.status === 'refreshing' ? t('refreshing') : t('refresh'))),
      )

      const priceCounts = needle
        ? h('span', { className: 'rr-monitor-counts' },
          h('span', { className: 'rr-status' }, t('monitorMatch') + ' ' + visible.length + ' / ' + priceRows.length))
        : h('span', { className: 'rr-monitor-counts' },
          h('span', { className: 'rr-status rr-status-error' }, t('monitorTriggered') + ' ' + (counts.triggered || 0)),
          h('span', { className: 'rr-status rr-status-warn' }, t('monitorNear') + ' ' + (counts.near || 0)),
        )

      const priceHead = h('div', { className: 'rr-monitor-cardhead' },
        h('h3', { className: 'rr-monitor-cardtitle' }, t('monitorPrice')),
        priceCounts,
        h('button', {
          type: 'button',
          className: 'rr-button rr-button-quiet' + (pinnedOnly ? ' rr-button-active' : ''),
          onClick: () => setPinnedOnly(value => !value),
          'aria-pressed': pinnedOnly ? 'true' : 'false',
        }, t('monitorPinnedOnly')),
        pinnedOnly
          ? null
          : h('button', {
            type: 'button',
            className: 'rr-button rr-button-quiet',
            onClick: () => setFilter(attentionOnly ? 'all' : 'attention'),
            disabled: Boolean(needle),
            title: needle ? t('monitorSearchAllHint') : undefined,
          }, attentionOnly ? t('monitorAll') + ' · ' + priceRows.length : t('monitorAttentionOnly')),
      )

      const priceTable = visible.length
        ? h('div', { className: 'rr-doc-tablewrap' },
          h('table', { className: 'rr-doc-table rr-monitor-table' },
            h('thead', null, h('tr', null,
              h('th', null, t('monitorTarget')),
              h('th', null, t('monitorMarket')),
              h('th', { className: 'rr-monitor-num' }, t('monitorCondition')),
              h('th', { className: 'rr-monitor-num' }, t('monitorPriceLabel')),
              h('th', { className: 'rr-monitor-num' }, t('monitorGap')),
              h('th', null, t('monitorStatus')),
            )),
            h('tbody', null, visible.map((row, rowIndex) => h('tr', {
              key: row.targetId + '|' + row.name + '|' + row.zoneLabel + '|' + row.market + '|' + rowIndex,
              title: [row.note, row.whyNow].filter(Boolean).join('\n'),
            },
            h('td', null,
              h('div', { className: 'rr-monitor-target' },
                isPinned(row) ? h('span', { className: 'rr-monitor-pinned', title: t('pinHint') }, pinIcon(true)) : null,
                row.priority
                  ? h('span', { className: 'rr-monitor-priority', title: t('monitorLegend') }, row.priority)
                  : null,
                row.researchPath
                  ? h('button', {
                    type: 'button',
                    className: 'rr-link-button',
                    onClick: () => openReport(row.researchPath),
                    title: row.researchDate ? t('monitorResearchDate') + ' ' + row.researchDate : undefined,
                  }, row.name)
                  : h('span', null, row.name),
              ),
              row.zoneLabel || row.researchDate
                ? h('div', { className: 'rr-monitor-zone' },
                  [
                    row.zoneLabel,
                    row.researchDate ? t('monitorResearchDate') + ' ' + row.researchDate : '',
                  ].filter(Boolean).join(' · '))
                : null,
            ),
            h('td', null, row.market || '-'),
            h('td', { className: 'rr-monitor-num' }, row.condition || '-'),
            h('td', { className: 'rr-monitor-num' }, row.price || '-'),
            h('td', { className: 'rr-monitor-num' }, row.gap || '-'),
            h('td', null, statusChip(t, row.status)),
            )))))
        : h('div', { className: 'rr-hint' }, needle ? t('monitorEmptySearch') : t('monitorEmpty'))

      const eventCounts = needle
        ? h('span', { className: 'rr-monitor-counts' },
          h('span', { className: 'rr-status' }, t('monitorMatch') + ' ' + eventRows.length + ' / ' + events.length))
        : h('span', { className: 'rr-monitor-counts' },
          counts.today ? h('span', { className: 'rr-status rr-status-warn' }, t('monitorToday') + ' ' + counts.today) : null,
          counts.overdue ? h('span', { className: 'rr-status rr-status-error' }, t('monitorOverdue') + ' ' + counts.overdue) : null,
          counts.review ? h('span', { className: 'rr-status rr-status-brand' }, t('monitorReview') + ' ' + counts.review) : null,
          h('span', { className: 'rr-status' }, t('monitorEventsTotal') + ' ' + events.length),
        )

      const eventsHead = h('div', { className: 'rr-monitor-cardhead' },
        h('h3', { className: 'rr-monitor-cardtitle' }, t('monitorEvents')),
        eventCounts,
      )

      const eventsList = shownEvents.length
        ? h('ul', { className: 'rr-monitor-events' },
          shownEvents.map((row, rowIndex) => h('li', {
            key: row.targetId + '|' + row.title + '|' + row.status + '|' + rowIndex,
            className: 'rr-monitor-event',
            title: row.title,
          },
          statusChip(t, row.status),
          h('span', { className: 'rr-monitor-kind' },
            row.kind === 'event' ? t('monitorKindOther') : t('monitorKindDisclosure')),
          row.researchPath
            ? h('button', {
              type: 'button',
              className: 'rr-link-button rr-monitor-event-name',
              onClick: () => openReport(row.researchPath),
            }, row.name)
            : h('span', { className: 'rr-monitor-event-name' }, row.name),
          h('span', { className: 'rr-monitor-event-title' }, row.title),
          row.date ? h('span', { className: 'rr-monitor-event-date' }, row.date) : null,
          row.url
            ? h('a', {
              className: 'rr-doc-link rr-monitor-event-link',
              href: row.url,
              target: '_blank',
              rel: 'noreferrer noopener',
              title: t('monitorOpenAnnouncement'),
            }, '↗')
            : null,
          )))
        : h('div', { className: 'rr-hint' }, needle ? t('monitorEmptySearch') : t('monitorEmpty'))

      const moreLine = hiddenEvents > 0
        ? (payload.reportPath
          ? h('button', {
            type: 'button',
            className: 'rr-link-button rr-monitor-more',
            onClick: () => openReport(payload.reportPath),
          }, t('monitorMoreEvents').replace('{n}', String(hiddenEvents)))
          : h('div', { className: 'rr-hint' }, t('monitorMoreEvents').replace('{n}', String(hiddenEvents))))
        : null

      return h('section', { className: 'rr-reports rr-monitor', 'aria-label': t('monitor') },
        head,
        h('div', { className: 'rr-monitor-card' },
          priceHead,
          h('div', { className: 'rr-monitor-legend' }, t('monitorLegend')),
          priceTable),
        h('div', { className: 'rr-monitor-card' }, eventsHead, eventsList, moreLine),
      )
    }

    const EMPTY_PREFS = { version: 1, buckets: {} }

    /** Read pins and ordering once, then keep the panel's copy authoritative. */
    function useViewPrefs() {
      const [prefs, setPrefs] = React.useState(EMPTY_PREFS)
      const [save, setSave] = React.useState({ status: 'idle', error: '', at: 0 })
      const [loadError, setLoadError] = React.useState('')
      const [nonce, setNonce] = React.useState(0)
      const timer = React.useRef(null)
      const alive = React.useRef(true)
      /** A pin or drag before the first read lands wins over the stored copy. */
      const touched = React.useRef(false)

      React.useEffect(() => {
        alive.current = true
        const controller = new AbortController()
        fetch(STATE_URL, { cache: 'no-store', signal: controller.signal, headers: { accept: 'application/json' } })
          .then(async (response) => {
            if (!response.ok) throw new Error('HTTP ' + response.status)
            const payload = await response.json()
            if (payload && payload.broken) throw new Error('state file is unreadable')
            return payload && payload.buckets ? { version: 1, buckets: payload.buckets } : EMPTY_PREFS
          })
          .then((payload) => {
            if (!alive.current || touched.current) return
            setPrefs(payload)
            setLoadError('')
          })
          .catch((error) => {
            if (!alive.current) return
            setLoadError(error && error.message ? error.message : String(error))
          })
        // `nonce` re-runs this read when the user retries from the notice.
        return () => {
          alive.current = false
          controller.abort()
        }
      }, [nonce])

      const flush = React.useCallback((next) => {
        setSave({ status: 'saving', error: '', at: 0 })
        fetch(STATE_URL, {
          method: 'POST',
          headers: { 'content-type': 'application/json', accept: 'application/json' },
          body: JSON.stringify({ version: 1, buckets: next.buckets }),
        })
          .then(async (response) => {
            if (!response.ok) {
              const payload = await response.json().catch(() => null)
              throw new Error((payload && payload.error) || 'HTTP ' + response.status)
            }
            if (!alive.current) return
            setSave({ status: 'saved', error: '', at: Date.now() })
            setLoadError('')
          })
          .catch((error) => {
            if (!alive.current) return
            setSave({ status: 'error', error: error && error.message ? error.message : String(error), at: 0 })
          })
      }, [])

      const update = React.useCallback((next) => {
        touched.current = true
        setPrefs(next)
        if (timer.current) clearTimeout(timer.current)
        timer.current = setTimeout(() => {
          timer.current = null
          flush(next)
        }, SAVE_DELAY)
      }, [flush])

      React.useEffect(() => () => {
        if (timer.current) clearTimeout(timer.current)
      }, [])

      const reload = React.useCallback(() => setNonce(n => n + 1), [])
      return { prefs, update, save, loadError, reload }
    }

    /** One report, read from the Host half and parsed there into a block tree. */
    function useReportDoc(t, path) {
      const [doc, setDoc] = React.useState({ status: 'idle', path: '', payload: null, error: '' })
      const [nonce, setNonce] = React.useState(0)

      React.useEffect(() => {
        if (!path) {
          setDoc({ status: 'idle', path: '', payload: null, error: '' })
          return undefined
        }
        const controller = new AbortController()
        let alive = true
        setDoc(previous => (previous.path === path && previous.payload
          ? { ...previous, status: 'ready', error: '' }
          : { status: 'loading', path, payload: null, error: '' }))
        fetch(REPORT_URL + '?path=' + encodeURIComponent(path), {
          cache: 'no-store',
          signal: controller.signal,
          headers: { accept: 'application/json' },
        })
          .then(async (response) => {
            const payload = await response.json().catch(() => null)
            if (!response.ok) throw new Error((payload && payload.error) || 'HTTP ' + response.status)
            if (!payload || !Array.isArray(payload.blocks)) throw new Error(t('readFailed'))
            return payload
          })
          .then((payload) => {
            if (alive) setDoc({ status: 'ready', path, payload, error: '' })
          })
          .catch((error) => {
            if (!alive || (error && error.name === 'AbortError')) return
            setDoc({ status: 'error', path, payload: null, error: error && error.message ? error.message : String(error) })
          })
        return () => {
          alive = false
          controller.abort()
        }
      }, [path, nonce, t])

      const retry = React.useCallback(() => setNonce(n => n + 1), [])
      return { doc, retry }
    }

    function GroupRow(props) {
      const {
        group, drag, dropHint, onSelect, onTogglePin, onMoveByKeyboard, onOpenMenu,
        onDragStart, onDragEnd, onDragOver, onDropRow, t,
      } = props
      const pinned = Boolean(group.pinned)
      const dragging = drag && drag.name === group.name
      let dropClass = ''
      if (dropHint && dropHint.name === group.name && drag && drag.name !== group.name) {
        dropClass = dropHint.side === 'before' ? ' rr-drop-before' : ' rr-drop-after'
      }
      const className = 'rr-group'
        + (dragging ? ' rr-dragging' : '')
        + (pinned ? ' is-pinned' : '')
        + dropClass

      return h('div', {
        className,
        role: 'button',
        tabIndex: 0,
        draggable: props.canDrag,
        'aria-current': props.active ? 'true' : 'false',
        'aria-label': group.name
          + (pinned ? ', ' + t('pinHint') : '')
          + ', ' + group.shown.length + ' ' + t('reports'),
        title: (group.ticker ? group.ticker + ' · ' : '') + group.name
          + (pinned ? ' · ' + t('pinHint') : '')
          + ' · ' + t('rowMenuHint'),
        'aria-keyshortcuts': 'Alt+ArrowUp Alt+ArrowDown',
        'aria-haspopup': 'menu',
        onClick: () => onSelect(group.name),
        onContextMenu: (event) => {
          event.preventDefault()
          event.stopPropagation()
          onOpenMenu(event, group)
        },
        onKeyDown: (event) => {
          // The pin button is a real button inside this row; its own key events
          // must not also select the row.
          if (event.target !== event.currentTarget) return
          if (event.key === 'ContextMenu' || (event.shiftKey && event.key === 'F10')) {
            event.preventDefault()
            onOpenMenu(event, group)
            return
          }
          if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
            event.preventDefault()
            onMoveByKeyboard(group, event.key === 'ArrowUp' ? -1 : 1)
            return
          }
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            onSelect(group.name)
          }
        },
        onDragStart: (event) => onDragStart(event, group),
        onDragEnd,
        onDragOver: (event) => onDragOver(event, group),
        onDrop: (event) => onDropRow(event, group),
      },
      h('span', { className: 'rr-grip', 'aria-hidden': true }, '⠿'),
      h('span', { className: 'rr-group-name' }, group.name),
      h('button', {
        type: 'button',
        className: 'rr-pin',
        'aria-pressed': pinned ? 'true' : 'false',
        'aria-label': pinned ? t('unpin') : t('pin'),
        title: pinned ? t('unpin') : t('pin'),
        onClick: (event) => {
          event.stopPropagation()
          onTogglePin(group)
        },
      }, pinIcon(pinned)),
      h('span', {
        className: 'rr-group-count' + (group.shown.length === 0 && group.hidden ? ' rr-group-count-hidden' : ''),
        title: group.hidden ? group.hidden + ' ' + t('hiddenDrafts') : undefined,
      }, String(group.shown.length)))
    }

    /** Pinned state glyph: a filled pin when pinned, an outline when not. */
    function pinIcon(pinned) {
      return h('svg', {
        width: 13,
        height: 13,
        viewBox: '0 0 24 24',
        fill: pinned ? 'currentColor' : 'none',
        stroke: 'currentColor',
        strokeWidth: 1.7,
        strokeLinejoin: 'round',
        'aria-hidden': true,
        style: { display: 'block' },
      },
      h('path', { d: 'M9 3.6h6l-.7 5.1 3.2 3.2v1.6H6.5v-1.6l3.2-3.2z' }),
      h('path', { d: 'M12 13.5V20', strokeLinecap: 'round' }))
    }

    function Panel(props) {
      const t = props && props.t ? props.t : (key) => ZH[key] || key
      const { state, refresh } = useReportData()
      const { prefs, update: updatePrefs, save: saveState, loadError, reload: reloadPrefs } = useViewPrefs()
      const [query, setQuery] = React.useState('')
      const [showDrafts, setShowDrafts] = React.useState(false)
      const [selected, setSelected] = React.useState('')
      const [pane, setPane] = React.useState('reports')
      const [docStack, setDocStack] = React.useState([])
      const [copyState, setCopyState] = React.useState({ path: '', ok: true })
      const [toast, setToast] = React.useState('')
      const [resetArmed, setResetArmed] = React.useState(false)
      const [drag, setDrag] = React.useState(null)
      const [dropHint, setDropHint] = React.useState(null)
      const [menu, setMenu] = React.useState(null)
      const menuRef = React.useRef(null)
      const copyTimer = React.useRef(null)
      const toastTimer = React.useRef(null)
      const resetTimer = React.useRef(null)
      const navRef = React.useRef(null)
      const dragScroll = React.useRef({ dir: 0, timer: null })
      const skipSaveToast = React.useRef(false)
      const docScroll = React.useRef(null)
      const scrollMemory = React.useRef(new Map())
      const [coarsePointer] = React.useState(() => {
        if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
        try {
          return window.matchMedia('(hover: none)').matches
        } catch {
          return false
        }
      })
      const docPath = docStack.length ? docStack[docStack.length - 1] : ''
      const savedAt = saveState.at || 0

      const { doc, retry: retryDoc } = useReportDoc(t, docPath)
      const { state: monitorState, refresh: refreshMonitor } = useMonitorData()

      /** Remember where each report was left, so 「返回上一篇」 lands there. */
      React.useEffect(() => {
        const node = docScroll.current
        if (!node || doc.status !== 'ready') return
        node.scrollTop = scrollMemory.current.get(docPath) || 0
      }, [docPath, doc.status])

      const stopDragScroll = React.useCallback(() => {
        dragScroll.current.dir = 0
        if (dragScroll.current.timer) {
          clearInterval(dragScroll.current.timer)
          dragScroll.current.timer = null
        }
      }, [])

      /** Start the edge scroller; it keeps running until the drag ends. */
      const pumpDragScroll = React.useCallback(() => {
        if (dragScroll.current.timer) return
        dragScroll.current.timer = setInterval(() => {
          const nav = navRef.current
          if (!nav || !dragScroll.current.dir) return
          nav.scrollTop += dragScroll.current.dir
        }, 16)
      }, [])

      React.useEffect(() => () => {
        if (copyTimer.current) clearTimeout(copyTimer.current)
        if (toastTimer.current) clearTimeout(toastTimer.current)
        if (resetTimer.current) clearTimeout(resetTimer.current)
        stopDragScroll()
      }, [stopDragScroll])

      /** Escape steps out of the reader, or leaves the monitor view. */
      React.useEffect(() => {
        if (!docPath && pane !== 'monitor') return undefined
        const onKeyDown = (event) => {
          if (event.key !== 'Escape') return
          if (docPath) {
            setDocStack(previous => (previous.length > 1 ? previous.slice(0, -1) : []))
            return
          }
          setPane('reports')
        }
        window.addEventListener('keydown', onKeyDown)
        return () => window.removeEventListener('keydown', onKeyDown)
      }, [docPath, pane])

      const view = React.useMemo(() => buildView(state.data, showDrafts), [state.data, showDrafts])
      const needle = query.trim().toLowerCase()
      const sections = React.useMemo(() => sectionsOf(view.groups, needle, prefs), [view, needle, prefs])

      /** A report opened through an in-tree link moves the highlight to its own 标的. */
      React.useEffect(() => {
        const group = doc.payload && doc.payload.group
        if (group) setSelected(previous => (previous === group ? previous : group))
      }, [doc.payload])

      const active = React.useMemo(() => {
        const flat = []
        for (const section of sections) for (const group of section.groups) flat.push(group)
        if (!flat.length) return null
        return flat.find(group => group.name === selected) || flat[0]
      }, [sections, selected])

      const openDoc = React.useCallback((path) => {
        if (!path) return
        setDocStack(previous => (previous[previous.length - 1] === path ? previous : previous.concat([String(path)])))
      }, [])

      /** Leave the reader entirely, back to the report list of the active 标的. */
      const closeDoc = React.useCallback(() => setDocStack([]), [])

      /** Toggle the monitor pane; leaving it also leaves any open report. */
      const toggleMonitor = React.useCallback(() => {
        setDocStack([])
        setPane(current => (current === 'monitor' ? 'reports' : 'monitor'))
      }, [])

      /** Step back one report when the reader was entered through an in-report link. */
      const backDoc = React.useCallback(() => {
        setDocStack(previous => (previous.length > 1 ? previous.slice(0, -1) : []))
      }, [])

      const showToast = React.useCallback((message) => {
        setToast(message)
        if (toastTimer.current) clearTimeout(toastTimer.current)
        toastTimer.current = setTimeout(() => setToast(''), 2200)
      }, [])

      const copyPath = React.useCallback((path) => {
        const nav = typeof navigator === 'undefined' ? null : navigator
        const settle = (ok) => {
          setCopyState({ path, ok })
          if (copyTimer.current) clearTimeout(copyTimer.current)
          copyTimer.current = setTimeout(() => setCopyState({ path: '', ok: true }), 1600)
        }
        if (!nav || !nav.clipboard || !nav.clipboard.writeText) {
          settle(false)
          return
        }
        nav.clipboard.writeText(path).then(() => settle(true)).catch(() => settle(false))
      }, [])

      /** The category's saved manual order, without materialising one. */
      const savedOrder = React.useCallback((bucket) => {
        const saved = prefs.buckets ? prefs.buckets[bucket] : undefined
        return saved && Array.isArray(saved.order) ? saved.order.slice() : []
      }, [prefs])

      /** Persist one bucket's pin list and manual order. */
      const applyLists = React.useCallback((bucket, lists) => {
        const buckets = { ...prefs.buckets }
        if (!lists.pinned.length && !lists.rest.length) delete buckets[bucket]
        else buckets[bucket] = { pins: lists.pinned, order: lists.rest }
        updatePrefs({ version: 1, buckets })
      }, [prefs, updatePrefs])

      const togglePin = React.useCallback((group) => {
        const bucket = group.bucket
        const saved = (prefs.buckets && prefs.buckets[bucket]) || {}
        const pins = Array.isArray(saved.pins) ? saved.pins.filter(Boolean) : []
        const order = Array.isArray(saved.order) ? saved.order.filter(Boolean) : []
        applyLists(bucket, togglePinLists(pins, order, group.name, pins.includes(group.name)))
      }, [applyLists, prefs])

      /**
       * Keyboard reordering: move one row inside its own zone. Disabled while a
       * search narrows the list, for the same reason dragging is: the neighbour
       * it would swap with is not on screen.
       */
      const moveByKeyboard = React.useCallback((group, delta) => {
        if (needle) return
        const lists = bucketLists(group.bucket, view.groups, prefs)
        const pinned = Boolean(group.pinned)
        const list = pinned ? lists.pinned : lists.rest
        const from = list.indexOf(group.name)
        const to = from + delta
        if (from < 0 || to < 0 || to >= list.length) return
        const next = list.slice()
        next.splice(from, 1)
        next.splice(to, 0, group.name)
        applyLists(group.bucket, pinned
          ? { pinned: next, rest: savedOrder(group.bucket) }
          : { pinned: lists.pinned, rest: next })
      }, [applyLists, needle, prefs, savedOrder, view.groups])

      const resetOrder = React.useCallback(() => {
        if (!resetArmed) {
          setResetArmed(true)
          if (resetTimer.current) clearTimeout(resetTimer.current)
          resetTimer.current = setTimeout(() => setResetArmed(false), 4000)
          return
        }
        if (resetTimer.current) clearTimeout(resetTimer.current)
        setResetArmed(false)
        skipSaveToast.current = true
        updatePrefs({ version: 1, buckets: {} })
        showToast(t('orderReset'))
      }, [resetArmed, showToast, t, updatePrefs])

      const canDrag = !needle && !docPath

      const onDragStart = React.useCallback((event, group) => {
        if (!canDrag) return
        setDrag({ name: group.name, bucket: group.bucket })
        setDropHint(null)
        try {
          event.dataTransfer.effectAllowed = 'move'
          event.dataTransfer.setData('text/plain', group.name)
        } catch {}
      }, [canDrag])

      const onDragEnd = React.useCallback(() => {
        stopDragScroll()
        setDrag(null)
        setDropHint(null)
      }, [stopDragScroll])

      const onDragOver = React.useCallback((event, group) => {
        if (!drag || drag.bucket !== group.bucket) return
        event.preventDefault()
        try {
          event.dataTransfer.dropEffect = 'move'
        } catch {}
        // Long categories scroll while dragging: HTML5 drag never scrolls the
        // container, and its event cadence is too irregular to drive the motion.
        const nav = navRef.current
        if (nav) {
          const box = nav.getBoundingClientRect()
          const edge = 36
          dragScroll.current.dir = event.clientY < box.top + edge
            ? -14
            : event.clientY > box.bottom - edge
              ? 14
              : 0
          if (dragScroll.current.dir) pumpDragScroll()
        }
        const rect = event.currentTarget.getBoundingClientRect()
        const side = event.clientY > rect.top + rect.height / 2 ? 'after' : 'before'
        const zone = group.pinned ? 'pinned' : 'rest'
        setDropHint(previous => (previous
          && previous.name === group.name
          && previous.side === side
          && previous.zone === zone
          ? previous
          : { name: group.name, side, zone, bucket: group.bucket }))
      }, [drag, pumpDragScroll])

      const onDropRow = React.useCallback((event, group) => {
        if (!drag || drag.bucket !== group.bucket) return
        event.preventDefault()
        const rect = event.currentTarget.getBoundingClientRect()
        const after = dropHint && dropHint.name === group.name
          ? dropHint.side === 'after'
          : event.clientY > rect.top + rect.height / 2
        if (drag.name === group.name) {
          setDrag(null)
          setDropHint(null)
          return
        }
        const lists = bucketLists(group.bucket, view.groups, prefs)
        const fromPinned = lists.pinned.includes(drag.name)
        const toPinned = Boolean(group.pinned)
        if (fromPinned === toPinned) {
          const list = fromPinned ? lists.pinned : lists.rest
          const next = moveWithin(list, drag.name, group.name, after)
          // Reordering the pinned block must not freeze the unpinned ones: only
          // a drag inside the rest block creates a manual order.
          applyLists(group.bucket, fromPinned
            ? { pinned: next, rest: savedOrder(group.bucket) }
            : { pinned: lists.pinned, rest: next })
        } else if (fromPinned) {
          // Unpinning is an explicit position, so the rest list is materialised.
          const moved = moveAcross(lists.pinned, lists.rest, drag.name, group.name, after)
          applyLists(group.bucket, { pinned: moved.source, rest: moved.target })
        } else {
          const moved = moveAcross(lists.rest, lists.pinned, drag.name, group.name, after)
          applyLists(group.bucket, { pinned: moved.target, rest: savedOrder(group.bucket).filter(name => name !== drag.name) })
        }
        stopDragScroll()
        setDrag(null)
        setDropHint(null)
      }, [applyLists, drag, dropHint, prefs, savedOrder, stopDragScroll, view.groups])

      /** Right-click (or ContextMenu / Shift+F10) opens the 标的 actions. */
      const openMenu = React.useCallback((event, group) => {
        const rect = event.currentTarget.getBoundingClientRect()
        const fromKeyboard = event.type === 'keydown'
        menuAnchor.current = event.currentTarget
        setMenu({
          name: group.name,
          bucket: group.bucket,
          pinned: Boolean(group.pinned),
          x: fromKeyboard ? rect.left + 6 : event.clientX,
          y: fromKeyboard ? rect.bottom - 4 : event.clientY,
        })
        setDropHint(null)
      }, [])

      const menuAnchor = React.useRef(null)
      const closeMenu = React.useCallback((restoreFocus) => {
        setMenu(null)
        if (restoreFocus !== false && menuAnchor.current && menuAnchor.current.focus) {
          try {
            menuAnchor.current.focus()
          } catch {}
        }
      }, [])

      /** Move one 标的 to either end of its own zone; pin state is untouched. */
      const moveToEdge = React.useCallback((group, edge) => {
        const lists = bucketLists(group.bucket, view.groups, prefs)
        const pinned = Boolean(group.pinned)
        const list = pinned ? lists.pinned : lists.rest
        const next = moveToListEdge(list, group.name, edge)
        if (next.join('\u0000') === list.join('\u0000')) return
        applyLists(group.bucket, pinned
          ? { pinned: next, rest: savedOrder(group.bucket) }
          : { pinned: lists.pinned, rest: next })
        showToast(edge === 'first' ? t('movedTop') : t('movedBottom'))
      }, [applyLists, prefs, savedOrder, showToast, t, view.groups])

      const metaBits = []
      if (view.groups.length) metaBits.push(count(view.groups.length) + ' ' + t('groups'))
      if (view.visibleReports) metaBits.push(count(view.visibleReports) + ' ' + t('reports'))
      if (view.latest) metaBits.push(t('latest') + ' ' + view.latest)
      if (view.hiddenDrafts) metaBits.push(count(view.hiddenDrafts) + ' ' + t('drafts'))

      React.useEffect(() => {
        if (!menu) return undefined
        const onPointerDown = (event) => {
          if (menuRef.current && menuRef.current.contains(event.target)) return
          closeMenu(false)
        }
        const onKeyDown = (event) => {
          if (event.key !== 'Escape') return
          // Capture phase: closing the menu must not also step out of the reader.
          event.preventDefault()
          event.stopPropagation()
          closeMenu(true)
        }
        const onViewportChange = () => closeMenu(false)
        document.addEventListener('mousedown', onPointerDown, true)
        document.addEventListener('keydown', onKeyDown, true)
        window.addEventListener('scroll', onViewportChange, true)
        window.addEventListener('resize', onViewportChange)
        return () => {
          document.removeEventListener('mousedown', onPointerDown, true)
          document.removeEventListener('keydown', onKeyDown, true)
          window.removeEventListener('scroll', onViewportChange, true)
          window.removeEventListener('resize', onViewportChange)
        }
      }, [menu, closeMenu])

      /** Confirm a landed write once, so pinning and dragging show a result. */
      React.useEffect(() => {
        if (!savedAt) return
        if (skipSaveToast.current) {
          skipSaveToast.current = false
          return
        }
        showToast(t('orderSaved'))
      }, [savedAt, showToast, t])

      const hasPrefs = Object.keys(prefs.buckets || {}).length > 0

      const header = h('header', { className: 'rr-header' },
        h('div', { className: 'rr-titleline' },
          h('h1', { className: 'rr-title' }, t('title')),
          h('span', { className: 'rr-subtitle' }, t('subtitle')),
          h('span', { className: 'rr-meta' }, metaBits.join(' · ')),
        ),
        h('div', { className: 'rr-toolbar' },
          h('input', {
            className: 'rr-search',
            type: 'search',
            value: query,
            placeholder: t('search'),
            'aria-label': t('search'),
            onChange: event => setQuery(event.currentTarget.value),
          }),
          h('button', {
            type: 'button',
            className: 'rr-button' + (pane === 'monitor' ? ' rr-button-active' : ''),
            onClick: toggleMonitor,
            title: t('monitorHint'),
            'aria-pressed': pane === 'monitor' ? 'true' : 'false',
          },
          pane === 'monitor' ? t('backToReports') : t('monitor'),
          monitorState.data && monitorState.data.ok
            ? h('span', { className: 'rr-monitor-counts rr-monitor-counts-inline' },
              h('span', { className: 'rr-status rr-status-error' },
                t('monitorTriggered') + ' ' + (monitorState.data.counts.triggered || 0)),
              h('span', { className: 'rr-status rr-status-warn' },
                t('monitorNear') + ' ' + (monitorState.data.counts.near || 0)))
            : null),
          h('label', { className: 'rr-toggle' },
            h('input', { type: 'checkbox', checked: showDrafts, onChange: event => setShowDrafts(event.currentTarget.checked) }),
            t('showDrafts'),
          ),
          hasPrefs
            ? h('button', {
              type: 'button',
              className: 'rr-button rr-button-quiet' + (resetArmed ? ' rr-button-danger' : ''),
              onClick: resetOrder,
              title: resetArmed ? t('resetConfirm') : t('resetOrder'),
            }, resetArmed ? t('resetConfirm') : t('resetOrder'))
            : null,
          h('button', {
            type: 'button',
            className: 'rr-button',
            onClick: refresh,
            disabled: state.status === 'loading' || state.status === 'refreshing',
          }, state.status === 'refreshing' ? t('refreshing') : t('refresh')),
        ),
      )

      const notices = []
      if (state.status === 'error' && state.data) {
        notices.push(h('div', { className: 'rr-notice', role: 'status', key: 'load' },
          h('span', { className: 'rr-notice-text' }, t('staleNote') + '：' + state.error),
          h('button', { type: 'button', className: 'rr-button', onClick: refresh }, t('retry')),
        ))
      }
      if (saveState.status === 'error') {
        notices.push(h('div', { className: 'rr-notice', role: 'status', key: 'save' },
          h('span', { className: 'rr-notice-text' }, t('saveFailed') + '：' + saveState.error),
        ))
      }
      if (loadError) {
        notices.push(h('div', { className: 'rr-notice', role: 'status', key: 'prefs' },
          h('span', { className: 'rr-notice-text' }, t('orderLoadFailed') + '：' + loadError),
          h('button', { type: 'button', className: 'rr-button', onClick: reloadPrefs }, t('retry')),
        ))
      }

      const shell = (children, overlay) => h('div', { className: 'rr-root' },
        h('style', null, CSS), header, notices, children, overlay || null)

      if (state.status === 'loading') {
        return shell(h('div', { className: 'rr-state' }, h('div', { className: 'rr-state-title' }, t('loading'))))
      }

      if (state.status === 'error' && !state.data) {
        return shell(h('div', { className: 'rr-state rr-error' },
          h('div', { className: 'rr-state-title' }, t('errorTitle')),
          h('div', { className: 'rr-state-text' }, state.error),
          h('button', { type: 'button', className: 'rr-button', onClick: refresh }, t('retry')),
        ))
      }

      const data = state.data || {}
      if (!view.groups.length && pane !== 'monitor') {
        return shell(h('div', { className: 'rr-state' },
          h('div', { className: 'rr-state-title' }, t('emptyDir')),
          h('div', { className: 'rr-state-text' }, t('emptyDirHint')),
          data.reportsDir ? h('div', { className: 'rr-state-path' }, data.reportsDir) : null,
          h('button', { type: 'button', className: 'rr-button', onClick: refresh }, t('refresh')),
        ))
      }

      if (!sections.length && pane !== 'monitor') {
        return shell(h('div', { className: 'rr-state' },
          h('div', { className: 'rr-state-title' }, t('emptySearch')),
          view.hiddenDrafts ? h('div', { className: 'rr-state-text' }, t('showThem')) : null,
        ))
      }

      const hasManualOrder = (bucket) => {
        const saved = prefs.buckets ? prefs.buckets[bucket] : undefined
        return Boolean(saved && Array.isArray(saved.order) && saved.order.length)
      }
      const hintText = coarsePointer
        ? t('reorderHintTouch')
        : needle
          ? t('reorderHintOffSearch')
          : docPath
            ? t('reorderHintOffReader')
            : t('reorderHint')

      const nav = h('div', { className: 'rr-nav' },
        h('nav', { className: 'rr-groups', 'aria-label': t('groups'), ref: navRef },
          sections.map(section => h('div', { className: 'rr-section', key: section.bucket },
            h('div', { className: 'rr-section-label' },
              bucketLabel(t, section.bucket),
              hasManualOrder(section.bucket)
                ? h('span', { className: 'rr-section-note', title: t('manualOrderHint') }, t('manualOrder'))
                : null,
            ),
            section.groups.map((group, position) => {
              const previous = position > 0 ? section.groups[position - 1] : null
              // A dashed rule marks where the pinned block ends inside this section.
              const separator = !group.pinned && previous && previous.pinned
                ? h('div', { className: 'rr-pin-sep' })
                : null
              return h(React.Fragment, { key: group.name },
                separator,
                h(GroupRow, {
                  group,
                  active: Boolean(active && active.name === group.name),
                  canDrag,
                  drag,
                  dropHint,
                  t,
                  onSelect: (name) => {
                    // Switching or re-picking a 标的 always returns to its list.
                    setPane('reports')
                    closeDoc()
                    setSelected(name)
                  },
                  onTogglePin: togglePin,
                  onMoveByKeyboard: moveByKeyboard,
                  onOpenMenu: openMenu,
                  onDragStart,
                  onDragEnd,
                  onDragOver,
                  onDropRow,
                }))
            }),
          )),
        ),
        h('div', { className: 'rr-groups-hint' }, hintText),
      )

      const docView = docPath
        ? h('div', {
          className: 'rr-reports rr-doc',
          key: docPath,
          ref: docScroll,
          onScroll: (event) => scrollMemory.current.set(docPath, event.currentTarget.scrollTop),
        },
        h('div', { className: 'rr-doc-head' },
          h('button', {
            type: 'button',
            className: 'rr-button rr-button-quiet',
            onClick: backDoc,
          }, '← ' + (docStack.length > 1
            ? t('backToPrevious')
            : (pane === 'monitor' ? t('backToMonitor') : t('backToList')))),
          h('div', { className: 'rr-doc-headline' },
            h('div', { className: 'rr-doc-title' }, doc.payload ? doc.payload.title : t('reading')),
            h('div', { className: 'rr-doc-meta' },
              [
                doc.payload && doc.payload.date ? doc.payload.date : '',
                doc.payload && doc.payload.type ? doc.payload.type : '',
                doc.payload && doc.payload.group ? doc.payload.group : '',
                docPath,
              ].filter(Boolean).join(' · ')),
          ),
          h('div', { className: 'rr-doc-actions' },
            h('button', {
              type: 'button',
              className: 'rr-button rr-button-quiet',
              onClick: () => copyPath(docPath),
              title: t('copyPath'),
            }, copyState.path === docPath ? (copyState.ok ? t('copied') : t('copyFailed')) : t('copyPath')),
          ),
        ),
        doc.status === 'loading' || doc.status === 'idle'
          ? h('div', { className: 'rr-state' }, h('div', { className: 'rr-state-title' }, t('reading')))
          : doc.status === 'error'
            ? h('div', { className: 'rr-state rr-error' },
              h('div', { className: 'rr-state-title' }, t('readFailed')),
              h('div', { className: 'rr-state-text' }, doc.error),
              h('button', { type: 'button', className: 'rr-button', onClick: retryDoc }, t('retry')),
            )
            : h('div', { className: 'rr-doc-body' },
              doc.payload && doc.payload.cut
                ? h('div', { className: 'rr-doc-note' },
                  t('docTruncated') + ' ' + bytes(doc.payload.shownBytes) + ' / ' + bytes(doc.payload.size))
                : null,
              doc.payload && doc.payload.truncated
                ? h('div', { className: 'rr-doc-note' }, t('docBlocksCut'))
                : null,
              doc.payload && doc.payload.blocks && doc.payload.blocks.length
                ? renderBlocks(doc.payload.blocks, { t, openDoc })
                : h('div', { className: 'rr-hint' }, t('docEmpty')),
            ),
        )
        : null

      const listView = h('section', { className: 'rr-reports', 'aria-label': active ? active.name : t('reports') },
        active
          ? h('div', null,
            h('div', { className: 'rr-reports-head' },
              h('span', { className: 'rr-reports-name' }, active.name),
              h('span', { className: 'rr-reports-meta' },
                active.shown.length + ' ' + t('reports')
                + (active.ticker ? ' · ' + active.ticker : '')
                + (active.latest ? ' · ' + t('latest') + ' ' + active.latest : ''),
              ),
            ),
            active.shown.length === 0
              ? h('div', { className: 'rr-hint' },
                active.hidden
                  ? active.hidden + ' ' + t('hiddenDrafts') + ' · ' + t('showThem')
                  : t('none'),
              )
              : h('ul', { className: 'rr-list' },
                active.shown.map(row => h('li', { key: row.path },
                  h('div', {
                    className: 'rr-item',
                    role: 'button',
                    tabIndex: 0,
                    title: t('openReport') + ' · ' + row.path,
                    'aria-label': [
                      isApprox(row) ? '~' + row.date : row.date,
                      row.title,
                      row.type,
                      row.draft ? t('showDrafts') : '',
                      t('openReport'),
                    ].filter(Boolean).join(', '),
                    onClick: () => openDoc(row.path),
                    onKeyDown: (event) => {
                      if (event.target !== event.currentTarget) return
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        openDoc(row.path)
                      }
                    },
                  },
                  h('span', {
                    className: 'rr-date' + (isApprox(row) ? ' rr-date-approx' : ''),
                    title: isApprox(row) ? t('approx') : row.dateSource,
                  }, (isApprox(row) ? '~' : '') + row.date),
                  h('span', { className: 'rr-item-title' }, row.title),
                  h('span', { className: 'rr-chip' }, row.type),
                  row.draft ? h('span', { className: 'rr-chip rr-chip-draft' }, '底稿') : null,
                  h('button', {
                    type: 'button',
                    className: 'rr-copy'
                      + (copyState.path === row.path ? (copyState.ok ? ' rr-copy-done' : ' rr-copy-failed') : ''),
                    title: t('copyPath'),
                    onClick: (event) => {
                      event.stopPropagation()
                      copyPath(row.path)
                    },
                  }, copyState.path === row.path ? (copyState.ok ? t('copied') : t('copyFailed')) : t('copyPath')),
                  )),
              )),
          )
          : h('div', { className: 'rr-hint' }, t('emptySelection')),
      )

      const menuView = (() => {
        if (!menu) return null
        const lists = bucketLists(menu.bucket, view.groups, prefs)
        const zone = menu.pinned ? lists.pinned : lists.rest
        const index = zone.indexOf(menu.name)
        const subject = { name: menu.name, bucket: menu.bucket, pinned: menu.pinned }
        const items = [
          {
            key: 'pin',
            label: menu.pinned ? t('unpin') : t('pin'),
            onRun: () => togglePin(subject),
          },
          {
            key: 'top',
            label: menu.pinned ? t('moveTopInPins') : t('moveTop'),
            disabled: index <= 0,
            onRun: () => moveToEdge(subject, 'first'),
          },
          {
            key: 'bottom',
            label: menu.pinned ? t('moveBottomInPins') : t('moveBottom'),
            disabled: index === zone.length - 1,
            onRun: () => moveToEdge(subject, 'last'),
          },
        ]
        const width = 196
        const height = items.length * 32 + 12
        const viewportWidth = typeof window === 'undefined' ? 1024 : window.innerWidth
        const viewportHeight = typeof window === 'undefined' ? 768 : window.innerHeight
        const left = Math.max(8, Math.min(menu.x, viewportWidth - width - 8))
        const top = Math.max(8, Math.min(menu.y, viewportHeight - height - 8))
        const runItem = (item) => {
          if (item.disabled) return
          item.onRun()
          closeMenu(true)
        }
        return h('div', {
          className: 'rr-menu',
          role: 'menu',
          'aria-label': t('menuLabel'),
          ref: menuRef,
          style: { left: left + 'px', top: top + 'px', minWidth: width + 'px' },
          onContextMenu: (event) => event.preventDefault(),
          onKeyDown: (event) => {
            if (event.key === 'Escape') {
              event.preventDefault()
              event.stopPropagation()
              closeMenu(true)
              return
            }
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
              event.preventDefault()
              const buttons = menuRef.current
                ? [...menuRef.current.querySelectorAll('[role="menuitem"]:not(:disabled)')]
                : []
              if (!buttons.length) return
              const current = buttons.indexOf(document.activeElement)
              const step = event.key === 'ArrowDown' ? 1 : -1
              buttons[(current + step + buttons.length) % buttons.length].focus()
              return
            }
            if (event.key === 'Tab') closeMenu(false)
          },
        },
        items.map((item, itemIndex) => h('button', {
          key: item.key,
          type: 'button',
          role: 'menuitem',
          className: 'rr-menu-item',
          disabled: Boolean(item.disabled),
          autoFocus: itemIndex === 0,
          onClick: () => runItem(item),
        }, item.label)))
      })()

      const note = h('div', { className: 'rr-note' },
        t('source'),
        data.reportsDir ? ' · ' + data.reportsDir : '',
        data.generatedAt ? ' · ' + t('generated') + ' ' + data.generatedAt.slice(11, 19) : '',
        view.hiddenDrafts ? ' · ' + count(view.hiddenDrafts) + ' ' + t('drafts') + '（' + t('showThem') + '）' : '',
        hasPrefs && saveState.status !== 'error' ? ' · ' + t('savedPins') : '',
        saveState.status === 'saving' ? ' · ' + t('orderSaving') : '',
        toast ? ' · ' + toast : '',
      )

      const pinnedNames = Object.values(prefs.buckets || {})
        .flatMap(bucket => (bucket && Array.isArray(bucket.pins) ? bucket.pins : []))
      const monitorPanel = pane === 'monitor'
        ? h(MonitorView, {
          t,
          state: monitorState,
          refresh: refreshMonitor,
          openReport: openDoc,
          needle,
          pinned: pinnedNames,
        })
        : null

      const content = docPath ? docView : (monitorPanel || listView)

      return shell(h('div', { className: 'rr-main' }, h('div', { className: 'rr-body' }, nav, content), note), menuView)
    }

    /** Sidebar entry glyph: a report sheet with ruled lines, drawn in the row's own color. */
    function PanelIcon(props) {
      const size = props && props.size ? props.size : 16
      return h('svg', {
        width: size,
        height: size,
        viewBox: '0 0 24 24',
        fill: 'none',
        'aria-hidden': true,
        style: { display: 'block' },
      },
      h('path', {
        d: 'M6.5 3.5h7.2L18 7.8v12.7H6.5z',
        stroke: 'currentColor',
        strokeWidth: 1.5,
        strokeLinejoin: 'round',
      }),
      h('path', {
        d: 'M13.4 3.7v4.4h4.4',
        stroke: 'currentColor',
        strokeWidth: 1.5,
        strokeLinejoin: 'round',
      }),
      h('path', {
        d: 'M9 12h6M9 15.2h6M9 8.9h2.3',
        stroke: 'currentColor',
        strokeWidth: 1.5,
        strokeLinecap: 'round',
      }))
    }

    return {
      inject: ['slots', 'locale'],
      apply(ctx) {
        ctx.effect(() => ctx.locale.register(NS, 'zh', ZH), NS + ': zh')
        ctx.effect(() => ctx.locale.register(NS, 'en', EN), NS + ': en')
        const t = ctx.locale.bind(NS)

        ctx.effect(() => ctx.slots.inject('main', () => ctx.slots.register({
          name: 'main',
          key: PANEL_ID,
          locale: NS,
          inject: () => ({ t }),
        }, Panel)), NS + ': main panel')

        ctx.effect(() => ctx.slots.inject('sidebar.panellist', () => ctx.slots.register({
          name: 'sidebar.panellist',
          id: PANEL_ID,
          order: 20,
          locale: NS,
          label: () => t('panel'),
        }, PanelIcon)), NS + ': sidebar entry')
      },
      /**
       * Pure ordering helpers, exposed for the package's Node unit test. They
       * take and return plain data, so the test never renders anything.
       */
      __internals: {
        buildView, orderBucket, bucketLists, sectionsOf,
        moveWithin, moveAcross, moveToListEdge, togglePinLists,
      },
    }
  },
})
