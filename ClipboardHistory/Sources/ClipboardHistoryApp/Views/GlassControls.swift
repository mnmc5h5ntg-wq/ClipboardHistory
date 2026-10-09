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
            withAnimation(.easeInOut(duration: 0.15)) {
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
    let copyAction: () -> Void
    let deleteAction: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            GlassPillButton(
                symbol: isFavorite ? "star.fill" : "star",
                helpText: isFavorite ? "取消收藏" : "收藏",
                foregroundStyle: isFavorite ? AnyShapeStyle(Color.yellow) : AnyShapeStyle(.primary),
                action: favoriteAction
            )

            Rectangle()
                .fill(.separator)
                .frame(width: 28, height: 1)

            GlassPillButton(symbol: "doc.on.doc", helpText: "再次复制", action: copyAction)

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
                foregroundStyle: foregroundStyle
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
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
            .symbolRenderingMode(.hierarchical)
            .foregroundStyle(foregroundStyle)
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
