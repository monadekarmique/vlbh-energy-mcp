import Foundation
import Combine
import SwiftUI

@MainActor
final class AgentCoordinator: ObservableObject {
    @Published var agents: [AgentType: AgentState] = [:]
    @Published var activityLog: [ActivityLogEntry] = []
    @Published var mcpEndpoints: [MCPEndpointStatus] = []
    @Published var mcpConnected: Bool = false
    @Published var mcpBaseURL: String = "https://vlbh-energy-mcp.onrender.com"
    @Published var mcpToken: String = ""

    private var mcpClient: MCPClient?
    private var simulationTimer: Timer?
    private var mcpHealthTimer: Timer?

    init() {
        // Initialize agent states
        for type in AgentType.allCases {
            agents[type] = AgentState(type: type)
        }

        // Initialize MCP endpoints
        mcpEndpoints = [
            MCPEndpointStatus(endpoint: "/health", method: "GET", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/slm/push", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/slm/pull", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/sla/push", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/sla/pull", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/session/push", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/session/pull", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/lead/push", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
            MCPEndpointStatus(endpoint: "/lead/pull", method: "POST", lastResponseTime: 0, lastStatusCode: 0, requestCount: 0, errorCount: 0, avgResponseTime: 0, lastChecked: .distantPast),
        ]
    }

    // MARK: - MCP Connection

    func connectToMCP() {
        guard let url = URL(string: mcpBaseURL), !mcpToken.isEmpty else { return }
        mcpClient = MCPClient(baseURL: url, token: mcpToken)
        startMCPHealthCheck()
        log(.superagent, "Connexion MCP établie vers \(mcpBaseURL)", level: .info)
    }

    func disconnectMCP() {
        mcpHealthTimer?.invalidate()
        mcpHealthTimer = nil
        mcpClient = nil
        mcpConnected = false
        log(.superagent, "Déconnexion MCP", level: .info)
    }

    private func startMCPHealthCheck() {
        mcpHealthTimer?.invalidate()
        mcpHealthTimer = Timer.scheduledTimer(withTimeInterval: 15, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.checkMCPHealth()
            }
        }
        Task { await checkMCPHealth() }
    }

    private func checkMCPHealth() async {
        guard let client = mcpClient else { return }
        do {
            let health = try await client.checkHealth()
            mcpConnected = health.status == "healthy"
            if let idx = mcpEndpoints.firstIndex(where: { $0.endpoint == "/health" }) {
                mcpEndpoints[idx].lastStatusCode = 200
                mcpEndpoints[idx].lastChecked = Date()
                mcpEndpoints[idx].requestCount += 1
            }
        } catch {
            mcpConnected = false
            if let idx = mcpEndpoints.firstIndex(where: { $0.endpoint == "/health" }) {
                mcpEndpoints[idx].lastStatusCode = 0
                mcpEndpoints[idx].errorCount += 1
                mcpEndpoints[idx].lastChecked = Date()
            }
        }
    }

    // MARK: - Agent Simulation (Live Activity Feed)

