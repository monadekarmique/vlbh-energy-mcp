# Patches skills locaux — Grooming 2026-04-21 S3 J2

**Contexte** : grooming Asana + nettoyage Notion-as-SSOT demandé par Patrick le 2026-04-21 05h34.
Les fichiers SKILL.md ciblés sont dans `~/.claude/skills/` (hors workspace de l'agent), donc à appliquer manuellement.

---

## Patch 1 — `~/.claude/skills/po-08-data-quality/SKILL.md`

### Ligne 3 (frontmatter description)

```diff
-description: PO-08 Data Quality — audit quotidien des datastores Make.com (billing_praticien + svlbh-v2), détection anomalies, dual-write Notion+Asana, matrice L1/L2/L3 pour auto-correction
+description: PO-08 Data Quality — audit quotidien des datastores Make.com (billing_praticien + svlbh-v2), détection anomalies, log Asana PO-10 RTM (SSOT) + miroir Notion optionnel, matrice L1/L2/L3 pour auto-correction
```

### Lignes 10-11 (§Mandat)

```diff
 ## Mandat
-Auditer quotidiennement les datastores Make.com pour détecter les anomalies de données, appliquer les fixes auto-corrigeables (matrice L1/L2/L3), dual-écrire les traces dans Notion PO-01 + Asana PO-10 RTM.
+Auditer quotidiennement les datastores Make.com pour détecter les anomalies de données, appliquer les fixes auto-corrigeables (matrice L1/L2/L3), tracer dans Asana PO-10 RTM (canonical SSOT). Miroir Notion PO-01 OPTIONNEL pour visibilité Claude.ai web — jamais source d'analyse.
```

### Lignes 62-68 (§Actions de reporting (a))

```diff
-### (a) Bug Notion PO-01 (staging data)
+### (a) Bug Notion PO-01 (OPTIONNEL — miroir lecture pour Claude.ai web)
 - data_source_id: `428e4168-7013-4cdd-9cc0-d1cff31cad5f`
 - Properties : Type=Bug, Priority=P2, Status=Pas commencé, Sprint=S1, Platform=iOS, VLBH Module=hDOM, GAFA Exposure=Zone fermee, RGPD Impact=Faible
 - ATTENTION : utiliser "Zone fermee" (sans accent) pour GAFA Exposure.
 - Contenu : anomalies + fixes appliqués + L3 ouverts.
+- N'EST PAS la source de vérité — primary write reste §(b) Asana PO-10 RTM.

-### (b) Tâche Asana PO-10 RTM (action tracker)
+### (b) Tâche Asana PO-10 RTM (action tracker — CANONICAL SSOT)
```

---

## Patch 2 — `~/.claude/skills/po-11-onboarding-testers/SKILL.md`

### Ligne 6 (introduction)

```diff
-Tu es PO-11 Onboarding/Pipeline du Release Train SVLBH. Tu travailles de manière autonome, sans intervention humaine.
+Tu es la facette thématique PO-11 Onboarding/Pipeline du Release Train SVLBH — miroir de Patrick sur la cohérence pipeline (cf. v0.8 méta-principe : pas un agent autonome, un miroir thématique).
```

---

## Application

Soit Patrick applique manuellement (copier/coller dans VSCode/équivalent), soit via bash :

```bash
# Patch 1
sed -i '' 's|dual-write Notion+Asana|log Asana PO-10 RTM (SSOT) + miroir Notion optionnel|g' \
  ~/.claude/skills/po-08-data-quality/SKILL.md
sed -i '' 's|dual-écrire les traces dans Notion PO-01 + Asana PO-10 RTM|tracer dans Asana PO-10 RTM (canonical SSOT). Miroir Notion PO-01 OPTIONNEL pour visibilité Claude.ai web — jamais source d'\''analyse|g' \
  ~/.claude/skills/po-08-data-quality/SKILL.md
sed -i '' 's|### (a) Bug Notion PO-01 (staging data)|### (a) Bug Notion PO-01 (OPTIONNEL — miroir lecture pour Claude.ai web)|g' \
  ~/.claude/skills/po-08-data-quality/SKILL.md

# Patch 2
sed -i '' 's|Tu es PO-11 Onboarding/Pipeline du Release Train SVLBH. Tu travailles de manière autonome, sans intervention humaine.|Tu es la facette thématique PO-11 Onboarding/Pipeline du Release Train SVLBH — miroir de Patrick sur la cohérence pipeline (cf. v0.8 méta-principe : pas un agent autonome, un miroir thématique).|g' \
  ~/.claude/skills/po-11-onboarding-testers/SKILL.md
```
