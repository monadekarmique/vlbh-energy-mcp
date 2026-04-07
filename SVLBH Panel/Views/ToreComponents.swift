// SVLBHPanel — Views/ToreComponents.swift
// Composants UI réutilisables pour les onglets Tore (PR05, PR09)

import SwiftUI

// MARK: - Slider

struct ToreSlider: View {
    let label: String
    @Binding var value: Double
    let range: ClosedRange<Double>
    var unit: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(label).font(.callout)
                Spacer()
                Text("\(Int(value))\(unit)")
                    .monospacedDigit()
                    .font(.callout)
                    .foregroundColor(.secondary)
            }
            Slider(value: $value, in: range)
                .tint(Color(hex: "#8B3A62"))
        }
    }
}

// MARK: - Corrélation (-100 → +100)

struct ToreCorrelation: View {
    let label: String
    @Binding var value: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(label).font(.callout)
                Spacer()
                Text("\(Int(value))")
                    .monospacedDigit()
                    .font(.callout)
                    .foregroundColor(value > 0 ? .green : value < 0 ? .red : .secondary)
            }
            Slider(value: $value, in: -100...100)
                .tint(value > 0 ? .green : value < 0 ? .red : .gray)
        }
    }
}

// MARK: - Phase Badge

struct TorePhaseBadge: View {
    let phase: String

    private var color: Color {
        switch phase {
        case "SYNERGIQUE": return .green
        case "ANTAGONISTE": return .red
        case "NEUTRE": return .gray
        case "TRANSITOIRE": return .orange
        default: return .secondary
        }
    }

    var body: some View {
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
