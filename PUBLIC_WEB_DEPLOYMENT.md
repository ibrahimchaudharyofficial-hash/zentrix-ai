# ZENTRIX AI v4.1.1 — Public Web Edition

This package prepares the existing v4.0.1 FastAPI + static frontend for a public guest-access website with optional Supabase accounts and cross-device progress sync. It retains the existing math engine and tools; it does not replace the UI or require a React rewrite.

## Public/guest behaviour
- Visitors can use the mathematics workspace without registering.
- Browser history, theme and usage information remain in that visitor's browser.
- In public mode, the old shared SQLite arcade/progress endpoints do not read or write the server's shared database. Guest profile endpoints return empty progress rather than exposing another visitor's activity.
- Server-wide AI key settings and server-wide AI photo OCR are disabled in public mode. This prevents one operator-configured provider key from being exposed as a shared public feature. The offline math solver and offline tutor remain available.
- Sign-in and account sync use Supabase Auth plus the user's own row in `zentrix_user_data`. Row Level Security is enabled by the supplied SQL. The browser receives only the Supabase project URL and public anon/publishable key; never put a Supabase service-role key in the browser or Render environment for this design.

## Configure Supabase
1. Create a Supabase project.
2. Open SQL Editor and run `supabase_schema.sql`.
3. In Authentication > URL Configuration, set the Site URL to your eventual Render URL and add that URL to Redirect URLs.
4. Copy the Project URL and public anon/publishable key from the Supabase project API settings. Do not use the service-role/secret key.

## Deploy to Render
1. Push the contents of this project folder to a private or public GitHub repository you control. Do not commit `.env` or real API keys.
2. In Render, choose **New > Blueprint** and connect that repository. Render reads `render.yaml`.
3. In the Render service environment, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` to the values from Supabase. Keep `ZENTRIX_PUBLIC_MODE=true`.
4. Deploy. Open `/api/health` and `/api/public-config` on the resulting site to confirm the service and public auth config.
5. In Supabase, update Site URL and Redirect URLs to the exact deployed URL.
6. Test guest solving, sign-up, email confirmation, sign-in, cross-device sync, and sign-out.

## Important limitations before announcing the site
- This is a deployment-ready integration package, not a deployed public website. You must create/connect your own Supabase and Render projects and provide their configuration.
- Free Render web services can sleep when idle; the first request after inactivity may take time. Free-tier terms and limits can change.
- Supabase email confirmation and SMTP settings may need configuration for reliable public registration.
- The first account-sync implementation synchronizes browser-side history, exam stats, theme, and active-use records. It does not yet synchronize every possible UI state or arcade attempt detail.
- Per-user API keys / AI provider billing are deliberately not enabled in this public edition. Do not add a global provider key and advertise unlimited AI usage.
- Before large-scale launch, add request rate limiting, CAPTCHA/abuse controls, monitoring, privacy policy, terms, account deletion/export, database backups, and load testing.
- Existing v4.0.1 source and desktop package are left untouched; this is a separate public-web build.
