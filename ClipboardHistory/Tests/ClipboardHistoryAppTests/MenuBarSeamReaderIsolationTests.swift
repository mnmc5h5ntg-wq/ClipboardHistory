import XCTest

/// R237（BACKLOG 268 / D-222）：**「读缝的格子有没有标 `@MainActor`」这把静态尺**。
///
/// 起因是 runner 给的一次本机绿、机器红的编译失败（run 39345462910 的 STEP[4]
/// `Build (must be warning-free)` 打的是 error，正文原文：
/// `MenuBarSwiftUIDismissRowInkTests.swift:80:57: error: main actor-isolated static property
/// 'dismissRowInk' can not be referenced from a nonisolated context`
/// 而本机同一支文件 `swift build --build-tests` 不报这一条、全量卷 913/44/0。
///
/// 两边都不是"谁写错了"，而是**工具链对 `View` 的隔离推断不一样**：在那套 SDK 上，
/// conform `View` 的类型其成员被整体推断成 main-actor 隔离 ⇒ 非隔离上下文读这颗缝是编译期 error。
/// 这条推断**本机复现不出来**，于是「编译器会替我记住」在本机等于没有 ——
/// 只印不拦的读数等于没有读数（D-221 那条附则的同一族）。所以这里补一把**与 SDK 无关的静态尺**：
/// 扫测试目录里「代码位（剥掉行注释与字符串字面量之后）」对缝的引用，
/// 要求它所在的那根 func（或它外面那层类型）带着 `@MainActor`。
///
/// 两格形状：
/// ① `testAnalyzerTruthTable` —— 正对照：合成夹具里「没标注 / 有标注 / 只在注释与字面量里」三种各判一次，
///   钉住这把尺既不空转也不被自己的引用喂饱（本文件与 `MenuBarSwiftUIDismissRowInkTests` 的
///   文档注释、路径字面量里都出现同一颗名字，R236 实测过这个坑）。夹具用假名 `Foo.Bar.`，
///   免得①里出现的真名被②算成一处引用。
/// ② `testEveryLiveSeamReaderCarriesMainActor` —— 真扫：名单为空=红（代码位引用数 `>= 1`），未标注数必须 0。
///   变异刀 M792 删掉那一行 `@MainActor` ⇒ 这一格必须自己红，而不是等 runner 编译失败才知道。
///
/// 这是**静态尺不是编译器**：它不解析语法树，只看「引用行往上第一根 func 的紧邻标注属性」，
/// 所以它能在本机拦住 runner 那套 SDK 会判 error 的写法，但代替不了 STEP[4] 本身。
///
/// 不覆盖管线：这把尺量的是「测试代码怎么引用那颗值」，不是产品画面/菜单内容/管线；
/// 行为轴与结构轴在 `MenuBarSwiftUIDismissRowInkTests`，帧侧基线在 `UICaptureTests`。
final class MenuBarSeamReaderIsolationTests: XCTestCase {

    /// 被引用的那颗缝（住在 `Sources/ClipboardHistoryApp/Views/`）。拆成两段拼接是为了让它
    /// **只**以字面量身份出现在本文件 —— 下面那把尺第一步就剥字面量，所以本文件不会被自己抓住。
    private var seamNeedle: String { "MenuBarRecommendations" + "View." }

    /// 剥掉行注释（含 `///` 文档注释）与字符串字面量的内容，只留代码位。
    private func codeOnly(_ line: String) -> String {
        var out: [Character] = []
        var inString = false
        for ch in line {
            if inString {
                if ch == "\"" { inString = false }
                continue
            }
            if ch == "\"" { inString = true; continue }
            if ch == "/" {
                if out.last == "/" { _ = out.removeLast(); return String(out) }
                out.append(ch); continue
            }
            out.append(ch)
        }
        return String(out)
    }

    private struct Hit { let file: String, line: Int, method: String, annotated: Bool }

    /// `idx` 上方**紧邻**的标注属性（跳过空行与整行注释），拼成一颗串供判 main-actor。
    private func annotationAbove(_ lines: [String], above idx: Int) -> String {
        var j = idx - 1
        var bag: [String] = []
        while j >= 0 {
            let e = codeOnly(lines[j]).trimmingCharacters(in: .whitespaces)
            if e.isEmpty { j -= 1; continue }
            if e.hasPrefix("@") { bag.append(e); j -= 1; continue }
            break
        }
        return bag.joined(separator: " ")
    }

