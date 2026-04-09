import Foundation
import Combine

@MainActor
final class ProcessMonitor: ObservableObject {
    @Published var processes: [ProcessInfo] = []
    @Published var systemCPU: Double = 0.0
    @Published var systemMemoryUsedGB: Double = 0.0
    @Published var systemMemoryTotalGB: Double = 0.0
    @Published var isMonitoring: Bool = false

    private var timer: Timer?
    private let pollingInterval: TimeInterval = 2.0

    var systemMemoryPercent: Double {
        guard systemMemoryTotalGB > 0 else { return 0 }
        return (systemMemoryUsedGB / systemMemoryTotalGB) * 100
    }

    var agentProcesses: [ProcessInfo] {
        processes.filter(\.isAgentProcess)
    }

    var topProcesses: [ProcessInfo] {
        Array(processes.sorted { $0.cpuPercent > $1.cpuPercent }.prefix(20))
    }

    func startMonitoring() {
        guard !isMonitoring else { return }
        isMonitoring = true
        refreshProcesses()
        timer = Timer.scheduledTimer(withTimeInterval: pollingInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.refreshProcesses()
            }
        }
    }

    func stopMonitoring() {
        isMonitoring = false
        timer?.invalidate()
        timer = nil
    }

    func refreshProcesses() {
        Task.detached { [weak self] in
            let procs = await Self.fetchProcessList()
            let (cpu, memUsed, memTotal) = await Self.fetchSystemStats()
            await MainActor.run {
                self?.processes = procs
                self?.systemCPU = cpu
                self?.systemMemoryUsedGB = memUsed
                self?.systemMemoryTotalGB = memTotal
            }
        }
    }

    // MARK: - Process List via ps

    private static func fetchProcessList() async -> [ProcessInfo] {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/ps")
        task.arguments = ["aux"]

        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = Pipe()

        do {
            try task.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            task.waitUntilExit()

            guard let output = String(data: data, encoding: .utf8) else { return [] }
            return parsePS(output)
        } catch {
            return []
        }
    }

    private static func parsePS(_ output: String) -> [ProcessInfo] {
        let lines = output.components(separatedBy: "\n").dropFirst() // skip header
        return lines.compactMap { line -> ProcessInfo? in
            let cols = line.split(separator: " ", maxSplits: 10, omittingEmptySubsequences: true)
            guard cols.count >= 11 else { return nil }

            let user = String(cols[0])
            guard let pid = Int32(cols[1]) else { return nil }
            let cpu = Double(cols[2]) ?? 0.0
            let mem = Double(cols[3]) ?? 0.0
            let vsz = (Double(cols[4]) ?? 0.0) / 1024.0 // KB -> MB
            let rss = (Double(cols[5]) ?? 0.0) / 1024.0
            let command = String(cols[10])
            let name = URL(fileURLWithPath: command.components(separatedBy: " ").first ?? command)
                .lastPathComponent

            return ProcessInfo(
                id: pid,
                name: name,
                cpuPercent: cpu,
                memoryMB: rss,
                residentMB: rss,
                virtualMB: vsz,
                threadCount: 0,
                state: String(cols[7]),
                user: user,
                startTime: nil,
                parentPID: 0
            )
        }
    }

    // MARK: - System Stats

    private static func fetchSystemStats() async -> (cpu: Double, memUsed: Double, memTotal: Double) {
        // Get total physical memory
        let totalMemory = Double(ProcessInfo_System.processInfo.physicalMemory) / (1024 * 1024 * 1024)

        // Get memory pressure via vm_stat
        let vmTask = Process()
        vmTask.executableURL = URL(fileURLWithPath: "/usr/bin/vm_stat")
        let vmPipe = Pipe()
        vmTask.standardOutput = vmPipe
        vmTask.standardError = Pipe()

        var memUsed: Double = 0
        do {
            try vmTask.run()
            let data = vmPipe.fileHandleForReading.readDataToEndOfFile()
            vmTask.waitUntilExit()
            if let output = String(data: data, encoding: .utf8) {
                memUsed = parseVMStat(output, totalGB: totalMemory)
            }
        } catch {}

        // Get CPU usage from top
        let topTask = Process()
        topTask.executableURL = URL(fileURLWithPath: "/usr/bin/top")
        topTask.arguments = ["-l", "1", "-n", "0", "-s", "0"]
        let topPipe = Pipe()
        topTask.standardOutput = topPipe
        topTask.standardError = Pipe()

        var cpuUsage: Double = 0
        do {
            try topTask.run()
            let data = topPipe.fileHandleForReading.readDataToEndOfFile()
            topTask.waitUntilExit()
            if let output = String(data: data, encoding: .utf8) {
                cpuUsage = parseCPUFromTop(output)
            }
        } catch {}

        return (cpuUsage, memUsed, totalMemory)
    }

    private static func parseVMStat(_ output: String, totalGB: Double) -> Double {
        let pageSize: Double = 16384 // Apple Silicon default page size
        var activePages: Double = 0
        var wiredPages: Double = 0
        var compressedPages: Double = 0

        for line in output.components(separatedBy: "\n") {
            if line.contains("Pages active") {
                activePages = extractVMStatValue(line)
            } else if line.contains("Pages wired") {
                wiredPages = extractVMStatValue(line)
            } else if line.contains("Pages occupied by compressor") {
                compressedPages = extractVMStatValue(line)
            }
        }

        let usedBytes = (activePages + wiredPages + compressedPages) * pageSize
        return usedBytes / (1024 * 1024 * 1024) // Convert to GB
    }

    private static func extractVMStatValue(_ line: String) -> Double {
        let parts = line.components(separatedBy: ":")
        guard parts.count >= 2 else { return 0 }
        let valueStr = parts[1].trimmingCharacters(in: .whitespaces).replacingOccurrences(of: ".", with: "")
        return Double(valueStr) ?? 0
    }

    private static func parseCPUFromTop(_ output: String) -> Double {
        for line in output.components(separatedBy: "\n") {
            if line.contains("CPU usage") {
                // "CPU usage: 5.26% user, 3.41% sys, 91.32% idle"
                if let idleRange = line.range(of: #"(\d+\.?\d*)% idle"#, options: .regularExpression) {
                    let idleStr = line[idleRange].replacingOccurrences(of: "% idle", with: "")
                    if let idle = Double(idleStr) {
                        return 100.0 - idle
                    }
                }
            }
        }
        return 0
    }
}

// Avoid naming conflict with Foundation.ProcessInfo
private enum ProcessInfo_System {
    static let processInfo = Foundation.ProcessInfo.processInfo
}
