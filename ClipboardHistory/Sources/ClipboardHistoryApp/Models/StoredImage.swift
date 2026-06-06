import AppKit

struct StoredImage: Equatable, Hashable {
    let nsImage: NSImage

    init(_ image: NSImage) {
        self.nsImage = image
    }

    static func == (lhs: StoredImage, rhs: StoredImage) -> Bool {
        lhs.nsImage === rhs.nsImage
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(ObjectIdentifier(nsImage))
    }
}
