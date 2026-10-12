import SwiftUI

struct SearchField: View {
    @Binding var text: String
    @State private var isHovered = false

    private var isActive: Bool {
        isHovered || !text.isEmpty
    }

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: VisualFont.body, weight: .medium))
                .foregroundStyle(isActive ? .primary : .secondary)

            ChineseEditableTextField(text: $text, placeholder: "搜索历史……")
                .frame(maxWidth: .infinity, minHeight: 17, maxHeight: 17)

            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: VisualFont.row, weight: .medium))
                        .foregroundStyle(isHovered ? .secondary : .tertiary)
                }
                .buttonStyle(.plain)
                // 图标按钮没有可读文本，VoiceOver 会念不出用途（审计第二轮 1.11）
                .helpLabel("清除搜索")
            }
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 7)
        .background(
            VisualShape.rounded(VisualRadius.card)
                .fill(Color.primary.opacity(isActive ? VisualFill.fieldActive : VisualFill.fieldIdle))
        )
        .overlay(
            VisualShape.rounded(VisualRadius.card)
                .stroke(Color.primary.opacity(isActive ? VisualTint.fieldActiveStroke : VisualTint.fieldIdleStroke),
                        lineWidth: VisualHairline.edge)
        )
        .animation(MotionCatalog.animation(for: .hover), value: isHovered)
        .animation(MotionCatalog.animation(for: .contentFade), value: text.isEmpty)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
