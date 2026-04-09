// SVLBHPanel — Services/ToreService.swift
// Service réseau pour le module Tore — push/pull vers vlbh-energy-mcp.onrender.com

import Foundation

final class ToreService {
    static let shared = ToreService()
    private static let baseURL = "https://vlbh-energy-mcp.onrender.com"

    // MARK: - Push

    func push(_ request: TorePushRequest, token: String) async throws -> Bool {
        let url = URL(string: "\(Self.baseURL)/tore/push")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        req.timeoutInterval = 15
        req.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await URLSession.shared.data(for: req)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            let body = String(data: data, encoding: .utf8) ?? "HTTP \(status)"
            throw ToreError.pushFailed(body)
        }
        return true
    }

    // MARK: - Pull

    func pull(sessionKey: String, token: String) async throws -> TorePullResponse {
        let url = URL(string: "\(Self.baseURL)/tore/pull")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(token, forHTTPHeaderField: "X-VLBH-Token")
        req.timeoutInterval = 15
        req.httpBody = try JSONEncoder().encode(TorePullRequest(sessionKey: sessionKey))

        let (data, response) = try await URLSession.shared.data(for: req)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            let body = String(data: data, encoding: .utf8) ?? "HTTP \(status)"
            throw ToreError.pullFailed(body)
        }
        return try JSONDecoder().decode(TorePullResponse.self, from: data)
    }
}

enum ToreError: LocalizedError {
    case pushFailed(String)
    case pullFailed(String)

    var errorDescription: String? {
        switch self {
        case .pushFailed(let msg): return "Push tore: \(msg)"
        case .pullFailed(let msg): return "Pull tore: \(msg)"
        }
    }
}
