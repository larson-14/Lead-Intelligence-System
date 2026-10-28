# Lead Intelligence System: implementation review

Reviewed 28 October 2026 against the complete Mini_Project_Brief.docx, supporting assignment notes, all application and test code, rubric, datasets, and saved reports. Application code and scoring configuration were not changed. Secrets were not inspected and no live provider requests were made.

## Assessment

The deterministic scoring engine, configurable rubric, batched enrichment, per-lead explanations, and fallback reporting are a sound foundation. The main obstacle is business judgment: the shipped rubric effectively scores only acquisition source. More model sophistication will not fix that. Define a defensible ideal customer profile (ICP), make uncertainty explicit, prove the LLM path works, and close the reproduced crash paths before expanding architecture.

The assignment intentionally supplies no outcome labels. Therefore predictive accuracy cannot be calculated from these files. Assignment correctness means faithful, consistent application of a stated policy. Actual sales accuracy requires independently collected dispositions and conversion outcomes.

## Evidence

- All 12 existing unit tests passed, including mocked provider success and fallback cases.
- Fresh local scoring: training 29 = 10 qualified / 0 rejected / 19 review; testing 20 = 7 / 0 / 13; full-scale 100 = 35 / 0 / 65.
- The saved output_report.json has 10 failed LLM batches and all 100 leads marked failed. testing_report.json has two failed batches and all 20 leads marked failed. These demonstrate fallback, not successful live enrichment. The reports do not record enough error detail to establish the original failure cause.
- All 35 qualified full-scale leads score 7.0 and receive medium priority. Their source is either inbound demo request or referral.
- Reproduced uncaught TypeError for a provider response whose lead_id is an array.
- Reproduced a rubric that passes validation with unknown_source_score set to the string "3", then crashes on an unmapped source.
- Overlapping and gapped size bands pass validation. A malformed date and company name "Unknown" can qualify without flags; size "5,0" is silently interpreted as 50.

## Prioritized findings

### P1: Replace the source-only qualification policy

Location: rubric.json; lead_qualifier.py:228.

Size and industry are constant at 5, so score = 3 + 0.4 × source_score. Configured known sources yield scores from 4.6 to 7.0; the unknown default yields 4.2. No input can reach the rejection threshold of 4 under the current rubric. No input can reach high priority at 8.5 either. Three factor names therefore mask one effective factor, leaving the brief's emphasis on sound judgment weakly satisfied.

Define the seller's product, target customer, disqualifiers, and assumptions. The brief says the seller is a mid-market SaaS company; it does not establish that its buyers must be mid-market or SaaS. Do not infer that customer profile from the seller's description. Source is an acquisition/engagement proxy, not evidence of budget, authority, or an active buying project. Referral should not automatically equal a demo request.

Unknown fit should trigger an explicit uncertainty flag rather than an apparently authoritative fit score. Do not lower the rejection threshold merely to manufacture rejected examples; derive rejection rules from the stated ICP and show cases that exercise them.

### P1: Demonstrate successful LLM integration and on-brand messaging

Location: lead_qualifier.py:214, 371; output_report.json; testing_report.json.

The brief explicitly requires an LLM API. Integration code exists, but saved evidence shows complete enrichment failure. Diagnose with a small representative batch, validate the returned schema, then run the 100-lead demonstration using --require-llm. Capture sanitized error categories, model, latency, usage, and success/failure counts. Preserve the existing fallback behavior.

Neither the prompt nor configuration defines the seller's product, approved value proposition, brand voice, or permissible claims. The fallback assumes the seller offers lead prioritization, which the brief does not specify. Add explicit seller configuration and 2–3 controlled message variants, for example demo acknowledgment, referral introduction, and educational follow-up. Include one supported lead detail and one clear call to action. Do not fabricate referral names, prior conversations, pain points, or product capabilities. Evaluate factuality separately from JSON validity.

### P1: Make malformed LLM responses fail safely

Location: lead_qualifier.py:434, 464.

Membership testing occurs before checking that lead_id is a string. An array or object ID raises TypeError, which bypasses the LLMError fallback and prevents report generation. Validate every field's type before use; convert expected response-validation failures into LLMError. Test null/empty choices, wrong root types, missing/duplicate/extra IDs, malformed JSON, blank explanations, and outreach on nonqualified leads.

