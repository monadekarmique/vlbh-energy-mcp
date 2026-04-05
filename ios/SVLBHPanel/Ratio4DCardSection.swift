import SwiftUI

// MARK: - Ratio 4D Card Section (to embed in SVLBHTab session card)
//
// Usage in SVLBHTab.swift:
//   Replace the static ratio text with:
//     Ratio4DCardSection(passeport: session.passeport)
//
// The session card layout becomes:
//   [Patient | Ratio4DCardSection | Tier | Niveau]

struct Ratio4DCardSection: View {
    @ObservedObject var passeport: Passeport4DData
    @State private var showDetail = false

    var body: some View {
        Button { showDetail = true } label: {
            VStack(spacing: 2) {
                // Cluster label above
                if let cluster = passeport.cluster, !cluster.isEmpty {
                    Text(passeport.clusterDisplay)
                        .font(.system(size: 8, weight: .semibold))
                        .textCase(.uppercase)
                        .foregroundStyle(passeport.ratioColor.opacity(0.8))
                        .lineLimit(1)
                        .minimumScaleFactor(0.7)
                }

                // Ratio value
                if let ratio = passeport.ratio4D {
                    Text(String(format: "%.2f\u{00d7}", ratio))
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundStyle(passeport.ratioColor)
                } else {
                    Text("—")
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundStyle(.secondary)
                }

                // Label
                Text("Ratio 4D")
                    .font(.system(size: 9))
                    .foregroundStyle(.secondary)
            }
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $showDetail) {
            Ratio4DDetailView(passeport: passeport)
        }
    }
}
