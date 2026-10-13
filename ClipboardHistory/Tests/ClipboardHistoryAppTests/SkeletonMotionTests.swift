// 不覆盖管线：本文件钉骨架扫光的纯值规则（跑不跑、几何、节奏）与"它确实接在详情预览
// 的加载分支上"这条源码守卫。**不**证明屏幕上真的在扫 —— 那半条在
// `MotionFilmstripTests.testSkeletonSweepActuallySweeps`（要环境变量才跑）。
// （第三轮审计 C-1：这类文件要自己写明边界。）
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 动效审计 M9：详情预览加载态从 spinner 换成骨架扫光。
///
/// 为什么这里的东西这么多：这一条是仓库里**第一条常驻动画**。常驻的意思是
/// "它会在没人看的时候继续跑"，所以它的风险面不是"好不好看"，而是"什么时候停、按什么节奏走"。
/// 起、停、推进、以及"减弱动态时不许起"这四件事都必须能被断言，不能靠 review。
@MainActor
final class SkeletonMotionTests: XCTestCase {
    func testSweepRunsOnlyWhenMotionMayBeShown() {
        XCTAssertTrue(SkeletonMotion.sweepIsRunning(reduceMotion: false))
        XCTAssertFalse(SkeletonMotion.sweepIsRunning(reduceMotion: true),
                       "减弱动态时还在扫 ⇒ 常驻动画对前庭敏感的人是噪音")
    }

    /// 亮带必须在每一圈里**完整地**进出画面：相位 0 时整条在左外，1 时整条在右外。
    /// 停在画面里的话，每圈头尾都切在边缘上，读起来像"扫到一半卡住再弹回去"。
    func testBandStartsAndEndsFullyOutsideTheView() {
        XCTAssertLessThanOrEqual(SkeletonMotion.bandStart(forPhase: 0) + SkeletonMotion.bandSize, 0,
                                 "相位 0 时亮带已经露进画面里了")
        XCTAssertGreaterThanOrEqual(SkeletonMotion.bandStart(forPhase: 1), 1,
                                    "相位 1 时亮带还没完全走出右边缘")
        XCTAssertLessThan(SkeletonMotion.bandStart(forPhase: 0), SkeletonMotion.bandStart(forPhase: 1),
                          "方向反了 ⇒ 亮带会从右往左扫")
    }

    /// 端点几何：带宽恒定，且 start 一定在 end 左边。
    /// 带宽一旦随相位变，看到的就不是"一条带在动"，而是"一条带在呼吸"。
    func testBandKeepsItsWidthAcrossTheWholeCycle() {
        for phase in stride(from: CGFloat(0), through: 1, by: 0.05) {
            let points = SkeletonMotion.unitPoints(phase: phase)
            XCTAssertLessThan(points.start.x, points.end.x, "phase=\(phase)")
            XCTAssertEqual(points.end.x - points.start.x, SkeletonMotion.bandSize, accuracy: 0.0001,
                           "phase=\(phase)：带宽变了，那不再是一条带在移动")
            XCTAssertEqual(points.start.y, points.end.y, accuracy: 0.0001, "带不该斜着走")
        }
    }

    /// 推进必须**绕回**。不绕的话相位过 1 就停住，"常驻循环"实际只演一次。
    func testAdvanceWrapsInsteadOfSticking() {
        XCTAssertEqual(SkeletonMotion.advance(0.95, by: 0.1), 0.05, accuracy: 0.0001,
                       "过了一圈的终点就该回到起点附近")
        XCTAssertEqual(SkeletonMotion.advance(0.5, by: 0.1), 0.6, accuracy: 0.0001)
        XCTAssertEqual(SkeletonMotion.advance(0.5, by: 0), 0.5, "零步长不许把相位推走")
        XCTAssertEqual(SkeletonMotion.advance(0.5, by: -0.2), 0.5, "负步长（时钟倒灌）直接忽略")
        var phase: CGFloat = 0
        for _ in 0..<1000 { phase = SkeletonMotion.advance(phase, by: 1.0 / 45.0) }
        XCTAssertGreaterThanOrEqual(phase, 0)
        XCTAssertLessThan(phase, 1, "跑了一千拍之后相位还在 0…1 内：没有漂出去，也没有卡死在 1")
    }

    /// 三根条、宽度互不相同且都在可用宽度内。
    /// 三根一样会被读成"这里有个进度条"，而它说的应该是"这里马上有标题和两行正文"。
    func testBarsReadAsContentNotAsAProgressBar() {
        XCTAssertEqual(SkeletonMotion.barFractions.count, 3, "报告 §3 给的就是三条 8px 高的条带")
        XCTAssertEqual(Set(SkeletonMotion.barFractions).count, SkeletonMotion.barFractions.count,
                       "宽度全相同 ⇒ 三根一样的杠，读不出'内容'")
        for fraction in SkeletonMotion.barFractions {
            XCTAssertGreaterThan(fraction, 0.1)
            XCTAssertLessThanOrEqual(fraction, 1.0, "条带比可用宽度还宽会被裁，而裁掉的正是'马上来'的那部分")
        }
    }

    // MARK: - 节奏

