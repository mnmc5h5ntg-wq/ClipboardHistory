import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 §4 U-5（状态语言统一）的判据，外加 U-4 那条夹具帧的前提校验。
///
/// "统一"是个很容易被说成完成、其实只是"我觉得像"的东西，所以这里能钉住的都钉住：
/// 规范本身的映射关系、三处是不是真的走了同一个组件、以及横幅里不再自己设字号。
/// 剩下真正只能看的（颜色在同一块面板里是否协调）交给帧，见 `AGENT_UI_AUDIT.md` 的 U-15。
@MainActor
final class Round3StateLanguageTests: XCTestCase {

    // MARK: - 规范本身

    func testSpecPinsOneFontSizeAndASubordinateIcon() {
        XCTAssertEqual(StatePresentation.messageFontSize, 13,
                       "状态文案字号漂了：三处对齐的前提是这一份常数")
        XCTAssertLessThan(StatePresentation.symbolFontSize, StatePresentation.messageFontSize,
                          "图标不该比那句人话更抢眼")
    }

    func testAlignmentRuleIsSurfaceDependentNotKindDependent() {
        // 内联（横幅、菜单行）左对齐；整块面板的空态居中。
        // 这条存在的理由：审计原文写"统一左对齐"，但一刀切会把 macOS 既有的
        // 居中空态改成看起来像坏了 —— 规则要说清"按表面分"，而不是按状态分。
        XCTAssertEqual(StatePresentation.alignment(for: .inline), .leading)
        XCTAssertEqual(StatePresentation.alignment(for: .pane), .center)
    }

    func testLoadingStateCannotHaveAnAction() {
        // "正在整理推荐…" 旁边放一个按钮会让用户以为可以取消，而那会儿按下去什么都没有。
        XCTAssertNil(StatePresentation.actionTitle(for: .loading, provided: "取消"))
        XCTAssertEqual(StatePresentation.actionTitle(for: .warning, provided: nil), "知道了")
        XCTAssertEqual(StatePresentation.actionTitle(for: .error, provided: "打开历史文件夹"), "打开历史文件夹",
                       "错误态的下一步常常不是「知道了」，规范不许把它写死")
        XCTAssertEqual(StatePresentation.actionTitle(for: .empty, provided: "清除搜索"), "清除搜索")
        XCTAssertNil(StatePresentation.actionTitle(for: .empty, provided: nil),
                     "没有下一步时空态不许留一个空按钮位")
    }

    /// 严重度决定那句人话该不该被读到（R24 / U-46 / D-083）。
    ///
    /// 真值表只有四行，但它钉的是"以前四个状态共用一档墨"这件事。
    /// 这一条**不覆盖管线**（判的是纯函数映射）；管线级判据在 `UICaptureTests` 的
    /// `testNoticeBodyTextStaysReadable` —— 它量的是渲染出来的像素，也就是"档位真的换成了墨"。
    /// 两层都要：R21 记过"数值断言证明不了来源"，而只测映射又会重演第二轮 N-1
    /// （守卫绕过 adapter，几百条断言全绿、产品照崩）。
    func testSeverityStatesCarryTheirOwnTextInk() {
        XCTAssertEqual(StatePresentation.messageInk(for: .warning), .prominent,
                       "警告正文不许退回 `.subdued`：亮色实测 3.85:1，不达 AA")
        XCTAssertEqual(StatePresentation.messageInk(for: .error), .prominent,
                       "错误正文是「你的数据出问题了」，它必须是这块面板里最先被读到的东西")
        XCTAssertEqual(StatePresentation.messageInk(for: .loading), .subdued,
                       "「正在整理推荐…」升档就是喧宾夺主 —— 菜单栏那行不是让人读的句子，是背景状态")
        XCTAssertEqual(StatePresentation.messageInk(for: .empty), .subdued,
                       "空态跟着升档会把「没有东西」喊得比内容还响")
    }

    /// 映射之外还要钉"接线"：`StateLine` 里那句 `Text` 必须走档位，不许再自己挑颜色。
    func testStateLineWiresTheInkTierInsteadOfPickingAColor() throws {
        let source = codeOnly(try productSource(named: "Utilities/StatePresentation.swift"))
        XCTAssertTrue(source.contains("foregroundStyle(StatePresentation.messageInkStyle(for: kind))"),
                      "StateLine 的正文没有走 `messageInkStyle` ⇒ 真值表成了摆设")
        XCTAssertFalse(source.contains(".foregroundStyle(.secondary)"),
                       "StateLine 里又出现了硬写的 `.secondary` ⇒ 四个状态重新共用一档墨")
    }

