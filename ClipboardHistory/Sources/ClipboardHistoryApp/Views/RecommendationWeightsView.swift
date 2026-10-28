import SwiftUI

struct RecommendationWeightsView: View {
    @ObservedObject var store: RecommendationWeightsStore

    /// R99 / BACKLOG 142：二级标题那一行与说明段**搬进卡片**（只动容器，一行行为都没改）。
    ///
    /// 缺陷是量出来的，不是看代码看出来的。`testSettingsCardVerticalRhythmIsOneNumber`
    /// 新增的那格"卡片之外还剩几段墨"在两档 × 十屏上给出：
    ///   上方 —— 九屏各 **1** 段（78.5..90.5pt，就是分区标题那一行），
    ///          唯独这一屏 **3** 段：多出来 112.5..124.5pt（「推荐权重客制化」+「恢复默认」）
    ///          与 146.0..155.0pt（那句说明）；
    ///   下方 —— 其余各屏 0 段，这一屏 1040 那一档 2 段（885.0..895.0、911.5..923.5）。
    /// 也就是说：同一扇设置窗口里，"这一段属于那一组"这句话有**两种说法** ——
    /// 「数据」「隐私」「快捷键」把小标题、说明、动作按钮都放在 `GroupBox` 里面
    ///（见 `SettingsView` 的 `历史记录存储` / `清空未收藏记录` 那两段：
    /// `VStack(spacing: 8){标题; 说明}` + 卡片内 `Divider()`），
    /// 而这一屏把它们挂在卡片外面。R92 当年给「数据」屏做的就是同一件事：
    /// "向多数靠拢，只动容器"。
    ///
    /// 字号跟着改成 `.subheadline`：搬进卡片之后它就是卡片内的小标题，
    /// 与「历史记录存储」「导出与导入」同一档；留着 `.headline` 会让卡片里外出现两种标题。
    var body: some View {
        GroupBox {
            VStack(spacing: 12) {
                // 形状抄「数据」那一屏的 `清空未收藏记录` 那一段：
                // `HStack(alignment: .center){ VStack{标题; 说明}; Spacer(); 按钮 }`。
                // 为什么不是"标题与按钮同一行、说明在下一行"（本轮第一版就是这么写的）：
                // 那样这一行最高的元素是那颗 22pt 的按钮，标题被往下推 4pt ⇒
                // 卡片顶到第一行墨 18.5pt，而卡片底那侧 12.5pt，极差 6.0 被
                // `testSettingsCardVerticalRhythmIsOneNumber` 的 4.5pt 判红。
                // 标题+说明一起放进左侧那块之后，文字块本身比按钮高，
                // 行的顶就是标题的墨顶 ⇒ 边距回到 14.0（实测两档都是 14.0：亮 14.0/12.5、暗 14.0/12.0），
                // 与其余五张卡片同一档。
                HStack(alignment: .center, spacing: 12) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("推荐权重客制化")
                            .font(.subheadline)

                        Text("调整各因子对推荐排序的影响力。0% = 禁用，100% = 默认，200% = 双倍。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    HStack(spacing: 0) {
                        Button("恢复默认") {
                            Self.resetDefaults(in: store)
                        }
                    // R382：权重全默认时这颗按钮点了不产生任何变化 —— 禁用态是它唯一诚实的呈现。
                    // 判据不是「有没有写 .disabled」，而是同一颗按钮在默认/动过两帧里的**标签墨**
                    // 必须读得出差别（`testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault`）。
                    .disabled(store.weights == .default)
                    // R388：样式自己演 primary↔secondary，禁用标签停在可读的 secondary。
                    .buttonStyle(ResetDefaultButtonStyle())
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Divider()

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

    /// R389：一次复位会同时搬动九根滑杆。按钮自己那点色变已经在演，滑杆却瞬移 ⇒
    /// 两件事说的是「一次操作」和「九次跳变」。把复位收进同一条位移档：胶片现读 2x 过渡 5 帧、
    /// 1x 过渡 13 帧（声明 200ms），直接拖滑杆不走这条路、不会拖出延迟。
    static func resetDefaults(in store: RecommendationWeightsStore) {
        withAnimation(MotionCatalog.animation(for: .slider)) {
            store.restoreDefaults()
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
                // R452：0–200% 的量程里，100% 默认位没有可见参照（原生只有一排 1pt 小点）。
                // 中心下方加一条 1×5pt 的短刻度，滑杆移开后仍能看到"默认在哪"。
                .overlay(alignment: .center) {
                    Capsule()
                        .fill(Color.secondary.opacity(0.55))
                        .frame(width: 1, height: 5)
                        .offset(y: 9)
                        .allowsHitTesting(false)
                }
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
