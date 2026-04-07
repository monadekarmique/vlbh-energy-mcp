// ToreGlycemieScleroseView.swift
// VLBHEnergyKit — Vue SwiftUI du module Tore dans la section Glycemie/Sclerose

#if canImport(SwiftUI)
import SwiftUI

@available(iOS 16.0, macOS 13.0, *)
public struct ToreGlycemieScleroseView: View {
    @StateObject private var vm = ToreViewModel()

    public init() {}

    public var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // MARK: - Champ Toroidal
                    GroupBox(label: Label("Champ Toroidal", systemImage: "hurricane")) {
                        VStack(spacing: 12) {
                            SliderRow(label: "Intensite", value: $vm.toreIntensite, range: 0...100_000, unit: "")
                            SliderRow(label: "Coherence", value: $vm.toreCoherence, range: 0...100, unit: "%")
                            HStack {
                                Text("Phase")
                                Spacer()
                                Picker("Phase", selection: $vm.torePhase) {
                                    ForEach(ChampToroidal.Phase.allCases, id: \.self) { phase in
                                        Text(phase.rawValue).tag(phase)
                                    }
                                }
                                .pickerStyle(.segmented)
                            }
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Glycemie
                    GroupBox(label: Label("Glycemie", systemImage: "drop.fill")) {
                        VStack(spacing: 12) {
                            SliderRow(label: "Index", value: $vm.glycIndex, range: 0...500, unit: "")
                            SliderRow(label: "Balance", value: $vm.glycBalance, range: 0...100, unit: "%")
                            SliderRow(label: "Absorption", value: $vm.glycAbsorption, range: 0...100, unit: "%")
                            SliderRow(label: "Resistance", value: $vm.glycResistance, range: 0...1000, unit: "")
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Sclerose
                    GroupBox(label: Label("Sclerose", systemImage: "waveform.path.ecg")) {
                        VStack(spacing: 12) {
                            SliderRow(label: "Score", value: $vm.sclScore, range: 0...1000, unit: "")
                            SliderRow(label: "Densite", value: $vm.sclDensite, range: 0...100, unit: "%")
                            SliderRow(label: "Elasticite", value: $vm.sclElasticite, range: 0...100, unit: "%")
                            SliderRow(label: "Permeabilite", value: $vm.sclPermeabilite, range: 0...100, unit: "%")
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Couplage
                    GroupBox(label: Label("Couplage", systemImage: "link.circle.fill")) {
                        VStack(spacing: 12) {
                            CorrelationRow(label: "Tore - Glycemie", value: $vm.corrTG)
                            CorrelationRow(label: "Tore - Sclerose", value: $vm.corrTS)
                            CorrelationRow(label: "Glycemie - Sclerose", value: $vm.corrGS)

                            if let score = vm.scoreCouplage {
                                HStack {
                                    Text("Score couplage")
                                    Spacer()
                                    Text("\(score)")
                                        .fontWeight(.bold)
                                        .foregroundColor(.orange)
                                }
                            }
                            if let phase = vm.phaseCouplage {
                                HStack {
                                    Text("Phase")
                                    Spacer()
                                    PhaseBadge(phase: phase)
                                }
                            }
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Sclerose Tissulaire
                    GroupBox(label: Label("Sclerose Tissulaire", systemImage: "circle.grid.cross.fill")) {
                        VStack(spacing: 12) {
                            SliderRow(label: "Fibrose", value: $vm.stFibrose, range: 0...1000, unit: "")
                            SliderRow(label: "Zones atteintes", value: $vm.stZones, range: 0...50, unit: "")
                            SliderRow(label: "Profondeur", value: $vm.stProfondeur, range: 0...10, unit: "")
                            SliderRow(label: "Revascularisation", value: $vm.stRevasc, range: 0...100, unit: "%")
                            SliderRow(label: "Decompaction", value: $vm.stDecompaction, range: 0...100, unit: "%")
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Stockage Global
                    GroupBox(label: Label("Stockage Energetique", systemImage: "battery.100.bolt")) {
                        VStack(spacing: 12) {
                            SliderRow(label: "Niveau", value: $vm.niveau, range: 0...100_000, unit: "")
                            SliderRow(label: "Capacite", value: $vm.capacite, range: 0...100_000, unit: "")
                            SliderRow(label: "Taux restauration", value: $vm.tauxRest, range: 0...100, unit: "%")

                            if let rendement = vm.rendement {
                                HStack {
                                    Text("Rendement")
                                    Spacer()
                                    Text(String(format: "%.1f%%", rendement))
                                        .fontWeight(.bold)
                                        .foregroundColor(rendement > 70 ? .green : rendement > 40 ? .orange : .red)
                                }
                            }
                        }
                        .padding(.top, 4)
                    }

                    // MARK: - Actions
                    HStack(spacing: 16) {
                        Button(action: { Task { await vm.pull() } }) {
                            Label("Charger", systemImage: "arrow.down.circle.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)

                        Button(action: { Task { await vm.push() } }) {
                            Label("Sauvegarder", systemImage: "arrow.up.circle.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding(.top, 8)

                    if let msg = vm.statusMessage {
                        Text(msg)
                            .font(.caption)
                            .foregroundColor(vm.isError ? .red : .green)
                    }
                }
                .padding()
            }
            .navigationTitle("Tore - Glycemie / Sclerose")
        }
    }
}

// MARK: - Composants UI

@available(iOS 16.0, macOS 13.0, *)
public struct SliderRow: View {
    let label: String
    @Binding var value: Double
    let range: ClosedRange<Double>
    let unit: String

    public var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(label)
                Spacer()
                Text("\(Int(value))\(unit)")
                    .monospacedDigit()
                    .foregroundColor(.secondary)
            }
            Slider(value: $value, in: range)
        }
    }
}

@available(iOS 16.0, macOS 13.0, *)
public struct CorrelationRow: View {
    let label: String
    @Binding var value: Double

    public var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(label)
                Spacer()
                Text("\(Int(value))")
                    .monospacedDigit()
                    .foregroundColor(value > 0 ? .green : value < 0 ? .red : .secondary)
            }
            Slider(value: $value, in: -100...100)
        }
    }
}

@available(iOS 16.0, macOS 13.0, *)
public struct PhaseBadge: View {
    let phase: String

    var color: Color {
        switch phase {
        case "SYNERGIQUE": return .green
        case "ANTAGONISTE": return .red
        case "NEUTRE": return .gray
        case "TRANSITOIRE": return .orange
        default: return .secondary
        }
    }

    public var body: some View {
        Text(phase)
            .font(.caption)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.2))
            .foregroundColor(color)
            .clipShape(Capsule())
    }
}
#endif
