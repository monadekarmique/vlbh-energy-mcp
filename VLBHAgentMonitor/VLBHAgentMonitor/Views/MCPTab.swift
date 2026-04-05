import SwiftUI

struct MCPTab: View {
    @EnvironmentObject var coordinator: AgentCoordinator

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Connection Card
                connectionCard

                // Endpoints Grid
                endpointsGrid
            }
            .padding()
        }
    }

    // MARK: - Connection

    private var connectionCard: some View {
        GroupBox("Connexion MCP Server") {
            VStack(spacing: 12) {
                HStack {
                    Circle()
                        .fill(coordinator.mcpConnected ? .green : .red)
                        .frame(width: 12, height: 12)
                    Text(coordinator.mcpConnected ? "Connecté" : "Déconnecté")
                        .font(.headline)
                    Spacer()
                }

                HStack {
                    TextField("URL du serveur MCP", text: $coordinator.mcpBaseURL)
                        .textFieldStyle(.roundedBorder)

                    SecureField("Token", text: $coordinator.mcpToken)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 200)

                    if coordinator.mcpConnected {
                        Button("Déconnecter") {
                            coordinator.disconnectMCP()
                        }
                        .tint(.red)
                    } else {
                        Button("Connecter") {
                            coordinator.connectToMCP()
                        }
                        .tint(.green)
                        .disabled(coordinator.mcpToken.isEmpty)
                    }
                }
            }
            .padding()
        }
    }

    // MARK: - Endpoints

    private var endpointsGrid: some View {
        GroupBox("Endpoints MCP") {
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible()),
            ], spacing: 12) {
                ForEach(coordinator.mcpEndpoints) { endpoint in
                    EndpointCard(endpoint: endpoint)
                }
            }
            .padding()
        }
    }
}

// MARK: - Endpoint Card

struct EndpointCard: View {
    let endpoint: MCPEndpointStatus

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(endpoint.method)
                    .font(.caption.bold())
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(methodColor.opacity(0.15))
                    .foregroundStyle(methodColor)
                    .clipShape(Capsule())

                Text(endpoint.endpoint)
                    .font(.callout.bold().monospaced())
                    .lineLimit(1)
            }

            HStack {
                VStack(alignment: .leading) {
                    Text("Status")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    HStack(spacing: 4) {
                        Circle()
                            .fill(endpoint.isHealthy ? .green : (endpoint.lastStatusCode == 0 ? .secondary : .red))
                            .frame(width: 6, height: 6)
                        Text(endpoint.lastStatusCode == 0 ? "—" : "\(endpoint.lastStatusCode)")
                            .font(.caption.monospacedDigit())
                    }
                }

                Spacer()

                VStack(alignment: .leading) {
                    Text("Requêtes")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text("\(endpoint.requestCount)")
                        .font(.caption.monospacedDigit())
                }

                Spacer()

                VStack(alignment: .leading) {
                    Text("Erreurs")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text("\(endpoint.errorCount)")
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(endpoint.errorCount > 0 ? .red : .primary)
                }
            }

            if endpoint.lastChecked != .distantPast {
                Text("Vérifié \(endpoint.lastChecked, style: .relative)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.quaternary)
        )
    }

    private var methodColor: Color {
        endpoint.method == "GET" ? .green : .blue
    }
}
