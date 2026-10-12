import XCTest
import SwiftUI
@testable import ClipboardHistoryApp

/// R6：**驱动那一侧**的判据（R5 那条 A6 的镜像）。
///
/// 第五轮修的是"声明了过渡却没有供电"（挂在 `Spacer()` 上、挂在没有 `.animation` 的 `body` 上）。
/// 这一轮钉相反的那一半：**挂了 `.animation(value:)`，而那个键永远不变**。
/// 两者是同一族缺陷的两个方向，而第二个更阴 —— 它连"这里写了过渡"这句话都不留给你，
/// 读代码的人只看到"动画已接"，屏幕上却一帧都不演。
///
/// 本文件不覆盖管线：这些是**源码级**判据（扫产品源码里的形状）。
/// 管线级判据是同文件里那两条走 `HistoryStore` 的（`testClearHistoryReceiptCountsTheRealRemoval`）
/// 与动效胶片套件（`MotionFilmstripTests`，按像素判"到底演没演"）。
@MainActor
final class MotionDriverTests: XCTestCase {

    // MARK: - 恒假的动画键

    /// `Views/` 一族里不许有 `.animation(_:value:)` 的键是**字面量**。
    /// 字面量键 = 这条动画永远不会被触发 = 一行不会执行的声明（与 A6 同族）。
    func testNoConstantAnimationKeysAcrossViews() throws {
        var offenders: [String] = []
        for entry in try productViewSources() {
            let code = Self.stripCommentLines(entry.source)
            for key in Self.animationKeys(in: code) where Self.isConstantKey(key) {
                offenders.append("\(entry.file)：.animation 的键是常量「\(key)」⇒ 这条动画永远不会被触发")
            }
        }
        XCTAssertTrue(offenders.isEmpty, offenders.joined(separator: "\n"))
    }

    /// 上面那条扫描器的真值表：抓得住恒假键，也不把合法写法误报。
    /// 不门控、不开窗口 ⇒ CI 每轮都跑（R5 那一课的延续：**能被打红的东西才叫判据**）。
    func testAnimationKeyScanIsATruthTable() {
        // ① 字面量键 ⇒ 必须抓到（三种写法各来一次）。
        XCTAssertEqual(Self.animationKeys(in: "view.animation(.easeInOut, value: true)"), ["true"])
        XCTAssertEqual(Self.animationKeys(in: "view.animation(.spring(), value: 0)"), ["0"])
        XCTAssertEqual(Self.animationKeys(in: "view.animation(a, value: \"x\")"), ["\"x\""])
        XCTAssertTrue(Self.isConstantKey("true"))
        XCTAssertTrue(Self.isConstantKey(" 0.2 "), "数字字面量算常量")
        XCTAssertTrue(Self.isConstantKey(""), "没有键 ⇒ 也算恒假")

        // ② 合法写法不许误报：比较表达式、状态属性、可选布尔。
        XCTAssertEqual(Self.animationKeys(in: "v.animation(a, value: store.filteredEntries.isEmpty)"),
                       ["store.filteredEntries.isEmpty"])
        XCTAssertFalse(Self.isConstantKey("clearReceipt == nil"))
        XCTAssertFalse(Self.isConstantKey("previewStage"))
        XCTAssertFalse(Self.isConstantKey("historyStore.selectedEntry == nil"))

        // ③ 跨行写法必须能找到（本仓库的写法就是换行的，找不到等于判据空转）。
        let multiline = """
        someView
            .animation(MotionCatalog.animation(for: .contentFade),
                       value: isDropTargeted)
        """
        XCTAssertEqual(Self.animationKeys(in: multiline), ["isDropTargeted"])

        // ④ 嵌套括号不许把调用截断：`animation(MotionCatalog.animation(for: .x))` 里还有一层括号。
        let nested = "v.animation(MotionCatalog.animation(for: .hover, reduceMotion: false), value: isHovered)"
        XCTAssertEqual(Self.animationKeys(in: nested), ["isHovered"])

        // ⑤ 没有 `value:` 的 `.animation` 不产出键（那是另一族：隐式动画，本条不判）。
        XCTAssertTrue(Self.animationKeys(in: "v.animation(.default)").isEmpty)
    }

    // MARK: - 清空历史那条回执（管线级）

