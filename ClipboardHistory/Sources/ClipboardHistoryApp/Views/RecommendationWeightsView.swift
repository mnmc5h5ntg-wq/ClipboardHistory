import SwiftUI

struct RecommendationWeightsView: View {
    @ObservedObject var store: RecommendationWeightsStore

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("推荐权重客制化")
                    .font(.headline)

                Spacer()

                Button("恢复默认") {
                    store.restoreDefaults()
                }
            }

            Text("调整各因子对推荐排序的影响力。0% = 禁用，100% = 默认，200% = 双倍。")
                .font(.caption)
                .foregroundStyle(.secondary)

            GroupBox {
                VStack(spacing: 16) {
                    ForEach(RecommendationWeights.Factor.allCases, id: \.self) { factor in
                        WeightSliderRow(
                            factor: factor,
                            value: Binding(
                                get: { store.weights[factor] },
                                set: { newValue in
                                    var w = store.weights
                                    w[factor] = newValue
                                    store.weights = w
                                }
                            )
                        )
                        if factor != RecommendationWeights.Factor.allCases.last {
                            Divider()
                        }
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }
}

private struct WeightSliderRow: View {
    let factor: RecommendationWeights.Factor
    @Binding var value: Double

    private var percentage: String {
        let pct = Int((value * 100).rounded())
        if pct == 100 { return "默认" }
        if pct < 100 { return "\(pct)%" }
        return "\(pct)%"
    }

    private var tintColor: Color {
        if value > 1.0 { return .orange }
        if value < 1.0 { return .secondary }
        return .accentColor
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(factor.label)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Spacer()

                Text(percentage)
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(tintColor)
            }

            Text(factor.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)

            Slider(value: $value, in: 0...2.0, step: 0.05)
        }
    }
}
