// SVLBHPanel — Views/ToreGlycemieViewModel.swift
// ViewModel pour PR05GlycemiesTab

import SwiftUI

@MainActor
final class ToreGlycemieViewModel: ObservableObject {
    // Champ Toroïdal
    @Published var toreIntensite: Double = 0
    @Published var toreCoherence: Double = 0
    @Published var torePhase: ChampToroidal.Phase = .repos

    // Glycémie
    @Published var glycIndex: Double = 0
    @Published var glycBalance: Double = 0
    @Published var glycAbsorption: Double = 0
    @Published var glycResistance: Double = 0

    // Couplage
    @Published var corrTG: Double = 0
    @Published var scoreCouplage: Int?
    @Published var phaseCouplage: String?

    // Stockage
    @Published var niveau: Double = 0
    @Published var capacite: Double = 0
    @Published var tauxRest: Double = 0
    @Published var rendement: Double?

    // UI
    @Published var statusMessage: String?
    @Published var isError = false
    @Published var isLoading = false

    private var vlbhToken: String {
        UserDefaults.standard.string(forKey: "vlbh_token") ?? ""
    }

    // MARK: - Push

    func push(session: SessionState) async {
        let key = session.pushKey
        guard !key.isEmpty else {
            statusMessage = "Aucune session active"
            isError = true
            return
        }
        isLoading = true
        let request = TorePushRequest(
            sessionKey: key,
            stockage: buildStockage(),
            therapistName: session.role.displayName,
            platform: "ios"
        )
        do {
            _ = try await ToreService.shared.push(request, token: vlbhToken)
            statusMessage = "Glycémie sauvegardée"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
        isLoading = false
    }

    // MARK: - Pull

    func pull(session: SessionState) async {
        let key = session.pushKey
        guard !key.isEmpty else {
            statusMessage = "Aucune session active"
            isError = true
            return
        }
        isLoading = true
        do {
            let resp = try await ToreService.shared.pull(sessionKey: key, token: vlbhToken)
            guard resp.found, let s = resp.stockage else {
                statusMessage = "Aucune donnée trouvée"
                isError = true
                isLoading = false
                return
            }
            applyStockage(s)
            statusMessage = "Glycémie chargée"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
        isLoading = false
    }

    // MARK: - Build

    private func buildStockage() -> StockageEnergetique {
        StockageEnergetique(
            tore: ChampToroidal(
                intensite: Int(toreIntensite),
                coherence: Int(toreCoherence),
                phase: torePhase
            ),
            glycemie: GlycemieTore(
                index: Int(glycIndex),
                balance: Int(glycBalance),
                absorption: Int(glycAbsorption),
                resistanceScore: Int(glycResistance)
            ),
            couplage: CouplageToreGlycemie(
                correlationTG: Int(corrTG)
            ),
            niveau: Int(niveau),
            capacite: Int(capacite),
            tauxRestauration: Int(tauxRest)
        )
    }

    // MARK: - Apply

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
        if let cp = s.couplage {
            corrTG = Double(cp.correlationTG ?? 0)
            scoreCouplage = cp.scoreCouplage
            phaseCouplage = cp.phaseCouplage
        }
        niveau = Double(s.niveau ?? 0)
        capacite = Double(s.capacite ?? 0)
        tauxRest = Double(s.tauxRestauration ?? 0)
        rendement = s.rendement
    }
}
