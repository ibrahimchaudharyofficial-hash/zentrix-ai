# ZENTRIX AI 3.2.0 — Accuracy & Trust Release

This release prioritizes honest verification, domain awareness and numerical checking.

## Accuracy improvements
- Verification status is now strict: a result is fully verified only when every reported check passes. Inconclusive checks produce a distinct `partially-verified` status rather than a full-verification claim.
- Numerical expression comparisons use a symmetric, higher-precision relative tolerance.
- Root substitution checks try exact symbolic zero detection first, then use high-precision numerical evaluation with a scaled tolerance.
- Identity verification reports denominator restrictions on each side, making excluded values visible after algebraic cancellation.
- Answer comparison reports the common-domain interpretation and any denominator restrictions.
- The identity-verification interface displays domain restrictions instead of hiding them in the response.

## Compatibility
- Preserves the existing FastAPI, SymPy, NumPy, SciPy and mpmath stack.
- No paid API key required for mathematical calculations.
- Existing 3.1.0 features and local progress data format remain unchanged.

## Verification
- Automated test suite: 60 passed.
- Python compilation: passed.
- Inline JavaScript syntax check: passed.
- Manual API checks for domain-aware identity and answer verification: passed.
- ZIP integrity: verified after packaging.

## Boundaries
Numerical sampling remains diagnostic, not a proof. The identity check's symbolic simplification is the primary equality test. OCR recognition accuracy and broad natural-language interpretation are not certified by this release.
