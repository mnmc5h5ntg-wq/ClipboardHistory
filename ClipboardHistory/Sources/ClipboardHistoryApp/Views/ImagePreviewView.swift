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
            }
        }
    }
}
