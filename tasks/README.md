# POPCAST Benchmark Tasks

Ten historical pop-culture prediction-market style forecasting tasks. Each task is grounded in a real, already-resolved event from 2023-2024, formatted with a strict decision timestamp before which agents may use information.

## Task Schema

Each `T<n>.json` file contains:

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Identifier (T1..T10) |
| `domain` | string | One of: film, tv, music, awards, celebrity, streaming, viral |
| `difficulty` | string | easy, medium, or hard |
| `title` | string | The market question, in natural language |
| `decision_timestamp` | ISO 8601 | Cutoff: agent may only use information published before this UTC timestamp |
| `resolution_timestamp` | ISO 8601 | When the event resolves |
| `resolution_criteria` | string | Objective rule by which YES/NO is determined |
| `outcome` | int (0 or 1) | Ground truth (YES=1, NO=0). Hidden from agent during forecasting. |
| `price_history` | list of floats | Recent implied YES probabilities (e.g. weekly snapshots prior to T0) |
| `volatility_proxy` | float | Standard deviation proxy of recent price movement |
| `liquidity_proxy` | float | Market liquidity score in [0, 1] |
| `context_hint` | string | Background description framing the market state |
| `notes_for_evaluation` | string | Post-hoc explanation of how the market resolved (NEVER shown to agent) |

## Task Distribution

| ID | Domain | Difficulty | Outcome |
|---|---|---|---|
| T1 | Film (Box Office) | Easy | 1 |
| T2 | Film (Casting) | Medium | 1 |
| T3 | TV (Release) | Medium | 1 |
| T4 | Music (Chart) | Hard | 0 |
| T5 | Music (Album Release) | Easy | 1 |
| T6 | Awards (Nomination) | Hard | 0 |
| T7 | Awards (Win) | Medium | 1 |
| T8 | Celebrity Activity | Hard | 0 |
| T9 | Streaming (Viewership) | Medium | 1 |
| T10 | Viral / Album Debut | Hard | 0 |

Difficulty: 2 easy, 4 medium, 4 hard. Outcomes: 5 YES, 5 NO (balanced).

## Leakage Discipline

Agents must filter all retrieved evidence by `published_date < decision_timestamp`. The benchmark harness applies this filter automatically when using Tavily search. The `notes_for_evaluation` field contains post-resolution information and is never made visible to any agent or baseline.
