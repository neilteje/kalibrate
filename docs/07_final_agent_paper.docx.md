# Assignment 7: Final Agent Paper

**Due Date:** May 5, 2026 (Tuesday, Week 15 \- Last day of presentations) **Format:** PDF ([ICLR LaTeX template](https://github.com/ICLR/Master-Template/raw/master/iclr2026.zip)) **Page Length:** 3-4 pages (excluding references and appendix) **Submission:** PDF \+ Code on Canvas (one per group)

## Overview

Submit your final agent paper with complete experimental results and analysis. This paper documents your agent implementation and demonstrates its performance on your benchmark.

## Changes from Draft

Refine your draft agent paper by:

1. **Completing experiments:** Include full experimental results on all benchmark tasks

2. **Deepening analysis:** Provide thorough analysis of results, successes, and failures

3. **Addressing feedback:** Incorporate all TA feedback from your draft

4. **Polishing writing:** Ensure clarity, fix errors, improve flow

## Final Paper Structure

Your final paper should include all sections from the draft (see Draft Agent Paper assignment), fully complete:

1. Introduction

2. Related Work

3. Agent Design

4. Experimental Setup

5. Results

6. Discussion

7. Conclusion

8. References

## Additional Requirements

### Changelog

Include a brief changelog (1 paragraph) at the end of your submission describing: \- Major changes since the draft \- How you addressed TA feedback \- Any implementation or experimental changes

### Code Submission

Submit alongside your paper:

1. **Agent Implementation:** Complete source code for your agent

   * Should be well-organized and documented

   * Include requirements.txt or environment.yml

2. **README:** Clear documentation including:

   * Setup instructions

   * How to run the agent

   * How to reproduce experiments

   * Dependencies and requirements

3. **Evaluation Scripts:** Code used to run your experiments

   * Scripts to evaluate agent on benchmark

   * Scripts to generate results and figures

4. **Experiment Data (Optional):** Raw experimental results

   * Can be useful for reproducibility

   * Not required if experiments are fast to rerun

## Results Requirements

Your final paper must include:

### Complete Results

* Performance on **all** benchmark tasks

* Results for your agent and **all** baseline comparisons

* Multiple trials to show consistency (where applicable)

* Statistical significance testing (if appropriate)

### Comprehensive Analysis

* **Quantitative:** Tables and graphs showing performance metrics

* **Qualitative:** Example successes and failures with analysis

* **Breakdown:** Performance by task type, difficulty, or other dimensions

* **Ablation:** Results with key components removed (if applicable)

### Honest Reporting

* Report both positive and negative results

* Acknowledge unexpected outcomes

* Discuss limitations openly

## Discussion Requirements

Your discussion should:

1. **Explain results:** Why did you see the results you saw?

2. **Analyze strengths:** What does your agent do well and why?

3. **Analyze weaknesses:** What does your agent struggle with and why?

4. **Compare to baselines:** What explains differences in performance?

5. **Identify patterns:** What trends or patterns emerge from results?

6. **Discuss limitations:** What are the boundaries of your approach?

7. **Suggest improvements:** How could your agent be enhanced?

## “What if my results are negative?”

**Negative results are completely acceptable** if you:

* Report them honestly and thoroughly

* Provide deep analysis of why performance was lower than expected

* Discuss what you learned from the failures

* Propose concrete ideas for how future work could address the issues

* Demonstrate understanding of your agent’s limitations

**We grade on:** \- Quality of analysis and understanding \- Depth of investigation \- Honesty and rigor \- NOT on achieving high performance numbers

A paper with negative results but excellent analysis will receive full credit.

## Quality Expectations

Your final agent paper should be: \- **Publication-ready:** Written at the quality of a workshop or conference paper \- **Complete:** All experiments finished, all sections polished \- **Rigorous:** Thorough experimental methodology and analysis \- **Honest:** Transparent about results, limitations, and failures \- **Reproducible:** Others could reimplement and verify your results

## Page Length

* **Required:** 3-4 pages for main content (excluding references)

* **Under 3 pages:** Likely missing important details or analysis

* **Over 4 pages:** Needs to be more concise

The page limit does not include: \- References \- Appendix (if you include one)

## Grading Rubric (40 points)

* **Agent Design** (12pt): Is the agent clearly described with sufficient technical detail? Is the approach sound?

* **Experimental Rigor** (8pt): Are experiments complete and well-executed? Is methodology sound?

* **Results and Analysis** (12pt): Are results presented clearly? Is analysis thorough and insightful?

* **Discussion** (4pt): Are limitations acknowledged? Are failures honestly analyzed?

* **Writing Quality** (2pt): Is the paper well-written and well-organized?

* **Feedback Integration** (2pt): Did you address TA feedback from the draft?

## Submission Checklist

Before submitting, ensure you have:

* Final agent paper PDF (3-4 pages \+ references)

* Changelog describing changes from draft

* Agent source code with documentation

* README with setup and reproduction instructions

* Evaluation scripts

* Requirements/dependencies specification

* All experimental results complete

* Statistical analysis included (if appropriate)

* Addressed all TA feedback from draft

## Common Issues to Avoid

1. **Incomplete experiments:** Must evaluate on ALL benchmark tasks

2. **Shallow analysis:** Don’t just report numbers—explain what they mean

3. **Ignoring failures:** Must analyze what doesn’t work, not just what does

4. **Missing baselines:** Need proper comparison to other approaches

5. **Unclear implementation:** Need sufficient detail for reproduction

6. **Page limit violations:** Stay within 3-4 pages for main content

## Integration with Benchmark Paper

Note that your two papers should work together: \- **Benchmark paper:** Documents your task suite independently \- **Agent paper:** References benchmark paper and focuses on your agent \- **Together:** They form a complete picture of your research

## Post-Submission

After the semester, consider: \- Submitting to workshops or conferences \- Sharing your agent implementation on GitHub \- Writing a blog post about your findings \- Continuing to develop and improve your agent