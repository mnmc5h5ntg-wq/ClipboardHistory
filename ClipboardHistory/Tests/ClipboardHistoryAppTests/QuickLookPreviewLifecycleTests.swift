import XCTest
@testable import ClipboardHistoryApp

final class QuickLookPreviewLifecycleTests: XCTestCase {
    func testFirstLoadUsesExistingView() {
        var lifecycle = QuickLookPreviewLifecycle()
        let url = URL(fileURLWithPath: "/tmp/document.pdf")

        XCTAssertEqual(lifecycle.decision(for: url), .load(requiresFreshView: false))
    }

    func testRepeatedSameURLSkipsReload() {
        var lifecycle = QuickLookPreviewLifecycle()
        let url = URL(fileURLWithPath: "/tmp/document.pdf")

        lifecycle.markLoaded(url)

        XCTAssertEqual(lifecycle.decision(for: url), .skip)
    }

    func testChangingURLRequiresFreshView() {
        var lifecycle = QuickLookPreviewLifecycle()
        let firstURL = URL(fileURLWithPath: "/tmp/first.pdf")
        let secondURL = URL(fileURLWithPath: "/tmp/second.pdf")

        lifecycle.markLoaded(firstURL)

        XCTAssertEqual(lifecycle.decision(for: secondURL), .load(requiresFreshView: true))
    }

    func testDetachedViewRequiresFreshViewBeforeReloading() {
        var lifecycle = QuickLookPreviewLifecycle()
        let url = URL(fileURLWithPath: "/tmp/document.pdf")

        lifecycle.markLoaded(url)
        lifecycle.markDetached()

        XCTAssertEqual(lifecycle.decision(for: url), .load(requiresFreshView: true))
    }

    func testDetachedEmptyViewStillRequiresFreshViewBeforeLoading() {
        var lifecycle = QuickLookPreviewLifecycle()
        let url = URL(fileURLWithPath: "/tmp/document.pdf")

        lifecycle.markDetached()

        XCTAssertEqual(lifecycle.decision(for: url), .load(requiresFreshView: true))
    }
}
