create table if not exists public.zentrix_billing (
  user_id uuid primary key references auth.users(id) on delete cascade,
  plan text not null default 'free' check (plan in ('free','monthly','lifetime')),
  status text not null default 'inactive' check (status in ('inactive','active','trialing','past_due','paused','canceled')),
  paddle_subscription_id text unique,
  paddle_customer_id text,
  current_period_end timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.zentrix_billing enable row level security;

create table if not exists public.zentrix_billing_events (
  event_id text primary key,
  event_type text not null,
  received_at timestamptz not null default now()
);
alter table public.zentrix_billing_events enable row level security;

create index if not exists idx_zentrix_billing_status
  on public.zentrix_billing(status, plan);