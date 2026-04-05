import Foundation
import SwiftUI

// MARK: - Agent Types

enum AgentType: String, CaseIterable, Identifiable, Codable {
    case superagent = "SuperAgent"
    case makeagent = "MakeAgent"
    case cowork = "Cowork"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .superagent: return "bolt.circle.fill"
        case .makeagent: return "gearshape.2.fill"
        case .cowork: return "person.3.fill"
        }
    }

    var color: Color {
        switch self {
        case .superagent: return .purple
        case .makeagent: return .orange
        case .cowork: return .cyan
        }
    }

    var description: String {
        switch self {
        case .superagent: return "Orchestrateur principal — gère le pipeline MCP et les workflows Make.com"
        case .makeagent: return "Agent Make.com — exécute les scénarios, webhooks et datastores"
        case .cowork: return "Agent collaboratif — synchronise les sessions entre praticiens"
        }
    }
}

// MARK: - Agent Status

enum AgentStatus: String, Codable {
    case idle = "En attente"
    case running = "En cours"
    case processing = "Traitement"
    case error = "Erreur"
    case completed = "Terminé"
    case stalled = "Bloqué"

    var color: Color {
        switch self {
        case .idle: return .secondary
        case .running: return .green
        case .processing: return .blue
        case .error: return .red
        case .completed: return .mint
        case .stalled: return .yellow
        }
    }

    var isActive: Bool {
        self == .running || self == .processing
    }
}

// MARK: - Agent Task

struct AgentTask: Identifiable, Codable {
    let id: UUID
    let name: String
    let agentType: AgentType
    let startedAt: Date
    var completedAt: Date?
    var status: AgentStatus
    var progress: Double // 0.0 - 1.0
    var details: String
    var dataPayload: String?

    var duration: TimeInterval {
        let end = completedAt ?? Date()
        return end.timeIntervalSince(startedAt)
    }

    var durationFormatted: String {
        let d = duration
        if d < 60 { return String(format: "%.1fs", d) }
        if d < 3600 { return String(format: "%.0fm %02.0fs", d / 60, d.truncatingRemainder(dividingBy: 60)) }
        return String(format: "%.0fh %02.0fm", d / 3600, (d / 60).truncatingRemainder(dividingBy: 60))
    }
}

// MARK: - Agent State

struct AgentState: Identifiable {
    let id = UUID()
    let type: AgentType
    var status: AgentStatus = .idle
    var currentTask: AgentTask?
    var taskHistory: [AgentTask] = []
    var cpuUsage: Double = 0.0
    var memoryMB: Double = 0.0
    var memoryHistory: [MemorySample] = []
    var requestsPerMinute: Int = 0
    var totalRequests: Int = 0
    var errorCount: Int = 0
    var lastActivity: Date?
    var pid: Int32?

    var successRate: Double {
        guard totalRequests > 0 else { return 1.0 }
        return Double(totalRequests - errorCount) / Double(totalRequests)
    }

    var hasLeakSuspicion: Bool {
        guard memoryHistory.count >= 10 else { return false }
        let recent = memoryHistory.suffix(10)
        let trend = recent.map(\.megabytes)
        guard let first = trend.first, let last = trend.last else { return false }
        return last > first * 1.3 // 30% growth over recent samples
    }
}

// MARK: - Memory Sample

struct MemorySample: Identifiable, Codable {
    let id: UUID
    let timestamp: Date
    let megabytes: Double
    let residentMB: Double
    let virtualMB: Double

    init(timestamp: Date = Date(), megabytes: Double, residentMB: Double = 0, virtualMB: Double = 0) {
        self.id = UUID()
        self.timestamp = timestamp
        self.megabytes = megabytes
        self.residentMB = residentMB
        self.virtualMB = virtualMB
    }
}

// MARK: - Process Info

struct ProcessInfo: Identifiable {
    let id: Int32 // PID
    let name: String
    var cpuPercent: Double
    var memoryMB: Double
    var residentMB: Double
    var virtualMB: Double
    var threadCount: Int
    var state: String
    var user: String
    var startTime: Date?
    var parentPID: Int32

    var isAgentProcess: Bool {
        let lowerName = name.lowercased()
        return lowerName.contains("python") ||
               lowerName.contains("uvicorn") ||
               lowerName.contains("node") ||
               lowerName.contains("make") ||
               lowerName.contains("vlbh")
    }
}

// MARK: - Leak Report

struct LeakReport: Identifiable {
    let id = UUID()
    let timestamp: Date
    let agentType: AgentType?
    let processName: String
    let pid: Int32
    let initialMemoryMB: Double
    let currentMemoryMB: Double
    let growthRate: Double // MB per minute
    let severity: LeakSeverity
    let samples: [MemorySample]

    var growthPercent: Double {
        guard initialMemoryMB > 0 else { return 0 }
        return ((currentMemoryMB - initialMemoryMB) / initialMemoryMB) * 100
    }
}

enum LeakSeverity: String, CaseIterable {
    case low = "Faible"
    case medium = "Moyen"
    case high = "Élevé"
    case critical = "Critique"

    var color: Color {
        switch self {
        case .low: return .yellow
        case .medium: return .orange
        case .high: return .red
        case .critical: return .pink
        }
    }
}

// MARK: - MCP Endpoint Status

struct MCPEndpointStatus: Identifiable {
    let id = UUID()
    let endpoint: String
    let method: String
    var lastResponseTime: TimeInterval
    var lastStatusCode: Int
    var requestCount: Int
    var errorCount: Int
    var avgResponseTime: TimeInterval
    var lastChecked: Date

    var isHealthy: Bool {
        lastStatusCode >= 200 && lastStatusCode < 300
    }
}

// MARK: - Activity Log Entry

struct ActivityLogEntry: Identifiable {
    let id = UUID()
    let timestamp: Date
    let agent: AgentType
    let message: String
    let level: LogLevel
    let details: String?
}

enum LogLevel: String {
    case info = "INFO"
    case warning = "WARN"
    case error = "ERROR"
    case debug = "DEBUG"

    var color: Color {
        switch self {
        case .info: return .primary
        case .warning: return .yellow
        case .error: return .red
        case .debug: return .secondary
        }
    }
}
