import AppKit
import Foundation

enum LifecycleDebugLogSinkError: Error {
    case refusingSymbolicLinkTarget
}

/// 调试日志落盘器。线程安全，可在主线程与后台线程共用。
///
/// 设计要点：
/// - 只写 `~/Library/Logs/<App 名>/`（或 `CLIPBOARD_HISTORY_LOG_DIR` 指定目录），
///   目录 0700、文件 0600；不再使用 `/tmp` 这类全局可写目录中的可预测路径
///   （旧实现会跟随符号链接并截断目标）。
/// - 目标若是符号链接则拒绝写入（宁可没日志，也不写到别处去）。
/// - 打开/写入失败记入 `lastError`，不再"静默失败却假装还在写"。
final class LifecycleDebugLogSink: @unchecked Sendable {
    private let lock = NSLock()
    private let url: URL
    private var handle: FileHandle?
    private(set) var lastError: String?

    init(url: URL) {
        self.url = url
    }

    var fileURL: URL { url }

    func write(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        lock.lock()
        defer { lock.unlock() }
        if handle == nil {
            do {
                handle = try openForAppend()
                lastError = nil
            } catch {
                lastError = String(describing: error)
            }
        }
        guard let handle else { return }
        do {
            try handle.write(contentsOf: data)
        } catch {
            lastError = String(describing: error)
            try? handle.close()
            self.handle = nil
        }
    }

    func close() {
        lock.lock()
        defer { lock.unlock() }
        try? handle?.close()
        handle = nil
    }

    private func openForAppend() throws -> FileHandle {
        let fileManager = FileManager.default
        let directory = url.deletingLastPathComponent()
        if fileManager.fileExists(atPath: url.path) {
            let values = try? url.resourceValues(forKeys: [.isSymbolicLinkKey])
            if values?.isSymbolicLink == true {
                throw LifecycleDebugLogSinkError.refusingSymbolicLinkTarget
            }
        }
        if !fileManager.fileExists(atPath: directory.path) {
            try fileManager.createDirectory(
                at: directory,
                withIntermediateDirectories: true,
                attributes: [.posixPermissions: 0o700]
            )
        }
        if !fileManager.fileExists(atPath: url.path) {
            fileManager.createFile(atPath: url.path, contents: nil)
        }
        try fileManager.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
        return try FileHandle(forWritingTo: url)
    }
}

/// 生命周期/窗口状态调试日志。默认关闭，只在 `CLIPBOARD_HISTORY_DEBUG=1` 时启用。
///
/// 历史上这里出现过 `_isEnabledOverride: Bool? = true`（注释写"临时开启用于诊断红按钮问题"），
/// 后果有两个：正式版无条件把窗口标题抄送进 `/tmp`；以及测试进程里 `NSApp` 为 nil 时取值崩溃，
/// 直接终止整个测试套件（135 个用例只跑成 3 个）。
enum LifecycleDebugLogger {
    static let logFileName = "lifecycle_debug.log"
    static let environmentKey = "CLIPBOARD_HISTORY_DEBUG"
    static let logDirectoryEnvironmentKey = "CLIPBOARD_HISTORY_LOG_DIR"

    static var isEnabled: Bool {
        ProcessInfo.processInfo.environment[environmentKey] == "1"
    }

    static var appDisplayName: String {
        (Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String) ?? "时间剪史"
    }

    /// `CLIPBOARD_HISTORY_LOG_DIR` 让测试与离屏渲染工具把日志指到临时目录，
    /// 不污染真实 `~/Library/Logs`。
    static var logDirectory: URL {
        if let override = ProcessInfo.processInfo.environment[logDirectoryEnvironmentKey],
           !override.isEmpty {
            return URL(fileURLWithPath: override, isDirectory: true)
        }
        let base = FileManager.default.urls(for: .libraryDirectory, in: .userDomainMask).first
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library")
        return base
            .appendingPathComponent("Logs", isDirectory: true)
            .appendingPathComponent(appDisplayName, isDirectory: true)
    }

    static var logURL: URL { logDirectory.appendingPathComponent(logFileName) }

    private static let sink = LifecycleDebugLogSink(url: logURL)

    static func reset() {
        guard isEnabled else { return }
        sink.close()
        write("[DEBUG] ===== Lifecycle debug started \(Date()) =====\n")
    }

    static func log(_ message: @autoclosure () -> String) {
        guard isEnabled else { return }
        write("[DEBUG] \(message())\n")
    }

