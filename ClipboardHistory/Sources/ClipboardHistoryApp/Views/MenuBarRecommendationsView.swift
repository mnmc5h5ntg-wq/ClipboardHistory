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
                // 旧实现在没有推荐时整段静默消失，用户分不清"算过了没结果"和"这块坏了"
                // （审计第二轮 R2-09 / 1.8）。而"还在算"也不能说成"没有"：菜单是同步画的，
                // 刷新是异步的，所以这里跟着 `isRefreshingPredictions` 分两种说法。
                //
                // 字号与图标现在取自 `StatePresentation`（审计 §4 U-5）：以前这句是 11pt、
                // 横幅是 `.callout`、空态是 13pt，同一件"没有东西可看"在三个地方三种大小。
                // 加载态刻意不画转圈 —— 菜单是同步渲染的，一个不动的循环箭头加一句"正在整理"
                // 比一个真转的指示器更诚实，也不会让人以为点了能取消。
                let kind: StatePresentation.Kind = historyStore.isRefreshingPredictions ? .loading : .empty
                StateLine(kind: kind,
                          message: historyStore.isRefreshingPredictions ? "正在整理推荐…" : "暂无推荐")
                    // 刻意**不挂** `.transition`（R5 删掉了原来那条）：这个文件里没有任何动画事务
                    // （`grep -c "animation(" = 0`），而 `MenuBarExtraStyle.menu` 的内容会被编译成真的
                    // `NSMenu`（账本 D-055 / M15 实测），SwiftUI 的过渡在那一层根本不执行。
                    // 留着一行不会执行的声明，只会让下一个人以为这里已经淡过了。
            } else {
                Divider()

                Text("猜你要粘贴")
                    .font(.system(size: VisualFont.meta, weight: .semibold))
                    .foregroundStyle(.secondary)

                ForEach(historyStore.predictionSuggestionEntries.prefix(3)) { entry in
                    let reasonText = historyStore.predictionReasonByEntryID[entry.id] ?? ""

                    Button {
                        appDelegate.copyAndPasteHistoryEntry(id: entry.id)
                    } label: {
                        // 与 macOS 12 的状态栏菜单同一套脱敏标签（审计 R-43：
                        // 上一轮文档承诺"菜单只显示类型信息"，两版实现都不符）
                        let label = EntryPresentation.menuLabel(for: entry)
                        // 第三轮审计 U-1：macOS 菜单项一律左对齐、不画自绘底、不把内部指标端出来。
                        // 旧写法是"标题\n理由"两行居中卡片，理由还带着 24% 这种原始分数。
                        // 现在：标题在左、理由在右且更弱色，一行读完，与系统菜单同一套语言。
                        HStack(alignment: .firstTextBaseline, spacing: 10) {
                            Text(label)
                                .lineLimit(1)
                            Spacer(minLength: 12)
                            if !reasonText.isEmpty {
                                Text(reasonText)
                                    .font(.system(size: VisualFont.meta))
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                                    .truncationMode(.tail)
                                    .layoutPriority(-1)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                    }
                    // 系统菜单项没有按钮底：`.plain` 去掉 SwiftUI 默认那层，
                    // 悬停高亮交给菜单自己的选中态（帧里之前那种"卡片"就是这么来的）。
                    // 同理**不接按压态**（R4）：菜单自己的高亮已经是"收到了"的证据，
                    // 再叠一层自绘底会把 U-1 刚拆掉的卡片感装回来。
                    .buttonStyle(.plain)
                }

                Divider()
                Button {
                    historyStore.perform(.dismissAllRecommendations)
                } label: {
                    Text("都不是我想要的")
                        .font(.system(size: VisualFont.meta))
                    // R235（D-220）：不在这里钉颜色，与 `MenuBarController` 那棵 12 的树同一条决定
                    // —— 写死的墨在静置与选中两种底上都读不过自家正文参照（实测见那条）。
                }
                .buttonStyle(.plain)
                .frame(maxWidth: .infinity, alignment: .leading)
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
