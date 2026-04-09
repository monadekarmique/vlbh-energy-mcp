import SwiftUI

struct LogsTab: View {
    @EnvironmentObject var coordinator: AgentCoordinator
    @State private var filterAgent: AgentType?
    @State private var filterLevel: LogLevel?
    @State private var searchText = ""

    private var filteredLog: [ActivityLogEntry] {
        coordinator.activityLog.filter { entry in
            if let agent = filterAgent, entry.agent != agent { return false }
            if let level = filterLevel, entry.level != level { return false }
            if !searchText.isEmpty {
                return entry.message.localizedCaseInsensitiveContains(searchText) ||
                       (entry.details?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
            return true
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Filters
            HStack {
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Filtrer les logs...", text: $searchText)
                        .textFieldStyle(.plain)
                }
                .padding(8)
                .background(.quaternary)
                .clipShape(RoundedRectangle(cornerRadius: 8))

                Picker("Agent", selection: $filterAgent) {
                    Text("Tous les agents").tag(nil as AgentType?)
                    ForEach(AgentType.allCases) { type in
                        Label(type.rawValue, systemImage: type.icon).tag(type as AgentType?)
                    }
                }
                .frame(width: 160)

                Picker("Niveau", selection: $filterLevel) {
                    Text("Tous").tag(nil as LogLevel?)
                    Text("INFO").tag(LogLevel.info as LogLevel?)
                    Text("WARN").tag(LogLevel.warning as LogLevel?)
                    Text("ERROR").tag(LogLevel.error as LogLevel?)
                    Text("DEBUG").tag(LogLevel.debug as LogLevel?)
                }
                .frame(width: 100)

                Text("\(filteredLog.count) entrées")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button("Effacer") {
                    coordinator.clearLog()
                }
                .controlSize(.small)
            }
            .padding()

            Divider()

            // Log entries
            if filteredLog.isEmpty {
                ContentUnavailableView("Aucun log", systemImage: "doc.text", description: Text("Démarrez les agents pour générer des logs"))
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(filteredLog) { entry in
                            LogRow(entry: entry)
                            Divider()
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Log Row

struct LogRow: View {
    let entry: ActivityLogEntry
    @State private var showDetails = false

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 8) {
                Text(entry.timestamp, format: .dateTime.hour().minute().second().secondFraction(.fractional(2)))
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .frame(width: 100, alignment: .leading)

                Text(entry.level.rawValue)
                    .font(.caption2.bold().monospaced())
                    .foregroundStyle(entry.level.color)
                    .frame(width: 40)

                Image(systemName: entry.agent.icon)
                    .font(.caption)
                    .foregroundStyle(entry.agent.color)
                    .frame(width: 16)

                Text(entry.agent.rawValue)
                    .font(.caption.bold())
                    .foregroundStyle(entry.agent.color)
                    .frame(width: 90, alignment: .leading)

                Text(entry.message)
                    .font(.callout)
                    .lineLimit(1)

                Spacer()

                if entry.details != nil {
                    Button {
                        withAnimation { showDetails.toggle() }
                    } label: {
                        Image(systemName: "info.circle")
                            .font(.caption)
                    }
                    .buttonStyle(.borderless)
                }
            }

            if showDetails, let details = entry.details {
                Text(details)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.leading, 260)
                    .padding(.top, 2)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 6)
        .background(entry.level == .error ? Color.red.opacity(0.05) : .clear)
    }
}
