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
    /// R524：展开态侧栏的缝位（`navigationSplitViewColumnWidth` 的 ideal 280）。
    /// 过渡时折叠列表只从这条缝右侧开始遮罩 —— 否则两棵整树交叉淡会同时画出两套 chrome。
    static let sidebarSeamWidth: CGFloat = 280
    /// R524：时长/曲线**只从 MotionCatalog 取**（`.windowFold`），这里不再写第二个常数。
    /// R523 的 reduce=0 判据继续用 `animationDuration`。
    static var toggleDuration: TimeInterval { MotionCatalog.duration(for: .windowFold) }

    static var foldControlPoints: [Double] {
        MotionCatalog.timingControlPoints(for: .windowFold, reduceMotion: false)
    }

    static func animationDuration(reduceMotion: Bool) -> TimeInterval {
        reduceMotion ? 0 : toggleDuration
    }

    /// 三次贝塞尔缓动（与 `Animation.timingCurve` 同一条曲线）。控制器自己按 60Hz 驱动，
    /// 所以需要把控制点摊成 `t → 进度` 的纯函数；reduce 路径根本不走它（时长为 0）。
    static func easedProgress(_ linear: Double,
                              controlPoints: [Double] = foldControlPoints) -> Double {
        let x = min(max(linear, 0), 1)
        guard controlPoints.count == 4 else { return x }
        let x1 = controlPoints[0], y1 = controlPoints[1]
        let x2 = controlPoints[2], y2 = controlPoints[3]
        func bezier(_ t: Double, _ a: Double, _ b: Double) -> Double {
            let u = 1 - t
            return 3 * u * u * t * a + 3 * u * t * t * b + t * t * t
        }
        var low = 0.0, high = 1.0, t = x
        for _ in 0..<12 {
            let bx = bezier(t, x1, x2)
            if abs(bx - x) < 0.0005 { break }
            if bx < x { low = t } else { high = t }
            t = (low + high) / 2
        }
        return min(max(bezier(t, y1, y2), 0), 1)
    }

    /// 交叉淡的两端：展开布局 `1−p`、折叠布局 `p`。两端都由各自的 tree 是否挂载兜底
    ///（p=1 时展开树整棵不渲染，detail 不存在；p=0 时折叠树不渲染）。
    static func expandedContentOpacity(foldProgress: Double) -> Double {
        1 - min(max(foldProgress, 0), 1)
    }

    static func collapsedContentOpacity(foldProgress: Double) -> Double {
        min(max(foldProgress, 0), 1)
    }

    /// 中缝折页阴影：两端 0，中段最强（4p(1−p)，p=0.5 时 1）。
    static func hingeOpacity(foldProgress: Double) -> Double {
        4 * min(max(foldProgress, 0), 1) * (1 - min(max(foldProgress, 0), 1))
    }

    static func minWidth(collapsed: Bool) -> CGFloat {
        collapsed ? collapsedMinWidth : expandedMinWidth
    }

    static func detailVisible(collapsed: Bool) -> Bool { !collapsed }

    static func nextCollapsed(_ current: Bool) -> Bool { !current }

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
