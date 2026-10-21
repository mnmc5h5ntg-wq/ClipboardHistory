// 不覆盖管线：这一卷是**源码形状**的守卫（它问的是"画法与动画问的是不是同一句话"），
// 它不替代管线级判据。管线级的那一侧仍然在 `ControlHoverLadderTests`（两态墨从帧里读）、
// `MotionFilmstripTests`（过渡到底演没演，按场景表判）与 `UICaptureHarness` 的两态夹具里。
//
// R275 / BACKLOG 291 与 D-249 那一族的复发：`hoveredForCapture` 是离屏取证键（产品路径永远是 nil），
// R263 把 `HistoryRowViews` 里"字形墨 + animation value"两处都改读同一个合取式，并把这件事写成
// "一处 tint + 一条 animation value"。但那是**按文件**做的账 —— 同一形状的写法在另外三个文件里
// 还活着（本轮现读：`SettingsView.swift` 的侧栏行、`HistorySidebarView.swift` 的段按钮、
// `SearchField.swift` 的清除图标），而 R249 做掉 `SearchField` 那一格时只改了墨、没改动画的触发条件。
// 后果不是"像素错了"：静置帧一模一样。后果是**这条淡入在取证通道里从来没有过程** ——
// `.onHover` 在离屏恒 false ⇒ 动画的 value 永远不变 ⇒ 墨落下但没有中间态可数。
// 于是"这一档是不是淡进来的"这句话，在本仓库里连一个能被打红的证人都不配称。
//
// 这一格因此只判一件事，并且把它能判的范围写清楚：**同一个文件里如果画法读了取证键，
// 那条 `.hover` 动画的 value 就不许直读裸 `isHovered`。**
// 它不声明"动画真的在演"（那要帧侧证人 ⇒ 新开 BACKLOG 330）。
//
// 根目录由 `#filePath` 推（D-260：写死本机绝对路径的守卫是一台机器上的私货）。
import XCTest
@testable import ClipboardHistoryApp

final class HoverAnimationChannelTests: XCTestCase {

    // MARK: - 根与扫描面

