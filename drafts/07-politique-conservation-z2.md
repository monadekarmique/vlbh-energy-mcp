# Draft 07 — Politique de conservation des données Zone 2

**Version** : 0.1
**Date** : 2026-04-17
**Statut** : Draft pour revue juridique + décision PB
**Parent** : `data-model-vlbh.md` v0.2 — question ouverte n°7
**Périmètre** : Zone 2 — étudiantes en formation 15 mois, tous shards (CH/EU/CA)

---

## Changelog

| Version | Date | Changements |
|---|---|---|
| 0.1 | 2026-04-17 | Draft initial — durées par type de donnée, mécanismes d'effacement et d'anonymisation |

---

## 1. Cadre juridique

### 1.1 Principe de minimisation de la conservation

- **RGPD art. 5.1.e** : « conservées sous une forme permettant l'identification des personnes concernées pendant une durée n'excédant pas celle nécessaire au regard des finalités pour lesquelles elles sont traitées »
- **nLPD art. 6.4** : équivalent suisse, avec obligation de déterminer une durée précise

### 1.2 Obligations de conservation par nature

| Catégorie | Durée minimale imposée | Source |
|---|---|---|
| Documents comptables et factures | 10 ans | CO art. 958f (Suisse), LPF (France), obligations fiscales provinciales (Canada) |
| Contrats de formation | Durée du contrat + prescription | Droit civil contractuel général |
| Données de santé (Z3) | 10 ans après fin du traitement | LPMéd Suisse, usages RGPD |
| Registre des ancêtres (Z2) | Pas d'obligation (défunts hors scope) | Considérant 27 RGPD |

### 1.3 Droit à l'effacement

- **RGPD art. 17** : la personne peut demander l'effacement sous les conditions de l'article
- **nLPD art. 32** : droit à la destruction
- **Loi 25 Québec art. 28** : droit à la cessation de diffusion et à la désindexation
- Exceptions : obligations légales de conservation (comptabilité), intérêts publics, défense de droits en justice

---

## 2. Matrice de conservation par table Zone 2

| Table | Durée active | Archive (cold) | Anonymisation | Purge |
|---|---|---|---|---|
| `student_profile` | Pendant formation + 2 ans | 2 à 10 ans post-formation | An 10 | An 10 (identité) |
| `ancestors_registry` | Indéfinie | — | Non applicable (défunts) | Sur demande étudiante pour SA lignée seulement |
| `vibrational_signatures` | Pendant formation + 2 ans | 2 à 10 ans post-formation | An 10 (lien student délié) | — |
| `billing_student` | 10 ans post-transaction | Au-delà si audit fiscal | Non (obligation comptable) | An 15 (après prescription fiscale) |
| `contract_formation` (signatures, consentements) | 10 ans post-fin de contrat | Au-delà si litige | Non | An 15 |

### 2.1 Justification de la durée 10 ans post-formation

Proposition retenue : **10 ans après la fin de formation** pour `student_profile` et données liées. Raisons :

- Alignement avec la durée fiscale suisse (CO art. 958f) pour la partie billing
- Délai de prescription de la responsabilité contractuelle (10 ans, art. 127 CO)
- Permet de répondre à une éventuelle plainte ou recours de l'ancienne étudiante pendant ce délai
- Pas de donnée sensible → pas d'argument pour une durée plus courte imposée

### 2.2 Cas particulier du `ancestors_registry`

Les données du registre des ancêtres portent sur des défunts (hors RGPD/nLPD). Elles n'ont donc pas de durée de conservation imposée par ces règlements.

**Toutefois** :
- L'étudiante peut demander la suppression du registre de SA lignée (considérant éthique, même sans obligation juridique)
- Les données peuvent être conservées à des fins statistiques anonymisées (agrégats sur les patterns transgénérationnels, sans identifier la descendante)

---

## 3. Cycle de vie d'un dossier étudiante

```
Année 0        : Entrée Z2 (séance découverte CHF 59) → création student_profile
Année 0 à 1.25 : Formation 15 mois → enrichissement continu
Année 1.25     : Fin de formation → passage en archive active (2 ans)
Année 3.25     : Basculement en cold storage (compressé, accès sur demande)
Année 11.25    : Anonymisation :
                 - Suppression de civil_identity
                 - Suppression de contract_signed_at (identité)
                 - Dissociation du svlbh_id dans vibrational_signatures
                 - Conservation statistique des patterns VLBH (anonyme)
Année 11.25    : Purge complète de billing_student (si aucun litige pendant)
```

**Option** : si l'étudiante devient praticienne certifiée (passage Z2 → Z3), son `student_profile` est conservé comme partie de son historique professionnel tant qu'elle exerce + 10 ans post-cessation.

---

## 4. Mécanismes techniques

### 4.1 Marquage automatique

