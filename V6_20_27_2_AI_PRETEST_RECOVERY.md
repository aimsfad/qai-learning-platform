# V6.20.27.2 — AI pre-test recovery and diagnostics

This hotfix keeps the course-version-pinned AI pre-test architecture from V6.20.27 and improves production reliability.

- Adds a third compact schema-first recovery generation after the initial generation and repair pass.
- Accepts common provider field aliases (`choices`, `answers`, `answer_index`, `feedback`) without weakening answer-key validation.
- Maps common question-type aliases to the canonical diagnostic taxonomy.
- Preserves the strict six-question quality gate, concept diversity, prerequisite, misconception, and application/transfer coverage.
- Displays the provider/model, attempt count, and sanitized generation diagnostics in Teacher Studio when the package is rejected.
- Does not change learner enrollment, course routing, scoring, progress, or the pre-test UI grid.