    /// 找出 `source` 里所有「代码位引用了 `needle`」的格子，并判断它所在那根 func（或它外面那层
    /// 类型声明）是否带着 `@MainActor`。`file` 只用于报告。
    private func scan(source: String, file: String, needle: String) -> [Hit] {
        let lines = source.components(separatedBy: "\n")
        var hits: [Hit] = []
        for (idx, raw) in lines.enumerated() where codeOnly(raw).contains(needle) {
            var j = idx - 1
            var funcIdx = -1
            var typeIdx = -1
            var method = "<无外层 func>"
            while j >= 0 {
                let e = codeOnly(lines[j]).trimmingCharacters(in: .whitespaces)
                if e.hasPrefix("func ") {
                    funcIdx = j
                    method = e.components(separatedBy: "(").first?
                        .replacingOccurrences(of: "func ", with: "")
                        .trimmingCharacters(in: .whitespaces) ?? e
                    break
                }
                if e.hasPrefix("final class ") || e.hasPrefix("class ") || e.hasPrefix("struct ") {
                    typeIdx = j
                    break
                }
                j -= 1
            }
            var annotated = funcIdx >= 0
                && annotationAbove(lines, above: funcIdx).lowercased().contains("mainactor")
            if !annotated, typeIdx >= 0 {
                annotated = annotationAbove(lines, above: typeIdx)
                    .lowercased().contains("mainactor")
            }
            hits.append(Hit(file: file, line: idx + 1, method: method, annotated: annotated))
        }
        return hits
    }

    // MARK: ①正对照：三种形状各判一次（空转与被自己喂饱都当场红）

    func testAnalyzerTruthTable() throws {
        let n = "Foo.Bar."
        let unmarked = """
        final class C: XCTestCase {
            func testA() throws {
                let v = Foo.Bar.x
            }
        }
        """
        let marked = """
        final class C: XCTestCase {
            /// 文档注释提到 Foo.Bar.x，不该被算成一次引用
            @MainActor
            func testA() throws {
                let v = Foo.Bar.x
            }
        }
        """
        let prose = """
        /// 文档注释里提到 Foo.Bar.x
        // 行注释 Foo.Bar.x
        final class C: XCTestCase {
            func testA() throws {
                let p = "Sources/Foo.Bar.swift"
            }
        }
        """
        let ua = scan(source: unmarked, file: "unmarked", needle: n)
        XCTAssertEqual(ua.count, 1, "a) 没标注的引用尺看不见 ⇒ 这把尺空转，②会恒绿")
        XCTAssertEqual(ua.first?.method, "testA", "a) 外层 func 名没读到 ⇒ 往上那根尺走错了方向")
        XCTAssertEqual(ua.first?.annotated, false, "a) 没标注却被判已标注 ⇒ ②会恒绿")
        let ma = scan(source: marked, file: "marked", needle: n)
        XCTAssertEqual(ma.count, 1, "b) 带标注的那处也应被抓到（只是判为已标注）")
        XCTAssertEqual(ma.first?.annotated, true,
                       "b) 带 @MainActor（上面还压着一行文档注释）的那根 func 应判为已标注")
        let pr = scan(source: prose, file: "prose", needle: n)
        XCTAssertEqual(pr.count, 0, "c) 注释与字符串字面量不许喂饱这把尺（会造出永远抓不到的假红）")
    }

    // MARK: ②真扫：测试目录里每一处代码位引用都要有标注

    func testEveryLiveSeamReaderCarriesMainActor() throws {
        let testsDir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        let entries: [String]
        do {
            entries = try FileManager.default.contentsOfDirectory(atPath: testsDir.path)
        } catch {
            return XCTFail("测试目录读不到 \(testsDir.path) ⇒ \(error)：这把尺没有对象，不判（不是通过）")
        }
        let files = entries.filter { $0.hasSuffix(".swift") }.sorted()
        guard !files.isEmpty else {
            return XCTFail("\(testsDir.path) 里没有 .swift ⇒ 名单为空，不判（不是通过）")
        }
        var refs = 0
        var bad: [String] = []
        for f in files {
            guard let raw = try? String(contentsOf: testsDir.appendingPathComponent(f), encoding: .utf8) else {
                return XCTFail("读不到 \(f) ⇒ 证据指针指不到东西，这一格不许绿")
            }
            for h in scan(source: raw, file: f, needle: seamNeedle) {
                refs += 1
                if !h.annotated {
                    bad.append("\(f):\(h.line) 在 `\(h.method)` 里读缝，却没有 @MainActor")
                }
            }
        }
        // 结论行打在闸门之前：未标注=0 的时候也要能看到「到底有几处在读」。
        CaptureReadings.emit("SEAM_READER_ISOLATION 目录=\(testsDir.lastPathComponent) "
                            + "文件=\(files.count) 代码位引用=\(refs) 未标注=\(bad.count)"
                            + (bad.isEmpty ? "" : " 红名=[\(bad.joined(separator: " ;; "))]"))
        XCTAssertGreaterThanOrEqual(refs, 1,
                                    "整个测试目录一处代码位都不读缝 ⇒ 要么缝被搬走、要么尺被弄坏，"
                                    + "两种都不该由这一格绿着代替")
        XCTAssertEqual(bad, [],
                       "有格子在非隔离上下文里读这颗缝：本机工具链放过，"
                       + "runner 那套 SDK 判成编译期 error（run 39345462910 的 STEP[4] 就是这一句）")
    }
}
