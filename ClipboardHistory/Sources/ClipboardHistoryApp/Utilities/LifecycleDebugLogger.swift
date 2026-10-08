import AppKit
import Foundation

@MainActor
enum LifecycleDebugLogger {
    private static let fileName = "时间剪史_lifecycle_debug.log"
        private static let _isEnabledOverride: Bool? = true  // 临时开启用于诊断红按钮问题
    private static var isEnabled: Bool { _isEnabledOverride ?? (ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_DEBUG"] == "1") }
    private static let logURL = URL(fileURLWithPath: "/tmp/\(fileName)")
    private static var fileHandle: FileHandle?

    static func reset() {
        guard isEnabled else { return }
        close()
        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        fileHandle = try? FileHandle(forWritingTo: logURL)
        write("[DEBUG] ===== Lifecycle debug started \(Date()) =====\n")
    }

    static func log(_ message: @autoclosure () -> String) {
        guard isEnabled else { return }
        write("[DEBUG] \(message())\n")
    }

    @MainActor
    static func logAppState(_ context: String, menuBarController: MenuBarController? = nil) {
        guard isEnabled else { return }
        log("---- \(context) ----")
        log("NSApp.isActive = \(NSApp.isActive)")
        log("NSApp.isHidden = \(NSApp.isHidden)")
        log("NSApp.activationPolicy = \(NSApp.activationPolicy().rawValue)")
        log("NSApp.windows.count = \(NSApp.windows.count)")
        for (index, window) in NSApp.windows.enumerated() {
            log(
                "window[\(index)] title='\(window.title)' " +
                "isVisible=\(window.isVisible) " +
                "isMiniaturized=\(window.isMiniaturized) " +
                "isReleasedWhenClosed=\(window.isReleasedWhenClosed) " +
                "identifier=\(window.identifier?.rawValue ?? "nil") " +
                "class=\(type(of: window))"
            )
            logWindowLayout(window, index: index)
        }
        menuBarController?.logStatusItemState(context: context)
    }

    @MainActor
    static func logKeyWindowLayout(_ context: String) {
        guard isEnabled else { return }
        log("---- key window layout: \(context) ----")
        guard let window = NSApp.keyWindow ?? NSApp.windows.first(where: { $0.isVisible }) else {
            log("no visible key window")
            return
        }
        logWindowLayout(window, index: nil)
    }

    @MainActor
    private static func logWindowLayout(_ window: NSWindow, index: Int?) {
        let prefix = index.map { "window[\($0)]" } ?? "window"
        let styleMask = window.styleMask
        let fullSize = styleMask.contains(.fullSizeContentView)
        let titled = styleMask.contains(.titled)
        let fullScreen = styleMask.contains(.fullScreen)
        let resizable = styleMask.contains(.resizable)
        let miniaturizable = styleMask.contains(.miniaturizable)
        let closable = styleMask.contains(.closable)
        let titlebarDelta = window.frame.maxY - window.contentLayoutRect.maxY
        log(
            "\(prefix) styleMaskRaw=\(styleMask.rawValue) " +
            "fullSizeContentView=\(fullSize) titled=\(titled) fullScreen=\(fullScreen) " +
            "resizable=\(resizable) miniaturizable=\(miniaturizable) closable=\(closable)"
        )
        log(
            "\(prefix) titlebarAppearsTransparent=\(window.titlebarAppearsTransparent) " +
            "titleVisibility=\(window.titleVisibility.rawValue) " +
            "toolbarExists=\(window.toolbar != nil) toolbarVisible=\(window.toolbar?.isVisible.description ?? "nil")"
        )
        log(
            "\(prefix) frame=\(format(window.frame)) " +
            "contentLayoutRect=\(format(window.contentLayoutRect)) " +
            "contentViewFrame=\(format(window.contentView?.frame)) " +
            "titlebarDelta=\(String(format: "%.1f", titlebarDelta))"
        )
    }

    private static func format(_ rect: NSRect?) -> String {
        guard let rect else { return "nil" }
        return "x:\(String(format: "%.1f", rect.origin.x)) " +
            "y:\(String(format: "%.1f", rect.origin.y)) " +
            "w:\(String(format: "%.1f", rect.size.width)) " +
            "h:\(String(format: "%.1f", rect.size.height))"
    }

    private static func write(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        do {
            if fileHandle == nil {
                FileManager.default.createFile(atPath: logURL.path, contents: nil)
                fileHandle = try? FileHandle(forWritingTo: logURL)
            }
            try fileHandle?.seekToEnd()
            try fileHandle?.write(contentsOf: data)
        } catch {
            close()
        }
    }

    static func close() {
        try? fileHandle?.close()
        fileHandle = nil
    }
}
