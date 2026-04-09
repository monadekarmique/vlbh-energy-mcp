import SwiftUI

// MARK: - Énergie Féminine Section
//
// Affiche dans la vue Routine du Matin :
//   Énergie féminine
//   Capacité : {compteur_max_total} (somme des compteur_max_patient des certifiées)
//   Couverture : {compteur_total / compteur_max_total}% (compteur / max des certifiées)
//
// Données source : datastore billing_praticien #156396
// Filtre : role == "certifiee" && statut == "active"

struct EnergieFeminineSection: View {
    let certifiees: [CertifieeBilling]

    private var maxTotal: Int {
        certifiees.reduce(0) { $0 + $1.compteurMax }
    }

    private var compteurTotal: Int {
        certifiees.reduce(0) { $0 + $1.compteur }
    }

    private var couverture: Double {
        guard maxTotal > 0 else { return 0 }
        return Double(compteurTotal) / Double(maxTotal) * 100
    }

    private var couvertureColor: Color {
        if couverture >= 70 { return .green }
        if couverture >= 40 { return .orange }
        return .red
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\u{00c9}nergie f\u{00e9}minine")
                .font(.headline)

            HStack {
                Text("Capacit\u{00e9}")
                    .foregroundStyle(.secondary)
                Spacer()
                Text(formatNumber(maxTotal))
                    .fontWeight(.semibold)
            }

            HStack {
                Text("Couverture")
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(formatNumber(compteurTotal)) / \(formatNumber(maxTotal))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(String(format: "%.1f%%", couverture))
                    .fontWeight(.bold)
                    .foregroundStyle(couvertureColor)
            }

            // Progress bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color(.tertiarySystemFill))
                        .frame(height: 8)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(couvertureColor)
                        .frame(width: geo.size.width * min(couverture / 100, 1.0), height: 8)
                }
            }
            .frame(height: 8)

            // Per-shamane breakdown
            ForEach(certifiees) { c in
                HStack {
                    Text("\(c.emoji) \(c.nom)")
                        .font(.caption)
                    Spacer()
                    Text("\(formatNumber(c.compteur)) / \(formatNumber(c.compteurMax))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    private func formatNumber(_ n: Int) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.groupingSeparator = "\u{2019}"
        return formatter.string(from: NSNumber(value: n)) ?? "\(n)"
    }
}

// MARK: - Model

struct CertifieeBilling: Identifiable {
    let code: String
    let nom: String
    let compteurMax: Int
    let compteur: Int

    var id: String { code }

    var emoji: String {
        switch code {
        case "0300": return "\u{1F431}"
        case "0301": return "\u{2728}"
        case "0302": return "\u{1F338}"
        case "0303": return "\u{1F4AB}"
        default: return "\u{1F469}"
        }
    }
}

// MARK: - Parser for billing_praticien pull
//
// Le datastore billing_praticien est pullé via l'app.
// Pour construire les CertifieeBilling depuis les données locales :
//
//   let certifiees = [
//       CertifieeBilling(code: "0300", nom: "Cornelia", compteurMax: 3545, compteur: 794),
//       CertifieeBilling(code: "0301", nom: "Flavia", compteurMax: 14285, compteur: 13545),
//       CertifieeBilling(code: "0302", nom: "Anne", compteurMax: 547, compteur: 383),
//       CertifieeBilling(code: "0303", nom: "Chloé", compteurMax: 15299, compteur: 581),
//   ]
//
//   EnergieFeminineSection(certifiees: certifiees)
