# ZENTRIX AI — Learn, Solve, Master

**Mathematics Without Limits.**

ZENTRIX AI is a free mathematics learning workspace designed to help students understand problems, practise skills and prepare for exams. The current learning interface focuses on school mathematics, with a dedicated Matrix Lab and additional tools.

## What students can do

- **Solve:** work through supported arithmetic, algebra and other school-mathematics questions with step-by-step explanations.
- **Practise:** generate questions at different difficulty levels and check answers.
- **Prepare:** use the Exam Centre to practise selected subjects and test lengths.
- **Learn:** search the Definitions library for clear explanations and examples.
- **Visualise:** explore functions with 2D graphs and interactive, draggable 3D surface plots. The 2D graph studio includes automatic or custom y-axis scaling plus PNG and CSV export; 3D surfaces include built-in examples, custom x/y ranges, camera reset, and PNG/CSV export.
- **Explore:** use Matrix Lab for supported matrix operations.
- **Read photos and PDFs:** use browser-based OCR for images, extract selectable PDF text, or render scanned PDF pages and OCR them locally in your browser. Review the transcription before solving.
- **Build equations:** use the equation toolbar for fractions, powers, roots, Greek constants, operators, functions and a live mathematical preview.
- **Track learning:** review practice accuracy, topic-level performance, a seven-day activity chart, completed exams and saved calculations. Export progress to CSV or reset it locally.
- **Study:** review a built-in formula deck with spaced repetition (Again/Hard/Good/Easy scheduling) across algebra, geometry, trigonometry, calculus, statistics and probability. Use the built-in 25-minute focus / 5-minute break timer and track completed focus sessions locally.
- **Personalise the interface:** choose Soft Lavender, Ocean Blue, Sage Green or Rose Pink; switch light/dark appearance and comfortable/compact spacing. Preferences are saved on this device. Controls include clearer focus states, larger touch targets and reduced-motion support.

The solver is a tool for learning, not a substitute for checking important work. OCR can misread handwriting and mathematical notation, so review the extracted question before solving. Scanned PDF OCR is processed locally and limited to eight pages per run to keep browser memory use manageable. Progress data is stored in browser local storage and does not automatically sync across devices.

## Free by design

Core mathematics and learning tools are intended to remain free. Optional external AI providers may require a user-supplied API key and can incur charges with that provider. You do not need an AI-provider key for core mathematical calculations.

## Technology

- Python and FastAPI
- SymPy for symbolic mathematics
- NumPy, SciPy and mpmath for numerical tools and diagnostics
- HTML, CSS and JavaScript frontend
- KaTeX for mathematical rendering

## Run locally on Windows

1. Download or clone this repository.
2. Extract it if downloaded as a ZIP.
3. Run `start_zentrix.bat`.
4. Open the local address shown in the terminal (normally `http://127.0.0.1:8000`).

Core calculations work without connecting an external AI provider. The installable web app also caches its app shell for offline reopening; solving still requires the app's API server to be reachable. PDF text extraction requires the PDF.js library to load, and scanned PDFs need image OCR.

## Project and community

- Source code: [GitHub repository](https://github.com/ibrahimchaudharyofficial-hash/zentrix-ai)
- Growth and content guide: [Audience-building playbook](docs/GROWTH_PLAN.md)

If you try ZENTRIX AI, share specific feedback: the question you entered, what you expected, what happened, and (if possible) a screenshot with personal information removed. Helpful bug reports make the solver better.

## Project principles

1. Keep essential mathematics and learning tools accessible for free.
2. Explain the method, not just the final answer.
3. Be transparent when a result is approximate, unverified or outside the supported scope.
4. Protect user privacy and avoid collecting unnecessary personal information.

**Created by Ayaan Chaudhry; developed with assistance from ChatGPT.**


## Adaptive learning coach

The Learning Studio includes a private adaptive study coach. It reviews locally saved practice attempts, identifies topics with at least two recorded answers, recommends a practice difficulty, tracks a configurable daily target and active-day streak, and starts a recommended practice set. The coach runs entirely in the browser using local progress data; it does not require an AI API key or send study history to a server.


## Research mathematics workbench

The Research Lab adds free, local multivariable analysis without requiring an AI provider or API key:

- Scalar fields: exact symbolic gradients and Hessians, Hessian eigenvalue diagnostics, local critical-point classification, and second-order Taylor polynomials.
- Vector fields: exact Jacobians and divergence, three-dimensional curl, and a local Jacobian-symmetry test for conservative fields.
- Bounded input validation, finite point checks, selectable 15–80 digit evaluation precision, and explicit notes distinguishing local numerical diagnostics from global proofs.

The research endpoints use the existing safe mathematical parser and SymPy/NumPy. They do not execute arbitrary Python, send expressions to external AI services, or require paid services.


## Advanced Matrix Lab

The Matrix Lab supports exact symbolic operations through the solver:

- `determinant of [[...]]`, `inverse of [[...]]`, `eigenvalues of [[...]]`, `rank of [[...]]`, and `transpose of [[...]]`
- `rref of [[...]]` for reduced row-echelon form and pivot columns
- `nullspace of [[...]]`, `column space of [[...]]`, and `row space of [[...]]` for basis calculations
- `lu of [[...]]` and `qr of [[...]]` for exact matrix factorizations
- `svd of [[...]]` and `condition number of [[...]]` for real numeric matrices

Use nested square-bracket notation, for example `[[1,2],[3,4]]`. SVD and condition-number calculations require real numeric entries; the other listed operations retain symbolic entries where supported. The Matrix Lab also exposes quick-action cards for these operations so users can try each workflow without memorising command syntax. The eigenvalue workflow displays both the characteristic equation and its roots, including algebraic multiplicities. Verification checks are diagnostics, not a substitute for a formal proof.


## Graph Studio analysis

Graph Studio can numerically estimate real roots and stationary points over the selected x-interval, classify turning points using the second derivative, and display the first two symbolic derivatives and y-intercept. The analysis is explicitly labelled approximate: it uses a bounded sign-change search and is not a proof or a complete root-isolation method. Constant and identically-zero functions are handled separately.


## Exam Centre

Practice tests can be run with a 60-second-per-question limit, a 90-second-per-question limit, or without a timer. Timed sessions finish automatically when the clock reaches zero. The result screen includes an answer review with the selected answer, correct answer and worked explanation; unanswered questions are included in the review. The question bank includes arithmetic, algebra, geometry, trigonometry, statistics, calculus, matrices and probability.

## Proof Auditor and misconception feedback

The Proof Auditor checks adjacent algebra lines using symbolic comparison and polynomial solution-set checks. When a transition appears invalid, it can add a cautious pattern-based misconception suggestion and a short practice prompt. These suggestions include a confidence label and are learning hints, not definitive claims about a student's reasoning.