    /// 回执里的数字必须等于**真的被删掉的那些**。
    ///
    /// 从产品入口进（AGENTS.md 定义 of done 第 1 条）：建一个真 `HistoryStore`，
    /// 用真 `add` / `perform(.toggleFavorite)` 摆出"2 条收藏 + 3 条未收藏"，
    /// 按**控制器用的同一条表达式**取回执，再 `perform(.clear)`，
    /// 然后拿回执里的数字与 Store 的真实剩余去对。
    /// 这条同时钉住两件事：数字对不对，以及"先数再清"那个顺序（顺序错了回执会说 0 条）。
    func testClearHistoryReceiptCountsTheRealRemoval() throws {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        for text in ["a", "b", "c", "d", "e"] { store.add(intakeEntry(text: text)) }
        XCTAssertEqual(store.entries.count, 5)
        for entry in store.entries.prefix(2) { store.perform(.toggleFavorite(entry)) }

        // 与 `SettingsWindowController` 里那一行**同一个表达式**：先数，再清。
        let receipt = ClearHistoryReceiptPolicy.receipt(isFavorites: store.entries.map(\.isFavorite))
        store.perform(.clear)

        XCTAssertTrue(receipt.contains("已清空 3 条"), "回执：\(receipt)")
        XCTAssertTrue(receipt.contains("2 条收藏保留"), "回执：\(receipt)")
        XCTAssertEqual(store.entries.count, 2, "回执说清了 3 条，Store 里却还剩 \(store.entries.count) 条")
        XCTAssertTrue(store.entries.allSatisfy(\.isFavorite), "「清空未收藏」不许动收藏")
    }

    /// 一条不可撤销的删除之后，"什么都没发生"是最坏的回执。
    func testClearHistoryReceiptNeverSilentEvenWithNothingToRemove() {
        XCTAssertEqual(ClearHistoryReceiptPolicy.receipt(isFavorites: []),
                       "没有可清空的记录（0 条收藏保留）。")
        XCTAssertEqual(ClearHistoryReceiptPolicy.receipt(isFavorites: [true, true]),
                       "没有可清空的记录（2 条收藏保留）。")
        XCTAssertEqual(ClearHistoryReceiptPolicy.tally(isFavorites: [false, false, true]).removed, 2)
    }

    /// "先数再清"这个顺序是这条回执的全部价值，所以它必须**会红**。
    /// 上一轮教训（R3/R4：值断言证明不了来源）：这里不比对文案，比对**两行代码的先后**。
    func testReceiptIsComputedBeforeTheStoreIsCleared() throws {
        let controller = try productSource(named: "Managers/SettingsWindowController.swift")
        let receiptAt = try XCTUnwrap(controller.range(of: "ClearHistoryReceiptPolicy.receipt"),
                                      "清空回执不再走 ClearHistoryReceiptPolicy：文案有两个作者了")
        let clearAt = try XCTUnwrap(controller.range(of: "store.perform(.clear)"),
                                    "找不到 perform(.clear)：锚点失效")
        XCTAssertLessThan(controller.distance(from: controller.startIndex, to: receiptAt.lowerBound),
                          controller.distance(from: controller.startIndex, to: clearAt.lowerBound),
                          "回执改成在 perform(.clear) **之后**数 ⇒ 永远报 0 条")
    }

