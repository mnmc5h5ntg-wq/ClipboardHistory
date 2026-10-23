// 不覆盖管线：本文件钉的是**页底参照怎么选**这块纯函数（候选窗的几何、三道闸的取舍）。
// 管线级判据在捕获卷：`UICaptureTests.testQuickPickSelectionPillAgainstSystemArms`
// —— 它走 `quickpick-list` 夹具、落盘 PNG、再读回字节，两档外观各判一次"选中底落在哪枚系统参照色上"，
// 并由本轮新增的 `QUICKPICK_SELARM_BANDS` 把那一台的几何与两块候选窗的读数打成证据。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R321：`QUICKPICK_SELARM` 在 runner 上判红，而红的是尺。
///
/// runner（1× 那台机器）读数：`light[原因=取样窗底色不实：药丸中段占比=78% 页底占比=45%，下限 60%]`，
/// 而暗档**过了闸**、打印出 `页底=(61,61,61)`，同一帧全帧页底档是 30 ——
/// 那一格落在**滚动条槽**上：同一台机器上药丸比本机窄 16pt（`OVERLAY_HOVER_OUTLINE`
/// 在 runner 印 22…382，本机 43…796px=21.5…398pt）。本机 2× 的帧与它的 1× 代理上，
/// 药丸**左侧前导留白**（x=4…39px@2× / 2…21px@1×）的精确众数占比都是 100%（亮 255 / 暗 30）。
///
/// 下面这些格子量的是"换成两块候选窗、再加一道『它得真的是页底』"之后那个选择函数的行为，
/// 包括**把 runner 那一格的形状合成出来**再判一次（第 ② 组）。
/// 合成帧不是产品事实：它只证明这把尺认得那个形状；
/// "这一台到底读到了什么"由上面那条捕获卷判据自己印。
@MainActor
final class QuickPickSelectionArmTests: XCTestCase {

    // MARK: - 合成帧

    /// 合成帧。`@MainActor` 不是装饰：`armMedian` 住在 `UICaptureTests`（整颗类是主 Actor 的）里，
    /// 嵌套类型**不继承**外层的隔离，漏标就是一片 `#ActorIsolationCall`。
    @MainActor
    private struct Frame {
        let width: Int
        let height: Int
        var bytesPerRow: Int { width * 4 }
        var bytes: [UInt8]

        init(width: Int, height: Int, fill: (Int, Int, Int)) {
            self.width = width
            self.height = height
            bytes = [UInt8](repeating: 0, count: width * height * 4)
            paint(xRange: 0..<width, yRange: 0..<height, rgb: fill)
        }

        mutating func paint(xRange: Range<Int>, yRange: Range<Int>, rgb: (Int, Int, Int)) {
            for y in yRange {
                for x in xRange {
                    let o = y * bytesPerRow + x * 4
                    bytes[o] = UInt8(max(0, min(255, rgb.0)))
                    bytes[o + 1] = UInt8(max(0, min(255, rgb.1)))
                    bytes[o + 2] = UInt8(max(0, min(255, rgb.2)))
                    bytes[o + 3] = 255
                }
            }
        }

        func median(xRange: Range<Int>, yRange: Range<Int>)
            -> (rgb: UICaptureTests.ArmRGB, share: Int)? {
            bytes.withUnsafeBufferPointer { pointer in
                guard let base = pointer.baseAddress else { return nil }
                return UICaptureTests.armMedian(bytes: base, bytesPerRow: bytesPerRow,
                                                xRange: xRange, yRange: yRange)
            }
        }
    }

    /// 把候选窗喂给选择函数 —— 与捕获卷里那一段**同形状**：窗由 `pageBands` 给、
    /// 读数由 `armMedian` 给、取舍由 `choosePageArm` 给（不许真值表测另一颗尺）。
    private func choose(frame: Frame, bands: [(label: String, xRange: Range<Int>)],
                        pillY: Range<Int>, pageLuma: Int)
        -> (chosen: (label: String, rgb: UICaptureTests.ArmRGB, share: Int)?, report: String) {
        let probes: [(label: String, probe: (rgb: UICaptureTests.ArmRGB, share: Int)?)] =
            bands.map { band in
                (label: band.label, probe: frame.median(xRange: band.xRange, yRange: pillY))
            }
        return UICaptureTests.choosePageArm(probes: probes, pageLuma: pageLuma,
                                            floor: UICaptureTests.armSolidShareFloor)
    }

    // MARK: - ① 候选窗的几何按倍率换算，不是裸像素