    /// 后台线程（如 OCR 队列）也可用的日志入口。
    /// 取代原先无条件写 `/tmp/ocr_debug.log` 的第二条通道。
    static func logFromBackground(_ message: @autoclosure () -> String) {
        guard isEnabled else { return }
        sink.write("[DEBUG] \(message())\n")
    }

    static let missingApplicationReason =
        "NSApp unavailable (non-GUI process); skipped window state dump"

    /// 纯函数：展开应用与窗口状态。`nil` 代表非 GUI 进程（单元测试、命令行工具）——
    /// 此时对 `NSApp` 这个隐式解包全局量取属性会崩，只能返回一行说明。
    @MainActor
    static func windowStateLines(for application: NSApplication?) -> [String] {
        guard let application else { return [missingApplicationReason] }
        var lines = [
            "NSApp.isActive = \(application.isActive)",
            "NSApp.isHidden = \(application.isHidden)",
            "NSApp.activationPolicy = \(application.activationPolicy().rawValue)",
            "NSApp.windows.count = \(application.windows.count)",
        ]
        for (index, window) in application.windows.enumerated() {
            lines.append(windowStateLine(window: window, index: index))
        }
        return lines
    }

    @MainActor
    static func windowStateLine(window: NSWindow, index: Int) -> String {
        "window[\(index)] title='\(window.title)' " +
        "isVisible=\(window.isVisible) " +
        "isMiniaturized=\(window.isMiniaturized) " +
        "isReleasedWhenClosed=\(window.isReleasedWhenClosed) " +
        "identifier=\(window.identifier?.rawValue ?? "nil") " +
        "class=\(type(of: window))"
    }

    @MainActor
    static func windowLayoutLine(
        window: NSWindow,
        prefix: String,
        dateFormatter: (NSRect?) -> String = format
    ) -> String {
        let styleMask = window.styleMask
        let titlebarDelta = window.frame.maxY - window.contentLayoutRect.maxY
        return "\(prefix) styleMaskRaw=\(styleMask.rawValue) " +
            "fullSizeContentView=\(styleMask.contains(.fullSizeContentView)) " +
            "titled=\(styleMask.contains(.titled)) " +
            "fullScreen=\(styleMask.contains(.fullScreen)) " +
            "resizable=\(styleMask.contains(.resizable)) " +
            "miniaturizable=\(styleMask.contains(.miniaturizable)) " +
            "closable=\(styleMask.contains(.closable)) " +
            "titlebarAppearsTransparent=\(window.titlebarAppearsTransparent) " +
            "titleVisibility=\(window.titleVisibility.rawValue) " +
            "toolbarExists=\(window.toolbar != nil) " +
            "toolbarVisible=\(window.toolbar?.isVisible.description ?? "nil") " +
            "frame=\(dateFormatter(window.frame)) " +
            "contentLayoutRect=\(dateFormatter(window.contentLayoutRect)) " +
            "titlebarDelta=\(String(format: "%.1f", titlebarDelta))"
    }

    @MainActor
    static func logAppState(_ context: String, menuBarController: MenuBarController? = nil) {
        guard isEnabled else { return }
        log("---- \(context) ----")
        let application: NSApplication? = NSApp
        windowStateLines(for: application).forEach { log($0) }
        if let windows = application?.windows {
            for (index, window) in windows.enumerated() {
                log(windowLayoutLine(window: window, prefix: "window[\(index)]"))
            }
        }
        menuBarController?.logStatusItemState(context: context)
    }

    @MainActor
    static func logKeyWindowLayout(_ context: String) {
        guard isEnabled else { return }
        let application: NSApplication? = NSApp
        guard let application else { return }
        log("---- key window layout: \(context) ----")
        guard let window = application.keyWindow ?? application.windows.first(where: { $0.isVisible }) else {
            log("no visible key window")
            return
        }
        log(windowLayoutLine(window: window, prefix: "window"))
    }

    /// 测试/排查用：实际落盘位置与最近一次写失败原因。
    static func debugFileURL() -> URL { sink.fileURL }
    static func debugLastError() -> String? { sink.lastError }

    private static func format(_ rect: NSRect?) -> String {
        guard let rect else { return "nil" }
        return "x:\(String(format: "%.1f", rect.origin.x)) " +
            "y:\(String(format: "%.1f", rect.origin.y)) " +
            "w:\(String(format: "%.1f", rect.size.width)) " +
            "h:\(String(format: "%.1f", rect.size.height))"
    }

    private static func write(_ text: String) {
        sink.write(text)
    }

    static func close() {
        sink.close()
    }
}
