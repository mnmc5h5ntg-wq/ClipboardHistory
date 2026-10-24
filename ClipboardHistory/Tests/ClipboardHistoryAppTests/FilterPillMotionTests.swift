// 不覆盖管线：本文件只钉动效参数的纯函数分支，不证明屏幕上真的按这套参数在动。
// 在屏证据在 `UIInteractionProbeTests.testFrameIntervalsUnderStateChanges`（需要环境变量才跑）。
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-10（1.1 / 1.12）：筛选 pill 的过冲弹簧与 hover 放大以前不读「减弱动态效果」，
/// 而系统分段控件本来也没有这种弹性。策略抽成纯值 `SlideMotion`，两个分支都在这里钉住。
final class FilterPillMotionTests: XCTestCase {
    /// R12 把这一条**翻了过来**，理由写在这里而不是藏在 diff 里：
    /// 原来它断言 `damping < 1`（"正常态保留轻微过冲"）且 `response == 0.38`。
    /// 那是 R2-10 当时的决定，而目录后来立了规矩（MC-1）：
    /// **只有手势跟手的位移才给过冲**，程序触发的（点一下、换一档）一律临界阻尼。
    /// 这颗胶囊是点出来的 ⇒ 过冲不合法；0.38 又越过 `maximumDuration`。
    /// 也就是说：修规矩那一轮改了 `bannerIn` 的 0.86，却漏了这一处实例，
    /// 而目录注释里还写着"正确定义在 `FilterPillMotion`" —— 注释引用了一个没被改的旧值。
    func testSlideMotionIsCriticallyDampedAndSourcedFromTheCatalog() {
        let normal = FilterPillMotion.slideMotion(reduceMotion: false)
        XCTAssertFalse(normal.isInstant)
        XCTAssertEqual(normal.damping, MotionCatalog.criticalDamping,
                       "程序触发的位移不该过冲（MC-1）")
        XCTAssertEqual(normal.response, MotionCatalog.duration(for: .slider),
                       "参数必须出自目录，不许再写死一个字面量")
        XCTAssertLessThanOrEqual(normal.response, MotionCatalog.maximumDuration,
                                 "滑块这一档自己也要在上限之下")

        let reduced = FilterPillMotion.slideMotion(reduceMotion: true)
        XCTAssertTrue(reduced.isInstant, "减少动态时滑块瞬移：位移本身就是这条动效的全部内容")
        XCTAssertNotEqual(normal, reduced)
    }

