import Foundation

/// 「关于」页的文案与版本行。
///
/// 为什么要有这一页（R442）：设置里能看到版本的地方只有侧栏底部那一行 `时间剪史 1.4.8`，
/// 它既没有 build，也没有一句"这个应用是什么"。关于页把应用名、版本、build、一句定位
/// 与版权放在一处 —— 这是 macOS 应用的常规落点，也是设置里唯一一块"介绍自己"的地方。
///
/// 版本号只做**展示**：读不到就不编占位（与 `SettingsSidebarFooterPolicy` 同一条规矩）。
/// build 与版本分开：版本回答"这是哪一版"，build 回答"这一版的第几次构建"。
enum AboutPresentation {
    static let appName = "时间剪史"
    static let tagline = "轻量、离线、可回溯的剪贴板历史。"
    /// 版权年份写成常量而不是读当前年：帧基线要跨年稳定（跨年时间那条 BACKLOG 456 是另一件事）。
    static let copyright = "© 2026 时间剪史"

    static func versionLine(shortVersion: String?, build: String?) -> String {
        guard let version = normalized(shortVersion) else { return "版本信息未读到" }
        if let build = normalized(build) {
            return "版本 \(version)（build \(build)）"
        }
        return "版本 \(version)"
    }

    static func resolvedVersionLine(shortVersionOverride: String? = nil,
                                    buildOverride: String? = nil,
                                    bundle: Bundle = .main) -> String {
        let shortVersion = normalized(shortVersionOverride)
            ?? (bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String)
        let build = normalized(buildOverride)
            ?? (bundle.object(forInfoDictionaryKey: "CFBundleVersion") as? String)
        return versionLine(shortVersion: shortVersion, build: build)
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
