import Foundation

/// 排序与保留的稳定规则：固定项（pin）置顶、且不参与复用提升与保留裁剪
/// （第三轮审计 §5 F-5）。
///
/// 全是纯函数：`entries` 进、`entries` 出，所以"固定了却还被顶到后面 / 被保留策略删掉"
/// 这类只有跑几天才会暴露的行为，可以在一次调用里被判掉。
enum EntryOrdering {
    /// 列表顺序：**固定的在前**，其余保持原相对顺序（稳定划分，不引入按时间的二次排序）。
    static func ordered(_ entries: [ClipboardEntry]) -> [ClipboardEntry] {
        let pinned = entries.filter(\.isPinned)
        let rest = entries.filter { !$0.isPinned }
        return pinned + rest
    }

    /// 复制后"顶到最前"的实际插入位置：固定项组成的那段之后。
    /// 否则"常用片段"会被每次复制挤下去，正是 F-5 要解决的问题。
    static func promotionIndex(_ entries: [ClipboardEntry]) -> Int {
        entries.prefix(while: \.isPinned).count
    }

    /// 保留策略裁剪：固定项**不参与**裁剪（它们就是"别删"的意思），
    /// 非固定项按策略裁完之后，把固定项按原顺序接回去。
    static func retaining(_ entries: [ClipboardEntry], by policy: HistoryRetentionPolicy) -> [ClipboardEntry] {
        let pinned = entries.filter(\.isPinned)
        let rest = entries.filter { !$0.isPinned }
        return policy.retaining(rest) + pinned
    }
}

/// OCR 结果的存放方式（第三轮审计 §5 F-4 的"只索引不落盘"）。
enum OCRPolicy {
    enum StorageMode: String {
        /// 识别文本随条目写进 `history.json`（历史行为，默认）。
        case persisted
        /// 识别文本只留在内存索引里，重启后对现有图片重新识别。
        /// 敏感文本不再二次落盘，代价是启动后要多跑一轮 OCR。
        case indexOnly
    }

    static let modeKey = "ocrStorageMode"

    static func mode(from defaults: UserDefaults = .standard) -> StorageMode {
        switch defaults.string(forKey: modeKey) {
        case StorageMode.indexOnly.rawValue: return .indexOnly
        default: return .persisted          // 没写过键 ⇒ 与历史行为一致
        }
    }

    static func setMode(_ mode: StorageMode, defaults: UserDefaults = .standard) {
        defaults.set(mode.rawValue, forKey: modeKey)
    }

    /// 要不要为这一条排一次识别任务。`hasImage` 由条目内容决定（图片或图片文件），
    /// 关掉开关 ⇒ 什么都不排（第三轮审计 D-3 / §5 F-4 的判据本体）。
    static func shouldSchedule(isEnabled: Bool, hasImage: Bool) -> Bool {
        isEnabled && hasImage
    }

    /// 识别结果要不要写进条目（进而落盘）。
    static func persistsResult(_ mode: StorageMode) -> Bool {
        mode == .persisted
    }

    /// 搜索时去哪儿找识别文本：条目上的优先，其次内存索引（「只索引不落盘」模式）。
    static func searchableText(entryOcrText: String?, indexValue: String?) -> String? {
        entryOcrText ?? indexValue
    }

    /// 这一条的识别文本是否命中查询。判据放在这里而不是 `HistoryStore` 里，
    /// 是为了让"不落盘也要能搜到"这件事能被单测钉住。
    static func matches(entry: ClipboardEntry, index: [ClipboardEntry.ID: String], query: String) -> Bool {
        guard !query.isEmpty,
              let text = searchableText(entryOcrText: entry.ocrText, indexValue: index[entry.id]) else { return false }
        return text.localizedCaseInsensitiveContains(query)
    }
}
