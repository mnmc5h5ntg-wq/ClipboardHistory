import XCTest

/// 文档里点名的测试必须真的存在（第三轮审计 C-1 的配套守卫）。
///
/// 起因是本轮自己的一个错：`AGENTS.md` 的定义完成标准里写了守卫叫
/// `testHistoryStoreAverageFunctionLengthDoesNotGrow`，而那个"平均方法长度"的判据
/// 在变异对照里被证伪（往 Store 塞一个 33 行的方法，均值 20.02 → 20.25，守卫还是绿），
/// 于是我把它换成了 `testHistoryStoreStaysThin` —— **但文档没跟着改**。
/// 结果是：仓库的"硬规矩"指向一个不存在的守卫，读它的人会以为有一道闸在守着，
/// 而那道闸已经不存在了。这类事比缺一条注释严重得多。
///
/// 所以这不是"顺手加个测试"，是给"文档说有一道守卫"这句话本身加一道守卫。
final class DocumentationAnchorTests: XCTestCase {
    /// 找出仓库根目录。测试文件在 `ClipboardHistory/Tests/ClipboardHistoryAppTests/` 下，往上三层。
    private var repoRoot: URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // ClipboardHistoryAppTests
            .deletingLastPathComponent()   // Tests
            .deletingLastPathComponent()   // ClipboardHistory
            .deletingLastPathComponent()   // 仓库根
    }

    private func markdownDocuments() throws -> [(name: String, text: String)] {
        var documents: [(String, String)] = []
        let candidates = ["AGENTS.md", "docs/agents/issue-tracker.md", "docs/agents/domain.md",
                          "docs/agents/triage-labels.md"]
        for relative in candidates {
            let url = repoRoot.appendingPathComponent(relative)
            guard let text = try? String(contentsOf: url, encoding: .utf8) else { continue }
            documents.append((relative, text))
        }
        XCTAssertFalse(documents.isEmpty, "一份文档都没读到：这条守卫会静默变成空跑")
        return documents
    }

    private func testNamesDefinedInTests() throws -> Set<String> {
        let testsDirectory = repoRoot.appendingPathComponent("ClipboardHistory/Tests", isDirectory: true)
        guard let enumerator = FileManager.default.enumerator(at: testsDirectory,
                                                             includingPropertiesForKeys: nil) else {
            // 路径漂了必须红：这条守卫一旦静默返回空集合，"文档点名的守卫都存在"就永远成立。
            XCTFail("读不到测试目录：\(testsDirectory.path)")
            return []
        }
        var names: Set<String> = []
        var scanned = 0
        for case let url as URL in enumerator {
            guard url.pathExtension == "swift" else { continue }
            scanned += 1
            guard let text = try? String(contentsOf: url, encoding: .utf8) else { continue }
            for name in Self.functionNames(in: text) where name.hasPrefix("test") {
                names.insert(name)
            }
        }
        XCTAssertGreaterThan(scanned, 30, "只扫到 \(scanned) 个测试文件：路径大概漂了")
        return names
    }

    /// 从一个 Swift 文件里取出所有 `func X` 的名字。
    /// 手写单遍扫描而不是正则；也**不能**用 `String(characters[index...]).hasPrefix`：
    /// 那种写法每个位置都构造一次后缀字符串，扫全仓测试文件时这条测试跑了 91 秒
    /// （第一版就是这么写的 —— 慢到离谱本身就是一种错）。
    static func functionNames(in text: String) -> [String] {
        let characters = Array(text)
        let keyword: [Character] = ["f", "u", "n", "c", " "]
        var found: [String] = []
        var index = 0
        while index + keyword.count <= characters.count {
            var matches = true
            for offset in 0..<keyword.count where characters[index + offset] != keyword[offset] {
                matches = false
                break
            }
            guard matches else { index += 1; continue }
            var cursor = index + keyword.count
            while cursor < characters.count, characters[cursor] == " " { cursor += 1 }
            var name = ""
            while cursor < characters.count,
                  characters[cursor].isLetter || characters[cursor].isNumber || characters[cursor] == "_" {
                name.append(characters[cursor])
                cursor += 1
            }
            if !name.isEmpty { found.append(name) }
            index = max(cursor, index + 1)
        }
        return found
    }

    /// 文档里用反引号点名的 `testXxx` 守卫，必须能在测试源码里找到同名方法。
    func testEveryGuardNamedInDocsExists() throws {
        let defined = try testNamesDefinedInTests()
        XCTAssertFalse(defined.isEmpty, "一个测试名都没解析出来：解析逻辑坏了，不是文档坏了")
        var dangling: [String] = []
        for (document, text) in try markdownDocuments() {
            for run in backtickedTokens(in: text) where run.hasPrefix("test") {
                if !defined.contains(run) { dangling.append("\(document): \(run)") }
            }
        }
        XCTAssertEqual(dangling, [],
                       "文档点名的守卫不存在 —— 读文档的人会以为那里有一道闸")
    }

    /// 反引号里、以 `test` 开头的标识符。手写正则在这里不值得：规则就是"整段只含标识符字符"。
    private func backtickedTokens(in text: String) -> [String] {
        var tokens: [String] = []
        var rest = Substring(text)
        // 逐个扫描 ` ... `，跳过代码块围栏造成的空段
        while let open = rest.firstIndex(of: "`") {
            let afterOpen = rest.index(after: open)
            guard let close = rest[afterOpen...].firstIndex(of: "`") else { break }
            let token = String(rest[afterOpen..<close])
            if token.allSatisfy({ $0.isLetter || $0.isNumber || $0 == "_" }), token.hasPrefix("test") {
                tokens.append(token)
            }
            rest = rest[rest.index(after: close)...]
        }
        return tokens
    }

    /// 台账里两格「不归它」的判定，挂在**一个 API 的默认值**上 —— 现在它有自己的守卫（R135 / U-447）。
    ///
    /// 具体是哪两格：`docs/motion_surface_ledger.json` 里
    /// 「菜单栏/推荐面板 × 加载」与「菜单栏/状态菜单 × 悬停」都判成"SwiftUI 的过渡与 hover 修饰符
    /// 在那一层根本不执行"，理由是 `MenuBarExtra` 的样式是 `.menu`，内容会被编译成**真 NSMenu**。
    /// `App.swift` 的注释自己写着"默认值不是契约：哪天有人加一行 `.menuBarExtraStyle(.window)`，
    /// 这条结论要重判"。一句会过期的注释不等于守卫 —— 所以把它变成会红的断言：
    /// 那行字面量一旦被删掉或改成 `.window`，这两格就得重判，而不是继续拿着旧结论当免检。
    func testMenuBarExtraStyleStillSaysMenuWhileTheLedgerSaysNotApplicable() throws {
        let url = repoRoot.appendingPathComponent(
            "ClipboardHistory/Sources/ClipboardHistoryApp/App.swift")
        let text = try String(contentsOf: url, encoding: .utf8)
        // 只扫**代码行**：App.swift 那段注释里就写着"哪天有人加一行 `.menuBarExtraStyle(.window)`"，
        // 整文件 contains 会命中我自己引用的那句话 ⇒ 守卫第一次全量跑就假红（R135 / U-448，
        // 与"region() 命中守卫自己"、"扫前剥注释"同一族）。
        let codeOnly = text.split(separator: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        let windowStyling = codeOnly.contains(".menuBarExtraStyle(.window)")
        let menuStyling = codeOnly.contains(".menuBarExtraStyle(.menu)")
        print("MENUBAR_STYLE 显式=.menu:\(menuStyling ? 1 : 0) 显式=.window:\(windowStyling ? 1 : 0)")
        XCTAssertFalse(windowStyling,
            "App.swift 里出现了 `.menuBarExtraStyle(.window)` ⇒ 推荐面板不再是真 NSMenu，"
                + "台账里那两格『不归它 / 不执行』要重判（清账表与 BACKLOG 173 那一族都依赖它）")
        XCTAssert(menuStyling,
            "App.swift 里连 `.menuBarExtraStyle(.menu)` 这行都没了 ⇒ 样式回到默认值本身，"
                + "而默认值不是契约：那两格的理由现在没有任何东西在守（R135 / U-447）")
    }
}