    /// 产品源码目录：从本文件位置往上走，绝不写死任何一台机器的路径。
    private func sourcesRoot() throws -> URL {
        var url = URL(fileURLWithPath: #filePath)
        // .../ClipboardHistory/Tests/ClipboardHistoryAppTests/此文件 → 上三层到 ClipboardHistory
        for _ in 0..<3 { url.deleteLastPathComponent() }
        let candidate = url.appendingPathComponent("Sources/ClipboardHistoryApp")
        XCTAssertTrue(FileManager.default.fileExists(atPath: candidate.path),
                      "推出来的源码目录不存在：\(candidate.path) ⇒ 这把尺今天什么都没扫")
        return candidate
    }

    private func swiftFiles(in dir: URL) throws -> [URL] {
        let fm = FileManager.default
        guard let en = fm.enumerator(at: dir, includingPropertiesForKeys: nil) else { return [] }
        var out: [URL] = []
        for case let f as URL in en where f.pathExtension == "swift" { out.append(f) }
        return out.sorted { $0.path < $1.path }
    }

    /// 剥掉行注释（并只在**代码段**里判定），R76 那一课：整文件 contains 会命中自己引用的注释。
    private func codeOnly(_ text: String) -> String {
        text.split(separator: "\n", omittingEmptySubsequences: false).map { raw -> String in
            var out = ""
            var inString = false
            var previous: Character? = nil
            for ch in raw {
                if ch == "\"", previous != "\\" { inString.toggle() }
                if !inString && ch == "/" {
                    if previous == "/" { break }
                }
                out.append(ch)
                previous = ch
            }
            return String(out)
        }.joined(separator: "\n")
    }

    private struct Site: Equatable, CustomStringConvertible {
        let file: String
        let line: Int
        let valueExpression: String
        var description: String { "\(file):\(line) value=\(valueExpression)" }
    }

    /// 找出一个文件里所有 `.animation(MotionCatalog.animation(for: .hover), value: X)` 的 X。
    private func hoverAnimationSites(_ code: String, file: String) -> [Site] {
        var sites: [Site] = []
        let needle = "animation(for: .hover), value: "
        for (index, raw) in code.split(separator: "\n", omittingEmptySubsequences: false).enumerated() {
            let line = String(raw)
            guard let range = line.range(of: needle) else { continue }
            let rest = line[range.upperBound...]
            let value = rest.prefix { $0 != ")" }.trimmingCharacters(in: .whitespaces)
            sites.append(Site(file: file, line: index + 1, valueExpression: value))
        }
        return sites
    }

    // MARK: - 判定

    /// 一个文件"画法读了取证键"的证据：`@Environment(\.hoveredForCapture)` 出现在代码里。
    private func readsCaptureKey(_ code: String) -> Bool { code.contains("hoveredForCapture") }

    /// 裸读 = 动画 value 恰好是 `isHovered`（合取式的任何别名都不算）。
    private func isBare(_ value: String) -> Bool { value == "isHovered" }

    func testEveryHoverAnimationInAKnownFilesReadsTheSameConditionAsTheInk() throws {
        let root = try sourcesRoot()
        let files = try swiftFiles(in: root)
        XCTAssertGreaterThan(files.count, 20, "只扫到 \(files.count) 个文件 ⇒ 扫描面塌了，不是产品干净")

        var totalSites = 0
        var exemptFiles = 0
        var bare: [Site] = []
        for url in files {
            let text = try String(contentsOf: url, encoding: .utf8)
            let code = codeOnly(text)
            let sites = hoverAnimationSites(code, file: url.lastPathComponent)
            totalSites += sites.count
            if !readsCaptureKey(code) {
                exemptFiles += sites.count
                continue
            }
            bare.append(contentsOf: sites.filter { isBare($0.valueExpression) })
        }
        // 结论行打在断言之前（R94：掉在闸门之后就等于没跑）。
        print("HOVER_ANIM_ALIGNMENT files=\(files.count) sites=\(totalSites) "
              + "免检(不读取证键)=\(exemptFiles) 裸读=\(bare.count) 判=\(bare.isEmpty ? "PASS" : "RED")")
        XCTAssertTrue(totalSites > 0, "一把 hover 动画都没扫到 ⇒ 这把尺读的不是产品")
        XCTAssertEqual([], bare,
                       "画法接了取证键、动画的触发条件还直读裸 isHovered ⇒ 这条淡入在离屏通道里"
                       + "永远不触发（墨落下但没有过程）：\(bare.map { String(describing: $0) }.joined(separator: "、"))")
    }

    // MARK: - 真值表：这把尺自己的判别力

    func testTheRulerFlagsTheBareFormAndAcceptsTheConjunction() {
        XCTAssertTrue(isBare("isHovered"))
        XCTAssertFalse(isBare("isHoveredForDrawing"), "别名被当成裸读 ⇒ 修完也不会绿")
        XCTAssertFalse(isBare("isHovered || (hoveredForCapture ?? false)"))
    }

    func testTheRulerCountsSitesOnlyInCodeNotInComments() throws {
        let sample = """
        // .animation(MotionCatalog.animation(for: .hover), value: isHovered) 这一行是注释
        .animation(MotionCatalog.animation(for: .hover), value: isHoveredForDrawing)
        """
        let sites = hoverAnimationSites(codeOnly(sample), file: "Sample.swift")
        XCTAssertEqual(1, sites.count, "注释里那一行不该被数进来（R76：扫前剥注释）")
        XCTAssertEqual("isHoveredForDrawing", sites.first?.valueExpression)
    }

    func testExemptionIsDirectional() throws {
        // 不读取证键的文件豁免；一旦它接了键，同一处写法就必须被判红。
        let withoutKey = ".animation(MotionCatalog.animation(for: .hover), value: isHovered)"
        let withKey = "@Environment(\\.hoveredForCapture) var hoveredForCapture\n" + withoutKey
        XCTAssertFalse(readsCaptureKey(withoutKey))
        XCTAssertTrue(readsCaptureKey(withKey))
        let sites = hoverAnimationSites(withKey, file: "Directional.swift")
        XCTAssertEqual(1, sites.filter { isBare($0.valueExpression) }.count,
                       "接了键还留裸读 ⇒ 豁免必须翻面，否则名册会静默漏掉这一位")
    }
}
