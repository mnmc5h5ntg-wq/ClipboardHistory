import SwiftUI

extension View {
    @ViewBuilder
    func windowBackground() -> some View {
        if #available(macOS 15, *) {
            self.containerBackground(VisualMaterial.window, for: .window)
        } else {
            self.background(VisualMaterial.window)
        }
    }

    /// 详情区**只有一条内容左轴**（R32 / BACKLOG 39）：可读列贴着 gutter 起排，
    /// 向右最多排到 `DetailTypography.columnWidth()`，窗口再宽多出来的空间留在右边。
    ///
    /// 为什么不是"把可读列居中"（这是本轮改掉的旧写法）：
    /// 居中的列，它的左缘 = (面板宽 − 列宽)/2，**随窗口宽度变**。于是
    /// ① 加载态的骨架（在 gutter=20，R26 钉的）与它替代的正文（实测 55）不是一条轴
    ///    —— 预览落地的一瞬间整块内容向右跳 35pt；
    /// ② 头部 meta 与正文各自居中，读者要重新找"这条记录的内容从哪儿开始"。
    /// 系统的邮件/备忘录也是这个语言：正文从固定内缩起排，宽出来的部分留在右边。
    /// 三个调用点（头部 meta、渲染正文、原文正文）都走这里，轴只有一处定义。
    func detailReadableColumn() -> some View {
        self.frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)
            .frame(maxWidth: .infinity, alignment: .leading)
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