    /// 本机 2× 与 runner 1× 上，同一对 pt 偏移必须换算成各自的 px。
    ///
    /// 这一格钉的是"两台机器量的是同一片地方"：上一版写死 `right+4 ..< right+24` **像素**，
    /// 2× 上是 2…12pt、1× 上就成了 4…24pt —— 窗在 runner 上比在本机宽一倍，
    /// 而那个位置恰好是滚动条槽。R58 那族（像素数不是几何）第三次复发，这次连"哪一格能用"都改了。
    func testPageBandOffsetsAreBackingScaleRelative() {
        let twoX = UICaptureTests.pageBands(width: 840, pillLeft: 43, pillRight: 796, scale: 2)
        XCTAssertEqual(twoX.map { $0.label }, ["前导", "右侧"],
                       "2× 上两块窗都该在（前导 35px 宽、右侧 20px 宽，都过 8px 下限）")
        XCTAssertEqual(twoX[0].xRange, 4..<39, "前导 = 2pt 到药丸左沿减 2pt（按 2× 换算成 px）")
        XCTAssertEqual(twoX[1].xRange, 800..<820,
                       "右侧 = 右沿加 2pt 到加 12pt（与上一版在本机上的 4…24px 等价）")

        // runner 那一台的实测几何：药丸 23…381px@1×、帧宽 420px。
        let oneX = UICaptureTests.pageBands(width: 420, pillLeft: 23, pillRight: 381, scale: 1)
        XCTAssertEqual(oneX.map { $0.label }, ["前导", "右侧"])
        XCTAssertEqual(oneX[0].xRange, 2..<21)
        XCTAssertEqual(oneX[1].xRange, 383..<393,
                       "1× 上右侧窗必须仍是 2…12pt（写成裸像素 4…24px 就会把槽读进来）")
        XCTAssertEqual(oneX[1].xRange.count, 10)
        XCTAssertEqual(twoX[1].xRange.count, 20, "2× 上同一片 pt 就是两倍的 px —— 宽度差是倍率，不是几何")
    }

    /// 前导留白窄到不够一块窗时不许硬造（宁可少一块候选，也不要一根 1px 的线当窗）。
    func testPageBandDropsWhenTooNarrow() {
        let tight = UICaptureTests.pageBands(width: 420, pillLeft: 5, pillRight: 381, scale: 1)
        XCTAssertEqual(tight.map { $0.label }, ["右侧"],
                       "药丸左沿只有 5px ⇒ 前导窗宽度不足 8px，必须整块不给")
        XCTAssertTrue(UICaptureTests.pageBands(width: 420, pillLeft: 5, pillRight: 414, scale: 1)
                      .isEmpty, "右侧窗被帧宽截到 8px 以下、前导又不足 ⇒ 两块都不给，选择函数只能点名")
    }

    // MARK: - ② runner 那一格的形状：底色稳不等于它是页底

    /// 合成一张 runner 形状的暗档帧：页底 (30,30,30)、药丸 (70,70,70)、
    /// 药丸右侧那一格是一整片 (61,61,61) 的**滚动条槽**（占比很高、底色很"稳"，但它不是页底）。
    ///
    /// 这一格是本轮的结案证人：上一版只有右侧那一格，于是 61 被当成页底喂进混合模型，
    /// 而 obs 与非 key 逐字节相等时最小二乘解出 a=1.00、残差 0 ——
    /// **错的参照物照样报出落点**，那一行的 `key残差=11(a=0.04)` 就是它撑不住的形状。
    func testRunnerShapedScrollerBandIsRejectedByName() {
        var frame = Frame(width: 420, height: 300, fill: (30, 30, 30))
        frame.paint(xRange: 23..<382, yRange: 46..<80, rgb: (70, 70, 70))   // 药丸
        frame.paint(xRange: 383..<393, yRange: 46..<80, rgb: (61, 61, 61))  // 槽：稳的第三色
        let bands = UICaptureTests.pageBands(width: frame.width, pillLeft: 23,
                                             pillRight: 381, scale: 1)
        let picked = choose(frame: frame, bands: bands, pillY: 46..<80, pageLuma: 30)
        guard let chosen = picked.chosen else {
            return XCTFail("前导那一格是干净页底，必须选出来：\(picked.report)")
        }
        XCTAssertEqual(chosen.label, "前导")
        XCTAssertEqual(chosen.rgb, UICaptureTests.ArmRGB(r: 30, g: 30, b: 30),
                       "页底必须是那一层自己的 30，不是槽的 61")
        XCTAssertTrue(picked.report.contains("不是页底那一层"), picked.report)
        XCTAssertTrue(picked.report.contains("右侧[档="),
                      "拦住槽的必须是第二道闸（档与全帧页底档差得太远），点名到那一格：\(picked.report)")
        XCTAssertFalse(picked.report.contains("右侧[占比"),
                       "槽的占比本来就达标 ⇒ 若这次还是占比拦下的，那就是地板被改动了：\(picked.report)")
    }

    /// 两档都能用时必须互相印证；印不上就不挑一块算数（只准变严）。
    func testTwoUsableBandsMustCorroborate() {
        var frame = Frame(width: 420, height: 300, fill: (30, 30, 30))
        frame.paint(xRange: 23..<382, yRange: 46..<80, rgb: (70, 70, 70))
        // 右侧窗给一片 (25,25,25)：亮度与页底差 5 < 12 ⇒ 过第二道闸，但众数与左侧不相等。
        frame.paint(xRange: 383..<393, yRange: 46..<80, rgb: (25, 25, 25))
        let bands = UICaptureTests.pageBands(width: frame.width, pillLeft: 23,
                                             pillRight: 381, scale: 1)
        let picked = choose(frame: frame, bands: bands, pillY: 46..<80, pageLuma: 30)
        XCTAssertNil(picked.chosen, "两块窗都过闸却读出不同的底色 ⇒ 至少一块不是页底")
        XCTAssertTrue(picked.report.contains("互不相印"), picked.report)
    }

