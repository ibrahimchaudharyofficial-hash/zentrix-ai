# ZENTRIX AI Billing — secure setup

Billing remains disabled until the owner configures Paddle and the backend secrets. Never commit API keys, webhook secrets, Supabase service-role keys, or customer payment details to GitHub.

## Provider choice

The integration is built for Paddle Billing. Seller onboarding, identity/business verification, product approval, and payout eligibility must be confirmed directly with Paddle before launch.

## 1. Supabase database

For a fresh project:
1. Run `supabase_schema.sql` if the existing user-data table has not already been created.
2. Run `billing_schema.sql`.

The connected project already has the four billing migrations recorded under `supabase/migrations/`. Billing tables have RLS enabled, no browser policies, and no `anon` or `authenticated` table privileges. Only the backend `service_role` can access billing data and execute the atomic webhook function. Never expose its key.

## 2. Paddle dashboard

1. Apply for a Paddle account and complete its verification.
2. Create a ZENTRIX AI product and a monthly recurring price.
3. Create a separate one-time lifetime price.
4. Optionally create a fixed-amount one-time donation price. Variable-amount donations need a separate reviewed checkout flow.
5. Set up a checkout URL on the deployed ZENTRIX domain and have Paddle approve that domain.
6. Create a notification destination pointing to `https://YOUR-APP-DOMAIN/api/billing/webhook`.
7. Subscribe to `subscription.created`, `subscription.updated`, `subscription.activated`, `subscription.trialing`, `subscription.past_due`, `subscription.canceled`, `subscription.paused`, `subscription.resumed`, and `transaction.completed`.
8. Copy the notification destination's endpoint secret. Keep it private.

## 3. Backend environment variables

Set these in the actual backend host's secret/environment settings, not in GitHub, frontend JavaScript, or a committed .env:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` — server only
- `PADDLE_API_KEY` — server only
- `PADDLE_WEBHOOK_SECRET_KEY` — server only
- `PADDLE_PRICE_ID_MONTHLY` — Paddle price ID beginning `pri_`
- `PADDLE_PRICE_ID_LIFETIME` — Paddle price ID beginning `pri_`
- `PADDLE_PRICE_ID_DONATION` — optional fixed donation price ID beginning `pri_`
- `PADDLE_CHECKOUT_URL` — HTTPS checkout page on the Paddle-approved domain
- `PADDLE_ENVIRONMENT=sandbox` while testing; use `live` only after successful sandbox tests and approval

## 4. API behaviour

- `GET /api/billing/status` requires a valid Supabase access token.
- `POST /api/billing/checkout` requires a signed-in account and accepts `monthly`, `lifetime`, or `donation`.
- `POST /api/billing/webhook` verifies the raw request body with Paddle's HMAC-SHA256 signature and the documented five-second replay-protection window.
- A single Postgres function records each event and updates the entitlement atomically. Duplicate deliveries are ignored; older out-of-order events cannot overwrite newer subscription state.
- Monthly access is accepted only when the actual subscription item matches the configured monthly price. Lifetime access requires a completed transaction containing the configured lifetime price, and later monthly events cannot downgrade lifetime access. Donations never grant Premium.
- The browser cannot read or write billing tables. The backend validates the user's Supabase session before creating a checkout.

## 5. Before launch

Test all cases in Paddle sandbox: successful monthly payment, renewal, failed payment, cancellation, lifetime purchase, donation, duplicate webhook, invalid signature, expired signature, signed-out checkout, and another user's token. Confirm that canceled/past-due subscriptions do not retain active access. Publish clear prices, renewal/cancellation/refund terms, privacy policy, and support contact before enabling live checkout.

The current Premium UI still says "Coming soon". Checkout buttons, feature gating, Paddle credentials, sandbox delivery tests, and deployment verification remain pending. No payments are enabled by this work.
