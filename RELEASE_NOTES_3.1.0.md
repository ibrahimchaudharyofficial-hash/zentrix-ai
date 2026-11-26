# ZENTRIX AI 3.1.0 — Efficiency & Reliability Release

This release upgrades the existing v3.0.0 feature set in place, with particular attention to the target low-spec laptop environment.

## Improvements
- Solve requests use whitespace-normalized cache keys, a bounded 384-entry LRU and a dedicated two-worker math executor.
- Solver requests have a clear timeout and concurrent work is bounded to avoid runaway CPU pressure.
- Graph rendering uses 640 samples rather than 800, debounces resize redraws and ignores stale responses.
- SQLite progress storage uses WAL, busy timeouts, indexes and deterministic connection cleanup.
- API responses include security headers; API responses are not cached; oversized API requests are rejected; large responses are gzip-compressed.
- New `/api/diagnostics` endpoint reports cache capacity/use, solver concurrency and graph sample count.
- Knowledge Topics cards now display correctly.
- The shared numerical cross-check samples negative, fractional and positive inputs at higher working precision, with explicit tolerances. This remains a diagnostic rather than a formal proof.
- Launchers skip repeated dependency installation on subsequent launches.

## Compatibility
- Python 3.10+
- Windows 10/11 and Linux
- No paid API key required for mathematical calculations
- Gemini remains optional
- OCR still uses browser-loaded Tesseract assets and requires internet on first use

## Verification
See `TEST_REPORT_3.1.0.md`. Tests are automated in the build environment; actual speed and memory performance on the user's laptop have not been physically benchmarked.
