// 不覆盖管线：本文件只判 `FilterPillGeometry` 这颗纯核（段号 ↔ 矩形 ↔ 段号的恒等式、内缩、越界夹住、
// 以及"视图确实调了它"的接线扫描）。管线级判据在同目录 `UICaptureHarness.swift` 的
// `testFilterPillBrightBandFollowsTheSelectedSegment` —— 那条拍两态帧、逐行量亮区落在第几段。
// 分开写是因为这两件事的坏法不同：纯核坏了 = 算错；接线断了 = 算对了也没人用（AGENTS.md 第 1 条）。
import XCTest
@testable import ClipboardHistoryApp

final class FilterPillGeometryTests: XCTestCase {

    /// 恒等式：对任意轨道宽、任意段数、任意段号，**药丸矩形中心反解回来的段号必须等于进去的段号**。
    /// 这条比"逐格写期望值"更硬：它不依赖我手算任何坐标（R130 那一课：真值表的期望值不许心算）。
    func testPillRectRoundTripsToItsOwnSegment() {
        for count in [1, 2, 3, 4] {
            for rawWidth in [40.0, 129.0, 256.0, 517.0, 900.0] {
                let track = CGRect(x: 12, y: 4, width: rawWidth, height: 26)
                for index in 0..<count {
                    let rect = FilterPillGeometry.pillRect(in: track, count: count, index: index)
                    XCTAssertEqual(
                        FilterPillGeometry.segmentIndex(containingX: rect.midX, in: track, count: count),
                        index,
                        "count=\(count) width=\(rawWidth) index=\(index)：算出来的矩形中心反解回第几段不等于进去的段号")
                    XCTAssertEqual(rect.height, 26 - 2 * FilterPillGeometry.verticalInset, accuracy: 0.001,
                                   "count=\(count) index=\(index)：药丸高度没按 verticalInset 内缩")
                    XCTAssertLessThanOrEqual(rect.minX, track.maxX, "index=\(index) 跑到轨道右边外")
                    XCTAssertGreaterThanOrEqual(rect.maxX, track.minX, "index=\(index) 跑到轨道左边外")
                }
            }
        }
    }

    /// 最后一段的右沿不许越过轨道（`index = count-1` 是这个控件最容易漏的一格）。
    func testLastSegmentStaysInsideTheTrack() {
        let track = CGRect(x: 0, y: 0, width: 256, height: 26)
        for count in [2, 3, 5] {
            let rect = FilterPillGeometry.pillRect(in: track, count: count, index: count - 1)
            XCTAssertLessThanOrEqual(rect.maxX, track.maxX + 0.001,
                                     "count=\(count)：最后一段的药丸顶出轨道右沿")
            XCTAssertGreaterThan(rect.width, 0, "count=\(count)：段宽被内缩吃掉了，药丸画不出来")
        }
    }

    /// 越界**夹住**而不是回落到 0：回落到 0 会把"索引算错"画成"药丸在最左段"，
    /// 而那正好是这个控件最像正常的一种坏法（R188 撤回归档时量的就是这个形状）。
    func testOutOfRangeIndexIsClampedNotSilentlyZero() {
        let track = CGRect(x: 0, y: 0, width: 200, height: 26)
        let high = FilterPillGeometry.pillRect(in: track, count: 2, index: 7)
        let last = FilterPillGeometry.pillRect(in: track, count: 2, index: 1)
        XCTAssertEqual(high, last, "越上界应当夹到最后一段，而不是回落到第 0 段")
        let negative = FilterPillGeometry.pillRect(in: track, count: 2, index: -3)
        XCTAssertEqual(negative, FilterPillGeometry.pillRect(in: track, count: 2, index: 0),
                       "越下界应当夹到第 0 段")
    }

    func testDegenerateInputsGiveEmptyRectInsteadOfCrashing() {
        XCTAssertEqual(FilterPillGeometry.pillRect(in: .zero, count: 2, index: 0), .zero)
        XCTAssertEqual(FilterPillGeometry.pillRect(in: CGRect(x: 0, y: 0, width: 100, height: 26),
                                                   count: 0, index: 0), .zero)
        XCTAssertEqual(FilterPillGeometry.segmentIndex(containingX: 500, in: CGRect(x: 0, y: 0, width: 100, height: 26),
                                                       count: 2), -1,
                       "轨道外的 x 不许被算成某一段（宁可给 -1 让判据点名）")
    }

