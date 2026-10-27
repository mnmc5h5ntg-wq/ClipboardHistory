import AppKit
import SwiftUI

/// 来源 App 图标的真实解析：只在这里碰 `NSWorkspace`，并缓存结果。
/// 解析不到就返回 nil，由视图退回 `app` 符号（见 `SourceAppBadgePolicy`）。
@MainActor
enum SourceAppIconProvider {
    private static var cache: [String: NSImage] = [:]

    static func icon(forBundleID bundleID: String?) -> NSImage? {
        SourceAppBadgePolicy.resolvedIcon(bundleID: bundleID) { id in
            if let cached = cache[id] { return cached }
            guard let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: id) else {
                return nil
            }
            let icon = NSWorkspace.shared.icon(forFile: url.path)
            cache[id] = icon
            return icon
        }
    }
}

struct SourceAppBadge: View {
    let sourceAppBundleID: String?

    var body: some View {
        Group {
            if let icon = SourceAppIconProvider.icon(forBundleID: sourceAppBundleID) {
                Image(nsImage: icon)
                    .resizable()
                    .interpolation(.high)
                    .frame(width: SourceAppBadgePolicy.iconSize,
                           height: SourceAppBadgePolicy.iconSize)
            } else {
                Image(systemName: SourceAppBadgePolicy.fallbackSymbolName)
                    .font(.system(size: VisualGlyph.chipSymbol, weight: .regular))
                    .foregroundStyle(.secondary)
                    .frame(width: SourceAppBadgePolicy.iconSize,
                           height: SourceAppBadgePolicy.iconSize)
            }
        }
        .accessibilityHidden(true)
    }
}
