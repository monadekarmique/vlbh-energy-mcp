# Architecture Decision Records — iTherapeut 6.0

## ADR-001: Supabase comme DB relationnelle (pas Make.com seul)

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Contexte**: Make.com datastore 155674 gere les syncs VLBH temps reel mais n'est pas relationnel.
**Decision**: Supabase PostgreSQL pour patients/factures/sessions. Make.com reste pour les syncs SLM/SLA/Tore.
**Raison**: Row Level Security, relations FK, requetes complexes, auth integree, free tier 50k rows.

## ADR-002: React web (pas React Native) pour le sprint 5 jours

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**: App web React + Tailwind + shadcn. Wrapper Capacitor pour mobile plus tard.
**Raison**: 2x plus rapide, fonctionne sur iPad via Safari, PWA installable.

## ADR-003: PostFinance Checkout (pas Stripe)

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**: PostFinance Checkout pour abonnements 59/179 CHF.
**Raison**: 100% suisse, SDK Python officiel (postfinancecheckout), Twint integre.
**Config**: space_id + user_id + secret_key.

## ADR-004: 2 plans — Therapeute 59 / Cabinet Pro 179
**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**:
- Plan Therapeute (59 CHF/mois): gestion cabinet + Scores de Lumiere + Rose des Vents + modeles Pydantic (SLM, Leads, Sessions, Tores base, Sclerose, Glycemie) + assistant IA Claude
- Plan Cabinet Pro (179 CHF/mois): + agenda Google Cal + WhatsApp + Twint + pipeline Lead->Billing + Tore Couplages avances + Chromotherapie
**Raison**: La valeur therapeutique VLBH est dans le plan de base pour attirer les therapeutes. Le premium = automatisation business.

## ADR-005: Coexistence API — ne pas casser l'existant

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**: Les 6 routers existants (slm, sla, session, lead, tore, billing) ne sont PAS modifies. Les nouveaux routers (patients, invoices, qrbill) s'ajoutent a cote.
**Raison**: L'app iOS SVLBHPanel utilise les endpoints existants. Casser = casser la prod.
**Regle**: Tout nouveau code va dans de NOUVEAUX fichiers (models/patient.py, routers/patient.py, etc.)

## ADR-006: Hebergement Suisse obligatoire (nLPD)

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**: Supabase region eu-central + Render.com (deja en place). Migration vers Infomaniak/Exoscale si necessaire.
**Raison**: nLPD (loi suisse protection donnees) exige hebergement adequat pour donnees de sante.

## ADR-007: QR-facture SIX v2.4 + Tarif 590

**Date**: 2026-04-08
**Statut**: ACCEPTE
**Decision**: Librairie Python `qrbill` pour QR-facture. ReportLab pour Tarif 590 PDF.
**Contraintes**: Adresses structurees uniquement (depuis nov 2025). XML 5.0 obligatoire juillet 2027.
