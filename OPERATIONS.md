# Policy and operations

## Business assumptions

The brief identifies a mid-market SaaS seller but does not specify its product or customer profile. `seller.json` therefore declares a fictional LeadFlow product, approved claims and voice. `rubric.json` explicitly assumes a target of 11–500 employee technology/professional-service businesses. These are editable demonstration assumptions, not established customer facts or learned predictors.

Size scores: 1–10 employees = 3; 11–500 = 10; 501–5000 = 6; larger = 4. Industry scores are explicit core (10), adjacent (6), and lower-fit (3) mappings. Unknown categories remain unknown. Industry is a proxy: it does not prove a B2B use case.

Source scores: demo = 10, referral = 8, sales call = 6, webinar = 5, content = 3, LinkedIn outreach = 2. Sources do not prove budget or authority. Recency scores at the declared snapshot: 0–30 days = 10, 31–90 = 7, 91–180 = 4, older = 2.

Weights are 30% size, 30% industry, 25% source, 15% recency. Automatic qualification requires complete evidence, weighted score >=7.5 and size/industry scores >=6. Rejection requires complete evidence and score <=4. Other cases go to review; no unsupported hard disqualifier is assumed. High priority starts at 8.5; other qualified leads start at medium. Decisions use unrounded scores.

An unknown factor has score bounds [1,10]. The report's estimated midpoint is labeled `score_is_estimate`; it cannot authorize outreach. Evidence coverage is weighted completeness, not confidence or probability. `fit_decision` survives missing contact details, while final `decision` becomes review and `outreach_ready` becomes false for qualified leads with unusable contact data. Duplicate records remain in the report but repeated occurrences are withheld from outreach.

## Architecture and safeguards

- `ingestion.py`: UTF-8 CSV, required/duplicate header checks, row-count errors flagged per record. Structurally unparseable CSV fails with a controlled error because record boundaries cannot be trusted.
- `scoring.py`: validated numeric policy, contiguous nonoverlapping bands, date/size normalization, score bounds, decisions, stable content fingerprints and ranks.
- `messaging.py`: seller-approved source-specific variants and deterministic fallback.
- `llm_client.py`: lazy LiteLLM import, batched evidence/variant selection, bounded exponential retries for transient failures, strict per-item validation, partial success and sanitized error categories. Fatal authentication/credit failures stop further requests but mark remaining leads and preserve reports.
- `reporting.py`: outreach/review queues, aggregate reasons, diversified samples and atomic file replacement. CSV carries run metadata and escapes formula-leading strings; the CLI also writes a metadata sidecar.
- `lead_qualifier.py`: orchestration, explicit snapshot, strict exit status, run manifest and runtime/usage metrics.

The LLM selects evidence factors and a permitted message variant. Code renders both using existing lead facts and approved claims. It cannot add free-form product promises, alter scores or produce outreach for unready leads. This deliberately trades unrestricted prose generation for auditability. Pattern detection of suspicious inputs is supplementary; the closed response contract provides the main protection. Messages are drafts; the tool never sends email or updates a CRM.

## Running

Use the README commands for sample data. For real contemporary data, choose the appropriate `--as-of YYYY-MM-DD`; omission uses local current date. `--no-llm` does not load `.env` or import LiteLLM. `--require-llm` still writes results but exits 2 when enrichment fails or credentials are absent. Batch sizes must be >=2; a final partial batch can contain one row.

Configure the model and base URL supplied by your provider. API keys stay in `.env` or environment variables. Optional `LLM_JSON_MODE=true` requests JSON-object mode only when your provider supports it; local validation always runs. Timeout is bounded to 1–300 seconds, retries to 0–5. No raw provider error bodies or credentials are written to reports. Runtime includes configuration/scoring/enrichment but excludes final serialization; token usage is recorded when returned. Cost remains null unless externally verified from provider billing.

Reports contain sensitive lead information. Only use data authorized for the configured provider. Report fingerprints help reconcile identical records across input reordering; they are not CRM IDs and change when content changes. Tied ranks use score, source score, company, fingerprint, then row; a tie-break is not evidence of superior conversion propensity.

## Reproduction and packaging

`python validate_project.py` runs all tests, regenerates fixture JSON/CSV reports and writes explicitly simulated provider evidence under `validation/`. It never calls a live API. `python build_submission.py` builds an allowlisted ZIP and excludes `.env`, `.venv`, caches, legacy reports and prior ZIPs. The original review is a historical baseline, superseded by REQUIREMENTS_ALIGNMENT.md. `archive/training_report.pre_v2.json` preserves the old misspelled report and is not a current deliverable.