Use a response schema where the selected provider supports it, with local validation in every case. Treat lead fields as untrusted data in the prompt. Instructions alone cannot ensure factual explanations. Keep deterministic reasoning authoritative; reject contradictory drafts or mark them for review. Isolate invalid items so one bad record does not discard otherwise valid batch results, while preserving an explicit status for every input.

### P2: Normalize and validate rubric configuration once

Location: lead_qualifier.py:71, 200, 209.

Validation checks numeric convertibility but returns original values. An unmapped lookup returns its default without conversion, allowing numeric strings to crash multiplication. Normalize accepted numbers into typed values or reject strings consistently. Reject booleans as numbers, require finite values, detect normalized duplicate category keys, and validate nonoverlapping size bands with explicit coverage/default behavior. Overlap currently makes list order decide the score; gaps silently use a default.

Compare thresholds with the unrounded internal score, rounding only for display, or explicitly document rounded-score decisions. Move hardcoded priority thresholds into the rubric so changing qualification thresholds does not leave contradictory priorities.

### P2: Separate business fit, missing evidence, and contact readiness

Location: lead_qualifier.py:185, 228.

Unknown detection recognizes only the literal word "unknown" or its prefix. A new source such as "Partner event" receives the default but no unknown-source flag. Industry mappings similarly fall back silently. Record whether a score came from a mapping, a band, or a default. Distinguish known poor fit from unavailable evidence.

A missing contact name currently forces review even if company fit is otherwise clear. Represent fit_decision, data_quality_flags, and outreach_ready separately; a contact-enrichment task need not consume a qualification decision. Reject malformed employee counts rather than removing arbitrary commas. Parse dates for validity even if recency remains excluded from scoring. Add a review reason for borderline scores; currently such records can have an empty review_flags list.

Dates are historical (2022–2024). If recency is introduced, require an explicit --as-of date for evaluation and record it in the report. A declared synthetic snapshot such as 2024-01-20 is more interpretable than judging this fixture against today's date. Validate future dates relative to that snapshot. Recency should represent observed engagement, not an assumed buying timeline.

### P2: Make the report a usable sales queue

Location: lead_qualifier.py:328, 497, 541.

Qualified leads have rank fields, but the lead list remains in input order and sample messages select the first five qualified inputs. Add explicit priority_queue and review_queue sections, sorted by useful business signals, with recommended action and review reason. A 65% review rate leaves much of the original manual bottleneck unresolved; measure that workload without forcing uncertain leads into rejection.

Tie-breaking uses row-derived IDs, while README promises company-name ordering as well. Reordering inputs can alter tied ranks. Align documentation and implementation; describe ties honestly rather than implying measured differences in propensity. Keep row provenance and add stable source IDs or content fingerprints when needed for reruns and deduplication.

JSON embeds the rubric, but CSV omits its version and failed-batch count. Include a run manifest with input hash, rubric hash/version, code version, model/prompt version, as-of date, and LLM status. Write reports through a temporary file followed by atomic replacement. Handle unreadable dotenv files inside main's error boundary; load_dotenv currently runs before its try block.

## Proposed rubric to validate, not an accuracy claim

First declare an illustrative business assumption, for example: a lead-workflow SaaS product serving 11–500 employee B2B companies. This is a proposed scenario, not a fact established by the brief. Industry alone does not prove a company sells B2B; treat it as a proxy and request evidence when necessary.

| Factor | Starting weight | Policy to make explicit |
|---|---:|---|
| Company-size fit | 30% | Target 11–500 = 10; adjacent 501–5000 = 6; 1–10 = 3; larger = 4, subject to actual product economics |
| Industry/use-case fit | 30% | Core supported vertical = 10; adjacent = 6; validated unsupported use case = 2; unmapped = unknown |
| Observed engagement/source | 25% | Demo request = 10; referral = 8; sales call = 6; webinar = 5; content = 3; outbound LinkedIn = 2 |
| Interaction recency | 15% | At declared snapshot: 0–30 days = 10; 31–90 = 7; 91–180 = 4; older = 2; missing/invalid = unknown |

