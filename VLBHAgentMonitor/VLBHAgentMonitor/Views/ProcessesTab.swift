import SwiftUI

struct ProcessesTab: View {
    @EnvironmentObject var processMonitor: ProcessMonitor
    @EnvironmentObject var leakDetector: LeakDetector
    @State private var searchText = ""
    @State private var showOnlyAgentProcesses = false
    @State private var sortOrder = [KeyPathComparator(\ProcessInfo.cpuPercent, order: .reverse)]

    private var filteredProcesses: [ProcessInfo] {
        var procs = showOnlyAgentProcesses ? processMonitor.agentProcesses : processMonitor.processes
        if !searchText.isEmpty {
            procs = procs.filter { $0.name.localizedCaseInsensitiveContains(searchText) ||
                                    $0.user.localizedCaseInsensitiveContains(searchText) }
        }
        return procs.sorted(using: sortOrder)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack {
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Rechercher un processus...", text: $searchText)
                        .textFieldStyle(.plain)
                }
                .padding(8)
                .background(.quaternary)
                .clipShape(RoundedRectangle(cornerRadius: 8))

                Toggle("Agents uniquement", isOn: $showOnlyAgentProcesses)
                    .toggleStyle(.switch)
                    .controlSize(.small)

                Button {
                    processMonitor.refreshProcesses()
                } label: {
                    Label("Rafraîchir", systemImage: "arrow.clockwise")
                }
                .controlSize(.small)

                Text("\(filteredProcesses.count) processus")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()

            Divider()

            // Process Table
            Table(filteredProcesses, sortOrder: $sortOrder) {
                TableColumn("PID") { proc in
                    Text("\(proc.id)")
                        .font(.caption.monospacedDigit())
                }
                .width(60)

                TableColumn("Nom", value: \.name) { proc in
                    HStack {
                        Circle()
                            .fill(proc.isAgentProcess ? .green : .secondary.opacity(0.3))
                            .frame(width: 6, height: 6)
                        Text(proc.name)
                            .font(.callout)
                            .lineLimit(1)
                    }
                }
                .width(min: 150, ideal: 200)

                TableColumn("Utilisateur") { proc in
                    Text(proc.user)
                        .font(.caption)
                }
                .width(80)

                TableColumn("CPU %", value: \.cpuPercent) { proc in
                    HStack {
                        Text(String(format: "%.1f%%", proc.cpuPercent))
                            .font(.caption.monospacedDigit())
                        Spacer()
                        MiniBar(value: proc.cpuPercent / 100, color: cpuColor(proc.cpuPercent))
                    }
                }
                .width(120)

                TableColumn("Mémoire (MB)", value: \.memoryMB) { proc in
                    HStack {
                        Text(String(format: "%.1f", proc.memoryMB))
                            .font(.caption.monospacedDigit())
                        Spacer()
                        MiniBar(value: min(proc.memoryMB / 1000, 1), color: .purple)
                    }
                }
                .width(120)

                TableColumn("RSS (MB)") { proc in
                    Text(String(format: "%.1f", proc.residentMB))
                        .font(.caption.monospacedDigit())
                }
                .width(80)

                TableColumn("VSZ (MB)") { proc in
                    Text(String(format: "%.0f", proc.virtualMB))
                        .font(.caption.monospacedDigit())
                }
                .width(80)

                TableColumn("État") { proc in
                    Text(proc.state)
                        .font(.caption.monospacedDigit())
                }
                .width(50)

                TableColumn("Actions") { proc in
                    HStack(spacing: 4) {
                        Button {
                            leakDetector.trackProcess(pid: proc.id)
                        } label: {
                            Image(systemName: "eye")
                                .font(.caption)
                        }
                        .buttonStyle(.borderless)
                        .help("Surveiller les fuites mémoire")

                        if leakDetector.trackedProcesses[proc.id] != nil {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.caption)
                                .foregroundStyle(.green)
                        }
                    }
                }
                .width(60)
            }
        }
    }

    private func cpuColor(_ value: Double) -> Color {
        if value > 50 { return .red }
        if value > 20 { return .orange }
        return .blue
    }
}

// MARK: - Mini Bar

struct MiniBar: View {
    let value: Double
    let color: Color

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 2)
                    .fill(color.opacity(0.15))
                RoundedRectangle(cornerRadius: 2)
                    .fill(color)
                    .frame(width: geo.size.width * min(max(value, 0), 1))
            }
        }
        .frame(width: 40, height: 6)
    }
}
