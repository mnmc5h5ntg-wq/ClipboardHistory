import SwiftUI

/// 设置侧栏最底下那行：应用名 + 版本。只在设置窗口里出现，不参与布局分配（由外层 Spacer 顶到底部）。
struct SettingsSidebarFooter: View {
    let text: String

    var body: some View {
        HStack(spacing: 0) {
            Text(text)
                // 侧栏在 `NavigationSplitView` 的 vibrant 材质里：`.secondary` 会被重映射，
                // 这里用动态系统色（与行内图标同一条理由，R381），亮暗都读得出来。
                .foregroundStyle(Color(nsColor: .secondaryLabelColor))
                .font(.system(size: VisualFont.meta))
                .lineLimit(1)
                .truncationMode(.tail)
                .accessibilityLabel(text)
            Spacer(minLength: 0)
        }
        // 16 = 侧栏行外 6 + 行内 10 ⇒ 与行内容的左沿同一条轴。
        .padding(.leading, 16)
        .padding(.trailing, 12)
        .padding(.top, 8)
        .padding(.bottom, 14)
    }
}

/// 取证通道（R426）：夹具注入固定版本，产品路径永远不写这个键 ⇒ 真实 bundle 那条路一字未动。
struct SettingsSidebarVersionForCaptureKey: EnvironmentKey {
    static let defaultValue: String? = nil
}

/// 取证通道（R426）：只有夹具会写 `false` 来拍"没有脚注"的负臂；`nil`/`true` 都按产品行为走。
struct SettingsSidebarFooterForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

/// 取证通道（R442）：关于页的 build 号；夹具注入固定值，产品路径读真实 bundle。
struct SettingsAboutBuildForCaptureKey: EnvironmentKey {
    static let defaultValue: String? = nil
}

extension EnvironmentValues {
    var settingsSidebarVersionForCapture: String? {
        get { self[SettingsSidebarVersionForCaptureKey.self] }
        set { self[SettingsSidebarVersionForCaptureKey.self] = newValue }
    }

    var settingsSidebarFooterForCapture: Bool? {
        get { self[SettingsSidebarFooterForCaptureKey.self] }
        set { self[SettingsSidebarFooterForCaptureKey.self] = newValue }
    }

    var settingsAboutBuildForCapture: String? {
        get { self[SettingsAboutBuildForCaptureKey.self] }
        set { self[SettingsAboutBuildForCaptureKey.self] = newValue }
    }
}
