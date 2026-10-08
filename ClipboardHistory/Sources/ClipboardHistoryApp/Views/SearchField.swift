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
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(isActive ? .primary : .secondary)

            ChineseEditableTextField(text: $text, placeholder: "搜索历史……")
                .frame(maxWidth: .infinity, minHeight: 17, maxHeight: 17)

            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(isHovered ? .secondary : .tertiary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 7)
        .background(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .fill(Color.primary.opacity(isActive ? 0.06 : 0.035))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(Color.primary.opacity(isActive ? 0.095 : 0.05), lineWidth: 0.5)
        )
        .animation(.easeInOut(duration: 0.12), value: isHovered)
        .animation(.easeInOut(duration: 0.12), value: text.isEmpty)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
