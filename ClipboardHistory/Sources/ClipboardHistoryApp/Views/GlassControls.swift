import SwiftUI

struct GlassPill: View {
    @Environment(\.colorScheme) private var colorScheme
    let isFavorite: Bool
    let favoriteAction: () -> Void
    /// 固定态与固定动作（§5 F-5）。单条记录的固定入口放在这里而不是行上：
    /// 行首的徽标是状态不是控件（`HistoryRowButton` 里那颗星已经是唯一的行内控件了），
    /// 而表头的批量按钮只在多选时出现 —— 没有这一颗，"只固定一条"在界面上做不到。
    let isPinned: Bool
    let pinAction: () -> Void
    /// 「已复制」回执（M7）。这颗按钮平时是"复制"，点下去变成 1.1 秒的勾 ——
    /// 复制成功以前没有任何反馈（只有行位置变化），那是可用性缺口。
    var copyConfirmed: Bool = false
    /// 复制**失败**那一档（R5）。以前失败是"什么都不演"：图标回到原样、界面一句话都没说，
    /// 而 `clipboardWriteErrorMessage` 全仓只有一个 guard 读取点、没有任何显示点 ——
    /// 用户按了、没写进去、接着去别处 ⌘V 粘出旧内容。那是给了一句假话，不是少了一个动画。
    var copyFailed: Bool = false
    let copyAction: () -> Void
    let deleteAction: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            GlassPillButton(
                symbol: FavoriteTogglePresentation.symbolName(isFavorite: isFavorite),
                helpText: FavoriteTogglePresentation.helpText(isFavorite: isFavorite),
                foregroundStyle: isFavorite ? AnyShapeStyle(FavoriteTogglePresentation.favoriteColor) : AnyShapeStyle(.primary),
                replaceSymbol: true,
                // 收藏是"状态被改了"，HIG 给 bounce 的语义就是 "an action occurred"；
                // 它与 replace **同时挂**（见 `SymbolMotion`），不再是二选一。
                bounceValue: isFavorite ? 1 : 0,
                action: favoriteAction
            )

            GlassPillDivider()

            GlassPillButton(
                symbol: PinTogglePresentation.symbolName(isPinned: isPinned),
                helpText: PinTogglePresentation.helpText(isPinned: isPinned),
                foregroundStyle: isPinned ? AnyShapeStyle(.primary) : AnyShapeStyle(.primary.opacity(0.78)),
                replaceSymbol: true,
                bounceValue: isPinned ? 1 : 0,
                action: pinAction
            )

            GlassPillDivider()

            GlassPillButton(symbol: copyFailed ? "exclamationmark"
                                               : (copyConfirmed ? "checkmark" : "doc.on.doc"),
                            helpText: copyFailed ? "复制失败：没能写进剪贴板"
                                : (copyConfirmed ? "已复制到剪贴板" : "再次复制"),
                            // R394：失败只换图标不够 —— 成功/失败两态在颜色上原本完全一样，
                            // 用户要读第二眼才知道「刚才没写进剪贴板」。错误色跟随系统红，
                            // 与横幅/登录失败回执用同一套语言；成功仍是主色，不新造绿色。
                            // R399 CI：R394 的 `Color.red` / 1.0,0.48,0.44 在 runner 的 1x
                            // 字体平滑下只有亮 2.90 / 暗 2.55（地板 3.0）。亮档压深、暗档提亮，
                            // 仍用错误红，不改判据地板。
                            foregroundStyle: copyFailed
                                ? AnyShapeStyle(colorScheme == .dark
                                    ? Color(red: 1.0, green: 0.62, blue: 0.58)
                                    : Color(red: 0.72, green: 0.0, blue: 0.0))
                                : AnyShapeStyle(.primary),
                            // 图标换了要说"换过了"，不是"闪了一下"：14+ 用系统的符号替换过渡，
                            // 12/13 退化成交叉淡入（见 `SymbolMotion`）。
                            replaceSymbol: true,
                            action: copyAction)

            GlassPillDivider()

            GlassPillButton(symbol: "trash", helpText: "删除", action: deleteAction)
        }
        // 收藏与固定是"状态被改了"：这两条事务是 `symbolMotion` 那两臂唯一的供电来源。
        // 以前整个文件只有 hover 一处 `withAnimation`（`:105`），于是 14+ 的符号替换过渡与
        // 12/13 的自绘淡入**都拿不到事务** —— 声明在、图标硬换，看起来像"动效做了没效果"。
        // 复制那颗不挂在这里：它的状态是视图态 `copyConfirmed`，事务在 `DetailView.confirmCopy` 里。
        .animation(MotionCatalog.animation(for: .emphasis), value: isFavorite)
        .animation(MotionCatalog.animation(for: .emphasis), value: isPinned)
        .padding(4)
        .background(VisualMaterial.glass, in: Capsule())
        .clipShape(Capsule())
        .overlay(GlassBorder(shape: Capsule()))
        // 分组合成不在这里写：`visualShadow` 按 `VisualShadow.raised` 的规定自己加 ——
        // "材质必须先合成一次再打阴影"是这条投影定义的一部分，留给调用方就一定会被漏
        // （R0 审计在视频控件那处抓到的就是漏了它）。
        .visualShadow(VisualShadow.raised)
    }
}

/// 胶囊内部的分隔线。
///
/// 抽出来的理由不是省四行：分隔线以前是三处手抄的同一段代码，
/// 宽度 28、高度 1 全是字面量 —— 想改"胶囊的呼吸"就得记得数清有三处，而那没有人会记得。
private struct GlassPillDivider: View {
    var body: some View {
        Rectangle()
            .fill(.separator)
            .frame(width: 28, height: VisualHairline.divider)
    }
}

