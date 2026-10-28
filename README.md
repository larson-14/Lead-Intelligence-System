# Lead Intelligence System

Python CLI for transparent qualification, batched LLM-assisted outreach, and sales queues.

**Run (Python 3.10+):**
```powershell
python -m pip install -r requirements.txt
python lead_qualifier.py --no-llm --as-of 2024-01-20
python -m unittest -v
```
For live enrichment, copy `.env.example` to `.env`, configure your provider, and run:
```powershell
python lead_qualifier.py --require-llm --as-of 2024-01-20 --limit 5 --output smoke_report.json
python lead_qualifier.py --require-llm --as-of 2024-01-20
```

**Rubric:** This demonstration assumes a lead-workflow SaaS targeting 11–500 employee technology/professional-service companies; it is not a customer profile specified by the brief. Scores use company size (30%), industry (30%), source signal (25%), and interaction recency (15%); qualification requires >=7.5 and adequate size/industry fit, rejection <=4, otherwise review. Unknown evidence forces review with score bounds; missing contact details separately block outreach.

**Outputs:** `output_report.json` includes all leads, ranked outreach/review queues, reasons, samples, failures and run provenance. Use `--output output_report.csv` for CSV plus a metadata sidecar. Default input has 100 leads; use `--input leads_testing.csv` for messy cases.

**Limits:** Historical fixtures require the shown snapshot; omitted `--as-of` uses the local current date. Seller/ICP assumptions need business validation. Scores are not probabilities and these files contain no outcome labels. The LLM chooses approved personalized variants and evidence; wording is rendered locally to prevent invented claims. Messages are drafts, never automatically sent. `--require-llm` writes fallback results and returns nonzero if enrichment fails.

See [requirement alignment](REQUIREMENTS_ALIGNMENT.md), [test results](VALIDATION_RESULTS.md), [policy and operation](OPERATIONS.md), and [evaluation plan](EVALUATION.md).
