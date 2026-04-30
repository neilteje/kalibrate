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

  function normalizeTicker(raw) {
    if (!raw) {
      return null;
    }
    const t = String(raw).split(/[/?#]/)[0].trim().toUpperCase();
    if (!/^[A-Z0-9][A-Z0-9-]{2,63}$/.test(t)) {
      return null;
    }
    return t;
  }

  /** Kalshi uses lowercase paths on the site; API tickers are uppercase. */
  function extractTicker(value) {
    if (!value) {
      return null;
    }
    const s = String(value);
    const path = s.match(/\/markets\/([^/?#]+)/i);
    if (path) {
      const t = normalizeTicker(path[1]);
      if (t) {
        return t;
      }
    }
    const q = s.match(/[?&](?:ticker|market_ticker)=([^&]+)/i);
    if (q) {
      const t = normalizeTicker(decodeURIComponent(q[1]));
      if (t) {
        return t;
      }
    }
    const byToken = s.match(/\b(kx[a-z0-9][a-z0-9-]{2,})\b/i);
    if (byToken) {
      return normalizeTicker(byToken[1]);
    }
    return null;
  }

  function tickerFromDataset(el) {
    if (!el || !el.dataset) {
      return null;
    }
    const d = el.dataset;
    return (
      normalizeTicker(d.ticker) ||
      normalizeTicker(d.marketTicker) ||
      normalizeTicker(d.market)
    );
  }

  function tickerFromNearby(el, maxHops = 8) {
    let node = el;
    for (let i = 0; i < maxHops && node; i += 1) {
      const fromLink =
        extractTicker(node.getAttribute && node.getAttribute("href")) ||
        (node.querySelector &&
          extractTicker(
            node.querySelector('a[href*="/markets/"], a[href*="markets/"]')?.getAttribute("href")
          ));
      if (fromLink) {
        return fromLink;
      }
      const fromDs = tickerFromDataset(node);
      if (fromDs) {
        return fromDs;
      }
      node = node.parentElement;
    }
    return null;
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

  function isJunkTitle(text) {
    const clean = normalizeText(text);
    if (!clean || clean.length < 8) {
      return true;
    }
    if (/^\d+\s+markets?$/i.test(clean)) {
      return true;
    }
    if (/markets?\s+(found|available)$/i.test(clean)) {
      return true;
    }
    const pctHits = clean.match(/\d{1,3}%/g) || [];
    if (pctHits.length >= 4) {
      return true;
    }
    const clockHits = clean.match(/\d{1,2}:\d{2}/g) || [];
    if (clockHits.length >= 3) {
      return true;
    }
    if (/»{2,}|[\u2192\u2193]{2,}/.test(clean)) {
      return true;
    }
    if (/\d{1,2}(?::\d{2})?(?:am|pm)\d{1,2}(?::\d{2})?(?:am|pm)/i.test(clean.replace(/\s/g, ""))) {
      return true;
    }
    return false;
  }

  function titleScore(line) {
    const clean = normalizeText(line);
    if (!clean || isJunkTitle(clean)) {
      return -1e9;
    }
    let score = Math.min(clean.length, 120);
    const letters = (clean.match(/[A-Za-z]/g) || []).length;
    if (letters < 8) {
      return -1e9;
    }
    const digits = (clean.match(/\d/g) || []).length;
    score -= digits * 3;
    const pcts = (clean.match(/\d+%/g) || []).length;
    score -= pcts * 25;
    if (/^(yes|no|buy|sell|trade|volume)$/i.test(clean)) {
      score -= 500;
    }
    return score;
  }

  function pickTitle(lines) {
    const ignore = /^(buy|sell|yes|no|volume|open interest|expires|closing|market|event|trade)$/i;
    let best = "";
    let bestScore = -1e9;
    for (const line of lines) {
      const clean = normalizeText(line);
      if (!clean || clean.length < 10 || clean.length > 200) {
        continue;
      }
      if (ignore.test(clean)) {
        continue;
      }
      const s = titleScore(clean);
      if (s > bestScore) {
        bestScore = s;
        best = clean;
      }
    }
    return bestScore > -1e8 ? best : "";
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

  function splitSemanticChunks(raw) {
    if (!raw) {
      return [];
    }
    let s = normalizeText(raw.replace(/\s+/g, " "));
    s = s.replace(/(\d{1,3}%)(?=[A-Za-z])/g, "$1\n");
    s = s.replace(/([?.!])(?=[A-Z])/g, "$1\n");
    s = s.replace(/((?:am|pm))(?=\d)/gi, "$1\n");
    return s
      .split(/\n+/)
      .map((x) => normalizeText(x))
      .filter(Boolean);
  }

  function headingLinesIn(rootEl) {
    if (!rootEl || !rootEl.querySelectorAll) {
      return [];
    }
    const out = [];
    rootEl.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach((h) => {
      const t = normalizeText(h.textContent || "");
      if (t) {
        out.push(t);
      }
    });
    return out;
  }

  function buildTitleLines(anchor, container) {
    const lines = [];
    const anchorText = normalizeText(anchor.innerText || anchor.textContent || "");
    if (anchorText) {
      lines.push(anchorText);
    }
    if (container) {
      lines.push(...headingLinesIn(container));
      lines.push(...splitLines(container.innerText || container.textContent));
      lines.push(...splitSemanticChunks(container.textContent || ""));
    }
    const seen = new Set();
    return lines.filter((x) => {
      const k = x.slice(0, 200);
      if (seen.has(k)) {
        return false;
      }
      seen.add(k);
      return true;
    });
  }

  function marketCandidatesFromAnchors() {
    const anchors = Array.from(
      document.querySelectorAll('a[href*="/markets/"], a[href*="markets/"]')
    ).filter(isVisible);
    return anchors
      .map((anchor) => {
        const href = anchor.getAttribute("href") || "";
        const ticker = extractTicker(href) || tickerFromNearby(anchor);
        const container = anchor.closest("article,li,section,div");
        const lines = buildTitleLines(anchor, container);
        let title = pickTitle(lines);
        if (!title || isJunkTitle(title)) {
          const fallback = shorten(normalizeText(anchor.innerText || anchor.textContent || ""), 140);
          title = fallback && !isJunkTitle(fallback) ? fallback : "";
        }
        if (!title && ticker) {
          title = `Market ${ticker}`;
        }
        if (!title) {
          return null;
        }
        const rawContext = (container && container.innerText) || anchor.innerText || "";
        const context = shorten(rawContext, 420);
        return { ticker: ticker || null, title: shorten(title, 160), context };
      })
      .filter(Boolean);
  }

  function marketCandidatesFromButtons() {
    const buttons = Array.from(document.querySelectorAll("button")).filter(isVisible);
    const interesting = buttons.filter((btn) => /yes|no|buy|sell|trade/i.test(btn.textContent || ""));
    return interesting
      .map((btn) => {
        const container = btn.closest("article,li,section,div");
        if (!container) {
          return null;
        }
        const ticker = tickerFromNearby(btn) || tickerFromNearby(container);
        if (!ticker) {
          return null;
        }
        const link = container.querySelector('a[href*="/markets/"], a[href*="markets/"]');
        const lines = buildTitleLines(link || btn, container);
        let title = pickTitle(lines);
        if (!title || isJunkTitle(title)) {
          title = `Market ${ticker}`;
        }
        const context = shorten(container.innerText || "", 420);
        return { ticker, title: shorten(title, 160), context };
      })
      .filter(Boolean);
  }

  function scrapeMarkets() {
    const candidates = [
      ...marketCandidatesFromAnchors(),
      ...marketCandidatesFromButtons()
    ];

    const cleaned = uniqueBy(candidates, (m) => m.ticker || m.title)
      .filter(
        (m) =>
          m.title &&
          m.title.length >= 8 &&
          !/^untitled/i.test(m.title) &&
          !isJunkTitle(m.title)
      )
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
        <div class="kc-market-title"></div>
        <div class="kc-market-meta"></div>
        <div class="kc-row">
          <label>tools</label>
          <input value="1" min="0" max="5" type="number" />
          <button type="button">Predict</button>
        </div>
        <div class="kc-result"></div>
      `;
      row.querySelector(".kc-market-title").textContent = market.title;
      row.querySelector(".kc-market-meta").textContent = `ticker: ${market.ticker || "unknown"}`;
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
