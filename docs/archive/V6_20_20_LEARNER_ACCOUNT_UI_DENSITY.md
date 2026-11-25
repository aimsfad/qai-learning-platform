# 3alimnIA V6.20.20 - Learner Account Compatibility + UI Density

Baseline: V6.20.19 course-enrollment baseline gate.

## Changes

- Keeps learner identity global: one student account can enroll in multiple teacher-published courses.
- Keeps enrollment course-local through the existing unique `(student_id, project_id)` contract.
- Keeps each published-course diagnostic baseline isolated by learner, project, and pinned blueprint version.
- Normalizes learner identifiers at sign-in (Unicode NFKC, trimming, zero-width character removal) without weakening password verification.
- Adds a safe account diagnostic helper that never exposes password hashes.
- Restores the R2 password-reset policy through `password_policy_error`, matching new-password hashing rules.
- Adds a compact UI density layer for shared page headers, section headers, cards, forms, buttons, and published-course flows.
- Adds a behavioral validator proving that one existing learner can authenticate once and enroll in two separate courses while pretests remain course-local.

## Apply

From the project root on Windows:

```cmd
py -3 apply_v62020_patch.py .
py -3 validate_v62020_learner_account_compat.py
py -3 validate_current_release.py
```

Then run:

```cmd
streamlit run app.py
```

## If an old account is still rejected

Run against the same deployed database configuration:

```cmd
py -3 diagnose_learner_account.py "QAI-XXXXXX"
```

If `account_found` is false, the account is not present in the database currently selected by `DATABASE_URL`; code changes must not fabricate or silently migrate credentials. Restore/use the persistent database that contains the existing learner records.
