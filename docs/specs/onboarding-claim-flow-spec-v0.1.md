# Onboarding « claim flow » — spec v0.1 (2026-07-24)

> Objectif : supprimer le casse-tête de l'onboarding Apple. Aujourd'hui tout le
> rattachement identité → dossier dépend du fait qu'Apple envoie un **vrai e-mail
> qui matche** `praticienne_profile.email`. Hide My Email, e-mail Apple ≠ e-mail du
> dossier, ou méthodes mélangées entre appareils → **orphelin muet** + aliasage
> manuel. `auto_link_alias()` l'admet dans son propre code : *« Apple Hide My Email :
> pas d'email réel → lien explicite requis. »*

## Principe : inverser la dépendance

On arrête de dépendre de l'e-mail Apple. On ancre le lien sur un **canal qu'on possède
déjà** (WhatsApp z4 / e-mail sur fiche). La personne prouve qu'elle contrôle ce canal,
et on **aliase automatiquement la session Apple courante** (par `user_id`) vers son
`svlbh_id`. Hide My Email devient sans effet ; le multi-appareils s'auto-répare.

## Déclencheur

L'app détecte un orphelin : après login, `auth_svlbh_id()` renvoie `NULL`
(aucun alias pour ce `supabase_user_id`, aucun match e-mail). Au lieu du cul-de-sac
« coquille vide », l'app ouvre l'écran **« Confirme ton identité »**.

## Flux (2 appels)

```
[App orpheline]                         [Backend /claim]                 [Canal connu]
   |  POST /claim/request                    |                                |
   |  Bearer <session Apple orpheline>       |                                |
   |  { identifier: "yvette.dayer@bluewin" } |                                |
   |---------------------------------------->|  1. vérifie la session (user_id, provider)
   |                                         |  2. refuse si déjà résolue (auth_svlbh_id != null)
   |                                         |  3. trouve la fiche par identifier (email/mobile)
   |                                         |  4. code 6 chiffres, stocké HASHÉ, TTL 10 min
   |                                         |  5. envoie le code sur le canal SUR FICHE ------>|  (WhatsApp z4
   |<-- { challenge_id, channel, hint } -----|     (pas ce que l'utilisateur a tapé)           |   ou e-mail Resend)
   |                                         |                                |
   |  POST /claim/confirm                    |                                |
   |  Bearer <même session>                  |                                |
   |  { challenge_id, code: "418302" }       |                                |
   |---------------------------------------->|  6. vérifie code (hash, TTL, tentatives)
   |                                         |  7. admin_link_praticienne_alias(svlbh_id, user_id)
   |<-- { linked: true, svlbh_id } ----------|  8. challenge consommé
   |                                         |
   [ auth_svlbh_id() résout désormais → RLS débloqué, ses données chargent ]
```

## Garanties de sécurité

- **Preuve de possession du canal SUR FICHE** — le code part vers l'e-mail/WhatsApp
  déjà enregistré, jamais vers ce que l'utilisateur tape (l'`identifier` sert seulement
  à retrouver la fiche). Anti-usurpation.
- **Lié à la session courante** — on ne peut revendiquer que dans une identité qu'on
  contrôle réellement sur l'appareil (`claimant_user_id` = `auth.uid` du token présenté).
- **Refus si déjà résolue** — une session déjà rattachée ne peut pas en revendiquer une autre.
- **Code hashé (SHA-256), TTL 10 min, single-use, max 5 tentatives.**
- **Idempotent** — `admin_link_praticienne_alias` garde le `NOT EXISTS` (doctrine #11,
  pas de contrainte unique sur la table alias).

## Ce que ça règle

| Cas cassé aujourd'hui | Après |
|---|---|
| Hide My Email → orphelin | revendication guidée → aliasé auto |
| e-mail Apple ≠ e-mail fiche | idem (on ne dépend plus de l'e-mail Apple) |
| 2e appareil / autre méthode | chaque nouvelle identité s'auto-revendique au 1er usage |
| échec silencieux + INSERT manuel | self-service, zéro intervention DB |

## Points hors-scope v0.1 (à durcir avant prod)

- Rate-limiting par IP/identifier + anti-énumération (aligner sur le pattern `magic-link`
  qui ne révèle pas l'existence).
- Choix consultante vs praticienne (v0.1 = praticienne, cf. `auth_svlbh_id`). Ajouter
  un `admin_link_consultante_alias` symétrique si besoin côté portail consultante.
- i18n des messages, tests, journalisation `api_trace`.
- Envoi WhatsApp : passe par `z4-bridge.svlbh.com` (CF Access) — secrets en env Render.

## Reste séparé : le défaut d'auth-bypass

Indépendant de ce flux : `AuthState.init()` (Priv-1) fait confiance à une session du
keychain partagé `svlbh-shared` **sans la revalider ni vérifier l'identité**, en
court-circuitant `LoginView`. À corriger à part (valider la session serveur + lier
l'identité attendue avant `isAuthenticated = true`).
