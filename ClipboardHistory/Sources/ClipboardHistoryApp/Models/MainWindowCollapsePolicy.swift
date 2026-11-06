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

    /// R592（用户机上实测之后补的一条不变量）：高度离 √2 超过容差 ⇒ 那是旧恢复通路留下的，抬回来。
    ///
    /// 为什么这条能成立而不越界：产品**从不记高度**（`rememberWidth` 只写宽），而 macOS 13+ 的
    /// `contentAspectRatio` 锁住了比例 ⇒ 用户手动拖出来的一定还在 √2 上；所以"不在 √2 上"这件事
    /// 只能来自锁出现之前那一次恢复（用户机上现读 848×492，比 1.72）。
    /// 折叠态同理但方向相反：424 宽对应的规格高仍是 600（D5「折叠 = 高度不变、宽度对折」）。
    /// macOS 12 没有那条锁 ⇒ 调用方必须**不**用这一支（12 上拖得出任意比例，抬它就是抹用户的调整）。
    static func heightLift(collapsed: Bool, width: CGFloat, height: CGFloat,
                           tolerance: CGFloat = 0.02) -> CGFloat? {
        guard width > 0, height > 0 else { return nil }
        let target = collapsed ? width * 2.0.squareRoot() : width / 2.0.squareRoot()
        return abs(height - target) / target > tolerance ? target : nil
    }

    /// 收缩/放宽都保持左上角：x 不越过屏幕左右边，top 不越过屏幕上下边。
    static func originX(clampingX x: CGFloat, width: CGFloat, visibleFrame: CGRect) -> CGFloat {
        min(max(x, visibleFrame.minX), max(visibleFrame.minX, visibleFrame.maxX - width))
    }

    static func originY(clampingTop top: CGFloat, height: CGFloat, visibleFrame: CGRect) -> CGFloat {
        min(max(top - height, visibleFrame.minY), max(visibleFrame.minY, visibleFrame.maxY - height))
    }
}

/// R592（用户实测反馈）：把"记忆值压住新默认值"这一族一次性抬过去。
///
/// 为什么不改 `width(forKey:fallback:)` 的优先序：记忆优先是对的（用户手动 resize 过就该听他的），
/// 错的是**旧规格的那两档默认值还留在盘上**。2026-11-06 在用户机上现读：
/// `mainWindowExpandedWidth = 750`、`mainWindowCollapsedWidth = 420`（R567 之前的两档默认），
/// 而 SwiftUI 还存着窗口帧 `…-AppWindow-1 = "585 368 750 492"` 与分栏子视图帧
/// `423.5 / 326.5` ⇒ 升级用户看到的既不是 848 宽、两栏也不等分，第①段对他们**根本没发生过**。
///
/// 三条边界，都是"不许抹掉用户的东西"：
/// ① 只在记忆值**恰好等于旧默认对**（750 与 420）时抬 —— 那对值只可能来自旧默认，手动调过宽度的人
///    落在 `not-legacy-pair`，一律不碰；
/// ② 抬完立刻打版本键 ⇒ 此后用户再怎么调，这一段都不会再跑第二次（`already-migrated`）；
/// ③ 窗口帧不删、只改写宽高，并按"顶边不动"回算 origin.y ⇒ 用户放的位置逐字保留。
@MainActor
enum MainWindowGeometryMigration {
    static let versionKey = "mainWindowGeometryMigrationVersion"
    /// 目前只有一个版本；以后规格再改默认几何，就加一档并在 `plan` 里补一条分支。
    static let currentVersion = 1
    /// R567 之前的两档默认宽。判据与变异刀都从这里取，不写字面量。
    static let legacyExpandedWidth: CGFloat = 750
    static let legacyCollapsedWidth: CGFloat = 420

    struct Plan: Equatable {
        let expandedWidth: CGFloat?
        let collapsedWidth: CGFloat?
        let rewritesRestoredFrames: Bool
        let stampsVersion: Bool
        /// 四种具名出口，判据逐字读它：`legacy-default-pair` / `not-legacy-pair` /
        /// `no-legacy-memory` / `already-migrated`。
        let reason: String
    }

    /// 纯函数真值表：没有记忆值 / 记忆值不是旧默认对 / 已经迁过 ⇒ 一律不改宽高，但前两种要打版本键。
    static func plan(storedExpanded: CGFloat?, storedCollapsed: CGFloat?, storedVersion: Int?) -> Plan {
        if let storedVersion, storedVersion >= currentVersion {
            return Plan(expandedWidth: nil, collapsedWidth: nil,
                        rewritesRestoredFrames: false, stampsVersion: false,
                        reason: "already-migrated")
        }
        if storedExpanded == legacyExpandedWidth, storedCollapsed == legacyCollapsedWidth {
            return Plan(expandedWidth: MainWindowCollapsePolicy.expandedWidthDefault,
                        collapsedWidth: MainWindowCollapsePolicy.collapsedWidthDefault,
                        rewritesRestoredFrames: true, stampsVersion: true,
                        reason: "legacy-default-pair")
        }
        return Plan(expandedWidth: nil, collapsedWidth: nil,
                    rewritesRestoredFrames: false, stampsVersion: true,
                    reason: (storedExpanded == nil && storedCollapsed == nil) ? "no-legacy-memory" : "not-legacy-pair")
    }

