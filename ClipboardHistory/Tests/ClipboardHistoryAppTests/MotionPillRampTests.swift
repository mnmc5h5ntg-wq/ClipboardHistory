// 不覆盖管线：本文件钉的是**斜坡尺的四颗纯尺**（列中位数剖面、轨道范围、洞的切分、
// 会动的洞所在的行带，以及把中心序列归成四格词表的那颗），输入全是合成字节缓冲。
// 管线级判据在捕获卷：`MotionFilmstripTests.testFilterPillRampIsMonotone`
// —— 它走 `Scenario.filterPillSlide()`（`HistorySidebarView` 真视图）、逐帧抓 `cacheDisplay`、
// 再按这些纯函数读每一帧的药丸中心，两臂各判一次；行带与轨道范围都由那一卷自己量出来。
// 合成帧不是产品事实：它只证明这把尺认得那个形状；"这一台到底读到了什么"由上面那条判据自己印。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R323：给全仓唯一那条位移档装**斜坡尺**时，四条已经栽过的路各自有一格证人。
///
/// 本轮自曝的两件事都由这里的格子钉住：
/// ① R322 那条带子是**在另一张帧上目测**的（组件帧 66…92pt），真窗口里胶囊在 49…75pt
///    ⇒ 峰值 0.097 是被低估的读数（改完本机读到 0.277）。行带必须从这一卷量。
/// ② 第一版用"哪些行在变"定位行带，本机直接量到 **126…520pt** —— 换档会重排整个列表，
///    列表那一片逐行都在变，比胶囊那 26pt 大一个数量级。所以定位谓词换成
///    "一颗宽度稳定、位置会走的洞"（`movingHoleRowReading`），第 ⑧ 格就是那个反例。
@MainActor
final class MotionPillRampTests: XCTestCase {

    // MARK: - 合成帧

    /// RGBA8 合成帧（`lumaAt` 读的就是这个布局：每像素 4 字节，取前三字节算 Rec.709 亮度）。
    /// `@MainActor` 不是装饰：这些纯尺住在 `@MainActor` 的 `MotionFilmstripTests` 里。
    @MainActor
    private struct Frame {
        let width: Int
        let height: Int
        var bytesPerRow: Int { width * 4 }
        var bytes: [UInt8]

        init(width: Int, height: Int, grey: Int) {
            self.width = width
            self.height = height
            bytes = [UInt8](repeating: 0, count: width * height * 4)
            paint(xRange: 0..<width, yRange: 0..<height, grey: grey)
        }

        mutating func paint(xRange: Range<Int>, yRange: Range<Int>, grey: Int) {
            for y in yRange {
                for x in xRange {
                    let o = y * bytesPerRow + x * 4
                    let value = UInt8(max(0, min(255, grey)))
                    bytes[o] = value
                    bytes[o + 1] = value
                    bytes[o + 2] = value
                    bytes[o + 3] = 255
                }
            }
        }
    }

    private func profile(_ frame: Frame, yRange: Range<Int>, xRange: Range<Int>? = nil) -> [Double] {
        MotionFilmstripTests.columnMedianProfile(
            pixels: frame.bytes, bytesPerRow: frame.bytesPerRow, yRange: yRange,
            xRange: xRange ?? 0..<frame.width)
    }

    // MARK: - ① 列中位数：字墨不许把洞抬起来

    func testColumnMedianProfileIgnoresMinorityGlyphInk() {
        var frame = Frame(width: 40, height: 9, grey: 52)
        // 第 20 列有 4/9 行是字墨（220），其余是轨道（52）；第 30 列整列都是字墨。
        frame.paint(xRange: 20..<21, yRange: 0..<4, grey: 220)
        frame.paint(xRange: 30..<31, yRange: 0..<9, grey: 220)
        let values = profile(frame, yRange: 0..<9)
        XCTAssertEqual(values.count, 40, "剖面长度必须等于被扫的列数")
        XCTAssertEqual(values[10], 52, accuracy: 0.001, "没人碰的列该是轨道那一档")
        XCTAssertEqual(values[20], 52, accuracy: 0.001,
            "字只占 4/9 行 ⇒ **中位数**必须还落在轨道上。这一格钉的是"
            + "「按列取均值会把药丸内部抬上去」那条本机实测（均值会读到 ~127）。")
        XCTAssertEqual(values[30], 220, accuracy: 0.001,
            "整列都是字墨时中位数就是字 —— 尺不许假装看不见，它只是不许被少数行劫持")
    }

