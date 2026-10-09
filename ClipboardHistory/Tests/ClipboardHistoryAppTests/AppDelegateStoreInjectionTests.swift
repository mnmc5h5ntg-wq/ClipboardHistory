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
}
