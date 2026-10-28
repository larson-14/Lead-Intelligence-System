# Alignment with Mini_Project_Brief.docx

Reviewed against the complete brief, including its grading table. Status after implementation on 28 October 2026. “Aligned” means the implemented behavior meets the stated requirement; it is not a claim of conversion accuracy or an instructor's grade.

| Requirement from the brief | Current implementation/evidence | Alignment |
|---|---|---|
| Command-line tool ingesting the six specified CSV fields | `lead_qualifier.py`, `ingestion.py`; all three fixtures run | Aligned |
| Score fit from 1–10 with a qualification rubric | Four weighted factors; local score bounds, explicit assumptions and unrounded decisions | Aligned; business assumptions need sales validation |
| 3–5 clear factors with explicit weights/logic | Size 30%, industry 30%, source 25%, recency 15%; policy in rubric.json and OPERATIONS.md | Aligned |
| Qualified/rejected/review decisions with reasoning | Every row has decisions, factor reasons, evidence coverage and review flags | Aligned |
| Assign outreach priority and priority rank | Configurable priority thresholds and sorted outreach queue; deterministic tie-breaking | Aligned |
| Personalized first message for qualified leads | Source-specific approved templates with name, company, industry and seller context; suppressed for unready leads | Aligned under declared seller assumption |
| Messaging excellent band: on-brand, 2–3 unique variants | Demo, referral, educational and discovery variants; model selects from valid choices | Implemented; live model selection blocked, real-brand approval pending |
| Must use an LLM API | LiteLLM integration makes actual requests; live smoke and full-scale attempt hit insufficient Anthropic credit | Partially aligned: API integration exists and was exercised, successful enrichment not demonstrated |
| Batch requests, not an API request per lead | 100-lead simulated success uses 10 batches of 10; bounded retry loop | Aligned technically; successful live batch run pending |
| API-failure/rate-limit handling | Retry tests, partial-item validation, fallback and fatal-error circuit breaker; live credit failure preserves 100 results | Aligned |
| Process at least 100 leads without manual intervention | Offline 100-lead run succeeds; simulated 100-lead LLM run succeeds; live failure path writes all 100 rows and exits 2 | Aligned for processing/fallback; successful live enrichment pending |
| At least 30 diverse sample leads | `leads.csv` is the supplied 100-lead fixture; original 29/20/100 files retained | Aligned |
| Mix of wins/rejects/unclear cases | Full-scale results: 29 qualified, 1 rejected, 70 review; independent unit cases exercise clear policy outcomes | Aligned; no conversion labels supplied |
| JSON/CSV report with per-lead score, decision, reasoning, rank | Both formats regenerated from the same current offline run; metadata sidecar for CSV | Aligned |
| Aggregate total, qualified %, common rejection reasons | Report summaries and factor-based rejection counts | Aligned |
| Flagged/disqualified leads and actionable priority queue | Full lead records plus sorted outreach/review ID queues and recommended actions | Aligned |
| 3–5 sample outreach messages | Five samples, preferring variant diversity and then priority | Aligned |
| README maximum one page; run instructions, rubric, limitations | Concise README; detailed policy, operations and evaluation moved to separate files | Aligned in intended concise scope; physical pagination depends on renderer |
| Clean/readable/commented source | Separate modules, typed policy/input/result contracts, docstrings and policy comments | Implemented; readability remains a reviewer judgment |
| Test prompt on 5–10 leads before full run | Actual 5-lead smoke attempted first; contract and adversarial tests; explicit 100-lead simulation | Partial: actual prompt quality cannot be assessed until provider succeeds |
| Faster than manual 8–12 minutes per decision | Local 100-lead compute run takes milliseconds; full process benchmark recorded separately | Local processing aligned; live latency and sales time savings unproven |
| Human loop for unclear cases | Missing evidence and borderline fit go to review with reasons; missing contact treated separately | Aligned |
| Solve the sales bottleneck usefully | Differentiated ranking and queues exist, but 70% still require review | Partially aligned: sales-policy validation/enrichment needed to reduce review workload |
| Keep the system simple | One local Python application, no database/services/agent framework | Aligned |
| ZIP source, sample data, output, README; exclude keys/large intermediate files | Allowlisted `build_submission.py`; ZIP contents checked; `.env`, environment and legacy artifacts excluded | Aligned |

## Implemented improvement plan

1. **Completed:** replace constant fit scores with an explicit business policy and four active factors; keep unknown evidence explicit and historical dates reproducible.
2. **Completed:** separate modules, fix configuration/response crashes, reject malformed sizes/dates, isolate bad provider items, add controlled retries and fatal-error handling.
3. **Completed:** seller context, approved variants, grounded LLM evidence selection and safe local rendering.
4. **Completed:** sorted queues, stable fingerprints, contact readiness, duplicates, explicit review reasons, atomic exports and reproducibility metadata.
5. **Completed:** expanded tests, offline fixture runs, simulated full-scale provider success, live smoke/failure-path validation, concise docs, label-evaluation tooling and clean packaging.

## Remaining improvement plan and dependencies

1. **Provider account owner:** add Anthropic credit or configure another authorized funded provider. Then run the README 5-lead smoke command; inspect messages; run 100 leads with `--require-llm`. Acceptance: zero failed batches, 100 successful item enrichments, supported messages, actual latency/usage recorded. The account failure cannot be repaired in application code; no payment or account changes were attempted.
2. **Sales/product owner:** approve the real seller claims and ICP. Review high-scoring but low-fit leads and decide when to nurture, enrich or reject. Implement the approved policy by editing the validated JSON configuration and adding expected cases. Acceptance: independently agreed decisions and lower manual-review load without an unacceptable false-rejection rate. No numerical business target is invented here.
3. **Sales operations:** collect independent qualification and conversion labels with a fixed outcome horizon. Use the included evaluator on a company-separated temporal holdout. Acceptance: agreed precision/recall at sales capacity and confidence intervals; no unsupported “highest accuracy” claim.

The supplied brief does not require automatic email sending, CRM integration, a UI, model training or a distributed service. Its outreach deliverable is a prioritized queue and first-message drafts; the implementation intentionally stays within that scope.
