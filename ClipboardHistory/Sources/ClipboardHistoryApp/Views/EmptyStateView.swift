import SwiftUI

struct EmptyStateView: View {
    let systemName: String
    let title: String
    var spacing: CGFloat = 12
    var imageSize: CGFloat = 28
    var titleSize: CGFloat = 13

    var body: some View {
        VStack(spacing: spacing) {
            Image(systemName: systemName)
                .font(.system(size: imageSize))
                .foregroundStyle(.tertiary)
            Text(title)
                .font(.system(size: titleSize))
                // 空状态里这句话就是全部信息，不能压到 tertiary（暗色实测 2.2:1）
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
