# Validation results

Executed 28 October 2026 in the project virtual environment (Python 3.14). Python 3.10 is the declared minimum but was not separately exercised here.

## Automated tests

**53 tests passed; zero failures and zero errors.** Test-run duration: 0.238 seconds. Evidence: `validation/unit_tests.txt` and `validation/summary.json`. Reproduce with `python validate_project.py`.

Coverage includes independent obvious-win/reject/borderline policy cases; exact size/recency boundaries; unrounded threshold behavior; missing/unmapped data; malformed employee counts/dates; stable ranks and duplicate suppression; three outreach variants; numeric-string/boolean/NaN/overlap/gap configuration rejection; malformed JSON and unhashable/duplicate/missing/extra provider IDs; forbidden score changes; partial success; timeout and rate-limit retry bounds; fatal-credit circuit breaking; strict nonzero failure exits with reports preserved; atomic write failure; JSON/CSV metadata; all three fixture CLIs; and independent-label evaluator metrics/coverage checks.

## Offline fixture results

Snapshot: **2024-01-20**. These are policy decisions, not ground-truth predictions.

| Input | Rows | Qualified | Rejected | Review | Distinct scores |
|---|---:|---:|---:|---:|---:|
| leads_training.csv | 29 | 7 | 0 | 22 | 22 |
| leads_testing.csv | 20 | 4 | 1 | 15 | 17 |
| leads_full_scale_100.csv | 100 | 29 | 1 | 70 | 41 |

All 149 input rows are preserved. Current `output_report.json`, `output_report.csv`, its manifest, `training_report.json` and `testing_report.json` were regenerated. Five output message samples cover demo, referral, educational and discovery variants; examples include CloudScale AI and Cybersecurity Startup. Messages contain supported name/company/industry context, the declared seller proposition and a call to action. Real brand suitability and persuasion are not empirically established.

Whole-process offline benchmark: **0.4072 seconds for 100 leads**, including Python startup and JSON output. This is a single local measurement, not a production SLA. It excludes API work and human handling; it cannot establish end-to-end sales savings against the brief's manual 8?12 minutes per lead.

## Provider success/failure evidence

- **Simulated success:** 100 leads, 10 batches, 100 successful validated items, strict exit 0. Scores and decisions exactly match offline results. Artifact: `validation/simulated_full_scale_report.json`. This explicitly uses a mock provider and demonstrates the integration contract, not live model quality.
- **Actual 5-lead smoke:** request reached the configured Anthropic endpoint and failed because the account's credit balance was too low. All five fallback results were written; strict exit 2. Artifact: `smoke_report.json` (the earlier smoke records generic BadRequestError; the subsequent diagnostic identified insufficient credit).
- **Actual full-scale failure path:** 100 fallback results retained; strict exit 2; one actual provider attempt, then nine batches skipped by the fatal-credit circuit breaker. All 10 batches are counted as unsuccessful. Artifact: `live_full_scale_report.json`; sanitized error: `provider_error:InsufficientProviderCredit`.
- **Not proven:** successful live enrichment, live prompt quality, provider cost or success latency. The configured account needs credit or a different authorized working provider. Existing `.env` was not modified and no account/billing changes were made.

## Compared with the reviewed baseline

The old full-scale policy yielded 35 qualified / 0 rejected / 65 review, with all qualified leads tied at 7.0. The new policy yields 29 / 1 / 70 and 41 distinct scores. Rejection/high-priority paths are now reachable, factors vary meaningfully, and both reproduced crashes have regression coverage. **The review rate increased to 70%; this is not a demonstrated improvement in sales accuracy or manual workload.** Business-approved policy changes and independent labels are required before those claims can be made.

## Remaining acceptance conditions

See `REQUIREMENTS_ALIGNMENT.md` for every brief requirement and `EVALUATION.md` for the improvement plan. Open dependencies are successful funded-provider validation, real seller/ICP approval, and independent outcome collection. Everything that can be established locally is accompanied by reproducible code and evidence; no conversion labels or accuracy scores were invented.
