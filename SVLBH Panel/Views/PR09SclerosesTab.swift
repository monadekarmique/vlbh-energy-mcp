import SwiftUI

struct PR09SclerosesTab: View {
    @EnvironmentObject var session: SessionState

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(spacing: 3) {
                        Text("\u{25c8} PR 09 : Scl\u{00e9}roses chromatiques")
                            .font(.title2.bold()).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Scl\u{00e9}roses chromatiques multiples")
                            .font(.caption).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.top, 14)

                    VStack(alignment: .leading, spacing: 12) {
                        Divider()
                        Label("Programme en cours de r\u{00e9}daction", systemImage: "doc.text")
                            .font(.headline).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Ce programme de recherche documente les scl\u{00e9}roses chromatiques transg\u{00e9}n\u{00e9}rationnelles multiples, o\u{00f9} plusieurs fr\u{00e9}quences lumineuses sont simultan\u{00e9}ment bloqu\u{00e9}es dans le corps de lumi\u{00e8}re, et les protocoles SVLBH de d\u{00e9}sintrication.")
                            .font(.callout).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.horizontal, 16)
                }
                .padding()
                .padding(.bottom, 80)
            }
            .navigationTitle("PR 09 : Scl\u{00e9}roses")
            .navigationBarTitleDisplayMode(.inline)
        }
        .navigationViewStyle(.stack)
