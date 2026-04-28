# Kalibrate

KALIBRATE is an agentic forecasting system for pop-culture prediction markets, evaluated on the **POPCAST** benchmark — a custom 10-task suite of historical pop-culture forecasting problems.

This repo contains:
- The KALIBRATE agent (5-module pipeline: market state, tool router, evidence extractor, forecaster, risk controller)
- The POPCAST benchmark (`tasks/T1.json` ... `tasks/T10.json`)
- Four baselines (random, single-prompt LLM, tool-enabled frontier model, market-only ablation)
- A full evaluation harness with proper scoring (Brier, log loss, task success rate)
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
  results/               # raw run JSONs (gitignored)
  docs/                  # papers (LaTeX)
```

## Running the Benchmark

### Validate task files

```bash
python3 benchmark/validator.py
```

### Sanity test (no API keys required)

```bash
python3 eval/run_eval.py --systems random
python3 eval/report.py
```

### Run the full benchmark

```bash
python3 eval/run_eval.py --trials 3
```

This evaluates every system on every task with 3 trials for non-deterministic systems. Results land in `results/{system}__{task_id}__trial{n}.json`. The harness is **resumable**: if a run already exists for a (system, task, trial) triple it is skipped unless `--overwrite` is passed.

To run a subset (smoke test):

```bash
python3 eval/run_eval.py --systems kalibrate market_only --tasks T1 T2 T6 --trials 1
```

### Generate report tables

```bash
python3 eval/report.py
```

Writes `results/summary.csv`, `results/per_task.csv`, `results/by_difficulty.csv` and prints LaTeX-ready snippets to stdout for direct paste into the agent paper.

## Cost Estimate

Single full evaluation run (5 systems x 10 tasks; 3 trials for non-deterministic systems):
- ~30 KALIBRATE episodes (~$0.10-0.30 each = $3-9 total)
- ~30 single-prompt baseline calls (~$0.02 each = ~$0.60)
- ~30 frontier-tool baseline calls (~$0.15-0.40 each = $4-12)
- ~10 market-only ablation calls (~$0.05 each = ~$0.50)
- Total: roughly **$8-25** for one full evaluation pass.

## Architecture

See `docs/CS498DK_AgentPaperDraft.tex` for the full architecture description and pipeline diagram. The high-level flow:

```
Task JSON
   |
   v
Market State Constructor  --> normalized JSON state
   |
   v
Tool Router (budget B=3)  --> Tavily search (cutoff-filtered)
   |
   v
Evidence Extractor        --> structured features per doc
   |
   v
Forecaster (GPT-4o mini)  --> {p_hat, confidence, reasoning}
   |
   v
Risk Controller           --> abstain or commit
   |
   v
Forecast Output JSON
```

## Leakage Discipline

All Tavily searches are filtered server-side: any document whose `published_date >= decision_timestamp` is dropped before reaching the agent. Tasks include a `notes_for_evaluation` field used only by the eval harness for ground-truth verification — never shown to the agent.
