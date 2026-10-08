import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R-01 / R-30 的回归守卫：调试日志必须由环境变量门控、落在用户目录、
/// 并且不再往 `/tmp` 这类全局可写目录写内容。
@MainActor
final class DebugLoggingTests: XCTestCase {
    func testLoggingIsDisabledUnlessEnvironmentFlagIsSet() {
        XCTAssertFalse(
            LifecycleDebugLogger.isEnabled,
            "默认必须关闭：曾用 _isEnabledOverride=true 硬开，导致正式版抄送窗口标题 + 测试套件崩"
        )
        setenv(LifecycleDebugLogger.environmentKey, "1", 1)
        XCTAssertTrue(LifecycleDebugLogger.isEnabled)
        unsetenv(LifecycleDebugLogger.environmentKey)
        XCTAssertFalse(LifecycleDebugLogger.isEnabled)
    }

    func testLogPathIsInsideUserLibraryAndNeverTmp() {
        let url = LifecycleDebugLogger.logURL
        XCTAssertFalse(url.path.hasPrefix("/tmp"), "日志不得落在 /tmp：\(url.path)")
        XCTAssertTrue(url.path.contains("/Library/Logs/"), "日志应在用户 Library/Logs：\(url.path)")
    }

    func testLogDirectoryCanBeRedirectedByEnvironmentForTests() {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent("logdir-\(UUID().uuidString)", isDirectory: true)
        setenv(LifecycleDebugLogger.logDirectoryEnvironmentKey, directory.path, 1)
        defer { unsetenv(LifecycleDebugLogger.logDirectoryEnvironmentKey) }
        XCTAssertEqual(LifecycleDebugLogger.logDirectory, directory)
    }

    func testSinkCreatesPrivateDirectoryAndFileWithOwnerOnlyPermissions() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("sink-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let url = root.appendingPathComponent("Logs/时间剪史/lifecycle_debug.log")
        let sink = LifecycleDebugLogSink(url: url)
        sink.write("first\n")
        sink.write("second\n")
        sink.close()

        let written = try String(contentsOf: url, encoding: .utf8)
        XCTAssertEqual(written, "first\nsecond\n")
        XCTAssertNil(sink.lastError)

        let fileMode = permissions(of: url)
        XCTAssertEqual(fileMode, 0o600, "日志文件必须仅本人可读写")
        let directoryMode = permissions(of: url.deletingLastPathComponent())
        XCTAssertEqual(directoryMode, 0o700, "日志目录必须仅本人可进入")
    }

    func testSinkRefusesSymbolicLinkTargetAndLeavesRealFileAlone() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("symlink-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)

        let realTarget = root.appendingPathComponent("victim.txt")
        try "SENTINEL".write(to: realTarget, atomically: true, encoding: .utf8)
        let link = root.appendingPathComponent("lifecycle_debug.log")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: realTarget)

        let sink = LifecycleDebugLogSink(url: link)
        sink.write("should not be written\n")
        XCTAssertNotNil(sink.lastError, "符号链接目标必须拒绝写入并记录原因")
        XCTAssertEqual(try String(contentsOf: realTarget, encoding: .utf8), "SENTINEL")
    }

    func testWindowStateLinesIsSafeWhenApplicationIsMissing() {
        // 非 GUI 进程里对 NSApp 取属性会崩；纯函数必须只返回一行说明。
        XCTAssertEqual(
            LifecycleDebugLogger.windowStateLines(for: nil),
            [LifecycleDebugLogger.missingApplicationReason]
        )
    }

    private func permissions(of url: URL) -> Int {
        let attributes = try? FileManager.default.attributesOfItem(atPath: url.path)
        let mode = attributes?[.posixPermissions] as? NSNumber
        return Int(truncating: mode ?? NSNumber(value: 0))
    }
}

/// R-44：产品 target 里不得出现网络 API（"本地优先"承诺的机器化守卫）。
final class LocalOnlyGuardTests: XCTestCase {
    func testProductSourcesDoNotReferenceNetworkingAPIs() throws {
        // 从测试文件位置逐级上溯，找到包含 Sources/ClipboardHistoryApp 的包根目录。
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var url: URL?
        for _ in 0..<6 {
            let probe = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
            if FileManager.default.fileExists(atPath: probe.path) {
                url = candidate.appendingPathComponent("Sources", isDirectory: true)
                break
            }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let url else {
            throw XCTSkip("找不到包根目录的 Sources（从 \(#filePath) 上溯 6 层未果）")
        }
        let forbidden = ["URLSession", "NWConnection", "CFStream", "Socket(", "WebKit.loadURL"]
        let forbiddenFiles = ["AIProviderModels.swift", "AIPrivacyPolicy.swift"]
        var violations: [String] = []
        let enumerator = FileManager.default.enumerator(at: url, includingPropertiesForKeys: nil)
        while let file = enumerator?.nextObject() as? URL {
            guard file.pathExtension == "swift" else { continue }
            // AI 设计稿文件本身含 URL 字段定义，属于未接线的设计稿，跳过。
            if forbiddenFiles.contains(file.lastPathComponent) { continue }
            guard let text = try? String(contentsOf: file, encoding: .utf8) else { continue }
            for needle in forbidden where text.contains(needle) {
                violations.append("\(file.lastPathComponent): \(needle)")
            }
        }
        XCTAssertEqual(violations, [], "产品代码出现网络 API 引用：\(violations)")
    }
}
