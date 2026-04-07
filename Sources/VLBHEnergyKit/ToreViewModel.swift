// ToreViewModel.swift
// VLBHEnergyKit — ViewModel pour ToreGlycemieScleroseView

#if canImport(SwiftUI)
import SwiftUI

@available(iOS 16.0, macOS 13.0, *)
@MainActor
public final class ToreViewModel: ObservableObject {
    // Champ Toroidal
    @Published public var toreIntensite: Double = 0
    @Published public var toreCoherence: Double = 0
    @Published public var torePhase: ChampToroidal.Phase = .repos

    // Glycemie
    @Published public var glycIndex: Double = 0
    @Published public var glycBalance: Double = 0
    @Published public var glycAbsorption: Double = 0
    @Published public var glycResistance: Double = 0

    // Sclerose
    @Published public var sclScore: Double = 0
    @Published public var sclDensite: Double = 0
    @Published public var sclElasticite: Double = 0
    @Published public var sclPermeabilite: Double = 0

    // Couplage
    @Published public var corrTG: Double = 0
    @Published public var corrTS: Double = 0
    @Published public var corrGS: Double = 0
    @Published public var scoreCouplage: Int?
    @Published public var phaseCouplage: String?

    // Sclerose Tissulaire
    @Published public var stFibrose: Double = 0
    @Published public var stZones: Double = 0
    @Published public var stProfondeur: Double = 0
    @Published public var stRevasc: Double = 0
    @Published public var stDecompaction: Double = 0

    // Stockage
    @Published public var niveau: Double = 0
    @Published public var capacite: Double = 0
    @Published public var tauxRest: Double = 0
    @Published public var rendement: Double?

    // UI State
    @Published public var statusMessage: String?
    @Published public var isError: Bool = false

    // Session
    public var sessionKey: String = ""
    public var therapistName: String?

    private let service: ToreService
    private let tokenProvider: () -> String

    public init(service: ToreService = .shared, tokenProvider: @escaping () -> String = { UserDefaults.standard.string(forKey: "vlbh_token") ?? "" }) {
        self.service = service
        self.tokenProvider = tokenProvider
    }

    // MARK: - Push

    public func push() async {
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
            _ = try await service.pushStockage(request, token: tokenProvider())
            statusMessage = "Sauvegarde OK"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
    }

    // MARK: - Pull

    public func pull() async {
        guard !sessionKey.isEmpty else {
            statusMessage = "Aucune session active"
            isError = true
            return
        }

        do {
            let response = try await service.pullStockage(sessionKey: sessionKey, token: tokenProvider())
            guard response.found, let s = response.stockage else {
                statusMessage = "Aucune donnee trouvee"
                isError = true
                return
            }
            applyStockage(s)
            statusMessage = "Charge OK"
            isError = false
        } catch {
            statusMessage = error.localizedDescription
            isError = true
        }
    }

    // MARK: - Build / Apply

    public func buildStockage() -> StockageEnergetique {
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
                scoreCouplage: nil,
                fluxNet: nil,
                phaseCouplage: nil,
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
            rendement: nil
        )
    }

    public func applyStockage(_ s: StockageEnergetique) {
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
#endif
