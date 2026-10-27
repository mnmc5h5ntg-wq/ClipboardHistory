import Foundation

/// 设置侧栏底部署名行：`时间剪史 <版本>`。
///
/// 版本号只做**展示**，不参与任何逻辑；读不到 `CFBundleShortVersionString` 时只写应用名，
/// 不编一个假版本（"1.x 未读"之类的占位比没有更坏）。
enum SettingsSidebarFooterPolicy {
    static let appName = "时间剪史"

    static func versionText(shortVersion: String?) -> String {
        guard let version = normalized(shortVersion) else { return appName }
        return "\(appName) \(version)"
    }

    /// 采集夹具注入固定版本，产品路径读真实 bundle。
    static func resolvedVersionText(override: String? = nil, bundle: Bundle = .main) -> String {
        if let override = normalized(override) {
            return versionText(shortVersion: override)
        }
        return versionText(shortVersion: bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String)
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
