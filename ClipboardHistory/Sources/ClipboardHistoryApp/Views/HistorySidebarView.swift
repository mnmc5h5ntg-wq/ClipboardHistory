import AppKit
import SwiftUI

struct HistorySidebarView: View {
    @ObservedObject var historyStore: HistoryStore
    @State private var dragSelectionAnchorID: HistoryStore.Entry.ID?
    @State private var rowFrames: [HistoryStore.Entry.ID: CGRect] = [:]

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 8) {
                SearchField(
                    text: Binding(
                        get: { historyStore.searchText },
                        set: { historyStore.perform(.updateSearch($0)) }
                    )
                )

                SegmentedFilterPicker(
                    selection: Binding(
                        get: { historyStore.filter },
                        set: { historyStore.perform(.updateFilter($0)) }
                    )
                )
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
            Text(headerTitle)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(.secondary)
                .lineLimit(1)

            Spacer()

            if historyStore.selectedCount > 1 {
                bulkActionButtons
            } else {
                Text(countText)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .frame(height: 39)
        .animation(.easeInOut(duration: 0.12), value: historyStore.selectedCount > 1)
    }



    private var bulkActionButtons: some View {
        HStack(spacing: 8) {
            Button {
                historyStore.perform(.favoriteSelection)
            } label: {
                Image(systemName: "star")
            }
            .help("收藏所选记录")

            Button {
                historyStore.perform(.unfavoriteSelection)
            } label: {
                Image(systemName: "star.slash")
            }
            .help("取消收藏所选记录")

            Button(role: .destructive) {
                historyStore.perform(.deleteSelection)
            } label: {
                Image(systemName: "trash")
            }
            .help("删除所选记录")
            .foregroundStyle(.red)
        }
        .buttonStyle(.borderless)
    }

    private var headerTitle: String {
        if historyStore.selectedCount > 1 {
            return "已选 \(historyStore.selectedCount) 条"
        }
        return "时间剪史"
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
                        selected: historyStore.isSelected(entry),
                        action: { select(entry) }
                    )
                    .background(rowFrameReader(for: entry.id))
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
        }
        .coordinateSpace(name: "history-list")
        .simultaneousGesture(
            DragGesture(minimumDistance: 4, coordinateSpace: .named("history-list"))
                .onChanged { value in
                    updateDragSelection(at: value.location)
                }
                .onEnded { _ in
                    endDragSelection()
                }
        )
    }

    private func select(_ entry: HistoryStore.Entry) {
        let modifiers = NSEvent.modifierFlags
        if modifiers.contains(.shift) {
            historyStore.perform(.selectRange(to: entry))
        } else if modifiers.contains(.command) {
            historyStore.perform(.toggleSelection(entry))
        } else {
            historyStore.perform(.selectOnly(entry))
        }
    }

    private func updateDragSelection(at location: CGPoint) {
        guard let entry = entry(at: location) else { return }
        if dragSelectionAnchorID == nil {
            dragSelectionAnchorID = entry.id
            historyStore.perform(.selectOnly(entry))
            return
        }
        guard let dragSelectionAnchorID else { return }
        historyStore.perform(.dragSelectRange(anchorID: dragSelectionAnchorID, target: entry))
    }

    private func endDragSelection() {
        dragSelectionAnchorID = nil
    }

    private func entry(at location: CGPoint) -> HistoryStore.Entry? {
        historyStore.filteredEntries.first { entry in
            rowFrames[entry.id]?.contains(location) == true
        }
    }

    private func rowFrameReader(for id: HistoryStore.Entry.ID) -> some View {
        GeometryReader { proxy in
            Color.clear.preference(
                key: HistoryRowFramePreferenceKey.self,
                value: [id: proxy.frame(in: .named("history-list"))]
            )
        }
        .onPreferenceChange(HistoryRowFramePreferenceKey.self) { value in
            // 原来是 merge：过滤/删除后消失的行永远留在表里，
            // 拖动选择可能命中已经不在列表中的条目，且表只增不减（审计 R-40）。
            rowFrames = value
        }
    }
}

private struct HistoryRowFramePreferenceKey: PreferenceKey {
    static let defaultValue: [HistoryStore.Entry.ID: CGRect] = [:]

    static func reduce(
        value: inout [HistoryStore.Entry.ID: CGRect],
        nextValue: () -> [HistoryStore.Entry.ID: CGRect]
    ) {
        value.merge(nextValue()) { _, new in new }
    }
}

// MARK: - Segmented Filter Picker — sliding pill with spring overshoot

private struct SegmentedFilterPicker: View {
    @Binding var selection: HistoryStore.Filter

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 7, style: .continuous)
                .fill(.quaternary)

            slidingPill

            HStack(spacing: 0) {
                ForEach(HistoryStore.Filter.allCases) { filter in
                    FilterSegmentButton(
                        title: filter.title,
                        isSelected: selection == filter,
                        action: { selection = filter }
                    )
                }
            }
        }
        .frame(height: 26)
        .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
    }

    private var slidingPill: some View {
        GeometryReader { geo in
            let count = CGFloat(HistoryStore.Filter.allCases.count)
            let idx = CGFloat(HistoryStore.Filter.allCases.firstIndex(of: selection) ?? 0)
            RoundedRectangle(cornerRadius: 6, style: .continuous)
                .fill(.ultraThickMaterial)
                .frame(width: geo.size.width / count - 2)
                .padding(.vertical, 1)
                .offset(x: idx * (geo.size.width / count) + 1)
                .animation(.spring(response: 0.38, dampingFraction: 0.72), value: selection)
        }
    }
}

private struct FilterSegmentButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 12, weight: isSelected ? .semibold : .regular))
                .scaleEffect(isHovered ? 1.08 : 1.0)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 5)
                .padding(.horizontal, 10)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .animation(.easeInOut(duration: 0.14), value: isHovered)
        .animation(.easeInOut(duration: 0.14), value: isSelected)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
