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
                    .stroke(.white.opacity(0.28), lineWidth: 0.5)
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
            .background(.white.opacity(0.08))
            .clipShape(RoundedRectangle(cornerRadius: 4))
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(.white.opacity(0.22), lineWidth: 0.5)
            )
            .shadow(color: .black.opacity(0.06), radius: 1, y: 0.5)
    }
}
