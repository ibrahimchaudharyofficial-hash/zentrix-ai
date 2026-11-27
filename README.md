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
