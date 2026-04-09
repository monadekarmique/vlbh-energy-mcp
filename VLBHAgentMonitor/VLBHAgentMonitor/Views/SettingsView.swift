import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @AppStorage("pollingInterval") private var pollingInterval: Double = 2.0
    @AppStorage("maxLogEntries") private var maxLogEntries: Int = 500
    @AppStorage("enableNotifications") private var enableNotifications: Bool = true
    @AppStorage("leakThresholdMB") private var leakThresholdMB: Double = 50.0

    var body: some View {
        TabView {
            generalSettings
                .tabItem { Label("Général", systemImage: "gear") }

            mcpSettings
                .tabItem { Label("MCP Server", systemImage: "server.rack") }

            leakSettings
                .tabItem { Label("Leak Detector", systemImage: "drop.triangle") }
        }
        .frame(width: 500, height: 400)
    }

    // MARK: - General

    private var generalSettings: some View {
        Form {
            Section("Monitoring") {
                HStack {
                    Text("Intervalle de polling")
                    Spacer()
                    Slider(value: $pollingInterval, in: 1...10, step: 0.5)
                        .frame(width: 200)
                    Text(String(format: "%.1fs", pollingInterval))
                        .monospacedDigit()
                        .frame(width: 40)
                }

                Stepper("Max entrées journal: \(maxLogEntries)", value: $maxLogEntries, in: 100...2000, step: 100)
            }

            Section("Notifications") {
                Toggle("Activer les notifications", isOn: $enableNotifications)
                Toggle("Alertes fuites mémoire", isOn: $enableNotifications)
                Toggle("Alertes erreurs agents", isOn: $enableNotifications)
            }
        }
        .padding()
    }

    // MARK: - MCP

    private var mcpSettings: some View {
        Form {
            Section("Connexion") {
                TextField("URL du serveur", text: $coordinator.mcpBaseURL)
                SecureField("Token d'authentification", text: $coordinator.mcpToken)
            }

            Section("Endpoints") {
                ForEach(coordinator.mcpEndpoints) { endpoint in
                    HStack {
                        Text(endpoint.method)
                            .font(.caption.bold())
                            .foregroundStyle(endpoint.method == "GET" ? .green : .blue)
                        Text(endpoint.endpoint)
                            .font(.callout.monospaced())
                        Spacer()
                        Circle()
                            .fill(endpoint.isHealthy ? .green : .secondary)
                            .frame(width: 8, height: 8)
                    }
                }
            }
        }
        .padding()
    }

    // MARK: - Leak Detection

    private var leakSettings: some View {
        Form {
            Section("Seuils de détection") {
                HStack {
                    Text("Seuil d'alerte")
                    Spacer()
                    Slider(value: $leakThresholdMB, in: 10...200, step: 10)
                        .frame(width: 200)
                    Text(String(format: "%.0f MB", leakThresholdMB))
                        .monospacedDigit()
                        .frame(width: 60)
                }
            }

            Section("Sévérité") {
                ForEach(LeakSeverity.allCases, id: \.self) { severity in
                    HStack {
                        Circle()
                            .fill(severity.color)
                            .frame(width: 10, height: 10)
                        Text(severity.rawValue)
                        Spacer()
                        Text(severityDescription(severity))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding()
    }

    private func severityDescription(_ severity: LeakSeverity) -> String {
        switch severity {
        case .low: return "> 0.2 MB/min ou > 10% croissance"
        case .medium: return "> 1 MB/min ou > 20% croissance"
        case .high: return "> 5 MB/min ou > 50% croissance"
        case .critical: return "> 10 MB/min ou > 100% croissance"
        }
    }
}
