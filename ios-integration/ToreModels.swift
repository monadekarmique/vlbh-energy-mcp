// ToreModels.swift
// SVLBHPanel — Module Tore : Stockage Énergétique + Couplage Glycémie/Sclérose
// Compatible avec POST /tore/push et /tore/pull

import Foundation

// MARK: - Champ Toroïdal

struct ChampToroidal: Codable {
    var intensite: Int?       // 0–100 000
    var coherence: Int?       // 0–100%
    var frequence: Double?    // 0.01–1000 Hz
    var phase: Phase?

    enum Phase: String, Codable, CaseIterable {
        case repos = "REPOS"
        case charge = "CHARGE"
        case decharge = "DECHARGE"
        case equilibre = "EQUILIBRE"
    }
}

// MARK: - Glycémie

struct Glycemie: Codable {
    var index: Int?             // 0–500
    var balance: Int?           // 0–100%
    var absorption: Int?        // 0–100%
    var resistanceScore: Int?   // 0–1000
}

// MARK: - Sclérose

struct Sclerose: Codable {
    var score: Int?          // 0–1000
    var densite: Int?        // 0–100%
    var elasticite: Int?     // 0–100%
    var permeabilite: Int?   // 0–100%
}

// MARK: - Sclérose Tissulaire

struct ScleroseTissulaire: Codable {
    var fibroseIndex: Int?        // 0–1000
    var zonesAtteintes: Int?      // 0–50
    var profondeur: Int?          // 0–10
    var revascularisation: Int?   // 0–100%
    var decompaction: Int?        // 0–100%
}

// MARK: - Couplage Tore–Glycémie–Sclérose

struct CouplageToreGlycemie: Codable {
    var correlationTG: Int?          // -100 à +100
    var correlationTS: Int?          // -100 à +100
    var correlationGS: Int?          // -100 à +100
    var scoreCouplage: Int?          // 0–10 000 (auto-calc serveur)
    var fluxNet: Int?                // -100 000 à +100 000
    var phaseCouplage: PhaseCouplage?  // auto-inféré serveur
    var scleroseTissulaire: ScleroseTissulaire?

    enum PhaseCouplage: String, Codable, CaseIterable {
        case synergique = "SYNERGIQUE"
        case antagoniste = "ANTAGONISTE"
        case neutre = "NEUTRE"
        case transitoire = "TRANSITOIRE"
    }
}

// MARK: - Stockage Énergétique

struct StockageEnergetique: Codable {
    var tore: ChampToroidal?
    var glycemie: Glycemie?
    var sclerose: Sclerose?
    var couplage: CouplageToreGlycemie?
    var niveau: Int?              // 0–100 000
    var capacite: Int?            // 0–100 000
    var tauxRestauration: Int?    // 0–100%
    var rendement: Double?        // auto-calc serveur: niveau/capacite × 100
}

// MARK: - Push Request

struct TorePushRequest: Codable {
    let sessionKey: String
    let stockage: StockageEnergetique
    var therapistName: String?
    var platform: String = "ios"
}

// MARK: - Pull Request / Response

struct TorePullRequest: Codable {
    let sessionKey: String
}

struct TorePullResponse: Codable {
    let sessionKey: String?
    let stockage: StockageEnergetique?
    let found: Bool
    let timestamp: Int?

    // Snake case mapping from backend
    enum CodingKeys: String, CodingKey {
        case sessionKey = "session_key"
        case stockage
        case found
        case timestamp
    }
}
