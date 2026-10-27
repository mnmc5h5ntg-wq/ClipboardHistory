import SwiftUI

/// 整块面板空出来的时候那句话（详情区没选中、列表没有记录、筛选无结果）。
///
/// 与 `NoticeBanner`、菜单栏状态行共用 `StatePresentation` 的字号 / 图标色系（审计 §4 U-5）。
/// 对齐在这里刻意是**居中**：规范里 `.pane` 表面就是居中（Finder 的空文件夹、XCode 的空结果都这样），
/// 但块内部的多行文字仍然左对齐 —— 居中的参差行比居中一行难读得多。
struct EmptyStateView: View {
    let systemName: String
    let title: String
    var spacing: CGFloat = 12
    var imageSize: CGFloat = VisualGlyph.emptyCompact
    var titleSize: CGFloat = StatePresentation.messageFontSize
    /// R422：列表"还没有记录"那一档换成两张叠起来的卡片插画（空态是停，插画是静的）。
    /// 无匹配/其它空态保持原字形；默认 false ⇒ 既有调用点一字不改。
    var illustration: Bool = false
    /// 下一步动作。空态可以没有动作（"暂无剪贴板历史"就没有），但"无匹配结果"必须有。
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        let kind: StatePresentation.Kind = .empty
        VStack(alignment: StatePresentation.alignment(for: .pane), spacing: spacing) {
            if illustration {
                EmptyStateIllustration()
            } else {
                Image(systemName: systemName)
                    .font(.system(size: imageSize))
                    .foregroundStyle(StatePresentation.iconStyle(for: kind))
                    .accessibilityHidden(true)
            }
            Text(title)
                .font(.system(size: titleSize))
                // 空状态里这句话就是全部信息：`.secondary` 在亮档只有 2.90:1（暗 4.52 刚好贴线），
                // 低于 AA 正文线 4.5；pane 这一档单独取墨（R397 / StatePresentation）。
                .foregroundStyle(StatePresentation.paneMessageInkStyle)
                .multilineTextAlignment(.center)

            if let actionTitle, let action {
                Button(actionTitle, action: action)
                    .controlSize(.small)
                    .padding(.top, 2)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// R422：列表空态的插画 —— 两张叠起来的卡片 + 剪贴板字形。
///
/// 为什么是"叠起来的两张"而不是换一颗更大的符号：这一屏的语义是"这里会积累一条条历史"，
/// 一张卡代表一条；背卡向右上错开半格，前面那张带玻璃与发丝边，读起来是一叠还没长出来的记录。
/// 空态是"停"，所以它是**静的**：没有动画、没有动作；动作仍由标题下的可选按钮承担。
/// 颜色只用既有令牌（`VisualMaterial.glass` / `VisualTint.hoverStroke` / `VisualHairline.edge`），
/// 不新增档位，免得"同一件安静"再多出一种音量。
struct EmptyStateIllustration: View {
    var body: some View {
        ZStack {
            VisualShape.rounded(9)
                .fill(Color.primary.opacity(VisualTint.chipStroke * 0.4))
                .frame(width: 38, height: 38)
                .offset(x: 9, y: -9)
            VisualShape.rounded(9)
                .fill(VisualMaterial.glass)
                .frame(width: 42, height: 42)
                .overlay(
                    VisualShape.rounded(9)
                        .stroke(Color.primary.opacity(VisualTint.chipStroke * 0.5),
                                lineWidth: VisualHairline.edge)
                )
                .overlay(
                    Image(systemName: "clipboard")
                        .font(.system(size: VisualGlyph.emptyCompact * 0.72, weight: .regular))
                        .foregroundStyle(StatePresentation.iconStyle(for: .empty))
                )
        }
        .frame(width: 58, height: 54)
        .accessibilityHidden(true)
    }
}