    // MARK: - ② 轨道范围：第一根到最后一根"与页底不同档"的列

    func testTrackExtentSpansFirstToLastDifferentColumn() {
        let values: [Double] = [30, 30, 52, 52, 36, 36, 36, 52, 52, 30]
        let extent = MotionFilmstripTests.trackExtent(profile: values, margin: 30, delta: 8,
                                                      minTrackPixels: 2)
        XCTAssertEqual(extent, 2..<9,
            "范围要含住**首尾两根**不同档的列（含 8 不含 9），中间那颗与页底同档的洞不算边界")
        XCTAssertNil(MotionFilmstripTests.trackExtent(profile: values, margin: 30, delta: 8,
                                                     minTrackPixels: 8),
            "宽度地板要真的拦得住：8 比 2..<9 的宽度大 ⇒ 必须读不出，不许硬给一根")
    }

    // MARK: - ③ 洞 = 与页底同档的那一段（不是亮的那一段）

    func testPillRunIsTheHoleThatReadsLikeThePage() {
        let values: [Double] = [30, 30, 52, 52, 36, 36, 36, 52, 52, 30]
        let run = MotionFilmstripTests.pillRun(profile: values, margin: 30, delta: 8,
                                               extent: 2..<9, minPillPixels: 2)
        XCTAssertNotNil(run, "轨道里有一颗与页底同档的洞 ⇒ 必须读出来")
        XCTAssertEqual(run?.range, 4..<7,
            "洞的下界是 4 不是 2：把「亮的那一段」当成药丸就会读到轨道两端（本机极性 轨道 52 / 药丸 36 / 页底 30）")
        XCTAssertEqual(run?.pillLuma ?? -1, 36, accuracy: 0.001)
        XCTAssertEqual(run?.trackLuma ?? -1, 52, accuracy: 0.001)
    }

    func testPillRunRefusesSubFloorHole() {
        let values: [Double] = [52, 52, 36, 36, 52, 52, 52, 52]
        XCTAssertNil(MotionFilmstripTests.pillRun(profile: values, margin: 30, delta: 8,
                                                  extent: 0..<8, minPillPixels: 3),
            "两颗像素的洞不够地板 ⇒ 必须 nil，不许把噪声当成药丸")
        XCTAssertEqual(MotionFilmstripTests.pillRun(profile: values, margin: 30, delta: 8,
                                                    extent: 0..<8, minPillPixels: 2)?.range,
                       2..<4, "同一颗尺，地板降到 2 就该选中那两颗 —— 拦的是宽度不是极性")
    }

    // MARK: - ④ 行带定位：洞必须**会走**

    private func reading(_ a: Frame, _ b: Frame, y: Int, minMove: Double = 0.1)
        -> (extent: Range<Int>, holeA: Range<Int>, holeB: Range<Int>, margin: Double)? {
        MotionFilmstripTests.movingHoleRowReading(
            pixelsA: a.bytes, pixelsB: b.bytes, bytesPerRow: a.bytesPerRow, y: y,
            xRange: 0..<a.width, marginWindow: 3, delta: 8, minTrackPixels: 5,
            minHolePixels: 3, maxHoleFraction: 0.8, minMoveFraction: minMove)
    }