    /// 三种真实形状各钉一格（R190）。为什么必须在本机钉：这条出口在 runner 上被走到，
    /// 而 runner 不能当自己的证人 —— 出口如果哪天误判（把能判的说成判不了），只有本机的表能红。
    func testChannelCapabilityRejectsTheTwoBlindShapes() {
        let col = 560
        XCTAssertTrue(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 512, columnWidth: col, contrast: 214),
                      "本机暗档的真实形状（底轨占满列、材质与侧栏底差 214luma）必须判成「能判」，"
                      + "否则这条判据永远只走出口")
        XCTAssertFalse(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 250, columnWidth: col, contrast: 9),
                       "本机亮档的真实形状（差只有 9luma）必须判成「判不了」——它不是能判的那一档")
        XCTAssertFalse(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 0, columnWidth: col, contrast: -1),
                       "runner 的真实形状（底轨根本找不到）必须判成「判不了」，而不是拿 -1 当对比去红")
        XCTAssertFalse(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 100, columnWidth: col, contrast: 250),
                       "底轨只占列宽 18% 就说「找到了」是恒真式：宽度这一半前提也得有牙")
        XCTAssertTrue(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 224, columnWidth: col, contrast: 30),
                      "两条地板取等号时必须放行（`>=` 而不是 `>`），否则边界那一格永远差一点点")
        XCTAssertFalse(FilterPillGeometry.channelCanSeeMaterial(trackWidth: 512, columnWidth: 0, contrast: 214),
                       "列宽为 0 不许被算成「占比无穷大」")
    }

    /// 接线：出口与它的点名读数必须真的在判据里（把谓词从判据里删掉 ⇒ 这一格红）。
    func testCaptureJudgmentWiresTheCapabilityExit() throws {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let text = try String(contentsOf: url, encoding: .utf8)
        let code = text.split(separator: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("///") }
            .joined(separator: "\n")
        XCTAssertEqual(code.components(separatedBy: "FilterPillGeometry.channelCanSeeMaterial(").count - 1, 1,
                       "能力谓词在判据里应当恰好调用一次（多了是重复实现，少了是出口被摘掉）")
        XCTAssertTrue(code.contains("FILTER_PILL_UNCAPABLE"),
                      "点名读数不在了 ⇒ 出口变成静默 skip，那正是「把红放宽成沉默」那一族")
        XCTAssertTrue(code.contains("两档都判不了"),
                      "全档无能力时的 XCTSkip 分支不在了：那时判据会安静地什么都不判")
    }

    /// 接线扫描（**能力**而不是词汇）：视图里必须真的拿轨道尺寸去问这颗纯核，
    /// 并且摆放要用 `.position` —— 原来的 `frame(width:) + offset(x:)` 组合把基准交给了
    /// `GeometryReader` 的隐式对齐，实测两态读回来是镜像的（BACKLOG 210 / R189）。
    func testSidebarPillIsWiredToTheGeometryCore() throws {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
        let text = try String(contentsOf: url, encoding: .utf8)
        // 只扫**代码行**：注释里会出现"offset(x:)"这种被讨论的旧写法，整文件 contains 会被散文喂饱（R100 那一族）。
        let code = text.split(separator: "\n").filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        let calls = code.components(separatedBy: "FilterPillGeometry.pillRect(").count - 1
        XCTAssertEqual(calls, 1, "视图里 `FilterPillGeometry.pillRect(` 应当恰好一处（读到 \(calls)）⇒ 多了是重复实现，少了是没接线")
        XCTAssertTrue(code.contains(".position(x: rect.midX"),
                      "药丸的摆放必须走 `.position`（把中心钉在纯函数算出的那块），不许退回 `offset` + 隐式对齐")
        XCTAssertFalse(code.contains(".offset(x: idx"),
                       "`offset(x: idx…)` 那支旧写法还在视图里 —— 它就是 210 那条镜像反号的落点")
    }
}
