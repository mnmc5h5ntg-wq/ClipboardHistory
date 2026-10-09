import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-02（1.10）：键盘用户到不了列表。方向键的落点计算是纯函数，
/// 在这里逐格钉住；"在屏焦点链真的能走到列表"由 `UIInteractionProbeTests` 量
/// （需要 `CLIPBOARD_HISTORY_UI_INTERACTION=1`，因为它会开窗抢前台）。
final class SidebarKeyboardNavigationTests: XCTestCase {
    func testArrowDownFromNoSelectionStartsAtTheFirstRow() {
        XCTAssertEqual(SidebarKeyboardNavigation.targetIndex(currentIndex: nil, count: 5, direction: .down), 0)
    }

    func testArrowUpFromNoSelectionStartsAtTheLastRow() {
        XCTAssertEqual(SidebarKeyboardNavigation.targetIndex(currentIndex: nil, count: 5, direction: .up), 4,
                       "与 Finder/邮件一致：没有选中项时向上从最后一条开始")
    }

    func testArrowsMoveOneRowAndDoNotWrap() {
        XCTAssertEqual(SidebarKeyboardNavigation.targetIndex(currentIndex: 2, count: 5, direction: .down), 3)
        XCTAssertEqual(SidebarKeyboardNavigation.targetIndex(currentIndex: 2, count: 5, direction: .up), 1)
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: 4, count: 5, direction: .down),
                     "到底了不许绕回第一条：绕回会让键盘用户以为自己还在往下走")
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: 0, count: 5, direction: .up))
    }

    func testLeftRightHaveNoMeaningInASingleColumnList() {
        for index in [nil, 0, 2, 4] {
            XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: index, count: 5, direction: .left))
            XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: index, count: 5, direction: .right))
        }
    }

    func testEmptyAndDegenerateInputsDoNotCrash() {
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: nil, count: 0, direction: .down))
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: 0, count: 0, direction: .up))
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: 0, count: 5, direction: .down, step: 0))
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(currentIndex: 0, count: 5, direction: .down, step: -3))
        XCTAssertEqual(SidebarKeyboardNavigation.targetIndex(currentIndex: 0, count: 1, direction: .down), nil)
    }

    func testPageStepKeepsOneRowOfOverlapAndSurvivesTinyViewports() {
        XCTAssertEqual(SidebarKeyboardNavigation.pageStep(visibleRows: 10), 9)
        XCTAssertEqual(SidebarKeyboardNavigation.pageStep(visibleRows: 2), 1)
        XCTAssertEqual(SidebarKeyboardNavigation.pageStep(visibleRows: 1), 1)
        XCTAssertEqual(SidebarKeyboardNavigation.pageStep(visibleRows: 0), 1, "退化输入也不能给出 0 或负数步长")
    }

    func testPagingNearTheEndStopsInsteadOfWrapping() {
        XCTAssertEqual(
            SidebarKeyboardNavigation.targetIndex(
                currentIndex: 0, count: 100, direction: .down,
                step: SidebarKeyboardNavigation.pageStep(visibleRows: 10)
            ), 9)
        XCTAssertNil(SidebarKeyboardNavigation.targetIndex(
            currentIndex: 95, count: 100, direction: .down,
            step: SidebarKeyboardNavigation.pageStep(visibleRows: 10)
        ), "最后一页不满时停在原地，而不是绕回顶部")
    }

    /// 接线守卫：视图必须真的把方向键接到这套策略上（纯函数正确但没人调用 = 没修）。
    func testSidebarWiresArrowKeysThroughThePolicy() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 HistorySidebarView.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)

        XCTAssertTrue(source.contains(".onMoveCommand(perform: moveSelection)"),
                      "列表没有接方向键：键盘导航等于没接上")
        XCTAssertTrue(source.contains(".focusable()"), "列表容器不可聚焦，方向键永远到不了它")
        // 上一条留着 `.focusable()`，这一条钉住"环被关掉"：两件事必须同时成立 ——
        // 只留 focusable 就是用户报的那圈蓝框，只关环而不 focusable 方向键就废了。
        XCTAssertTrue(source.contains(".sidebarFocusRingHidden()"),
                      "列表容器的系统焦点环没有被抑制：鼠标点一下，整块列表外面就会出现一圈蓝框")
        XCTAssertTrue(source.contains("self.focusEffectDisabled()"),
                      "抑制函数是个空壳（没有真的调用 focusEffectDisabled），上面那条守卫会被骗过")
        XCTAssertEqual(
            source.components(separatedBy: "SidebarKeyboardNavigation.targetIndex(").count - 1, 1,
            "落点计算应当恰好由策略给出一处"
        )
        XCTAssertTrue(source.contains("proxy.scrollTo(selectedID"),
                      "键盘移动选择后必须把选中行滚进视野")
        XCTAssertTrue(source.contains("selectionChangedByKeyboard"),
                      "自动滚动只该由键盘触发，否则会改动鼠标点击的既有行为")
    }
}
