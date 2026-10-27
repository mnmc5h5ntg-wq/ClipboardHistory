import Foundation

/// 侧栏分区头的行号规划。
///
/// 只有**有固定条目**时才多出一行 `已固定` 头；`SelectedRowRevealer` 用的表格行号要把这一行算进去，
/// 否则固定条目被选中时会把上一行滚进视口。没有固定条目时是恒等变换（老帧/老判据不动）。
struct SidebarSectionPlan: Equatable {
    static let pinnedTitle = "已固定"

    let pinnedCount: Int

    var hasPinnedHeader: Bool { pinnedCount > 0 }

    func displayRowIndex(forFilteredIndex index: Int) -> Int {
        index + (hasPinnedHeader ? 1 : 0)
    }
}
