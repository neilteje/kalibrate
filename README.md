# Kalibrate

KALIBRATE is an agentic forecasting system for pop-culture prediction markets, evaluated on the **POPCAST** benchmark — a custom 10-task suite of historical pop-culture forecasting problems.

This repo contains:
- The KALIBRATE agent (5-module pipeline: market state, tool router, evidence extractor, forecaster, risk controller)
- The POPCAST benchmark (`tasks/T1.json` ... `tasks/T10.json`)
- Four baselines (random, single-prompt LLM, tool-enabled frontier model, market-only ablation)
- A full evaluation harness with proper scoring (Brier, log loss, task success rate)
- A Kalshi Demo integration that fetches live demo markets and runs KALIBRATE forecasts
- LaTeX-ready report tables for our papers in `docs/`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add OPENAI_API_KEY, ANTHROPIC_API_KEY, TAVILY_API_KEY
```

## Repo Layout

```
kalibrate/
  agent/                 # KALIBRATE agent modules
    market_state.py
    tool_router.py
    evidence_extractor.py
    forecaster.py
    risk_controller.py
    agent.py             # top-level run_episode()
    llm_clients.py       # cached OpenAI/Anthropic/Tavily clients
  baselines/             # 4 baseline implementations
    random_baseline.py
    single_prompt.py
    frontier_tool.py
    market_only.py
  benchmark/
    scoring.py           # Brier, log loss, TSR
    validator.py         # task JSON schema validator
  tasks/                 # POPCAST tasks T1..T10
  eval/
    run_eval.py          # main evaluation script
    report.py            # tables + LaTeX output
  kalshi/
    client.py            # signed Kalshi Demo API client
    live_state.py
    forecast.py
  results/
  docs/
```

## Kalshi Demo Integration

Kalshi Demo API root is `https://demo-api.kalshi.co/trade-api/v2`. Authenticated requests are RSA-PSS signed with:

- `KALSHI-ACCESS-KEY`
- `KALSHI-ACCESS-TIMESTAMP`
- `KALSHI-ACCESS-SIGNATURE`

The local client follows Kalshi's documented signing flow: sign `timestamp + HTTP_METHOD + path_without_query`, where the signed path includes `/trade-api/v2/...`.

### Check Demo balance

```bash
python3 -m kalshi.forecast --balance
```

If this returns `token_authentication_failure`, the saved key does not authenticate against Demo. Market listing and forecasting can still use public Demo market data, but portfolio endpoints require a valid Demo API key.

### List open Demo markets

```bash
python3 -m kalshi.forecast --list --limit 10
python3 -m kalshi.forecast --list --query sports --limit 20
```

### Forecast one live Demo market

```bash
python3 -m kalshi.forecast --ticker KXMLBTOTAL-26APR291310TBCLE-9 --tool-budget 0
```

Use `--tool-budget 1` or higher to let KALIBRATE retrieve external evidence through Tavily. By default, live forecasts still output the model's committed probability even if the Risk Controller raises a risk flag. Add `--abstain` to make the risk controller force uncertain forecasts to `0.5`.

### Kalshi Copilot browser overlay (Demo page)

This repo now includes a local Chrome extension overlay that appears on `https://demo.kalshi.co/*`, scrapes visible market cards/tickers, and calls your local KALIBRATE runtime for forecasts.

1) Start the local copilot bridge:

```bash
python3 -m kalshi.copilot_server --port 8765 --tool-budget 1
```

2) Load extension in Chrome:
- Open `chrome://extensions`
- Enable **Developer mode**
- Click **Load unpacked**
- Select `extension/kalshi-copilot`

3) Open the Kalshi Demo page and click the floating **Kalshi Copilot** button.
- Click **Rescan Markets** to detect visible open markets.
- Click **Predict** on any detected market card.
- If ticker lookup succeeds, forecasts use live Kalshi API state (`source=kalshi_api`).
- If ticker extraction fails, it falls back to page text context (`source=page_only` or `source=page_fallback`).

## Running the Benchmark

### End-to-end pipeline (recommended)

```bash
# 1. Validate all 10 POPCAST task files
python3 benchmark/validator.py

# 2. Fetch real Kalshi Demo API market data + enrich tasks
python3 eval/fetch_kalshi_markets.py

# 3. Run full benchmark: 5 systems x 10 tasks x 3 trials
python3 eval/run_eval.py --trials 3 --overwrite

# 4. Generate summary tables + LaTeX output
python3 eval/report.py

# 5. Generate all 12 publication-quality plots
python3 eval/plots.py
```

### Kalshi API data enrichment

```bash
python3 eval/fetch_kalshi_markets.py
```

Fetches 1000+ open markets from the Kalshi Demo API, pulls orderbooks for active markets, computes aggregate market statistics (volume, spreads, depth), and writes:
- `results/kalshi_snapshots/api_snapshot.json` — raw API data dump
- `results/kalshi_snapshots/enriched_tasks/T*.json` — POPCAST tasks with `kalshi_api_context` block containing real API data

### Running evaluations

```bash
python3 eval/run_eval.py --trials 3
```

Evaluates every system on every task with 3 trials for non-deterministic systems. Results land in `results/{system}__{task_id}__trial{n}.json`. The harness is **resumable**: if a run already exists for a (system, task, trial) triple it is skipped unless `--overwrite` is passed.

To run a subset (smoke test):

```bash
python3 eval/run_eval.py --systems kalibrate market_only --tasks T1 T2 T6 --trials 1
```