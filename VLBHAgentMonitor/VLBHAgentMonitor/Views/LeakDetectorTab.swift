import SwiftUI
import Charts

struct LeakDetectorTab: View {
    @EnvironmentObject var leakDetector: LeakDetector

    var body: some View {
        VStack(spacing: 0) {
            // Controls
            HStack {
                Label("Leak Detector", systemImage: "drop.triangle.fill")
                    .font(.headline)

                Spacer()

                HStack(spacing: 12) {
                    Toggle("Détection active", isOn: Binding(
                        get: { leakDetector.isDetecting },
                        set: { $0 ? leakDetector.startDetecting() : leakDetector.stopDetecting() }
                    ))
                    .toggleStyle(.switch)
                    .controlSize(.small)

                    Text("Processus surveillés: \(leakDetector.trackedProcesses.count)")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Button("Effacer rapports") {
                        leakDetector.clearReports()
                    }
                    .controlSize(.small)
                    .disabled(leakDetector.reports.isEmpty)
                }
            }
            .padding()

            Divider()

            if leakDetector.reports.isEmpty && leakDetector.trackedProcesses.isEmpty {
                ContentUnavailableView(
                    "Aucune surveillance active",
                    systemImage: "drop.triangle",
                    description: Text("Allez dans l'onglet Processus et cliquez sur l'icône œil pour surveiller un processus")
                )
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        // Tracked processes overview
                        if !leakDetector.trackedProcesses.isEmpty {
                            trackedProcessesSection
                        }

                        // Leak reports
                        if !leakDetector.reports.isEmpty {
                            leakReportsSection
                        }
                    }
                    .padding()
                }
            }
        }
    }

    // MARK: - Tracked Processes

    private var trackedProcessesSection: some View {
        GroupBox("Processus Surveillés") {
            VStack(spacing: 12) {
                ForEach(Array(leakDetector.trackedProcesses.keys.sorted()), id: \.self) { pid in
                    if let samples = leakDetector.trackedProcesses[pid] {
                        HStack {
                            VStack(alignment: .leading) {
                                Text("PID \(pid)")
                                    .font(.callout.bold().monospacedDigit())
                                Text("\(samples.count) échantillons")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            if samples.count > 5 {
                                Chart(samples.suffix(50)) { sample in
                                    LineMark(
                                        x: .value("T", sample.timestamp),
                                        y: .value("MB", sample.megabytes)
                                    )
                                    .foregroundStyle(.blue)
                                }
                                .frame(height: 40)
                                .chartXAxis(.hidden)
                                .chartYAxis(.hidden)
                            }

                            Spacer()

                            if let last = samples.last {
                                Text(String(format: "%.1f MB", last.megabytes))
                                    .font(.caption.monospacedDigit().bold())
                            }

                            Button {
                                leakDetector.untrackProcess(pid: pid)
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.secondary)
                            }
                            .buttonStyle(.borderless)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .padding()
        }
    }

    // MARK: - Leak Reports

    private var leakReportsSection: some View {
        GroupBox("Rapports de Fuite") {
            VStack(spacing: 0) {
                ForEach(leakDetector.reports) { report in
                    LeakReportRow(report: report)
                    Divider()
                }
            }
        }
    }
}

// MARK: - Leak Report Row

struct LeakReportRow: View {
    let report: LeakReport
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Severity badge
                Text(report.severity.rawValue)
                    .font(.caption.bold())
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(report.severity.color.opacity(0.2))
                    .foregroundStyle(report.severity.color)
                    .clipShape(Capsule())

                VStack(alignment: .leading) {
                    Text("\(report.processName) (PID: \(report.pid))")
                        .font(.callout.bold())
                    Text(report.timestamp, style: .relative)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                VStack(alignment: .trailing) {
                    Text(String(format: "+%.1f%%", report.growthPercent))
                        .font(.callout.bold())
                        .foregroundStyle(.red)
                    Text(String(format: "%.1f → %.1f MB", report.initialMemoryMB, report.currentMemoryMB))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                }

                Button {
                    withAnimation { isExpanded.toggle() }
                } label: {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                }
                .buttonStyle(.borderless)
            }

            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 24) {
                        LabeledContent("Croissance") {
                            Text(String(format: "%.2f MB/min", report.growthRate))
                                .monospacedDigit()
                        }
                        LabeledContent("Échantillons") {
                            Text("\(report.samples.count)")
                                .monospacedDigit()
                        }
                    }
                    .font(.caption)

                    Chart(report.samples) { sample in
                        AreaMark(
                            x: .value("Temps", sample.timestamp),
                            y: .value("MB", sample.megabytes)
                        )
                        .foregroundStyle(report.severity.color.opacity(0.2))

                        LineMark(
                            x: .value("Temps", sample.timestamp),
                            y: .value("MB", sample.megabytes)
                        )
                        .foregroundStyle(report.severity.color)
                    }
                    .frame(height: 120)
                    .chartYAxisLabel("MB")
                }
                .padding(.top, 4)
            }
        }
        .padding()
    }
}
