// 不覆盖管线：这几格量的是**反馈梯的数值形状**（两档各自的 alpha、台阶、次序），
// 以及"画法有没有去读按档的那个函数"。管线级的像素证人在捕获卷：
// `row-favorite-idle` / `row-favorite-hover` / `controlprobe-hover-ladder` 两档各一张，
// 由 `UICaptureTests.testHoverPillIsVisibleAgainstItsOwnSurfaceInBothAppearances` 逐像素判
// （R229 / BACKLOG 251：这一档以前从来没有帧）。
import XCTest
import SwiftUI
@testable import ClipboardHistoryApp

/// R229：亮档整条反馈梯抬一档（hover +0.025、pressed +0.015），暗档一字未动。
///
/// 病是实测出来的：亮档悬停药丸 `(238)` 压 `(255)` = **1.160:1**，掉在仓库自己定的亮档地板
/// 1.20 之下；而 R14 早就量过"只抬 hover"会把 `hover→pressed` 压到 `3.7/255`（地板 4/255）。
/// 两条地板在单一亮度通道上**不能同时满足** ⇒ 抬整条梯子，把台阶一起带走。
final class ControlHoverLadderTests: XCTestCase {

    /// 4/255 的"一块平面上看得出来"台阶，换算成 alpha 差（底是白，1 单位 alpha ≈ 1/255 灰阶）。
    private let minimumStep = 4.0 / 255.0

    /// 走**产品那个入口**（`PressableAppearance.fillOpacity`）而不是内部助手：
    /// 助手只是文本，函数才是产品读的东西 —— `VisualTokenTests` 那条"令牌必须有消费者"
    /// 正是按"VisualTokens.swift 以外有没有读它"判的，测试自己造个助手会把它骗过去。
    private func level(isPressed: Bool, isHovered: Bool, dark: Bool) -> Double {
        PressableAppearance.fillOpacity(isPressed: isPressed, isHovered: isHovered,
                                        hoverLevel: VisualFill.controlHover, dark: dark)
    }

    func testDarkLadderIsExactlyWhatItWas() {
        XCTAssertEqual(level(isPressed: false, isHovered: true, dark: true), 0.08, accuracy: 0.0001,
                       "暗档 hover 必须一字未动（R219 的教训：抬亮档不许顺手改暗档）")
        XCTAssertEqual(level(isPressed: true, isHovered: false, dark: true), 0.12, accuracy: 0.0001,
                       "暗档 pressed 必须一字未动")
    }

    /// **梯子的每一级都要分得开，不只是 hover→pressed 那一级**（R260 / BACKLOG 308）。
    ///
    /// 现读：亮档 hover 0.12 → pressed 0.15 → selected 0.16 —— 最后一级只剩 0.01 = 2.55/255，
    /// 比仓库自己给 hover→pressed 定的 4/255 地板还小，而这一条**从来没有被断言过**：
    /// 上面那格里 ② 有地板、③ 只查了严格小于。次序对、分不开，是两种不同的病。
    /// 暗档 0.08 → 0.12 → 0.16 两级都是 0.04，所以这条在暗档一直成立、在亮档一直不成立 ——
    /// 亮档那一级是被 R256 抬 hover（0.105→0.12）时挤出来的：抬了下面两级，没动最上面那一级。
    /// 这条判据先红在**改之前**（红名只有 light），红本身就是缺陷的证人；
    /// 修法是给选中那一档一条自己的换算 `SelectedInk`（亮档 0.16→0.18，暗档一字未动）。
    func testEveryRungOfTheLadderIsSeparableInBothAppearances() {
        let minimumStep = 4.0 / 255.0
        for dark in [true, false] {
            let tag = dark ? "dark" : "light"
            let hover = level(isPressed: false, isHovered: true, dark: dark)
            let pressed = level(isPressed: true, isHovered: false, dark: dark)
            let selected = SelectedInk.opacity(dark: dark)
            // 绝对锚点压在**字面数**上（R100：对照/相对判据对"整把尺一起偏"免疫，
            // 必须有一条压在自陈输入上的绝对格）：暗档一字未动、亮档 0.18。
            XCTAssertEqual(selected, dark ? 0.16 : 0.18, accuracy: 0.0001,
                           "\(tag)：选中那一档的字面数不是这个 ⇒ 令牌或换算被改了（R219：抬亮档不许顺手改暗档）")
            XCTAssertGreaterThanOrEqual(pressed - hover, minimumStep,
                                        "\(tag)：hover→pressed 只剩 \(pressed - hover) ⇒ 两档会被读成同一档")
            XCTAssertGreaterThanOrEqual(selected - pressed, minimumStep,
                                        "\(tag)：pressed→selected 只剩 \(selected - pressed)（地板 \(minimumStep)）"
                                        + "⇒ 按下与选中长得一样：瞬时状态盖不住持久状态，次序虽然对但读者分不出来")
        }
    }

