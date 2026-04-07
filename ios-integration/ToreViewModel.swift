// ToreViewModel.swift
// SVLBHPanel — ViewModel pour ToreGlycemieScleroseView

import SwiftUI

@MainActor
final class ToreViewModel: ObservableObject {
    // Champ Toroïdal
    @Published var toreIntensite: Double = 0
    @Published var toreCoherence: Double = 0
    @Published var torePhase: ChampToroidal.Phase = .repos

    // Glycémie
    @Published var glycIndex: Double = 0
    @Published var glycBalance: Double = 0
    @Published var glycAbsorption: Double = 0
    @Published var glycResistance: Double = 0

    // Sclérose
    @Published var sclScore: Double = 0
    @Published var sclDensite: Double = 0
    @Published var sclElasticite: Double = 0
    @Published var sclPermeabilite: Double = 0

    // Couplage
    @Published var corrTG: Double = 0
    @Published var corrTS: Double = 0
    @Published var corrGS: Double = 0
    @Published var scoreCouplage: Int?
    @Published var phaseCouplage: String?

    // Sclérose Tissulaire
    @Published var stFibrose: Double = 0
    @Published var stZones: Double = 0
    @Published var stProfondeur: Double = 0
    @Published var stRevasc: Double = 0
    @Published var stDecompaction: Double = 0

    // Stockage
    @Published var niveau: Double = 0
    @Published var capacite: Double = 0
    @Published var tauxRest: Double = 0
    @Published var rendement: Double?

    // UI State
    @Published var statusMessage: String?
    @Published var isError: Bool = false

    // Session — à connecter avec le gestionnaire de session existant
    var sessionKey: String = ""
    var therapistName: String?

    // MARK: - Push

    func push() async {
        guard !sessionKey.isEmpty else {
            statusMessage = "Aucune session active"
            isError = true
            return
        }

        let request = TorePushRequest(
            sessionKey: sessionKey,
            stockage: buildStockage(),
            therapistName: therapistName,
            platform: "ios"
        )

        do {
            _ = try await ToreService.shared.pushStockage(request)
            statusMessage = "Sauvegardé ✓"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
    }

    // MARK: - Pull

    func pull() async {
        guard !sessionKey.isEmpty else {
            statusMessage = "Aucune session active"
            isError = true
            return
        }

        do {
            let response = try await ToreService.shared.pullStockage(sessionKey: sessionKey)
            guard response.found, let s = response.stockage else {
                statusMessage = "Aucune donnée trouvée"
                isError = true
                return
            }
            applyStockage(s)
            statusMessage = "Chargé ✓"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
    }

    // MARK: - Build / Apply

    private func buildStockage() -> StockageEnergetique {
        StockageEnergetique(
            tore: ChampToroidal(
                intensite: Int(toreIntensite),
                coherence: Int(toreCoherence),
                frequence: nil,
                phase: torePhase
            ),
            glycemie: Glycemie(
                index: Int(glycIndex),
                balance: Int(glycBalance),
                absorption: Int(glycAbsorption),
                resistanceScore: Int(glycResistance)
            ),
            sclerose: Sclerose(
                score: Int(sclScore),
                densite: Int(sclDensite),
                elasticite: Int(sclElasticite),
                permeabilite: Int(sclPermeabilite)
            ),
            couplage: CouplageToreGlycemie(
                correlationTG: Int(corrTG),
                correlationTS: Int(corrTS),
                correlationGS: Int(corrGS),
                scoreCouplage: nil,   // auto-calc serveur
                fluxNet: nil,
                phaseCouplage: nil,   // auto-inféré serveur
                scleroseTissulaire: ScleroseTissulaire(
                    fibroseIndex: Int(stFibrose),
                    zonesAtteintes: Int(stZones),
                    profondeur: Int(stProfondeur),
                    revascularisation: Int(stRevasc),
                    decompaction: Int(stDecompaction)
                )
            ),
            niveau: Int(niveau),
            capacite: Int(capacite),
            tauxRestauration: Int(tauxRest),
            rendement: nil  // auto-calc serveur
        )
    }

    private func applyStockage(_ s: StockageEnergetique) {
        if let t = s.tore {
            toreIntensite = Double(t.intensite ?? 0)
            toreCoherence = Double(t.coherence ?? 0)
            torePhase = t.phase ?? .repos
        }
        if let g = s.glycemie {
            glycIndex = Double(g.index ?? 0)
            glycBalance = Double(g.balance ?? 0)
            glycAbsorption = Double(g.absorption ?? 0)
            glycResistance = Double(g.resistanceScore ?? 0)
        }
        if let sc = s.sclerose {
            sclScore = Double(sc.score ?? 0)
            sclDensite = Double(sc.densite ?? 0)
            sclElasticite = Double(sc.elasticite ?? 0)
            sclPermeabilite = Double(sc.permeabilite ?? 0)
        }
        if let cp = s.couplage {
            corrTG = Double(cp.correlationTG ?? 0)
            corrTS = Double(cp.correlationTS ?? 0)
            corrGS = Double(cp.correlationGS ?? 0)
            scoreCouplage = cp.scoreCouplage
            phaseCouplage = cp.phaseCouplage?.rawValue
            if let st = cp.scleroseTissulaire {
                stFibrose = Double(st.fibroseIndex ?? 0)
                stZones = Double(st.zonesAtteintes ?? 0)
                stProfondeur = Double(st.profondeur ?? 0)
                stRevasc = Double(st.revascularisation ?? 0)
                stDecompaction = Double(st.decompaction ?? 0)
            }
        }
        niveau = Double(s.niveau ?? 0)
        capacite = Double(s.capacite ?? 0)
        tauxRest = Double(s.tauxRestauration ?? 0)
        rendement = s.rendement
    }
}
