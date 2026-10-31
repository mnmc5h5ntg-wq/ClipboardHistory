import Foundation

/// 批量删除的确认策略：先问，确认后才删。
///
/// R515 的事故：多选栏的「删除所选记录」直接 `perform(.deleteSelection)`，
/// 实机验证时误删 6 条（BACKLOG 619）。这里把"问"与"删"分开：
/// 取消/零选区都不返回 true，调用方只有拿到 true 才允许删除。
@MainActor
enum BulkDeleteConfirmation {
    static let title = "删除所选记录"

    static func message(count: Int) -> String {
        "将删除 \(count) 条记录。此操作不可撤销。"
    }

    static func confirm(count: Int, using confirming: DestructiveConfirming) -> Bool {
        guard count > 0 else { return false }
        return confirming.confirm(
            title: title,
            message: message(count: count),
            confirmTitle: "删除",
            cancelTitle: "取消"
        )
    }
}
