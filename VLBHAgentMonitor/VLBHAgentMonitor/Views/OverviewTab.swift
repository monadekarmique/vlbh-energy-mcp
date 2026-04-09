import SwiftUI
import Charts

struct OverviewTab: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @EnvironmentObject var processMonitor: ProcessMonitor

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Top Stats Cards
                statsCards

                // Agent Cards
                HStack(spacing: 16) {
                    ForEach(AgentType.allCases) { type in
                        if let state = coordinator.agents[type] {
                            AgentOverviewCard(type: type, state: state)
                        }
                    }
                }

                // System & Memory Charts
                HStack(spacing: 16) {
                    systemResourcesCard
                    memoryTrendChart
                }

                // Recent Activity
                recentActivity
            }
            .padding()
        }
    }

    // MARK: - Stats Cards

    private var statsCards: some View {
        HStack(spacing: 16) {
            StatCard(
                title: "Agents Actifs",
                value: "\(coordinator.totalActiveAgents)/\(AgentType.allCases.count)",
                icon: "cpu",
                color: .green
            )
            StatCard(
                title: "Requêtes Totales",
                value: "\(coordinator.totalRequests)",
                icon: "arrow.up.arrow.down",
                color: .blue
            )
            StatCard(
                title: "Taux de Succès",
                value: String(format: "%.1f%%", coordinator.overallSuccessRate * 100),
                icon: "checkmark.circle",
                color: coordinator.overallSuccessRate > 0.95 ? .green : .orange
            )
            StatCard(
                title: "Erreurs",
                value: "\(coordinator.totalErrors)",
                icon: "exclamationmark.triangle",
                color: coordinator.totalErrors > 0 ? .red : .secondary
            )
            StatCard(
                title: "CPU Système",
                value: String(format: "%.0f%%", processMonitor.systemCPU),
                icon: "gauge.with.dots.needle.33percent",
                color: processMonitor.systemCPU > 80 ? .red : .blue
            )
            StatCard(
                title: "Mémoire",
                value: String(format: "%.1f/%.0f GB", processMonitor.systemMemoryUsedGB, processMonitor.systemMemoryTotalGB),
                icon: "memorychip",
                color: processMonitor.systemMemoryPercent > 80 ? .red : .purple
            )
        }
    }

    // MARK: - System Resources

    private var systemResourcesCard: some View {
        GroupBox("Ressources Système") {
            VStack(alignment: .leading, spacing: 12) {
                ResourceBar(label: "CPU", value: processMonitor.systemCPU / 100, color: .blue)
                ResourceBar(label: "Mémoire", value: processMonitor.systemMemoryPercent / 100, color: .purple)

                Divider()

                HStack {
                    VStack(alignment: .leading) {
                        Text("Processus monitorés")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text("\(processMonitor.agentProcesses.count)")
                            .font(.title2.bold())
                    }
                    Spacer()
                    VStack(alignment: .leading) {
                        Text("Total processus")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text("\(processMonitor.processes.count)")
                            .font(.title2.bold())
                    }
                }
            }
            .padding()
        }
        .frame(minHeight: 200)
    }

    // MARK: - Memory Trend

    private var memoryTrendChart: some View {
        GroupBox("Tendance Mémoire Agents") {
            Chart {
                ForEach(AgentType.allCases) { type in
                    if let state = coordinator.agents[type] {
                        ForEach(state.memoryHistory.suffix(50)) { sample in
                            LineMark(
                                x: .value("Temps", sample.timestamp),
                                y: .value("MB", sample.megabytes)
                            )
                            .foregroundStyle(by: .value("Agent", type.rawValue))
                        }
                    }
                }
            }
            .chartForegroundStyleScale([
                "SuperAgent": Color.purple,
                "MakeAgent": Color.orange,
                "Cowork": Color.cyan,
            ])
            .chartYAxisLabel("Mémoire (MB)")
            .padding()
        }
        .frame(minHeight: 200)
    }

    // MARK: - Recent Activity

    private var recentActivity: some View {
        GroupBox("Activité Récente") {
            if coordinator.activityLog.isEmpty {
                ContentUnavailableView(
                    "Aucune activité",
                    systemImage: "clock",
                    description: Text("Démarrez les agents pour voir l'activité")
                )
                .frame(height: 100)
            } else {
                VStack(spacing: 0) {
                    ForEach(coordinator.activityLog.prefix(10)) { entry in
                        HStack {
                            Image(systemName: entry.agent.icon)
                                .foregroundStyle(entry.agent.color)
                                .frame(width: 20)

                            Text(entry.timestamp, style: .time)
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(.secondary)
                                .frame(width: 70, alignment: .leading)

                            Text(entry.level.rawValue)
                                .font(.caption.bold())
                                .foregroundStyle(entry.level.color)
                                .frame(width: 45)

                            Text(entry.message)
                                .font(.callout)
                                .lineLimit(1)

                            Spacer()
                        }
                        .padding(.vertical, 4)

                        if entry.id != coordinator.activityLog.prefix(10).last?.id {
                            Divider()
                        }
                    }
                }
                .padding()
            }
        }
    }
}

// MARK: - Stat Card

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        GroupBox {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(color)
                Text(value)
                    .font(.title3.bold().monospacedDigit())
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
        }
    }
}

// MARK: - Resource Bar

struct ResourceBar: View {
    let label: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(.caption.bold())
                Spacer()
                Text(String(format: "%.0f%%", value * 100))
                    .font(.caption.monospacedDigit())
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color.opacity(0.15))
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color)
                        .frame(width: geo.size.width * min(max(value, 0), 1))
                }
            }
            .frame(height: 8)
        }
    }
}

// MARK: - Agent Overview Card

struct AgentOverviewCard: View {
    let type: AgentType
    let state: AgentState

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Image(systemName: type.icon)
                        .font(.title2)
                        .foregroundStyle(type.color)
                    VStack(alignment: .leading) {
                        Text(type.rawValue)
                            .font(.headline)
                        Text(state.status.rawValue)
                            .font(.caption)
                            .foregroundStyle(state.status.color)
                    }
                    Spacer()
                    if state.status.isActive {
                        ProgressView()
                            .scaleEffect(0.7)
                    }
                }

                Divider()

                if let task = state.currentTask {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(task.name)
                            .font(.callout.bold())
                        ProgressView(value: task.progress)
                            .tint(type.color)
                        Text(task.details)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                } else {
                    Text("Aucune tâche en cours")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()

                HStack {
                    VStack(alignment: .leading) {
                        Text("CPU").font(.caption2).foregroundStyle(.secondary)
                        Text(String(format: "%.1f%%", state.cpuUsage))
                            .font(.caption.monospacedDigit().bold())
                    }
                    Spacer()
                    VStack(alignment: .leading) {
                        Text("RAM").font(.caption2).foregroundStyle(.secondary)
                        Text(String(format: "%.0f MB", state.memoryMB))
                            .font(.caption.monospacedDigit().bold())
                    }
                    Spacer()
                    VStack(alignment: .leading) {
                        Text("req/min").font(.caption2).foregroundStyle(.secondary)
                        Text("\(state.requestsPerMinute)")
                            .font(.caption.monospacedDigit().bold())
                    }
                }

                if state.hasLeakSuspicion {
                    Label("Suspicion de fuite mémoire", systemImage: "exclamationmark.triangle.fill")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
            }
            .padding(4)
        }
    }
}
