## v4.0.1 — Learn, Solve, Master

Adds a polished student workspace and an Exam Centre with selectable subjects, test lengths, levels, instant feedback, and local score tracking. Matrix Lab and the Definitions library are retained.

# ZENTRIX AI v4.0.1

## School mathematics edition + definitions library

This release focuses the visible workspace on school-level mathematics: arithmetic, algebra, geometry, trigonometry, statistics, probability, coordinate graphs and school physics. University-level calculus/research tools remain outside the school-focused learning interface. Matrix Lab is retained. A searchable Definitions page explains school mathematics and basic physics vocabulary in simple language, with an example for each term. The solver interface explains when a question is outside this edition’s scope.

Core local calculation, photo OCR, optional connected AI providers, learning tools, games, graphing and local progress remain available.


**Mathematics Without Limits.** Created by Ayaan Chaudhry; developed with assistance from ChatGPT.

## What’s new in v3.9.0

- Added a searchable Definitions page with simple explanations and worked everyday examples across number skills, algebra, geometry, measurement, coordinate geometry, trigonometry, statistics, probability, sets and introductory physics.
- Filter definitions by subject and search by term, explanation or example.
- Matrix Lab remains available.

## Previous v3.7.0 update

- Photo question reader keeps free, on-device Tesseract OCR.
- Connect your own **Google Gemini, OpenAI, Anthropic Claude or OpenRouter** API key in Settings.
- Choose a connected provider for optional AI math-image transcription. ZENTRIX asks for confirmation before sending the image to that provider.
- Provider keys are saved locally in the project's `.env` file. API usage may cost money depending on provider/model.
- OCR output is editable; check all mathematical symbols before solving.

## Run on Windows

1. Extract the ZIP.
2. Double-click `start_zentrix.bat`.
3. Open the local address shown in the terminal (normally `http://127.0.0.1:8000`).

Core calculations remain local and do not require an AI provider.

---

# ZENTRIX AI 3.4.0

A local-first mathematics workspace built with FastAPI, SymPy and a lightweight HTML/CSS/JavaScript interface. The 3.4.0 update strengthens photo-question recognition with recoverable browser OCR and optional, user-approved Gemini image transcription for mathematical notation.

## Run on Windows

1. Extract the ZIP.
2. Double-click `start_zentrix.bat`.
3. Open the local address shown in the terminal (normally `http://127.0.0.1:8000`).

The first launch installs the Python requirements if needed. Core mathematical solving works locally; Gemini is optional.

## Usage tracking

The dashboard counts time only while the app tab is visible and there has been recent interaction. It pauses after 75 seconds of inactivity and when the tab is hidden. Statistics are stored in this browser's local storage and are not uploaded.

## Photo-question recognition

The free OCR button uses Tesseract.js in the browser. It retries the script/worker through two CDN hosts, clears failed worker initialisation so a later attempt can recover, bounds image processing to about 4 megapixels, and compares original, contrast-enhanced, black-and-white and sparse-layout readings. The image is not uploaded to the ZENTRIX server for this local OCR mode.

When Gemini is connected in Settings, an additional **AI math reading** button is available. It is optional: clicking it asks for confirmation before ZENTRIX sends a compressed copy of the selected image to Google's Gemini API for transcription. The image is processed in memory and is not stored by ZENTRIX. The transcribed text is not a verified mathematical result; review every symbol before solving. Provider usage limits and terms apply.

Tesseract is general printed-text OCR, not a dedicated mathematical typesetter. It can still confuse variables, digits, exponents, stacked fractions, roots or diagram labels. Gemini vision can also make transcription mistakes. Always review the editable transcription before sending it to the math engine.

---

# Zentrix AI v3.1.0

## What's new in v3.1.0

- **Faster repeated solving:** normalized question cache with a bounded 384-result LRU.
- **Laptop-safe solver queue:** math workloads run through a dedicated two-worker pool with request timeouts.
- **Lighter graph rendering:** reduced graph sampling from 800 to 640 points and discarded stale responses during rapid redraws.
- **Lower startup overhead:** Windows and Linux launchers install dependencies only when creating the virtual environment; access logging is disabled for the local app.
- **More reliable local progress:** SQLite connections close deterministically, WAL mode and busy timeout improve concurrent reads/writes, and indexes speed up progress summaries.
- **Safer API defaults:** bounded request size, security headers, no-store API responses and runtime diagnostics.
- **Stronger numerical cross-checks:** verifier samples include negative, fractional and positive values at higher working precision; these checks remain diagnostics, not formal proofs.
- **Fixed Knowledge Topics navigation:** topic cards now render correctly and remain keyboard accessible.

