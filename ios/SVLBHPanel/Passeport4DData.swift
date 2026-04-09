import SwiftUI

// MARK: - Passeport 4D Data Model

/// Holds the full Ratio 4D response from Make.com webhook
struct Passeport4DResult: Codable {
    let ratio_4d: Double
    let cluster: String
    let slsa_ch_baseline: Int
    let sltda_origine: Int
    let sltda_ch: Int
    let pays: String
}

/// Observable wrapper stored in SessionState
class Passeport4DData: ObservableObject {
    @Published var ratio4D: Double?
    @Published var cluster: String?
    @Published var paysOrigine: String?
    @Published var slsaHistorique: Int?
    @Published var slsaChBaseline: Int?
    @Published var sltdaOrigine: Int?
    @Published var sltdaCh: Int?
    @Published var dateTrauma: String?

    func apply(_ result: Passeport4DResult, slsaHist: Int, trauma: String) {
        ratio4D = result.ratio_4d
        cluster = result.cluster
        paysOrigine = result.pays
        slsaHistorique = slsaHist
        slsaChBaseline = result.slsa_ch_baseline
        sltdaOrigine = result.sltda_origine
        sltdaCh = result.sltda_ch
        dateTrauma = trauma
    }

    /// Color for the ratio badge
    var ratioColor: Color {
        guard let r = ratio4D else { return .gray }
        if r <= 3 { return .green }
        if r <= 10 { return .orange }
        return .pink
    }

    /// Cluster display with accents restored
    var clusterDisplay: String {
        guard let c = cluster else { return "" }
        return c.replacingOccurrences(of: "Hypersensibilite extreme", with: "Hypersensibilit\u{00e9} extr\u{00ea}me")
                .replacingOccurrences(of: "Sensibilite active", with: "Sensibilit\u{00e9} active")
    }
}
