# Zentrix AI — Initial Security Audit

Date: 2026-11-22

## v1.4.0 follow-up

- Added a numeric exponent magnitude guard to the restricted AST parser.
- Added `/api/verify` with bounded expression lengths and the same restricted parser; it compares expressions symbolically and returns generic errors for unsupported input.
- Added a local deterministic practice generator with finite topic/difficulty enums. It does not execute generated code or accept arbitrary prompt templates.
- Photo OCR remains browser-side. Image preprocessing occurs in the browser and no image upload endpoint is exposed.
- Result metadata now identifies symbolic, numerical, rule-based, failed, and unverified states. These labels are not formal proof certificates.


## Findings addressed in this pass

### 1. User-controlled expression parsing

**Original risk:** `sympy.parsing.sympy_parser.parse_expr` was used on user-supplied text. That parser relies on Python evaluation internally and must not be treated as a safe parser for untrusted input.

**Change:** Replaced it with a restricted Python AST evaluator. It accepts a small allowlist of numeric literals, names, arithmetic operators, selected mathematical function calls, and list/tuple literals for matrices. Attribute access, imports, lambdas, arbitrary calls, keyword arguments, and Python statements are rejected.

### 2. Unbounded input sizes

**Original risk:** The API limited question length but expression parsing and graph inputs had fewer explicit bounds.

**Change:** Added expression length and AST-node limits, Pydantic request-length limits, finite plotting-bound checks, and a maximum graph interval width.

### 3. Optional Gemini natural-language integration

**Original risk:** Natural-language questions that were not covered by the local command parser could not be translated into supported solver commands.

**Change:** Added an optional Google Gemini adapter. The API key is read server-side from the project-root `.env` file and sent in the `x-goog-api-key` request header; it is never embedded in frontend assets. Gemini is instructed to return a single restricted Zentrix command, which is then processed by the existing safe parser. SymPy remains responsible for all calculations. The integration is disabled when `GEMINI_API_KEY` is absent.

**Privacy note:** Google documents that content submitted under its free tier may be used to improve its products. Do not submit sensitive personal or confidential information through the optional cloud interpreter. Free-tier availability and quotas can change.

### 4. Error detail exposure

**Change:** API-level unexpected processing errors now return generic client-facing messages rather than raw exception details.

## Verification performed

- Core solver regression suite: 40/40 cases pass.
- Punjab Class 10 suite: 22/22 cases pass.
- Cross-grade suite: 38/38 cases pass.
- Expanded school mathematics suite: 28/28 cases pass.
- Added parser regression cases for implicit multiplication, scientific notation, and square roots.
- Added rejection checks for import execution, file opening, attribute access, and lambda calls.
- Python bytecode compilation passes for the backend modules.
- FastAPI health and matrix-solve smoke tests pass.
- Gemini request/response flow passes a mocked integration test; a live call requires the user to configure their own key.

## Remaining risks and limitations

- `asyncio.wait_for` around a worker thread limits request wait time but does not forcibly terminate a computation already running in that thread. Production deployment should isolate expensive symbolic jobs in killable worker processes or containers with CPU/memory limits.
- This is not a complete sandbox against all denial-of-service inputs. More adversarial fuzzing and resource isolation are still required.
- Numerical spot checks are not formal mathematical proofs. Existing verification labels need a broader redesign before research-grade claims are appropriate.
- General mathematical handwriting OCR, reliable diagram understanding, PDF parsing, account management, and cloud features are not implemented. Existing browser OCR is general English text recognition and may misread mathematical notation.
- The frontend currently loads KaTeX from a CDN, so offline mathematical typesetting is not yet fully self-contained.

## Next recommended work

1. Add process-isolated calculation workers and explicit resource budgets.
2. Redesign verification metadata to distinguish symbolic identities, numerical checks, formal proofs, and unverified results.
3. Add provider selection and a local Ollama adapter.
4. Bundle frontend assets locally for offline operation.
5. Expand property-based, fuzz, and domain-specific mathematical tests.