    func startSimulation() {
        guard simulationTimer == nil else { return }
        simulationTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.simulateTick()
            }
        }
        // Activate all agents
        for type in AgentType.allCases {
            agents[type]?.status = .running
            agents[type]?.lastActivity = Date()
            log(type, "Agent démarré", level: .info)
        }
    }

    func stopSimulation() {
        simulationTimer?.invalidate()
        simulationTimer = nil
        for type in AgentType.allCases {
            agents[type]?.status = .idle
            log(type, "Agent arrêté", level: .info)
        }
    }

    private func simulateTick() {
        for type in AgentType.allCases {
            guard var state = agents[type] else { continue }

            // Simulate varying CPU/memory
            let baseCPU: Double = type == .superagent ? 12 : (type == .makeagent ? 8 : 5)
            let baseMem: Double = type == .superagent ? 180 : (type == .makeagent ? 120 : 95)
            state.cpuUsage = baseCPU + Double.random(in: -3...15)
            state.memoryMB = baseMem + Double.random(in: -10...30)
            state.requestsPerMinute = Int.random(in: 5...45)
            state.totalRequests += state.requestsPerMinute / 20
            state.lastActivity = Date()

            // Add memory sample
            let sample = MemorySample(megabytes: state.memoryMB, residentMB: state.memoryMB * 0.8, virtualMB: state.memoryMB * 2.5)
            state.memoryHistory.append(sample)
            if state.memoryHistory.count > 200 {
                state.memoryHistory.removeFirst()
            }

            // Randomly generate tasks
            if state.currentTask == nil && Double.random(in: 0...1) > 0.7 {
                let task = generateTask(for: type)
                state.currentTask = task
                state.status = .processing
                log(type, "Tâche démarrée: \(task.name)", level: .info, details: task.details)
            } else if var task = state.currentTask {
                task.progress = min(1.0, task.progress + Double.random(in: 0.05...0.25))
                if task.progress >= 1.0 {
                    task.status = .completed
                    task.completedAt = Date()
                    state.taskHistory.insert(task, at: 0)
                    if state.taskHistory.count > 50 { state.taskHistory = Array(state.taskHistory.prefix(50)) }
                    state.currentTask = nil
                    state.status = .running
                    log(type, "Tâche terminée: \(task.name) (\(task.durationFormatted))", level: .info)
                } else {
                    state.currentTask = task
                }
            }

            // Rare errors
            if Double.random(in: 0...1) > 0.95 {
                state.errorCount += 1
                log(type, "Erreur transitoire détectée", level: .error, details: "Timeout ou réponse inattendue")
            }

            agents[type] = state
        }
    }

    private func generateTask(for type: AgentType) -> AgentTask {
        let tasks: [(String, String)]
        switch type {
        case .superagent:
            tasks = [
                ("Pipeline SLM Sync", "Synchronisation des Scores de Lumière via Make.com"),
                ("Orchestration Session", "Coordination des flux session entre praticiens"),
                ("Health Monitor", "Vérification de la santé de tous les endpoints MCP"),
                ("Data Validation", "Validation croisée des scores SLA/SLM"),
                ("Webhook Dispatch", "Dispatch des webhooks push vers Make.com"),
            ]
        case .makeagent:
            tasks = [
                ("Scénario Make #247", "Exécution du scénario de mise à jour datastore"),
                ("Webhook Inbound", "Traitement du webhook entrant depuis SVLBHPanel"),
                ("Datastore Sync", "Synchronisation du datastore 155674"),
                ("SLA Calculation", "Calcul des scores SLA agrégés"),
                ("Export CSV", "Export des données de session en CSV"),
            ]
        case .cowork:
            tasks = [
                ("Session Sync Cornelia", "Sync session praticien #300"),
                ("Session Sync Patrick", "Sync session praticien #455000"),
                ("Lead Update", "Mise à jour du statut lead FORMATION"),
                ("Conflict Resolution", "Résolution de conflit de données entre praticiens"),
                ("Notification Push", "Envoi de notifications aux praticiens actifs"),
            ]
        }

        let (name, details) = tasks.randomElement()!
        return AgentTask(
            id: UUID(),
            name: name,
            agentType: type,
            startedAt: Date(),
            status: .processing,
            progress: 0.0,
            details: details
        )
    }

    // MARK: - Logging

    func log(_ agent: AgentType, _ message: String, level: LogLevel, details: String? = nil) {
        let entry = ActivityLogEntry(
            timestamp: Date(),
            agent: agent,
            message: message,
            level: level,
            details: details
        )
        activityLog.insert(entry, at: 0)
        if activityLog.count > 500 {
            activityLog = Array(activityLog.prefix(500))
        }
    }

    func clearLog() {
        activityLog.removeAll()
    }

    // MARK: - Stats

    var totalActiveAgents: Int {
        agents.values.filter { $0.status.isActive }.count
    }

    var totalRequests: Int {
        agents.values.reduce(0) { $0 + $1.totalRequests }
    }

    var totalErrors: Int {
        agents.values.reduce(0) { $0 + $1.errorCount }
    }

    var overallSuccessRate: Double {
        let total = agents.values.reduce(0) { $0 + $1.totalRequests }
        let errors = agents.values.reduce(0) { $0 + $1.errorCount }
        guard total > 0 else { return 1.0 }
        return Double(total - errors) / Double(total)
    }
}