## What's new in v3.0.0

- **Math Arcade:** six mini-game modes, selectable subjects, six difficulty settings plus adaptive difficulty, 5/10/15/20-question rounds, instant feedback and explanations.
- **Local progress:** Arcade attempts and accuracy are stored in a local SQLite database on this computer. No account or cloud sync.
- **Animated interface:** lightweight page, card, hover and animated-gradient effects are part of the default experience.
- **Offline Tutor:** built-in explanations for core topics, with optional Gemini-generated guidance when connected.
- **Optional About ZENTRIX:** enable the concise product introduction from Settings.
- **Low-device approach:** no game engine or new heavy frontend framework; the Arcade uses native HTML/CSS/JavaScript.


## What's new in v1.6.0
- **Misconception Detection Coach:** new Error Coach workspace and `/api/diagnose` endpoint. It identifies selected common algebra errors, explains the likely misunderstanding, and suggests targeted practice. It is deliberately cautious and is not a universal error classifier.
- **Mathematical Proof Auditor:** workspace and `/api/audit` endpoint. Enter 2–12 algebraic lines; Zentrix compares adjacent transformations, checks polynomial equation solution sets where possible, and identifies the first invalid or uncertain transition. Scope is algebraic expressions/equations, not a universal theorem prover.
- **Safer word-problem handling:** strict templates replace broad keyword guessing. Unambiguous relationships such as ‘a number increased by 7 is three times the difference between the number and 5’ are translated into explicit equations. Ambiguous wording is rejected rather than assigned a guessed percentage model.
- **Linear algebra working:** matrix inverse steps show the actual inverse and determinant; eigenvalue steps show the characteristic polynomial, eigenvalues, and eigenvector bases.
- **Statistics and limits:** repeated observations remain visible in the working; two-sided limits display a two-sided limit operator.
- **Binomial probability:** exact fair-coin ‘exactly k heads in n tosses’ questions use the binomial formula and show combinations, substitution, and simplification.
- **Solution guidance:** polynomial equations above degree two now identify factorisation / the factor theorem, and arithmetic and unit-conversion operations include a method/formula label.

## What's new in v1.4.0
- **Physics numericals:** force, work, power, Ohm's law, kinetic energy, gravitational potential energy, momentum, density, pressure, speed, and acceleration. Use explicit `physics <model> key=value` commands; quantities are interpreted in SI units.
- **Learning Studio:** generate practice questions across algebra, calculus, arithmetic, physics, and geometry at easy, medium, or hard levels. Reveal the worked solution or submit an answer for exact symbolic comparison. Includes a searchable 21-formula reference covering algebra, calculus, geometry, physics, electricity, statistics, and probability.
- **Answer checker:** `/api/verify` compares expressions symbolically, so equivalent forms such as `1/2` and `0.5` are accepted.
- **Verification labels:** each result distinguishes symbolic, numerical, formula/rule-based, failed, and unavailable checks instead of implying every result has a proof.
- **Photo OCR preprocessing:** the browser automatically enlarges and increases contrast/grayscale before Tesseract recognition, and displays the OCR confidence estimate. Always review extracted text.
- **Security hardening:** numeric exponent magnitude is now enforced in the AST expression parser.

### Physics command examples
```text
physics force mass=5 acceleration=2
physics work force=10 distance=3
physics power work=100 time=5
physics ohms voltage=12 resistance=4
physics kinetic energy mass=2 velocity=3
physics potential energy mass=2 height=5
physics momentum mass=2 velocity=3
physics density mass=10 volume=2
physics pressure force=100 area=5
physics speed distance=100 time=2
physics acceleration initial_velocity=0 final_velocity=20 time=5
```
All numeric inputs must be in SI units (kg, m, s, N, V, Ω, etc.) for the displayed result unit to be meaningful. The engine does not infer or convert units in physics commands.

