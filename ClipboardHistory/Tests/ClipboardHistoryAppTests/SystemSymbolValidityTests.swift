import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-09 / 1.3：`DetailPreviewViews` 里写着 `Image(systemName: "questionable")`，
/// 而这不是一个合法的 SF Symbol 名字 —— SwiftUI/AppKit 不报错，只是画一个**空白图标**，
/// 于是"视频分辨率读不到"的错误态看起来像少了个图标。编译期与运行期都不会提醒，
/// 所以这里加一道扫描式守卫：把产品源码里所有符号名字面量拿去问 `NSImage`。
///
/// 识别器本身也要被证明有效（否则"一条都没抓到"和"全部合法"长得一模一样）：
/// 前两条用例用合成输入钉住识别器，包括那条历史上真实出错的 `"questionable"`；
/// 全仓扫描那条另有一个**由 grep 独立得出**的数量下限，防止正则失配导致的假绿。
final class SystemSymbolValidityTests: XCTestCase {
    /// 取出源码里所有"会被当成 SF Symbol 名字"的字符串字面量，覆盖三种写法：
    /// ① `Image(systemName: "star")` ② 三元里的两个字面量 `Image(systemName: 条件 ? "a" : "b")`
    /// ③ 透传到 `Image(systemName:)` 的具名参数，如 `ThumbnailSymbol(systemName: "doc")`、
    ///    `GlassCircleButton(symbol: "trash")`。
    /// 只认字面量：`Image(systemName: 变量)` 静态扫不到，属预期（那种情况由调用点自己负责）。
    static func symbolLiterals(in source: String) -> [String] {
        var found: [String] = []
        func add(_ name: String) {
            guard !name.isEmpty, !found.contains(name) else { return }
            found.append(name)
        }

        let whole = NSRange(source.startIndex..., in: source)
        let labelled = try? NSRegularExpression(pattern: #"(?:systemName|symbol):\s*"([^"]+)""#)
        labelled?.matches(in: source, range: whole).forEach { match in
            guard let range = Range(match.range(at: 1), in: source) else { return }
            add(String(source[range]))
        }

        let imageExpression = try? NSRegularExpression(pattern: #"Image\(\s*systemName:\s*([^)\n]*)\)"#)
        let anyLiteral = try? NSRegularExpression(pattern: #""([^"]+)""#)
        imageExpression?.matches(in: source, range: whole).forEach { match in
            guard let expressionRange = Range(match.range(at: 1), in: source) else { return }
            let expression = String(source[expressionRange])
            let expressionRangeNS = NSRange(expression.startIndex..., in: expression)
            anyLiteral?.matches(in: expression, range: expressionRangeNS).forEach { literalMatch in
                guard let range = Range(literalMatch.range(at: 1), in: expression) else { return }
                add(String(expression[range]))
            }
        }
        return found
    }

    static func isResolvable(_ symbolName: String) -> Bool {
        NSImage(systemSymbolName: symbolName, accessibilityDescription: nil) != nil
    }

    // MARK: - 识别器自证

    func testDetectorFindsEveryLiteralShapeIncludingTheInvalidOne() {
        let source = """
        Image(systemName: "star")
        Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
        ThumbnailSymbol(systemName: "doc")
        GlassCircleButton(symbol: "trash") { }
        let icon = Image(systemName: "questionable")
        Image(systemName: dynamicName)
        """
        // 用集合比：识别器先扫具名参数、再扫三元表达式，顺序不代表任何语义。
        // 条数单独断言，否则"重复计入"会被集合悄悄吃掉。
        let detected = Self.symbolLiterals(in: source)
        XCTAssertEqual(
            Set(detected),
            Set(["star", "chevron.down", "chevron.right", "doc", "trash", "questionable"]),
            "识别器漏了某种写法或多找了东西；扫不出东西的守卫等于没有守卫"
        )
        XCTAssertEqual(detected.count, 6, "同一个字面量被重复计入了：\(detected)")
    }

    func testDetectorCanTellAValidSymbolFromTheHistoricalBug() {
        XCTAssertFalse(Self.isResolvable("questionable"),
                       "阳性对照失败：`questionable` 必须是不可解析的，否则这道守卫抓不到任何东西")
        XCTAssertTrue(Self.isResolvable("questionmark.circle"),
                      "替换用的符号必须真的存在，否则只是把一个空白图标换成另一个")
        XCTAssertTrue(Self.isResolvable("star"))
        XCTAssertTrue(Self.isResolvable("exclamationmark.triangle"))
    }

    // MARK: - 全仓扫描

    func testEverySystemSymbolLiteralInProductSourcesResolves() throws {
        let sources = try Self.packageSourcesURL()
        var literals: [(file: String, line: Int, name: String)] = []
        let enumerator = FileManager.default.enumerator(at: sources, includingPropertiesForKeys: nil)
        while let file = enumerator?.nextObject() as? URL {
            guard file.pathExtension == "swift" else { continue }
            let text = try String(contentsOf: file, encoding: .utf8)
            for name in Self.symbolLiterals(in: text) {
                literals.append((file.lastPathComponent, Self.lineNumber(of: name, in: text), name))
            }
        }

        // 数量下限是**独立**数出来的，不是拿识别器自己的输出定的（那样等于自证）：
        //   grep -roE '(systemName|symbol):[[:space:]]*"' Sources | wc -l   → 16 个具名字面量站点
        //   另有 2 个 `Image(systemName: 条件 ? "a" : "b")` 站点不被上面那条 grep 计入 → ≥ 18
        XCTAssertGreaterThanOrEqual(
            literals.count, 18,
            "只扫到 \(literals.count) 个符号名字面量，低于独立计数的 18：正则或包根定位很可能坏了"
        )
        // 每次跑都把实际条数打出来：账本里引用的数字要能对上现场，而不是靠记忆。
        print("SYMBOL-LITERALS scanned=\(literals.count) unique=\(Set(literals.map(\.name)).count)")

        let violations = literals.filter { !Self.isResolvable($0.name) }
        XCTAssertTrue(
            violations.isEmpty,
            "以下 SF Symbol 名字不存在，界面上会画成空白图标：\n"
                + violations.map { "  \($0.file):\($0.line) → \"\($0.name)\"" }.joined(separator: "\n")
        )
    }

    // MARK: - 辅助

    private static func packageSourcesURL() throws -> URL {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let probe = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
            if FileManager.default.fileExists(atPath: probe.path) { return probe }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp（从 \(#filePath) 上溯 6 层未果）")
    }

    private static func lineNumber(of symbolName: String, in text: String) -> Int {
        guard let range = text.range(of: "\"\(symbolName)\"") else { return 0 }
        return text[..<range.lowerBound].filter { $0 == "\n" }.count + 1
    }
}
