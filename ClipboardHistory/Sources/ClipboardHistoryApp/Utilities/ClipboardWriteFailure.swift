import Foundation

/// 一次"写剪贴板失败"里，界面必须知道的**两件事**（R41 / U-67 / D-100）。
///
/// ① **一句人话**。修前这里是 `error.localizedDescription` 直出：
/// 已知那四种 `ClipboardWriteError` 有中文，但**任何非本模块抛出的错误**（AppKit 的
/// `NSPOSIXErrorDomain` / `OSStatus` 之类）会把 "The operation couldn't be completed.
/// (NSOSStatusErrorDomain error -100.)" 这样的英文原文搬进横幅 —— 读不懂，也没给下一步。
/// 仓库里已有成例：`SystemEventsPasteKey.reason(fromStderr:)` 就是把 -1743 翻成
/// "去「系统设置 → 隐私与安全性 → 自动化」"。这一层做的是同一件事。
///
/// ② **我们有没有已经把剪贴板清空**。这一条是本轮真正的发现：
/// `SystemClipboardWriter.write` 的顺序是「先校验 → `pasteboard.clearContents()` → 再写入」，
/// 而三种"写入失败"（文本 / 图片 / 文件）全部发生在**清空之后**。
/// 也就是说：那三种失败发生时，用户原来的剪贴板内容**已经没了**。
/// 而 R40 那句回执写的是"剪贴板里仍是原来的内容，没有被替换" ——
/// 恰好在这三种失败里**说了假话**。（`fileDoesNotExist` 抛在清空之前，那句才是对的。）
/// 一个只用来报告失败的回执，不能反过来成为第二个缺陷。
///
/// 为什么不复用 `ClipboardWriteError.errorDescription`：那是"错误是什么"，
/// 而回执要说的是"现在怎么办 + 你的东西还在不在"。两者放一起会互相拖累
/// （日志里想要原文，界面上想要下一步）。原文继续进 `LifecycleDebugLogger`。
struct ClipboardWriteFailure: Equatable {
    /// 界面上那一句人话（含下一步）。**不**含系统原文，也**不**含条目内容。
    let message: String
    /// 这次失败是否发生在 `clearContents()` 之后 —— 决定"原来的内容还在不在"怎么说。
    let clearedPasteboard: Bool

    /// 分类一个任意错误。未知错误按**保守**处理：当作已经清空过。
    /// 理由：猜错方向的代价不对称 —— 说"还在"而实际没了，用户会去粘一个空的东西
    /// 或者粘出上一条无关内容；说"没了"而实际还在，他只是重新复制一次。
    static func classify(_ error: Error) -> ClipboardWriteFailure {
        guard let writeError = error as? ClipboardWriteError else {
            return ClipboardWriteFailure(
                message: "系统剪贴板拒绝写入（未分类错误）。这条记录本身没有变化，请重新复制一次。",
                clearedPasteboard: true)
        }
        switch writeError {
        case .fileDoesNotExist:
            // 抛在 `clearContents()` 之前 ⇒ 剪贴板确实没被动过。
            return ClipboardWriteFailure(
                message: "文件已被移动或删除，这条没能复制。请从原来的位置再复制一次。",
                clearedPasteboard: false)
        case .failedToWriteText:
            return ClipboardWriteFailure(
                message: "文本没能写进系统剪贴板（常被其他应用短暂占用）。",
                clearedPasteboard: true)
        case .failedToWriteImage:
            return ClipboardWriteFailure(
                message: "图片没能写进系统剪贴板（常被其他应用短暂占用）。",
                clearedPasteboard: true)
        case .failedToWriteFileURL:
            return ClipboardWriteFailure(
                message: "文件没能写进系统剪贴板（常被其他应用短暂占用）。",
                clearedPasteboard: true)
        }
    }
}
