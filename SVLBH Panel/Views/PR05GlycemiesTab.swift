import SwiftUI

struct PR05GlycemiesTab: View {
    @EnvironmentObject var session: SessionState

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(spacing: 3) {
                        Text("\u{25c8} PR 05 : Glyc\u{00e9}mies")
                            .font(.title2.bold()).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Glyc\u{00e9}mies I, II")
                            .font(.caption).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.top, 14)

                    VStack(alignment: .leading, spacing: 12) {
                        Divider()
                        Label("Programme en cours de r\u{00e9}daction", systemImage: "doc.text")
                            .font(.headline).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Ce programme de recherche explore les signatures vibratoires des d\u{00e9}s\u{00e9}quilibres glyc\u{00e9}miques de type I et II, leurs racines transg\u{00e9}n\u{00e9}rationnelles et les protocoles SVLBH de r\u{00e9}\u{00e9}quilibrage.")
                            .font(.callout).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.horizontal, 16)
                }
                .padding()
                .padding(.bottom, 80)
            }
            .navigationTitle("PR 05 : Glyc\u{00e9}mies")
            .navigationBarTitleDisplayMode(.inline)
        }
        .navigationViewStyle(.stack)
