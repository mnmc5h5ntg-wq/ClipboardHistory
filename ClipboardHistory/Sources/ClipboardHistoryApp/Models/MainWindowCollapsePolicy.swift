import Foundation
import CoreGraphics

/// R523：主窗口折叠/展开的**纯函数**。宽度、最小宽、时长、屏幕 clamp 都在这里判，
/// 视图与窗口只照着放 —— 这样"折叠宽不许沿用 268pt 侧栏宽"与"折叠不演（时长恒 0）"
/// 都能被真值表逐格点名，而不是只活在注释里。
enum MainWindowCollapsePolicy {
    /// 折叠宽是**单独定义**的：268pt 是侧栏在展开态里的列宽，列表挤在那条里读不出条目。
    /// R567（规格 `docs/FOLD_DUO_SPEC_2026-11-03.md` D5）：展开 **848×600**、折叠 = 高度不变、
    /// 宽度对折 ⇒ **424×600**；两态各自是一个 √2 矩形（横 / 竖），所以折痕正好落在中缝上。
    static let collapsedWidthDefault: CGFloat = 424
    static let expandedWidthDefault: CGFloat = 848
    /// R567：规格的默认高。折叠不碰它（`applyGeometry` 只写宽度）。
    static let contentHeightDefault: CGFloat = 600
    static let collapsedMinWidth: CGFloat = 360
    static let expandedMinWidth: CGFloat = 600
    static let minHeight: CGFloat = 440
    /// R567：中缝那 1pt 是 AppKit 分隔条自己占掉的（`dividerThickness` 真窗实测 1.00）。
    /// 所以"两栏各半"落到窗口里是 `423.5 + 1 + 423.5`：**分隔条的中心**正好在 424 = 848/2。
    static let seamDividerThickness: CGFloat = 1
    static var columnWidth: CGFloat { (expandedWidthDefault - seamDividerThickness) / 2 }
    static var seamCenter: CGFloat { columnWidth + seamDividerThickness / 2 }
    /// D5 的"锁比例"：横 √2 与竖 √2 是同一个对折的两侧，切换时**必须把锁的值一起翻过去**。
    static var expandedAspectRatio: NSSize {
        NSSize(width: expandedWidthDefault, height: contentHeightDefault)
    }
    static var collapsedAspectRatio: NSSize {
        NSSize(width: collapsedWidthDefault, height: contentHeightDefault)
    }
    static func aspectRatio(collapsed: Bool) -> NSSize {
        collapsed ? collapsedAspectRatio : expandedAspectRatio
    }
    /// R524：展开态侧栏的缝位（旧值 `navigationSplitViewColumnWidth` 的 ideal 280）。
    /// R567 重锚成**半页宽**：折页要的就是"左半页正好是右半页的镜像位置"。
    static var sidebarSeamWidth: CGFloat { expandedWidthDefault / 2 }
    /// R552：**折叠/展开不再演**（D-552）。时长恒为 0 —— 不是"还没调好"，是三条路都被真机读数否掉了：
    /// 1. 旧版（t=0 翻状态 + 60Hz 逐拍 `setFrame(display:true)`）：切换那一拍主线程空窗
    ///    60ms（折叠）/106ms（展开），屏上只在 50ms 内换 4 帧、17ms 内换 2 帧 ⇒ 先卡一下再整窗跳；
    /// 2. 快照盖子：`cacheDisplay` 拍不出侧栏材质，那一块在窗口服务里是纯黑；
    /// 3. 几何交给窗口服务（`animator().setFrame`，`display:false`）：本机屏上右缘只给出
    ///    3 档（750→535→302）、展开方向 2 档（750→417）⇒ 中间帧根本不存在，"演"就还是跳。
    /// 一步切换至少是**诚实**的：没有中间态可卡，也不会让人以为窗口在动而它其实在跳。
    /// 下一次要重新演，必须先解决「窗口服务给不给中间帧」与「材质怎么冻」这两格（BACKLOG 631）。
    static func animationDuration(reduceMotion: Bool) -> TimeInterval { 0 }

    static func minWidth(collapsed: Bool) -> CGFloat {
        collapsed ? collapsedMinWidth : expandedMinWidth
    }

    static func detailVisible(collapsed: Bool) -> Bool { !collapsed }

    /// R529：Window 菜单项标题随状态在「折叠窗口/展开窗口」间切换（界面入口的同一动作）。
    static func menuTitle(collapsed: Bool) -> String {
        collapsed ? "展开窗口" : "折叠窗口"
    }

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

/// R532：折叠态一次性提示的文案。单独成 enum 是为了让「提示说了什么」可被判据现读，
/// 而不是埋进视图字面量里只能靠人眼核对。
enum CollapseHintPresentation {
    static let text = "窗口已折叠 · 点箭头或按 ⌘\\ 展开"
    static let dismissTitle = "知道了"
    static let dismissHelp = "不再显示这条提示"
}
