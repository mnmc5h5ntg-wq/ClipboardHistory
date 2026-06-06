import SwiftUI

extension View {
    @ViewBuilder
    func windowBackground() -> some View {
        if #available(macOS 15, *) {
            self.containerBackground(.thickMaterial, for: .window)
        } else {
            self.background(.thickMaterial)
        }
    }
}
