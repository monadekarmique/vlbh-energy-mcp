# Snippet à intégrer dans vlbh-energy-mcp/CLAUDE.md

À ajouter sous une section type `## Make.com automation` ou `## Ops / Scenarios` :

---

### Scenario Make 9048144 · SVLBH Asana RTM-Bot

- **Statut** : actif depuis 2026-04-22 (réparé après 9 jours d'indisponibilité)
- **Webhook** : 4043084 (SVLBH PO Agent Webhook), URL via éditeur Make
- **Workspace cible Asana** : 1214033209540021
- **Connection** : SVLBH Make.com Bot (`__IMTCONN__: 14052590`)
- **3 actions** : `add_comment`, `create_task`, `update_task`

**Convention d'appel — champs requis par action** :
- `add_comment` : `action`, `task_gid` (non vide), `po_id`, `po_name`, `message`
- `create_task` : `action`, `project_gid` (non vide), `task_name` (non vide), `task_notes`
- `update_task` : `action`, `task_gid` (non vide), `task_notes`, `completed`

⚠️ Les filters du routeur rejettent silencieusement toute requête avec champ requis vide. Pas de retour erreur côté caller — la requête disparaît dans le vide. Vérifier les inputs avant POST.

**Postmortem** : `ops/postmortems/2026-04-22-fix-rtm-bot-9048144.md`
**Pattern technique réutilisable** : `.auto-memory/feedback_make_filter_required_for_optional_inputs.md`
