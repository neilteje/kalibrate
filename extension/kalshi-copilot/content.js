(function initKalshiCopilot() {
  if (window.__KALSHI_COPILOT_LOADED__) {
    return;
  }
  window.__KALSHI_COPILOT_LOADED__ = true;

  const API_URL = "http://127.0.0.1:8765/forecast";
  const root = document.createElement("div");
  root.id = "kalshi-copilot-root";
  root.innerHTML = `
    <button class="kc-button" type="button">Kalshi Copilot</button>
    <div class="kc-panel">
      <div class="kc-header">
        <div>
          <div class="kc-title">Kalshi Copilot</div>
          <div class="kc-status">Scan page, match markets, predict.</div>
        </div>
      </div>
      <div class="kc-content"></div>
      <div class="kc-footer">
        <button type="button" class="kc-rescan">Rescan Markets</button>
      </div>
    </div>
  `;
  document.documentElement.appendChild(root);

  const button = root.querySelector(".kc-button");
  const panel = root.querySelector(".kc-panel");
  const content = root.querySelector(".kc-content");
  const status = root.querySelector(".kc-status");
  const rescanButton = root.querySelector(".kc-rescan");

  function isVisible(el) {
    if (!el) {
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function uniqueBy(items, keyFn) {
    const seen = new Set();
    return items.filter((item) => {
      const key = keyFn(item);
      if (!key || seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  function extractTicker(value) {
    if (!value) {
      return null;
    }
    const byPath = value.match(/\/markets\/([A-Z0-9-]{6,})/);
    if (byPath) {
      return byPath[1];
    }
    const byToken = value.match(/\b([A-Z0-9]{2,}-[A-Z0-9-]{3,})\b/);
    return byToken ? byToken[1] : null;
  }

  function normalizeText(value) {
    if (!value) {
      return "";
    }
    return value
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .replace(/([A-Za-z])(\d{1,3}%)/g, "$1 $2")
      .replace(/(\d{1,3}%)([A-Za-z])/g, "$1 $2")
      .replace(/([a-zA-Z])(\d)([a-zA-Z])/g, "$1 $2 $3")
      .replace(/\s+/g, " ")
      .trim();
  }

  function shorten(value, maxLen = 110) {
    const clean = normalizeText(value);
    if (clean.length <= maxLen) {
      return clean;
    }
    return `${clean.slice(0, maxLen - 1)}...`;
  }

  function pickTitle(lines) {
    const ignore = /^(buy|sell|yes|no|volume|open interest|expires|closing|market|event|trade)$/i;
    for (const line of lines) {
      const clean = normalizeText(line);
      if (!clean || clean.length < 8 || clean.length > 130) {
        continue;
      }
      if (ignore.test(clean)) {
        continue;
      }
      const alphaCount = (clean.match(/[A-Za-z]/g) || []).length;
      const digitCount = (clean.match(/[0-9]/g) || []).length;
      if (alphaCount < 5) {
        continue;
      }
      if (digitCount > alphaCount) {
        continue;
      }
      return clean;
    }
    return "";
  }

  function splitLines(raw) {
    if (!raw) {
      return [];
    }
    return raw
      .split(/\n+/)
      .map((x) => normalizeText(x))
      .filter(Boolean);
  }

  function marketCandidatesFromAnchors() {
    const anchors = Array.from(document.querySelectorAll('a[href*="/markets/"]')).filter(isVisible);
    return anchors.map((anchor) => {
      const href = anchor.getAttribute("href") || "";
      const ticker = extractTicker(href) || extractTicker(anchor.textContent || "");
      const container = anchor.closest("article,li,section,div");
      const lines = [
        ...splitLines(anchor.textContent || ""),
        ...splitLines(container && container.textContent)
      ];
      const title = pickTitle(lines) || shorten(anchor.textContent, 140) || "Untitled market";
      const context = shorten((container && container.textContent) || anchor.textContent, 340);
      return { ticker, title, context };
    });
  }

  function marketCandidatesFromButtons() {
    const buttons = Array.from(document.querySelectorAll("button")).filter(isVisible);
    const interesting = buttons.filter((btn) => /yes|no|buy|sell|trade/i.test(btn.textContent || ""));
    return interesting.map((btn) => {
      const container = btn.closest("article,li,section,div");
      if (!container) {
        return null;
      }
      const text = container.textContent || "";
      const ticker = extractTicker(text);
      const lines = splitLines(text);
      const title = pickTitle(lines) || shorten(text, 140) || "Untitled market";
      const context = shorten(text, 340);
      return { ticker, title, context };
    }).filter(Boolean);
  }

  function scrapeMarkets() {
    const candidates = [
      ...marketCandidatesFromAnchors(),
      ...marketCandidatesFromButtons()
    ];

    const cleaned = uniqueBy(candidates, (m) => m.ticker || m.title)
      .filter((m) => m.title && m.title.length >= 8 && !/^untitled/i.test(m.title))
      .slice(0, 25);
    return cleaned;
  }

  function formatResult(result) {
    const pct = (result.p_final * 100).toFixed(1);
    const conf = (result.confidence * 100).toFixed(1);
    const src = result.source || "unknown";
    const risk = result.risk_flag ? "yes" : "no";
    return `YES ${pct}% | conf ${conf}% | risk ${risk} | source ${src}`;
  }

  async function predictOne(market, row, budgetInput) {
    const resultEl = row.querySelector(".kc-result");
    resultEl.textContent = "Predicting...";
    const toolBudget = Number.parseInt(budgetInput.value || "1", 10);
    const payload = {
      ticker: market.ticker,
      title: market.title,
      page_context: market.context,
      tool_budget: Number.isFinite(toolBudget) ? toolBudget : 1
    };
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      const result = data.result;
      const summary = formatResult(result);
      const tickerLabel = result.resolved_ticker || market.ticker || "unknown";
      resultEl.textContent = `${summary}\nresolved ticker: ${tickerLabel}\n${result.reasoning_summary || ""}`;
    } catch (err) {
      resultEl.textContent = `Error: ${err.message}`;
    }
  }

  function render(markets) {
    content.innerHTML = "";
    if (!markets.length) {
      content.textContent = "No market cards detected. Open a Kalshi markets page and rescan.";
      status.textContent = "No markets found";
      return;
    }
    status.textContent = `${markets.length} markets detected`;
    markets.forEach((market) => {
      const row = document.createElement("div");
      row.className = "kc-market";
      row.innerHTML = `
        <div class="kc-market-title">${market.title}</div>
        <div class="kc-market-meta">ticker: ${market.ticker || "unknown"}</div>
        <div class="kc-row">
          <label>tools</label>
          <input value="1" min="0" max="5" type="number" />
          <button type="button">Predict</button>
        </div>
        <div class="kc-result"></div>
      `;
      const budgetInput = row.querySelector("input");
      const predictButton = row.querySelector("button");
      predictButton.addEventListener("click", () => predictOne(market, row, budgetInput));
      content.appendChild(row);
    });
  }

  function rescan() {
    const markets = scrapeMarkets();
    render(markets);
  }

  button.addEventListener("click", () => {
    panel.classList.toggle("kc-open");
    if (panel.classList.contains("kc-open")) {
      rescan();
    }
  });
  rescanButton.addEventListener("click", rescan);
})();
