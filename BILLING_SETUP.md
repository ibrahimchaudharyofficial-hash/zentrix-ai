# ZENTRIX AI Billing — secure setup

Billing is intentionally disabled until the owner configures the provider and server secrets. Never commit API keys, webhook secrets, Supabase service-role keys, or customer payment details to GitHub.

## Provider choice

The integration is built for Paddle Billing. Paddle's published seller-country policy does not list Pakistan as unsupported, and its Pakistan page describes SaaS payment and subscription management. Acceptance is still subject to Paddle's onboarding, identity/business verification, and product approval. Confirm eligibility and payout details directly with Paddle before relying on it.

## 1. Supabase database

1. Open the Supabase SQL Editor.
2. Run \`supabase_schema.sql\` if the existing user-data table has not already been created.
3. Run \`billing_schema.sql\`.
4. The billing schema enables RLS, removes all anon and authenticated table privileges, and grants the backend service_role access only. Do not add browser-facing policies or expose the service-role key.

## 2. Paddle dashboard

1. Apply for a Paddle account and complete its verification.
2. Create a ZENTRIX AI product and a monthly recurring price.
3. Create a separate one-time lifetime price.
4. Optionally create a fixed-amount one-time donation price. The current first integration uses a fixed donation product; variable-amount donations need a separate reviewed checkout flow.
5. Set up a checkout URL on the deployed ZENTRIX domain and have Paddle approve that domain.
6. Create a notification destination pointing to \`https://YOUR-APP-DOMAIN/api/billing/webhook\`.
7. Subscribe to \`subscription.created\`, \`subscription.updated\`, \`subscription.canceled\`, \`subscription.paused\`, \`subscription.resumed\`, and \`transaction.completed\`.
8. Copy the notification destination's endpoint secret. Keep it private.

## 3. Server environment variables

Set these in the backend host's secret/environment settings (not in GitHub, frontend JavaScript, or a committed .env):

- \`SUPABASE_URL\`
- \`SUPABASE_ANON_KEY\`
- \`SUPABASE_SERVICE_ROLE_KEY\` — server only; never expose to the browser
- \`PADDLE_API_KEY\` — server only
- \`PADDLE_WEBHOOK_SECRET_KEY\` — server only
- \`PADDLE_PRICE_ID_MONTHLY\` — Paddle price ID beginning \`pri_\`
- \`PADDLE_PRICE_ID_LIFETIME\` — Paddle price ID beginning \`pri_\`
- \`PADDLE_PRICE_ID_DONATION\` — optional fixed donation price ID beginning \`pri_\`
- \`PADDLE_CHECKOUT_URL\` — HTTPS checkout page on the Paddle-approved domain
- \`PADDLE_ENVIRONMENT=sandbox\` while testing; change to \`live\` only after successful sandbox tests and approval

## 4. API behaviour

- \`GET /api/billing/status\` requires a valid Supabase access token.
- \`POST /api/billing/checkout\` requires a signed-in account and accepts \`monthly\`, \`lifetime\`, or \`donation\`.
- \`POST /api/billing/webhook\` accepts only Paddle requests with a valid timestamped HMAC-SHA256 signature with a five-second freshness window.
- Monthly/lifetime access is written to Supabase only from verified provider events. Donation events never grant Premium.
- The browser cannot write to billing tables. The backend checks the user's Supabase session with Supabase Auth before creating a checkout.

## 5. Before launch

Test all cases in Paddle sandbox: successful monthly payment, renewal, failed payment, cancellation, lifetime purchase, donation, duplicate webhook, invalid signature, expired signature, signed-out checkout, and another user's token. Confirm that canceled/past-due subscriptions do not retain active access. Publish clear prices, renewal/cancellation/refund terms, privacy policy, and support contact before enabling live checkout.

The database migrations applied to the connected Supabase project are tracked under `supabase/migrations/`. The current UI remains "Coming soon"; checkout buttons, feature gating, Paddle credentials, sandbox delivery tests, and deployment verification are still pending. No payments are enabled by this work.
