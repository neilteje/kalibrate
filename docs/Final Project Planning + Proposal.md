# Tab 1

**Final project overview:** [https://docs.google.com/document/d/1VgiYrteTzQtFNiD8P\_Kiqs6GUiA\_NBGz/edit\#bookmark=id.4wq0qzfl084](https://docs.google.com/document/d/1VgiYrteTzQtFNiD8P_Kiqs6GUiA_NBGz/edit#bookmark=id.4wq0qzfl084)

**Brainstorming:**

- Email agent for handling emails/checking into flights/calendar invites  
- Canvas agent for doing school assignments  
- Agent that automatically adds important events to a calendar  
  - Free food calendar   
  -   
- Travel Agent that handles making itineraries based on an existing google calendar or emails of plans  
- Cs374 autograder because im mad at the cas for not reading my solutions

- Interior design agent

- Kalshi / Polymarket Futures Prediction agent  
  - forecasting based on past events (input data is the historical data and predictions)  
  - this can be our benchmark: given only historical market data up to time t, forecast probability at time t+h (or at close) across different markets  
  - I think for this class we could do a forecasting agent instead of a trading agent  
    - we pull historical \+ live market data & forecast probabilities and the agent will output prediction and signals (buy or no buy)  
  - problem/motivation we’re addressing: maybe that prediction markets are very noisy, so data about trends can be difficult to obtain, but using historical market data and live market data in a systemic way will allow us to make more informed estimations about the outcome  
  - work to evaluate method

- Security agent that can scan code bases for potential vulnerabilities and suggest fixes  
  - Can incorporate RAG so agent can have more context about the codebase and unique security vulnerabilities

# Final Proposal

## 

## **Section I: Introduction**

Pop culture prediction markets, such as those on Kalshi, have grown significantly in popularity and trading volume. These fast-moving markets are driven by hype and sentiment, presenting challenges in forecasting pop culture prediction markets that traditional AI agents struggle to dynamically adapt to. Accurate forecasting in this domain is valuable, as it enables timely probabilistic predictions and insight into broader social trends.   
Existing AI approaches rely on interpreting structured historical data and fall short when it comes to interpreting unstructured real-time information. These bursts of information significantly shift market probabilities, yet are difficult to model (Arora & Malpani, 2026). Furthermore, traditional approaches don’t take into account behavioral biases like herding behavior and emotional trading. By over-relying on past prices or static features, standard forecasting systems struggle to adapt to pop culture markets.

## **Part II: Benchmark Design**

The benchmark covers pop-culture predictive markets on Kalshi.  This domain requires successful agents to integrate financial signals with high-velocity trends to produce updated forecasts under time pressure. We will design tasks that vary by market category and information shock to test generalization and robustness.

1. **Film/TV:** Box office performance, casting announcements, award nominations.  
2. **Music:** Album release dates, chart performance, celebrity rumors.  
3. **Tech/Viral Trends:** Viral challenges, social media milestones, product leaks.  
4. **Signal Variation:** Define tasks based on the complexity of the signal environment:  
5. **Market-Only:** Agent must forecast using only historical price/volatility data (for comparison to the Market-only baseline).  
6. **Single-Event Shock:** Agent is given one sudden, impactful piece of news (e.g., an artist's nomination) and must rapidly adjust its forecast.

We will present our agent with conflicting information (e.g., an "official announcement" versus a credible "leak"), requiring it to rate uncertainty and potentially abstain. Example tasks include:

1. Forecasting whether a film’s opening weekend exceeds a revenue threshold 72 hours before market close.  
2. Forecasting a Best New Artist market during a period of high volatility with limited external query budget.  
3. Forecasting a celebrity related market following a data outage and contradictory media reports. 

These tasks are challenging for agents, as they often over-rely on structured historical data and fail to incorporate sudden information shocks that define pop culture markets. Task difficulty scales with Time-to-Resolution, Signal-to-Noise Ratio, a tighter Tool Budget, and reliance on external news over historical price action. Subjective metrics are hard to measure on Kalshi and unimportant in this scenario, so we exclude them. Researchers can backtest our benchmarks using Kalshi’s API, its demo environment, and historical data from the WayBack Machine.  
**Section III: Agent Design**  
Inputs will be market snapshot(s) with titles, rules/resolution criterion, close time, current implied probabilities, recent price paths, and optional external signals. The output will be a forecast at a timestep difference or a forecast of price at close time, as well as an uncertainty and calibration score (essentially a confidence score). The agent will advise whether to forecast or abstain on the market. Its key components include a market scanner, main planner, tool router, a memory system for the market, a risk controller, and an auditor. Our agent will scan pop culture markets and choose top event contracts to forecast. Tools will fetch online information like news and online bias, and an evidence extractor will convert the text to unstructured signals.   
The agent operates in discrete forecasting episodes. For each episode, it constructs a structured state from market inputs including recent price trajectories, volatility and liquidity proxies, time-to-resolution, and pop culture–specific event metadata (e.g., award type, nomination phase). External information like news is accessed if explicitly invoked under a tool budget and is converted into structured evidence features. We use a schema-constrained prompting strategy in which the LLM receives a JSON market state and must output valid JSON containing the forecast, uncertainty, and abstention decision. If external tool calls fail or return low-quality information, the agent falls back to a market-only forecast.	  
We will evaluate our agent against several baselines, including a market-only counterpart, simple Kalshi-style forecasting approaches based on current prices or trends, and standard probabilistic baselines evaluated using proper scoring rules. All methods are evaluated on identical historical markets using objective metrics (Brier score and log loss), along with limited human and LLM review of reasoning traces. These baselines ensure fair, ground-truth comparison.

**Section IV: Resources and Timeline**  
Our system requires API access to Claude or OpenAI for agent reasoning, planning, and structured forecasting, along with access to news and web search APIs to retrieve external pop culture signals. We will use Kalshi’s public and developer APIs to obtain historical and live market data, including price histories and resolution outcomes, and maintain storage for cached market data and retrieved news. The agent will use a lightweight model, GPT-4o mini, for forecasting and a stronger reasoning model for complex planning. Access to these resources will be obtained via public archives, Kalshi’s API, and API credits funded by the team, with estimated total costs of $100–150 depending on experimental scale.  
We will first finalize the pop culture market scope and benchmark task definitions and collect historical Kalshi market data by the end of February. Next, we will implement the benchmark infrastructure and baseline forecasting methods, followed by building the core agent including interactions, forecasting, abstention, and optional tool use by the end of March. Afterwards, we will run evaluations and ablations, calibrate uncertainty, and iterate on the agent. The final phase will focus on our paper and final presentation.

**Section V: References**

1. Mohanty, S. N., Nanjundan, P., & Kar, T. Artificial Intelligence in Forecasting. Taylor & Francis.  
2. Arora, A., & Malpani, R. (2026). PredictionMarketBench: A SWE-bench-Style Framework for Backtesting Trading Agents on Prediction Markets. [arXiv preprint arXiv:2602.00133](https://arxiv.org/abs/2602.00133).  
3. Todasco, M (2025) Going All-In on LLM Accuracy: Fake Prediction Markets, Real Confidence Signals [https://arxiv.org/pdf/2512.05998](https://arxiv.org/pdf/2512.05998)

