import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class EntryPresentationTests: XCTestCase {
    func testTextPreviewReplacesNewlinesAndTruncatesLongText() {
        let text = String(repeating: "a", count: 30) + "\n" + String(repeating: "b", count: 40)

        let preview = EntryPresentation.preview(for: .text(text))

        XCTAssertTrue(preview.contains(" ↵ "))
        XCTAssertEqual(preview.count, 61)
        XCTAssertTrue(preview.hasSuffix("…"))
    }

    func testSizeDescriptionForText() {
        XCTAssertEqual(
            EntryPresentation.sizeDescription(for: .text("hello")),
            "5 个字符"
        )
    }

    func testSizeDescriptionForFilesHidesFullPath() {
        let url = URL(fileURLWithPath: "/Users/me/private/report.pdf")

        let description = EntryPresentation.sizeDescription(for: .file(url))

        XCTAssertEqual(description, "文件: report.pdf")
        XCTAssertFalse(description.contains("/Users/me/private"))
    }

    func testFileNamePartsSplitsExtensionAndUsesFallbackForHiddenFile() {
        let fileURL = URL(fileURLWithPath: "/tmp/report.final.pdf")
        let hiddenURL = URL(fileURLWithPath: "/tmp/.gitignore")

        let fileParts = EntryPresentation.fileNameParts(for: fileURL)
        let hiddenParts = EntryPresentation.fileNameParts(for: hiddenURL)

        XCTAssertEqual(fileParts.baseName, "report.final")
        XCTAssertEqual(fileParts.fileExtension, "pdf")
        XCTAssertEqual(fileParts.displayBaseName, "report.final")
        XCTAssertEqual(hiddenParts.displayBaseName, ".gitignore")
    }

    func testMenuTitleTruncatesTextAndUsesFileName() {
        let textEntry = makeClipboardEntry(
            content: .text("line one\n" + String(repeating: "a", count: 80))
        )
        let fileEntry = makeClipboardEntry(
            content: .file(URL(fileURLWithPath: "/tmp/report.pdf"))
        )

        XCTAssertEqual(EntryPresentation.menuTitle(for: textEntry, maxLength: 12), "line one aa…")
        XCTAssertEqual(EntryPresentation.menuTitle(for: fileEntry), "report.pdf")
    }

    // MARK: - 有界字符计数（审计第二轮 B-3 / R2-11）

    func testCharacterCountStopsAtTheLimit() {
        XCTAssertEqual(EntryPresentation.characterCount(of: "abc", limit: 3), 3, "刚好到上限仍给准确值")
        XCTAssertNil(EntryPresentation.characterCount(of: "abcd", limit: 3), "超过上限返回 nil，由文案说“超过”")
        XCTAssertEqual(EntryPresentation.characterCount(of: "", limit: 3), 0)
        XCTAssertNil(EntryPresentation.characterCount(of: "aaaaa", limit: 0), "上限为 0 时任何非空串都算超限")
    }

    func testSizeDescriptionStillCountsGraphemesNotScalars() {
        // 换实现不许换语义：显示给用户的一直是"字素数"，
        // 所以 ZWJ 家庭 emoji 是 1 个字符，不是 5 个 scalar。
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text("👨‍👩‍👧")), "1 个字符")
        XCTAssertEqual(EntryPresentation.characterCount(of: "é"), 1)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text("hello")), "5 个字符")
    }

    func testSizeDescriptionFallsBackToTheBoundForHugeText() {
        let limit = EntryPresentation.sizeCountLimit
        let huge = String(repeating: "a", count: limit + 1)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text(huge)), "超过 \(limit) 个字符")

        let exactlyAtLimit = String(repeating: "a", count: limit)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text(exactlyAtLimit)), "\(limit) 个字符",
                       "边界值必须给准确数字，不能提前退化")
    }

    // MARK: - R65 / BACKLOG 94：产品自己写的那句文案里不许放 emoji 图标

    /// 真值表：三种"产品决定怎么说"的内容，各给一句**只有字**的预览。
    ///
    /// 为什么钉"没有 emoji"而不是只钉那三串文案：这条规则的形状是
    /// **"图标不靠文案里的一个彩色字符来表达"**。只断言 `== "report.pdf"` 的话，
    /// 下一次有人加一个 ✅ 表示"这条已经复制过"，这条判据仍然是绿的。
    ///
    /// `.text` **故意不在这一格里**：那一支返回的是用户自己的正文，里面本来就可以有 emoji ——
    /// 把"没有 emoji"推广到它，判的就是用户剪贴板的内容，那是一条会逼人把正文改掉的坏判据
    /// （同一个词在两个判据里含义不同，见账本里"口径"那一族）。
    func testProductWrittenPreviewsCarryNoEmojiGlyphs() throws {
        let cases: [(ClipboardEntryContent, String)] = [
            (.file(URL(fileURLWithPath: "/Users/me/private/report.pdf")), "report.pdf"),
            (.files([URL(fileURLWithPath: "/tmp/a.pdf"), URL(fileURLWithPath: "/tmp/b.pdf"),
                     URL(fileURLWithPath: "/tmp/c.pdf")]), "a.pdf 等 3 个文件"),
            (.files([]), "多个文件"),
            (.image(try makeStoredImage(size: NSSize(width: 240, height: 140))), "图片 240×140"),
        ]
        for (content, expected) in cases {
            let preview = EntryPresentation.preview(for: content)
            // 先判"有没有 emoji"，再判逐字文案：前者是这条判据的**不变量**，
            // 后者只是它今天的取值。顺序反过来的话，把 📄 塞回去的那一刀会红在"文案不等于"上，
            // 于是电池证明的是"文案钉住了"，而不是"emoji 那把尺有牙"。
            XCTAssertFalse(Self.containsEmojiPresentation(preview),
                           "预览里出现了 emoji 图形（\(preview)）⇒ 图标又搬回文案里了：它会参与搜索匹配"
                           + "（打一个图形符号就能筛出整类）、白吃截断预算，还和行首那列 SF Symbol 是两套语言")
            XCTAssertEqual(preview, expected, "这句文案就是浮层那一行的正文，必须逐字对得上")
        }
    }

    /// 正对照：上面那条"没有 emoji"必须真的抓得住 📄，否则它只是在证明今天恰好没有。
    func testTheEmojiRulerActuallyCatchesAPageGlyph() {
        XCTAssertTrue(Self.containsEmojiPresentation("📄 report.pdf"),
                      "尺坏了：连 📄 都判不出是 emoji ⇒ 上面那条『没有 emoji』是空判据")
        XCTAssertFalse(Self.containsEmojiPresentation("图片 240×140 · 10月9日 16:51"))
        // 这三个是最容易被误伤的：`isEmoji` 会把它们也算成 emoji，于是这条判据会因为误伤被人关掉。
        XCTAssertFalse(Self.containsEmojiPresentation("©"), "版权号不是 emoji")
        XCTAssertFalse(Self.containsEmojiPresentation("é"), "带变音符的字母不是 emoji")
        XCTAssertFalse(Self.containsEmojiPresentation("a ↵ b"), "我们自己插的换行记号不是 emoji")
    }

    /// 用 `isEmojiPresentation` 而不是 `isEmoji`：后者把 ©、™、é 都算进来（实测，见上面那一格）。
    private static func containsEmojiPresentation(_ text: String) -> Bool {
        text.unicodeScalars.contains { $0.properties.isEmojiPresentation }
    }

    /// 浮层行首那一列：四种内容必须给**四个不同**的名字，而且每个名字都得真画得出东西。
    ///
    /// 第二条不是形式主义：`NSImage(systemSymbolName:)` 对写错的名字**返回 nil**，
    /// 而 `NSImageView` 拿着 nil 什么都不画、也不报错 —— 于是"符号名打错一个字母"
    /// 在屏幕上的表现是"那一格空了"，在测试上的表现是"全绿"。
    @MainActor
    func testQuickPickRowSymbolsAreDistinctAndActuallyDraw() throws {
        let kinds: [ClipboardEntryContent] = [
            .text("x"), .image(try makeStoredImage()),
            .file(URL(fileURLWithPath: "/tmp/a.pdf")),
            .files([URL(fileURLWithPath: "/tmp/a.pdf")]),
        ]
        let names = kinds.map { QuickPickController.rowSymbolName(for: $0) }
        XCTAssertEqual(Set(names).count, kinds.count,
                       "四种内容共用一个符号名 ⇒ 那一列不携带任何信息，画了等于没画：\(names)")
        for (content, name) in zip(kinds, names) {
            let image = QuickPickController.rowSymbol(for: content)
            XCTAssertNotNil(image, "`\(name)` 画不出图 ⇒ 这个名字在这个系统上不存在（或拼错了）")
            XCTAssertGreaterThan(image?.size.width ?? 0, 0, "`\(name)` 画出了一张零宽的图")
        }
        // 正对照：这条判据必须能抓到"名字不存在"这一类。
        XCTAssertNil(NSImage(systemSymbolName: "doc.textt", accessibilityDescription: nil),
                     "正对照失效：一个不存在的符号名也返回了图 ⇒ 上面那条 XCTAssertNotNil 没有判别力")
    }

    /// 两个列表必须说同一套图标语言（R65 / BACKLOG 94）。
    ///
    /// 判的是**源码里真的出现了那几个名字**，而不是"我记得侧栏用的是 doc"：
    /// 侧栏那一列由 SwiftUI 画，浮层那一列由 AppKit 画，两条路没有任何共享常量，
    /// 所以"一致"这件事只能由一条会红的守卫钉住（同 R15 的"令牌必须进梯子"）。
    @MainActor
    func testOverlaySymbolsAreTheSameNamesTheSidebarUses() throws {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift")
        let sidebar = try String(contentsOf: url, encoding: .utf8)
        for name in ["doc.text", "doc", "doc.on.doc"] {
            XCTAssertTrue(sidebar.contains("\"" + name + "\""),
                          "侧栏不再用 `\(name)` 了，而浮层还在用 ⇒ 两边又变成两套语言（BACKLOG 94）")
            XCTAssertTrue(QuickPickController.rowSymbolNameForTest.contains(name),
                          "浮层这一列丢了 `\(name)`")
        }
    }

}

private extension QuickPickController {
    /// 给上面那条守卫用的"浮层用到的全部符号名"清单（四种内容各一个）。
    @MainActor static var rowSymbolNameForTest: [String] {
        [ClipboardEntryContent.text("x"), .image(try! makeStoredImage()),
         .file(URL(fileURLWithPath: "/tmp/a.pdf")), .files([URL(fileURLWithPath: "/tmp/a.pdf")])]
            .map { rowSymbolName(for: $0) }
    }
}

