import SwiftUI

// MARK: - Shamanes Overview View

struct ShamanePending: Codable, Identifiable {
    let code: String
    let name: String
    let soins: Int
    let recherche: Int
    let total: Int
    let records: [String]

    var id: String { code }

    var emoji: String {
        switch code {
        case "0300": return "🐱"   // Cornelia
        case "0301": return "✨"   // Flavia
        case "0302": return "🌸"   // Anne
        case "0303": return "💫"   // Chloé
        case "455000": return "🔬" // Patrick
        default: return "👤"
        }
    }

    var badgeColor: Color {
        if total == 0 { return .green }
        if total <= 3 { return .orange }
        return .red
    }
}

struct ShamanesPendingResponse: Codable {
    let shamanes: [ShamanePending]
    let total_soins: Int
    let total_recherche: Int
    let total: Int
}

// MARK: - View Model

@MainActor
class ShamanesViewModel: ObservableObject {
    @Published var response: ShamanesPendingResponse?
    @Published var isLoading = false
    @Published var error: String?

    // Configure with your backend URL
    static let baseURL = "https://vlbh-energy-mcp.onrender.com"

    func fetch(token: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        guard let url = URL(string: "\(Self.baseURL)/shamanes/pending") else {
            error = "URL invalide"
            return
        }

        var req = URLRequest(url: url)
        req.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        req.timeoutInterval = 20

        do {
            let (data, resp) = try await URLSession.shared.data(for: req)
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
                error = "HTTP \((resp as? HTTPURLResponse)?.statusCode ?? 0)"
                return
            }
            response = try JSONDecoder().decode(ShamanesPendingResponse.self, from: data)
        } catch {
            self.error = error.localizedDescription
        }
    }
}

// MARK: - View

struct ShamanesOverviewView: View {
    @StateObject private var vm = ShamanesViewModel()
    let vlbhToken: String

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading {
                    ProgressView("Chargement...")
                } else if let error = vm.error {
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundStyle(.orange)
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Button("Réessayer") {
                            Task { await vm.fetch(token: vlbhToken) }
                        }
                    }
                } else if let data = vm.response {
                    contentView(data)
                } else {
                    Text("Aucune donnée")
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Shamanes")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await vm.fetch(token: vlbhToken) }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .task {
                await vm.fetch(token: vlbhToken)
            }
        }
    }

    // MARK: - Content

    @ViewBuilder
    private func contentView(_ data: ShamanesPendingResponse) -> some View {
        List {
            // Summary header
            Section {
                HStack(spacing: 24) {
                    summaryPill("Soins", count: data.total_soins, color: .blue)
                    summaryPill("Recherche", count: data.total_recherche, color: .purple)
                    summaryPill("Total", count: data.total, color: data.total > 10 ? .red : .orange)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 4)
            }

            // Shamanes list
            Section("Soins en attente par shamane") {
                ForEach(data.shamanes) { shamane in
                    shamaneRow(shamane)
                }
            }
        }
    }

    private func summaryPill(_ label: String, count: Int, color: Color) -> some View {
        VStack(spacing: 4) {
            Text("\(count)")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    private func shamaneRow(_ shamane: ShamanePending) -> some View {
        DisclosureGroup {
            ForEach(shamane.records, id: \.self) { key in
                Text(key)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
        } label: {
            HStack {
                Text(shamane.emoji)
                    .font(.title2)

                VStack(alignment: .leading, spacing: 2) {
                    Text(shamane.name)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Text("Code \(shamane.code)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                HStack(spacing: 8) {
                    if shamane.soins > 0 {
                        badge("\(shamane.soins) soins", color: .blue)
                    }
                    if shamane.recherche > 0 {
                        badge("\(shamane.recherche) rech.", color: .purple)
                    }
                }
            }
        }
    }

    private func badge(_ text: String, color: Color) -> some View {
        Text(text)
            .font(.system(size: 10, weight: .semibold))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.15), in: Capsule())
            .foregroundStyle(color)
    }
}
