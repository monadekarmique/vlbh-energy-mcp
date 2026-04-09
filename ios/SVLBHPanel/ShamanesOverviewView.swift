import SwiftUI

// MARK: - Shamanes Pending Badges
//
// Lit le record SHAMANES-PENDING via le webhook PULL existant.
// Format: "0300:6|0301:4|0302:3|0303:1|455000:16"
// Affiche un badge (chiffre) à côté de chaque shamane dans le menu recevoir.

struct ShamaneBadge: Identifiable {
    let code: String
    let name: String
    let emoji: String
    let count: Int
    var id: String { code }
}

@MainActor
class ShamanesPendingManager: ObservableObject {
    @Published var badges: [String: Int] = [:]  // code → count

    static let shamanes: [(code: String, name: String, emoji: String)] = [
        ("0300", "Cornelia", "\u{1F431}"),
        ("0301", "Flavia", "\u{2728}"),
        ("0302", "Anne", "\u{1F338}"),
        ("0303", "Chlo\u{00e9}", "\u{1F4AB}"),
        ("455000", "Patrick", "\u{1F52C}"),
    ]

    // Call this when the receive/pull menu opens
    func fetch(pullURL: URL) async {
        var req = URLRequest(url: pullURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: ["session_id": "SHAMANES-PENDING"])
        req.timeoutInterval = 10

        do {
            let (data, response) = try await URLSession.shared.data(for: req)
            guard (response as? HTTPURLResponse)?.statusCode == 200,
                  let text = String(data: data, encoding: .utf8),
                  !text.isEmpty, text != "READ" else { return }
            parse(text)
        } catch {
            print("[ShamanesPending] fetch error: \(error.localizedDescription)")
        }
    }

    private func parse(_ text: String) {
        // Format: "0300:6|0301:4|0302:3|0303:1|455000:16"
        var result: [String: Int] = [:]
        for pair in text.split(separator: "|") {
            let parts = pair.split(separator: ":")
            if parts.count == 2, let count = Int(parts[1]) {
                result[String(parts[0])] = count
            }
        }
        badges = result
    }

    func count(for code: String) -> Int {
        badges[code] ?? 0
    }

    var allBadges: [ShamaneBadge] {
        Self.shamanes.map { s in
            ShamaneBadge(code: s.code, name: s.name, emoji: s.emoji, count: count(for: s.code))
        }
    }
}

// MARK: - Badge View (to embed next to each shamane in the receive menu)
//
// Usage in your existing pull source picker:
//
//   @StateObject var pendingManager = ShamanesPendingManager()
//
//   ForEach(pendingManager.allBadges) { shamane in
//       Button { selectSource(shamane.code) } label: {
//           HStack {
//               Text("\(shamane.emoji) \(shamane.name)")
//               Spacer()
//               if shamane.count > 0 {
//                   PendingBadge(count: shamane.count)
//               }
//           }
//       }
//   }
//   .task { await pendingManager.fetch(pullURL: yourPullWebhookURL) }

struct PendingBadge: View {
    let count: Int

    var body: some View {
        Text("\(count)")
            .font(.system(size: 12, weight: .bold))
            .foregroundStyle(.white)
            .frame(minWidth: 22, minHeight: 22)
            .background(count > 5 ? Color.red : Color.orange, in: Circle())
    }
}
