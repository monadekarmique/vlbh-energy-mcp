import SwiftUI

// MARK: - Ratio 4D Detail View (sheet)

struct Ratio4DDetailView: View {
    @ObservedObject var passeport: Passeport4DData
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // ── Header: Ratio + Cluster ──
                    ratioHeader

                    // ── Patient reference card ──
                    patientCard

                    // ── 21S Reference Table ──
                    referenceTable

                    // ── Explanation ──
                    explanationCard
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Passeport SVLBH")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Fermer") { dismiss() }
                }
            }
        }
    }

    // MARK: - Ratio Header

    private var ratioHeader: some View {
        VStack(spacing: 6) {
            Text(passeport.clusterDisplay)
                .font(.caption)
                .fontWeight(.semibold)
                .textCase(.uppercase)
                .foregroundStyle(passeport.ratioColor)

            Text(String(format: "%.2f\u{00d7}", passeport.ratio4D ?? 0))
                .font(.system(size: 56, weight: .bold, design: .rounded))
                .foregroundStyle(passeport.ratioColor)

            Text("Ratio 4D")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Patient Card

    private var patientCard: some View {
        VStack(spacing: 0) {
            sectionHeader("Fiche patient")

            row("Pays d'origine", passeport.paysOrigine ?? "—")
            Divider().padding(.leading)
            row("Date du trauma", passeport.dateTrauma ?? "—")
            Divider().padding(.leading)
            row("SLSA historique", "\(passeport.slsaHistorique ?? 0)%")
            Divider().padding(.leading)
            row("SLSA_CH baseline 21S", "\(passeport.slsaChBaseline ?? 0)%")
            Divider().padding(.leading)
            row("SLTdA origine", "\(passeport.sltdaOrigine ?? 0)%")
            Divider().padding(.leading)
            row("SLTdA CH", "\(passeport.sltdaCh ?? 0)%")
            Divider().padding(.leading)
            row("Ratio 4D", String(format: "%.2f\u{00d7}", passeport.ratio4D ?? 0),
                valueColor: passeport.ratioColor)
        }
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - 21S Reference Table

    private static let ref21S: [(pays: String, slsaCh: Int, sltdaOrig: Int, sltdaCh: Int)] = [
        ("Iran",            9176, 1,  78),
        ("Ukraine",         1922, 3,  49),
        ("Pologne",         1118, 2,  19),
        ("USA",              857, 7,  45),
        ("Kosovo",           465, 45, 178),
        ("C\u{00f4}te d'Ivoire", 424, 5,  18),
        ("Cambodge",         314, 48, 128),
        ("England",          216, 43, 79),
        ("France",           196, 15, 25),
        ("Serbie",           180, 19, 29),
        ("Suisse",           136, 85, 98),
        ("Espagne",          133, 15, 17),
        ("Su\u{00e8}de",     128, 89, 97),
        ("Alg\u{00e9}rie",   96,  48, 39),
        ("UK",                86,  74, 54),
        ("Allemagne",         55,  75, 35),
        ("Italie",            50,  28, 12),
        ("Turquie",           50,  45, 19),
        ("S\u{00e9}n\u{00e9}gal", 42, 39, 14),
        ("Portugal",          37,  45, 14),
        ("Tibet",             18,  94, 14),
    ]

    private var referenceTable: some View {
        VStack(spacing: 0) {
            sectionHeader("Table de r\u{00e9}f\u{00e9}rence 21\u{1D49}")

            // Column headers
            HStack {
                Text("Pays").font(.caption2).fontWeight(.semibold).frame(width: 100, alignment: .leading)
                Text("SLSA_CH").font(.caption2).fontWeight(.semibold).frame(width: 65, alignment: .trailing)
                Text("SLTdA\u{2080}").font(.caption2).fontWeight(.semibold).frame(width: 55, alignment: .trailing)
                Text("SLTdA\u{1d9c}\u{2095}").font(.caption2).fontWeight(.semibold).frame(width: 55, alignment: .trailing)
            }
            .padding(.horizontal).padding(.vertical, 6)
            .background(Color(.tertiarySystemGroupedBackground))

            ForEach(Self.ref21S, id: \.pays) { entry in
                let isPatient = entry.pays.lowercased() == (passeport.paysOrigine ?? "").lowercased()
                HStack {
                    Text(entry.pays)
                        .font(.caption).frame(width: 100, alignment: .leading)
                        .fontWeight(isPatient ? .bold : .regular)
                    Text("\(entry.slsaCh)%")
                        .font(.caption).frame(width: 65, alignment: .trailing)
                    Text("\(entry.sltdaOrig)%")
                        .font(.caption).frame(width: 55, alignment: .trailing)
                    Text("\(entry.sltdaCh)%")
                        .font(.caption).frame(width: 55, alignment: .trailing)
                }
                .padding(.horizontal).padding(.vertical, 4)
                .background(isPatient ? passeport.ratioColor.opacity(0.12) : Color.clear)

                if entry.pays != Self.ref21S.last?.pays {
                    Divider().padding(.leading)
                }
            }
        }
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Explanation

    private var explanationCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Qu'est-ce que le Ratio 4D ?")

            Text("""
            Le Ratio 4D mesure le poids \u{00e9}nerg\u{00e9}tique port\u{00e9} par le patient \
            par rapport au baseline de son pays d'origine au 21\u{00e8}me si\u{00e8}cle.

            \u{2022} **Formule** : SLSA historique \u{00f7} SLSA_CH baseline du pays
            \u{2022} **1\u{00d7}** = le patient porte exactement le poids de r\u{00e9}f\u{00e9}rence
            \u{2022} **> 10\u{00d7}** = surcharge \u{00e9}nerg\u{00e9}tique majeure

            **Clusters :**
            \u{2022} **Compression** (SLSA_CH < 128%) \u{2014} \u{00e9}nergie contenue
            \u{2022} **Sensibilit\u{00e9} active** (128\u{2013}800%) \u{2014} r\u{00e9}activit\u{00e9} \u{00e9}lev\u{00e9}e
            \u{2022} **Hypersensibilit\u{00e9} extr\u{00ea}me** (> 800%) \u{2014} terrain tr\u{00e8}s charg\u{00e9}
            """)
            .font(.caption)
            .foregroundStyle(.secondary)
            .padding(.horizontal)
            .padding(.bottom, 12)
        }
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.footnote)
            .fontWeight(.semibold)
            .foregroundStyle(.secondary)
            .textCase(.uppercase)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal).padding(.top, 12).padding(.bottom, 4)
    }

    private func row(_ label: String, _ value: String, valueColor: Color = .primary) -> some View {
        HStack {
            Text(label).font(.subheadline).foregroundStyle(.secondary)
            Spacer()
            Text(value).font(.subheadline).fontWeight(.medium).foregroundStyle(valueColor)
        }
        .padding(.horizontal).padding(.vertical, 8)
    }
}
