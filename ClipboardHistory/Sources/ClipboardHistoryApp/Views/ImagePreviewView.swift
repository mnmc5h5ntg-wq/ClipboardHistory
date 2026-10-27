import SwiftUI

/// R433：详情预览的贴合尺寸。抽成纯函数是为了让「边贴在图本身」这件事能被单测钉住：
/// `scaledToFit` 在有上限的 `frame` 里画的是**居中、留白**的一张图，边若挂在那个 frame 上，
/// 画出来的是一个比图大一圈的空框。
enum ImagePreviewLayout {
    static func fittedSize(image: CGSize, available: CGSize) -> CGSize {
        guard image.width > 0, image.height > 0,
              available.width > 0, available.height > 0 else { return .zero }
        // 只缩不放：`scaledToFit` 的旧行为就是这样（240×140 的图在 720 窗口里仍是 240×140）。
        // 第一版漏了 `1` 这一项，帧上量到 240×140 被拉到 680×397 —— 那是自伤，不是改进。
        let scale = min(1, min(available.width / image.width, available.height / image.height))
        return CGSize(width: (image.width * scale).rounded(),
                      height: (image.height * scale).rounded())
    }
}

struct ImagePreviewView: View {
    let nsImage: NSImage

    var body: some View {
        GeometryReader { geo in
            ScrollView([.horizontal, .vertical]) {
                // R433：大图补一圈 1pt 中性边。以前白底图片（截图、白底海报）与详情底色
                // 完全同色，整张图看不出边界；边挂在**贴合图本身的尺寸**上，
                // 不是挂在 `maxWidth/maxHeight` 那块大区域上（那会画成一个空框）。
                let available = CGSize(width: max(geo.size.width - 40, 100),
                                       height: max(geo.size.height - 40, 100))
                let fitted = ImagePreviewLayout.fittedSize(image: nsImage.size,
                                                           available: available)
                Image(nsImage: nsImage)
                    .resizable()
                    .frame(width: fitted.width, height: fitted.height)
                    .padding(1)
                    .background(Color.primary.opacity(VisualTint.chipStroke))
                    .padding(20)
                    // 详情里的大图同样要有名字（审计第二轮 1.11）；只说"图片"，不读任何内容。
                    .accessibilityLabel("图片内容")
            }
        }
    }
}