    func testLightLadderClearsTheFloorAndKeepsTheStep() {
        let hover = level(isPressed: false, isHovered: true, dark: false)
        let pressed = level(isPressed: true, isHovered: false, dark: false)
        // ① 看得见：亮档药丸对白底要 ≥1.20。合成灰 = 255×(1−alpha)，实测有约 +3 的色管偏差，
        //    所以这里按"最坏也不低于地板"取：不加那个偏差时 alpha 必须已经够。
        let composite = 255.0 * (1.0 - hover)
        XCTAssertLessThanOrEqual(composite, 229.5,
                                 "亮档 hover \(hover) 合成到 \(composite) ⇒ 对 255 的对比度不足 1.20")
        // ② 分得开：hover→pressed 的台阶不许被抬 hover 压平（这正是 R14 拦下 0.10 的那条）。
        XCTAssertGreaterThanOrEqual(pressed - hover, minimumStep,
                                    "亮档 hover→pressed 只剩 \(pressed - hover) ⇒ 两档会被读成同一档")
        // ③ 次序仍是语义：hover < pressed < selected。
        XCTAssertLessThan(hover, pressed)
        XCTAssertLessThan(pressed, VisualFill.selected,
                          "pressed 抬过 selected ⇒ 持久状态与瞬时状态反了")
    }

