## 3.4.0 — Photo OCR reliability and optional vision transcription
- Added retryable Tesseract.js loading through jsDelivr and unpkg; failed library/worker initialisation no longer leaves a permanently rejected promise.
- Added explicit worker, WebAssembly core and English trained-data paths, with a second worker/CDN configuration.
- Bounded browser OCR preprocessing to a maximum 2,400-pixel long edge and about 4 megapixels to avoid excessive memory use on laptop browsers.
- OCR now compares original, enhanced grayscale, black-and-white and sparse-layout readings with clearer confidence feedback.
- Added optional Gemini image transcription for math notation when Gemini is connected. The user must explicitly confirm before a compressed image is sent to Google; ZENTRIX does not persist the image.
- Added API size, MIME/signature, local-request, key-presence and error handling checks plus OCR regression tests.

# Changelog

## 3.1.0 — Efficiency and reliability upgrade
- Bounded SymPy solver concurrency with a dedicated two-worker executor and request timeout.
- Increased bounded LRU solve cache to 384 normalized queries and exposed local diagnostics.
- Added API request-size guard, response security headers, API no-store policy and gzip compression for larger responses.
- Switched local progress storage to deterministic connection cleanup, SQLite WAL, busy timeout and an additional time index.
- Reduced graph samples to 640 for lower laptop load and prevented stale graph responses from overwriting newer plots.
- Debounced graph redraws during window resizing.
- Fixed Knowledge Topics cards so they are actually rendered.
- Optimized launchers to avoid reinstalling/checking all dependencies on every normal startup.
- Strengthened the shared numerical equivalence checker with negative/fractional sample points, higher precision and explicit tolerance handling.
- Added regression tests for API protections, diagnostics, graph bounds, research-variable validation and numeric cross-checks.

## 3.0.0 — Mathematical Research Platform
- Added Research Lab: derivatives, second derivatives, antiderivatives, point evaluation, limits, roots, Taylor polynomials, definite integrals and sampled numerical values.
- Added exact symbolic identity verification with numerical spot checks and explicit proof limitations.
- Improved photo OCR with three enhanced image variants and segmentation passes.
- Added printable research report export.
- Added local Math Arcade learning profile and confidence-aware subject estimates.
- Added structured knowledge topic map.
- Preserved the existing laptop-optimized interface and core feature set.

## 1.7.0
- Math Arcade, laptop layout refinements and existing mathematical workspace features.
