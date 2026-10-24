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

    /// 锚是"两帧之间没动的那一档"（轨道），不是"页底那一档"：
    /// 暗档里药丸 36 恰好与页底 30 同档（R323 据此写死了锚），亮档里药丸 255 比轨道 230 **更亮** ——
    /// 同一句"药丸与页底同档"在两个时刻一个是真的一个是假的（本机 09:07 复跑就是后者）。
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

    /// 亮档形状的**反向**证人（R324）：本机自动外观转到亮档之后，同一卷读到的三档是
    /// 页底 230 / 轨道 230 / 药丸 233（本轮临时逐列转储读出来的；那把临时尺用完就撤了，
    /// 所以这里复现的是**那个形状**，不是那天的绝对数）。按这把尺的 `delta=8`：
    /// 轨道与页底同档 ⇒ `trackExtent` 找不到轨道 ⇒ 一个候选都没有。
    /// 这一格存在的理由是那条钉色档的前提不是审美：亮档里这把尺**没有对象**，
    /// 于是"胶囊走过没有"会被读成"看不见"，而那既是错的结论也是错的归因。
    func testBandLocatorHasNoObjectInTheMeasuredLightAppearance() {
        let width = 300, height = 30
        var a = Frame(width: width, height: height, grey: 230)
        var b = Frame(width: width, height: height, grey: 230)
        a.paint(xRange: 14..<286, yRange: 4..<20, grey: 230)
        b.paint(xRange: 14..<286, yRange: 4..<20, grey: 230)
        a.paint(xRange: 16..<146, yRange: 4..<20, grey: 233)
        b.paint(xRange: 154..<286, yRange: 4..<20, grey: 233)
        let got = band(a, b, width: width, height: height)
        XCTAssertNil(got.band, "亮档那三档只差 3 级 ⇒ 这把尺必须说'没有对象'，"
            + "不许硬框出一条带子替它作证：" + got.report)
        XCTAssertTrue(got.report.contains("候选行=0"),
            "报告必须点名'一个候选都没有'（否则判据只能干说一句找不到）：" + got.report)
    }

    // MARK: - ④ 行带定位：洞要**会走**，还要**长得像那颗胶囊**

    /// 三道结构闸 + 三道形状闸的参数表（与判据侧 `measuredMovingHoleBand` 同一组数）。
    /// 写两遍就会漂：R38 那一族（同一个阈值不许有两个权威）—— 所以这里也走同一组常量。
    private func reading(_ a: Frame, _ b: Frame, y: Int, minMove: Double = 0.1,
                         minHole: Double = 0.25, edgeFlush: Double = 0.04,
                         widthTol: Double = 0.15)
        -> (extent: Range<Int>, holeA: Range<Int>, holeB: Range<Int>, margin: Double, gate: String)? {
        MotionFilmstripTests.movingHoleRowReading(
            pixelsA: a.bytes, pixelsB: b.bytes, bytesPerRow: a.bytesPerRow, y: y,
            xRange: 0..<a.width, marginWindow: 3, delta: 8, minTrackPixels: 5,
            minHolePixels: 3, maxHoleFraction: 0.8, minMoveFraction: minMove,
            minHoleFraction: minHole, edgeFlushFraction: edgeFlush, widthToleranceFraction: widthTol)
    }

    private func band(_ a: Frame, _ b: Frame, width: Int, height: Int, minRows: Int = 2)
        -> (band: Range<Int>?, report: String) {
        MotionFilmstripTests.movingHoleBand(
            pixelsA: a.bytes, pixelsB: b.bytes, bytesPerRow: a.bytesPerRow, height: height,
            xRange: 0..<width, marginWindow: 3, delta: 8, minTrackPixels: 5, minHolePixels: 3,
            maxHoleFraction: 0.8, minMoveFraction: 0.1, minHoleFraction: 0.25,
            edgeFlushFraction: 0.04, widthToleranceFraction: 0.15, yStride: 1, minRows: minRows)
    }

    /// 合成一张"胶囊行"：轨道 4..<36，洞从**贴左端**走到**贴右端**（静止态药丸占满一整段）。
    private func pillFrames() -> (a: Frame, b: Frame) {
        var a = Frame(width: 40, height: 6, grey: 30)
        var b = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        a.paint(xRange: 4..<16, yRange: 0..<6, grey: 36)
        b.paint(xRange: 24..<36, yRange: 0..<6, grey: 36)
        return (a, b)
    }

    func testMovingHoleReadingRejectsAHoleThatStaysPut() {
        let pill = pillFrames()
        XCTAssertNil(reading(pill.a, pill.a, y: 2),
            "两帧同一颗洞停在同一处 ⇒ 这不是「走过」，不许当行带证人（否则静止的一行会被读成位移）。"
            + "注意它还有一层意思：两帧不动时亮区的并集就是轨道那半段，洞整个落在并集之外 ⇒ 连候选都不是")
        let both = reading(pill.a, pill.b, y: 2)
        XCTAssertEqual(both?.gate, "过", "正对照：贴端走过、宽度稳定的那颗洞必须被判成候选（六闸全过）")
        XCTAssertEqual(both?.holeA, 4..<16, "首帧的洞必须读成贴左端那 12 列")
        XCTAssertEqual(both?.holeB, 24..<36, "末帧的洞必须读成贴右端那 12 列")
    }

    func testMovingHoleReadingRejectsARowReplacedWholesale() {
        let (a, _) = pillFrames()
        var b = Frame(width: 40, height: 6, grey: 30)
        // 整行换内容、没有洞：这是"列表重排"那一类的形状。
        b.paint(xRange: 4..<36, yRange: 2..<3, grey: 60)
        XCTAssertNil(reading(a, b, y: 2),
            "末帧整行都是轨道档（读不出洞）⇒ 必须拒绝：换档重排整个列表时，列表每一行都在变，"
            + "但那里没有一颗宽度稳定、位置会走的洞")
    }

    /// R324 的主证：runner 那一跑找到的就是这种"走在中间"的洞（列表里的一行）。
    func testMovingHoleReadingRejectsAHoleThatWandersInTheMiddle() {
        var a = Frame(width: 40, height: 6, grey: 30)
        var b = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        // 洞在中间走：10..<22 → 18..<30 —— 两端都不贴（静止的胶囊必然占满一整段）。
        a.paint(xRange: 10..<22, yRange: 0..<6, grey: 36)
        b.paint(xRange: 18..<30, yRange: 0..<6, grey: 36)
        XCTAssertEqual(reading(a, b, y: 2)?.gate, "不贴两端",
            "结构闸全过、形状闸必须点名 —— 这一格就是 runner 上那朵假红的形状（RUN=40032708615）")
    }

    func testMovingHoleReadingRejectsAStretchingHole() {
        var a = Frame(width: 40, height: 6, grey: 30)
        var b = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        a.paint(xRange: 4..<16, yRange: 0..<6, grey: 36)
        b.paint(xRange: 26..<36, yRange: 0..<6, grey: 36)   // 10 列 vs 12 列：刚体不许拉长
        XCTAssertEqual(reading(a, b, y: 2)?.gate, "宽度不稳",
            "两帧里洞的宽度差两列（>15%）⇒ 那不是同一颗胶囊在走，是两处不同的东西各自成了洞")
        XCTAssertEqual(reading(a, b, y: 2, widthTol: 0.6)?.gate, "过",
            "把宽度容差放宽到 60% 就该放行 —— 每道闸只管自己那一条，不许互相顶替")
    }

    func testMovingHoleReadingRejectsASlitTooNarrowForASegment() {
        var a = Frame(width: 40, height: 6, grey: 30)
        var b = Frame(width: 40, height: 6, grey: 30)
        a.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        a.paint(xRange: 4..<8, yRange: 0..<6, grey: 36)
        b.paint(xRange: 32..<36, yRange: 0..<6, grey: 36)   // 4/32 = 12.5%：贴两端但太窄
        XCTAssertEqual(reading(a, b, y: 2)?.gate, "洞太窄",
            "字缝也能贴边 —— 所以「至少一段之宽」这一道不能省")
    }

    func testMovingHoleBandChoosesThePillRowNotTheListRow() {
        let width = 40, height = 30
        var a = Frame(width: width, height: height, grey: 30)
        var b = Frame(width: width, height: height, grey: 30)
        // 胶囊：第 0…5 行，轨道 52，洞从**贴左端** 4..<16 走到**贴右端** 24..<36。
        a.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<6, grey: 52)
        a.paint(xRange: 4..<16, yRange: 0..<6, grey: 36)
        b.paint(xRange: 24..<36, yRange: 0..<6, grey: 36)
        // 列表行（runner 那一跑的真实形状）：底色 90 两帧都不动，底上一块内容从左中走到右中。
        a.paint(xRange: 4..<36, yRange: 12..<30, grey: 90)
        b.paint(xRange: 4..<36, yRange: 12..<30, grey: 90)
        a.paint(xRange: 10..<22, yRange: 12..<18, grey: 30)
        b.paint(xRange: 18..<30, yRange: 12..<18, grey: 30)
        let got = band(a, b, width: width, height: height)
        XCTAssertEqual(got.band, 0..<6,
            "行带必须是那颗贴端走过的洞所在的 6 行。本机第一版按「哪些行在变」定位，"
            + "量出来是 126…520pt（列表那一片），比胶囊大一个数量级的一段直接赢掉了定位")
        XCTAssertTrue(got.report.contains("不贴两端"),
            "被拒的候选要能被点名（runner 那一跑就是缺这个才只留下一朵红）：\(got.report)")
    }

    func testMovingHoleBandDeclinesWithAReportInsteadOfSilence() {
        var a = Frame(width: 40, height: 12, grey: 30)
        var b = Frame(width: 40, height: 12, grey: 30)
        a.paint(xRange: 4..<36, yRange: 0..<12, grey: 52)
        b.paint(xRange: 4..<36, yRange: 0..<12, grey: 52)
        a.paint(xRange: 10..<22, yRange: 0..<12, grey: 36)
        b.paint(xRange: 18..<30, yRange: 0..<12, grey: 36)
        let got = band(a, b, width: 40, height: 12)
        XCTAssertNil(got.band, "整幅都是那颗「走在中间」的洞 ⇒ 一段都不能取")
        XCTAssertTrue(got.report.contains("候选段=y0..12px"),
            "报告要给出被拒的段在哪：\(got.report)")
        XCTAssertTrue(got.report.contains("取用=无"), "取用了什么必须一起印：\(got.report)")
    }

    /// 2× 尺度下的正对照：把本机量出来的那套数（页底 30 / 轨道 52 / 药丸 36、
    /// 轨道 28..<572px、药丸 32..<292 → 308..<572、行带 102..<150）原样合成一遍，
    /// 用**判据侧同一组参数**跑一次 —— 这一格红就说明尺自己坏了，而不是那台机器的画面变了。
    func testBandLocatorFindsTheLocalScalePill() {
        let width = 600, height = 200
        var a = Frame(width: width, height: height, grey: 30)
        var b = Frame(width: width, height: height, grey: 30)
        a.paint(xRange: 28..<572, yRange: 102..<150, grey: 52)
        b.paint(xRange: 28..<572, yRange: 102..<150, grey: 52)
        a.paint(xRange: 32..<292, yRange: 102..<150, grey: 36)
        b.paint(xRange: 308..<572, yRange: 102..<150, grey: 36)
        let got = MotionFilmstripTests.movingHoleBand(
            pixelsA: a.bytes, pixelsB: b.bytes, bytesPerRow: width * 4, height: height,
            xRange: 2..<598, marginWindow: 12, delta: 8, minTrackPixels: 40, minHolePixels: 24,
            maxHoleFraction: 0.8, minMoveFraction: 0.1, minHoleFraction: 0.25,
            edgeFlushFraction: 0.04, widthToleranceFraction: 0.15, yStride: 2, minRows: 12)
        XCTAssertEqual(got.band, 102..<150, "本机尺度下那颗贴端走过的洞必须被取用：\(got.report)")
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

    // MARK: - 出口谓词与退化采样（R325 / D-311）：两处"只印不判"各配一颗证人

    /// 出口的谓词必须钉在**判据自己用的那两个数**上（过渡帧数、峰值）。
    /// runner 那一跑（RUN=40053805112）是三臂 1/1/1 帧、峰值 0.925 全等，而数组别处各不相同 ——
    /// 上一版要求"逐字节相同"，于是出口没响、红落在产品断言上。这一格就是那个形状的反例。
    func testArmsIndistinguishableUsesTheNumbersTheJudgeActuallyCompares() {
        XCTAssertTrue(MotionFilmstripTests.armsIndistinguishable(spanA: 1, spanB: 1, spanOff: 1,
                                                                 peakA: 0.925, peakB: 0.925,
                                                                 peakOff: 0.925),
            "runner 那一跑的形状：三臂的帧数与峰值全等 ⇒ 必须判成没有对照物（数组别处不同不算有对照物）")
        XCTAssertFalse(MotionFilmstripTests.armsIndistinguishable(spanA: 3, spanB: 3, spanOff: 1,
                                                                   peakA: 0.266, peakB: 0.266,
                                                                   peakOff: 0.949),
            "本机那一跑的形状：开臂 3 帧对关臂 1 帧 ⇒ 开关分得开，这条判据在真判，不许被出口放行")
        XCTAssertFalse(MotionFilmstripTests.armsIndistinguishable(spanA: 1, spanB: 1, spanOff: 1,
                                                                   peakA: 0.925, peakB: 0.925,
                                                                   peakOff: 0.900),
            "峰值差 0.025 就是**有**对照物：谓词不许带容差，否则把'差一点'洗成'全等'")
        XCTAssertFalse(MotionFilmstripTests.armsIndistinguishable(spanA: 1, spanB: 2, spanOff: 1,
                                                                   peakA: 0.925, peakB: 0.925,
                                                                   peakOff: 0.925),
            "同一台机器两遍开臂自己都不一致 ⇒ 那不是'开关不可分'，是通道在抖，得让它红")
    }

    /// 词表默认输入里至少有一颗中间样本；一步跳变不许发"走得平稳"的证。
    func testIntermediateCountRefusesToCertifyATeleport() {
        XCTAssertEqual(0, MotionFilmstripTests.intermediateCount([80.0, 219.0, 219.0, 219.0],
                                                                 tolerance: 5.5),
            "runner 那一卷的序列：首帧之后直接是末态 ⇒ 中间样本必须是 0（斜坡无从判）")
        let ramp: [Double] = [80.5, 93.0, 124.5, 158.0, 178.5, 193.0, 202.5, 209.0, 212.5, 219.0]
        XCTAssertGreaterThan(MotionFilmstripTests.intermediateCount(ramp, tolerance: 5.5), 3,
            "本机那一卷的序列：中间态必须数得出来，否则本机也走不出'单调'这张证")
        XCTAssertEqual(MotionFilmstripTests.intermediateCount([219.0, 158.0, 80.0], tolerance: 5.5), 1,
            "方向无关：往左走的斜坡同样有中间样本（端点按容差让开）")
        XCTAssertEqual(0, MotionFilmstripTests.intermediateCount([100.0, 100.0, 100.0], tolerance: 5.5),
            "首末同档（没动）⇒ 中间样本 0，不许因为'都在区间内'就数出东西来")
        XCTAssertEqual(0, MotionFilmstripTests.intermediateCount([], tolerance: 5.5),
            "空序列 ⇒ 0，不是崩溃也不是 -1")
    }

    // MARK: - 缺席点名器的正对照（R324）：先证明它数得对，才有资格报「没钉的有几颗」

    /// `MotionFilmstripTests.scenarioPinCensus` 读的是**自己那本文件**，所以它没有第二只眼。
    /// 这一格就是那只第二只眼：喂一段合成源码，三颗工厂一颗钉了、两颗没钉，
    /// 外加一条注释里也写着 `appearance:` 与一颗注释掉的工厂 —— 那两条都不许进名单。
    /// 没有这一格，本机那句"没钉=N 颗"就只是又一次"我又敲错了一扇门"。
    ///
    /// 两条注释各拦一种坏法，别混成一条：注释里那颗 `static func … -> Scenario {` 是被
    /// **签名样式**认不出的（行首是 `//`），所以它不进名单与剥注释无关；而正文里那条写着
    /// `appearance:` 的注释**只有靠剥注释**才不会把没钉的 `plainOne` 说成钉了 —— M936 那一刀打的正是后者。
    func testScenarioPinCensusSeparatesPinnedFromUnpinnedAndSkipsComments() {
        let code = [
            "struct Holder {",
            "    // static func commentedOut() -> Scenario {   ← 注释里的一颗，被签名样式认不出",
            "        static func pinnedOne() -> Scenario {",
            "            Scenario(name: \"a\", appearance: .darkAqua) { _ in }",
            "        }",
            "        static func plainOne() -> Scenario {",
            "            // 这一行注释里写着 appearance: ，它不算钉了（剥注释那一格就红在这里）",
            "            Scenario(name: \"b\") { _ in }",
            "        }",
            "        static func deepOne() -> Scenario {",
            "            Scenario(name: \"c\",",
            "                     root: { store in AnyView(Text(\"x\")) }) { _ in }",
            "        }",
            "    static func otherShape() -> [Scenario] { [] }",
            "}"
        ].joined(separator: "\n")
        let census = MotionFilmstripTests.scenarioPinCensus(code: code)
        XCTAssertEqual(["pinnedOne"], census.pinned.sorted(),
            "钉了色档的名单读成了 \(census.pinned) ⇒ 要么把注释里的 `appearance:` 数进来了，"
            + "要么把真钉了的认成了没钉（两条都会让本机那句『没钉=N 颗』是假的）")
        XCTAssertEqual(["deepOne", "plainOne"], census.unpinned.sorted(),
            "没钉的名单读成了 \(census.unpinned) ⇒ 点名器漏认工厂（注释里那颗"
            + " `commentedOut` 与 `-> [Scenario]` 那种形状都不该进来）")
    }

    // MARK: - 色档依赖分类器（R325 立 / R326 换统计量）：四格词表、两条分界、通道无关性都要有牙

    /// R325 / BACKLOG 383 的探针把 12 颗场景归成 同 / 漂 / 敏感 / 换对象 四格。
    /// 探针自己活在真机跑里，这四格的分界就得由这一格钉住 ——
    /// 否则"漂"与"敏感"是哪两条线、"换对象"为什么优先，都只是注释里的分类法（R146 那一族）。
    ///
    /// R326 换的是**收哪几个数**（首末面积 + 动过并集 + 首末墨量，取较大的相对差），阈值一个字没动，
    /// 所以这些格子改的是参数而不是形状：5% 那条线仍然"等于算同、超过算漂"。
    func testAppearanceDependenceVerdictWordsAndBoundaries() {
        // 只是打包参数，不做任何判断：判定仍然只可能来自产品侧那颗纯函数。
        func verdict(endpoint: (Double, Double) = (0.10, 0.10),
                     union: (Double, Double) = (0.10, 0.10),
                     ink: (Double, Double) = (0.10, 0.10),
                     changed: (Bool, Bool) = (true, true)) -> String {
            MotionFilmstripTests.appearanceDependenceVerdict(
                endpointDark: endpoint.0, endpointLight: endpoint.1,
                unionDark: union.0, unionLight: union.1,
                inkDark: ink.0, inkLight: ink.1,
                changedDark: changed.0, changedLight: changed.1)
        }
        // ① 换对象优先于相对差：两臂读数**完全相同**，但一档看得见变化、另一档看不见 ⇒ 前提翻了脸。
        XCTAssertEqual("换对象", verdict(changed: (true, false)),
                       "相对差 0% 就把'前提翻脸'读成'同' ⇒ 那正是 R324 在亮档里撞上的形状")
        // ② 5% 那条线：等于 5% 还算同，超过才算漂（分界要能被钉在某一侧，不许两头都算）。
        XCTAssertEqual("同", verdict(endpoint: (0.100, 0.105), union: (0.100, 0.105),
                                     ink: (0.100, 0.105)),
                       "相对差正好 5% ⇒ 不许升成漂（升了就等于把地板往下挪）")
        XCTAssertEqual("漂", verdict(endpoint: (0.100, 0.106), union: (0.100, 0.106),
                                     ink: (0.100, 0.106)),
                       "相对差 5.7% ⇒ 必须点名，否则'漂'那一格永远读不出来")
        // ③ 25% 那条线：同上，两条线各自可钉。三颗都给同一个数 —— 判定取较大者，
        // 任何一颗单独过线都会把这一格抬到另一侧，所以这格要问的是"这条线本身在哪一侧"。
        XCTAssertEqual("漂", verdict(endpoint: (0.20, 0.25), union: (0.20, 0.25), ink: (0.20, 0.25)),
                       "相对差 20%（0.05/0.25）⇒ 仍是漂，不许提前升成敏感")
        XCTAssertEqual("敏感", verdict(endpoint: (0.20, 0.28), union: (0.20, 0.28), ink: (0.20, 0.28)),
                       "相对差 >25% ⇒ 这条判据的读数随色档走，必须与'漂'分开（修法相反：一个要钉，一个只要登记）")
        // ④ 两臂都是 0（空白对照那类）不许算出 NaN 或除零。
        XCTAssertEqual("同", verdict(endpoint: (0, 0), union: (0, 0), ink: (0, 0),
                                     changed: (false, false)),
                       "两臂都读不到变化 ⇒ 是'同'（空白对照），不是 NaN，也不是'换对象'")
        // ⑤ 取较大者这一半：一颗看不见、另一颗看得见时，不许因为"用的那颗恰好是 0"就判同。
        XCTAssertEqual("敏感", verdict(endpoint: (0.100, 0.101), union: (0.100, 0.167)),
                       "首末面积只有 1% 但并集差 40% ⇒ 取 min 或只读面积都会把它洗成'同'")
        // ⑥ 墨量那一颗必须**自己**就能把判定抬起来：面积与并集全等，只有"动了多少级"不同。
        // 这一格是本轮的自证：少了它，"换成通道无关统计量"就等于把判据换窄到它恰好看不见的那一半。
        XCTAssertEqual("敏感", verdict(ink: (0.6667, 0.4000)),
                       "面积/并集两臂全等而墨量差 40% ⇒ 只读像素集合的尺看不见'同样的动、不同的深浅'，"
                           + "而这正是逐行电平尺的对象")
        // ⑦ 三颗都压在线上但都没过 ⇒ 同。这一格是为了钉"取较大者"不会自己变成加分项：
        // 第一版这里给的是 union=(0.20, 0.215)（6.98%），判据当场回给我"漂" —— 那是它对，我错。
        XCTAssertEqual("同", verdict(endpoint: (0.20, 0.21), union: (0.20, 0.21), ink: (0.30, 0.315)))
    }

    /// R326 的核心证词：**同一份过渡，粗采样与细采样必须在三颗通道无关的尺上给出同一个判定，
    /// 而在峰值那颗尺上给出不同判定。** 两个方向都要证，缺一个都不算：
    /// 只证"首末差不随采样变"，可能那把尺本来就什么都读不出来（分母坏、恒为 0）；
    /// 只证"峰值随采样变"，是给要被推翻的旧口径作证，不是给修法作证。
    func testAppearanceStatisticsSurviveASamplingChange() {
        // 同一件事实：画面从左到右亮满 70 列。粗的那卷 5 步跳完，细的那卷 11 步亮完。
        let coarse = MotionFilmstripTests.syntheticRevealFilm(revealedColumns: [0, 20, 35, 50, 70])
        let fine = MotionFilmstripTests.syntheticRevealFilm(
            revealedColumns: [0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70])
        // ① 通道无关的三颗：必须各读满（面积 1.0 / 墨量同一值），且两卷相同。
        XCTAssertEqual(1.0, MotionFilmstripTests.endpointChangedFraction(coarse), accuracy: 0.0001,
            "首末面积读不到满幅（0→70 列亮满）⇒ 这颗尺瞎了，它给的'同'不能作数")
        XCTAssertEqual(1.0, MotionFilmstripTests.endpointChangedFraction(fine), accuracy: 0.0001,
            "细采样那卷的首末面积与粗采样不同 ⇒ 首末面积并不像我说的那样与采样次数无关，本轮的修法前提没了")
        XCTAssertEqual(1.0, MotionFilmstripTests.everChangedFraction(coarse), accuracy: 0.0001,
            "并集读不到满幅 ⇒ 同样的瞎尺问题")
        XCTAssertEqual(1.0, MotionFilmstripTests.everChangedFraction(fine), accuracy: 0.0001,
            "两卷的并集不同 ⇒ 并集也随采样粒度走了")
        XCTAssertEqual(MotionFilmstripTests.endpointInkDifference(coarse),
                       MotionFilmstripTests.endpointInkDifference(fine), accuracy: 0.0001,
                       "墨量差在两卷之间不同 ⇒ 它也读采样通道，那三颗里就有两颗不成立")
        XCTAssertGreaterThan(MotionFilmstripTests.endpointInkDifference(coarse), 0.5,
            "墨量差读不到 0.5 以上（0→200 级应该接近 0.78）⇒ 这颗尺也瞎了")
        // ② 峰值那颗：粗采样每步亮得多，峰值必须**明显更大** —— 这就是 confound 本身。
        let peakCoarse = MotionFilmstripTests.peakChangedFraction(coarse)
        let peakFine = MotionFilmstripTests.peakChangedFraction(fine)
        XCTAssertGreaterThan(peakCoarse, peakFine * 2.0,
            "粗采样峰值 \(peakCoarse) 没有明显大于细采样 \(peakFine) ⇒ 这台机器上造不出粒度差，"
                + "下面的对照是空的（不许据此说峰值没问题）")
        // ②b 前提臂也要在这对合成帧上成立：否则"换对象"那一格只是我编的布尔值。
        XCTAssertTrue(MotionFilmstripTests.premisePictureChanged(coarse),
                      "粗采样那卷 premise 读不到'画面变了' ⇒ 夹具没动，证人不能替任何人说话")
        XCTAssertTrue(MotionFilmstripTests.premisePictureChanged(fine),
                      "细采样那卷 premise 读不到'画面变了' ⇒ 同上")
        // ③ 两口径各自的判定：峰值把同一件事判成敏感，通道无关口径判成同。
        XCTAssertEqual("敏感", MotionFilmstripTests.peakVerdict(peakDark: peakCoarse, peakLight: peakFine,
                                                                changedDark: true, changedLight: true),
            "旧口径在这对合成帧上都不肯翻脸 ⇒ 我没换统计量，换的是一句没有反例的说法")
        XCTAssertEqual("同", MotionFilmstripTests.appearanceDependenceVerdict(
            endpointDark: MotionFilmstripTests.endpointChangedFraction(coarse),
            endpointLight: MotionFilmstripTests.endpointChangedFraction(fine),
            unionDark: MotionFilmstripTests.everChangedFraction(coarse),
            unionLight: MotionFilmstripTests.everChangedFraction(fine),
            inkDark: MotionFilmstripTests.endpointInkDifference(coarse),
            inkLight: MotionFilmstripTests.endpointInkDifference(fine),
            changedDark: true, changedLight: true),
            "换了口径之后这对合成帧还判得出差别 ⇒ 新尺仍然在读采样粒度，本轮的修法没成立")
    }

    /// 面积那两颗对"动了多少级"是**盲**的，而墨量那一颗必须自己能把判定抬起来。
    ///
    /// 这一格是给"别把判据换窄"装的牙：R326 差点只留首末面积 + 并集就交差，而那两颗
    /// 只看像素**集合** —— 同一批像素在暗档里动 200 级、在亮档里动 120 级，它们读出来一模一样，
    /// 于是"这条判据的读数随色档走"这句话恰好被换成了它看不见的那一半（逐行电平尺量的就是这个）。
    func testEndpointAreaIsBlindToInkMagnitudeButTheVerdictIsNot() {
        let strong = MotionFilmstripTests.syntheticRevealFilm(revealedColumns: [0, 70], ink: 200)
        let weak = MotionFilmstripTests.syntheticRevealFilm(revealedColumns: [0, 70], ink: 120)
        // ① 两颗面积尺：动的像素集合完全相同 ⇒ 必须读成相等（这就是它们的盲区，要能被拍下来）。
        XCTAssertEqual(MotionFilmstripTests.endpointChangedFraction(strong),
                       MotionFilmstripTests.endpointChangedFraction(weak), accuracy: 0.0001,
                       "面积尺分得开'深浅'了？那本轮登记的盲区是假的，得重看这三颗的分工")
        XCTAssertEqual(MotionFilmstripTests.everChangedFraction(strong),
                       MotionFilmstripTests.everChangedFraction(weak), accuracy: 0.0001,
                       "并集分得开深浅 ⇒ 同上")
        // ② 墨量那颗必须读出 40% 的差别（200 对 120）。
        let inkStrong = MotionFilmstripTests.endpointInkDifference(strong)
        let inkWeak = MotionFilmstripTests.endpointInkDifference(weak)
        XCTAssertGreaterThan(inkStrong, inkWeak, "墨量差读不出深浅 ⇒ 这颗尺只是面积尺的别名")
        XCTAssertEqual(0.4, MotionFilmstripTests.relativeDifference(inkStrong, inkWeak), accuracy: 0.01,
                       "200 级与 120 级的相对差应该接近 40%，实测 "
                           + String(format: "%.3f", MotionFilmstripTests.relativeDifference(inkStrong, inkWeak)))
        // ③ 判定：面积与并集全等、只有墨量差 40% ⇒ 敏感。少了②那一颗，这里会得到"同"。
        XCTAssertEqual("敏感", MotionFilmstripTests.appearanceDependenceVerdict(
            endpointDark: MotionFilmstripTests.endpointChangedFraction(strong),
            endpointLight: MotionFilmstripTests.endpointChangedFraction(weak),
            unionDark: MotionFilmstripTests.everChangedFraction(strong),
            unionLight: MotionFilmstripTests.everChangedFraction(weak),
            inkDark: inkStrong, inkLight: inkWeak,
            changedDark: true, changedLight: true),
            "面积全等而墨量差 40% 却判成'同' ⇒ 本轮的修法是拿窄的尺换掉旧的尺，不是修它")
    }

    /// 两臂采样粒度的容差（R326）：这条线是本轮**被红逼出来的**，不是设计出来的 ——
    /// 第一版把它写成"帧数必须相等"，`blank` 那颗粒刻当场红在 暗 27 / 亮 28 上，
    /// 而帧数是墙上时钟决定的，同一进程里差 1 帧是常态。
    /// 放行抖动、拦住"一臂塌了"，两半都要有格子。
    func testSamplingComparableToleranceAdmitsJitterButNotACollapsedArm() {
        XCTAssertTrue(MotionFilmstripTests.samplingComparable(27, 28),
                      "差 1 帧就判不可比 ⇒ 这条闸在拦时钟抖动，不是在拦坏通道（本机实测的正是 27/28）")
        XCTAssertTrue(MotionFilmstripTests.samplingComparable(7, 8),
                      "小样本的 1 帧豁免也要成立：7/8 的相对差 12.5% 本来就够，别让它靠四舍五入过线")
        XCTAssertTrue(MotionFilmstripTests.samplingComparable(20, 25),
                      "20 对 25（20%）应当可比 ⇒ 容差不该窄到只放行 1 帧，那样一整批场景会被误判成没对照物")
        XCTAssertFalse(MotionFilmstripTests.samplingComparable(30, 3),
                       "一臂只剩 3 帧（10%）还说'可比' ⇒ 这格等于没有：那条胶片根本没拍到过程")
        XCTAssertFalse(MotionFilmstripTests.samplingComparable(30, 0),
                       "一臂 0 帧必须拦住")
        XCTAssertTrue(MotionFilmstripTests.samplingComparable(1, 1),
                      "1/1 这种退化输入不许判成不可比（不许把它当成塌了）")
    }

    /// 并集与首末差**必须共用同一套分母**（同一条 stride-7 采样、同一个 band 映射）。
    ///
    /// 为什么单独钉：两臂取较大相对差的前提是"这两个数可比"。并集那份循环是我照着 `axisPair`
    /// 手抄的第二份采样几何 —— 手抄的几何会漂（BACKLOG 80 那一族就是映射漂），而它一漂，
    /// "首末差读整窗、并集读半窗"这种数就会安静地混进同一格里。
    /// 两帧的胶片是这两颗尺的**同一点**：那时两个数必须逐格相等。
    func testEverChangedUsesTheSameDenominatorAsChangedFraction() {
        // ① 整窗：两帧的胶片 ⇒ 并集 = 首末差。
        let half = MotionFilmstripTests.syntheticRevealFilm(revealedColumns: [0, 35])
        XCTAssertEqual(MotionFilmstripTests.endpointChangedFraction(half),
                       MotionFilmstripTests.everChangedFraction(half), accuracy: 0.0001,
                       "两帧的胶片上并集与首末差不等 ⇒ 两颗尺的分母不是同一套，取较大者没有意义")
        XCTAssertEqual(0.5, MotionFilmstripTests.everChangedFraction(half), accuracy: 0.0001,
                       "亮满一半列应该读 0.5（70 宽、stride 7 ⇒ 10 个采样列）实测 "
                           + "\(MotionFilmstripTests.everChangedFraction(half)) ⇒ 分母不是采样像素数")
        // ② 带内：带子盖住**亮了的那半边**（x 0…0.4 ⇒ 采样列 0,7,14,21 全在亮区内）⇒ 两个数都该读满。
        let leftBand = CGRect(x: 0.0, y: 0.0, width: 0.4, height: 1.0)
        XCTAssertEqual(MotionFilmstripTests.endpointChangedFraction(half, band: leftBand),
                       MotionFilmstripTests.everChangedFraction(half, band: leftBand), accuracy: 0.0001,
                       "带内两个数不等 ⇒ 并集那份循环的 band 映射与 axisPair 不是同一套")
        XCTAssertGreaterThan(MotionFilmstripTests.everChangedFraction(half, band: leftBand), 0.9,
                             "带子盖住亮着的那半边却读不到满幅 ⇒ 带映射朝向漂了（BACKLOG 80 那一族）")
        // ③ 带子挪到**没亮的那半边** ⇒ 两个数都该读 0（正对照：同一颗尺要能分出两侧）。
        let rightBand = CGRect(x: 0.6, y: 0.0, width: 0.4, height: 1.0)
        XCTAssertEqual(0.0, MotionFilmstripTests.everChangedFraction(half, band: rightBand), accuracy: 0.0001,
                       "没亮的那半边读出了非 0 ⇒ 这两颗尺里的带子不是同一个位置")
        XCTAssertEqual(0.0, MotionFilmstripTests.endpointChangedFraction(half, band: rightBand), accuracy: 0.0001,
                       "首末差在没亮的那半边读出非 0 ⇒ 带映射两侧都不可信")
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