    /// 回执必须**渲染在按钮旁边**并且淡入（R6 / 审计 B-P1-2 的那半条）。
    func testClearReceiptIsRenderedAndFaded() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("clearReceipt = clearHistoryAction?()"),
                      "清空按钮的结果没有落到界面上（回执被丢掉了）")
        XCTAssertTrue(settings.contains("value: clearReceipt == nil"),
                      "回执没有淡入驱动：它突然出现，用户不知道是哪一下带来的")
        XCTAssertTrue(settings.contains("clearHistoryAction: (() -> String?)?"),
                      "clearHistoryAction 又变回 () -> Void：那条链路只能「做」，不能说结果")
        XCTAssertTrue(settings.contains("VoiceOverReceipt.announce(clearReceipt)"),
                      "清空回执只剩视觉表达：看不见屏幕的人按完一次不可撤销的删除之后，什么都收不到")
    }

    // MARK: - 详情预览三态（R6 / 审计 B-P1-1）

    /// 加载 / 成功 / 失败三态都要有过渡声明，并且有**一个**按阶段的驱动。
    func testPreviewStagesAreFed() throws {
        let preview = codeOnly(try productSource(named: "Views/DetailPreviewViews.swift"))
        let body = try XCTUnwrap(preview.components(separatedBy: "private var previewStage").first,
                                 "找不到 previewStage：那条按值动画的键没了")
        XCTAssertEqual(body.components(separatedBy: "\n")
            .filter { $0.contains(".transition(MotionCatalog.transition(for:") }.count, 3,
                       "三态里有人没有过渡声明 ⇒ 那一态是硬换")
        XCTAssertTrue(preview.contains("value: previewStage"),
                      "三态切换没有驱动（或者驱动换成了别的键）")
        // 键必须是**阶段**而不是整值：`FilePreview` 不是 Equatable，也不该整值比较。
        let stage = try XCTUnwrap(preview.components(separatedBy: "private var previewStage").dropFirst().first)
            .components(separatedBy: "}").first ?? ""
        XCTAssertEqual(Set(["0", "1", "2"]).subtracting(Self.returnedInts(stage)), [],
                       "previewStage 少了一档：\(stage)")
    }

    // MARK: - 展开箭头（R6 / 审计 B-P2）

    /// 箭头不许换符号名字，必须转 —— 而且挂在**同一条**揭示曲线上。
    func testChevronRotatesInsteadOfSwappingSymbolNames() throws {
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertFalse(detail.contains("\"chevron.down\""),
                       "箭头又回到换名字：那是一帧硬换，而旁边的内容正在用 0.22s 展开，两者对不上")
        XCTAssertTrue(detail.contains("rotationEffect(.degrees(isExpanded ? 90 : 0))"),
                      "箭头没有旋转表达")
        XCTAssertTrue(detail.contains(".animation(MultiFilePreviewLayout.animation, value: isExpanded)"),
                      "箭头的动画不是揭示那一条 ⇒ 又会各走各的")
    }

    // MARK: - 扫描器

    /// `.animation(...)` 调用里 `value:` 后面的表达式（含跨行、含嵌套括号）。
    static func animationKeys(in source: String) -> [String] {
        var keys: [String] = []
        let needle = ".animation("
        var search = source.startIndex
        while let open = source.range(of: needle, range: search..<source.endIndex) {
            var index = open.upperBound
            var depth = 1
            var body = ""
            while index < source.endIndex {
                let character = source[index]
                if character == "(" { depth += 1 }
                else if character == ")" {
                    depth -= 1
                    if depth == 0 { break }
                }
                body.append(character)
                index = source.index(after: index)
            }
            search = source.index(after: index)
            if let range = body.range(of: "value:") {
                keys.append(String(body[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines))
            }
        }
        return keys
    }

    /// 这个键是不是**永远不变**的东西（字面量 / 空）。
    static func isConstantKey(_ expression: String) -> Bool {
        let key = expression.trimmingCharacters(in: .whitespacesAndNewlines)
        if key.isEmpty { return true }
        if key == "true" || key == "false" { return true }
        if Double(key) != nil { return true }
        if key.hasPrefix("\"") { return true }
        return false
    }

    /// 从一段源码里抠出 `return <整数>` 的那几个整数（用来数 previewStage 的档位）。
    static func returnedInts(_ source: String) -> Set<String> {
        var found: Set<String> = []
        for line in source.components(separatedBy: "\n") {
            guard let range = line.range(of: "return ") else { continue }
            let tail = line[range.upperBound...].trimmingCharacters(in: .whitespaces)
            if tail.allSatisfy({ $0.isNumber }), !tail.isEmpty { found.insert(tail) }
        }
        return found
    }

    static func stripCommentLines(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func codeOnly(_ source: String) -> String { Self.stripCommentLines(source) }

    /// `Sources/ClipboardHistoryApp/Views/*.swift`。
    /// 这里自己写一份而不是复用别的测试文件里的同名扫描器：那几个都是 `private`，
    /// 而**按族判据的取目录逻辑必须能被本文件独立证伪**（复用别人的私有工具，
    /// 它就跟着那个文件一起被改坏而本文件不知道）。取不到目录 ⇒ 抛错，不静默返回空集。
    private func productViewSources() throws -> [(file: String, source: String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/Views", isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            let swift = names.filter { $0.hasSuffix(".swift") }
            XCTAssertFalse(swift.isEmpty, "Views 目录是空的：这条按族扫描没有守卫对象")
            return swift.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "MotionDriverTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Views 目录"])
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory + "/" + name)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "MotionDriverTests", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 \(relative)：守卫找不到被守卫的东西时必须红"])
    }

    private func intakeEntry(text: String) -> ClipboardIntake.Entry {
        // 固定来源 App：否则排序随测试期间谁在焦点上而随机失败（同 HistoryStoreTests 的注释）。
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
    }
}
