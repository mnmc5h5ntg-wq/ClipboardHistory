import Foundation

/// R432：设置页「不记录这些 App 的复制」那一列，以前把默认名单画成一串
/// `默认排除：com.…` 的裸 bundle ID —— 用户认不出这是哪个 App，
/// 九个不同长度的 ID 也让那一列没有可读的左/右轴。
///
/// 这一层只做「ID → 人话」的纯映射：视图负责图标与排版，判据直接钉这张表。
enum ExcludedAppPresentation {
    /// 默认名单里那些有公认名字的 App。键是 `CapturePolicy.defaultExcludedBundleIDs` 里的原值。
    static let knownNames: [String: String] = [
        "com.agilebits.onepassword7": "1Password 7",
        "com.agilebits.onepassword-osx": "1Password",
        "com.apple.keychainaccess": "钥匙串访问",
        "com.apple.Passwords": "密码",
        "com.apple.AppleAccountAuth": "Apple 账户认证",
        "com.bitwarden.desktop": "Bitwarden",
        "com.lastpass.LastPass": "LastPass",
        "com.dashlane.DashlaneMacOS": "Dashlane",
        "com.1password.Xcode-Integration": "1Password Xcode 集成",
    ]

    /// 认得的给名字，认不得的原样返回 ID（用户自己加的、没有名字的 App 也不该被吞掉）。
    static func displayName(for bundleID: String) -> String {
        let trimmed = bundleID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return bundleID }
        return knownNames[trimmed] ?? trimmed
    }

    static func hasKnownName(_ bundleID: String) -> Bool {
        knownNames[bundleID.trimmingCharacters(in: .whitespacesAndNewlines)] != nil
    }

    /// 找不到真实 App 图标时画的兜底符号（与 QuickPick 的未知类型同一套语言）。
    static let fallbackSymbolName = "app.dashed"
}
