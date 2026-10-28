# Evaluation and remaining business work

The implementation proves policy consistency and technical robustness, not conversion accuracy. There are no outcome labels in the supplied datasets; 28 training records also appear in the full-scale set. Do not report these as independent training/test accuracy evidence.

1. Agree the real seller product, ICP, qualification definition and contact policy with sales. Review 5–10 mixed cases (wins, rejects, missing data, borderline) independently of the code. Resolve reviewer disagreements and document rationales.
2. Replace the demonstration seller and policy assumptions with approved facts. Validate whether recency has business value; use a fixed snapshot for historical evaluation. Test policy changes on held-out cases rather than tuning to produce a desired rejection/review count.
3. Collect dispositions and fixed-horizon outcomes. Keep sales acceptance separate from conversion. Include audited rejected and review leads to reduce selection bias; use company-separated temporal holdouts.
4. Fill `validation/labels_template.csv` with independent 0/1 qualification labels, then run `python evaluate.py --report output_report.json --labels validation/labels_template.csv --k 10`. The evaluator rejects incomplete or duplicate cohorts and reports precision, recall, precision at outreach capacity, false rejections, positives awaiting review, review coverage and a 95% Wilson precision interval. Empty labels intentionally fail; no synthetic business labels are invented.
5. Evaluate messaging on factual support, lead relevance, approved claims, tone, variant diversity and one appropriate call to action. The constrained renderer guarantees allowed wording, but whether that wording persuades real buyers requires human review and outcome measurement. Do not use an LLM judging its own responses as the only quality measure.
6. Measure sales handling time, acceptance rate, API success, actual provider cost and end-to-end runtime. Compare with the brief's 8–12 minute manual decision baseline using the same workflow and cohort.

## Open improvement work

- **Provider access:** fund the configured Anthropic account or configure another authorized working provider; rerun the 5-lead smoke test before the strict 100-lead demonstration. The observed account error is insufficient credit. Do not treat the simulated provider run as live success.
- **Review workload:** the current explicit policy reviews 70/100 full-scale leads (previous baseline 65/100). It offers more differentiated scores, but does not yet solve most of the manual-review bottleneck. Sales must validate which low-fit/high-engagement cases should be nurtured, rejected or investigated. After agreement, add evidence-backed disqualifiers or enrichment and re-evaluate missed opportunities alongside review coverage. Do not force rejection merely to improve automation statistics.
- **Business validation:** approve ICP and seller facts before real outreach. The brief supplies neither product facts nor conversion labels; code cannot establish them.
- **Model freedom:** if business owners prefer free-form generated messages, add schema-constrained drafts with a separate factuality/claim-validation and human approval stage. The current implementation intentionally uses LLM selection plus local rendering to prevent hallucinated claims.

No microservices, database, vector store or agent framework is justified at this scale. Add caching/concurrency only after measuring a runtime bottleneck; any cache must incorporate input, rubric, seller, prompt and model versions.
