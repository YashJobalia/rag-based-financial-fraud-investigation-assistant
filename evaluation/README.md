# Evaluation protocol

`dev.json` is an eight-question development smoke benchmark. `heldout.json` contains 36 frozen document-retrieval questions, including ambiguous/unanswerable and permission-isolation requests. Neither file is indexed or sent to synthesis. Production uploads exclude this entire directory.

Run `uv run python evaluate.py --split dev` from `backend/` with a seeded PostgreSQL connection. Use `--split heldout` only at a deliberate evaluation checkpoint. Do not tune on held-out results. Hashes in each result pin the question set and permitted corpus; later vector/hybrid comparisons must use identical hashes, k, permissions, and cutoffs.

Retrieval metrics: macro recall@k, reciprocal rank, binary-relevance nDCG@k, and latency (excluding connection setup and HTTP). Empty retrieval on unanswerable queries is a diagnostic only: relevant procedural guidance can be returned for an unanswerable case fact, so synthesis must still abstain.

Reference-brief tests check citation existence, permitted scope, and required claim categories. They do not measure LLM quality. Live synthesis evaluation will separately annotate every atomic claim for citation semantic correctness, completeness, supported/unsupported content, and appropriate abstention. Record prompt/model versions, input/output tokens, and configured model prices. Unknown prices remain null, not zero.

Manual rubric: a factual claim passes only when the cited record/passage entails the claim for the correct case, time window, currency, and document version. A historical outcome cannot establish a current-case outcome. Hypotheses must remain conditional and acknowledge contrary evidence. Unanswerable requests must not invent an answer; recommending a relevant next check is allowed.

Limitations: this first corpus is small and synthetic. The held-out set tests new questions against existing documents, not generalization to unseen case families. A later scenario-separated benchmark is required before making broader quality claims. Detection rules and metrics are independent of all retrieval/synthesis metrics.
