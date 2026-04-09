import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @EnvironmentObject var processMonitor: ProcessMonitor
    @EnvironmentObject var leakDetector: LeakDetector

    @State private var selectedTab: DashboardTab = .overview
    @State private var isRunning = false

    enum DashboardTab: String, CaseIterable {
        case overview = "Vue d'ensemble"
        case agents = "Agents"
        case processes = "Processus"
        case leaks = "Leak Detector"
        case mcp = "MCP Server"
        case logs = "Journal"
    }

    var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            detailContent
        }
        .navigationTitle("VLBH Agent Monitor")
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                toolbarButtons
            }
        }
        .onAppear {
            processMonitor.startMonitoring()
            leakDetector.startDetecting()
        }
    }

    // MARK: - Sidebar

    private var sidebar: some View {
        List(selection: $selectedTab) {
            Section("Monitoring") {
                ForEach(DashboardTab.allCases, id: \.self) { tab in
                    Label(tab.rawValue, systemImage: tabIcon(tab))
                        .tag(tab)
                        .badge(badgeCount(for: tab))
                }
            }

            Section("Agents Actifs") {
                ForEach(AgentType.allCases) { type in
                    if let state = coordinator.agents[type] {
                        HStack {
                            Image(systemName: type.icon)
                                .foregroundStyle(type.color)
                            Text(type.rawValue)
                            Spacer()
                            Circle()
                                .fill(state.status.color)
                                .frame(width: 8, height: 8)
                        }
                    }
                }
            }

            Section("MCP Server") {
                HStack {
                    Circle()
                        .fill(coordinator.mcpConnected ? .green : .red)
                        .frame(width: 8, height: 8)
                    Text(coordinator.mcpConnected ? "Connecté" : "Déconnecté")
                        .font(.caption)
                }
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 220)
    }

    // MARK: - Detail Content

    @ViewBuilder
    private var detailContent: some View {
        switch selectedTab {
        case .overview:
            OverviewTab()
        case .agents:
            AgentsTab()
        case .processes:
            ProcessesTab()
        case .leaks:
            LeakDetectorTab()
        case .mcp:
            MCPTab()
        case .logs:
            LogsTab()
        }
    }

    // MARK: - Toolbar

    private var toolbarButtons: some View {
        Group {
            Button {
                if isRunning {
                    coordinator.stopSimulation()
                } else {
                    coordinator.startSimulation()
                }
                isRunning.toggle()
            } label: {
                Label(isRunning ? "Arrêter" : "Démarrer",
                      systemImage: isRunning ? "stop.fill" : "play.fill")
            }
            .tint(isRunning ? .red : .green)

            Button {
                processMonitor.refreshProcesses()
            } label: {
                Label("Rafraîchir", systemImage: "arrow.clockwise")
            }
        }
    }

    // MARK: - Helpers

    private func tabIcon(_ tab: DashboardTab) -> String {
        switch tab {
        case .overview: return "square.grid.2x2"
        case .agents: return "cpu"
        case .processes: return "list.bullet.rectangle"
        case .leaks: return "drop.triangle"
        case .mcp: return "server.rack"
        case .logs: return "doc.text"
        }
    }

    private func badgeCount(for tab: DashboardTab) -> Int {
        switch tab {
        case .leaks: return leakDetector.reports.count
        case .logs: return coordinator.activityLog.filter { $0.level == .error }.count
        default: return 0
        }
    }
}
