(() => {
  "use strict";

  const palette = {
    ink: "#14282e",
    subtle: "#486068",
    line: "#d8e2de",
    accent: "#006151",
    paper: "#f7f8f5",
    white: "#ffffff",
  };

  const leftGutter = 49;
  const rightGutter = 13;
  const metrics = [
    {key: "revenue", label: "Consolidated revenue", unit: "USD billions", minTop: 20, step: 20,
      value: (row) => Number(row.revenue_usd_m) / 1000, caption: (value) => `$${value.toFixed(2)}B`},
    {key: "share", label: "Data Center share", unit: "% of revenue", minTop: 100, step: 25,
      value: (row) => 100 * Number(row.data_center_usd_m) / Number(row.revenue_usd_m), caption: (value) => `${value.toFixed(2)}%`},
    {key: "rd", label: "GAAP R&D intensity", unit: "% of revenue", minTop: 30, step: 10,
      value: (row) => 100 * Number(row.gaap_rd_usd_m) / Number(row.revenue_usd_m), caption: (value) => `${value.toFixed(2)}%`},
  ];

  function quarterLabel(row) {
    return `FY${row.fiscal_year} Q${row.quarter}`;
  }

  function drawTrend(ctx, width, height, rows, metric, selected) {
    const labels = {left: leftGutter, right: rightGutter, top: 18, bottom: 31};
    const chartWidth = width - labels.left - labels.right;
    const chartHeight = height - labels.top - labels.bottom;
    const points = rows.map(metric.value);
    const step = metric.key === "revenue" && Math.max(...points) > 60 ? 30 : metric.step;
    const top = Math.max(metric.minTop, Math.ceil(Math.max(...points) / step) * step);
    const dotX = (index) => labels.left + (points.length === 1 ? chartWidth / 2 : index * chartWidth / (points.length - 1));
    const dotY = (value) => labels.top + chartHeight * (1 - value / top);

    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let level = 0; level <= top; level += step) {
      const y = dotY(level);
      ctx.fillStyle = palette.subtle;
      ctx.fillText(metric.key === "revenue" ? `$${level}B` : `${level}%`, labels.left - 7, y);
      ctx.strokeStyle = palette.line;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(labels.left, y);
      ctx.lineTo(width - labels.right, y);
      ctx.stroke();
    }

    ctx.strokeStyle = palette.accent;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.beginPath();
    points.forEach((value, index) => {
      const x = dotX(index);
      const y = dotY(value);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const end = points.length - 1;
    const indices = [...new Set([0, Math.round(end / 2), end])];
    ctx.fillStyle = palette.subtle;
    ctx.textBaseline = "top";
    indices.forEach((index) => {
      ctx.textAlign = index === 0 ? "left" : index === end ? "right" : "center";
      ctx.fillText(quarterLabel(rows[index]), dotX(index), height - labels.bottom + 8);
    });
    const focus = Math.max(0, Math.min(end, selected));
    const x = dotX(focus);
    const y = dotY(points[focus]);
    ctx.strokeStyle = "#779d92";
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x, height - labels.bottom);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = palette.accent;
    ctx.beginPath();
    ctx.arc(x, y, 4.8, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = palette.white;
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }

  function drawChart(canvas, rows, metric, selected) {
    const {width, height} = canvas.getBoundingClientRect();
    if (width < 72 || height < 72 || !rows.length) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    drawTrend(ctx, width, height, rows, metric, selected);
  }

  function canvasAt(width, height) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    return [canvas, canvas.getContext("2d")];
  }

  function financialImage(rows, selected, asOf) {
    const [canvas, ctx] = canvasAt(1440, 640);
    ctx.fillStyle = palette.paper;
    ctx.fillRect(0, 0, 1440, 640);
    ctx.fillStyle = palette.accent;
    ctx.font = "700 19px system-ui, sans-serif";
    ctx.fillText("NVIDIA EVIDENCE OBSERVATORY", 52, 53);
    ctx.fillStyle = palette.ink;
    ctx.font = "52px Georgia, serif";
    ctx.fillText("NVIDIA’s quarterly financial trends", 52, 121);
    ctx.fillStyle = palette.subtle;
    ctx.font = "21px system-ui, sans-serif";
    ctx.fillText(`${quarterLabel(rows[0])} to ${quarterLabel(rows[rows.length - 1])} · Highlight: ${quarterLabel(rows[selected])}`, 52, 158);
    metrics.forEach((metric, i) => {
      const left = 52 + i * 452;
      ctx.fillStyle = palette.white;
      ctx.fillRect(left, 193, 430, 341);
      ctx.font = "700 19px system-ui, sans-serif";
      ctx.fillStyle = palette.subtle;
      ctx.fillText(metric.label, left + 16, 226);
      ctx.font = "40px Georgia, serif";
      ctx.fillStyle = palette.ink;
      ctx.fillText(metric.caption(metric.value(rows[selected])), left + 16, 277);
      ctx.save();
      ctx.translate(left + 14, 295);
      drawTrend(ctx, 398, 213, rows, metric, selected);
      ctx.restore();
    });
    ctx.fillStyle = palette.subtle;
    ctx.font = "17px system-ui, sans-serif";
    ctx.fillText("Sources: NVIDIA earnings filings and quarterly market tables. Data Center is an issuer-defined market category.", 52, 568);
    ctx.fillText(`As of ${asOf} · github.com/dingyucanada/jensen-huang-research`, 52, 601);
    return canvas;
  }

  function governanceImage(events, asOf, format) {
    const [canvas, ctx] = canvasAt(1200, 715);
    ctx.fillStyle = "#0c332f";
    ctx.fillRect(0, 0, 1200, 715);
    ctx.fillStyle = "#bfe7d5";
    ctx.font = "700 21px system-ui, sans-serif";
    ctx.fillText("NVIDIA EVIDENCE OBSERVATORY", 64, 71);
    ctx.fillStyle = palette.white;
    ctx.font = "56px Georgia, serif";
    ctx.fillText("When did NVIDIA’s CEO change?", 64, 157);
    ctx.font = "23px system-ui, sans-serif";
    ctx.fillStyle = "#d5e9e3";
    ctx.fillText("Two EDGAR filings separate effective dates from disclosure dates.", 64, 212);
    for (const [index, item] of events.entries()) {
      const top = 255 + 146 * index;
      ctx.fillStyle = "#15443e";
      ctx.fillRect(64, top, 1072, 122);
      ctx.fillStyle = palette.white;
      ctx.font = "700 24px system-ui, sans-serif";
      ctx.fillText(item.title, 88, top + 36);
      ctx.font = "35px Georgia, serif";
      ctx.fillText(format(item.event.event_date), 88, top + 79);
      ctx.fillText(format(item.event.disclosed_on), 580, top + 79);
      ctx.fillStyle = "#bfe7d5";
      ctx.font = "18px system-ui, sans-serif";
      ctx.fillText("Effective", 88, top + 106);
      ctx.fillText("Disclosed", 580, top + 106);
      ctx.textAlign = "right";
      ctx.fillText(item.ref, 1111, top + 37);
      ctx.textAlign = "left";
    }
    ctx.font = "20px system-ui, sans-serif";
    ctx.fillStyle = "#d5e9e3";
    ctx.fillText(`Source: NVIDIA Forms 8-K, Item 5.02 · Evidence reviewed ${format(asOf)}`, 64, 621);
    ctx.fillText("github.com/dingyucanada/jensen-huang-research", 64, 659);
    return canvas;
  }

  function pointIndex(width, x, length) {
    const span = Math.max(1, width - leftGutter - rightGutter);
    const percent = Math.max(0, Math.min(1, (x - leftGutter) / span));
    return Math.round(percent * (length - 1));
  }

  window.observatoryCharts = {metrics, quarterLabel, drawChart, financialImage, governanceImage, pointIndex};
})();
