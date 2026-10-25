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

    /// 选中那颗的**抬量**按色档分叉（R339 / BACKLOG 411）：暗档在语义基准之上再盖一层白色，
    /// 亮档不盖。三句话各拦一种坏法：
    /// ① 暗档必须真的读到那个令牌（`liftAlpha(dark: true)` 改成 `nil` = 把本轮的修法删掉，
    ///    而它在**本机像素上不会红** —— 本机页底 30 时轨道 52、那颗 70 仍然差 +18，
    ///    这正是 runner 那 8 跑的盲区：绝对电平只在"页底恰好 30"的那台机器上成立）；
    /// ② 亮档必须是 `nil`（"顺手两档都盖"会把亮档的选中推出纸白 —— 230 的亮轨道再抬 25%
    ///    就顶到 255，选中与空白分不开，而亮档欠的是换一条轴，记在 BACKLOG 399）；
    /// ③ α 的两条边界必须是**实测**数夹出来的区间，写成会红的算术而不是注释（下面那一格）。
    /// 屏幕上那一半不在这里证：`UICaptureHarness.testSelectedPillStaysAboveItsTrackOnEveryBacking`
    /// （同一条夹具通道铺三档人造页底，逐档量「选中 − 轨道」）。
    /// R345 / 399·421：选中那颗的身份换到**边界**这条轴 —— 亮档画一根发丝边，暗档不画。
    func testSegmentEdgeIsLightOnlyAndWithinTheHairlineRange() {
        XCTAssertNil(SegmentEdge.width(dark: true), "暗档不画这根边：它的身份已经在抬量那条轴上")
        XCTAssertNil(SegmentEdge.alpha(dark: true))
        XCTAssertEqual(SegmentEdge.width(dark: false), 1)
        XCTAssertEqual(SegmentEdge.alpha(dark: false), VisualMaterial.selectedSegmentEdge)
        XCTAssertGreaterThan(VisualMaterial.selectedSegmentEdge, 0.0, "0 = 没有这根边")
        XCTAssertLessThan(VisualMaterial.selectedSegmentEdge, 0.30, "发丝边不是描边装饰")
        // 同一条形状的两支不许互相顶替：亮档两根都画、或哪一档两根都不画，都是换档换出了洞
        XCTAssertNil(SegmentKnob.liftAlpha(dark: false))
        XCTAssertEqual(SegmentKnob.liftAlpha(dark: true), VisualMaterial.selectedSegmentLiftWhite)
    }

    func testSegmentKnobLiftSplitsByAppearanceAndReadsTheToken() {
        XCTAssertEqual(SegmentKnob.liftAlpha(dark: true), VisualMaterial.selectedSegmentLiftWhite,
                       "暗档必须盖那一层：不透明基准停在解析值 70，而轨道跟着页底漂（30→52、50→70、真机 51→81）"
                       + " ⇒ 在页底 50 的机器上两者读成同一个灰阶，『哪颗被选中』就没有读者了（BACKLOG 411）")
        XCTAssertNil(SegmentKnob.liftAlpha(dark: false),
                     "亮档不许被顺手统一成叠加：白色压在 230 的亮轨道上会把选中顶到纸白，"
                     + "选中与空白又分不开（亮档欠的是换轴，见 BACKLOG 399）")
    }

    /// **α=0.20 是两条实测边界夹出来的区间中位**，不是试出来的数。
    /// 两头都有牙：往下调撞①（盖不过已测到最亮那条轨道），往上调撞②（超过平台自己那颗选中）。
    func testSelectedSegmentLiftAlphaIsTheSandwichSolvedFromMeasuredTracks() {
        let alpha = VisualMaterial.selectedSegmentLiftWhite
        let base = 70.0              // R331/R333 现读的解析值，两机同读（不随页底动）
        let brightestTrack = 97.0    // 本轮 `SEG_PILL_BACKING` 三档里最亮那条轨道（页底 80 那档）
        let systemKnob = 109.0       // 同一轮 `SEGREF_POLARITY dark` 在 runner 现读的系统那颗
        let pill = base + alpha * (255.0 - base)
        XCTAssertGreaterThan(pill, base, "叠加必须让那颗更亮，不然这一格量的是一条恒等式")
        // ① 下界：盖过最亮那条实测轨道 + 仓库自己的『分不开』线 8/255（真机那把尺的 DELTA）。
        XCTAssertGreaterThanOrEqual(pill - brightestTrack, 8.0,
            "抬量之后那颗只算到 " + String(format: "%.1f", pill) + "，比最亮那条轨道（"
                + String(format: "%.0f", brightestTrack) + "）只高 "
                + String(format: "%.1f", pill - brightestTrack) + "，低于『分不开』线 8"
                + " ⇒ 那一档页底上还是看不出哪颗被选中")
        // ② 上界：不许比平台自己那颗选中更亮（参照臂现读 109）。
        XCTAssertLessThanOrEqual(pill, systemKnob,
            "抬完算到 " + String(format: "%.1f", pill) + "，已经盖过系统那颗现读的 "
                + String(format: "%.0f", systemKnob) + " ⇒ 越过了参照臂，选中变成一块我自己的颜色")
        // 区间不是单点：三个两位小数可用，取正中那个 —— 这一条拦『把边界说成唯一解』的措辞。
        let candidates = (10...40).map { Double($0) / 100.0 }.filter {
            let p = base + $0 * (255.0 - base)
            return p - brightestTrack >= 8.0 && p <= systemKnob
        }
        XCTAssertGreaterThanOrEqual(candidates.count, 2,
            "边界只该有一个候选时说明我把区间写窄了（现数出来 "
                + String(candidates.count) + " 个：" + candidates.map { String($0) }.joined(separator: " ") + "）")
        XCTAssertEqual(alpha, candidates[candidates.count / 2],
                       "α 必须取那一段可行两位小数的中位（现取 " + String(alpha) + "）")
    }
}
