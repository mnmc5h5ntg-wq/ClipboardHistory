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
    /// 这样"令牌被改"与"函数被改坏"会分别红，而不是互相当对方的证人。
    func testFillOpacityTruthTableBothAppearances() {
        for dark in [true, false] {
            let tag = dark ? "dark" : "light"
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: false,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           0, accuracy: 0.0001, "\(tag)：既没按也没悬停却画了底")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.08 : 0.105, accuracy: 0.0001, "\(tag)：hover 那一档不对")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: true,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.12 : 0.135, accuracy: 0.0001,
                           "\(tag)：按下时 hover 还在 ⇒ 两档叠成一坨（R20 抓到过的叠层那一族）")
            XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: false,
                                                          hoverLevel: VisualFill.controlHover, dark: dark),
                           dark ? 0.12 : 0.135, accuracy: 0.0001, "\(tag)：pressed 那一档不对")
        }
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
