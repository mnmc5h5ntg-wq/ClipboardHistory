import SwiftUI

struct GlassCircleButton: View {
    let symbol: String
    let helpText: String
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            GlassIconControl(
                symbol: symbol,
                size: 40,
                iconSize: 16,
                isHovered: isHovered,
                hasOwnSurface: true,
                showsBorder: true
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
        .help(helpText)
    }
}

struct GlassPill: View {
    let copyAction: () -> Void
    let deleteAction: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            GlassPillButton(symbol: "doc.on.doc", helpText: "再次复制", action: copyAction)

            Rectangle()
                .fill(.white.opacity(0.18))
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
                showsBorder: false
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
        .help(helpText)
    }
}

private struct GlassIconControl: View {
    let symbol: String
    let size: CGFloat
    let iconSize: CGFloat
    let isHovered: Bool
    let hasOwnSurface: Bool
    let showsBorder: Bool

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
            .foregroundStyle(.primary)
            .frame(width: size, height: size)
    }

    @ViewBuilder
    private var surface: some View {
        Circle()
            .fill(hasOwnSurface ? AnyShapeStyle(.ultraThinMaterial) : AnyShapeStyle(.clear))
    }

    private var hoverLayer: some View {
        Circle()
            .fill(.white.opacity(isHovered ? 0.13 : 0))
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
                        .white.opacity(isHovered ? 0.42 : 0.24),
                        .white.opacity(0.08)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: 0.7
            )
    }
}
