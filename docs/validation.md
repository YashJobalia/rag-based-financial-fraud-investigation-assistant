# Local milestone validation — 2026-09-18

## Observed results

- PostgreSQL 18.4 local runtime; migrations and deterministic seed completed.
- 21 PostgreSQL-backed tests passed for totals, chronology, explicit alert inputs, case/citation isolation, tenant RLS, evidence cutoffs, ingestion version immutability, request budgets, analyst-only reviews, and reference-brief structure.
- Two additional focused OpenAI adapter tests cover the scoped model input/structured response contract and sanitized provider failures. These use a mocked provider and do not establish live-model quality.
- Three Playwright tests passed: public investigation/citation/retrieval workflow, signed analyst review persistence, and a 390px mobile layout without horizontal overflow.
- Vite production build and TypeScript checking passed. Ruff checks passed.
- Manual agent-browser inspection confirmed the case and reference brief render and expose clickable citations. No browser errors were reported in that inspection.
- Dependency installation reported no npm audit vulnerabilities for the installed root/frontend packages at the time of installation. This is not a comprehensive security audit.

## Keyword development benchmark

The eight-question development smoke set scored Recall@5 = 1.00, MRR = 1.00, and nDCG@5 = 0.9866. Six questions have supporting passages; two have none. The run returned no passages for both unanswerable development queries. Latest measured retrieval mean: 21.50 ms; p95: 32.20 ms, excluding database connection setup, HTTP, browser rendering, and synthesis. See the committed JSON report for exact corpus/dataset hashes and per-question results.

These results are from a tiny synthetic corpus and intentionally simple development questions. They are not fraud-detection accuracy, live-model groundedness, or evidence of real-world generalization. The 36-question held-out document-retrieval set remains unrun. Vector/hybrid search and unseen-case-family evaluation are not yet implemented.

## Unverified or limited

- One real OpenAI smoke call has now completed (see below). Systematic live citation entailment, completeness, groundedness, and abstention evaluation remain outstanding. Dollar cost is not configured.
- Reference briefs are deterministic and labeled. They must not be used to claim LLM quality.
- The prompt-injection test checks that the deterministic path does not execute actions. It is not a red-team result for a live model.
- PostgreSQL enforces tenant isolation; API case assignments and document-group predicates provide the finer scope. Production identity-provider integration and revocation remain future work.
- Documents are one short passage each; richer section-aware chunking and additional case scenarios are later phases.
- The test run emitted two upstream Starlette/AnyIO deprecation warnings. They did not fail the tests.
- Vercel build/runtime behavior and the requested custom domain are not yet verified. The separate hosted database is pending.
- Windows PostgreSQL initially lacked runtime DLLs. A system installer was rejected by automatic approval review; the working setup reuses an existing Microsoft runtime without installing a service.


## Live API smoke test ? 2026-09-19

One authenticated FastAPI TestClient request used the real PostgreSQL evidence/retrieval path and OpenAI `gpt-4.1-mini`. Live generation was enabled only in that test process; the saved environment flag remains false. This was not a browser or hosted-deployment test.

- Response: HTTP 200; all six required sections and the cautious conclusion were returned and persisted.
- Measured request duration: 19,761.97 ms. Usage: 4,655 input tokens and 1,010 output tokens. Cost remains unknown because model rates are not configured.
- All 17 distinct cited evidence IDs resolved through the authenticated API.
- Public live generation returned 403; the analyst's unassigned case returned 404.
- The brief included phone replacement as a legitimate hypothesis, missing authorization evidence, and further investigation rather than a fraud verdict.
- Full response and cited evidence are stored only in ignored `.local/live-smoke.json`. No key or session token is included in that report.

Manual inspection found limitations: the brief omitted timezone labels when rendering offset timestamps; it paraphrased the per-transfer alert threshold as an aggregate threshold and omitted the first 30-minute rule window. The database session uses local time, which also affects SQL day-boundary calculations; a follow-up must pin an explicit timezone and verify boundary cases before treating daily windows as portable. The sample transfer amounts and cited baseline totals matched their supplied calculations, but that does not validate window semantics. These are unresolved findings, not a perfect groundedness score. Valid IDs do not establish semantic correctness. No held-out evaluation or prompt-injection evaluation was performed in this smoke test.
