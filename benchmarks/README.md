# 3alimnIA research templates — no fabricated results

- `gold_queries_TEMPLATE.csv`: independent teacher adjudicators fill relevant source IDs for every retrieval case. `relevant_source_ids` separates IDs with semicolons. Never use model-retrieved IDs as the gold set.
- `human_grounding_TEMPLATE.csv`: expert labels for claim accuracy, source entailment, pedagogical alignment, and editing effort. Record variant labels before unblinding evaluators; use separate `evaluator_id` for independent raters.
- `run_retrieval_eval.py`: source-level Recall@K, Precision@K, nDCG@K, and reciprocal rank using the current lexical index. It refuses cloud mode unless an explicit, separately reviewed experiment protocol is established.

For a fair A/B/C/D study, fix the source corpus, model, prompt budget, locale, and temperature; vary one retrieval/governance component at a time. Log empty retrieval and provider failures. Blind expert reviewers. The scripts do **not** imply the method improves learning or factual correctness.
