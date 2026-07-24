-- Onboarding claim flow — challenge store + admin alias RPC (doctrine #11)
-- Projet Supabase : qodnztqsawsofimbsfhb
-- ⚠️ NON APPLIQUÉ EN PROD — revue Patrick puis apply_migration.
-- Voir docs/specs/onboarding-claim-flow-spec-v0.1.md

-- 1. Défi de revendication (proof-of-possession d'un canal sur fiche).
create table if not exists public.auth_claim_challenge (
  id                uuid primary key default gen_random_uuid(),
  claimant_user_id  uuid not null,          -- session Apple orpheline qui revendique
  target_svlbh_id   uuid not null,          -- praticienne_profile.svlbh_id revendiqué
  code_hash         text not null,          -- SHA-256 du code (jamais le code en clair)
  channel           text not null check (channel in ('whatsapp','email')),
  channel_hint      text,                   -- destination masquée montrée à l'utilisateur
  attempts          int  not null default 0,
  max_attempts      int  not null default 5,
  expires_at        timestamptz not null,
  consumed_at       timestamptz,
  created_at        timestamptz not null default now()
);

create index if not exists idx_claim_challenge_claimant
  on public.auth_claim_challenge (claimant_user_id) where consumed_at is null;

alter table public.auth_claim_challenge enable row level security;
-- Aucune policy anon/authenticated : le backend FastAPI (service_role) est seul
-- lecteur/écrivain. service_role contourne RLS by design.

-- 2. Alias admin : rattache une identité auth explicite à un svlbh_id praticienne.
--    Miroir de auto_link_alias() mais pour un user_id arbitraire (piloté backend).
create or replace function public.admin_link_praticienne_alias(
  p_svlbh_id  uuid,
  p_user_id   uuid,
  p_email     text,
  p_provider  text,
  p_note      text default null
) returns uuid
  language plpgsql
  security definer
  set search_path to 'public','pg_catalog'
as $$
begin
  insert into public.praticienne_user_alias
    (svlbh_id, supabase_user_id, alias_email, alias_provider, notes)
  select p_svlbh_id, p_user_id, lower(coalesce(p_email,'')), coalesce(p_provider,'unknown'),
         coalesce(p_note, 'claim flow — doctrine #11')
  where not exists (
    select 1 from public.praticienne_user_alias where supabase_user_id = p_user_id
  );
  return p_svlbh_id;
end;
$$;

revoke all on function public.admin_link_praticienne_alias(uuid,uuid,text,text,text)
  from public, anon, authenticated;
