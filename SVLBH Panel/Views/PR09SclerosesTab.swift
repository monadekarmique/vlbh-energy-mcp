// SVLBHPanel — Views/PR09SclerosesTab.swift
// PR 09 : Scléroses — Intégration du champ toroïdal + sclérose tissulaire

import SwiftUI

struct PR09SclerosesTab: View {
    @EnvironmentObject var session: SessionState
    @StateObject private var vm = ToreScleroseViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // En-tête
                    VStack(spacing: 3) {
                        Text("\u{25c8} PR 09 : Scléroses chromatiques")
                            .font(.title2.bold()).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Sclérose tissulaire — Couplage toroïdal × Sclérose")
                            .font(.caption).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.top, 14)

                    // MARK: - Sclérose globale
                    GroupBox(label: Label("Sclérose Chromatique", systemImage: "waveform.path.ecg")) {
                        VStack(spacing: 12) {
                            ToreSlider(label: "Score global", value: $vm.sclScore, range: 0...1000)
                            ToreSlider(label: "Densité tissulaire", value: $vm.sclDensite, range: 0...100, unit: "%")
                            ToreSlider(label: "Élasticité résiduelle", value: $vm.sclElasticite, range: 0...100, unit: "%")
                            ToreSlider(label: "Perméabilité membranaire", value: $vm.sclPermeabilite, range: 0...100, unit: "%")
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Sclérose Tissulaire détaillée
                    GroupBox(label: Label("Cartographie Tissulaire", systemImage: "circle.grid.cross.fill")) {
                        VStack(spacing: 12) {
                            ToreSlider(label: "Indice de fibrose", value: $vm.stFibrose, range: 0...1000)
                            ToreSlider(label: "Zones atteintes", value: $vm.stZones, range: 0...50)
                            ToreSlider(label: "Profondeur (couches)", value: $vm.stProfondeur, range: 0...10)
                            ToreSlider(label: "Revascularisation post-tore", value: $vm.stRevasc, range: 0...100, unit: "%")
                            ToreSlider(label: "Décompaction tissulaire", value: $vm.stDecompaction, range: 0...100, unit: "%")
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Couplage Tore↔Sclérose
                    GroupBox(label: Label("Couplage Tore ↔ Sclérose", systemImage: "link.circle.fill")) {
                        VStack(spacing: 12) {
                            ToreCorrelation(label: "Corrélation T↔S", value: $vm.corrTS)
                            ToreCorrelation(label: "Corrélation G↔S", value: $vm.corrGS)

                            if let score = vm.scoreCouplage {
                                HStack {
                                    Text("Score couplage").font(.callout)
                                    Spacer()
                                    Text("\(score)")
                                        .fontWeight(.bold)
                                        .foregroundColor(.orange)
                                }
                            }
                            if let phase = vm.phaseCouplage {
                                HStack {
                                    Text("Phase").font(.callout)
                                    Spacer()
                                    TorePhaseBadge(phase: phase)
                                }
                            }
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Actions
                    HStack(spacing: 16) {
                        Button(action: { Task { await vm.pull(session: session) } }) {
                            Label("Charger", systemImage: "arrow.down.circle.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                        .disabled(vm.isLoading)

                        Button(action: { Task { await vm.push(session: session) } }) {
                            Label("Sauvegarder", systemImage: "arrow.up.circle.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(Color(hex: "#8B3A62"))
                        .disabled(vm.isLoading)
                    }

                    if let msg = vm.statusMessage {
                        Text(msg)
                            .font(.caption)
                            .foregroundColor(vm.isError ? .red : .green)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding()
                .padding(.bottom, 80)
            }
            .navigationTitle("PR 09 : Scléroses")
            .navigationBarTitleDisplayMode(.inline)
        }
        .navigationViewStyle(.stack)
