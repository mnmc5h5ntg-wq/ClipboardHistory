import SwiftUI

@available(macOS 13, *)
struct MenuBarRecommendationsView: View {
    @ObservedObject var historyStore: HistoryStore
    let appDelegate: AppDelegate


    var body: some View {
        Group {
            Text("时间剪史")
                .font(.headline)

            if !historyStore.predictionSuggestionEntries.isEmpty {
                Divider()

                Text("猜你要粘贴")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(.tertiary)

                ForEach(historyStore.predictionSuggestionEntries.prefix(3)) { entry in
                    let reasonText = historyStore.predictionReasonByEntryID[entry.id] ?? ""

                    Button {
                        appDelegate.copyAndPasteHistoryEntry(id: entry.id)
                    } label: {
                        if reasonText.isEmpty {
                            Text(entry.shortPreview)
                                .lineLimit(1)
                        } else {
                            Text(entry.shortPreview + "\n" + reasonText)
                                .font(.system(size: 11))
                                .lineLimit(2)
                        }
                    }
                }
            }
            if !historyStore.predictionSuggestionEntries.isEmpty {
                Divider()
                Button {
                    historyStore.perform(.dismissAllRecommendations)
                } label: {
                    Text("都不是我想要的")
                        .font(.system(size: 11))
                        .foregroundStyle(.blue)
                }
                .buttonStyle(.plain)
                .frame(maxWidth: .infinity, alignment: .center)
            }
            Divider()
        }
        .onAppear {
            // 打开菜单时算一次即可。旧实现是每 2 秒无条件重算一次全库分析
            // （500 条 × 两套正则），合上菜单也在跑（审计 R-11/R-21）。
            historyStore.refreshPredictions()
        }
    }
}
