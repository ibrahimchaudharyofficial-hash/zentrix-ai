# Zentrix AI v0.9.1 — Simple Gemini setup

- Added an in-app AI settings panel so users can paste and save a Gemini API key without editing `.env` manually.
- The local backend stores the key in the project-root `.env` file and never returns it to the browser.
- Added a live Gemini connection check, status display, and remove-key action.
- Settings endpoints accept only loopback requests and reject cross-origin requests.
- Local mathematical solving remains available without Gemini.

The key is stored on the same computer running Zentrix. Do not expose the local development server to the public internet or share the `.env` file.
