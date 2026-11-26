# ZENTRIX AI v3.8.0 — Test Report

- Python compileall: passed.
- Inline JavaScript syntax check (Node.js): passed.
- Automated test suite: 76 passed.
- School-level UI regression tests: confirm calculus/research and matrix pages are absent, university-level subjects are removed from visible selectors, and the solver shows an out-of-scope notice for advanced topics.
- Release archive integrity: verified after packaging.

The symbolic engine's internal implementation is retained for stability and regression coverage; the v3.8.0 user interface is focused on school mathematics and blocks common university-level prompts in the main solver UI.
