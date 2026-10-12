import SwiftUI

struct ThumbnailImage: View {
    let nsImage: NSImage

    var body: some View {
        Image(nsImage: nsImage)
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: 16, height: 16)
            .clipShape(VisualShape.rounded(VisualRadius.chip))
            .overlay(
                VisualShape.rounded(VisualRadius.chip)
                    // 亮色下 `.white.opacity` 描边等于没有描边（审计第二轮 14-06 / R2-03）：
                    // 一律用 primary 派生，深浅两种外观下都在。
                    .stroke(Color.primary.opacity(VisualTint.chipStroke), lineWidth: VisualHairline.edge)
            )
            .visualShadow(VisualShadow.flat)
            // 真图片缩略图以前对 VoiceOver 完全沉默（审计第二轮 1.11）：读一句"图片缩略图"，
            // 刻意不读内容 —— 缩略图里可能是截图里的密码或聊天记录。
            .accessibilityLabel("图片缩略图")
    }
}

struct ThumbnailSymbol: View {
    let systemName: String

    var body: some View {
        Image(systemName: systemName)
            .font(.system(size: 11, weight: .medium))
            .foregroundStyle(.secondary)
            .frame(width: 16, height: 16)
            .background(VisualMaterial.track)
            .clipShape(VisualShape.rounded(VisualRadius.chip))
            .overlay(
                VisualShape.rounded(VisualRadius.chip)
                    .stroke(Color.primary.opacity(VisualTint.chipStroke), lineWidth: VisualHairline.edge)
            )
            .visualShadow(VisualShadow.flat)
            // 类型占位符号只是图形线索，"文件 / 图片 / 多文件"这一行文字里已经说清了，
            // 再读一遍符号名反而是噪音。
            .accessibilityHidden(true)
    }
}
