import CoreGraphics

/// 快速选择面板在屏幕上的落点（R421）。
///
/// 以前 `ensurePanel()` 把面板建在 (0,0) 就再也没动过 —— 那是**屏幕左下角**（Cocoa 原点），
/// 在大多数 Mac 上压在 Dock 上；而窗口位置从来没有进过任何一帧或判据。这里把落点收成纯函数：
/// 以**面板所在屏幕的 visibleFrame**（已排除菜单栏与 Dock）为房间，居中并夹住四边。
enum QuickPickPlacement {
    /// 面板的标称尺寸（`ensurePanel()` 建窗时的 contentRect）。
    /// 调用方可以传真实 `panel.frame.size`，这里只做测试与无窗口时的默认值。
    static let nominalSize = CGSize(width: 420, height: 300)

    /// 居中到 visibleFrame，再夹住四边；visibleFrame 比面板还小时从可见原点开始（不跑到负坐标）。
    static func origin(panelSize: CGSize = nominalSize, visibleFrame: CGRect) -> CGPoint {
        guard visibleFrame.width > 0, visibleFrame.height > 0,
              panelSize.width > 0, panelSize.height > 0 else { return .zero }
        let centeredX = visibleFrame.midX - panelSize.width / 2
        let centeredY = visibleFrame.midY - panelSize.height / 2
        // `max(min, max)`：房间比面板小时，夹到**可见原点**而不是负坐标 ——
        // 面板会超出小屏，但仍从用户能看到的左上角开始，而不是跑到菜单栏/Dock 外面。
        let maxX = max(visibleFrame.minX, visibleFrame.maxX - panelSize.width)
        let maxY = max(visibleFrame.minY, visibleFrame.maxY - panelSize.height)
        return CGPoint(x: min(max(centeredX, visibleFrame.minX), maxX),
                       y: min(max(centeredY, visibleFrame.minY), maxY))
    }
}
