import Foundation

/// R513：多选操作栏的可用性 —— 一个动词只有在选区里**至少有一条适用**时才该是亮的。
/// 以前五颗从不禁用：没有固定项时「取消固定」照样可点，点了什么也不会发生。
struct BulkActionAvailability: Equatable {
    let canFavorite: Bool
    let canUnfavorite: Bool
    let canPin: Bool
    let canUnpin: Bool

    init(selectedEntries: [HistoryStore.Entry]) {
        canFavorite = selectedEntries.contains { !$0.isFavorite }
        canUnfavorite = selectedEntries.contains { $0.isFavorite }
        canPin = selectedEntries.contains { !$0.isPinned }
        canUnpin = selectedEntries.contains { $0.isPinned }
    }
}
