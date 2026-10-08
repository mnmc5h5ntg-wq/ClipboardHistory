import SwiftUI

enum NoticeTone {
    case warning
    case error
}

/// 窗口顶部的一次性提示条。目前有两个使用者：存档恢复提示（R-02）与
/// 自动粘贴失败（R-13）。两者原本都是"只写进 @Published 属性，没人显示"，
/// 于是用户看不到任何解释 —— 这个视图把那半条链路补上。
struct NoticeBanner: View {
    let message: String
    var tone: NoticeTone = .warning
    let onDismiss: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                Image(systemName: tone == .error ? "exclamationmark.triangle.fill" : "exclamationmark.arrow.circlepath")
                    .foregroundStyle(tone == .error ? Color.red : Color.orange)
                    .accessibilityHidden(true)

                Text(message)
                    .font(.callout)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .fixedSize(horizontal: false, vertical: true)

                Button("知道了", action: onDismiss)
                    .controlSize(.small)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 9)

            Divider()
        }
        .background(tone == .error ? Color.red.opacity(0.10) : Color.orange.opacity(0.12))
        .accessibilityElement(children: .contain)
    }
}
