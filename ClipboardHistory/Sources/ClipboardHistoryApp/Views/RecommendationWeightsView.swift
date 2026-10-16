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
                // R98 / BACKLOG 140 的高夹具第一次把这张卡片的**底边**拍进画面，于是量出：
                // `边距=11.5/9.5` 而 `内侧=16.5/18.0/16.5/18.5/…`（亮暗两档同一组数）——
                // 首末两行贴卡片边，比它们彼此之间紧 5~9pt。这正是 R95 在「快捷键」那张上修的
                // 同一个形状，只是当时没人看得见：
                // ① 节奏判据的扫描带写死在 540 那一档（R97 修）；
                // ② 数卡片的源码守卫只扫 `SettingsView.swift`，而这张卡片长在**另一个文件**里，
                //    所以 R95 那次"五处一起补"根本没把它算进名单（本轮开 143 修守卫的覆盖面）。
                // 留白取 `spacing: 12` + 共享的 `.settingsCardInset()`：与其余五张卡片同一档
                //（快捷键 14.0/14.5、隐私 13.5/14.5、数据 14.0/14.5），
                // 而不是给这一张单独配一个"能对上 16"的边缘值 —— 同一个设置窗口里
                // "这几行属于同一组"只准有一种说法。
                VStack(spacing: 12) {
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
                .settingsCardInset()
            }
        }
    }
}

private struct WeightSliderRow: View {
    let factor: RecommendationWeights.Factor
    @Binding var value: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(factor.label)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Spacer()

                Text(WeightValuePresentation.percentageText(value: value))
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

    /// 颜色只表达"这行动过没有"，**不表达数值大小**。
    ///
    /// 旧版是三档：`>1.0` 橙、`<1.0` 次级、`==1.0` 强调蓝。两件事都错：
    /// ① 强调蓝在 macOS 里是"可点"的语言（链接 / 按钮），而这一格是只读文本 ——
    ///    实测它的字形是 #007AFF，而同一页里真正那颗「恢复默认」按钮是中性白字 (223,223,223)，
    ///    颜色把"能点"和"只能看"说反了；9 行全蓝时，这一页看起来像 9 个链接。
    /// ② 橙色是警示色，而 200% 是一个完全合法、说明文字里就写着的取值。
    /// 现在：没动过 = 次级（不抢视线），动过 = 主色（这是用户正在设的那个数）。
    private var tintColor: Color {
        switch WeightValuePresentation.tone(value: value) {
        case .atDefault: return .secondary
        case .raised, .lowered: return .primary
        }
    }
}

/// 权重数值的显示语言。**公开是为了让"文字与颜色出自同一个判断"这件事可测。**
///
/// 为什么要单独拎出来：旧版 `percentage` 里有一条
/// `if pct < 100 { return "\(pct)%" }` 后面紧跟 `return "\(pct)%"` —— 两个分支返回同一个字符串，
/// 说明"改过 / 没改过"这个判断本来就被写过两遍（文字一遍、颜色一遍），而其中一遍已经烂掉了。
/// 现在文字和颜色都从 `Int((value * 100).rounded())` 这一个量出发，四舍五入的边界
/// （0.999 → "100%" → 算"没动过"）只能有一种解释。
enum WeightValuePresentation {
    enum Tone: Equatable {
        case atDefault
        case raised
        case lowered
    }

    static func percent(value: Double) -> Int {
        Int((value * 100).rounded())
    }

    static func percentageText(value: Double) -> String {
        let pct = percent(value: value)
        return pct == 100 ? "默认" : "\(pct)%"
    }

    static func tone(value: Double) -> Tone {
        let pct = percent(value: value)
        if pct == 100 { return .atDefault }
        return pct > 100 ? .raised : .lowered
    }
}
