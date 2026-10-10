import Foundation

/// 采集准入：暂停开关 + 按 App 排除（第三轮审计 §5 F-1）。
///
/// 为什么单独成文件而不是写进 `HistoryStore`：`AGENTS.md` 的 DoD 第 2 条要求
/// 新逻辑先落成纯函数，Store 里只留薄胶水（守卫会红在"最长方法 / 总行数"上）。
///
/// 判据全部是纯函数，所以"哪些内容会被记录"这件事可以被真值表钉住，
/// 而不是靠"看起来加了个 if"。
enum CapturePolicy {
    /// 默认排除名单。这不是凭感觉列的：剪贴板管理器最容易出事的就是
    /// 密码管理器、系统钥匙串、以及会显示账号/验证码的窗口 —— 它们的内容一旦入库，
    /// 就以明文躺在 `history.json` 里，而用户通常以为自己"只是复制了一下"。
    static let defaultExcludedBundleIDs: Set<String> = [
        "com.agilebits.onepassword7",
        "com.agilebits.onepassword-osx",
        "com.apple.keychainaccess",
        "com.apple.Passwords",              // 系统设置里的"密码"面板
        "com.apple.AppleAccountAuth",
        "com.bitwarden.desktop",
        "com.lastpass.LastPass",
        "com.dashlane.DashlaneMacOS",
        "com.1password.Xcode-Integration",
    ]

    /// 用户自己加的排除项（`UserDefaults` 里的字符串数组，键与设置页共用）。
    static let userExcludedKey = "excludedAppBundleIDs"

    /// 用户排除项在 `UserDefaults` 里存成**一个分号连接的串**：
    /// `@AppStorage` 在部署下限 macOS 12 上不支持 `[String]`（只支持 RawRepresentable/String 等），
    /// 所以这里给一对纯编解码函数，顺带能被单测钉住（空串、重复项、首尾空格）。
    static func encodeUserExcluded(_ ids: [String]) -> String {
        Set(ids.map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty })
            .sorted()
            .joined(separator: ";")
    }

    static func decodeUserExcluded(_ raw: String) -> Set<String> {
        Set(raw.split(separator: ";").map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
              .filter { !$0.isEmpty })
    }

    static func userExcludedBundleIDs(from defaults: UserDefaults = .standard) -> Set<String> {
        decodeUserExcluded(defaults.string(forKey: userExcludedKey) ?? "")
    }

    static func effectiveExcludedBundleIDs(from defaults: UserDefaults = .standard) -> Set<String> {
        defaultExcludedBundleIDs.union(userExcludedBundleIDs(from: defaults))
    }

    /// 这一笔要不要入库。
    /// - 用户点名的导入（拖入文件）**不受排除名单影响**：那是显式动作，不是后台采集。
    /// - 来源 App 未知（`nil`）时**不排除** —— 拿"读不到来源"当理由挡掉用户的复制，
    ///   表现就是"历史记录莫名其妙不工作"，那比漏挡一次更坏。
    static func accepts(sourceAppBundleID: String? = nil,
                        paused: Bool,
                        isUserInitiated: Bool,
                        excluded: Set<String> = []) -> Bool {
        if isUserInitiated { return true }
        if paused { return false }
        if let id = sourceAppBundleID, excluded.contains(id) { return false }
        return true
    }

    /// 设置页展示用的名字：优先可读名，退到 bundle id。
    static func displayLabel(bundleID: String, name: String?) -> String {
        if let name, !name.isEmpty { return "\(name)（\(bundleID)）" }
        return bundleID
    }
}
