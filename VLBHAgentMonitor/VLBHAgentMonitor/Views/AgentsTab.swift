import SwiftUI
import Charts

struct AgentsTab: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @State private var selectedAgent: AgentType = .superagent

    var body: some View {
        VStack(spacing: 0) {
            // Agent selector
            Picker("Agent", selection: $selectedAgent) {
                ForEach(AgentType.allCases) { type in
                    Label(type.rawValue, systemImage: type.icon)
                        .tag(type)
                }
            }
            .pickerStyle(.segmented)
            .padding()

            if let state = coordinator.agents[selectedAgent] {
                ScrollView {
                    VStack(spacing: 16) {
                        agentHeader(state)
                        agentMetrics(state)
                        memoryChart(state)
                        taskHistory(state)
                    }
                    .padding()
                }
            }
        }
    }

    // MARK: - Header

    private func agentHeader(_ state: AgentState) -> some View {
        GroupBox {
            HStack(spacing: 16) {
                Image(systemName: selectedAgent.icon)
                    .font(.largeTitle)
                    .foregroundStyle(selectedAgent.color)
                    .frame(width: 60, height: 60)
                    .background(selectedAgent.color.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                VStack(alignment: .leading, spacing: 4) {
                    Text(selectedAgent.rawValue)
                        .font(.title.bold())
                    Text(selectedAgent.description)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                    HStack {
                        Label(state.status.rawValue, systemImage: "circle.fill")
                            .font(.caption.bold())
                            .foregroundStyle(state.status.color)
                        if let pid = state.pid {
                            Text("PID: \(pid)")
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(.secondary)
                        }
                        if let lastActivity = state.lastActivity {
                            Text("Dernière activité: \(lastActivity, style: .relative)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                Spacer()
            }
            .padding(8)
        }
    }

    // MARK: - Metrics Grid

    private func agentMetrics(_ state: AgentState) -> some View {
        HStack(spacing: 16) {
            MetricCard(title: "CPU", value: String(format: "%.1f%%", state.cpuUsage), icon: "cpu", color: .blue)
            MetricCard(title: "Mémoire", value: String(format: "%.0f MB", state.memoryMB), icon: "memorychip", color: .purple)
            MetricCard(title: "Requêtes", value: "\(state.totalRequests)", icon: "arrow.up.arrow.down", color: .green)
            MetricCard(title: "Erreurs", value: "\(state.errorCount)", icon: "xmark.circle", color: state.errorCount > 0 ? .red : .secondary)
            MetricCard(title: "Taux succès", value: String(format: "%.1f%%", state.successRate * 100), icon: "checkmark.seal", color: state.successRate > 0.95 ? .green : .orange)
            MetricCard(title: "req/min", value: "\(state.requestsPerMinute)", icon: "speedometer", color: .cyan)
        }
    }

    // MARK: - Memory Chart

    private func memoryChart(_ state: AgentState) -> some View {
        GroupBox("Évolution Mémoire — \(selectedAgent.rawValue)") {
            if state.memoryHistory.isEmpty {
                ContentUnavailableView("Pas de données", systemImage: "chart.line.downtrend.xyaxis", description: Text("En attente de données mémoire"))
                    .frame(height: 200)
            } else {
                Chart(state.memoryHistory.suffix(100)) { sample in
                    AreaMark(
                        x: .value("Temps", sample.timestamp),
                        y: .value("MB", sample.megabytes)
                    )
                    .foregroundStyle(
                        .linearGradient(
                            colors: [selectedAgent.color.opacity(0.3), selectedAgent.color.opacity(0.05)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                    LineMark(
                        x: .value("Temps", sample.timestamp),
                        y: .value("MB", sample.megabytes)
                    )
                    .foregroundStyle(selectedAgent.color)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }
                .chartYAxisLabel("Mémoire (MB)")
                .frame(height: 200)
                .padding()
            }
        }
    }

    // MARK: - Task History

    private func taskHistory(_ state: AgentState) -> some View {
        GroupBox("Historique des Tâches") {
            if state.taskHistory.isEmpty {
                ContentUnavailableView("Aucune tâche", systemImage: "tray", description: Text("Les tâches complétées apparaîtront ici"))
                    .frame(height: 100)
            } else {
                Table(state.taskHistory.prefix(20)) {
                    TableColumn("Tâche") { task in
                        Text(task.name).font(.callout)
                    }
                    TableColumn("Détails") { task in
                        Text(task.details)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    TableColumn("Durée") { task in
                        Text(task.durationFormatted)
                            .font(.caption.monospacedDigit())
                    }
                    .width(80)
                    TableColumn("Statut") { task in
                        Label(task.status.rawValue, systemImage: task.status == .completed ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .font(.caption)
                            .foregroundStyle(task.status.color)
                    }
                    .width(100)
                }
                .frame(minHeight: 250)
            }
        }
    }
}

// MARK: - Metric Card

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        GroupBox {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(color)
                Text(value)
                    .font(.headline.monospacedDigit())
                Text(title)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity)
        }
    }
}
