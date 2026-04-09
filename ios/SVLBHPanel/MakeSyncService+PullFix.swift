import Foundation

// ╔══════════════════════════════════════════════════════════════════════╗
// ║  FIX: Pull uniquement la source sélectionnée, pas toutes           ║
// ╚══════════════════════════════════════════════════════════════════════╝
//
// BUG: L'app envoie des pulls pour TOUTES les sources en parallèle
// (0300, 0301, 0302, 0303, 455000, 01, 21, 22, 103...).
// Résultat: un vieux record non-READ d'une autre source est retourné
// et "écrase" le soin attendu.
//
// FIX: Ne construire qu'UNE SEULE clé basée sur la source sélectionnée.

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// DANS MakeSyncService.swift — Chercher la méthode de pull
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// AVANT (code approximatif — chercher la boucle qui itère les sources):
//
//     // Pull from all sources
//     let allSources = [
//         pullSource.code,     // source sélectionnée
//         "455000",            // Patrick
//         "0300", "0301", "0302", "0303",  // shamanes
//         "01", "21", "22", "103"          // autres
//     ]
//     for code in allSources {
//         let key = "\(prefix)-\(patientId)-\(sessionNum)-\(code)"
//         // ... envoie requête pull ...
//     }
//
// REMPLACER PAR:
//
//     // Pull ONLY from selected source
//     let selectedCode = pullSource.code  // ex: "0303" pour Chloé
//     let prefix = session.isResearchProject ? "01" : "00"
//     let key = "\(prefix)-\(patientId)-\(sessionNum)-\(selectedCode)"
//     // ... envoie UNE SEULE requête pull ...

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ALTERNATIVE: Si on veut garder le pull multi-source mais filtrer
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Si le multi-pull est voulu (pour merger les suggestions de plusieurs
// shamanes), alors il faut au minimum:
//
// 1. Filtrer par le MÊME préfixe (00 ou 01):
//
//     let prefix = session.isResearchProject ? "01" : "00"
//     // Ne jamais mélanger 00 et 01
//
// 2. Et/ou ne retourner que le résultat de la source sélectionnée
//    comme résultat PRINCIPAL, les autres comme suggestions secondaires:
//
//     var primaryResult: String?
//     var suggestions: [String] = []
//     for (code, payload) in results {
//         if payload == "READ" { continue }
//         if code == selectedCode {
//             primaryResult = payload  // ← celui qu'on affiche
//         } else {
//             suggestions.append(payload)
//         }
//     }

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// STRUCTURE DES CLÉS — Référence
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Format: {prefix}-{patientId}-{sessionNum}-{sourceCode}
//
// Préfixes:
//   00 = Soin (traitement)
//   01 = Projet de recherche
//
// Codes source (shamanes certifiées):
//   0300 = Cornelia Althaus
//   0301 = Flavia Carriero
//   0302 = Anne Grangier Bays
//   0303 = Chloé P.Bays
//   455000 = Patrick (praticien/superviseur)
//
// Exemples:
//   00-12-001-0303 → Soin patient 12, session 1, par Chloé
//   01-12-001-0300 → Recherche patient 12, session 1, par Cornelia
