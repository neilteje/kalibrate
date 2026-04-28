# Kalshi Prediction Agent

**Due Date:** February 17, 2026 (Tuesday, Week 5\) **Word Count:** 600-900 words (excluding references) **Submission:** PDF on Canvas (one per group)

## Part I: Introduction

Write an introduction that covers:

### 1\. Problem and Motivation (Sophia)

* What problem are you addressing in the AI agents domain?

  Pop culture prediction markets, such as those on Kalshi,  have grown significantly in popularity and trading volume. These fast-moving markets are often driven by hype and sentiment, an act known as *emotional trading*. Due to emotional bias, forecasting pop culture prediction markets presents challenges that traditional AI agents struggle to dynamically adapt to.

* Why is this problem important?

  Accurate forecasting in pop culture markets is important for several reasons. First, the high velocity of information and emotional trading enables AI agents to provide timely, probabilistic predictions that would be difficult for a human to consistently generate.  Secondly, pop culture markets can reveal unique aspects about broader social/cultural trends and public opinion.

* What are the current limitations or challenges?

  Existing AI approaches commonly focus on interpreting structured historical data and fall short when it comes to interpreting unstructured real-time information, like announcements, leaks, and rumors. These sudden bursts of information have the ability to significantly shift market probabilities, yet they are difficult to model with a traditional approach. Furthermore, traditional approaches don’t take into account behavioral biases like herding behavior and emotional trading. While market prices may typically act as probabilistic signals, they may diverge in environments that are rumor-driven. Lastly, standard forecasting systems typically aren’t domain specific and not optimized for pop culture markets.  By overrelying on past price movements or static features, these systems may struggle to adapt quickly to fast-paced pop culture markets.

