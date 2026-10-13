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
                // 高度从 17 抬到 22（R20）：**这一列才是这一行的定高者**。
                // 不这么做的话，命中区加宽的那颗 ×（14+8=22pt）会在有文字时把整颗框顶高，
                // 空框与有字的框差 5pt —— 打字时搜索框自己跳一下，
                // 那是我第一次改法实测出来的回归（空框 31→27、有字 31→32，两态不再等高）。
                // 让文本列自己声明 22pt，两态就都锁在 22 + 10 = 32pt。
                .frame(maxWidth: .infinity, minHeight: 22, maxHeight: 22)

            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: VisualFont.row, weight: .medium))
                        .foregroundStyle(isHovered ? .secondary : .tertiary)
                }
                // 悬停药丸与命中区一起抬（R20）：这颗 × 的 label **只有字形那么大**
                // （`xmark.circle.fill` 在 `VisualFont.row` 下约 14pt，没有 frame、没有 padding），
                // 于是"能点的地方"就是 14pt —— 全 App 最小的一颗可点控件，
                // 而它管的还是"一键清空搜索"这种要快按的动作。
                // 底色挂在 label 的包围盒上，所以 `labelPadding` 同时是高亮与命中区：
                // 4pt 把它抬到约 22pt，与系统搜索框那颗取消按钮的观感一致。
                // 悬停档同理从行档（0.06）抬到控件档（0.08）—— 见 `VisualFill.controlHover`。
                .pressedStyle(in: Circle(),
                              hoverLevel: VisualFill.controlHover,
                              labelPadding: 4)
                // 图标按钮没有可读文本，VoiceOver 会念不出用途（审计第二轮 1.11）
                .helpLabel("清除搜索")
            }
        }
        .padding(.horizontal, 9)
        // 垂直内边距从 7 收到 5（R20）：上面那颗 × 加了 4pt 命中区之后，
        // HStack 的高度由它（22pt）而不是文本（17pt）决定，整颗搜索框会凭空长高 5pt。
        // 收掉这 2pt 把高度还原文本那一档：实测 31pt → 32pt（1pt 以内算平），
        // 换来的是命中区 14pt → 22pt。**命中区要长，但不该以整条侧栏的节奏为代价。**
        .padding(.vertical, 5)
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
