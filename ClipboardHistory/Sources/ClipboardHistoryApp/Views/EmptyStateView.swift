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
                .foregroundStyle(.quaternary)
            Text(title)
                .font(.system(size: titleSize))
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
