// R424：Dock 图标状态 —— 主窗口关掉、App 不在前台时新到的剪辑在 Dock 上挂未读数，
// 回到前台清零。角标本体由 WindowServer 画（进程里没有视图可截），像素通道具名 NOT-RUN；
// 这里的证人分两层：纯读数（policy/tracker）+ 真实 `NSApplication.dockTile.badgeLabel` 往返。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class DockBadgeTests: XCTestCase {

    func testPolicyHidesZeroAndCapsAtNinetyNine() {
        XCTAssertNil(DockBadgePolicy.label(unseenCount: 0))
        XCTAssertNil(DockBadgePolicy.label(unseenCount: -3))
        XCTAssertEqual(DockBadgePolicy.label(unseenCount: 1), "1")
        XCTAssertEqual(DockBadgePolicy.label(unseenCount: 42), "42")
        XCTAssertEqual(DockBadgePolicy.label(unseenCount: 99), "99")
        XCTAssertEqual(DockBadgePolicy.label(unseenCount: 100), "99+")
        XCTAssertEqual(DockBadgePolicy.label(unseenCount: 10_000), "99+")
    }

    func testTrackerCountsOnlyEntriesArrivingWhileInactiveAndClearsOnActivation() {
        var tracker = DockBadgeTracker(entryCount: 2, isActive: true)
        tracker.noteEntryCount(5)
        XCTAssertNil(tracker.badgeLabel, "前台新到的剪辑不该挂角标：列表当场可见")

        tracker.noteActivation(false)
        tracker.noteEntryCount(8)
        XCTAssertEqual(tracker.badgeLabel, "3")

        tracker.noteEntryCount(9)
        XCTAssertEqual(tracker.badgeLabel, "4")

        tracker.noteActivation(true)
        XCTAssertNil(tracker.badgeLabel, "回到前台没有清零 ⇒ 角标会一直挂着")

        tracker.noteEntryCount(10)
        XCTAssertNil(tracker.badgeLabel, "激活后的新剪辑又计进未读")
    }

    func testTrackerClampsUnseenWhenHistoryShrinksWhileInactive() {
        var tracker = DockBadgeTracker(entryCount: 10, isActive: false)
        tracker.noteEntryCount(15)
        XCTAssertEqual(tracker.badgeLabel, "5")

        tracker.noteEntryCount(2)
        XCTAssertEqual(tracker.badgeLabel, "2", "历史被清到 2 条，角标却还报 5 条未读 ⇒ 读数比记录还多")

        tracker.noteEntryCount(0)
        XCTAssertNil(tracker.badgeLabel)
    }

    /// 产品入口：真实的 `HistoryStore.add` → 真实的 `NSApplication.dockTile.badgeLabel`。
    /// 「旧读数」这一半在控制器创建之前量：同样在攒记录，Dock 上什么都不挂。
    func testRealDockTileShowsUnseenCountOnlyWhileInactive() {
        let dockTile = NSApplication.shared.dockTile
        let original = dockTile.badgeLabel
        dockTile.badgeLabel = nil
        defer { dockTile.badgeLabel = original }

        var isActive = true
        let store = makeStore()
        addEntry(store, "r424-old-a")
        addEntry(store, "r424-old-b")
        XCTAssertNil(dockTile.badgeLabel,
                     "旧读数：还没有 Dock 角标这一档，攒了两条记录也不该有数字")

        isActive = false
        let controller = DockBadgeController(store: store, isAppActive: { isActive })
        controller.applicationDidResignActive()
        addEntry(store, "r424-new-a")
        addEntry(store, "r424-new-b")
        addEntry(store, "r424-new-c")
        XCTAssertEqual(dockTile.badgeLabel, "3",
                       "后台新到 3 条，Dock 角标应读 3（旧/新同一把尺：dockTile.badgeLabel）")

        controller.applicationDidBecomeActive()
        XCTAssertNil(dockTile.badgeLabel, "回到前台后角标没有清零")

        CaptureReadings.emit("DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server"
              + " inProcessContentView=\(dockTile.contentView == nil ? "none" : "present")"
              + " badgeAfterActivate=\(dockTile.badgeLabel ?? "nil")")
    }

    func testAppDelegateWiresTheControllerOnConfigureAndBothActivationEdges() throws {
        let delegate = codeOnly(try productSource(named: "Managers/AppDelegate.swift"))
        XCTAssertTrue(delegate.contains(
            "if dockBadgeController == nil {\n"
            + "            dockBadgeController = DockBadgeController(store: historyStore)\n"
            + "        }"),
                      "configure() 没有建 DockBadgeController（或不是幂等的）")
        XCTAssertTrue(delegate.contains("dockBadgeController?.applicationDidBecomeActive()"),
                      "applicationDidBecomeActive 没有清角标")
        XCTAssertTrue(delegate.contains("dockBadgeController?.applicationDidResignActive()"),
                      "applicationDidResignActive 没有把「未读窗口」打开")

        let controller = codeOnly(try productSource(named: "Managers/DockBadgeController.swift"))
        XCTAssertTrue(controller.contains("NSApplication.shared.dockTile.badgeLabel = $0"),
                      "默认的 applyBadge 没有写真实 Dock 角标 ⇒ 产品里角标永远是 nil")
    }

    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil),
            maxEntries: 50
        )
    }

    private func addEntry(_ store: HistoryStore, _ text: String) {
        store.add(
            ClipboardIntake.Entry(
                content: .text(text),
                thumbnail: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            ),
            timestamp: Date(timeIntervalSince1970: 1_800_000_000)
        )
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "DockBadgeTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