    func testEachStateHasItsOwnSymbol() {        let symbols = [StatePresentation.symbolName(for: .loading),
                       StatePresentation.symbolName(for: .warning),
                       StatePresentation.symbolName(for: .error)]
        XCTAssertEqual(Set(symbols).count, 3, "两个状态共用一个图标，就等于没区分它们")
        XCTAssertTrue(symbols.allSatisfy { $0.hasPrefix("exclamationmark") || $0.hasPrefix("arrow") })
    }

    // MARK: - 三处真的用同一个组件（判使用处）

    func testBannerAndMenuBarBothGoThroughStateLine() throws {
        let banner = codeOnly(try productSource(named: "Views/NoticeBanner.swift"))
        XCTAssertTrue(banner.contains("StateLine(kind:"), "横幅没走 StateLine，字号还会漂回去")
        // 横幅自己**不许**再设字号：`.callout` 跟系统文字大小走，而状态行是硬字号，
        // 两者混用就是审计点名的"三态分散"。
        XCTAssertFalse(banner.contains(".font("), "横幅自己设了字号，规范就管不住它")
        XCTAssertFalse(banner.contains("Color.red.opacity"), "底色没从规范取")
        XCTAssertFalse(banner.contains("exclamationmark.triangle"), "图标没从规范取")

        let menu = codeOnly(try productSource(named: "Views/MenuBarRecommendationsView.swift"))
        XCTAssertTrue(menu.contains("StateLine(kind:"), "菜单栏状态行没走 StateLine")
        let afterStateLine = try XCTUnwrap(menu.components(separatedBy: "StateLine(kind:").dropFirst().first)
        XCTAssertTrue(afterStateLine.prefix(400).contains("正在整理推荐"),
                      "StateLine 不是那句状态文案的载体（判据就空了）")

        let empty = codeOnly(try productSource(named: "Views/EmptyStateView.swift"))
        XCTAssertTrue(empty.contains("StatePresentation.messageFontSize"), "空态字号没取规范")
        XCTAssertTrue(empty.contains("StatePresentation.iconStyle"), "空态图标颜色没取规范")
        XCTAssertTrue(empty.contains("actionTitle"), "空态没有下一步动作的入口")
    }

    func testNoResultsEmptyStateOffersToClearTheSearch() throws {
        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("清除搜索"), "搜不出东西时没有下一步")
        // 「清除搜索」必须走产品动作，而不是在视图里自己拨状态
        XCTAssertTrue(sidebar.contains("perform(.updateSearch("),
                      "清除搜索没经过 HistoryStore 的 .updateSearch 动作")
        XCTAssertTrue(sidebar.contains("historyStore.searchText.isEmpty ? nil"),
                      "动作位没按当前搜索词条件化：没有搜索词时也会画一个「清除搜索」")
    }

    // MARK: - U-4 夹具前提（帧不许量一个不存在的东西）

    func testHighlightFrameFixtureActuallyHasAHit() {
        let store = UICaptureTests().makePopulatedStore(selectingIndex: nil)
        guard let hit = store.entries.first(where: { $0.shortPreview.contains("视觉验收") }) else {
            return XCTFail("detail-text-highlight 帧的前提没了：夹具正文里找不到「视觉验收」")
        }
        store.perform(.selectOnly(hit))
        store.perform(.updateSearch("视觉"))
        XCTAssertEqual(store.selectedEntry?.id, hit.id,
                       "设了搜索词之后选中条目换了人 —— 那帧量的不是命中")
        guard case .text(let body) = hit.content else {
            return XCTFail("选中的不是文本条目")
        }
        let spans = MatchHighlighting.spans(in: body, query: "视觉")
        XCTAssertEqual(spans.count, 1,
                       "命中数不是 1：高亮帧量的到底是哪个位置就说不清了")
        XCTAssertLessThanOrEqual(NSMaxRange(NSRange(location: spans[0].location, length: spans[0].length)),
                                 body.utf16.count, "命中区间越界：临时属性会被 layoutManager 拒掉")
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
        // 找不到被守卫的文件时必须**红**，不能跳过：一个会跳过的守卫和一个通过的守卫
        // 在报表里长得一样，而文件改名之后它只会永远跳过。
        throw NSError(domain: "Round3StateLanguageTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
