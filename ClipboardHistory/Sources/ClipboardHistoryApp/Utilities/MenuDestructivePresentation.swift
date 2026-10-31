import Foundation

/// 破坏性菜单命令的视觉记号。
///
/// R515 曾用系统红文字；真窗口状态菜单的底是系统灰（实测 (104,104,104)），
/// 红字 (235,76,70) 与它的对比只有 **1.08:1** —— 不是可读的警告，只是换了个颜色。
/// 改用系统警告三角：符号是模板图，深/浅菜单底都保持高对比，文字回到正常墨色。
enum MenuDestructivePresentation {
    /// MenuBarExtra 的 `.menu` 会把 Label 的图标拍平成纯文本（R516 实测：菜单里那颗三角消失）。
    /// 用文本字符就能留下；U+FE0E 强制文字呈现，避免变成彩色 emoji。正常墨色在系统灰底上可读。
    static let warningPrefix = "\u{26A0}\u{FE0E} "
    static func title(_ base: String) -> String { warningPrefix + base }
}
