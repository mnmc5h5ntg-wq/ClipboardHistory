import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R406：详情正文是同一个 `NSScrollView` 复用的。换选到另一条记录时，
/// 它必须把视口带回正文顶部，而不是把上一条的滚动偏移留给新记录。
@MainActor
final class DetailScrollResetTests: XCTestCase {
    private func makeStore() -> HistoryStore {
        HistoryStore(clipboardWriter: TestClipboardWriter(),
                     persistence: RecordingHistoryPersistence(),
                     retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
    }

    private func add(_ text: String, to store: HistoryStore, at seconds: TimeInterval) {
        store.add(ClipboardIntake.Entry(content: .text(text), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.TextEdit",
                                        sourceAppName: "文本编辑"),
                  timestamp: Date(timeIntervalSince1970: seconds))
    }

    private func findBodyScrollView(in view: NSView) -> NSScrollView? {
        if let scroll = view as? NSScrollView,
           scroll.documentView is ChineseSelectableNSTextView {
            return scroll
        }
        for sub in view.subviews {
            if let hit = findBodyScrollView(in: sub) { return hit }
        }
        return nil
    }

    func testSelectingAnotherEntryBringsTheBodyBackToTheTop() throws {
        _ = NSApplication.shared
        let store = makeStore()
        let longA = (0..<160).map { "A-\($0) 这是第一条记录的第 \($0) 行正文" }.joined(separator: "\n")
        let longB = (0..<160).map { "B-\($0) 这是第二条记录的第 \($0) 行正文" }.joined(separator: "\n")
        add(longA, to: store, at: 2)
        add(longB, to: store, at: 1)
        guard let first = store.entries.first(where: { $0.shortPreview.contains("A-0") }),
              let second = store.entries.first(where: { $0.shortPreview.contains("B-0") }) else {
            return XCTFail("夹具里两条长正文没有建出来 ⇒ 这条判据没有对象")
        }
        store.perform(.selectOnly(first))

        let host = NSHostingView(rootView: DetailView(historyStore: store))
        let window = NSWindow(contentRect: NSRect(x: -20000, y: -20000, width: 720, height: 520),
                              styleMask: [.titled], backing: .buffered, defer: false)
        window.contentView = host
        window.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        window.orderFrontRegardless()
        window.layoutIfNeeded()
        host.layoutSubtreeIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))

        guard let scroll = findBodyScrollView(in: host) else {
            return XCTFail("详情正文的 NSScrollView 不在树里 ⇒ 这条判据没有对象")
        }
        scroll.layoutSubtreeIfNeeded()
        guard let document = scroll.documentView else {
            return XCTFail("正文 scroll view 没有 documentView ⇒ 这条判据没有对象")
        }
        let maxOffset = max(0, document.frame.height - scroll.contentView.bounds.height)
        guard maxOffset > 100 else {
            return XCTFail("正文只有 \(Int(document.frame.height))pt 高而视口 \(Int(scroll.contentView.bounds.height))pt"
                           + " ⇒ 这一条根本没得滚，先修夹具再加判据")
        }
        // 断言的对象是**文本视图自己的可见原点**，不是 clip bounds 的 origin：
        // 后者会随文本内边距/字体在机器间差 11pt（runner 顶部 −46、本机 −57，R406 的 CI 红）。
        let topVisible = document.visibleRect.origin.y
        let topOffset = scroll.contentView.bounds.origin.y
        scroll.contentView.scroll(to: NSPoint(x: 0, y: maxOffset))
        scroll.reflectScrolledClipView(scroll.contentView)
        let before = scroll.contentView.bounds.origin.y
        XCTAssertGreaterThan(before, 100,
                             "滚到底没有生效（offset=\(before)）⇒ 旧行为在镜头外，这条判据没有对象")

        store.perform(.selectOnly(second))
        host.layoutSubtreeIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        let after = scroll.contentView.bounds.origin.y
        let afterVisible = document.visibleRect.origin.y
        CaptureReadings.emit("DETAIL_SCROLL_RESET 可滚高=\(Int(maxOffset)) 顶部参照=\(Int(topOffset))"
                             + " 旧偏移=\(Int(before)) 换选后=\(Int(after))"
                             + " 顶部可见=\(Int(topVisible)) 换选可见=\(Int(afterVisible))"
                             + " docOrigin=\(Int(document.frame.origin.y))")
        XCTAssertLessThanOrEqual(afterVisible, 1.0,
                                 "换选后正文可见原点是 \(Int(afterVisible))（顶部参照 \(Int(topVisible))，"
                                 + "clip 偏移 \(Int(topOffset))→\(Int(after))，可滚高 \(Int(maxOffset))）"
                                 + " ⇒ 新记录从中间开始读，用户分不清这是新记录的开头还是旧记录的位置")
    }
}
