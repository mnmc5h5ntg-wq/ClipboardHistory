import SwiftUI

struct ImagePreviewView: View {
    let nsImage: NSImage

    var body: some View {
        GeometryReader { geo in
            ScrollView([.horizontal, .vertical]) {
                Image(nsImage: nsImage)
                    .resizable()
                    .scaledToFit()
                    .frame(
                        maxWidth: max(geo.size.width - 40, 100),
                        maxHeight: max(geo.size.height - 40, 100)
                    )
                    .padding(20)
                    // 详情里的大图同样要有名字（审计第二轮 1.11）；只说"图片"，不读任何内容。
                    .accessibilityLabel("图片内容")
            }
        }
    }
}
