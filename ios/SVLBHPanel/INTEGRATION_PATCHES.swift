// ╔══════════════════════════════════════════════════════════════════════╗
// ║  PATCHES D'INTÉGRATION — À appliquer dans le projet Xcode existant  ║
// ╚══════════════════════════════════════════════════════════════════════╝

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 1 — SessionData.swift (ou SessionState.swift)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// AVANT (ligne existante):
//     var ratio4D: Double?
//
// REMPLACER PAR:
//     var ratio4D: Double?          // ← garder pour compat sérialisation
//     @Published var passeport = Passeport4DData()  // ← AJOUTER
//

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 2 — SVLBHTab.swift — Carte session
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// AVANT (dans la carte session, la colonne Ratio 4D):
//
//     VStack(spacing: 2) {
//         Text(session.ratio4D != nil
//              ? String(format: "%.1f×", session.ratio4D!)
//              : "—")
//             .font(.system(size: 18, weight: .bold, design: .rounded))
//             .foregroundStyle(ratioColor(session.ratio4D))
//         Text("Ratio 4D")
//             .font(.system(size: 9))
//             .foregroundStyle(.secondary)
//     }
//
// REMPLACER PAR:
//
//     Ratio4DCardSection(passeport: session.passeport)
//

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 3 — MakeSyncService.swift — fetchRatio4D → fetchPasseport4D
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// SUPPRIMER l'ancienne méthode fetchRatio4D() entière (lignes ~559-593)
// Le remplacement est dans MakeSyncService+Passeport.swift (extension)
//
// MODIFIER l'appel existant (si présent) :
//   AVANT:  await syncService.fetchRatio4D(patientId: ..., pays: ..., ...)
//   APRÈS:  await syncService.fetchPasseport4D(patientId: ..., pays: ...,
//               slsaHistorique: ..., dateTrauma: ...,
//               passeport: session.passeport)

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 4 — MakeSyncService.swift — Sérialisation push (buildPayload)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// AVANT (ligne existante):
//     if let r = s.ratio4D { lines.append("R4D:\(String(format: "%.2f", r))") }
//
// REMPLACER PAR:
//     if let p = s.passeport, let r = p.ratio4D {
//         let cluster = p.cluster ?? ""
//         let pays = p.paysOrigine ?? ""
//         let baseline = p.slsaChBaseline ?? 0
//         let sltdaO = p.sltdaOrigine ?? 0
//         let sltdaC = p.sltdaCh ?? 0
//         let hist = p.slsaHistorique ?? 0
//         let trauma = p.dateTrauma ?? ""
//         lines.append("R4D:\(String(format: "%.2f", r))|\(cluster)|\(pays)|\(baseline)|\(sltdaO)|\(sltdaC)|\(hist)|\(trauma)")
//     }

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 5 — MakeSyncService.swift — Parsing pull (applyPayload)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// AVANT (lignes existantes):
//     if line.hasPrefix("R4D:") {
//         if let val = Double(line.dropFirst(4)) {
//             session.ratio4D = val
//             log.append("📐 Ratio 4D: \(String(format: "%.2f", val))×")
//         }
//         continue
//     }
//
// REMPLACER PAR:
//     if line.hasPrefix("R4D:") {
//         let parts = String(line.dropFirst(4)).split(separator: "|", omittingEmptySubsequences: false).map(String.init)
//         if let val = Double(parts[0]) {
//             session.ratio4D = val
//             let p = session.passeport
//             p.ratio4D = val
//             if parts.count > 1 { p.cluster = parts[1] }
//             if parts.count > 2 { p.paysOrigine = parts[2] }
//             if parts.count > 3 { p.slsaChBaseline = Int(parts[3]) }
//             if parts.count > 4 { p.sltdaOrigine = Int(parts[4]) }
//             if parts.count > 5 { p.sltdaCh = Int(parts[5]) }
//             if parts.count > 6 { p.slsaHistorique = Int(parts[6]) }
//             if parts.count > 7 { p.dateTrauma = parts[7] }
//             log.append("📐 Ratio 4D: \(String(format: "%.2f", val))× [\(p.clusterDisplay)]")
//         }
//         continue
//     }

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PATCH 6 — Supprimer la fonction ratioColor() de SVLBHTab.swift
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Si une fonction helper ratioColor() existe dans SVLBHTab, elle peut
// être supprimée car la couleur vient maintenant de passeport.ratioColor

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// FICHIERS À AJOUTER AU PROJET XCODE (drag & drop dans le navigator):
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// 1. Passeport4DData.swift          ← modèle de données
// 2. Ratio4DCardSection.swift       ← widget carte session
// 3. Ratio4DDetailView.swift        ← sheet détail avec table 21S
// 4. MakeSyncService+Passeport.swift ← extension réseau
//
// Puis appliquer les 6 patches ci-dessus dans les fichiers existants.
