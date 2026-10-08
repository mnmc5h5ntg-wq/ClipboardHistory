import AppKit

/// "把 ⌘V 打到前一个 App" 这条链路的抽象。
///
/// 抽出来的原因不是洁癖：`osascript` 失败（最常见是系统没授权 Automation）过去完全静默 ——
/// `Process.launch()` 之后没人看退出码，用户看到的就是"点了菜单没反应"（审计 R-13）。
/// 有了这层协议，失败可注入、可测，真实实现也不会被测试误触发（真的按下 ⌘V 会写进用户当前界面）。
@MainActor
protocol PasteKeyExecuting {
    /// 返回 `nil` 表示成功；否则返回可直接展示给用户的失败原因。
    /// 必须是 `async`：实现要在后台等子进程，主线程等待会让界面冻结。
    func synthesizePaste() async -> String?
}

/// 用 `/usr/bin/osascript` 驱动 System Events 按下 ⌘V。
/// （`CGEvent.postToPid` 在 macOS 15 上被拦，所以仍走 AppleScript。）
@MainActor
struct SystemEventsPasteKey: PasteKeyExecuting {
    nonisolated static let pasteScript = "tell application \"System Events\" to keystroke \"v\" using command down"

    func synthesizePaste() async -> String? {
        await withCheckedContinuation { continuation in
            // 不能在 main 上 waitUntilExit：弹 TCC 授权框时那一句能把整个界面挂死。
            DispatchQueue.global(qos: .userInitiated).async {
                let reason = Self.run(osascriptArguments: ["-e", Self.pasteScript])
                continuation.resume(returning: reason)
            }
        }
    }

    /// 真正跑子进程。**测试里不要调用**：它会往用户当前的前台 App 按键。
    nonisolated static func run(osascriptArguments arguments: [String]) -> String? {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        task.arguments = arguments
        let errorPipe = Pipe()
        task.standardError = errorPipe
        task.standardOutput = Pipe()
        do {
            try task.run()
        } catch {
            return "无法启动 osascript：\(error.localizedDescription)"
        }
        // 先把 stderr 读空再等退出：子进程写满管道缓冲时，先 wait 会死锁。
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
        task.waitUntilExit()
        guard task.terminationStatus != 0 else { return nil }
        return reason(fromStderr: String(decoding: errorData, as: UTF8.self))
    }

    /// 把 AppleScript 的报错翻译成人能照着做的一句话。
    /// 未知错误只取首行并截断，且只可能是 osascript 自己的诊断文本 ——
    /// 这条链路上没有任何地方读剪贴板内容，所以不会把用户数据带进界面或日志。
    nonisolated static func reason(fromStderr stderr: String) -> String {
        let firstLine = stderr
            .split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .first(where: { !$0.isEmpty }) ?? ""
        if firstLine.contains("-1743")
            || firstLine.localizedCaseInsensitiveContains("not authorized")
            || firstLine.localizedCaseInsensitiveContains("errAEEventNotPermitted")
            || firstLine.contains("未获授权") || firstLine.contains("不允许") || firstLine.contains("无权") {
            return "系统未授权本 App 控制「System Events」，无法自动粘贴。请在「系统设置 → 隐私与安全性 → 自动化」里允许后重试；记录本身已复制到剪贴板，可手动粘贴。"
        }
        if firstLine.localizedCaseInsensitiveContains("does not respond") || firstLine.contains("没有响应") {
            return "「System Events」没有响应，自动粘贴未完成。记录已在剪贴板里，可手动粘贴。"
        }
        if firstLine.isEmpty {
            return "自动粘贴未完成（osascript 退出码非 0）。记录已在剪贴板里，可手动粘贴。"
        }
        return "自动粘贴未完成：\(firstLine.prefix(200))。记录已在剪贴板里，可手动粘贴。"
    }
}