Provisional decisions: qualify at >=7.5 with adequate fit evidence; reject at <=4 with adequate evidence or an explicit business disqualifier; otherwise review. Distinguish hard disqualifiers from weak signals. Represent unknown factors with score bounds and evidence coverage, not fabricated precision. If plausible bounds cross a decision threshold, route to review. Document these starting numbers as hypotheses and revise against human judgments/outcomes; they are not optimized weights.

If there is no defensible relationship between date and lead quality, retain three meaningful factors and exclude recency with a documented rationale. Do not invent budget or authority signals from these six input fields.

## Architecture recommendation

Keep a single local application for 100–1,200 leads. Split responsibilities into small modules only as fixes make that useful:

CSV intake → typed normalization and validation → feature extraction → deterministic rubric and decision policy → batched LLM explanation/message drafting → output validation → sales queues and report.

Use typed Lead, Rubric, Decision, and EnrichmentResult structures. Keep scores and decisions independent of provider output. A modest separation into ingestion.py, scoring.py, llm_client.py, reporting.py, and cli.py is enough; no database, vector store, agent framework, or distributed service is justified by the supplied workload. Add bounded concurrency or caching only if measured runtime warrants it. Key any cache by normalized inputs plus rubric, prompt, and model versions.

## Evaluation plan

1. Policy correctness: build independent expected cases covering each band, exact thresholds, critical missing fields, explicit rejection, borderline review, and priority ties. Expected answers should come from the written policy, not copied production calculations.
2. Robustness: test the reproduced failures, malformed CSV records, invalid rubric configurations, provider timeout/rate-limit sequences, partial responses, and report-write failures. Test that failures preserve local results and --require-llm exits nonzero. Current provider calls are mocked; retry timing and live compatibility are not proven by the 12 tests.
3. Message quality: review 5–10 representative leads before scale-up. Score factual support, business relevance, personalization, tone, call to action, and variant diversity. Include adversarial text in lead fields and verify it cannot redirect the task.
4. Operational usefulness: measure end-to-end runtime, cost, LLM success rate, review coverage, and sales handling time. Compare with the brief's 8–12 minute manual baseline using actual measured runs.
5. Predictive validity: collect sales-reviewed labels with a precise definition of qualification and a fixed outcome horizon. Evaluate precision/recall and precision at the team's outreach capacity; track missed opportunities and abstention/review coverage. Evaluate conversions separately because sales acceptance is not conversion. Audit a sample of rejected leads to reduce selection bias. Use company-separated, time-based holdouts. The 28 overlapping training/full-scale records make those files unsuitable as independent train/test evidence. Small samples require uncertainty reporting; do not claim a particular accuracy improvement from this review.

## Assignment readiness

| Brief requirement | Current assessment | Next action |
|---|---|---|
| 100+ leads without intervention | Local scoring produces 100 results; existing tests pass | Add malformed-response tests and successful strict LLM run |
| 3–5 clear qualification factors | Three named factors, only source varies | Declare ICP and activate meaningful fit factors |
| LLM API in batches | Implemented; saved live reports show failure | Diagnose and retain successful batch evidence |
| Personalized, on-brand, 2–3 variants | Lead details exist; fallback is one template and brand is unspecified | Add seller context and controlled variants |
| Decisions, stats, reasoning, rank | Present; rejection branch unreachable with shipped rubric | Fix policy; make queues and review reasons actionable |
| API/missing-data robustness | Useful fallback and missing-field handling; reproduced crash gaps | Expand contract and failure tests |
| At least 30 diverse sample leads | 100-lead file satisfies count; training file alone has 29 | Clearly identify full-scale file as submission sample |
| README one page maximum | Existing README substantially exceeds intended concise scope | Move detailed setup/evaluation into separate docs |

Submission cleanup: training_report.jso has an unusual extension. Regenerate canonical reports together after final changes to avoid stale artifacts. Explicitly exclude .env and .venv when building the submission ZIP; .gitignore does not control ZIP contents. Preserve a concise README with run command, rubric rationale, and known limits.

Recommended order: (1) define business assumptions and policy, (2) fix response/configuration crashes, (3) prove live LLM enrichment and messaging quality, (4) improve queues and provenance, (5) collect independent evaluation evidence. This addresses the project's core judgment requirements before adding infrastructure.
