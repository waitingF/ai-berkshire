# 研究报告浏览（DSH 插件）

DeepSeek Harness 本地插件：把本项目 `reports/` 下的研究报告按标的汇总，时间降序展示；标的可置顶、可拖拽、也可用右键菜单排序，点开任意一篇即可在面板内阅读正文；面板另有一个「每日监控」视图，列出进入或接近价格区间的标的。

- Host 半 `index.js`：扫描 `reports/` 目录，发布目录数据、单篇报告正文、报告图片、置顶/排序偏好与每日监控摘要五条路由。
- Host 半 `markdown.js`：把一篇报告解析成可渲染的块树（可单测）。
- Client 半 `client.js`：在侧边栏注册「研究报告」面板，渲染标的列表、置顶/拖拽/右键菜单、阅读视图与每日监控视图。

安装：在 DSH 里 `plugin_manager install_bundle` 指向本目录，或 Settings → Plugins → Add plugin 选择本地目录。
报告目录通过 `cordis.patch.yml` 的 `config.reportsDir` 指定；置顶与排序偏好保存在
`~/.dsh/storages/research-reports/ui-state.json`（可用 `config.statePath` 改）。

功能、路由、边界与自测说明详见 [docs/DETAIL.md](docs/DETAIL.md)。
