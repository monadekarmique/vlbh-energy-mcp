import SwiftUI

struct MenuBarView: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @EnvironmentObject var processMonitor: ProcessMonitor

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("VLBH Agent Monitor")
                .font(.headline)

            Divider()

            ForEach(AgentType.allCases) { type in
                if let state = coordinator.agents[type] {
                    HStack {
                        Image(systemName: type.icon)
                            .foregroundStyle(type.color)
                        Text(type.rawValue)
                            .font(.callout)
                        Spacer()
                        Circle()
                            .fill(state.status.color)
                            .frame(width: 8, height: 8)
                        Text(state.status.rawValue)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Divider()

            HStack {
                Label("CPU", systemImage: "cpu")
                    .font(.caption)
                Spacer()
                Text(String(format: "%.0f%%", processMonitor.systemCPU))
                    .font(.caption.monospacedDigit())
            }

            HStack {
                Label("RAM", systemImage: "memorychip")
                    .font(.caption)
                Spacer()
                Text(String(format: "%.1f/%.0f GB", processMonitor.systemMemoryUsedGB, processMonitor.systemMemoryTotalGB))
                    .font(.caption.monospacedDigit())
            }

            HStack {
                Label("MCP", systemImage: "server.rack")
                    .font(.caption)
                Spacer()
                Circle()
                    .fill(coordinator.mcpConnected ? .green : .red)
                    .frame(width: 6, height: 6)
                Text(coordinator.mcpConnected ? "OK" : "OFF")
                    .font(.caption)
            }

            Divider()

            HStack {
                Text("\(coordinator.totalRequests) requêtes")
                    .font(.caption)
                Spacer()
                Text("\(coordinator.totalErrors) erreurs")
                    .font(.caption)
                    .foregroundStyle(coordinator.totalErrors > 0 ? .red : .secondary)
            }
        }
        .padding()
        .frame(width: 280)
    }
}
