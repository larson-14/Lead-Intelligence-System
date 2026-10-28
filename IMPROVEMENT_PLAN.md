# Implementation plan

1. Define an explicit demonstration ICP, four-factor policy, uncertainty handling, seller context and reproducible snapshot.
2. Separate configuration/scoring, messaging, LLM adapter, reporting and CLI; validate inputs and preserve safe fallback results.
3. Add sorted queues, stable fingerprints, atomic reports and run provenance/metrics.
4. Add independent policy cases, malformed-input/provider tests and end-to-end checks.
5. Run a small live batch, then a strict 100-lead run if the provider works; record actual results without claiming predictive accuracy.
6. Publish a brief-alignment matrix, evaluation guide and clean submission package.

The example business is a lead-workflow SaaS for 11?500 employee technology and professional-service businesses. This is an explicit assignment assumption, not a fact supplied by the brief. Real ICP validation and conversion labels remain external business work.

## Final status

Steps 1?4 and 6 completed. Step 5 executed: live provider access fails for insufficient credit; safe full-scale fallback and simulated success are validated. See REQUIREMENTS_ALIGNMENT.md for remaining provider/business dependencies and VALIDATION_RESULTS.md for measured outcomes.
