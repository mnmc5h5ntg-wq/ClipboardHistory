import XCTest
@testable import ClipboardHistoryApp

/// 账本 R2-17 / 决策 D-019：`AppDelegate` 以前只有隐式 init，而它第一个被求值的成员就是
/// `static let sharedHistoryStore = HistoryStore()` —— 任何想"安全地构造 AppDelegate"的尝试
/// （比如拍菜单栏面板的帧）都会先去读用户真实存档，而 `HOME` 重定向实测不改变
/// `applicationSupportDirectory`，所以审计只能把菜单栏视觉标 NOT-RUN。
///
/// 现在有了注入接缝。这里钉住两件事：注入的 store 真的被用上；不注入时产品路径一字不变。
@MainActor
final class AppDelegateStoreInjectionTests: XCTestCase {
    func testInjectedStoreIsTheOneTheDelegateUses() {
        let injected = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        let delegate = AppDelegate(historyStore: injected)
        XCTAssertTrue(delegate.historyStore === injected,
                      "注入的 store 没有被使用，接缝等于不存在")
    }

    func testDefaultInitStillUsesTheSharedStore() {
        // 产品路径不能被接缝改变：默认构造必须仍然拿到全局共享 store。
        XCTAssertTrue(AppDelegate().historyStore === AppDelegate.sharedHistoryStore)
    }

    /// 这条是 v1.4.8 候选包启动即闪退的守卫（D-019 的副作用）。
    ///
    /// `@NSApplicationDelegateAdaptor(AppDelegate.self)` 存的是**元类型**，它通过 ObjC 发 `-init`；
    /// 而 Swift 侧写 `AppDelegate()` 会解析到 `init(historyStore: nil)`（默认参数），
    /// 永远碰不到那条路径 —— 所以当时上面两条用例全绿、CI 全绿，产品一打开就死。
    /// 编译器给未实现的 `-init` 留的是 trap 桩，一旦走到就是进程级 `SIGTRAP`（整个测试进程一起没），
    /// 这正是"红"的形状：修之前这条用例让 `swift test` 崩，修之后它正常通过。
    func testAppDelegateRespondsToTheObjCMetatypeInit() {
        let type: NSObject.Type = AppDelegate.self
        let delegate = type.init()
        XCTAssertTrue((delegate as? AppDelegate) !== nil, "元类型 init 出来的不是 AppDelegate")
        XCTAssertTrue((delegate as! AppDelegate).historyStore === AppDelegate.sharedHistoryStore,
                      "SwiftUI 走的那条构造路径没有拿到共享 store")
    }

    /// 便宜的兜底：即使上面那条被删，源码里也必须显式实现 `-init`。
    /// 只声明带默认参数的 `init(historyStore:)` 在 Swift 看来"有 init()"，ObjC 看来没有。
    func testAppDelegateDeclaresOverrideInit() throws {
        let source = try appDelegateSource()
        let code = source.split(separator: "\n").map { line -> String in
            if let cut = line.range(of: "//") { return String(line[..<cut.lowerBound]) }
            return String(line)
        }.joined(separator: "\n")
        XCTAssertTrue(code.contains("override convenience init()") || code.contains("override init()"),
                      "AppDelegate 没有显式 override init()：SwiftUI 通过 ObjC 元类型调 -init 会 trap（见 D-019 的回归）")
    }

    private func appDelegateSource() throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent(
                "Sources/ClipboardHistoryApp/Managers/AppDelegate.swift")
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到 AppDelegate.swift（从 \(#filePath) 上溯 6 层未果）")
    }
}
