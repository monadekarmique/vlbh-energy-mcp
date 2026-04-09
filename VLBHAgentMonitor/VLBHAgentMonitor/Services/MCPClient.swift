import Foundation

actor MCPClient {
    private let baseURL: URL
    private let token: String
    private let session: URLSession

    init(baseURL: URL, token: String) {
        self.baseURL = baseURL
        self.token = token

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)
    }

    // MARK: - Health Check

    func checkHealth() async throws -> MCPHealthResponse {
        let url = baseURL.appendingPathComponent("health")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw MCPError.unhealthy
        }

        return try JSONDecoder().decode(MCPHealthResponse.self, from: data)
    }

    // MARK: - Pull Data

    func pullSLM(sessionKey: String) async throws -> [String: Any] {
        return try await post(endpoint: "slm/pull", body: ["sessionKey": sessionKey])
    }

    func pullSLA(sessionKey: String) async throws -> [String: Any] {
        return try await post(endpoint: "sla/pull", body: ["sessionKey": sessionKey])
    }

    func pullSession(sessionKey: String) async throws -> [String: Any] {
        return try await post(endpoint: "session/pull", body: ["sessionKey": sessionKey])
    }

    func pullLead(shamaneCode: String) async throws -> [String: Any] {
        return try await post(endpoint: "lead/pull", body: ["shamaneCode": shamaneCode])
    }

    // MARK: - Generic POST

    private func post(endpoint: String, body: [String: Any]) async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw MCPError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw MCPError.httpError(httpResponse.statusCode)
        }

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw MCPError.invalidJSON
        }

        return json
    }

    // MARK: - Measure Response Time

    func measureEndpoint(_ endpoint: String) async -> (statusCode: Int, responseTime: TimeInterval) {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(token, forHTTPHeaderField: "X-VLBH-Token")

        let start = Date()
        do {
            let (_, response) = try await session.data(for: request)
            let elapsed = Date().timeIntervalSince(start)
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            return (statusCode, elapsed)
        } catch {
            return (0, Date().timeIntervalSince(start))
        }
    }
}

// MARK: - Models

struct MCPHealthResponse: Codable {
    let status: String
    let timestamp: String
}

enum MCPError: Error, LocalizedError {
    case unhealthy
    case invalidResponse
    case httpError(Int)
    case invalidJSON

    var errorDescription: String? {
        switch self {
        case .unhealthy: return "Le serveur MCP ne répond pas"
        case .invalidResponse: return "Réponse invalide du serveur"
        case .httpError(let code): return "Erreur HTTP \(code)"
        case .invalidJSON: return "JSON invalide"
        }
    }
}
