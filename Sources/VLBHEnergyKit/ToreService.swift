// ToreService.swift
// VLBHEnergyKit — Service reseau pour le module Tore
// Communique avec le backend VLBH Energy MCP

import Foundation

public final class ToreService: Sendable {
    public static let shared = ToreService()

    private let baseURL: String
    private let session: URLSession

    public init(baseURL: String = "https://vlbh-energy-mcp.onrender.com", session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    // MARK: - Push

    public func pushStockage(_ request: TorePushRequest, token: String) async throws -> Bool {
        let url = URL(string: "\(baseURL)/tore/push")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        req.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await session.data(for: req)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw ToreServiceError.pushFailed(body)
        }
        return true
    }

    // MARK: - Pull

    public func pullStockage(sessionKey: String, token: String) async throws -> TorePullResponse {
        let url = URL(string: "\(baseURL)/tore/pull")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        req.httpBody = try JSONEncoder().encode(TorePullRequest(sessionKey: sessionKey))

        let (data, response) = try await session.data(for: req)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw ToreServiceError.pullFailed(body)
        }
        return try JSONDecoder().decode(TorePullResponse.self, from: data)
    }
}

// MARK: - Errors

public enum ToreServiceError: LocalizedError {
    case pushFailed(String)
    case pullFailed(String)

    public var errorDescription: String? {
        switch self {
        case .pushFailed(let msg): return "Push tore failed: \(msg)"
        case .pullFailed(let msg): return "Pull tore failed: \(msg)"
        }
    }
}