    /// 只有主窗口自己的持久化键才动：两类键的名字里都带 `ClipboardHistoryApp.` 与 `-AppWindow-`，
    /// 而 `NSWindow Frame NSColorPanel` 那种系统面板键不在这个集合里。
    static func isMainWindowFrameKey(_ key: String) -> Bool {
        key.hasPrefix("NSWindow Frame ") && key.contains("ClipboardHistoryApp.") && key.contains("-AppWindow-")
    }

    static func isMainWindowSplitKey(_ key: String) -> Bool {
        key.hasPrefix("NSSplitView Subview Frames ") && key.contains("ClipboardHistoryApp.") && key.contains("-AppWindow-")
    }

    /// `"585 368 750 492 0 0 1470 923 "` → 宽高换成规格档，顶边（origin.y + height）逐字不动。
    /// 解析不出五个数就原样返回（迁移不许把用户的键改坏）。
    static func restoredFrameString(_ stored: String, width: CGFloat, height: CGFloat) -> String? {
        let parts = stored.split(separator: " ", omittingEmptySubsequences: true).map(String.init)
        guard parts.count >= 4, let x = Double(parts[0]), let y = Double(parts[1]),
              let oldHeight = Double(parts[3]) else { return nil }
        let top = y + oldHeight
        let screen = parts.count > 4 ? " " + parts[4...].joined(separator: " ") : ""
        return String(format: "%.0f %.0f %.0f %.0f", x, top - Double(height),
                      Double(width), Double(height)) + screen + " "
    }

    /// 薄胶水那一层：读盘 → 判 → 写。返回值给产品入口的判据现读 `reason`。
    @discardableResult
    static func apply(to defaults: UserDefaults) -> Plan {
        let version = defaults.object(forKey: versionKey) != nil ? defaults.integer(forKey: versionKey) : nil
        let expanded = storedWidth(defaults, MainWindowCollapseController.expandedWidthKey)
        let collapsed = storedWidth(defaults, MainWindowCollapseController.collapsedWidthKey)
        let outcome = plan(storedExpanded: expanded, storedCollapsed: collapsed, storedVersion: version)
        guard outcome.stampsVersion || outcome.expandedWidth != nil else { return outcome }
        if let expandedWidth = outcome.expandedWidth {
            defaults.set(Double(expandedWidth), forKey: MainWindowCollapseController.expandedWidthKey)
        }
        if let collapsedWidth = outcome.collapsedWidth {
            defaults.set(Double(collapsedWidth), forKey: MainWindowCollapseController.collapsedWidthKey)
        }
        if outcome.rewritesRestoredFrames {
            for key in defaults.dictionaryRepresentation().keys where isMainWindowFrameKey(key) {
                guard let stored = defaults.string(forKey: key),
                      let rewritten = restoredFrameString(stored,
                                                          width: MainWindowCollapsePolicy.expandedWidthDefault,
                                                          height: MainWindowCollapsePolicy.contentHeightDefault)
                else { continue }
                defaults.set(rewritten, forKey: key)
            }
            // 分栏子视图帧记的是**旧档的不对称**（423.5 / 326.5），没有"该抬成什么"的可算目标；
            // 删掉它，让 `navigationSplitViewColumnWidth` 的锁等宽约束自己给出 423.5 / 423.5。
            for key in defaults.dictionaryRepresentation().keys where isMainWindowSplitKey(key) {
                defaults.removeObject(forKey: key)
            }
        }
        if outcome.stampsVersion { defaults.set(currentVersion, forKey: versionKey) }
        return outcome
    }

    private static func storedWidth(_ defaults: UserDefaults, _ key: String) -> CGFloat? {
        guard defaults.object(forKey: key) != nil else { return nil }
        return CGFloat(defaults.double(forKey: key))
    }
}

/// R532：折叠态一次性提示的文案。单独成 enum 是为了让「提示说了什么」可被判据现读，
/// 而不是埋进视图字面量里只能靠人眼核对。
enum CollapseHintPresentation {
    static let text = "窗口已折叠 · 点箭头或按 ⌘\\ 展开"
    static let dismissTitle = "知道了"
    static let dismissHelp = "不再显示这条提示"
}
