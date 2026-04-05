import Foundation

// MARK: - MakeSyncService Passeport Extension
//
// Replace the existing fetchRatio4D() method in MakeSyncService.swift with this version.
// This parses the full webhook response and populates Passeport4DData.

extension MakeSyncService {

    static let passeportURL = URL(string: "https://hook.eu2.make.com/yn2nkf72r41y45cev2ary98y1ejdtbob")!

    /// Fetch Ratio 4D + full passeport data from Make.com
    func fetchPasseport4D(
        patientId: String,
        pays: String,
        slsaHistorique: Int,
        dateTrauma: String,
        passeport: Passeport4DData
    ) async -> Passeport4DResult? {
        let body: [String: Any] = [
            "patient_id": patientId,
            "pays": pays,
            "slsa_historique": slsaHistorique,
            "date_trauma": dateTrauma
        ]
        do {
            var req = URLRequest(url: Self.passeportURL)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try JSONSerialization.data(withJSONObject: body)
            req.timeoutInterval = 15

            let (data, response) = try await URLSession.shared.data(for: req)
            guard (response as? HTTPURLResponse)?.statusCode == 200 else {
                print("[MakeSyncService] fetchPasseport4D failed: HTTP \((response as? HTTPURLResponse)?.statusCode ?? 0)")
                return nil
            }

            let result = try JSONDecoder().decode(Passeport4DResult.self, from: data)

            await MainActor.run {
                passeport.apply(result, slsaHist: slsaHistorique, trauma: dateTrauma)
            }

            print("[MakeSyncService] fetchPasseport4D -> \(result.ratio_4d)x \(result.cluster) for \(result.pays)")
            return result

        } catch {
            print("[MakeSyncService] fetchPasseport4D error: \(error.localizedDescription)")
            return nil
        }
    }
}

// MARK: - Serialization helpers for push/pull
//
// Add to the existing push serialization block:
//
//   // Passeport 4D
//   if let p = session.passeport, let r = p.ratio4D {
//       lines.append("R4D:\(String(format: "%.2f", r))|\(p.cluster ?? "")|\(p.paysOrigine ?? "")")
//   }
//
// Add to the existing pull parsing block:
//
//   if line.hasPrefix("R4D:") {
//       let parts = String(line.dropFirst(4)).split(separator: "|").map(String.init)
//       if parts.count >= 3, let val = Double(parts[0]) {
//           session.passeport.ratio4D = val
//           session.passeport.cluster = parts[1]
//           session.passeport.paysOrigine = parts[2]
//       }
//       continue
//   }