    // MARK: - ③ 第一道闸（占比地板）不许因为加了第二道闸而松掉

    /// 前导与右侧两块窗里都混进一半字墨（本机第一版 (106,106,106) 的成因形状）
    /// ⇒ 两块都必须被**占比**这一道拦下，理由不许换成第二道闸。
    func testInkContaminatedBandsStillDeclineOnShareFloor() {
        var frame = Frame(width: 420, height: 300, fill: (30, 30, 30))
        frame.paint(xRange: 23..<382, yRange: 46..<80, rgb: (70, 70, 70))
        frame.paint(xRange: 2..<21, yRange: 46..<63, rgb: (0, 0, 0))      // 前导一半是墨
        frame.paint(xRange: 383..<393, yRange: 46..<63, rgb: (0, 0, 0))   // 右侧一半是墨
        let bands = UICaptureTests.pageBands(width: frame.width, pillLeft: 23,
                                             pillRight: 381, scale: 1)
        let picked = choose(frame: frame, bands: bands, pillY: 46..<80, pageLuma: 30)
        XCTAssertNil(picked.chosen)
        XCTAssertTrue(picked.report.contains("前导[占比=50%<60%]"),
                      "一半是墨 ⇒ 众数占比 50，必须由占比这一道闸点名：\(picked.report)")
        XCTAssertTrue(picked.report.contains("右侧[占比=50%<60%]"), picked.report)
    }

    /// 只有一块窗能用（前导被截掉）而右侧确实是页底 ⇒ 选择函数必须还能用它，
    /// 免得本轮的修法把上一版唯一那一格删成"永远没有页底"。
    func testTrailingBandStillUsableWhenItReallyIsPage() {
        var frame = Frame(width: 420, height: 300, fill: (30, 30, 30))
        frame.paint(xRange: 5..<382, yRange: 46..<80, rgb: (70, 70, 70))   // 药丸贴左 ⇒ 没有前导窗
        let bands = UICaptureTests.pageBands(width: frame.width, pillLeft: 5,
                                             pillRight: 381, scale: 1)
        XCTAssertEqual(bands.map { $0.label }, ["右侧"])
        let picked = choose(frame: frame, bands: bands, pillY: 46..<80, pageLuma: 30)
        guard let chosen = picked.chosen else { return XCTFail(picked.report) }
        XCTAssertEqual(chosen.label, "右侧")
        XCTAssertEqual(chosen.rgb, UICaptureTests.ArmRGB(r: 30, g: 30, b: 30))
    }

    // MARK: - ④ 参照臂与亮度公式（本轮把内联那份搬进 ArmRGB.luma）

    /// 两枚系统参照色若逐通道相等，判定必须塌成"两臂不可分"，而不是"落对了"。
    func testIdenticalReferenceArmsAreNotVerdict() {
        let gray = UICaptureTests.ArmRGB(r: 220, g: 220, b: 220)
        let (label, detail) = UICaptureTests.armVerdict(
            obs: gray, page: UICaptureTests.ArmRGB(r: 255, g: 255, b: 255),
            key: gray, nonKey: gray, tol: 2)
        XCTAssertEqual(label, "两臂不可分")
        XCTAssertTrue(detail.contains("参照臂塌成一枚"), detail)
    }

    /// `ArmRGB.luma` 与 `pillRightEdge` 现在共用同一个量：公式被改错时这一格必须红。
    func testLumaFormulaSeparatesGreyFromBlue() {
        XCTAssertEqual(UICaptureTests.ArmRGB(r: 255, g: 255, b: 255).luma, 255)
        XCTAssertEqual(UICaptureTests.ArmRGB(r: 0, g: 0, b: 0).luma, 0)
        XCTAssertEqual(UICaptureTests.ArmRGB(r: 30, g: 30, b: 30).luma, 30, "纯灰的亮度就是它自己")
        XCTAssertGreaterThan(abs(UICaptureTests.ArmRGB(r: 61, g: 61, b: 61).luma
                                 - UICaptureTests.ArmRGB(r: 30, g: 30, b: 30).luma), 12,
                             "runner 上槽与页底那两档，第二道闸必须分得开")
        XCTAssertEqual(UICaptureTests.ArmRGB(r: 0, g: 100, b: 225).chroma, 225,
                       "彩度那把尺没被本轮顺手改坏（key 那一档全靠它）")
    }

    /// 窗太小 ⇒ `armMedian` 只能给 nil：占比在小样本上没有意义。
    func testMedianRefusesSubFloorWindow() {
        let frame = Frame(width: 420, height: 300, fill: (30, 30, 30))
        XCTAssertNil(frame.median(xRange: 0..<4, yRange: 0..<4), "16 像素 < 64 ⇒ nil")
        XCTAssertNotNil(frame.median(xRange: 0..<8, yRange: 0..<8), "64 像素正好到线")
    }
}
