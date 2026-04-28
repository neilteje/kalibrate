# Assignment 6: Final Benchmark Paper

**Due Date:** May 5, 2026 (Tuesday, Week 15 \- Last day of presentations) **Format:** PDF ([ICLR LaTeX template](https://github.com/ICLR/Master-Template/raw/master/iclr2026.zip)) **Page Length:** 3-4 pages (excluding references and appendix) **Submission:** PDF \+ Benchmark Materials on Canvas (one per group)

## Overview

Submit your final benchmark paper with complete documentation. This paper should enable other researchers to use your benchmark to evaluate their own agents.

## Changes from Draft

Refine your draft benchmark paper by:

1. **Addressing feedback:** Incorporate all feedback from your draft

2. **Completing validation:** Include results from final benchmark validation

3. **Polishing writing:** Ensure clarity, fix typos, improve flow

4. **Adding missing elements:** Complete any sections that were incomplete in draft

## Final Paper Structure

Your final paper should include all sections from the draft (see Draft Benchmark Paper assignment), fully polished and complete:

1. Introduction

2. Related Work

3. Benchmark Design

4. Evaluation Protocol

5. Benchmark Validation

6. Conclusion

7. References

## Additional Requirements

### Changelog

Include a brief changelog (1 paragraph) at the end of your submission describing: \- Major changes since the draft \- How you addressed TA feedback \- Any design changes or refinements

### Benchmark Materials

Submit alongside your paper:

1. **Task Specifications:** Complete specifications for all 10 (or 20\) tasks

   * Can be in appendix or separate document

   * Should include inputs, expected outputs, and success criteria

2. **Evaluation Code:** Scripts or code for evaluating agents on your benchmark

   * Should be runnable by others

   * Include README with setup instructions

3. **Data/Resources:** Any data files, examples, or resources needed to use your benchmark

   * Provide instructions for accessing any external resources

4. **Documentation:** Clear instructions for how to use your benchmark

   * How to run an evaluation

   * How to interpret results

   * Any requirements or dependencies

## Validation Requirements

Your final paper must include solid evidence that your benchmark is well-designed:

### Required Validation

* **Human baseline:** Results from human performance on sample tasks

* **Agent baseline:** Results from at least one simple baseline agent

* **Task review:** Evidence of task quality verification (peer review, expert review, or pilot testing)

### Optional Validation

* Inter-rater reliability scores (if using human evaluation)

* Difficulty calibration data

* Coverage analysis showing task diversity

## Quality Expectations

Your final benchmark paper should be: \- **Publication-ready:** Written at the quality of a workshop or conference paper \- **Complete:** All sections fully developed with no placeholders \- **Reproducible:** Sufficient detail for others to use your benchmark \- **Well-validated:** Strong evidence of benchmark quality

## Page Length

* **Required:** 3-4 pages for main content (excluding references)

* **Under 3 pages:** Probably missing important details

* **Over 4 pages:** Needs to be more concise

The page limit does not include: \- References \- Appendix with task specifications (if applicable)

## Grading Rubric (40 points)

* **Benchmark Design** (15pt): Are tasks well-designed, diverse, appropriately challenging, and clearly specified?

* **Independence** (8pt): Can others easily use your benchmark? Is documentation complete?

* **Validation** (8pt): Is there strong evidence your benchmark is well-designed and reliable?

* **Evaluation Protocol** (4pt): Is the evaluation methodology clear, rigorous, and reproducible?

* **Writing Quality** (3pt): Is the paper well-written, well-organized, and publication-ready?

* **Feedback Integration** (2pt): Did you address TA feedback from the draft?

## Submission Checklist

Before submitting, ensure you have:

* Final benchmark paper PDF (3-4 pages \+ references)

* Changelog describing changes from draft

* Complete task specifications (appendix or separate doc)

* Evaluation code with README

* Data/resources needed to run benchmark

* Usage documentation

* Addressed all TA feedback from draft

## Common Issues to Avoid

1. **Vague task specifications:** Tasks must be precise enough to evaluate objectively

2. **Missing validation:** Must have evidence beyond “we think these are good tasks”

3. **Poor documentation:** Others should be able to use your benchmark without asking you questions

4. **Insufficient detail:** Need enough detail for reproduction

5. **Page limit violations:** Stay within 3-4 pages for main content

## Post-Submission

After the semester, consider: \- Publishing your benchmark as a standalone resource \- Sharing on platforms like Hugging Face or GitHub \- Submitting to benchmark tracks at conferences \- Using it in your own future research