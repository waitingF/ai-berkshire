export function compareResearchDates(left, right, sort) {
  if (sort === "default") return left.index - right.index;
  if (!left.date || !right.date) return (left.date ? -1 : right.date ? 1 : 0) || left.index - right.index;
  const comparison = left.date.localeCompare(right.date);
  return (sort === "newest" ? -comparison : comparison) || left.index - right.index;
}

export function matchesMonitorFilters(row, selectedMarkets, terms) {
  return selectedMarkets.has(row.market) && terms.every((term) => row.text.includes(term));
}

if (typeof document !== "undefined") {
  const marketNames = {
    A: "A股", H: "港股", US: "美股", KR: "韩国", JP: "日本", FR: "法国",
    UK: "英国", SE: "瑞典", NL: "荷兰", DE: "德国", AU: "澳大利亚", TW: "台湾",
  };

  const columnMenu = (header, id, accessibleName) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "monitor-column-button";
    button.setAttribute("aria-label", accessibleName);
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("popovertarget", id);
    const marker = document.createElement("span");
    marker.className = "monitor-column-marker";
    marker.setAttribute("aria-hidden", "true");
    button.append(header.textContent.trim(), marker);
    header.replaceChildren(button);
    header.setAttribute("scope", "col");

    const menu = document.createElement("div");
    menu.id = id;
    menu.className = "monitor-column-menu";
    menu.setAttribute("popover", "auto");
    menu.setAttribute("aria-label", accessibleName);
    document.body.append(menu);
    menu.addEventListener("toggle", () => {
      const open = menu.matches(":popover-open");
      button.setAttribute("aria-expanded", String(open));
      if (!open) return;
      menu.scrollTop = 0;
      const rect = button.getBoundingClientRect();
      menu.style.left = `${Math.max(16, Math.min(rect.left, innerWidth - menu.offsetWidth - 16))}px`;
      const below = innerHeight - rect.bottom - 24;
      const above = rect.top - 24;
      const opensBelow = menu.scrollHeight <= below || below >= above;
      menu.style.maxHeight = `${Math.max(80, Math.min(innerHeight * 0.65, opensBelow ? below : above))}px`;
      menu.style.top = `${opensBelow ? rect.bottom + 8 : Math.max(16, rect.top - menu.offsetHeight - 8)}px`;
    });
    document.addEventListener("scroll", (event) => {
      if (menu.matches(":popover-open") && !menu.contains(event.target)) menu.hidePopover();
    }, true);
    window.addEventListener("resize", () => {
      if (menu.matches(":popover-open")) menu.hidePopover();
    });
    return { button, menu, marker };
  };

  document.querySelectorAll("[data-monitor-table]").forEach((table, tableIndex) => {
    const headers = Array.from(table.querySelectorAll("thead th"));
    const columns = headers.map((cell) => cell.textContent.trim());
    const dateIndex = columns.indexOf("最新研究报告日期");
    const marketIndex = columns.indexOf("市场");
    const normalize = (value) => value.trim().toLocaleLowerCase("zh-CN");
    const rows = Array.from(table.querySelectorAll("tbody tr"), (row, index) => {
      const date = row.cells[dateIndex]?.textContent.trim() || "";
      return {
        row, index, date: /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : "",
        market: row.cells[marketIndex]?.textContent.trim() || "-",
        text: normalize(`${row.textContent} ${row.dataset.monitorAliases || ""}`),
      };
    });
    if (!rows.length) return;

    const markets = Array.from(new Set(rows.map((row) => row.market))).sort();
    let selected = new Set(markets);
    let sort = "default";
    const prefix = `monitor-${tableIndex + 1}`;
    const bar = document.createElement("div");
    bar.className = "monitor-filter";
    bar.innerHTML = `
      <label class="filter-label" for="${prefix}-search">搜索价格监控</label>
      <div class="monitor-search-row">
        <input id="${prefix}-search" data-monitor-search type="search" autocomplete="off"
          placeholder="输入简称、股票代码、市场或优先级，空格分隔多个条件"
          aria-describedby="${prefix}-status">
        <button type="button" class="monitor-reset">重置</button>
      </div>
      <p id="${prefix}-status" class="filter-status" role="status" aria-live="polite"></p>`;
    const input = bar.querySelector("input");
    const reset = bar.querySelector("button");
    const status = bar.querySelector("[role='status']");
    const empty = document.createElement("p");
    empty.className = "filter-empty";
    empty.hidden = true;
    empty.textContent = "没有匹配的监控记录，请调整搜索或市场筛选。";
    table.before(bar, empty);

    const dateMenu = dateIndex < 0 ? null : columnMenu(
      headers[dateIndex], `${prefix}-dates`, "按最新研究报告日期排序");
    const marketMenu = marketIndex < 0 ? null : columnMenu(
      headers[marketIndex], `${prefix}-markets`, "筛选市场");

    const update = () => {
      const terms = normalize(input.value).split(/\s+/).filter(Boolean);
      const ordered = [...rows];
      ordered.sort((left, right) => compareResearchDates(left, right, sort));
      let visible = 0;
      for (const entry of ordered) {
        const { row } = entry;
        row.hidden = !matchesMonitorFilters(entry, selected, terms);
        if (!row.hidden) {
          visible += 1;
          const number = row.querySelector(".monitor-row-number");
          if (number) number.textContent = String(visible);
        }
      }
      table.tBodies[0].append(...ordered.map(({ row }) => row));
      const filtered = terms.length > 0 || selected.size !== markets.length;
      status.textContent = filtered ? `显示 ${visible} / ${rows.length} 条` : `共 ${rows.length} 条`;
      if (sort !== "default") status.textContent += sort === "newest" ? " · 报告日期从新到旧" : " · 报告日期从旧到新";
      empty.hidden = visible !== 0;
      reset.disabled = !filtered && sort === "default" && input.value === "";
      if (dateMenu) {
        headers[dateIndex].setAttribute("aria-sort", {default: "none", newest: "descending", oldest: "ascending"}[sort]);
        dateMenu.marker.textContent = {default: "▾", newest: "↓", oldest: "↑"}[sort];
        for (const button of dateMenu.menu.querySelectorAll("button")) {
          button.setAttribute("aria-pressed", String(button.dataset.sort === sort));
        }
      }
      if (marketMenu) {
        marketMenu.marker.textContent = selected.size === markets.length ? "▾" : `${selected.size}/${markets.length} ▾`;
        marketMenu.button.dataset.active = String(selected.size !== markets.length);
        for (const checkbox of marketMenu.menu.querySelectorAll("input")) checkbox.checked = selected.has(checkbox.value);
      }
    };

    if (dateMenu) {
      for (const [value, label] of [["newest", "从新到旧"], ["oldest", "从旧到新"], ["default", "恢复默认顺序"]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.dataset.sort = value;
        button.addEventListener("click", () => {
          sort = value;
          update();
          dateMenu.menu.hidePopover();
          dateMenu.button.focus();
        });
        dateMenu.menu.append(button);
      }
    }
    if (marketMenu) {
      const actions = document.createElement("div");
      actions.className = "monitor-market-actions";
      for (const [label, values] of [["全选", markets], ["清空", []]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.addEventListener("click", () => { selected = new Set(values); update(); });
        actions.append(button);
      }
      const choices = document.createElement("div");
      choices.className = "monitor-market-choices";
      for (const market of markets) {
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = market;
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) selected.add(market);
          else selected.delete(market);
          update();
        });
        label.append(checkbox, marketNames[market] ? `${market} · ${marketNames[market]}` : market);
        choices.append(label);
      }
      marketMenu.menu.append(actions, choices);
    }
    input.addEventListener("input", update);
    reset.addEventListener("click", () => {
      input.value = "";
      sort = "default";
      selected = new Set(markets);
      update();
    });
    update();
  });
}
