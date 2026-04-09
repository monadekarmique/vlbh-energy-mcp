import Foundation
import Combine

@MainActor
final class LeakDetector: ObservableObject {
    @Published var reports: [LeakReport] = []
    @Published var trackedProcesses: [Int32: [MemorySample]] = [:]
    @Published var isDetecting: Bool = false
    @Published var alertThresholdMB: Double = 50.0
    @Published var sampleWindowSeconds: Int = 300 // 5 minutes

    private var timer: Timer?
    private let sampleInterval: TimeInterval = 5.0
    private let minimumSamples = 12 // ~1 minute of samples

    func startDetecting() {
        guard !isDetecting else { return }
        isDetecting = true
        timer = Timer.scheduledTimer(withTimeInterval: sampleInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.sampleAndAnalyze()
            }
        }
    }

    func stopDetecting() {
        isDetecting = false
        timer?.invalidate()
        timer = nil
    }

    func trackProcess(pid: Int32) {
        if trackedProcesses[pid] == nil {
            trackedProcesses[pid] = []
        }
    }

    func untrackProcess(pid: Int32) {
        trackedProcesses.removeValue(forKey: pid)
    }

    func clearReports() {
        reports.removeAll()
    }

    // MARK: - Analysis

    private func sampleAndAnalyze() {
        Task.detached { [weak self] in
            guard let self else { return }

            let pids = await MainActor.run { Array(self.trackedProcesses.keys) }

            for pid in pids {
                if let sample = await Self.sampleProcess(pid: pid) {
                    await MainActor.run {
                        self.trackedProcesses[pid, default: []].append(sample)

                        // Trim old samples
                        let cutoff = Date().addingTimeInterval(-Double(self.sampleWindowSeconds))
                        self.trackedProcesses[pid]?.removeAll { $0.timestamp < cutoff }

                        // Analyze for leaks
                        if let report = self.analyzeForLeak(pid: pid) {
                            // Avoid duplicate reports for same PID within 60 seconds
                            let isDuplicate = self.reports.contains {
                                $0.pid == pid &&
                                abs($0.timestamp.timeIntervalSinceNow) < 60
                            }
                            if !isDuplicate {
                                self.reports.insert(report, at: 0)
                                // Keep max 50 reports
                                if self.reports.count > 50 {
                                    self.reports = Array(self.reports.prefix(50))
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private static func sampleProcess(pid: Int32) async -> MemorySample? {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/ps")
        task.arguments = ["-p", "\(pid)", "-o", "rss=,vsz="]

        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = Pipe()

        do {
            try task.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            task.waitUntilExit()

            guard task.terminationStatus == 0,
                  let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !output.isEmpty else { return nil }

            let parts = output.split(separator: " ", omittingEmptySubsequences: true)
            guard parts.count >= 2,
                  let rssKB = Double(parts[0]),
                  let vszKB = Double(parts[1]) else { return nil }

            let rssMB = rssKB / 1024.0
            let vszMB = vszKB / 1024.0

            return MemorySample(
                megabytes: rssMB,
                residentMB: rssMB,
                virtualMB: vszMB
            )
        } catch {
            return nil
        }
    }

    private func analyzeForLeak(pid: Int32) -> LeakReport? {
        guard let samples = trackedProcesses[pid],
              samples.count >= minimumSamples else { return nil }

        let values = samples.map(\.megabytes)
        guard let first = values.first, let last = values.last, first > 0 else { return nil }

        // Linear regression to determine growth trend
        let n = Double(values.count)
        let xs = (0..<values.count).map { Double($0) }
        let sumX = xs.reduce(0, +)
        let sumY = values.reduce(0, +)
        let sumXY = zip(xs, values).map(*).reduce(0, +)
        let sumX2 = xs.map { $0 * $0 }.reduce(0, +)

        let slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)

        // slope is MB per sample interval
        let growthRatePerMinute = slope * (60.0 / sampleInterval)

        // Determine severity
        let growthPercent = ((last - first) / first) * 100
        let severity: LeakSeverity

        if growthRatePerMinute > 10 || growthPercent > 100 {
            severity = .critical
        } else if growthRatePerMinute > 5 || growthPercent > 50 {
            severity = .high
        } else if growthRatePerMinute > 1 || growthPercent > 20 {
            severity = .medium
        } else if growthRatePerMinute > 0.2 || growthPercent > 10 {
            severity = .low
        } else {
            return nil // No significant leak detected
        }

        // Get process name
        let processName = getProcessName(pid: pid)

        return LeakReport(
            timestamp: Date(),
            agentType: nil,
            processName: processName,
            pid: pid,
            initialMemoryMB: first,
            currentMemoryMB: last,
            growthRate: growthRatePerMinute,
            severity: severity,
            samples: samples
        )
    }

    private func getProcessName(pid: Int32) -> String {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/ps")
        task.arguments = ["-p", "\(pid)", "-o", "comm="]

        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = Pipe()

        do {
            try task.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            task.waitUntilExit()
            return String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? "Unknown"
        } catch {
            return "Unknown"
        }
    }
}