## Solve a question from a photo (v1.3.0)
On the Home page, use **Solve from a photo** to choose an image or drag one into the upload area. Select **Read question** to run free browser-based OCR, review/correct the extracted text, then choose **Solve recognised question**. The image is processed in the browser and is not uploaded to the Zentrix backend. The OCR library and English language data are loaded from a CDN on first use, so an internet connection is needed for photo recognition. Core calculations remain local and do not require a Gemini API key.

OCR can misread handwriting, exponents, fractions, and symbols; review the recognised text before solving.

**Release history: current release is v3.4.0.**

**Mathematics Without Limits.** Created by **M.Ayaan Chaudhry**. A local-first mathematical computing workspace built with Python, SymPy, NumPy, SciPy, mpmath, FastAPI, and an optional Google Gemini language interpreter.

## What works now — version 3.4.0

- Math Arcade, local SQLite progress, adaptive difficulty and six mini-game modes.
- Offline topic tutor with optional Gemini assistance; tutor text is not a verified calculation.
- Opt-in About ZENTRIX panel and animated interface.

- Symbolic arithmetic and simplification
- Algebraic equation, linear-system, and real inequality solving
- Factorization and expansion
- Differentiation, partial derivatives, Taylor series, and integration (including selected definite integrals)
- Limits and selected ordinary differential equations
- Finite summations
- Matrix addition, subtraction, multiplication, determinant, inverse, transpose, eigenvalues, and rank; named matrix assignments such as `A = [[1,2],[-1,0]]`, `B = [[3,2],[1,-1]]`, followed by `find A-B` work locally without Gemini
- Optional Gemini natural-language interpretation; all actual calculations remain in the local SymPy engine
- Number-theory utilities: GCD, LCM, primality, and prime factorization
- Step-by-step solution output with applicable verification checks
- 2D function plotting with adjustable expression and interval
- Browser-local recent calculation history
- Redesigned responsive workspace with guided topic starters, dedicated Matrix Lab, graph studio, searchable history, command palette (Ctrl+K), accessible keyboard focus, light/dark themes, and author-branded welcome screen
- Expanded school geometry, coordinate geometry, mensuration, grouped statistics, counting, unit conversions, and guided word-problem templates
- Local mathematical computation; no AI API key required

## Quick start — Windows

1. Install Python 3.10 or newer.
2. Extract this folder.
3. Double-click `start_zentrix.bat`.
4. Open <http://127.0.0.1:8000> in your browser.

### Optional Gemini setup (no manual file editing)

1. Open Zentrix and choose **AI settings** in the left sidebar.
2. Create a key at <https://aistudio.google.com/apikey>.
3. Paste it into the Gemini API key field and select **Save & connect**.
4. Zentrix verifies the connection and stores the key in the project-root `.env` file on this computer. The key is never returned to the frontend.

You can remove the saved key from the same settings panel. Keep this project on your own computer; do not expose its local development server to the public internet.

Gemini is called only when the local command parser cannot understand a question. Its response is treated as an untrusted command and passed through Zentrix's restricted parser; SymPy still performs the calculation.

The first launch installs the Python dependencies. Internet is needed for that initial installation. After installation, the mathematical API and graphing run locally. If you prefer manual setup:

