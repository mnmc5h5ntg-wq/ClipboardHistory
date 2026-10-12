import SwiftUI

struct GlassCircleButton: View {
    let symbol: String
    let helpText: String
    var foregroundStyle: AnyShapeStyle = AnyShapeStyle(.primary)
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            GlassIconControl(
                symbol: symbol,
                size: 44,
                iconSize: 16,
                isHovered: isHovered,
                hasOwnSurface: true,
                showsBorder: true,
                foregroundStyle: foregroundStyle
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(MotionCatalog.animation(for: .hover)) {
                isHovered = hovering
            }
        }
        .helpLabel(helpText)
        .shadow(color: .black.opacity(0.10), radius: 8, y: 3)
    }
}

struct GlassPill: View {
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

            Rectangle()
                .fill(.separator)
                .frame(width: 28, height: 1)

            GlassPillButton(
                symbol: PinTogglePresentation.symbolName(isPinned: isPinned),
                helpText: PinTogglePresentation.helpText(isPinned: isPinned),
                foregroundStyle: isPinned ? AnyShapeStyle(.primary) : AnyShapeStyle(.primary.opacity(0.78)),
                replaceSymbol: true,
                bounceValue: isPinned ? 1 : 0,
                action: pinAction
            )

            Rectangle()
                .fill(.separator)
                .frame(width: 28, height: 1)

            GlassPillButton(symbol: copyConfirmed ? "checkmark" : "doc.on.doc",
                            helpText: copyConfirmed ? "已复制到剪贴板" : "再次复制",
                            // 图标换了要说"换过了"，不是"闪了一下"：14+ 用系统的符号替换过渡，
                            // 12/13 退化成交叉淡入（见 `SymbolMotion`）。
                            replaceSymbol: true,
                            action: copyAction)

            Rectangle()
                .fill(.separator)
                .frame(width: 28, height: 1)

            GlassPillButton(symbol: "trash", helpText: "删除", action: deleteAction)
        }
        .padding(4)
        .background(.ultraThinMaterial, in: Capsule())
        .clipShape(Capsule())
        .overlay(GlassBorder(shape: Capsule(), isHovered: false))
        .compositingGroup()
        .shadow(color: .black.opacity(0.10), radius: 8, y: 3)
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
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            GlassIconControl(
                symbol: symbol,
                size: 44,
                iconSize: 18,
                isHovered: isHovered,
                hasOwnSurface: false,
                showsBorder: false,
                foregroundStyle: foregroundStyle,
                replacesSymbol: replaceSymbol,
                bounceValue: bounceValue
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(MotionCatalog.animation(for: .hover)) {
                isHovered = hovering
            }
        }
        .helpLabel(helpText)
    }
}

private struct GlassIconControl: View {
    let symbol: String
    let size: CGFloat
    let iconSize: CGFloat
    let isHovered: Bool
    let hasOwnSurface: Bool
    let showsBorder: Bool
    var foregroundStyle: AnyShapeStyle = AnyShapeStyle(.primary)
    /// 状态反馈（换符号的连续过渡 / 值变了弹一下）。默认关：
    /// 只有"图标代表一个状态"的那些按钮才开，纯动作按钮不该弹。
    var replacesSymbol = false
    var bounceValue: Int? = nil

    var body: some View {
        content
            .frame(width: size, height: size)
            .background(surface)
            .overlay(hoverLayer)
            .clipShape(Circle())
            .overlay {
                if showsBorder {
                    GlassBorder(shape: Circle(), isHovered: isHovered)
                }
            }
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

    @ViewBuilder
    private var surface: some View {
        Circle()
            .fill(hasOwnSurface ? AnyShapeStyle(.ultraThinMaterial) : AnyShapeStyle(.clear))
    }

    private var hoverLayer: some View {
        Circle()
            // 亮色材质上 `.white.opacity` 是看不见的（审计第二轮 14-06 / R2-03）：
            // 描边、分隔线、悬停层一律改用语义色或 primary 派生的透明度，两种外观下都在。
            .fill(.primary.opacity(isHovered ? 0.10 : 0))
    }
}

private struct GlassBorder<S: InsettableShape>: View {
    let shape: S
    let isHovered: Bool

    var body: some View {
        shape
            .strokeBorder(
                LinearGradient(
                    colors: [
                        Color.primary.opacity(isHovered ? 0.34 : 0.20),
                        Color.primary.opacity(0.07)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: 0.7
            )
    }
}
