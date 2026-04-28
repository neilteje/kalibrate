# Assignment 3: Evaluation Plan

**Due Date:** March 12, 2026 (Thursday, Week 8\) **Word Count:** 1000-1500 words **Submission:** PDF on Canvas (one per group)

## Overview

Develop a detailed evaluation plan for assessing your agent’s performance on your benchmark. This plan will guide your experimental work and form the basis of your results sections in both papers.

## Part 1: Evaluation Objectives

Clearly state what you want to demonstrate:

### Research Questions

* What specific questions will your evaluation answer?

* Examples:

  * “Does our agent outperform baseline approaches on complex multi-step tasks?”

  * “How does agent performance scale with task complexity?”

  * “What types of tasks does our agent handle well vs. poorly?”

### Success Criteria

* What would constitute a successful outcome?

* What results would validate your approach?

* What results would be considered negative or inconclusive?

## Part 2: Benchmark Evaluation Metrics

Define how you will measure performance on your benchmark:

### Primary Metrics

* **Task Success Rate:** Percentage of tasks completed successfully

* **Task Completion Quality:** Quality ratings or scores for completed tasks

* **Efficiency Metrics:** Time, API calls, tokens used, cost per task

* **Error Metrics:** Types and frequencies of errors

### Secondary Metrics (if applicable)

* **Robustness:** Performance on edge cases or adversarial inputs

* **Consistency:** Variance in performance across multiple runs

* **Generalization:** Performance on held-out or modified tasks

* **Human Evaluation:** User satisfaction, preference ratings

### Detailed Metric Definitions

For each metric, specify: \- How it will be calculated \- What constitutes a “good” vs. “poor” score \- How you will aggregate across tasks

## Part 3: Baseline Comparisons

Describe what you will compare your agent against:

### Baseline Approaches

List and describe 2-4 baseline approaches: \- **Simple baselines:** Random agent, rule-based agent, single-prompt agent \- **Existing systems:** Claude, GPT-4, specialized agents from prior work \- **Ablations:** Your agent with key components removed

For each baseline: \- Provide a brief description \- Explain why it’s a relevant comparison \- Describe how you will implement or access it

## Part 4: Experimental Setup

Detail how you will conduct your evaluation:

### Test Procedure

* How will you run each agent on each task?

* How many trials per task-agent combination?

* Will you randomize order to control for effects?

* How will you handle non-deterministic behavior?

### Data Collection

* What data will you log for each trial?

* How will you store and organize results?

* What tools or infrastructure will you use?

## Part 5: Benchmark Validation

Explain how you will validate that your benchmark is well-designed:

### Task Quality

* How will you ensure tasks are clear and well-specified?

* How will you verify that tasks are appropriately challenging?

* Will you pilot test with human subjects?

### Benchmark Coverage

* Do your tasks cover different aspects of the domain?

* Is there appropriate difficulty variation?

* Are there enough tasks to draw meaningful conclusions?

### Benchmark Reliability

* How will you verify that evaluation is consistent?

* Can results be reproduced?

* Are success criteria objective and unambiguous?

## Part 6: Expected Results (Optional)

If you have preliminary data, include: \- Early experimental results \- Pilot study findings \- Observations from initial testing

If you don’t have data yet, you may discuss: \- What results you expect to see and why \- What patterns you anticipate \- How different outcomes would inform your conclusions

## Part 7: Limitations and Threats

Discuss limitations of your evaluation approach:

### Known Limitations

* What aspects of agent performance won’t your evaluation capture?

* What real-world considerations are missing from your benchmark?

* What biases might exist in your task design?

### Threats to Validity

* What factors might confound your results?

* When might your results not generalize?

* What assumptions are you making?

### Mitigation Strategies

* How will you address or control for these limitations?

* What caveats will you include in your conclusions?

## Deliverable Format

Your evaluation plan should read as a detailed experimental protocol that someone else could follow to replicate your evaluation. Include:

1. Clear definitions of all metrics

2. Precise description of experimental procedure

3. Specification of baselines and how they’ll be implemented

4. Discussion of limitations

You may include: \- Diagrams of experimental setup \- Example data collection templates \- Pseudocode for evaluation scripts \- Mock-up graphs or tables showing expected result format

## Grading Rubric (20 points)

* **Evaluation Objectives** (3pt): Are research questions and success criteria clearly defined?

* **Metrics** (5pt): Are metrics well-defined, appropriate, and comprehensive?

* **Baselines** (3pt): Are baseline comparisons appropriate and feasible?

* **Experimental Design** (5pt): Is the experimental setup rigorous and reproducible?

* **Limitations** (2pt): Are limitations and threats honestly acknowledged?

* **Clarity** (2pt): Is the plan clearly written and well-organized?