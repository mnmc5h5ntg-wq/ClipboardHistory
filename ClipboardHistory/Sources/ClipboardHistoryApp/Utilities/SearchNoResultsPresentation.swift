import Foundation

/// 搜索无结果态的文案与图标（R423）。
///
/// 以前所有空态共用 `clipboard` 图标和「无匹配结果」：搜不到东西时画的还是剪贴板，
/// 而且不告诉用户**哪个词**没找到。这一层把「有没有历史 / 有没有搜索词」压成两个决定，
/// 视图只消费结果；纯函数让真值表可断言。
enum SearchNoResultsPresentation {
    /// 标题里最多展示多少个查询字符；再长就截断加省略号（侧栏只有 250pt 宽，标题会折两行）。
    static let maxQueryCharacters = 24
    static let magnifierSymbol = "magnifyingglass"
    static let clipboardSymbol = "clipboard"

    /// 无结果时画放大镜；没有历史/收藏为空仍画剪贴板（那不是"搜不到"，是"还没有"）。
    static func iconName(entriesEmpty: Bool,
                         isFavoritesFilter: Bool,
                         favoriteCount: Int,
                         searchText: String) -> String {
        if entriesEmpty { return clipboardSymbol }
        if isFavoritesFilter && favoriteCount == 0 { return clipboardSymbol }
        return normalized(searchText).isEmpty ? clipboardSymbol : magnifierSymbol
    }

    /// 查询词优先于「无匹配」；但**收藏为空**仍是"还没有收藏"（那是状态，不是搜不到）。
    static func title(entriesEmpty: Bool,
                      isFavoritesFilter: Bool,
                      favoriteCount: Int,
                      searchText: String) -> String {
        if entriesEmpty { return "暂无剪贴板历史" }
        if isFavoritesFilter && favoriteCount == 0 { return "暂无收藏" }
        let query = normalized(searchText)
        guard !query.isEmpty else { return "无匹配结果" }
        let clipped = query.count > maxQueryCharacters
            ? String(query.prefix(maxQueryCharacters)) + "…"
            : query
        return "没有找到「\(clipped)」"
    }

    private static func normalized(_ text: String) -> String {
        text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
