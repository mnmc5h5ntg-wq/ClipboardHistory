import SwiftUI

extension View {
    @ViewBuilder
    func windowBackground() -> some View {
        if #available(macOS 15, *) {
            self.containerBackground(.thickMaterial, for: .window)
        } else {
            self.background(.thickMaterial)
        }
    }

    /// 悬浮提示与无障碍标签一起给。
    ///
    /// 只写 `.help()` 的图标按钮，鼠标用户悬停能看到文字，VoiceOver 用户什么都读不到
    /// —— 而这一层里绝大多数按钮只有图标没有标题（审计 R-54）。
    /// 统一走这里，界面层就不该再出现裸的 `.help(`（有静态测试守着）。
    func helpLabel(_ text: String) -> some View {
        self.help(text).accessibilityLabel(text)
    }
}
