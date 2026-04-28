# Assignment 4: Draft Benchmark Paper

**Due Date:** April 7, 2026 (Tuesday, Week 11\) **Format:** PDF ([ICLR LaTeX template](https://github.com/ICLR/Master-Template/raw/master/iclr2026.zip)) **Page Length:** 3-4 pages (excluding references) **Submission:** Canvas (one per group)

## Overview

Write a draft paper documenting your benchmark design. This paper should be **independent** of your agent implementation—someone else should be able to use your benchmark to evaluate their own agents.

## Required Sections

Your benchmark paper should include:

### 1\. Introduction (\~0.75 pages)

* **Motivation:** What problem does your benchmark address?

* **Limitations of existing benchmarks:** Why are current benchmarks insufficient?

* **Your contribution:** What makes your benchmark unique or valuable?

* **Overview:** Brief summary of your benchmark design

### 2\. Related Work (\~0.5 pages)

* **Existing benchmarks:** Discuss 3-5 related benchmarks in similar or adjacent domains

* **Comparison:** How does your benchmark differ? What gap does it fill?

* **Task domains:** Relevant work on the application domain you’re targeting

Keep this section focused—you’re not writing a comprehensive literature review, just positioning your benchmark relative to existing work.

### 3\. Benchmark Design (\~1.5 pages)

This is the core of your paper. Include:

#### *Task Domain and Scope*

* What domain does your benchmark cover?

* What aspects of agent capability does it test?

* What is in scope vs. out of scope?

* State explicitly whether you followed an existing benchmark framework, and which one

#### *Task Descriptions*

* Overview of all 10 (or 20\) tasks

* Detailed description of 2-3 representative tasks as examples

* For each example task:

  * Input format and specifications

  * Expected output or behavior

  * Success criteria

  * Why this task is challenging for agents

#### *Task Design Principles*

* What principles guided your task design?

* How did you ensure diversity and coverage?

* How did you calibrate difficulty?

#### *Difficulty Distribution*

* Table or chart showing task difficulty levels

* How did you determine difficulty?

* Distribution across easy/medium/hard

### 4\. Evaluation Protocol (\~0.5 pages)

Explain how agents should be evaluated on your benchmark:

* **Metrics:** What should be measured? (success rate, quality scores, etc.)

* **Scoring:** How are tasks scored?

* **Aggregation:** How are scores combined across tasks?

* **Reporting:** What results should be reported?

### 5\. Benchmark Validation (\~0.5 pages)

Provide evidence that your benchmark is well-designed:

* **Pilot testing:** Did you test tasks with humans or baseline agents?

* **Task quality:** How did you verify tasks are clear and well-specified?

* **Inter-rater reliability:** If using human evaluation, what is the agreement rate?

* **Preliminary results:** Any early testing results (can use simple baselines)

### 6\. Conclusion (\~0.25 pages)

* **Summary:** Recap your benchmark’s key features

* **Impact:** How will this benchmark benefit the research community?

* **Future work:** Potential extensions or variations

### 7\. References

* Include all cited papers and resources

* Follow proper citation format

## Additional Materials

### Appendix (Optional, not counted toward page limit)

You may include: \- Full task specifications \- Example inputs and outputs \- Scoring rubrics \- Data collection templates

### Figures and Tables

Include relevant visual elements: \- **Required:** Table summarizing all benchmark tasks \- **Suggested:** \- Diagram of task distribution by difficulty/type \- Example task workflow or interaction \- Scoring rubric table \- Preliminary results (if available)

## What Should Be Complete vs. Outline

**Must be complete:** \- Introduction \- Benchmark Design section with all task descriptions \- Evaluation Protocol

**Can be less polished:** \- Related Work (can have placeholders for papers you plan to cite) \- Benchmark Validation (can use preliminary results or planned validation) \- Conclusion (can be brief)

## Writing Tips

1. **Focus on independence:** Write as if your reader will use this benchmark without access to your agent

2. **Be precise:** Provide exact specifications for tasks and evaluation

3. **Include examples:** Show concrete examples of tasks and expected behaviors

4. **Document assumptions:** Be clear about any assumptions or requirements

5. **Make it reproducible:** Someone else should be able to implement your benchmark from your paper

## Grading Rubric (15 points)

* **Benchmark Design** (7pt): Are tasks well-designed, clearly specified, and appropriately challenging?

* **Independence** (3pt): Can the benchmark be used independently by other researchers?

* **Evaluation Protocol** (2pt): Is the evaluation methodology clear and rigorous?

* **Clarity** (3pt): Is the paper well-written and well-organized?

## Notes

* This paper focuses solely on the **benchmark**—save agent details for the agent paper

* Think of this as documentation that will be released alongside your benchmark

* You’ll refine this for the final benchmark paper submission