    func testMovingHoleReadingRejectsAHoleThatStaysPut() {
        var a = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 2..<3, grey: 52)
        a.paint(xRange: 5..<17, yRange: 2..<3, grey: 36)
        let b = a
        XCTAssertNil(reading(a, b, y: 2),
            "两帧同一颗洞停在同一处 ⇒ 这不是「走过」，不许当行带证人（否则静止的一行会被读成位移）")
        XCTAssertEqual(reading(a, b, y: 2, minMove: 0.0)?.holeA, 5..<17,
            "把走量要求降到 0 就该读出那 12 列 —— 拦的是「会不会走」，不是形状")
    }

    func testMovingHoleReadingRejectsARowReplacedWholesale() {
        var a = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 2..<3, grey: 52)
        a.paint(xRange: 5..<17, yRange: 2..<3, grey: 36)
        var b = Frame(width: 40, height: 6, grey: 30)
        // 整行换内容、没有洞：这是"列表重排"那一类的形状。
        b.paint(xRange: 4..<36, yRange: 2..<3, grey: 60)
        XCTAssertNil(reading(a, b, y: 2),
            "末帧整行都是轨道档（读不出洞）⇒ 必须拒绝：换档重排整个列表时，列表每一行都在变，"
            + "但那里没有一颗宽度稳定、位置会走的洞")
    }

    func testMovingHoleBandChoosesThePillRowNotTheListRow() {
        let width = 40, height = 30
        var a = Frame(width: width, height: height, grey: 30)
        var b = Frame(width: width, height: height, grey: 30)
        // 胶囊：第 4…9 行，轨道 52，洞从 5..<17 走到 22..<34。
        a.paint(xRange: 4..<36, yRange: 4..<10, grey: 52)
        a.paint(xRange: 5..<17, yRange: 4..<10, grey: 36)
        b.paint(xRange: 4..<36, yRange: 4..<10, grey: 52)
        b.paint(xRange: 22..<34, yRange: 4..<10, grey: 36)
        // 列表：第 12…29 行整片换内容（比胶囊那 6 行高一整倍）。
        a.paint(xRange: 4..<36, yRange: 12..<30, grey: 90)
        b.paint(xRange: 4..<36, yRange: 12..<30, grey: 60)
        let band = MotionFilmstripTests.movingHoleBand(
            pixelsA: a.bytes, pixelsB: b.bytes, bytesPerRow: a.bytesPerRow, height: height,
            xRange: 0..<width, marginWindow: 3, delta: 8, minTrackPixels: 5, minHolePixels: 3,
            maxHoleFraction: 0.8, minMoveFraction: 0.1, yStride: 1, minRows: 2)
        XCTAssertEqual(band, 4..<10,
            "行带必须是那颗会走的洞所在的 6 行。本机第一版按「哪些行在变」定位，"
            + "量出来是 126…520pt（列表那一片），比胶囊大一个数量级的一段直接赢掉了定位")
        XCTAssertFalse((12..<30).overlaps(band ?? 0..<0),
            "列表那一块不许进带：它整片在变，但没有一颗位置会走的洞")
    }

    // MARK: - ⑤ 三臂相同这条**出口**自己要有正对照（出口最容易变成洗红的水）

    func testArmsAreIdenticalRequiresEveryArmToMatch() {
        let off = [0.1, 0.9, 0.0]
        XCTAssertTrue(MotionFilmstripTests.armsAreIdentical(onA: off, onB: off, off: off),
            "三臂逐帧差数组完全相同 ⇒ 这台机器的胶片里开关不可分（runner 实测就是这个形状）")
        XCTAssertFalse(MotionFilmstripTests.armsAreIdentical(onA: [0.2, 0.9, 0.0], onB: off, off: off),
            "开臂 A 只差第一格就不许说『相同』：放行一条真差异 = 把产品事实洗成绿")
        XCTAssertFalse(MotionFilmstripTests.armsAreIdentical(onA: off, onB: [0.1, 0.9, 0.1], off: off),
            "开臂 B 差最后一格同样不许放行 —— 两遍开臂**都**要与关臂重合才算三臂相同")
    }

    func testArmsAreIdenticalReadsTheSequenceNotTheMultiset() {
        XCTAssertFalse(MotionFilmstripTests.armsAreIdentical(onA: [0.9, 0.1, 0.0],
                                                             onB: [0.9, 0.1, 0.0],
                                                             off: [0.1, 0.9, 0.0]),
            "同样的数换了顺序就是另一卷胶片：这条判据要的是**逐帧**相同，不是总量相同")
    }

    // MARK: - ⑥ 四格词表

    func testRampVerdictWordsAreFourAndDistinct() {
        let tolerance = 5.0
        let monotone = [81.0, 93.0, 124.0, 156.0, 178.0, 195.0, 203.0, 210.0, 219.0]
        XCTAssertEqual(MotionFilmstripTests.rampVerdict(monotone, tolerance: tolerance).label, "单调",
            "本机这一卷的真实形状（临界阻尼：先快后拖尾、不倒退）必须落在『单调』")
        var overshoot = monotone
        overshoot[5] = 230.0
        overshoot[6] = 219.0
        XCTAssertEqual(MotionFilmstripTests.rampVerdict(overshoot, tolerance: tolerance).label, "回头",
            "冲过头再弹回来 = MC-1 禁止的过冲 ⇒ 这一格必须读成『回头』，它是产品事实")
        XCTAssertEqual(MotionFilmstripTests.rampVerdict([100.0, 100.4, 100.2, 100.0],
                                                        tolerance: tolerance).label, "没动",
            "走量小于容差 ⇒ 这是通道看不见，不许写产品没动")
        XCTAssertEqual(MotionFilmstripTests.rampVerdict([100.0, -1, 130.0],
                                                        tolerance: tolerance).label, "无对象",
            "任何一帧读不出中心 ⇒ 后面每一格都没有对象")
        XCTAssertTrue(MotionFilmstripTests.rampVerdict([], tolerance: tolerance).label == "无对象",
            "空的中心序列也是『无对象』，不是『没动』")
    }

    func testRampVerdictBackstepBoundaryMustFlipTheWord() {
        // 只差一个词的两侧：倒退 = 容差 不许读成回头，倒退 = 容差 × 1.2 必须读成回头。
        let tolerance = 5.0
        let atBoundary = [100.0, 120.0, 115.0, 130.0]
        XCTAssertEqual(MotionFilmstripTests.rampVerdict(atBoundary, tolerance: tolerance).label, "单调",
            "倒退恰好等于容差 ⇒ 还在噪声里（`>` 不是 `>=`），把它读成产品过冲就是假红")
        let overBoundary = [100.0, 120.0, 113.9, 130.0]
        XCTAssertEqual(MotionFilmstripTests.rampVerdict(overBoundary, tolerance: tolerance).label, "回头",
            "倒退比容差多一点点就必须换词 —— 两格之间不许有第三种读法")
    }

    func testRampVerdictDetailCarriesTheNumbersItJudgedOn() {
        let detail = MotionFilmstripTests.rampVerdict([81.0, 219.0], tolerance: 5.0).detail
        XCTAssertTrue(detail.contains("位移=138.0"), "结论行要能复查：\(detail)")
        XCTAssertTrue(detail.contains("容差=5.0"), "容差得跟着印出来，不然读者无法判它松紧：\(detail)")
        XCTAssertTrue(detail.contains("帧数=2"), "帧数也要印：\(detail)")
    }

    // MARK: - ⑦ 亮度口径与捕获卷那颗尺同源

    func testLumaUsesTheSameRec709WeightsAsTheCaptureRuler() {
        var frame = Frame(width: 3, height: 1, grey: 0)
        frame.paint(xRange: 0..<1, yRange: 0..<1, grey: 0)
        // (255,0,0) / (0,255,0) / (0,0,255) 三根通道各一列，权重必须是 0.2126 / 0.7152 / 0.0722。
        frame.bytes[0] = 255; frame.bytes[1] = 0; frame.bytes[2] = 0
        frame.bytes[4] = 0; frame.bytes[5] = 255; frame.bytes[6] = 0
        frame.bytes[8] = 0; frame.bytes[9] = 0; frame.bytes[10] = 255
        let red = MotionFilmstripTests.lumaAt(frame.bytes, frame.bytesPerRow, 0, 0)
        let green = MotionFilmstripTests.lumaAt(frame.bytes, frame.bytesPerRow, 1, 0)
        let blue = MotionFilmstripTests.lumaAt(frame.bytes, frame.bytesPerRow, 2, 0)
        XCTAssertGreaterThan(green, red, "绿权重要压过红：系数写反这里就红")
        XCTAssertGreaterThan(red, blue, "红权重要压过蓝")
        XCTAssertEqual(red + green + blue, 255.0, accuracy: 0.01,
            "三根权重之和必须是 1（与 UICaptureHarness.ArmRGB.luma 同一组系数，两把尺不许各抄一份）")
    }
}
