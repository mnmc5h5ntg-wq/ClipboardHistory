import SwiftUI

struct HistorySidebarView: View {
    @ObservedObject var manager: ClipboardManager
    @State private var showClearConfirmation = false

    var body: some View {
        VStack(spacing: 0) {
            SearchField(
                text: Binding(get: { manager.searchText }, set: { manager.updateSearch($0) })
            )
            .padding(.horizontal, 12)
            .padding(.vertical, 10)

            Divider()
            header

            if manager.filteredEntries.isEmpty {
                EmptyStateView(
                    systemName: "clipboard",
                    title: manager.entries.isEmpty ? "暂无剪贴板历史" : "无匹配结果"
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

            Text("\(manager.filteredEntries.count) 条记录")
                .font(.system(size: 15, weight: .regular))
                .foregroundStyle(.tertiary)

            if !manager.entries.isEmpty {
                GlassCircleButton(symbol: "trash.slash", helpText: "清空全部") {
                    showClearConfirmation = true
                }
                .foregroundStyle(.red)
                .padding(.leading, 6)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .alert("清空全部记录", isPresented: $showClearConfirmation) {
            Button("取消", role: .cancel) {}
            Button("清空", role: .destructive) { manager.clearAll() }
        } message: {
            Text("确定要清空所有剪贴板记录吗？此操作不可撤销。")
        }
    }

    private var historyList: some View {
        ScrollView {
            LazyVStack(spacing: 0) {
                ForEach(manager.filteredEntries) { entry in
                    HistoryRowButton(
                        entry: entry,
                        selected: manager.selectedEntry?.id == entry.id,
                        action: { manager.selectedEntry = entry }
                    )
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
        }
    }
}
