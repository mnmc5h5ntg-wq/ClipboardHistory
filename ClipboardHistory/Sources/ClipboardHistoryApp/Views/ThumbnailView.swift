import SwiftUI

struct ThumbnailImage: View {
    let nsImage: NSImage

    var body: some View {
        Image(nsImage: nsImage)
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: 16, height: 16)
            .clipShape(RoundedRectangle(cornerRadius: 4))
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    // 亮色下 `.white.opacity` 描边等于没有描边（审计第二轮 14-06 / R2-03）
                    .stroke(Color.primary.opacity(0.16), lineWidth: 0.5)
            )
            .shadow(color: .black.opacity(0.08), radius: 1, y: 0.5)
    }
}

struct ThumbnailSymbol: View {
    let systemName: String

    var body: some View {
        Image(systemName: systemName)
            .font(.system(size: 11, weight: .medium))
            .foregroundStyle(.secondary)
            .frame(width: 16, height: 16)
            .background(.quaternary)
            .clipShape(RoundedRectangle(cornerRadius: 4))
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.primary.opacity(0.14), lineWidth: 0.5)
            )
            .shadow(color: .black.opacity(0.06), radius: 1, y: 0.5)
    }
}
