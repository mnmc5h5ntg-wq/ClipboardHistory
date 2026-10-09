import SwiftUI

@available(macOS 13, *)
struct MenuBarRecommendationsView: View {
    @ObservedObject var historyStore: HistoryStore
    let appDelegate: AppDelegate


    var body: some View {
        Group {
            Text("时间剪史")
                .font(.headline)

            if historyStore.predictionSuggestionEntries.isEmpty {
                // 旧实现在没有推荐时整段静默消失，用户分不清"算过了没有结果"和"这块坏了"
                // （审计第二轮 R2-09 / 1.8）。给一句明确的话，字号与下面的理由行一致。
                Text("暂无推荐")
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
            } else {
                Divider()

                Text("猜你要粘贴")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)

                ForEach(historyStore.predictionSuggestionEntries.prefix(3)) { entry in
                    let reasonText = historyStore.predictionReasonByEntryID[entry.id] ?? ""

                    Button {
                        appDelegate.copyAndPasteHistoryEntry(id: entry.id)
                    } label: {
                        // 与 macOS 12 的状态栏菜单同一套脱敏标签（审计 R-43：
                        // 上一轮文档承诺"菜单只显示类型信息"，两版实现都不符）
                        let label = EntryPresentation.menuLabel(for: entry)
                        if reasonText.isEmpty {
                            Text(label)
                                .lineLimit(1)
                        } else {
                            Text(label + "\n" + reasonText)
                                .font(.system(size: 11))
                                .lineLimit(2)
                        }
                    }
                }

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
