// ToreModels.swift
// VLBHEnergyKit — Module Tore : Stockage Energetique + Couplage Glycemie/Sclerose
// Compatible avec POST /tore/push et /tore/pull

import Foundation

// MARK: - Champ Toroidal

public struct ChampToroidal: Codable, Equatable, Sendable {
    public var intensite: Int?       // 0-100 000
    public var coherence: Int?       // 0-100%
    public var frequence: Double?    // 0.01-1000 Hz
    public var phase: Phase?

    public enum Phase: String, Codable, CaseIterable, Sendable {
        case repos = "REPOS"
        case charge = "CHARGE"
        case decharge = "DECHARGE"
        case equilibre = "EQUILIBRE"
    }

    public init(intensite: Int? = nil, coherence: Int? = nil, frequence: Double? = nil, phase: Phase? = nil) {
        self.intensite = intensite
        self.coherence = coherence
        self.frequence = frequence
        self.phase = phase
    }
}

// MARK: - Glycemie

public struct Glycemie: Codable, Equatable, Sendable {
    public var index: Int?             // 0-500
    public var balance: Int?           // 0-100%
    public var absorption: Int?        // 0-100%
    public var resistanceScore: Int?   // 0-1000

    public init(index: Int? = nil, balance: Int? = nil, absorption: Int? = nil, resistanceScore: Int? = nil) {
        self.index = index
        self.balance = balance
        self.absorption = absorption
        self.resistanceScore = resistanceScore
    }
}

// MARK: - Sclerose

public struct Sclerose: Codable, Equatable, Sendable {
    public var score: Int?          // 0-1000
    public var densite: Int?        // 0-100%
    public var elasticite: Int?     // 0-100%
    public var permeabilite: Int?   // 0-100%

    public init(score: Int? = nil, densite: Int? = nil, elasticite: Int? = nil, permeabilite: Int? = nil) {
        self.score = score
        self.densite = densite
        self.elasticite = elasticite
        self.permeabilite = permeabilite
    }
}

// MARK: - Sclerose Tissulaire

public struct ScleroseTissulaire: Codable, Equatable, Sendable {
    public var fibroseIndex: Int?        // 0-1000
    public var zonesAtteintes: Int?      // 0-50
    public var profondeur: Int?          // 0-10
    public var revascularisation: Int?   // 0-100%
    public var decompaction: Int?        // 0-100%

    public init(fibroseIndex: Int? = nil, zonesAtteintes: Int? = nil, profondeur: Int? = nil, revascularisation: Int? = nil, decompaction: Int? = nil) {
        self.fibroseIndex = fibroseIndex
        self.zonesAtteintes = zonesAtteintes
        self.profondeur = profondeur
        self.revascularisation = revascularisation
        self.decompaction = decompaction
    }
}

// MARK: - Couplage Tore-Glycemie-Sclerose

public struct CouplageToreGlycemie: Codable, Equatable, Sendable {
    public var correlationTG: Int?          // -100 a +100
    public var correlationTS: Int?          // -100 a +100
    public var correlationGS: Int?          // -100 a +100
    public var scoreCouplage: Int?          // 0-10 000 (auto-calc serveur)
    public var fluxNet: Int?                // -100 000 a +100 000
    public var phaseCouplage: PhaseCouplage?  // auto-infere serveur
    public var scleroseTissulaire: ScleroseTissulaire?

    public enum PhaseCouplage: String, Codable, CaseIterable, Sendable {
        case synergique = "SYNERGIQUE"
        case antagoniste = "ANTAGONISTE"
        case neutre = "NEUTRE"
        case transitoire = "TRANSITOIRE"
    }

    public init(correlationTG: Int? = nil, correlationTS: Int? = nil, correlationGS: Int? = nil, scoreCouplage: Int? = nil, fluxNet: Int? = nil, phaseCouplage: PhaseCouplage? = nil, scleroseTissulaire: ScleroseTissulaire? = nil) {
        self.correlationTG = correlationTG
        self.correlationTS = correlationTS
        self.correlationGS = correlationGS
        self.scoreCouplage = scoreCouplage
        self.fluxNet = fluxNet
        self.phaseCouplage = phaseCouplage
        self.scleroseTissulaire = scleroseTissulaire
    }
}

// MARK: - Stockage Energetique

public struct StockageEnergetique: Codable, Equatable, Sendable {
    public var tore: ChampToroidal?
    public var glycemie: Glycemie?
    public var sclerose: Sclerose?
    public var couplage: CouplageToreGlycemie?
    public var niveau: Int?              // 0-100 000
    public var capacite: Int?            // 0-100 000
    public var tauxRestauration: Int?    // 0-100%
    public var rendement: Double?        // auto-calc serveur: niveau/capacite x 100

    public init(tore: ChampToroidal? = nil, glycemie: Glycemie? = nil, sclerose: Sclerose? = nil, couplage: CouplageToreGlycemie? = nil, niveau: Int? = nil, capacite: Int? = nil, tauxRestauration: Int? = nil, rendement: Double? = nil) {
        self.tore = tore
        self.glycemie = glycemie
        self.sclerose = sclerose
        self.couplage = couplage
        self.niveau = niveau
        self.capacite = capacite
        self.tauxRestauration = tauxRestauration
        self.rendement = rendement
    }
}

// MARK: - Push Request

public struct TorePushRequest: Codable, Sendable {
    public let sessionKey: String
    public let stockage: StockageEnergetique
    public var therapistName: String?
    public var platform: String = "ios"

    public init(sessionKey: String, stockage: StockageEnergetique, therapistName: String? = nil, platform: String = "ios") {
        self.sessionKey = sessionKey
        self.stockage = stockage
        self.therapistName = therapistName
        self.platform = platform
    }
}

// MARK: - Pull Request / Response

public struct TorePullRequest: Codable, Sendable {
    public let sessionKey: String

    public init(sessionKey: String) {
        self.sessionKey = sessionKey
    }
}

public struct TorePullResponse: Codable, Sendable {
    public let sessionKey: String?
    public let stockage: StockageEnergetique?
    public let found: Bool
    public let timestamp: Int?

    enum CodingKeys: String, CodingKey {
        case sessionKey = "session_key"
        case stockage
        case found
        case timestamp
    }
}
