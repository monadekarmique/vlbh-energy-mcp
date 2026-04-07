// SVLBHPanel — Models/ToreModels.swift
// Module Tore : Stockage Énergétique + Couplage Glycémie/Sclérose
// Compatible avec POST /tore/push et /tore/pull (vlbh-energy-mcp)

import Foundation

// MARK: - Champ Toroïdal

struct ChampToroidal: Codable {
    var intensite: Int?
    var coherence: Int?
    var frequence: Double?
    var phase: Phase?

    enum Phase: String, Codable, CaseIterable, Identifiable {
        case repos = "REPOS"
        case charge = "CHARGE"
        case decharge = "DECHARGE"
        case equilibre = "EQUILIBRE"
        var id: String { rawValue }
        var label: String {
            switch self {
            case .repos: return "Repos"
            case .charge: return "Charge"
            case .decharge: return "Décharge"
            case .equilibre: return "Équilibre"
            }
        }
    }
}

// MARK: - Glycémie

struct GlycemieTore: Codable {
    var index: Int?
    var balance: Int?
    var absorption: Int?
    var resistanceScore: Int?
}

// MARK: - Sclérose

struct ScleroseTore: Codable {
    var score: Int?
    var densite: Int?
    var elasticite: Int?
    var permeabilite: Int?
}

// MARK: - Sclérose Tissulaire

struct ScleroseTissulaire: Codable {
    var fibroseIndex: Int?
    var zonesAtteintes: Int?
    var profondeur: Int?
    var revascularisation: Int?
    var decompaction: Int?
}

// MARK: - Couplage

struct CouplageToreGlycemie: Codable {
    var correlationTG: Int?
    var correlationTS: Int?
    var correlationGS: Int?
    var scoreCouplage: Int?
    var fluxNet: Int?
    var phaseCouplage: String?
    var scleroseTissulaire: ScleroseTissulaire?
}

// MARK: - Stockage Énergétique

struct StockageEnergetique: Codable {
    var tore: ChampToroidal?
    var glycemie: GlycemieTore?
    var sclerose: ScleroseTore?
    var couplage: CouplageToreGlycemie?
    var niveau: Int?
    var capacite: Int?
    var tauxRestauration: Int?
    var rendement: Double?
}

// MARK: - API Request / Response

struct TorePushRequest: Codable {
    let sessionKey: String
    let stockage: StockageEnergetique
    var therapistName: String?
    var platform: String = "ios"
}

struct TorePullRequest: Codable {
    let sessionKey: String
}

struct TorePullResponse: Codable {
    let sessionKey: String?
    let stockage: StockageEnergetique?
    let found: Bool
    let timestamp: Int?

    enum CodingKeys: String, CodingKey {
        case sessionKey = "session_key"
        case stockage, found, timestamp
    }
}
