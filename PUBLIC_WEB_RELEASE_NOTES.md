# ZENTRIX AI v4.1.1 — Public Web Edition

## Added
- Public guest mode: the math workspace can be used without registration.
- Optional Supabase email/password sign-up and sign-in.
- Account cloud sync for calculation history, exam statistics, active usage, arcade attempts, and selected preferences.
- Supabase Row Level Security schema so authenticated users can access only their own progress row.
- Render Blueprint for a Python/FastAPI public deployment.
- Public configuration endpoint exposes only Supabase URL and public anon/publishable key.

## Public deployment safety changes
- Public-mode arcade and learning endpoints no longer read or write a shared SQLite progress database.
- Public-mode disables server-wide AI provider key settings and shared-key image transcription.
- Public-mode tutor does not use a server-wide Gemini key.
- Guest progress is kept in browser storage; signed-in data is synchronized to the authenticated user's Supabase row.

## Preserved
- Existing v4.0.1 mathematics engine, frontend, Matrix Lab, graphs, solver, verification, practice, definitions, Exam Centre, and learning tools.

## Verification
- Python compile checks passed.
- Inline JavaScript syntax check passed with Node.js.
- Full automated test suite: 91 passed.

## Not yet done
- No Render service or Supabase project has been created by this package.
- No public URL exists until the owner configures the two services and deploys.
- Real signup/email confirmation and multi-device cloud sync still need end-to-end testing against the owner's Supabase project.


## v4.1.1 — Direct workspace launch
- Removed the full-screen ZENTRIX identity/welcome splash and its Enter Workspace button.
- Website now opens directly to the mathematics workspace.
- Usage tracking starts automatically on page load.
