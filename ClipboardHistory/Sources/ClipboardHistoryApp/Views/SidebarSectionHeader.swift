import SwiftUI

/// 侧栏的固定条目分区头。只画一行 `已固定`，不画数量（数量留在页头）。
struct SidebarSectionHeader: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.system(size: VisualFont.meta, weight: .semibold))
            .foregroundStyle(Color(nsColor: .secondaryLabelColor))
            // R512：分组标题与行图标列同一左轴（侧栏内容从约 14.5pt 起，行首星标墨在 20pt）。
            // 原来 22 的缩进让标题落在图标列与标题列之间，两边都不对齐。
            .padding(.leading, 6)
            .padding(.vertical, 4)
            .accessibilityAddTraits(.isHeader)
    }
}

/// 取证通道（R429）：只有夹具写；`false` = 拍"没有分区头"的旧形状。
struct SidebarSectionHeadersForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var sidebarSectionHeadersForCapture: Bool? {
        get { self[SidebarSectionHeadersForCaptureKey.self] }
        set { self[SidebarSectionHeadersForCaptureKey.self] = newValue }
    }
}
