(() => {
  "use strict";

  const data = window.observatoryData;
  const charts = window.observatoryCharts;
  const get = (id) => document.getElementById(id);
  const views = ["timeline", "financials", "policy", "archive"];
  const names = {
    governance: "Governance", financials: "Financials", policy: "Policy", technology: "Technology",
    documented: "Documented", attributed: "Attributed statement", scheduled: "Scheduled",
    rule: "Rule", disclosure: "Issuer disclosure", agency_action: "Agency announcement",
    oversight: "Congressional oversight", enforcement: "Investigative action",
    historical: "Historical", superseded: "Superseded", reported: "Reported", issued: "Issued",
    open: "Open", effective: "Effective", requested: "Requested", rescheduled: "Rescheduled", held: "Held", canceled: "Canceled",
    oral_history: "Oral history", founding: "Founding", cuda: "CUDA and research",
    engineering: "Engineering", leadership: "Leadership",
  };
  const columns = ["id", "event_date", "disclosed_on", "precision", "status", "category", "event", "claim_id", "primary_source_id"];
  const controls = {
    timeline: {q: "timeline-search", category: "timeline-category", status: "timeline-status", order: "timeline-order"},
    financials: {range: "financial-range", quarter: "financial-quarter"},
    policy: {q: "policy-search", kind: "policy-kind", status: "policy-status"},
    archive: {q: "archive-search", topic: "archive-topic", scenario: "benchmark-scenario"},
  };
  const state = {view: "timeline", params: new URLSearchParams()};
  const figureEvents = [["EV-012", "Resignation", "SRC-001"], ["EV-014", "Reinstatement", "SRC-002"]]
    .map(([id, title, source]) => ({event: data.timeline.find((row) => row.id === id), title,
      ref: data.sources[source].stable_ref.replace("SEC:", "SEC ")}));
  const number = new Intl.NumberFormat("en-US", {maximumFractionDigits: 2});
  const dates = new Intl.DateTimeFormat("en-US", {year: "numeric", month: "short", day: "numeric", timeZone: "UTC"});
  const monthDates = new Intl.DateTimeFormat("en-US", {year: "numeric", month: "short", timeZone: "UTC"});
  let visibleTimeline = [];
  let visibleQuarters = [];
  let selectedQuarter = 0;
  let feedbackTimer;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function link(text, target, className) {
    const node = element("a", className, text);
    node.href = target;
    return node;
  }

  function formattedDate(value) {
    if (!value) return "Not recorded";
    if (value.length === 4) return value;
    if (value.length === 7) return monthDates.format(new Date(value + "-01T00:00:00Z"));
    return dates.format(new Date(value + "T00:00:00Z"));
  }

  function route(view, params) {
    const query = params.toString();
    return `#${view}${query ? `?${query}` : ""}`;
  }

  function routeTo(view, key, value) {
    return route(view, new URLSearchParams([[key, value]]));
  }

  function fromLocation() {
    const hash = location.hash.slice(1);
    const split = hash.indexOf("?");
    const dest = split === -1 ? hash : hash.slice(0, split);
    const params = new URLSearchParams(split === -1 ? "" : hash.slice(split + 1));
    return {view: views.includes(dest) ? dest : "timeline", params, direct: views.includes(dest)};
  }

  function param(key) {
    return state.params.get(key) || "";
  }

  function replaceParams(key, value) {
    if (param(key) === value) return;
    if (value) state.params.set(key, value);
    else state.params.delete(key);
    try {
      history.replaceState(null, "", route(state.view, state.params));
    } catch {
      location.hash = route(state.view, state.params);
    }
  }

  function copyLink(view, key, value) {
    const hash = routeTo(view, key, value);
    // A local preview shares a record path without exposing the host's filesystem.
    const target = location.protocol === "file:" ? hash : new URL(hash, location.href).toString();
    const label = location.protocol === "file:" ? "Record path copied." : "Record link copied.";
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(target).then(() => feedback(label), () => copyFallback(target, label));
    } else {
      copyFallback(target, label);
    }
  }

  function copyFallback(target, label) {
    const field = element("textarea");
    field.value = target;
    field.setAttribute("aria-label", "Record link");
    field.style.position = "fixed";
    field.style.left = "-9999px";
    document.body.append(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    if (copied) feedback(label);
    else window.prompt("Copy this record link", target);
  }

  function share(view, key, value) {
    const wrap = element("div", "share-row");
    const button = element("button", "text-button", "Copy record link");
    button.type = "button";
    button.addEventListener("click", () => copyLink(view, key, value));
    wrap.append(link("Record permalink", routeTo(view, key, value)), button);
    return wrap;
  }

  function feedback(text) {
    const node = get("feedback");
    node.textContent = text;
    node.hidden = false;
    clearTimeout(feedbackTimer);
    feedbackTimer = setTimeout(() => { node.hidden = true; }, 3400);
  }

  function blobDownload(content, name) {
    const url = URL.createObjectURL(content);
    const a = link("", url);
    a.download = name;
    a.hidden = true;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 7000);
  }

  const downloadCsv = (text, name) => blobDownload(new Blob([text], {type: "text/csv;charset=utf-8"}), name);
  function downloadCanvas(canvas, name) {
    canvas.toBlob((blob) => {
      if (blob) blobDownload(blob, name);
      else feedback("Image export failed.");
    }, "image/png");
  }

  function escapeCell(value) {
    let text = String(value || "");
    if (/^[=+@-]/.test(text)) text = "'" + text;
    return /["\n,\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function csvForTimeline() {
    return [columns.join(","), ...visibleTimeline.map((row) => columns.map((key) => escapeCell(row[key])).join(","))]
      .join("\r\n") + "\r\n";
  }

  function pill(status) {
    return element("span", `pill ${status}`, names[status] || status);
  }

  function labeledDate(label, value) {
    const wrapper = element("span");
    wrapper.append(element("strong", "", label + " "));
    if (value) {
      const time = element("time", "", formattedDate(value));
      time.dateTime = value;
      wrapper.append(time);
    } else {
      wrapper.append("Not recorded");
    }
    return wrapper;
  }

  function evidenceList(claim, primary) {
    const list = element("ul", "source-list");
    const ordered = primary
      ? [...claim.evidence.filter((item) => item.source_id === primary),
        ...claim.evidence.filter((item) => item.source_id !== primary)]
      : claim.evidence;
    for (const item of ordered) {
      const source = data.sources[item.source_id];
      const row = element("li");
      row.append(link(source.title, source.url),
        element("span", "", [item.source_id, source.publisher, source.published_on, item.locator].filter(Boolean).join(" · ")));
      list.append(row);
    }
    return list;
  }

  function claimTerms(claimId) {
    const claim = data.claims[claimId];
    return [claim.statement, ...claim.evidence.flatMap((item) => {
      const source = data.sources[item.source_id];
      return [item.source_id, source.publisher, source.stable_ref, source.title];
    })].join(" ");
  }

  function tracked(name, query) {
    const terms = query.toLocaleLowerCase("en-US").trim().split(/\s+/).filter(Boolean);
    const haystack = name.toLocaleLowerCase("en-US");
    return terms.every((term) => haystack.includes(term));
  }

  function empty(text) {
    return element("p", "empty", text);
  }

  function updateCount(id, count, singular) {
    get(id).textContent = `${count} ${singular}${count === 1 ? "" : "s"}`;
  }

  function bindDetails(card, view, key, id) {
    card.dataset.recordId = id;
    card.open = param(key) === id;
    card.addEventListener("toggle", () => {
      if (!card.isConnected || state.view !== view) return;
      if (card.open) {
        replaceParams(key, id);
        for (const opened of card.parentElement.querySelectorAll("details[open]")) {
          if (opened !== card) opened.open = false;
        }
      } else if (param(key) === id) {
        replaceParams(key, "");
      }
    });
  }

  function timelineCard(row) {
    const claim = data.claims[row.claim_id];
    const card = element("details", "record");
    const title = element("summary");
    const meta = element("span", "meta-line");
    meta.append(pill(row.status), names[row.category], element("span", "code", row.id));
    const times = element("span", "record-dates");
    times.append(labeledDate(row.status === "scheduled" ? "Scheduled" : "Event", row.event_date),
      labeledDate("Disclosed", row.disclosed_on));
    title.append(meta, element("span", "record-title", row.event), times);
    const content = element("div", "record-detail");
    content.append(element("p", "", claim.statement), element("p", "method-note", claim.boundary),
      evidenceList(claim, row.primary_source_id), share("timeline", "event", row.id));
    card.append(title, content);
    bindDetails(card, "timeline", "event", row.id);
    return card;
  }

  function renderTimeline() {
    const q = param("q");
    const category = param("category");
    const status = param("status");
    visibleTimeline = data.timeline.filter((row) => (!category || row.category === category)
      && (!status || row.status === status)
      && tracked([row.id, row.event, row.event_date, row.disclosed_on, row.claim_id, names[row.category],
        claimTerms(row.claim_id)].join(" "), q));
    if (param("order") === "oldest") visibleTimeline.reverse();
    if (param("order") === "disclosed") {
      visibleTimeline.sort((a, b) => b.disclosed_on.localeCompare(a.disclosed_on) || b.event_date.localeCompare(a.event_date));
    }
    updateCount("timeline-count", visibleTimeline.length, "record");
    get("download-timeline").disabled = !visibleTimeline.length;
    const items = visibleTimeline.map(timelineCard);
    get("timeline-results").replaceChildren(...(items.length ? items : [empty("No records match these filters.")]));
  }

  function periodKey(row) {
    return `FY${row.fiscal_year}-Q${row.quarter}`;
  }

  function financialSources(row) {
    const holder = element("div", "inline-actions");
    const filing = data.sources[row.source_id];
    holder.append(link(filing.stable_ref.replace("SEC:", "EDGAR "), filing.url),
      link("Market table", data.sources[row.market_source_id].url));
    return holder;
  }

  function financialRow(row, current) {
    const tr = element("tr");
    if (current) tr.setAttribute("aria-current", "true");
    const label = element("th");
    label.scope = "row";
    const action = element("button", "text-button", charts.quarterLabel(row));
    action.type = "button";
    action.addEventListener("click", () => selectQuarter(periodKey(row), true));
    label.append(action);
    tr.append(label, element("td", "", formattedDate(row.period_end)));
    for (const field of ["revenue_usd_m", "data_center_usd_m", "gaap_rd_usd_m"]) {
      tr.append(element("td", "num", number.format(Number(row[field]))));
    }
    for (const metric of charts.metrics.slice(1)) tr.append(element("td", "num", metric.caption(metric.value(row))));
    const sources = element("td");
    sources.append(financialSources(row));
    tr.append(sources);
    return tr;
  }

  function paintCharts() {
    if (state.view !== "financials" || !visibleQuarters.length) return;
    for (const metric of charts.metrics) {
      const canvas = get(`chart-${metric.key}`);
      charts.drawChart(canvas, visibleQuarters, metric, selectedQuarter);
    }
  }

  function renderFinancials() {
    const range = param("range");
    visibleQuarters = range === "recent" ? data.financials.slice(-8)
      : range === "fy24" ? data.financials.filter((row) => +row.fiscal_year >= 2024) : data.financials;
    const sought = visibleQuarters.findIndex((row) => periodKey(row) === param("quarter"));
    selectedQuarter = sought < 0 ? visibleQuarters.length - 1 : sought;
    const selected = visibleQuarters[selectedQuarter];
    const select = get("financial-quarter");
    select.replaceChildren(...visibleQuarters.map((row) => {
      const op = element("option", "", charts.quarterLabel(row));
      op.value = periodKey(row);
      return op;
    }));
    select.value = periodKey(selected);
    for (const metric of charts.metrics) {
      const output = get(`metric-${metric.key}`);
      output.textContent = metric.caption(metric.value(selected));
      output.title = charts.quarterLabel(selected);
      get(`chart-${metric.key}`).setAttribute("aria-label",
        `${metric.label}, ${charts.quarterLabel(visibleQuarters[0])} to ${charts.quarterLabel(visibleQuarters.at(-1))}. `
        + `Selected ${charts.quarterLabel(selected)}: ${output.textContent}. See the source table for exact values.`);
    }
    const detail = element("article", "panel financial-detail");
    detail.append(element("h3", "", charts.quarterLabel(selected)),
      element("p", "detail-meta", `Period ended ${formattedDate(selected.period_end)} · Reported ${formattedDate(selected.reported_on)} · ${selected.claim_id}`),
      financialSources(selected));
    get("financial-detail").replaceChildren(detail);
    get("financial-table").replaceChildren(...visibleQuarters.map((row, i) => financialRow(row, i === selectedQuarter)));
    paintCharts();
  }

  function selectQuarter(id, scroll) {
    replaceParams("quarter", id);
    renderFinancials();
    if (scroll) {
      get("financial-quarter").focus({preventScroll: true});
      get("financial-detail").scrollIntoView({block: "center"});
    }
  }

  function policyCard(row) {
    const claim = data.claims[row.claim_id];
    const card = element("details", "record");
    const summary = element("summary");
    const meta = element("span", "meta-line");
    meta.append(pill(row.status), names[row.kind], row.jurisdiction, element("span", "code", row.id));
    const times = element("span", "record-dates");
    if (row.published_on) times.append(labeledDate("Published", row.published_on));
    if (row.effective_on) times.append(labeledDate("Effective", row.effective_on));
    if (row.next_on) {
      const nextLabel = {superseded: "Rescinded", effective: "Comments due", held: "Held", canceled: "Canceled",
        rescheduled: "Rescheduled for"};
      times.append(labeledDate(nextLabel[row.status] || "Scheduled", row.next_on));
    }
    summary.append(meta, element("span", "record-title", row.title), times);
    const details = element("div", "record-detail");
    details.append(element("p", "", row.summary));
    if (row.reference) details.append(element("p", "detail-meta", row.reference));
    const event = data.timeline.find((item) => item.id === row.event_id);
    details.append(evidenceList(claim, event?.primary_source_id), share("policy", "record", row.id));
    card.append(summary, details);
    bindDetails(card, "policy", "record", row.id);
    return card;
  }

  function renderPolicy() {
    const list = data.policies.filter((row) => (!param("kind") || row.kind === param("kind"))
      && (!param("status") || row.status === param("status"))
      && tracked([row.id, row.title, row.summary, row.reference, row.jurisdiction, row.published_on, row.next_on,
        names[row.kind], names[row.status], claimTerms(row.claim_id)].join(" "), param("q")));
    updateCount("policy-count", list.length, "record");
    const results = list.map(policyCard);
    get("policy-results").replaceChildren(...(results.length ? results : [empty("No policy records match these filters.")]));
  }

  function videoLink(row) {
    const url = new URL(data.sources[row.source_id].url);
    if (row.timestamp_seconds) url.searchParams.set("t", `${row.timestamp_seconds}s`);
    return url.toString();
  }

  function archiveCard(row) {
    const card = element("article", "panel archive-card");
    const meta = element("div", "meta-line");
    meta.append(element("span", "eyebrow", names[row.topic]), formattedDate(row.event_date));
    const text = row.timestamp_seconds ? "Open at " + row.locator.replace("Publisher chapter ", "") : "Open original source";
    card.append(meta, element("h3", "", row.title),
      element("p", "locator", `${row.presenter} · ${row.locator}`),
      element("p", "", row.summary), link(text, videoLink(row), "archive-link"));
    return card;
  }

  function renderArchive() {
    const list = data.archive.filter((row) => (!param("topic") || row.topic === param("topic"))
      && tracked([row.title, row.summary, row.presenter, row.locator, row.id].join(" "), param("q")));
    get("archive-count").textContent = `${list.length} ${list.length === 1 ? "entry" : "entries"}`;
    const cards = list.map(archiveCard);
    get("archive-results").replaceChildren(...(cards.length ? cards : [empty("No archive entries match these filters.")]));
    renderBenchmark();
  }

  function buildFeatures() {
    get("snapshot").append(` · As of ${formattedDate(data.snapshot.as_of)} · v${data.snapshot.version}`);
    for (const item of figureEvents) {
      const row = element("div", "featured-row");
      const effective = element("div");
      effective.append(link(item.title, routeTo("timeline", "event", item.event.id)),
        element("span", "featured-date", formattedDate(item.event.event_date)),
        element("span", "featured-caption", "Effective date"));
      const disclosed = element("div");
      disclosed.append(element("span", "featured-caption", "Public disclosure"),
        element("span", "featured-date", formattedDate(item.event.disclosed_on)));
      row.append(effective, disclosed);
      get("featured-events").append(row);
    }
    const recentRule = data.policies.find((item) => item.kind === "rule" && item.status === "effective");
    const featuredPolicy = [["POL-011", "Remote access"], [recentRule?.id, "Latest tracked rule"],
      ["POL-015", "Senate Banking Committee"]];
    const shown = new Set();
    featuredPolicy.forEach(([id, kicker]) => {
      const item = data.policies.find((row) => row.id === id);
      if (!item || shown.has(id)) return;
      shown.add(id);
      const card = element("article", "policy-feature");
      card.append(element("p", "eyebrow", kicker), element("h3", "", item.title),
        element("p", "", item.summary), link("Open evidence", routeTo("policy", "record", id)));
      get("policy-overview").append(card);
    });
    for (const item of data.milestones) {
      const record = element("li");
      const time = element("time", "", formattedDate(item.event_date));
      time.dateTime = item.event_date;
      const detail = element("div");
      detail.append(link(item.title, routeTo("timeline", "event", item.event_id)), element("p", "", item.summary));
      record.append(time, detail);
      get("milestones").append(record);
    }
    get("benchmark-source").href = data.sources[data.benchmarks[0].source_id].url;
  }

  function renderBenchmark() {
    const scenario = param("scenario") === "Server" ? "Server" : "Offline";
    get("benchmark-scenario").value = scenario;
    get("benchmark-scenario-note").textContent = scenario === "Offline"
      ? "Offline sends the sample set together and measures the reported throughput."
      : "Server submits requests over time and evaluates throughput under workload-specific latency limits.";
    const selected = data.benchmarks.filter((item) => item.scenario === scenario);
    const rate = (item) => Number(item.throughput_tokens_s);
    const max = Math.ceil(Math.max(...data.benchmarks.map(rate)) / 20000) * 20000;
    const bars = selected.map((item) => {
      const row = element("div", "benchmark-row");
      const track = element("div", "benchmark-track");
      track.setAttribute("aria-hidden", "true");
      const bar = element("span", "benchmark-fill");
      bar.style.width = `${rate(item) / max * 100}%`;
      track.append(bar);
      row.append(element("span", "benchmark-label", `${item.accelerators} × ${item.accelerator}`),
        element("span", "benchmark-value", `${number.format(rate(item))} tokens/s`), track);
      return row;
    });
    get("benchmark-bars").replaceChildren(...bars);
    const ranked = [...selected].sort((a, b) => rate(b) - rate(a));
    const gap = ((rate(ranked[0]) / rate(ranked[1]) - 1) * 100).toFixed(2);
    get("benchmark-note").textContent = `The ${ranked[0].accelerator} configuration reported ${gap}% more tokens per second than the ${ranked[1].accelerator} configuration in these ${scenario} submissions. `
      + "The systems ran different software stacks. This comparison includes no power or cost measurements.";
  }

  const renderers = {timeline: renderTimeline, financials: renderFinancials, policy: renderPolicy, archive: renderArchive};
  function controlValue(node, value) {
    if (node.tagName === "SELECT") return [...node.options].some((option) => option.value === value) ? value : "";
    return value.slice(0, 120);
  }

  function present(move, initial = false) {
    if (!initial && location.hash === "#main-content") {
      get("main-content").focus();
      return;
    }
    const {view, params, direct} = fromLocation();
    state.view = view;
    state.params = params;
    for (const name of views) get(name).hidden = name !== view;
    for (const item of document.querySelectorAll("[data-view]")) {
      if (item.dataset.view === view) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    }
    for (const [key, id] of Object.entries(controls[view])) {
      if (key === "quarter") continue; // Render supplies legitimately filtered options.
      const node = get(id);
      const value = controlValue(node, param(key));
      node.value = value;
      if (value !== param(key)) state.params.delete(key);
    }
    renderers[view]();
    if (!direct || !move) return;
    const selected = param(view === "timeline" ? "event" : "record");
    const row = selected ? [...get(view).querySelectorAll("[data-record-id]")]
      .find((node) => node.dataset.recordId === selected) : null;
    (row || get(view)).scrollIntoView({block: "start"});
    (row?.querySelector("summary") || get(`${view}-title`)).focus({preventScroll: true});
  }

  function setup() {
    buildFeatures();
    for (const [view, bindings] of Object.entries(controls)) {
      for (const [key, id] of Object.entries(bindings)) {
        const node = get(id);
        node.addEventListener(node.tagName === "INPUT" ? "input" : "change", () => {
          replaceParams(key, node.value);
          const recordKey = view === "timeline" ? "event" : view === "policy" ? "record" : "";
          if (recordKey) replaceParams(recordKey, "");
          if (key === "range") replaceParams("quarter", "");
          renderers[view]();
        });
      }
    }
    window.addEventListener("hashchange", () => present(true));
    get("clear-timeline").addEventListener("click", () => {
      state.params = new URLSearchParams();
      history.replaceState(null, "", "#timeline");
      present(false);
      get("timeline-search").focus();
    });
    for (const button of document.querySelectorAll("[data-download]")) {
      button.addEventListener("click", () => downloadCsv(data.downloads[button.dataset.download], button.dataset.download));
    }
    get("download-timeline").addEventListener("click", () => downloadCsv(csvForTimeline(), "nvidia-timeline-filtered.csv"));
    get("download-governance").addEventListener("click", () =>
      downloadCanvas(charts.governanceImage(figureEvents, data.snapshot.as_of, formattedDate), "nvidia-governance-dates.png"));
    get("download-finance-image").addEventListener("click", () =>
      downloadCanvas(charts.financialImage(visibleQuarters, selectedQuarter, data.snapshot.as_of), "nvidia-quarterly-trends.png"));
    for (const metric of charts.metrics) {
      const canvas = get(`chart-${metric.key}`);
      canvas.addEventListener("click", (event) => {
        const bounds = canvas.getBoundingClientRect();
        const index = charts.pointIndex(bounds.width, event.clientX - bounds.left, visibleQuarters.length);
        selectQuarter(periodKey(visibleQuarters[index]), false);
      });
    }
    if ("ResizeObserver" in window) new ResizeObserver(paintCharts).observe(get("financials"));
    else window.addEventListener("resize", paintCharts);
    present(Boolean(location.hash), true);
  }

  setup();
})();
