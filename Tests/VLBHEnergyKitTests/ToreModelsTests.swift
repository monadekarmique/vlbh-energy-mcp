import XCTest
@testable import VLBHEnergyKit

final class ToreModelsTests: XCTestCase {

    // MARK: - Codable Round-Trip

    func testChampToroidalCodable() throws {
        let original = ChampToroidal(intensite: 50000, coherence: 75, frequence: 7.83, phase: .charge)
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(ChampToroidal.self, from: data)
        XCTAssertEqual(original, decoded)
    }

    func testGlycemieCodable() throws {
        let original = Glycemie(index: 250, balance: 60, absorption: 80, resistanceScore: 500)
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Glycemie.self, from: data)
        XCTAssertEqual(original, decoded)
    }

    func testScleroseCodable() throws {
        let original = Sclerose(score: 300, densite: 50, elasticite: 70, permeabilite: 85)
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Sclerose.self, from: data)
        XCTAssertEqual(original, decoded)
    }

    func testStockageEnergetiqueCodable() throws {
        let stockage = StockageEnergetique(
            tore: ChampToroidal(intensite: 1000, coherence: 90, phase: .equilibre),
            glycemie: Glycemie(index: 100, balance: 50),
            sclerose: Sclerose(score: 200),
            couplage: CouplageToreGlycemie(
                correlationTG: 50,
                correlationTS: -30,
                correlationGS: 10,
                scleroseTissulaire: ScleroseTissulaire(fibroseIndex: 100, zonesAtteintes: 5)
            ),
            niveau: 75000,
            capacite: 100000,
            tauxRestauration: 80
        )
        let data = try JSONEncoder().encode(stockage)
        let decoded = try JSONDecoder().decode(StockageEnergetique.self, from: data)
        XCTAssertEqual(stockage, decoded)
    }

    func testTorePushRequestCodable() throws {
        let request = TorePushRequest(
            sessionKey: "test-session-123",
            stockage: StockageEnergetique(niveau: 5000, capacite: 10000),
            therapistName: "Dr. Test"
        )
        let data = try JSONEncoder().encode(request)
        let decoded = try JSONDecoder().decode(TorePushRequest.self, from: data)
        XCTAssertEqual(decoded.sessionKey, "test-session-123")
        XCTAssertEqual(decoded.platform, "ios")
        XCTAssertEqual(decoded.therapistName, "Dr. Test")
    }

    func testTorePullResponseSnakeCaseDecoding() throws {
        let json = """
        {
            "session_key": "abc-123",
            "stockage": {"niveau": 5000},
            "found": true,
            "timestamp": 1700000000
        }
        """.data(using: .utf8)!

        let response = try JSONDecoder().decode(TorePullResponse.self, from: json)
        XCTAssertEqual(response.sessionKey, "abc-123")
        XCTAssertTrue(response.found)
        XCTAssertEqual(response.stockage?.niveau, 5000)
        XCTAssertEqual(response.timestamp, 1700000000)
    }

    // MARK: - Nil Handling

    func testAllNilFieldsEncodeDecode() throws {
        let stockage = StockageEnergetique()
        let data = try JSONEncoder().encode(stockage)
        let decoded = try JSONDecoder().decode(StockageEnergetique.self, from: data)
        XCTAssertNil(decoded.tore)
        XCTAssertNil(decoded.glycemie)
        XCTAssertNil(decoded.niveau)
        XCTAssertNil(decoded.rendement)
    }

    // MARK: - Phase Enums

    func testPhaseAllCases() {
        XCTAssertEqual(ChampToroidal.Phase.allCases.count, 4)
        XCTAssertEqual(CouplageToreGlycemie.PhaseCouplage.allCases.count, 4)
    }

    func testPhaseRawValues() {
        XCTAssertEqual(ChampToroidal.Phase.repos.rawValue, "REPOS")
        XCTAssertEqual(ChampToroidal.Phase.charge.rawValue, "CHARGE")
        XCTAssertEqual(CouplageToreGlycemie.PhaseCouplage.synergique.rawValue, "SYNERGIQUE")
        XCTAssertEqual(CouplageToreGlycemie.PhaseCouplage.antagoniste.rawValue, "ANTAGONISTE")
    }
}