```powershell
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>.

## Quick start — macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## Tests

Run from the project root:

```bash
python tests/test_engine.py
```

The core regression suite contains 40 mathematical cases, including named matrix workflows, transpose, inequalities, partial derivatives, Taylor series, and finite summations. API smoke tests should also be run after dependency installation:

```bash
python -c "import sys; sys.path.insert(0, 'backend'); from fastapi.testclient import TestClient; import main; c=TestClient(main.app); print(c.get('/api/health').json()); print(c.post('/api/solve', json={'question':'x^2-5x+6=0'}).json()['answer_text'])"
```

## Cost and privacy

- The symbolic math engine does not need an AI API or subscription.
- Gemini is optional. Without `GEMINI_API_KEY`, direct supported commands continue to work offline.
- Gemini API offers a free tier for eligible models, subject to Google account, model, region, and rate limits; Google may change availability and terms. See the [official pricing page](https://ai.google.dev/gemini-api/docs/pricing).
- Calculation history is stored in this browser's local storage.
- The UI loads optional fonts and KaTeX from CDNs when internet is available. If those CDNs are unavailable, the core solver remains usable, though typography and rendered mathematical notation may fall back.

## Security notes

- Mathematical expressions are parsed using a restricted Python AST whitelist; arbitrary Python execution, imports, attribute access, and unapproved calls are rejected.
- Expression length and AST complexity are bounded.
- API request sizes and plotting intervals are limited.
- The API binds to `127.0.0.1` in the supplied launch instructions; do not expose the development server directly to the public internet.
- A request timeout limits how long the API waits, but thread cancellation is not process isolation. For hostile multi-user deployment, run computations in isolated worker processes/containers with OS-level CPU and memory limits.

## Current limitations / roadmap

ZENTRIX is a local-first mathematical learning application, not a complete research-grade computer algebra system. Physics models require explicit SI values and do not perform dimensional analysis. Arcade questions are template-generated; adaptive difficulty currently uses recent aggregate Arcade accuracy rather than a full mastery model or spaced-repetition scheduler. The offline tutor provides concise topic explanations, while optional Gemini guidance may be wrong and is not independently verified. The Proof Auditor is limited to algebraic expressions and equations, not a universal theorem prover. Photo OCR uses general English Tesseract recognition and may misread handwriting, diagrams, fractions or exponents. There is no 3D plotting, PDF worksheet import, cloud sync or cross-device progress transfer. Numerical checks are not formal proofs, and derivation steps are not complete for every solver path.

## Class 10 Punjab Board Mathematics mode (v0.6)

The solver now includes tested command patterns aligned to the 12-unit Punjab Class 10 Mathematics textbook (2026-27):

1. Complex Numbers — `modulus 3+4i`, `conjugate 3+4i`, `real part 3+4i`, `argument 3+4i`
2. Quadratic Equations and Inequalities — `solve x^2-5x+6=0`, `solve x^2<9`
3. Matrices and Determinants — `det of [[1,2],[3,4]]`, `inverse of [[2,0],[0,4]]`
4. Functions and Graphs — `function f(x)=x^2+2x at 3`; use Graph Studio for supported y=f(x) plots
5. Algebraic Fractions — equation solving, factorisation, simplification, and denominator/domain warnings
6. Vectors in Plane — `vector add [1,2] and [3,4]`, `dot product [1,2] and [3,4]`, `magnitude [3,4]`, `angle between [1,0] and [0,1]`
7. Trigonometry — `trig simplify sin(x)^2+cos(x)^2`; exact trig expressions can also be evaluated in the normal solver
8–10. Circle units — `circumference 7`, `circle area 7`, `arc length 7,90`, `sector area 7,90`, `chord length 7,60`
11. Information Handling — `mean of [2,4,6,8]`, `median [1,7,3,5]`, `mode of [1,2,2,3]`, `variance of [2,4,6]`, `standard deviation of [2,4,6]`
12. Probability — `probability 3 out of 52` or `probability 1/6`

The Punjab coverage remains representative rather than exhaustive; see the v0.8 expanded scope and limitations below.

## Expanded school mathematics + welcome screen (v0.8)

On opening the local web app, a welcome screen displays **ZENTRIX AI** and **M.Ayaan Chaudhry** before entering the workspace.

Additional command support added in v0.8:

- **Geometry / coordinate geometry:** `pythagoras 3,4`; `heron area 3,4,5`; `triangle area 10,6`; `distance 0,0,3,4`; `midpoint 0,2,4,6`; `slope 1,2,3,6`.
- **Mensuration:** `rectangle area 5,4`; `rectangle perimeter 5,4`; `cube volume 3`; `cuboid volume 2,3,4`; `cylinder volume 2,5`; `cone volume 3,4`; `sphere surface area 3` (also surface-area commands for cube/cuboid/cylinder and sphere volume).
- **Counting:** `permutation 5,2`; `combination 5,2`.
- **Grouped frequency data:** `grouped mean values [10,20,30] frequencies [2,3,1]` (returns mean, population variance, and standard deviation).
- **Unit conversions:** `convert 2.5 km to m`. Supported dimensions: length (mm/cm/m/km), mass (mg/g/kg), volume (ml/l), time (s/min/h). Cross-dimension conversions are rejected.
- **Algebraic identity check:** `prove (x+1)^2 = x^2+2*x+1`. This is a symbolic identity checker, not a general Euclidean geometry proof engine.
- **Guided word-problem templates:** `word problem: A car travels 120 km in 2 hours; find speed`; `word problem: simple interest on 1000 at 5% for 2 years`; `word problem: increase 200 by 15%`; `word problem: decrease 200 by 15%`; `word problem: sum of two consecutive integers is 25`. These are explicit templates, not general-purpose language understanding.

Run all suites from the project root:

```powershell
python tests/test_engine.py
python tests/test_curriculum_benchmark.py
python tests/test_expanded_school_math.py
```

Current representative regression suite: 37 core + 22 Punjab Class 10 + 38 cross-grade + 28 expanded geometry/statistics/utility/word-model cases. These are finite regression tests, not exhaustive validation against every edition or question in every board's textbook.

### Remaining limitations (disclosed)

- No OCR or handwriting recognition for photos/PDFs in this release; type the problem as text.
- No automatic diagram understanding or interactive ruler-compass construction.
- `prove` checks algebraic/trigonometric identities by symbolic simplification. It does not produce or validate general synthetic geometry proofs (for example, triangle congruence, circle theorems, or a diagram-based Pythagoras proof).
- Word problems still need to be translated into an equation or one of the explicit command formats; unrestricted natural-language reasoning is not built in.
- Grouped statistics currently handles value-frequency pairs and computes mean/variance/standard deviation; it does not generate histograms, ogives, quartiles, or class-boundary interpolation.
- Formula calculations assume the dimensions supplied by the user are the correct quantities (for example, perpendicular height for triangle/parallelogram area). Units are not inferred automatically.

Do not describe these limitations as solved. A later phase should add a diagram canvas/proof-rule system, OCR pipeline, guided word-problem modeller, and grouped-data chart/statistics tools with their own test suites.


## Word problems and generated figures (v1.1.0)

The initial diagram solver recognises common ladder-against-wall right-triangle questions and rectangle area/perimeter questions. It calculates with SymPy and draws labelled SVG figures from the computed values. This first release supports these defined patterns; it does not claim to understand every free-form word problem or construct every geometry diagram.


## Word problems and generated figures (v1.3.0)

- Ladder against a wall: Pythagorean theorem and labelled right-triangle diagram.
- Rectangular area and perimeter: labelled rectangle.
- Triangle area: base and perpendicular height with a labelled triangle.
- Circle area and circumference: radius or diameter parsing with a labelled circle.
- Each supported geometry result includes calculation steps and a formula verification check.
- The solver deliberately avoids guessing a circle radius when the statement does not identify radius or diameter.

This is a pattern-based guided solver, not a universal natural-language mathematics engine. For unfamiliar statements, Gemini may help interpret supported commands; unsupported or ambiguous questions should be clarified rather than treated as solved.


## v3.0.0 — Mathematical Research Platform

This release builds on the v1.7.0 laptop-optimized foundation and adds an integrated research workspace:

- **Research Lab:** single-variable symbolic analysis with first/second derivatives, antiderivatives, point evaluation, limits, roots, Taylor polynomials, definite integrals, and numerical samples.
- **Identity verification:** exact symbolic simplification plus numerical spot checks and an explicit warning that samples alone are not proof.
- **Multi-pass photo OCR:** three locally processed image variants and page-segmentation passes; OCR library and language data are fetched by the browser when first used.
- **Research report export:** printable HTML report that can be saved as PDF through the browser.
- **Learning profile:** subject-level performance estimates derived from Math Arcade attempts, with sample-size confidence shown. This is not yet a complete spaced-repetition or curriculum mastery system.
- **Knowledge topic map:** structured topic areas for algebra, calculus, linear algebra, statistics, differential equations and numerical mathematics.

### Important scope notes

- The proof tools are symbolic identity checks and the existing algebraic step auditor; they are not universal theorem provers.
- Graph Studio remains a 2D function plotter; this release does not claim full 3D or implicit-geometry plotting.
- OCR works best on clear printed text. Handwriting, dense notation, diagrams, stacked fractions and complex layouts may still need manual correction. Always review recognised text before solving.
- The Research Lab uses SymPy for exact symbolic operations and NumPy-backed numerical samples. Numerical results are approximations and may fail at singularities or outside an expression's domain.
- Core solving and research calculations do not require a paid AI API. Gemini remains optional.
- The app is tuned for modest laptops, but performance and OCR accuracy should be benchmarked on the actual target device and a representative image set.


## Latest release: 3.2.0
See `RELEASE_NOTES_3.2.0.md` and `TEST_REPORT_3.2.0.md` for the accuracy and verification improvements.
