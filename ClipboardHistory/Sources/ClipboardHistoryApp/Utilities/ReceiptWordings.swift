import Foundation

/// 界面回执的措辞集中在这一个文件里（R43 / D-102）。
///
/// 为什么集中：这一族的话**同时**被三处产品入口消费（设置页的导出反馈、导出存档、导入存档），
/// 而它们的坏法是一样的 —— 把 `error.localizedDescription` 直接拼进界面。
/// 分开放就会分家：R41 收了"写剪贴板"那一条（D-100），这一族的另外三个出口当时没人管。
///
/// 这一族**只**管措辞：原文一律由调用点写进 `LifecycleDebugLogger`，
/// 界面只留"发生了什么 + 下一步"。
///
/// ### `FeedbackExportReceipt`
/// 「导出反馈数据」这一条回执该说什么（R43 / BACKLOG 62 / D-102）。
///
/// 修前两件事同时不合格：
/// ① **同一件事说两遍**：`exportFeedbackData` 既写 `exportMessage`（行内 `ReceiptLine`）
///    又置 `showExportAlert = true`（模态弹窗）⇒ 用户先被一个模态打断，再在窗口里看到同一句话。
///    仓库里另外三处回执（清空历史、导出/导入存档、排除名单）**都是行内**，
///    所以这里跟着它们走，而不是反过来给那一族加模态。
/// ② **失败那条直出系统原文**：`exportMessage = "导出失败：\(error.localizedDescription)"`，
///    而 `ExportError` 不是 `LocalizedError` ⇒ 界面会写
///    "The operation couldn't be completed. (…ErrorDomain error N.)"。
///    这正是 R41 的 U-67 在**另一个出口**上的复现（D-100 只收了"写剪贴板"那条路）。
///
/// 为什么单独做成纯函数：回执的**内容**与"谁去点导出"无关，
/// 而 `exportFeedbackData` 里夹着 `NSSavePanel` 与 Finder —— 那部分测试进程碰不得。
/// 把措辞抽出来，真值表就能不开窗口、不弹面板地判每一格（AGENTS.md 定义 of done 第 1 条里
/// "只测纯函数的文件要指出管线级判据在哪"：管线级是
/// `SettingsFailureReceiptTests.testExportFeedbackActionSpeaksThroughTheMapperOnce`
/// 与 `testArchiveActionsSpeakThroughTheMapperAndLogTheRawError`）。
enum FeedbackExportReceipt {
    /// 成功：只说文件叫什么，不庆祝。
    static func success(fileName: String) -> String { "已导出：\(fileName)" }

    /// 没数据可导 —— 这不是错误，措辞也不许写成错误。
    static let noData = "暂无反馈数据可导出"

    /// 失败：一句"发生了什么" + 一句"下一步"。**不**含系统原文。
    ///
    /// 原文交给调用点写日志（诊断要原文，界面要下一步 —— 与 D-100 同一条分工）。
    /// 未分类错误也说"文件没有生成"：`exportToFile` 的三个抛出点
    /// （找不到 Application Support / 编码结果为空 / 写盘失败）**都在写出文件之前或之中**，
    /// 所以这句话对每一格都是真的；而它比"说错方向"更安全 ——
    /// 用户听到"没生成"会再点一次导出，听到"已生成"才会被误导去找一个不存在的文件。
    static func failure(_ error: Error) -> String {
        switch error {
        case RecommendationFeedbackStore.ExportError.noData:
            // 竞态：判空之后、写盘之前数据被清空。说"暂无"而不是"失败"。
            return noData
        case RecommendationFeedbackStore.ExportError.writingFailed:
            return "导出失败：这些反馈数据没能写进磁盘，文件没有生成。"
                + "请确认磁盘没有写满、这个 App 的数据目录可写，再试一次。"
        default:
            return "导出失败：系统拒绝了这次导出，文件没有生成。请稍后重试。"
        }
    }
}

/// 导出 / 导入**存档**那两条失败回执（R43 / BACKLOG 62 的第二、第三个出口）。
///
/// 修前它们写在 `SettingsWindowController` 的两个注入闭包里：
/// `"导出失败：\(error.localizedDescription)"` 与 `"导入失败：\(error.localizedDescription)"`。
/// 这两条路上的错误多半来自 `Data(contentsOf:)` 与 `JSONDecoder`（都是 `NSError`），
/// `localizedDescription` 在中文系统上也常常是一句 "The operation couldn't be completed. …"
/// 或 "The file doesn't exist." —— 用户读不出下一步。
///
/// "记录没有任何变化"这句是**查过**才写的：`importArchiveJSON` 的两个抛出点
/// （读文件、`ArchiveTransfer.import`）都在 `entries` 被改之前
/// （`HistoryStore.swift:493-495`），所以失败之后列表还是原来那份，
/// 这句话对每一格都成立。以后有人把解码改成流式就地写入，这句就会变成假话 ——
/// 真值表第 ④ 格钉的就是它。
enum ArchiveTransferReceipt {
    /// 导出失败：文件没写成，历史本身没动。
    static func exportFailed(_ error: Error) -> String {
        "导出失败：这个文件没有写成，历史记录本身没有任何变化。"
            + "请确认磁盘没有写满、目标位置可写，再试一次。"
    }

    /// 导入失败：历史没被改动，用户可以先确认文件还在。
    static func importFailed(_ error: Error) -> String {
        "导入失败：这个文件没能读进历史，记录没有任何变化。"
            + "请确认文件还在原来的位置、是本项目导出的 JSON，再试一次。"
    }
}
