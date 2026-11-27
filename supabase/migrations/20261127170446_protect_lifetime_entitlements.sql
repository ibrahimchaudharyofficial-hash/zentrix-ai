create or replace function public.zentrix_apply_billing_event(
  p_event_id text,
  p_event_type text,
  p_occurred_at timestamptz,
  p_user_id uuid,
  p_plan text,
  p_status text,
  p_subscription_id text default null,
  p_customer_id text default null,
  p_current_period_end timestamptz default null
)
returns boolean
language plpgsql
security invoker
set search_path = pg_catalog, public
as $function$
declare
  inserted_event_id text;
begin
  if p_event_id is null or length(p_event_id) < 1 or length(p_event_id) > 255
     or p_event_type is null or length(p_event_type) < 1 or length(p_event_type) > 120
     or p_occurred_at is null then
    raise exception 'Invalid billing event identity or timestamp';
  end if;

  insert into public.zentrix_billing_events(event_id, event_type)
  values (p_event_id, p_event_type)
  on conflict (event_id) do nothing
  returning event_id into inserted_event_id;

  if inserted_event_id is null then
    return false;
  end if;

  if p_user_id is not null then
    if p_plan not in ('monthly', 'lifetime')
       or p_status not in ('inactive', 'active', 'trialing', 'past_due', 'paused', 'canceled') then
      raise exception 'Invalid billing entitlement';
    end if;

    insert into public.zentrix_billing(
      user_id, plan, status, paddle_subscription_id,
      paddle_customer_id, current_period_end, updated_at, last_event_at
    ) values (
      p_user_id, p_plan, p_status, p_subscription_id,
      p_customer_id, p_current_period_end, now(), p_occurred_at
    )
    on conflict (user_id) do update set
      plan = excluded.plan,
      status = excluded.status,
      paddle_subscription_id = excluded.paddle_subscription_id,
      paddle_customer_id = excluded.paddle_customer_id,
      current_period_end = excluded.current_period_end,
      updated_at = now(),
      last_event_at = excluded.last_event_at
    where (
      public.zentrix_billing.last_event_at is null
      or public.zentrix_billing.last_event_at <= excluded.last_event_at
    )
    and (
      public.zentrix_billing.plan <> 'lifetime'
      or excluded.plan = 'lifetime'
    );
  end if;

  return true;
end;
$function$;

revoke all on function public.zentrix_apply_billing_event(text, text, timestamptz, uuid, text, text, text, text, timestamptz) from public, anon, authenticated;
grant execute on function public.zentrix_apply_billing_event(text, text, timestamptz, uuid, text, text, text, text, timestamptz) to service_role;