// SVLBHPanel — Views/PR05GlycemiesTab.swift
// PR 05 : Glycémies — Intégration du champ toroïdal

import SwiftUI

struct PR05GlycemiesTab: View {
    @EnvironmentObject var session: SessionState
    @StateObject private var vm = ToreGlycemieViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // En-tête
                    VStack(spacing: 3) {
                        Text("\u{25c8} PR 05 : Glycémies")
                            .font(.title2.bold()).foregroundColor(Color(hex: "#8B3A62"))
                        Text("Stockage énergétique — Champ toroïdal × Glycémie")
                            .font(.caption).foregroundColor(Color(hex: "#333333"))
                    }
                    .padding(.top, 14)

                    // MARK: - Champ Toroïdal
                    GroupBox(label: Label("Champ Toroïdal hDOM", systemImage: "hurricane")) {
                        VStack(spacing: 12) {
                            ToreSlider(label: "Intensité", value: $vm.toreIntensite, range: 0...100_000)
                            ToreSlider(label: "Cohérence", value: $vm.toreCoherence, range: 0...100, unit: "%")

                            HStack {
                                Text("Phase").font(.callout)
                                Spacer()
                                Picker("Phase", selection: $vm.torePhase) {
                                    ForEach(ChampToroidal.Phase.allCases) { phase in
                                        Text(phase.label).tag(phase)
                                    }
                                }
                                .pickerStyle(.segmented)
                            }
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Glycémie
                    GroupBox(label: Label("Marqueurs Glycémiques", systemImage: "drop.fill")) {
                        VStack(spacing: 12) {
                            ToreSlider(label: "Index glycémique", value: $vm.glycIndex, range: 0...500)
                            ToreSlider(label: "Balance", value: $vm.glycBalance, range: 0...100, unit: "%")
                            ToreSlider(label: "Absorption", value: $vm.glycAbsorption, range: 0...100, unit: "%")
                            ToreSlider(label: "Résistance insulinique", value: $vm.glycResistance, range: 0...1000)
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Couplage Tore↔Glycémie
                    GroupBox(label: Label("Couplage Tore ↔ Glycémie", systemImage: "link.circle.fill")) {
                        VStack(spacing: 12) {
                            ToreCorrelation(label: "Corrélation T↔G", value: $vm.corrTG)

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

                    // MARK: - Stockage
                    GroupBox(label: Label("Stockage Énergétique", systemImage: "battery.100.bolt")) {
                        VStack(spacing: 12) {
                            ToreSlider(label: "Niveau", value: $vm.niveau, range: 0...100_000)
                            ToreSlider(label: "Capacité", value: $vm.capacite, range: 0...100_000)
                            ToreSlider(label: "Taux restauration", value: $vm.tauxRest, range: 0...100, unit: "%")

                            if let r = vm.rendement {
                                HStack {
                                    Text("Rendement").font(.callout)
                                    Spacer()
                                    Text(String(format: "%.1f%%", r))
                                        .fontWeight(.bold)
                                        .foregroundColor(r > 70 ? .green : r > 40 ? .orange : .red)
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
            .navigationTitle("PR 05 : Glycémies")
            .navigationBarTitleDisplayMode(.inline)
        }
        .navigationViewStyle(.stack)
