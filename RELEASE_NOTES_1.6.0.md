# Zentrix AI v1.6.0

## Misconception Detection Coach
- Added a dedicated Error Coach workspace and `/api/diagnose` endpoint.
- Audits adjacent algebra steps and locates the first invalid or uncertain transition.
- Recognizes selected school-algebra error patterns: incomplete distribution, sign changes when transposing terms, lost negative square roots, incorrect inverse operations with fractions, and selected zero-product/negative-distribution cases.
- Gives a short explanation and a targeted follow-up practice question.
- Uses the local SymPy engine; no Gemini/API key is required.
- Uses cautious confidence labels and a generic fallback for unclassified errors. A passed audit does not prove the original problem is fully solved.

## Reliability and scope
- Existing proof auditor remains available.
- API limits each submission to 2–12 lines and 300 characters per line.
- The coach is an educational aid for supported algebra transformations, not a universal misconception classifier or a replacement for teacher review.

## Validation
- Includes regression tests for correct work, incomplete distribution, missing negative root, fraction inverse-operation error, unknown errors, and request validation.
- Full test results are documented in `TEST_REPORT_1.6.0.md`.
