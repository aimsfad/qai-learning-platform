# V6.20.27 — AI-generated course pre-test engine

This release replaces the published-course self-report baseline as the primary assessment path with a validated, AI-generated objective pre-test that is created once per approved course version.

## Production contract

- Exactly six objective multiple-choice questions.
- Four distinct options per question and exactly one correct answer.
- Coverage includes prerequisites, a core concept, misconception diagnosis, application, and interpretation/transfer.
- At least four distinct course concepts.
- Questions are generated from the teacher project, approved blueprint, learning outcomes, prerequisites, and selected approved lesson evidence.
- Self-report questions, course titles, source titles, `$Untitled`, `Untitled`, `TBD`, and similar placeholders are rejected.
- Each accepted item stores concept, type, correct index, explanation, difficulty, and cognitive level.

## Fairness and versioning

The generated package is persisted in `published_course_pretest_packages` with a unique `(project_id, blueprint_run_id)` key. Every learner pinned to that course version therefore receives the same diagnostic questions. A content fingerprint detects later changes to approved instructional content and forces regeneration before the package is treated as current.

## Generation flow

1. Reuse a valid, current Phase-8 AI assessment package when it satisfies the V6.20.27 contract.
2. Otherwise route a dedicated diagnostic prompt through the existing provider chain.
3. Validate the response locally.
4. Perform at most one bounded AI repair attempt if the first output fails validation.
5. Persist only a quality-gated objective package.
6. Preserve the historical self-report baseline only as an emergency learner-access fallback when provider generation is unavailable.

## Teacher workflow

The final review/publish workspace now shows AI pre-test readiness, offers explicit generation/regeneration, and automatically prepares the package before publishing. Publication through the teacher UI does not proceed until the generated package passes the quality gate.

## Learner workflow

The learner runtime resolves the persisted course-version package before rendering the pre-test. Existing published courses can generate the package lazily on first access, so older publications are not stranded.

## Safety scope

No change is made to student authentication, course enrollment identity, lesson progress, the controlled Qiskit study tables, or the pre-test scoring formula. Objective questions continue to be scored from `correct_index` by the existing immutable learner-attempt storage path.
