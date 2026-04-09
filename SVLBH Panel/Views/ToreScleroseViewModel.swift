// SVLBHPanel — Views/ToreScleroseViewModel.swift
// ViewModel pour PR09SclerosesTab

import SwiftUI

@MainActor
final class ToreScleroseViewModel: ObservableObject {
    // Sclérose globale
    @Published var sclScore: Double = 0
    @Published var sclDensite: Double = 0
    @Published var sclElasticite: Double = 0
    @Published var sclPermeabilite: Double = 0

    // Sclérose Tissulaire
    @Published var stFibrose: Double = 0
    @Published var stZones: Double = 0
    @Published var stProfondeur: Double = 0
    @Published var stRevasc: Double = 0
    @Published var stDecompaction: Double = 0

    // Couplage
    @Published var corrTS: Double = 0
    @Published var corrGS: Double = 0
    @Published var scoreCouplage: Int?
    @Published var phaseCouplage: String?

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
            statusMessage = "Sclérose sauvegardée"
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
            statusMessage = "Sclérose chargée"
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
            sclerose: ScleroseTore(
                score: Int(sclScore),
                densite: Int(sclDensite),
                elasticite: Int(sclElasticite),
                permeabilite: Int(sclPermeabilite)
            ),
            couplage: CouplageToreGlycemie(
                correlationTS: Int(corrTS),
                correlationGS: Int(corrGS),
                scleroseTissulaire: ScleroseTissulaire(
                    fibroseIndex: Int(stFibrose),
                    zonesAtteintes: Int(stZones),
                    profondeur: Int(stProfondeur),
                    revascularisation: Int(stRevasc),
                    decompaction: Int(stDecompaction)
                )
            )
        )
    }

    // MARK: - Apply

    private func applyStockage(_ s: StockageEnergetique) {
        if let sc = s.sclerose {
            sclScore = Double(sc.score ?? 0)
            sclDensite = Double(sc.densite ?? 0)
            sclElasticite = Double(sc.elasticite ?? 0)
            sclPermeabilite = Double(sc.permeabilite ?? 0)
        }
        if let cp = s.couplage {
            corrTS = Double(cp.correlationTS ?? 0)
            corrGS = Double(cp.correlationGS ?? 0)
            scoreCouplage = cp.scoreCouplage
            phaseCouplage = cp.phaseCouplage
            if let st = cp.scleroseTissulaire {
                stFibrose = Double(st.fibroseIndex ?? 0)
                stZones = Double(st.zonesAtteintes ?? 0)
                stProfondeur = Double(st.profondeur ?? 0)
                stRevasc = Double(st.revascularisation ?? 0)
                stDecompaction = Double(st.decompaction ?? 0)
            }
        }
    }
}
