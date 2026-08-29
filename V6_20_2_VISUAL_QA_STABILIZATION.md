# V6.20.2 - Screenshot-driven Visual QA Stabilization

This release is based on the first real laptop screenshots of the deployed V6.20.1 interface.

## What changed

- Reduced the blank top band and tightened the application shell on 1366px laptops.
- Increased public-navigation label readability and normalized header spacing.
- Reduced the Arabic landing-hero title dominance while preserving hierarchy.
- Made program cards shorter, denser, and easier to scan on laptop displays.
- Tightened the teacher workspace header and project-production header.
- Widened the single-project card so it no longer floats as a narrow island in a large empty canvas.
- Replaced typographic learner-tool glyphs with native Streamlit Material icons.
- Made the AI Tutor header compact so the actual learning conversation appears earlier in the viewport.
- Removed a redundant leading generated Markdown heading when the teacher UI already renders the same lesson-section title.
- Improved lesson section-map density and long-content reading measure.
- Added laptop-, tablet-, phone-, and very-small-phone overrides in a final isolated CSS layer.

## Validation

- Python compileall: PASS
- Current supported regression suite: 21/21 PASS
- V6.20.2 visual QA contract: PASS

## Important test note

The screenshots used for this pass were all approximately 1362-1365 pixels wide. They validate the laptop/desktop view, not an actual phone viewport. A real 390x844 or similar mobile capture is still required for final mobile QA.
