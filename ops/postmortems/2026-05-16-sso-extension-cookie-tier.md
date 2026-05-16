# Postmortem — SSO inter-subdomain extension + consolidation auth.users

**Date** : 2026-05-16 (S5 J3 PI-1)
**Auteur** : Patrick Bays × Claude Opus 4.7
**Sévérité** : P2 — bloque l'extension VLBH Pathology Mapper (workflow ST3/ST4) mais workarounds disponibles (Apple Sign-In direct dans l'extension)
**Statut** : Résolu et validé en production
**Durée incident** : ~36h (observable depuis fin 2026-05-14, résolution finale 2026-05-16 11:53)
**Backlogs résolus** : #11 (multi-comptes auth.users), #18 (SSO server-side cookies cleanup)

---

## Résumé exécutif

Deux bugs structurels chevauchants empêchaient l'extension Chrome **VLBH Pathology Mapper** (v0.2.10) de récupérer une session Supabase via SSO depuis `pwa.app.svlbh.com` :

1. **Côté serveur (#18)** — la routine `expireHostOnlyLegacyCookies()` dans `auth/callback/route.ts` effaçait silencieusement les cookies `sb-*-auth-token` immédiatement après que `exchangeCodeForSession()` les venait de poser. Cette routine avait été conçue pour cleanup l'époque post-activation de `NEXT_PUBLIC_COOKIE_DOMAIN=.svlbh.com` ; mais comme `COOKIE_DOMAIN` a été retiré (cassait Apple Sign-In, cf. handoff 2026-05-15), les nouveaux cookies posés tombaient dans la même cible host-only que les anciens. Conséquence : seul le cookie `code-verifier` PKCE subsistait côté navigateur, la session était maintenue côté serveur seulement.

2. **Côté Supabase Postgres (#11)** — `auth_svlbh_id()` consultait directement `praticienne_profile.supabase_user_id`, ignorant la table de résolution `praticienne_user_alias`. Patrick avait 5 `auth.users` distincts (Apple email canonique + 4 Google/email secondaires) dont 2 résolvaient vers des persona testing REVOKED (Test T3, Test T4) au lieu du svlbh_id canonique `52adbc98`.

**Fix combiné** :
- Guard early-return dans `expireHostOnlyLegacyCookies()` si `COOKIE_DOMAIN` absent (#18 phase 1)
- Cookie tier dédié `vlbh-ext-pair-code` Domain=.svlbh.com non-HttpOnly + endpoint `/api/extension/exchange` service_role one-time consume (#18 phase 2)
- Refactor `auth_svlbh_id()`, `is_owner_st6()`, `current_praticienne_cabinet_id()` pour consulter `praticienne_user_alias` en priorité (#11)
- Insertion des 4 aliases manquants Patrick → tous résolvent vers `52adbc98` canonique

**Validation** : screenshot 2026-05-16 11:53 — 3 cookies présents sur pwa.app après reconnexion Apple Sign-In dont `vlbh-ext-pair-code` ; extension v0.2.19 sync ✓ vert via `chrome.cookies.getAll({domain:'svlbh.com'})` + POST exchange.

---

## Contexte

L'extension **VLBH Pathology Mapper** est l'outil quotidien des praticiennes ST3 Formation pour mapper pathologies / symptômes / VIFA pendant les séances. Elle doit récupérer une session Supabase pour lire les `decodages_v0`, `pathology_decodage` etc. Le design initial v0.2.10 prévoyait un SSO transparent depuis les 4 sites svlbh.com (pwa.app, priv, cockpit, svlbh.com) via lecture du cookie auth `sb-...-auth-token` partagé sur `.svlbh.com`.

L'activation initiale de `NEXT_PUBLIC_COOKIE_DOMAIN=.svlbh.com` avait été tentée pour permettre ce partage, mais elle cassait Apple Sign-In (loop infinie sur le callback). La désactivation de `COOKIE_DOMAIN` a laissé en place une routine de cleanup orpheline qui effaçait les nouveaux cookies host-only.

Symptôme externe pour les praticiennes : extension affichant *"Connexion requise pour accéder à tes données — Pas de session web .svlbh.com — ouvre pwa.app.svlbh.com ou cockpit.svlbh.com d'abord, puis recharge"* même après authentification manifeste sur pwa.app.

---

## Timeline

| Date | Événement |
|------|-----------|
| 2026-05-08 | Création de `praticienne_user_alias` (backfill primary aliases depuis `praticienne_profile.supabase_user_id`) |
| 2026-05-13 | Extension v0.2.10 publiée, SSO via cookie reader `.svlbh.com` |
| 2026-05-14 | `NEXT_PUBLIC_COOKIE_DOMAIN=.svlbh.com` désactivé suite à incident Apple Sign-In loop ; routine `expireHostOnlyLegacyCookies` reste active |
| 2026-05-15 | Handoff écrit pour SSO pwa/priv/cockpit (backlog #18) ; bug reproductible mais cause non identifiée |
| 2026-05-16 09:30 | Patrick reporte bug Photos onglet : `new row violates row-level security policy` ; investigation découvre 0 policies RLS sur `decodages_v0` malgré RLS=true |
| 2026-05-16 09:45 | Migration `decodages_v0_rls_policies` : 4 policies SELECT/INSERT/UPDATE/DELETE basées sur `auth_svlbh_id()` |
| 2026-05-16 10:15 | Test extension v0.2.10 → toujours bloqué sur SSO ; lancement diagnostic structural |
| 2026-05-16 10:30 | Patrick sonde radiesthésiquement matrice 7 hypothèses Postgres → confirme hypothèse 5 (trigger / mécanisme qui efface les cookies côté client) |
| 2026-05-16 10:35 | Lecture `auth/callback/route.ts` : identification de `expireHostOnlyLegacyCookies` comme cause racine. Commit `3199d08` : guard early-return si COOKIE_DOMAIN absent |
| 2026-05-16 10:59 | Validation : 2 cookies présents sur pwa.app après reconnexion Apple — `sb-...-auth-token` (32K) **enfin posé** |
| 2026-05-16 11:00 | Extension v0.2.12 (cookie reader pwa.app) testée → ne voit toujours pas les cookies (`GLOBAL store: 0 cookies total`) |
| 2026-05-16 11:00 → 11:30 | Itérations v0.2.13 / v0.2.14 / v0.2.15 / v0.2.16 / v0.2.17 / v0.2.18 — debug verbose, scan global, executeScript, optional_host_permissions — toutes échouent (extension semble totalement isolée du cookie store Chrome) |
| 2026-05-16 11:30 | Patrick sonde la matrice 16 options → Famille E (architecture) retient sa vote |
| 2026-05-16 11:35 | Plan accepté : cookie tier `vlbh-ext-pair-code` dédié extension (Domain=.svlbh.com, non-HttpOnly, opaque) |
| 2026-05-16 11:45 | Commit `d2dbbc1` : backend `auth/callback` génère pair-code + `/api/extension/exchange` service_role |
| 2026-05-16 11:50 | Commit `bc9d2eb` : extension v0.2.19 lit le pair-cookie + redeem POST |
| 2026-05-16 11:53 | **Validation finale** — screenshot Patrick montre 3 cookies dont `vlbh-ext-pair-code`, extension sync ✓ |
| 2026-05-16 12:00 | Consolidation #11 : INSERT 2 aliases manquants + UPDATE 2 aliases existants → 5/5 user_ids Patrick résolvent vers `52adbc98` |
| 2026-05-16 12:05 | Refactor `auth_svlbh_id()` + `is_owner_st6()` + `current_praticienne_cabinet_id()` pour consulter alias en priorité |

---

## Cause racine

### Bug #18 — `expireHostOnlyLegacyCookies` orphelin

```ts
// auth/callback/route.ts ligne 30 (avant fix)
function expireHostOnlyLegacyCookies(request: NextRequest, response: NextResponse) {
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  for (const c of request.cookies.getAll()) {
    if (!c.name.startsWith("sb-")) continue;
    response.headers.append(
      "Set-Cookie",
      `${c.name}=; Path=/; Max-Age=0; HttpOnly${secure}; SameSite=Lax`,
    );
  }
}
```

Cette routine avait été conçue dans le cadre d'une migration vers `COOKIE_DOMAIN=.svlbh.com` (handoff `2026-05-15-routine-nocturne-mtc`). Le contrat implicite était :

> Quand `COOKIE_DOMAIN=.svlbh.com` est actif, le SDK Supabase pose les cookies sur `.svlbh.com` (Domain attribute). On émet en parallèle des Set-Cookie d'expiration **host-only** (sans Domain attribute) pour effacer les anciens cookies legacy. Browsers gèrent les deux scopes indépendamment.

Or `COOKIE_DOMAIN` a été désactivé pour résoudre un autre incident (Apple Sign-In loop). Le SDK Supabase est revenu à poser les cookies **host-only sur pwa.app.svlbh.com**. La routine d'expiration cible **précisément le même scope** → cleanup self-defeating.

### Bug #11 — auth_svlbh_id() ignore les aliases

```sql
-- Version avant fix
CREATE FUNCTION public.auth_svlbh_id() RETURNS uuid
  AS $$ SELECT svlbh_id FROM praticienne_profile
        WHERE supabase_user_id::text = auth.uid()::text LIMIT 1 $$;
```

La table `praticienne_user_alias` existait depuis 2026-05-08 avec un backfill, mais aucune fonction RLS ne la consultait. Si Patrick se loggait avec `bays.patrick@gmail.com` (user_id `14230ea7`), `auth_svlbh_id()` retournait le svlbh_id `3b306daf` du persona "Test T4 Pro-NonCercle" REVOKED au lieu du canonique Patrick `52adbc98`.

---

## Fix appliqué

### Phase 1 — Guard expireHostOnlyLegacyCookies (#18 phase 1)

Commit `3199d08` :

```ts
function expireHostOnlyLegacyCookies(request, response) {
  if (!process.env.NEXT_PUBLIC_COOKIE_DOMAIN) return; // 🩹 GUARD
  // ... existing cleanup logic
}
```

### Phase 2 — Cookie tier pair-code (#18 phase 2)

Architecture :

```
Apple/Google Sign-In → /auth/callback
                       ↓ exchangeCodeForSession (pose sb-auth-token host-only)
                       ↓ maybeIssueExtensionPairCode :
                          - randomBytes(24).toString('hex') = 48 chars opaque
                          - INSERT extension_pairing_code { code, svlbh_id, access_token,
                            refresh_token, expires_at=NOW+5min }
                          - Set-Cookie vlbh-ext-pair-code Domain=.svlbh.com Max-Age=300
                            Secure SameSite=Lax (PAS HttpOnly)
                       ↓ redirect /dashboard

Extension Chrome → chrome.cookies.getAll({domain:'svlbh.com'}) → vlbh-ext-pair-code
                 ↓ POST /api/extension/exchange { code }
                 ↓ service_role : SELECT + UPDATE consumed_at + return tokens
                 ↓ supabase.auth.setSession() → ✓
```

Commits : `d2dbbc1` (backend) + `bc9d2eb` (extension v0.2.19).

### Phase 3 — Consolidation auth.users (#11)

Migration `consolidate_patrick_auth_users_aliases` :
- UPDATE 2 aliases existants (Test T3, Test T4) → svlbh_id `52adbc98`
- INSERT 2 nouveaux aliases (Google secondary, email secondary) → `52adbc98`

Migration `auth_svlbh_id_uses_alias` :
- `auth_svlbh_id()` réécrit : `COALESCE(alias.svlbh_id, profile.svlbh_id)`
- `is_owner_st6()` et `current_praticienne_cabinet_id()` refactor pour passer par `auth_svlbh_id()`

Validation : 5/5 user_ids Patrick résolvent vers `52adbc98 ✅ Patrick canonique`.

---

## Métriques

- **9 versions extension** publiées entre v0.2.11 et v0.2.19 (8 itérations diagnostic en ~2h)
- **4 migrations Supabase** appliquées (`decodages_v0_rls_policies`, `extension_pairing_code`, `consolidate_patrick_auth_users_aliases`, `auth_svlbh_id_uses_alias`)
- **3 commits svlbh-pro-web** (`3199d08` callback fix, `d2dbbc1` cookie tier backend, `bc9d2eb`/`240c91a` outils bumps)
- **2 backlogs résolus** (#11, #18)
- **0 perte de données** (tous les profils REVOKED restent en place pour audit)

---

## Leçons retenues

### 1. Code de cleanup défensif doit être **garde-fou**ed

`expireHostOnlyLegacyCookies` était sémantiquement "cleanup post-migration" mais n'avait aucun guard sur la pré-condition de migration. Lorsque la migration a été reverted, la cleanup est devenue auto-destructrice.

**Pattern à appliquer** : tout cleanup conditionnel à une variable d'env doit `return` early si la variable n'est pas dans l'état attendu. Sans guard, le cleanup peut survivre à son contexte d'application.

### 2. Audit de **toute la chaîne callback OAuth** quand SSO ne marche pas

Le diagnostic a tâtonné sur Chrome cookies API, partitionKey, profile, executeScript pendant ~2h alors que la cause était dans le **callback serveur**. Quand un cookie OAuth disparaît silencieusement, **toujours auditer la response HTTP du callback** (DevTools Network → response headers → Set-Cookie) avant de plonger dans le client.

### 3. **Cookie tier dédié** > modif des cookies Supabase standards

Tentative de poser les cookies Supabase sur `.svlbh.com` casse Apple Sign-In (incident antérieur). Solution : **cookie séparé** opaque + endpoint d'échange. C'est plus de plumbing mais isole proprement les couches (le cookie Supabase reste géré par le SDK ; le cookie extension est un canal dédié).

### 4. **Sondage radiesthésique de Patrick** = filtre puissant

Sur les 16 options proposées par Famille (A à E), Patrick a sondé radiesthésiquement et écarté A4, A5 (partitionKey) ainsi que B12 (qui s'est avéré inutile a posteriori — les cookies n'étaient pas le souci). La Famille E qu'il a retenue était la bonne. **Mode d'emploi** : présenter une matrice large d'options structurée par famille, laisser Patrick filtrer, raffiner sur ce qui résonne.

### 5. **Aliases sans consumer = aliases ignorés**

`praticienne_user_alias` existait depuis 8 jours mais n'était lue par aucune fonction RLS. Le backfill avait été fait mais la **boucle de résolution** dans `auth_svlbh_id()` manquait. Pattern : toute table de remapping doit être consommée par les fonctions canoniques, sinon c'est de la déco.

---

## TODO résiduel

### Court terme (~1 semaine)

- [ ] **Auto-alias création Hide My Email Apple** — trigger `on_auth_user_created` qui détecte `email LIKE '%@privaterelay.appleid.com'`, lookup le provider_email réel dans aliases existants, auto-link au svlbh_id canonique
- [ ] **Propager `auth_svlbh_id()` via alias à toutes les autres fonctions RLS** — il en reste plusieurs qui consultent `praticienne_profile.supabase_user_id` directement (chercher pattern `supabase_user_id::text = (auth.uid())`)
- [ ] **Tester le cookie tier sur cockpit.svlbh.com et priv.svlbh.com** — actuellement seul pwa.app.svlbh.com pose le pair-code. Identique logique à mirror sur les 2 autres callbacks OAuth

### Moyen terme

- [ ] **Cleanup périodique** `extension_pairing_code` — supprimer rows `consumed_at IS NOT NULL OR expires_at < NOW() - INTERVAL '1 day'` via pg_cron
- [ ] **Documenter** dans CLAUDE.md SVLBH la doctrine : "un humain = 1 svlbh_id, N auth.users via praticienne_user_alias"
- [ ] **Migrer les autres extensions VLBH** (svlbh-hdom-extension, à venir) sur le pattern cookie tier pair-code

### Long terme

- [ ] Évaluer un **passage à NEXT_PUBLIC_COOKIE_DOMAIN=.svlbh.com** maintenant que le cookie tier est en place — Apple Sign-In loop a peut-être une cause différente résolvable, et un cookie partagé .svlbh.com simplifierait drastiquement le SSO. À tester en environnement de dev d'abord.

---

## Risques résiduels

| Risque | Sévérité | Mitigation |
|--------|----------|------------|
| Le cookie tier stocke access_token + refresh_token en clair dans `extension_pairing_code` pendant 5min | Faible | RLS strict + service_role only access ; window de 5min + consumed_at one-time minimise l'exposition |
| Apple Hide My Email peut créer un nouvel auth.user à chaque re-signin sans alias auto | Moyen | Trigger auto-alias TODO court terme ; en attendant, fallback `praticienne_profile.supabase_user_id` direct reste cohérent |
| Si plusieurs `auth.users` du même humain accèdent simultanément à pwa.app, race sur `extension_pairing_code` | Faible | Single-use + consumed_at gère la concurrence ; les rows ne sont jamais réutilisées |

---

## Références

- Mémoires créées :
  - `~/.claude/projects/-Users-patricktest/memory/project_bug_18_resolved.md`
  - `~/.claude/projects/-Users-patricktest/memory/project_sso_extension_pair_code.md`
  - `~/.claude/projects/-Users-patricktest/memory/project_doctrine_11_auth_uses_alias.md`
- Handoffs liés (svlbh-pro-web/docs/handoff/) :
  - `2026-05-15-apple-signin-cookie-conflict.md`
  - `2026-05-15-doctrine-multi-comptes-auth-users.md`
  - `2026-05-15-routine-nocturne-mtc.md`
- Commits :
  - svlbh-pro-web : `3199d08`, `d2dbbc1`, `240c91a`, `bc9d2eb`
  - vlbh-pathology-mapper : `f5fdcd4` (v0.2.11) → `895030b` (v0.2.19)