Chaque table contient une colonne `retention_deadline` calculée automatiquement à l'insertion :
- `student_profile.retention_deadline = formation_end_date + 10 years`
- `billing_student.retention_deadline = paid_at + 10 years`

### 4.2 Jobs programmés

- **Quotidien** : job `check_archive_candidates` — identifie les records dont la `retention_deadline` approche (90 jours) et notifie l'équipe compliance
- **Mensuel** : job `move_to_cold_storage` — déplace les records `active + 2y` vers le schéma `archive_*`
- **Annuel** : job `anonymize_expired` — applique l'anonymisation aux records au-delà de leur `retention_deadline`
- **Annuel** : job `purge_billing_expired` — supprime les records `billing_student` > 15 ans

### 4.3 Anonymisation — définition opérationnelle

Une donnée est considérée anonymisée lorsque :
- Aucun champ direct n'identifie la personne (nom, email, téléphone, adresse, WhatsApp ID)
- Aucun quasi-identifiant ne permet une ré-identification avec des données auxiliaires raisonnablement accessibles
- Le SVLBH_Identifier est lui-même remplacé par un identifiant statistique non réversible (pas de mapping conservé)
- Les données vibratoires résiduelles peuvent rester, rattachées à cet identifiant statistique

Cela correspond au standard **« qualified anonymization »** requis par la Loi 25 du Québec — qui est le standard le plus strict applicable dans notre périmètre — et que nous appliquons uniformément par simplicité.

### 4.4 Audit log

Toute opération de cycle de vie (archive, anonymisation, purge) est loggée dans une table `retention_audit` immuable :
- timestamp
- action (archive, anonymize, purge)
- scope (table, record_count)
- operator (job_name ou user)
- justification (retention_policy ou demande utilisatrice)

Cette table est conservée sans limite (preuve de conformité).

---

## 5. Droit à l'effacement — processus opérationnel

### 5.1 Canal de réception

- Formulaire dédié dans l'espace étudiante
- Email à privacy@vlbh.energy
- Demande orale en séance (à consigner par écrit par vlbh)

### 5.2 Délai de traitement

- 30 jours maximum (RGPD art. 12.3), prolongeable à 90 jours pour demande complexe
- Confirmation de réception sous 7 jours
- Exécution et confirmation d'exécution sous 30 jours

### 5.3 Portée de l'effacement

Sur demande d'effacement, sont supprimés :
- `student_profile` : civil_identity, contact, progression
- `vibrational_signatures` : rattachement svlbh_id supprimé (signatures conservées en anonyme si valeur statistique)
- Demande de l'étudiante sur `ancestors_registry` : suppression ou conservation anonyme au choix

Sont **conservés** en justifiant auprès de l'étudiante :
- `billing_student` : obligation fiscale 10 ans
- `contract_formation` : preuve contractuelle 10 ans
- `retention_audit` : preuve de conformité

### 5.4 Lettre-type de réponse

Template à produire en Annexe du présent document (v0.2).

---

## 6. Cas spécifiques par shard régional

### 6.1 Shard CH
Durées alignées sur obligations suisses (CO 958f, LPMéd). Pas de spécificité supplémentaire.

### 6.2 Shard EU
Ajouter les obligations nationales éventuelles (France : prescription pénale spécifique ; Allemagne : Abgabenordnung §147 — 6 ans pour correspondance commerciale, 10 ans pour documents comptables, similaire CH). Les 10 ans proposés couvrent largement.

### 6.3 Shard CA — traitement particulier Québec (Loi 25)

- **Droit à la portabilité** (entré en vigueur septembre 2024) : fournir un export structuré sur demande
- **Anonymisation qualifiée** : standard strict, déjà appliqué uniformément (§4.3)
- **DPO désigné obligatoire** (art. 3.1)
- **Délai de notification de violation** : sans délai excessif (art. 3.5), plus strict que RGPD

---

## 7. Décisions à valider

- **Durée 10 ans post-formation** : confirmée ou à ajuster ? Option alternative : 5 ans (suffisant pour obligation contractuelle si le formation n'est pas considéré comme professionnel réglementé).
- **Conservation du registre des ancêtres** : indéfinie par défaut, ou durée bornée même si défunts ?
- **Statistiques anonymes post-purge** : conservées ou détruites aussi ?
- **Processus de re-consent** pour les étudiantes actuelles qui n'ont pas signé selon la nouvelle politique : à cadrer en lien avec Draft 09 (rétroactivité).

---

## 8. Annexes prévues

- **Annexe A** — Lettre-type de réponse à une demande d'effacement
- **Annexe B** — Script SQL des jobs d'archivage/anonymisation/purge
- **Annexe C** — Extrait de la politique à communiquer aux étudiantes (clause contrat + page publique vlbh.energy/vie-privee)
