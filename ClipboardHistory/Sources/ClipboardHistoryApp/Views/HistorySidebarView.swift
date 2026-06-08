import SwiftUI

struct HistorySidebarView: View {
    @ObservedObject var historyStore: HistoryStore
    @State private var showClearConfirmation = false

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 8) {
                SearchField(
                    text: Binding(
                        get: { historyStore.searchText },
                        set: { historyStore.perform(.updateSearch($0)) }
                    )
                )

                Picker(
                    "范围",
                    selection: Binding(
                        get: { historyStore.filter },
                        set: { historyStore.perform(.updateFilter($0)) }
                    )
                ) {
                    ForEach(HistoryStore.Filter.allCases) { filter in
                        Text(filter.title).tag(filter)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)

            Divider()
            header

            if historyStore.filteredEntries.isEmpty {
                EmptyStateView(
                    systemName: "clipboard",
                    title: emptyTitle
                )
                .padding(.vertical, 40)
                Spacer()
            } else {
                historyList
            }
        }
    }

    private var header: some View {
        HStack {
            Text("时间剪史")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .fixedSize(horizontal: true, vertical: false)

            Spacer()

            Text(countText)
                .font(.system(size: 15, weight: .regular))
                .foregroundStyle(.tertiary)

            if historyStore.ordinaryCount > 0 {
                GlassCircleButton(
                    symbol: "trash.slash",
                    helpText: "清空未收藏记录",
                    foregroundStyle: AnyShapeStyle(Color.red)
                ) {
                    showClearConfirmation = true
                }
                .padding(.leading, 6)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .alert("清空未收藏记录", isPresented: $showClearConfirmation) {
            Button("取消", role: .cancel) {}
            Button("清空", role: .destructive) { historyStore.perform(.clear) }
        } message: {
            Text("收藏记录会保留，其余历史会被清空。")
        }
    }

    private var countText: String {
        switch historyStore.filter {
        case .all:
            return "\(historyStore.filteredEntries.count) 条记录"
        case .favorites:
            return "\(historyStore.filteredEntries.count) 个收藏"
        }
    }

    private var emptyTitle: String {
        if historyStore.entries.isEmpty {
            return "暂无剪贴板历史"
        }
        if historyStore.filter == .favorites {
            return historyStore.favoriteCount == 0 ? "暂无收藏" : "无匹配结果"
        }
        return "无匹配结果"
    }

    private var historyList: some View {
        ScrollView {
            LazyVStack(spacing: 0) {
                ForEach(historyStore.filteredEntries) { entry in
                    HistoryRowButton(
                        entry: entry,
                        selected: historyStore.selectedEntry?.id == entry.id,
                        action: { historyStore.perform(.select(entry)) }
                    )
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
        }
    }
}
