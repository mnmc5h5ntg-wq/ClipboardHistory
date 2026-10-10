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
    var imageSize: CGFloat = 28
    var titleSize: CGFloat = StatePresentation.messageFontSize
    /// 下一步动作。空态可以没有动作（"暂无剪贴板历史"就没有），但"无匹配结果"必须有。
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        let kind: StatePresentation.Kind = .empty
        VStack(alignment: StatePresentation.alignment(for: .pane), spacing: spacing) {
            Image(systemName: systemName)
                .font(.system(size: imageSize))
                .foregroundStyle(StatePresentation.iconStyle(for: kind))
                .accessibilityHidden(true)
            Text(title)
                .font(.system(size: titleSize))
                // 空状态里这句话就是全部信息，不能压到 tertiary（暗色实测 2.2:1）
                .foregroundStyle(.secondary)
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
