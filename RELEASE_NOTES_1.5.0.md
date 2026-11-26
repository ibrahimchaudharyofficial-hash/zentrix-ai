# Zentrix AI 1.5.0

## Reliability fixes
- Replaced broad “increase/decrease” word-problem keyword matching with explicit templates and an algebraic relationship parser for unambiguous number-relationship forms; ambiguous phrasing is rejected.
- Unsupported word problems now fail closed rather than generating a guessed percentage answer.
- Fixed the matrix inverse working line that previously rendered as `False`; the determinant and actual inverse are now shown.
- Eigenvalue solutions now include the characteristic equation, explicit eigenvalues, and eigenvector bases.
- Statistics working preserves repeated observations and original order instead of converting the data to a set.
- Two-sided finite limits now display a two-sided limit operator rather than an incorrect right-hand direction.
- Added exact fair-coin binomial probability interpretation for “exactly k heads in n tosses,” with the binomial coefficient and substitution steps.
- Added formula/method labels for higher-degree polynomial solving, arithmetic evaluation, and unit conversion.

## New standout feature: Mathematical Proof Auditor
- New Proof Auditor workspace and `POST /api/audit` endpoint.
- Accepts 2–12 algebraic expressions/equations, one per line.
- Compares adjacent transformations symbolically, recognizes nonzero constant multiples, and compares polynomial equation solution sets when possible.
- Reports the first invalid or uncertain transition.
- Explicitly scoped to algebraic expressions/equations; not a universal proof assistant.

## 100-question benchmark
- Probability: 25/25 correct.
- Advanced algebra: 25/25 correct.
- Grade 8–10 mathematics: 30/30 correct.
- Difficult MCQ-style problems: 20/20 correct.
- Total: **100/100 correct** against the benchmark's expected results.
- 100/100 returned a passing solver check; 100/100 included solution steps and a formula/method label.
- Note: many solver checks are classified as rule-based, not independent formal proofs. MCQ-style testing evaluated the underlying mathematical question and matched the computed result to its expected option; it did not test free-form extraction of arbitrary MCQ layouts from text or images.

## Regression and smoke tests
- Full pytest suite: 35 passed.
- 100-question benchmark: 100/100.
- Python compilation and frontend JavaScript syntax checks pass.
- API smoke tests cover health, solve, plot, practice, and proof auditing.

## Known limitations
- The proof auditor currently handles algebraic expressions and equations; it does not verify geometry proofs, inequalities, or arbitrary natural-language proof arguments.
- Natural-language word-problem understanding is still template-based; unsupported statements are rejected. Optional Gemini can assist with command translation, but the local math engine remains responsible for calculation.
- Probability interpretation is not yet a full general-purpose combinatorics/probability word-problem parser. The new natural-language binomial pattern is specifically for fair coin tosses.
- A 100/100 result applies to this deliberately selected 100-question suite, not every possible mathematical problem.
- Physics remains SI-input based; OCR limitations from v1.4 remain.
