import Foundation

/// 历史存档的导出 / 导入（第三轮审计 §5 F-5 的另一半：用户此前没有任何方式把历史带走）。
///
/// 刻意不复用 `StoredEntry`（那是 `HistoryPersistence` 的私有格式，且图片是"文件名 + 旁边的
/// PNG 文件"两件套，单独拷 JSON 出去图片就是断链）。这里是一份**自包含、可人读**的交换格式：
/// 默认**不含图片**，并且导出前会把"里面是敏感内容"这句话说明白。
enum ArchiveTransfer {
    static let exchangeVersion = 1

    struct Item: Codable, Equatable {
        enum Kind: String, Codable {
            case text, file, files
        }

        let id: UUID
        let timestamp: Date
        let kind: Kind
        let text: String?
        let urls: [URL]?
        let isFavorite: Bool
        let isPinned: Bool
        let sourceAppBundleID: String?
        let sourceAppName: String?
        let ocrText: String?
    }

    struct Payload: Codable {
        var version: Int
        var exportedAt: Date
        var includesImages: Bool
        var entries: [Item]
    }

    struct Summary: Equatable {
        var exportedCount: Int
        var skippedImageCount: Int
        var importedCount: Int = 0
        var skippedDuplicateCount: Int = 0
    }

    /// 导出前的提示文案。**必须**说清两件事：内容里可能有密码/验证码之外的敏感东西，
    /// 以及默认不带图片（不带图片的导出文件拷走后再回来，图片条目是缺失的）。
    static func exportWarningText(summary: Summary) -> String {
        var parts = ["导出 \(summary.exportedCount) 条记录。存档里是完整的剪贴板内容"
            + "（可能包含账号、验证码、私人对话），请当作敏感文件保管。"]
        if summary.skippedImageCount > 0 {
            parts.append("另有 \(summary.skippedImageCount) 条图片记录未导出（默认不含图片）。")
        }
        return parts.joined()
    }

    static func export(entries: [ClipboardEntry], includeImages: Bool = false) -> (Data, Summary) {
        var skippedImages = 0
        var items: [Item] = []
        items.reserveCapacity(entries.count)
        for entry in entries {
            switch entry.content {
            case .text(let text):
                items.append(Item(id: entry.id, timestamp: entry.timestamp, kind: .text,
                                  text: text, urls: nil, isFavorite: entry.isFavorite,
                                  isPinned: entry.isPinned,
                                  sourceAppBundleID: entry.sourceAppBundleID,
                                  sourceAppName: entry.sourceAppName, ocrText: entry.ocrText))
            case .file(let url):
                items.append(Item(id: entry.id, timestamp: entry.timestamp, kind: .file,
                                  text: nil, urls: [url], isFavorite: entry.isFavorite,
                                  isPinned: entry.isPinned,
                                  sourceAppBundleID: entry.sourceAppBundleID,
                                  sourceAppName: entry.sourceAppName, ocrText: entry.ocrText))
            case .files(let urls):
                items.append(Item(id: entry.id, timestamp: entry.timestamp, kind: .files,
                                  text: nil, urls: urls, isFavorite: entry.isFavorite,
                                  isPinned: entry.isPinned,
                                  sourceAppBundleID: entry.sourceAppBundleID,
                                  sourceAppName: entry.sourceAppName, ocrText: entry.ocrText))
            case .image:
                // 图片要么显式带上（本轮仍不支持：单文件 JSON 装不下像素，且会把敏感截图
                // 悄悄复制一份到导出位置），要么如实报"跳过了几条"。
                skippedImages += 1
            }
        }
        let payload = Payload(version: exchangeVersion, exportedAt: Date(),
                              includesImages: includeImages, entries: items)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        let data = (try? encoder.encode(payload)) ?? Data()
        return (data, Summary(exportedCount: items.count, skippedImageCount: skippedImages))
    }

    /// 合并规则（纯函数）：同 id 视为重复并跳过，其余按时间倒序排回原列表。
    /// 放在这里而不是 `HistoryStore` 里，是为了让"导入会不会把老记录挤乱"可被单测钉住。
    static func merging(existing: [ClipboardEntry], incoming: [ClipboardEntry], summary: Summary)
        -> (entries: [ClipboardEntry], summary: Summary) {
        var summary = summary
        var merged = existing
        for entry in incoming {
            if merged.contains(where: { $0.id == entry.id }) {
                summary.skippedDuplicateCount += 1
                continue
            }
            merged.append(entry)
        }
        merged.sort { $0.timestamp > $1.timestamp }
        return (merged, summary)
    }

    static func `import`(_ data: Data) throws -> ([ClipboardEntry], Summary) {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let payload = try decoder.decode(Payload.self, from: data)
        var entries: [ClipboardEntry] = []
        entries.reserveCapacity(payload.entries.count)
        for item in payload.entries {
            let content: ClipboardEntryContent
            switch item.kind {
            case .text:
                guard let text = item.text, !text.isEmpty else { continue }
                content = .text(text)
            case .file:
                guard let url = item.urls?.first else { continue }
                content = .file(url)
            case .files:
                guard let urls = item.urls, !urls.isEmpty else { continue }
                content = urls.count == 1 ? .file(urls[0]) : .files(urls)
            }
            entries.append(ClipboardEntry(id: item.id, content: content, timestamp: item.timestamp,
                                          thumbnail: nil, sourceURL: content.sourceURL,
                                          isFavorite: item.isFavorite, sourceUTIs: [],
                                          sourceAppBundleID: item.sourceAppBundleID,
                                          sourceAppName: item.sourceAppName, ocrText: item.ocrText,
                                          isPinned: item.isPinned))
        }
        return (entries, Summary(exportedCount: 0, skippedImageCount: 0, importedCount: entries.count))
    }
}
