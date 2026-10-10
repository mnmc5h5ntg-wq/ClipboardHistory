import AppKit

/// 快速选择浮层的列表模型（第三轮审计 §5 F-3）。
///
/// 刻意做成纯函数模型：浮层本身是 AppKit 面板，而这台机器与 CI 都**无法**把真实按键路由进一个
/// 刚弹出的面板（`xctest` / 裸二进制里 `NSApp.activate` 是空操作 —— spike 实测，见账本 D-041），
/// 所以"按键 → 移动/选中/提交"这条链只能靠把判定抽成可调用函数来验。
/// 面板那一层留给人手测（清单里写了具体按几下）。
struct QuickPickModel {
    /// 没有查询词时最多列这么长，避免一整屏都是候选。
    static let maximumUnfilteredCount = 12
    static let maximumFilteredCount = 60

    /// 候选来自 store 的当前条目。`var` 是因为浮层每次呼出都要取一次最新历史 ——
    /// 用 `let` 的话只能靠重建模型对象，而重建会把用户的查询词与下标一起丢掉。
    var all: [ClipboardEntry]
    var query: String = ""
    var index: Int = 0

    var visible: [ClipboardEntry] {
        let matched = Self.filtered(all, query: query)
        let cap = query.isEmpty ? Self.maximumUnfilteredCount : Self.maximumFilteredCount
        return Array(matched.prefix(cap))
    }

    var selection: ClipboardEntry? {
        guard index >= 0, index < visible.count else { return nil }
        return visible[index]
    }

    /// 大小写与音调不敏感地匹配预览文本、文件名与来源 App ——
    /// 与侧栏 `HistoryStore.filteredEntries` 用同一套 `localizedCaseInsensitiveContains`，
    /// 否则会出现"侧栏搜得到、浮层搜不到"这种两套语言。
    static func filtered(_ entries: [ClipboardEntry], query: String) -> [ClipboardEntry] {
        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !needle.isEmpty else { return entries }
        return entries.filter { entry in
            if entry.shortPreview.localizedCaseInsensitiveContains(needle) { return true }
            if let name = entry.sourceAppName, name.localizedCaseInsensitiveContains(needle) { return true }
            switch entry.content {
            case .file(let url):
                return url.lastPathComponent.localizedCaseInsensitiveContains(needle)
            case .files(let urls):
                return urls.contains { $0.lastPathComponent.localizedCaseInsensitiveContains(needle) }
            case .text, .image:
                return false
            }
        }
    }

    mutating func setQuery(_ newQuery: String) {
        query = newQuery
        index = 0    // 换查询词必然回到第一条：留着旧下标会指向一条**不相干**的记录，
                     // 而那正是"按下回车粘了个别的东西"这种事故的形状。
    }

    /// 上下移动。**不循环**：在只有 3 条候选时按 4 下"↓"跳回第 1 条，
    /// 用户看不出自己绕了一圈，夹住反而更容易建立心智模型。
    mutating func move(delta: Int) {
        guard !visible.isEmpty else { index = 0; return }
        index = min(max(index + delta, 0), visible.count - 1)
    }

    /// 面板关闭/重开时下标归零（候选内容也可能已经变了）。
    mutating func reset() {
        query = ""
        index = 0
    }
}