private struct GlassPillButton: View {
    let symbol: String
    let helpText: String
    var foregroundStyle: AnyShapeStyle = AnyShapeStyle(.primary)
    /// 符号本身会变的按钮（收藏 / 固定 / 已复制）打开这一档：换符号时给一次系统过渡，
    /// 而不是"啪"地换成另一个图标。
    var replaceSymbol = false
    /// "状态被改了"的弹一下（14+，且未开启减弱动态）。只有代表状态的图标才给；
    /// 复制那颗**故意不传** —— 每天上百次的动作按频率闸门不该有弹跳。
    var bounceValue: Int? = nil
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            GlassIconControl(
                symbol: symbol,
                size: 44,
                iconSize: 18,
                foregroundStyle: foregroundStyle,
                replacesSymbol: replaceSymbol,
                bounceValue: bounceValue
            )
        }
        // 按压态（R4）：这四颗是"状态被改了"的控件，点下去必须先有一下"收到了"。
        //
        // R230 把**悬停那一层也交回这一条共享路径**，于是 R20 那段"两层叠加"的修法换了个方向：
        // 以前是"样式让位、自绘那一层算数"（`hoverLevel: 0` + `GlassIconControl` 自己画），
        // 现在是"样式算数、自绘那一层删掉"。理由不是审美，是两笔实测：
        // ① 自绘那一层夹在 `.compositingGroup()` 里，同一枚 `controlHover` 画出来比别家**淡**
        //    —— 帧上亮档 248→230（1.175:1，掉在仓库自己的地板 1.20 之下），
        //    而走共享路径的同一颗 44pt 圆是 248→226（1.220:1）。机制未逐行读，但**换画法读数就动**，
        //    这条分辨实验做得起（R74/R75 那一课：判"接线"要有一正一反两臂）。
        // ② 自绘那一层不走 `HoverInk`，R229 的亮档那一抬落不到它身上 ⇒ "亮档该更重一点"这件事
        //    在同一个控件上有两种说法。
        // 现在全仓的悬停墨只有一条换算、一个定义处（`PressableAppearance.fillOpacity` → `HoverInk`）。
        .pressedStyle(in: Circle(), hoverLevel: VisualFill.controlHover)
        .helpLabel(helpText)
    }
}

/// 胶囊里的一颗图标按钮本体：44pt 圆，只画图标。
///
/// 悬停与按压这两层反馈**不在这里**（R230 起）：由外层 `GlassPillButton` 的 `pressedStyle` 画，
/// 全仓的悬停墨因此只有一条换算、一种混色路径。
///
/// 曾经它还有 `hasOwnSurface` / `showsBorder` 两个开关（自带玻璃底 + 自带描边），
/// 唯一的调用方是 `GlassCircleButton` —— 一颗产品里**零调用点**的独立圆形玻璃按钮，
/// 只被一条测试当符号夹具养着。R1 把那个死表面删了，于是这两个开关各自只剩一种取值，
/// 而"永远为 false 的参数"比没有参数更坏：读者会以为还有第二种用法（见 D-056）。
/// 描边因此只由 `GlassPill` 整块画一次，悬停只改底色 —— 这两件事本来就都只有一种画法。
private struct GlassIconControl: View {
    let symbol: String
    let size: CGFloat
    let iconSize: CGFloat
    var foregroundStyle: AnyShapeStyle = AnyShapeStyle(.primary)
    /// 状态反馈（换符号的连续过渡 / 值变了弹一下）。默认关：
    /// 只有"图标代表一个状态"的那些按钮才开，纯动作按钮不该弹。
    var replacesSymbol = false
    var bounceValue: Int? = nil

    var body: some View {
        content
            .frame(width: size, height: size)
            // R230 这里少了 `.overlay(hoverLayer)`：悬停那一层改由外层的 `pressedStyle` 画
            // （理由与两笔实测见 `GlassPillButton` 那段注释）。
            // 本体现在**不知道悬停这件事** —— 它只画图标，反馈归样式，于是 `isHovered`
            // 与色档两个入参也一起没了：一个视图不该持有它不画的-state。
            .clipShape(Circle())
            .contentShape(Circle())
            .compositingGroup()
    }

    private var content: some View {
        Image(systemName: symbol)
            .font(.system(size: iconSize, weight: .medium))
            // `.hierarchical` 会把多层符号（如 `doc.on.doc`）的次层画淡，于是同一个
            // GlassPill 里三个图标的视觉重量不一致（审计第二轮 1.3 / §3.8）。
            // 单色渲染让每个符号都按前景色满权重画，控件内部才统一。
            .symbolRenderingMode(.monochrome)
            .foregroundStyle(foregroundStyle)
            .symbolMotion(symbol: symbol, replacesSymbol: replacesSymbol, bounceValue: bounceValue)
            .frame(width: size, height: size)
    }
}

/// 玻璃表面的受光描边：一条从左上到右下的淡出。
///
/// 以前它带一个 `isHovered` 参数（悬停时把上端从 0.20 抬到 0.34），
/// 而唯一的实时调用点是 `GlassCircleButton` 里那颗已经删掉的按钮 ——
/// `GlassPill` 自己写死 `isHovered: false`，胶囊整块的描边从来不跟随悬停。
/// 参数于是永远拿同一个值：那是死分支，不是"还没接上"。要接悬停描边就连 R3 的按压态一起做，
/// 到时候这里加回来的是一条**有消费者**的分支。
private struct GlassBorder<S: InsettableShape>: View {
    let shape: S

    var body: some View {
        shape
            .strokeBorder(
                LinearGradient(
                    colors: [
                        Color.primary.opacity(VisualTint.glassBorderTop),
                        Color.primary.opacity(VisualTint.glassBorderBottom)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: VisualHairline.rule
            )
    }
}