    /// 一拍的推进量。**目录给的 1.5s 一圈 / 30Hz 一拍 = 0.0222**，也就是 45 步一圈。
    /// 退化输入一律返回 nil（调用方据此**不起时钟**），因为"每拍推进 100%"的表现是
    /// 一条在随机跳的杠，比不动更糟。
    func testFractionIsTheCatalogDividedByTheTick() {
        let step = SkeletonMotion.fraction(secondsPerCycle: MotionCatalog.duration(for: .skeletonSweep))
        XCTAssertNotNil(step, "目录给的那一圈必须能起")
        let value = try? XCTUnwrap(step)
        XCTAssertEqual(value ?? 0, CGFloat(SkeletonMotion.tickInterval / MotionCatalog.duration(for: .skeletonSweep)),
                       accuracy: 0.000001, "推进量不是「一拍 ÷ 一圈」 ⇒ 视图里另写了一个秒数")
        XCTAssertGreaterThan(value ?? 0, 0)
        XCTAssertLessThan(value ?? 1, 1, "一圈至少要好几拍")
        for cycle in [0.0, -1.0, SkeletonMotion.tickInterval, SkeletonMotion.tickInterval / 2] {
            XCTAssertNil(SkeletonMotion.fraction(secondsPerCycle: cycle),
                         "一圈 \(cycle)s 配 \(SkeletonMotion.tickInterval)s 一拍：这个节奏不该起")
        }
    }

    /// 亮带必须比底色**亮到看得见**。这条是被测量逼出来的：抬 5 个点时胶片读到 0.0000，
    /// 和"动画根本没跑"是同一个读数（详见 `SkeletonMotion.minimumHighlightLift` 的注释）。
    /// 所以"克制"不能只写在注释里 —— 写成数字，谁调回去就会红。
    func testHighlightIsFarEnoughAboveTheBaseToBeSeen() {
        let lift = SkeletonMotion.highlightOpacity - SkeletonMotion.baseOpacity
        XCTAssertGreaterThanOrEqual(lift, SkeletonMotion.minimumHighlightLift,
                                    "亮带只抬了 \(lift)：像素上等于没动，这条扫光就是白做")
        XCTAssertLessThanOrEqual(SkeletonMotion.highlightOpacity, 0.35,
                                 "再亮就成三条白杠了，抢的是正文")
        XCTAssertGreaterThan(SkeletonMotion.baseOpacity, 0)
    }

    // MARK: - 接线守卫

    /// 接线守卫（D-055 / MC-12 的教训：纯值全对，也可能没人调用）。
    func testSkeletonIsWiredIntoTheDetailLoadingBranch() throws {
        let preview = try productSource(named: "Views/DetailPreviewViews.swift")
        let shimmer = codeOnly(try productSource(named: "Views/SkeletonShimmer.swift"))

        let loadingCase = try XCTUnwrap(
            preview.components(separatedBy: "case .loading:").dropFirst().first?
                .components(separatedBy: "case .").first,
            "找不到 `case .loading:` 分支：锚点失效")
        // R26 把 `loadingView` 这个私有计算属性提成了具名视图 `DetailLoadingView`，
        // 于是这条守卫从"分支里有个叫 loadingView 的东西"升级成两件更硬的事：
        // ① 分支必须画那个**类型**；② 帧基线里那张 `detail-loading` 必须画**同一个类型**
        //    —— 以前"帧长得像不像产品"只能靠人看，现在它由"两边引用同一个符号"钉住。
        XCTAssertTrue(loadingCase.contains("DetailLoadingView("),
                      "加载分支没走 `DetailLoadingView` ⇒ 骨架接在哪没人知道，"
                          + "而 `detail-loading` 那张帧也就没人保证它画的是产品真用的那个视图")
        let harnessURL = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let harness = try String(contentsOf: harnessURL, encoding: .utf8)
        XCTAssertTrue(harness.contains("DetailLoadingView("),
                      "`detail-loading` 帧不再渲染 `DetailLoadingView` ⇒ 帧与产品分家了："
                          + "这张帧审的是夹具自己拼的东西，产品改成什么样都不会让它红")
        XCTAssertTrue(preview.contains("SkeletonPreviewView("),
                      "详情预览的加载态里根本没有骨架 ⇒ M9 只是注释里的事实")
        XCTAssertFalse(preview.contains("ProgressView()"),
                       "spinner 又回来了：那意味着这块同时有'我在等'和'内容马上来'两种语言，"
                       + "而 M9 换掉它的理由恰恰是后者比前者有用")

        XCTAssertTrue(shimmer.contains("Timer.publish(every: SkeletonMotion.tickInterval, on: .main, in: .common)"),
                      "时钟没按目录的节奏来 ⇒ 视图里出现了自己写的秒数")
        XCTAssertTrue(shimmer.contains("phase = SkeletonMotion.advance(phase, by: step)"),
                      "每一拍没有推进相位 ⇒ 骨架是一条不动的灰杠，比 spinner 更糟")
        XCTAssertTrue(shimmer.contains("MotionCatalog.duration(for: .skeletonSweep)"),
                      "一圈的时长没走目录 ⇒ 250ms 上限例外表管不到它")
        XCTAssertTrue(shimmer.contains("if SkeletonMotion.sweepIsRunning(reduceMotion: reduceMotion)"),
                      "减弱动态的闸门没接在'要不要订阅时钟'上 ⇒ 系统开关对它无效")
        XCTAssertTrue(shimmer.contains("} else {\n            bars"),
                      "减弱动态那一档连骨架都不画了 ⇒ 那是把功能关掉，不是把动效替换成更轻的表达")
        XCTAssertFalse(shimmer.contains("repeatForever"),
                       "又用回渲染树那条循环：它**没被量过**（`SkeletonShimmer.swift` 文件头记着那三个 0.0000 里至少有一个是对比度造成的误判）。"
                       + "要换回去，先在胶片上把开臂跑到'变化帧对 ≥3'再说")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relative: String) throws -> String {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + relative)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "SkeletonMotionTests", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红",
        ])
    }
}