* Cite relevant work that motivates your problem

  [Mohanty, S. N., Nanjundan, P., & Kar, T. Artificial Intelligence in Forecasting](https://api.taylorfrancis.com/content/books/mono/download?identifierName=doi&identifierValue=10.1201/9781003399292&type=googlepdf)

- Talks about challenges with dynamic forecasting

  [Arora, A., & Malpani, R. (2026). PredictionMarketBench: A SWE-bench-Style Framework for Backtesting Trading Agents on Prediction Markets. *arXiv preprint arXiv:2602.00133*](https://arxiv.org/pdf/2602.00133)

- Talks about challenges with dynamic forecasting and good ways to evaluate agents

	[https://arxiv.org/pdf/2512.05998](https://arxiv.org/pdf/2512.05998)

### 2\. Your Approach (Sophia and Neil)

* What is your proposed solution?

  We’re building a pop culture agent to aid with forecasting outcomes in prediction markets, notably Kalshi. At a high level, our agent will be able to operate on historical and live prediction market data to produce probabilistic forecasts of the future market prices under constraints and in specific markets. We’ve noticed the rise in trading volume in these markets as well as popularity for prediction markets in pop culture.  Additionally, these specific markets have a defined schedule for resolution, strong rumor-driven trading, and quick announcements and turnarounds. Our agent’s goal would not be to trade or execute any orders. Our agent will be able to identify and prioritize upcoming pop culture markets with fixed resolution dates and futures to trade on, track pre-event market dynamics through querying external news/search tools under a budget to detect relevant signals and then generate probabilistic forecasts. 

* What makes your approach novel or different?

  We believe our approach is novel since we’re going extremely domain specific with pop-culture markets. Pop culture markets are driven less by continuous numerical signals as opposed to regular equity/capital markets, and more by discrete information events such as nominations, leaks, rumors through Tweets, etc. So, by targeting this, we hope to evaluate our agent behavior in an environment where the agentic tool use and overall workflow matters more than the outcome (forecast). 

* What are the key insights driving your design?

  Firstly, emotional and hype-driven dynamics matter since pop culture markets are commonly influenced by fandom bias, public sentiment, and media amplification. Therefore, we must incorporate external signals beyond historical data. Secondly, as mentioned before, the pop market is very fast-paced, with information arriving in bursts. Unlike traditional markets, changes in probability can be triggered by artist nominations and leaks. Therefore, our agent must detect and respond to those external signals in a timely manner. 

* How will your agent address the limitations you identified?

  To address the limitations of traditional prediction systems,  our AI will integrate historical and real-time data, budget-constrained external signal retrieval from news and search tools, and prioritization of markets with fixed resolution dates. This approach will allow our agent to factor in sentiment-based dynamics that standard models might not take into account. Additionally, engaging in markets with fixed resolution dates will enable us to evaluate forecasting accuracy and agentic decision-making. To also tackle the problem of 

### 3\. Evaluation Overview (Daniel and Bhavyaa)

* How will you demonstrate that your approach works?

  Pop culture trends tend to move on social sentiment and “hype” culture, so it is important for us to use an evaluation method that has a mix of traditional financial rigor and modern LLM-based behavioral qualitative analysis. Before trading, the agent must prove it actually understands the culture. Use these metrics to measure its forecasting ability. A way we can do this is by having a Brier Score which measures the accuracy of probabilistic predictions. If your agent says there is a 70% chance a movie breaks $100M, and it does, the Brier score will be low (good).  We can also “backtest” the agent by feeding it historical social data from the months leading up to an event. We can see i f it identifies the correct winner before the betting odds shifted. 

* What will you measure?

  We need to measure the agent’s “Predictive Alpha”. We need to quantify the probabilistic accuracy and the actual leads the agent has. We can execute this by calculating a Brier score and comparing real-time data with the agent’s predictions. 

* What baselines will you compare against?

  We'll know we've succeeded if we can consistently beat three things: the "Wisdom of the Crowd" (meaning, better than current prediction market odds), a simple "Naive Sentiment Bot" (proving our LLM's thinking is smarter than just counting keywords), and a "Passive Cultural Index" (a basic "buy-and-hold" strategy for the top 10 trends). If we have a better win rate and fewer losses than these benchmarks, it'll show our approach genuinely works and isn't just random luck or simple social media monitoring.

## Part II: Benchmark Design (Daniel \+ Bhavyaa)

Provide a detailed description of your benchmark:

### 1\. Task Domain 

* What domain will your benchmark cover?

  The benchmark covers pop-culture predictive markets on Kalshi, an up and coming method of trading money.

* Why is this domain appropriate for evaluating AI agents?

  This domain forces the agent to dynamically use financial signals along with high-velocity trends to create accurate updating predictions via a constant feedback loop. The fast paced and event based nature of these markets priorities agency and decision making under constraints and pressure. 

### 2\. Task Specifications

* How will you design 10 (or 20\) distinct tasks?

  Design tasks by varying the market category and the type of information shock the agent must process. This tests the agent’s generalization across different pop culture niches and its robustness against various signal types.

- Film/TV: Box office performance, casting announcements, award nominations.  
- Music: Album release dates, chart performance, celebrity rumors.  
- Tech/Viral Trends: Viral challenges, social media follower milestones, product leaks.

Signal Variation: Define tasks based on the complexity of the signal environment:

- Market-Only: Agent must forecast using only historical price/volatility data (for comparison to the Market-only baseline).  
- Single-Event Shock: Agent is given one sudden, impactful piece of news (e.g., an artist's nomination) and must rapidly adjust its forecast.  
- Contradictory Signals: Agent is presented with conflicting information (e.g., an "official announcement" versus a credible "leak"), requiring it to rate uncertainty and potentially abstain.

* Provide examples of 2-3 specific tasks

  Task 1: Forecasting the probability of a film's opening weekend surpassing $150M, 72 hours before the close time

  Task 2: Given a week of highly-volatile trading in a Best New Artist market, the agent must forecast the winner using limited queries to social media APIs.

  Task 3: Forecast a market involving a major celebrity where a technical glitch causes a 24-hour data outage, followed by contradictory statements from two different media outlets.

* What makes each task challenging for current agents?

  The core challenge for current agents lies in their inability to perform selective, budget-constrained external tool use and to effectively model non-traditional financial signals. Existing systems typically over-rely on structured historical data and fail to dynamically fuse this with high-velocity, unstructured information like leaks, rumors, and social sentiment. This lack of an effective evidence extractor and tool router makes them vulnerable to the emotional trading and sudden information shocks that define pop culture markets.

* How will tasks vary in difficulty/complexity?

  Task difficulty will be scaled by varying four key parameters. Complexity increases with a shorter Time to Resolution (e.g., hours before close), a lower Signal-to-Noise Ratio (e.g., contradictory rumors versus official news), a tighter Tool Budget (forcing strategic information retrieval), and an environment where the market is fully driven by immediate, external news events rather than historical price action.

### 3\. Success Criteria

* How will you determine if an agent successfully completes a task?

  The agent successfully completes a task if it produces a probability that beats the three baselines we are measuring against. 

* What are the objective metrics? (e.g., accuracy, completion rate)  
  Accuracy, brier score for all benchmarks

* What are the subjective metrics? (e.g., quality, user satisfaction)  
  Kalshi does not lend itself to many subjective metrics, as the main goal is to make money. Subjective metrics are hard to measure and relatively unimportant in this scenario, so there will not be any.

### 4\. Benchmark Independence

* Explain how your benchmark can be used independently by other researchers  
  Other researchers can backtest our benchmarks using kalshi’s API and internet wayback machine, with historical market and social data.

* How will you document the benchmark for others to use?

* What data or resources are needed to run the benchmark?

## Part III: Agent Design (Neil \+ Sophia)

Describe your planned agent implementation:

### 1\. Agent Architecture

* What is the high-level architecture of your agent?

  Inputs to our agent will be market snapshot(s) with titles, rules/resolution criterion, close time, current implied probabilities, recent price path (maybe data), and optional news or search results. The output will be a forecast at a timestep difference or a forecast of price at close time as well as an uncertainty and calibration score (essentially a confidence score). We would also want the agent to advise whether to forecast or abstain on the market. 

* What are the key components? (e.g., planner, executor, memory, tools)

  Key components of our agent will be the market scanner, a main planner, a tool router, a memory system with short term and long term market memory, potentially a risk controller and lastly an auditor. Ideally, our agent will scan the pop culture markets, plan and choose top few event contracts to forecast, tool use will fetch information such as news and internet search for bias, and an evidence extractor will convert the text to unstructured signals which are then forecasted output probabilities. 

### 2\. Technical Approach

* How will your agent process inputs and generate outputs?

  The agent operates in discrete forecasting episodes. For each episode, it first constructs a structured state representation from raw market inputs, including recent price trajectories, volatility and liquidity proxies, time-to-resolution, and event-level metadata specific to pop culture markets (e.g., award type, nomination phase, ceremony date). These signals are normalized and combined into a fixed-length representation that captures both market dynamics and event context. External information such as internet use or news/announcements are accessed only if explicitly invoked by the agent under a strict tool budget and is converted into structured evidence features rather than used as raw text. Given the constructed state, the agent applies a forecasting module that combines market-based signals with any retrieved evidence to produce a probabilistic forecast for a specified horizon (like a near close implied probability)). Alongside the forecast, the agent estimates uncertainty using recent volatility and model disagreement. If uncertainty exceeds a regime dependent threshold, the agent abstains rather than forcing a prediction. Otherwise, it outputs a calibrated probability forecast, a confidence score, and a brief structured summary of the signals used. This design hopefully ensures that outputs reflect both prediction quality and decision discipline under uncertainty.

* What prompting strategies or algorithms will you employ?

  We will use a structured schema based prompt that forces the LLM to behave as a deterministic agent over typed inputs rather than a writer. Each run should provide a JSON market state to avoid natural language predictions, this state will have recent probabilities, volatility/liquidity proxies, time to resolution, resolution rules, essentially everything we can extract from historical data and data present already in the event on Kalshi). We also hope to include a list of retrieved documents already pre-trimmed to short excerpts with timestamps and source labels so that the system prompt then requires the model to output only a validated JSON object with fields such as market selection, forecast (p\_hat and horizon), any uncertainty, and abstain reasons. 

* How will your agent handle errors or unexpected situations?

  If an external tool call fails or it cannot find any external data/or maybe returns not so useful information, the agent will fall back to a market-only based forecast without retrying again and again and going in a loop. When signals that it finds might be contradictory or incomplete, the agent will increase its uncertainty score rather than sticking to a direction and this could trigger abstention. Missing data or late stage noise as well as noisy data throughout can also escalate uncertainty instead of being useful for the agent in determining the outcome of a specific event contract.

### 3\. Baseline Comparisons

* What existing agent systems or approaches will you compare against?

- Market-only baseline (how well do we do without external tools)  
- Existing Kalshi agents  
- Potentially find standardized benchmarks to compare against…?  
- Ground-truth comparison  
- Use a judge to evaluate output of other models  
- Compare agent reasoning paths to manual reasoning paths (human review)

* How will you ensure fair comparison?

- Ensure models are evaluated on identical historical markets

* Why are these appropriate baselines?

  Ideas:

- Allow us to isolate value of external tools, structured planning, let us know if we need to calibrate  
- Allow us to ensure the decisions made by AI agents are judged and “fair”

## Part IV: Resources and Timeline (Sophia and Bhavyaa)

### Resources

* What APIs, tools, or computational resources do you need?

  Our system will require access to Claude Developer API/OpenAI API for agentic reasoning and tool orchestration. We’ll also access news and search APIs (e.g., web search tools and media aggregation APIs) to retrieve real-time external signals. In addition, we will require access to historical and live market data from Kalshi, such as previous pop culture market prices and resolution outcomes. Lastly, we’ll need API keys for external services and storage for scraped news and market data.

* What LLMs or models will you use?

  We plan to use a lightweight model (e.g., GPT-4o mini or Claude Sonnet 4.5) for structured probabilistic forecasting and summarization. We might use a more capable model similar to Claude Sonnet for reasoning to handle complex agentic planning under budget constraints. Using varying model tiers will allow us to balance 

* How will you get access to necessary resources?

  We’ll source historical pop culture market data from publicly available market archives or insights published by Kalshi. We will also plugin and use Kalshi’s API (click [HERE](https://docs.kalshi.com/welcome)) for any development/accessing or computing previous historical market data. News and online media data will be collected via APIs or scraping via publicly accessible sources. API credits for Claude and OpenAI models will be obtained and funded by the team.

* Estimated costs (if any)

  We estimate spending approximately $100-150 total credits,  with room to grow depending on query volume and experimental scale.

### Timeline

* High-level timeline for benchmark development

* High-level timeline for agent implementation

* Key milestones

- Develop a prediction for one event, whether it’s wrong or right  
- Achieve a successful prediction for one event

## Grading Rubric (20 points)

* **Problem and Motivation** (5pt): Is the problem clearly articulated and well-motivated?

* **Benchmark Design** (5pt): Is the benchmark design detailed, appropriate, and independent?

* **Agent Design** (5pt): Is the agent approach clearly described with sufficient technical detail?

* **Clarity** (5pt): Is the writing clear and easy to follow for a technical expert?