    /// 真值表：`fillOpacity` 的四个分支 × 两档，期望值写成**令牌表达式**再对字面数，
/// R256 / 300：亮档两行随抬量改（0.105→0.12、0.135→0.15）；暗档三行一字未动。
    /// 这样"令牌被改"与"函数被改坏"会分别红，而不是互相当对方的证人。
    func testFillOpacityTruthTableBothAppearances() {
        for dark in [true, false] {
            let tag = dark ? "dark" : "light"
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: false,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           0, accuracy: 0.0001, "\(tag)：既没按也没悬停却画了底")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.08 : 0.12, accuracy: 0.0001, "\(tag)：hover 那一档不对")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: true,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.12 : 0.15, accuracy: 0.0001,
                           "\(tag)：按下时 hover 还在 ⇒ 两档叠成一坨（R20 抓到过的叠层那一族）")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: false,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.12 : 0.15, accuracy: 0.0001, "\(tag)：pressed 那一档不对")
        }
        // R230 补的三格。第一格不是"防御性断言"：`hoverLevel: 0` 是调用点在说
        // "这一家的悬停我不画"（段按钮就是），而抬量如果无条件加上去，0 就变成 0.025 ⇒
        // 屏幕上凭空多出一层灰。这一格本轮是被**帧**抓到的 —— 段按钮里**选中的那一段**
        // （它根本没有悬停层）亮档从 `(233)` 被画成 `(228)`，暗档同一格一动不动。
        // 而 R229 那一版已经带着这个洞推上线了（`a7e3154`）。
        for dark in [true, false] {
            let tag = dark ? "dark" : "light"
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                           hoverLevel: 0, dark: dark),
                           0, accuracy: 0.0001,
                           "\(tag)：调用点说了不画，抬量还是把 0 抬成了 0.025 ⇒ 幽灵层")
        }
        // 行那一档（0.06）也在这条换算上：亮档 0.10（R256 之前是 0.085）。写出来是因为
        // DetailView / 设置行那几处直接读的是这一档，BACKLOG 251 剩下的一半要搬的就是它。
        // 0.085 → 0.10 的改判理由：旧字面数把缺陷钉成了契约，而 1.171 < 1.20
        // 正是它换来的那一格；详见 VisualFillLift 的注释（R253/300）。
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                       hoverLevel: VisualFill.hover, dark: false),
                       0.10, accuracy: 0.0001,
                       "行那一档的亮档抬量不对（R256/300 改判 0.085 → 0.10）")
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                       hoverLevel: VisualFill.hover, dark: true),
                       VisualFill.hover, accuracy: 0.0001, "暗档必须等于令牌原值：本轮没动暗档的任何一个数")
    }

    /// 画法必须自己去问色档 —— 数值对了但调用点没接，屏幕上什么都没变（R219 同一族）。
    func testPressedLabelResolvesTheAppearanceItself() throws {
        let text = try productSource("Views/PressableStyle.swift")
        XCTAssertTrue(text.contains("dark: colorScheme == .dark"),
                      "PressedLabel 没把色档传进 fillOpacity ⇒ 亮档那一抬是死数")
        XCTAssertTrue(text.contains("@Environment(\\.colorScheme)"),
                      "色档必须由视图自己问，不从外面传布尔")
        XCTAssertFalse(text.contains("hoverLevel: hoverLevel))"),
                       "画法还在读不带色档的旧调用")
    }

    /// 名册守卫（R230 / BACKLOG 251 剩下那一半）：**产品里每一个读悬停令牌的地方，
    /// 要么把令牌交给共享换算（`hoverLevel:` 传进样式、或 `HoverInk.opacity(level:`），
    /// 要么就在这张名册上登记着。**
    ///
    /// 为什么要这张册子：R229 把亮档那一抬接进了 `fillOpacity`，于是"改了抬量"在**样式那一条路**上
    /// 生效，而自绘那一层的路径静悄悄地没动 —— 同一件事有两种说法，而且不会有任何东西变红。
    /// 一张按文件计数、且**只准变短**的册子是这条盲区唯一的证人（与 `testHistoryStoreStaysThin`
    /// 同一形状：用单调量，不用均值）。
    ///
    /// 册子要改的时候必须带着判据一起改：修掉一处 ⇒ 数字变小 ⇒ 这条红替你说话，去把数改成新的；
    /// 新写一处自绘悬停 ⇒ 数字变大 ⇒ 不许通过，把它接进共享换算。
    func testEveryHoverTokenReaderGoesThroughTheSharedConversionOrIsOnTheRoster() throws {
        let root = productSourcesRoot()
        // 定义处豁免：令牌自己（声明）与共享换算自己（`fillOpacity` / `HoverInk`）。
        let exemptFiles: Set<String> = ["VisualTokens.swift", "PressableStyle.swift"]
        // R231 / BACKLOG 256：**这张册子现在是空的**。三处自绘悬停层（`DetailView` 的 chip 与 card、
        // `SettingsView` 的侧栏分类行）都接进了 `HoverInk.opacity(level:dark:)` ⇒ 数字从 3 降到 0，
        // 而这条断言就是替这次"变小"说话的那个人（变大 = 新写一处自绘层 ⇒ 不许通过）。
        // 留空不等于留盲区：`strays` 那一条仍然会把任何没登记的新直读位点拦下来，
        // `conformingElsewhere` 那一条仍然要求浮层那一条按档换算能被数出来。
        let knownPending: [String: Int] = [:]
        // 这两家**不共享那条换算**，但等价：`QuickPickController` 自带 `hoverFillAlpha(dark:)`
        // 的按档抬量（R225），走的是 AppKit 的绘制路径而不是 SwiftUI。它们在册是因为
        // "另一条按档换算"是可以的，"没有按档换算"才是不行的 —— 而这一格也得能被数出来。
        let conformingElsewhere = ["QuickPickController.swift": 1]
        var found: [String: Int] = [:]
        for url in allSwiftFiles(in: root) {
            let name = url.lastPathComponent
            if exemptFiles.contains(name) { continue }
            guard let text = try? String(contentsOf: url, encoding: .utf8) else { continue }
            for raw in text.split(separator: "\n", omittingEmptySubsequences: false) {
                // 剥行注释：判"用没用"要看代码，不能看散文（R76 那一族：整文件 contains 会命中引用自己的注释）。
                var line = String(raw)
                if let cut = line.range(of: "//") { line = String(line[..<cut.lowerBound]) }
                guard line.contains("VisualFill.hover") || line.contains("VisualFill.controlHover") else {
                    continue
                }
                if line.contains("hoverLevel: VisualFill") || line.contains("HoverInk.opacity(level: VisualFill") {
                    continue          // 这两条都汇进共享换算
                }
                found[name, default: 0] += 1
            }
        }
        emitHoverRoster(found)
        let strays = found.filter { !knownPending.keys.contains($0.key)
            && !conformingElsewhere.keys.contains($0.key) }
        XCTAssertTrue(strays.isEmpty,
                      "出现**没登记**的悬停令牌直读位点：\(strays) ⇒ 要么接进共享换算（`hoverLevel:` / `HoverInk`），"
                      + "要么把它写进上面两张册子之一并说清为什么")
        let pending = found.filter { knownPending.keys.contains($0.key) }
        XCTAssertEqual(pending, knownPending,
                       "待改名册不吻合。变大 = 新写了一处自绘悬停层（不该）；"
                       + "变小 = 修掉了一处（把册子里的数字改小，并在台账记一笔）")
        let elsewhere = found.filter { conformingElsewhere.keys.contains($0.key) }
        XCTAssertEqual(elsewhere, conformingElsewhere,
                       "「另一条按档换算」那张册子不吻合 ⇒ 浮层那一条按档换算被改了或多了")
    }

    /// 把名册打到 stdout：判据的处置要能被复查，而不是只留一句断言文本。
    private func emitHoverRoster(_ found: [String: Int]) {
        let pairs = found.keys.sorted().map { "\($0)=\(found[$0]!)" }
        print("HOVER_TOKEN_ROSTER files=\(found.keys.count) reads=\(found.values.reduce(0, +)) "
              + (pairs.isEmpty ? "none" : pairs.joined(separator: " ")))
    }

    private func allSwiftFiles(in dir: URL) -> [URL] {
        let fm = FileManager.default
        guard let en = fm.enumerator(at: dir, includingPropertiesForKeys: nil) else { return [] }
        return en.compactMap { $0 as? URL }.filter { $0.pathExtension == "swift" }.sorted { $0.path < $1.path }
    }

    private func productSourcesRoot() -> URL {
        var dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let url = dir.appendingPathComponent("Sources/ClipboardHistoryApp")
            if FileManager.default.fileExists(atPath: url.path) { return url }
            dir = dir.deletingLastPathComponent()
        }
        // 找不到目录**红**而不是跳过：会跳过的守卫和通过的守卫在报表里长得一样（R99）。
        XCTFail("找不到 Sources/ClipboardHistoryApp ⇒ 名册守卫根本没在看东西")
        return URL(fileURLWithPath: "/nonexistent")
    }

    private func productSource(_ relative: String) throws -> String {
        var dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let url = dir.appendingPathComponent("Sources/ClipboardHistoryApp/" + relative)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            dir = dir.deletingLastPathComponent()
        }
        // 读不到**红**而不是跳过：会跳过的守卫和通过的守卫在报表里长得一样。
        XCTFail("读不到 Sources/ClipboardHistoryApp/" + relative)
        return ""
    }
}
