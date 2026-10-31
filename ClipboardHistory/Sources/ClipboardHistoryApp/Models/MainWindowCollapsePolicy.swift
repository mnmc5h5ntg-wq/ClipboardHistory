import Foundation
import CoreGraphics

/// R523：主窗口折叠/展开的**纯函数**。宽度、最小宽、时长、屏幕 clamp 都在这里判，
/// 视图与窗口只照着放 —— 这样"折叠宽不许沿用 268pt 侧栏宽"与"reduce 下 0 时长"
/// 都能被真值表逐格点名，而不是只活在注释里。
enum MainWindowCollapsePolicy {
    /// 折叠宽是**单独定义**的：268pt 是侧栏在展开态里的列宽，列表挤在那条里读不出条目。
    static let collapsedWidthDefault: CGFloat = 420
    static let expandedWidthDefault: CGFloat = 750
    static let collapsedMinWidth: CGFloat = 360
    static let expandedMinWidth: CGFloat = 600
    static let minHeight: CGFloat = 440
    /// R523 只落静态骨架，时长先定义给 R524 的过渡用；reduce 下必须是 0。
    static let toggleDuration: TimeInterval = 0.22

    static func minWidth(collapsed: Bool) -> CGFloat {
        collapsed ? collapsedMinWidth : expandedMinWidth
    }

    static func detailVisible(collapsed: Bool) -> Bool { !collapsed }

    static func nextCollapsed(_ current: Bool) -> Bool { !current }

    static func animationDuration(reduceMotion: Bool) -> TimeInterval {
        reduceMotion ? 0 : toggleDuration
    }

    static func rememberedWidth(collapsed: Bool,
                                expandedWidth: CGFloat,
                                collapsedWidth: CGFloat) -> CGFloat {
        collapsed ? collapsedWidth : expandedWidth
    }

    /// 目标宽度：先尊重用户最近一次 resize 记住的宽度，再夹到折叠/展开各自的最小宽，
    /// 最后夹到屏幕可见宽。屏幕比最小宽还窄时，屏幕优先（窗口不许跑出屏）。
    static func targetWidth(collapsed: Bool,
                            expandedWidth: CGFloat,
                            collapsedWidth: CGFloat,
                            visibleWidth: CGFloat?) -> CGFloat {
        let remembered = rememberedWidth(collapsed: collapsed,
                                         expandedWidth: expandedWidth,
                                         collapsedWidth: collapsedWidth)
        let floor = max(remembered, minWidth(collapsed: collapsed))
        guard let visibleWidth, visibleWidth > 0 else { return floor }
        return min(floor, visibleWidth)
    }

    /// 收缩/放宽都保持左上角：x 不越过屏幕左右边，top 不越过屏幕上下边。
    static func originX(clampingX x: CGFloat, width: CGFloat, visibleFrame: CGRect) -> CGFloat {
        min(max(x, visibleFrame.minX), max(visibleFrame.minX, visibleFrame.maxX - width))
    }

    static func originY(clampingTop top: CGFloat, height: CGFloat, visibleFrame: CGRect) -> CGFloat {
        min(max(top - height, visibleFrame.minY), max(visibleFrame.minY, visibleFrame.maxY - height))
    }
}
