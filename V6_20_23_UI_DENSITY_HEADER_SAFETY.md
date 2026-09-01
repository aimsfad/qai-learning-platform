# 3alimnIA V6.20.23 — UI Density & Header Accent Safety

This visual-only maintenance release addresses the production screenshots recorded after the published Python course routing fix.

## What changed

- The decorative blue/cyan header accent now follows the **local header direction** (`dir="rtl"` or `dir="ltr"`) rather than relying on the global HTML direction.
- The title, subtitle, status, and metadata receive a reserved safe gutter so the decorative accent cannot cover text.
- Compact page headers use less vertical space while preserving readable typography.
- The learner tool dock keeps secondary destinations collapsed by default, reducing above-the-fold navigation height.
- Published-course onboarding steps are denser.
- Course-specific pre-tests now show a small `current/total` progress indicator and use tighter question/option spacing.
- Technical/code content inside the course pre-test is direction-isolated for mixed Arabic/Latin text.

## Functional guarantee

This release does **not** change authentication, enrollment, course-specific pre-test scoring, blueprint pinning, course identity, lesson progress, or AI-coach behavior.
