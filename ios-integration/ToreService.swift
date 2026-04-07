// ToreService.swift
// SVLBHPanel — Service réseau pour le module Tore
// Communique avec https://vlbh-energy-mcp.onrender.com/tore/

import Foundation

final class ToreService {
    static let shared = ToreService()

    private let baseURL = "https://vlbh-energy-mcp.onrender.com"
    private let session = URLSession.shared

    private var token: String {
        // Récupérer depuis UserDefaults, Keychain, ou config
        UserDefaults.standard.string(forKey: "vlbh_token") ?? ""
    }

    // MARK: - Push

    func pushStockage(_ request: TorePushRequest) async throws -> Bool {
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

    func pullStockage(sessionKey: String) async throws -> TorePullResponse {
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

enum ToreServiceError: LocalizedError {
    case pushFailed(String)
    case pullFailed(String)

    var errorDescription: String? {
        switch self {
        case .pushFailed(let msg): return "Push tore failed: \(msg)"
        case .pullFailed(let msg): return "Pull tore failed: \(msg)"
        }
    }
}
