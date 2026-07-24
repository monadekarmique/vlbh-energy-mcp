-- Praticienne invite-token (C4, Option B — ADR identité 24.07)
-- Projet Supabase : qodnztqsawsofimbsfhb
-- ⚠️ NON APPLIQUÉ EN PROD — revue Patrick puis apply_migration.
--
-- Premier-lien Apple/Google d'une praticienne via un lien d'invitation personnel,
-- pré-lié à son svlbh_id, consommé à la 1re connexion. Le bind réutilise le RPC
-- admin_link_praticienne_alias (déjà en prod). Pas de champ WhatsApp : une praticienne
-- bascule entre les 4 bridges (z1-z4) selon sa vibration — le lien part par le canal
-- qu'elle utilise, peu importe lequel.

create table if not exists public.praticienne_invite (
  id                   uuid primary key default gen_random_uuid(),
  token_hash           text not null unique,     -- sha256 du token (jamais le token en clair)
  svlbh_id             uuid not null,            -- praticienne pré-liée
  created_by_svlbh_id  uuid,                     -- qui a créé l'invitation (Patrick)
  expires_at           timestamptz not null,
  consumed_at          timestamptz,
  consumed_by_user_id  uuid,                     -- l'identité auth qui l'a consommée
  created_at           timestamptz not null default now()
);

create index if not exists idx_praticienne_invite_active
  on public.praticienne_invite (token_hash) where consumed_at is null;

alter table public.praticienne_invite enable row level security;
-- Aucune policy anon/authenticated : le backend FastAPI (service_role) est seul
-- lecteur/écrivain. service_role contourne RLS by design.