    /// 减弱动态时**悬停不能变成零反馈**：缩放是物理隐喻，收掉之后必须留下非运动的那一层。
    ///
    /// R230 把这一格从"一个数"改成"按档两个数"（`dark:` 是新增的参数）。
    /// 原来那条 `== VisualFill.controlHover` 是一种**静态断言把缺陷钉成契约**的形状：
    /// 它把"亮档与暗档共用 0.08"写成了期望值，于是同一家族在别的位点被修掉时（R219 骨架墨、
    /// R225 浮层悬停、R229 小控件）这一条永远不会替它说话。
    /// 现在断的是**次序与出口**，不是某个字面量：暗档 = 令牌原值、亮档 = 令牌 + 抬量、
    /// 未悬停与选中那两段必须是 0（抬量不许长在"没画"那两条分支上）。
    /// 屏幕上的那一半不在这里证 —— 见 `UICaptureHarness` 的 `segmented-filter-hover` 帧判据。
    func testHoverKeepsANonMotionSubstituteWhenReducingMotion() {
        XCTAssertEqual(FilterPillMotion.hoverFill(isHovered: true, isSelected: false, dark: true),
                       VisualFill.pillHover,
                       "R334 / BACKLOG 396：暗档改走胶囊自己那一档 —— 继续共用 `controlHover` 画出来的"
                       + "悬停档（实测灰阶 66）与选中那颗（70）只差 4 级，鼠标一停两颗看起来都被选中")
        XCTAssertEqual(FilterPillMotion.hoverFill(isHovered: true, isSelected: false, dark: false),
                       VisualFill.controlHover + VisualFillLift.hover,
                       "亮档 = 令牌 + 抬量（R230 / BACKLOG 251 那一族，这一发**没动**）："
                       + "亮档空闲 230 与选中 220 之间只剩 1.099，放不下第三条能过线的档 ⇒ 要修得换轴，"
                       + "记在 BACKLOG 399")
        XCTAssertLessThan(VisualFill.pillHover, VisualFill.controlHover,
                          "pillHover 必须比全局那一档轻 —— 它存在的全部理由就是『离选中那颗远一点』；"
                          + "写成 ≥ 就是把 396 又请回来了")
        XCTAssertGreaterThan(VisualFill.pressed, VisualFill.pillHover,
                             "按下必须比悬停重：梯子的次序（R14 / R256 同一条），换档不许把它倒过来")
        XCTAssertGreaterThan(FilterPillMotion.hoverFill(isHovered: true, isSelected: false, dark: false),
                             FilterPillMotion.hoverFill(isHovered: true, isSelected: false, dark: true),
                             "亮档必须比暗档重：primary 在亮档是 85% 黑、暗档是 85% 白，同一 alpha 下亮档天然更淡")
        for dark in [true, false] {
            XCTAssertEqual(FilterPillMotion.hoverFill(isHovered: true, isSelected: true, dark: dark), 0,
                           "选中那一段下面就是胶囊，再叠一层悬停底会读成两块")
            XCTAssertEqual(FilterPillMotion.hoverFill(isHovered: false, isSelected: false, dark: dark), 0,
                           "没悬停就不许有抬量：0.025 画在没被指的段上就是凭空多一层灰")
        }
        // 两臂合起来才成立：reduce 收掉缩放、底色留着。
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: true, reduceMotion: true), 1.0)
        XCTAssertGreaterThan(FilterPillMotion.hoverFill(isHovered: true, isSelected: false, dark: true), 0,
                             "缩放被收掉而底色也没有 ⇒ 开了减弱动态的用户悬停无反馈")
    }

    func testHoverScaleIsOneWhenReducingMotionOrNotHovered() {
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: true, reduceMotion: false), 1.08)
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: true, reduceMotion: true), 1.0,
                       "减少动态时不许放大")
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: false, reduceMotion: false), 1.0)
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: false, reduceMotion: true), 1.0)
    }

    /// 接线守卫：视图必须真的走这套策略。纯函数正确但没人调用 = 没修。
    func testSidebarConsumesTheMotionPolicyInsteadOfHardcodingSpring() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else {
            XCTFail("找不到 HistorySidebarView.swift ⇒ 守卫看不到被守卫的东西，不许当没跑")
            return
        }
        let source = try String(contentsOf: file, encoding: .utf8)
        // 注释里**允许**出现 0.38/0.72（这一轮就是要写下"以前是这两个值、为什么不能回来"），
        // 所以扫字面量之前先把注释行摘掉。不摘的话就是"守卫把自己写的说明判成违规"。
        let code = source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")

        XCTAssertFalse(code.contains(".spring(response: 0.38"),
                       "pill 的弹簧参数又被写死在视图里了，减少动态的门控会被绕过")
        // 旧值整族都不许回来：只禁 `.spring(response: 0.38` 会放过"把 0.38/0.72 挪到别处写"。
        XCTAssertFalse(code.contains("0.38") || code.contains("0.72"),
                       "0.38 / 0.72 这两个旧字面量还在侧栏的代码里 ⇒ 目录那一档改了这里也不会跟着改")
        XCTAssertEqual(
            source.components(separatedBy: "FilterPillMotion.slideAnimation(reduceMotion:").count - 1, 1,
            "滑块动画应当恰好在一处由策略给出"
        )
        XCTAssertEqual(
            source.components(separatedBy: "FilterPillMotion.hoverScale(isHovered:").count - 1, 1,
            "hover 放大应当恰好在一处由策略给出"
        )
        XCTAssertTrue(source.contains("accessibilityReduceMotion"),
                      "必须读系统的「减弱动态效果」（环境那一份是自动响应的）")
        // R12：这一段以前**只**读环境开关 ⇒ 开着 VoiceOver 的人别处都降级、只有这颗胶囊还在弹。
        XCTAssertTrue(source.contains("MotionCatalog.motionShouldBeReduced"),
                      "闸门必须与全仓同一份：系统开关 ∪ VoiceOver")
        XCTAssertGreaterThanOrEqual(
            source.components(separatedBy: "reduceMotion || MotionCatalog.motionShouldBeReduced").count - 1, 2,
            "两个视图（滑块、段按钮）都要用合成闸门，只有一处 = 另一半还在读单源")
        // 纯函数有人调用才算修完（MC-12 那一族）。底色是"reduce 时唯一剩下的悬停表达"，
        // 它没接上就等于这一轮什么都没改。
        XCTAssertEqual(
            source.components(separatedBy: "FilterPillMotion.hoverFill(isHovered:").count - 1, 1,
            "悬停底色没人读 ⇒ 减弱动态时这一段又回到'只有缩放'，也就是零反馈")
    }
}
