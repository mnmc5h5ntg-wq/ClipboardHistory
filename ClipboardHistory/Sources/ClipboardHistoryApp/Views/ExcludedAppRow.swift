import AppKit
import SwiftUI

/// R432：排除名单的一行 —— 真实 App 图标（找不到就画兜底符号）+ 应用名 + bundle ID。
/// 以前默认名单是一串 `默认排除：com.…` 的纯文本，用户认不出是哪个 App。
struct ExcludedAppRow: View {
    let bundleID: String

    var body: some View {
        HStack(spacing: 6) {
            ExcludedAppIcon(bundleID: bundleID)
                .frame(width: 16, height: 16)
            Text(ExcludedAppPresentation.displayName(for: bundleID))
                .font(.system(size: VisualFont.row))
                .lineLimit(1)
            Text(bundleID)
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)
            Spacer(minLength: 0)
        }
        .frame(height: 20)
        .accessibilityElement(children: .combine)
    }
}

private struct ExcludedAppIcon: View {
    let bundleID: String

    var body: some View {
        if let image = ExcludedAppIconCache.icon(for: bundleID) {
            Image(nsImage: image)
                .resizable()
                .interpolation(.high)
                .scaledToFit()
        } else {
            Image(systemName: ExcludedAppPresentation.fallbackSymbolName)
                .font(.system(size: VisualGlyph.chipSymbol, weight: .medium))
                .foregroundStyle(Color(nsColor: .secondaryLabelColor))
        }
    }
}

@MainActor
private enum ExcludedAppIconCache {
    private static var cache: [String: NSImage] = [:]
    private static var misses: Set<String> = []

    static func icon(for bundleID: String) -> NSImage? {
        if let hit = cache[bundleID] { return hit }
        if misses.contains(bundleID) { return nil }
        guard let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID) else {
            misses.insert(bundleID)
            return nil
        }
        let image = NSWorkspace.shared.icon(forFile: url.path)
        image.size = NSSize(width: 32, height: 32)
        cache[bundleID] = image
        return image
    }
}
