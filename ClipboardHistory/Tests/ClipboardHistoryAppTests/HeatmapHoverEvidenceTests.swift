import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R45 · 热图悬停那一圈的**表达**那一半（U-71 / D-104）。
///
/// 这一条判据存在的全部理由是一句**从没对过账的注释**：
/// `VisualHeat.hoverStroke` 那里写着「比发丝线重一档：它要在已经有色块的表面上把自己读出来，
/// 发丝线在深色格子上会消失」。这句话到 R45 之前没有任何证据 —— 因为
/// `hovered` 是宿主的 `@State`，而「合成 hover」的三条路 R14 实测全部走不通
/// （CGEvent 被窗口服务器丢弃、直接喂 `mouseEntered` 不回调、`sendEvent` 崩；
/// 数据在 `.scratch/motion-audit-2/spike_hover_channel.md`，结论抄在
/// `PressFeedbackTests` 那条梯子判据的开头）。R45 把格子画法抽成
/// `DailyCopyHeatmapCell(isHovered:)`，于是**表达**这一半第一次可离线渲染、可逐档量。
///
/// **覆盖管线**：渲染的是产品自己的 `DailyCopyHeatmapCell`，底色是设置页的
/// `windowBackgroundColor`，尺寸是 `VisualHeat.cell` 真实格宽，两种外观都走 ——
/// 而「网格那张图确实经过这个视图」由 `testGridCellsRouteThroughTheProductCellView`
/// 这条源码守卫钉住（不是「我测了个替身」）。
/// **不覆盖**：**触发**那一半（`.onHover` 在离线渲染里不会被调用；鼠标进来→那一圈出现
/// 这条链只能人眼验，人工批次 22 与 47）。也不覆盖 tooltip 那半（系统绘制，帧里没有）。
/// 半句话都不许写成「悬停已经验过了」。
///
/// `@MainActor`：这个文件要真的画像素（`NSHostingView` + `cacheDisplay`），
/// 理由与 `PressFeedbackTests` 开头那条一样 —— 不在主 actor 上会撞上 AppKit 的
/// main-actor 隔离警告（CI 要求 0 告警），而警告一旦变多就会被 `warning:` 计数漏掉。
@MainActor
final class HeatmapHoverEvidenceTests: XCTestCase {

    /// 读数一律走 `CaptureReadings`（stdout + 文件两条腿，整行原子）。
    /// 为什么不是 `print`：R64 量过 `swift test` 的 stdout **会成块丢**（同一批代码本机两遍
    /// 分别少 324 行与 238 行，切点落在行中间），而 R300 就是被这件事咬到的 ——
    /// 出货版的环读数当时只能靠一把刀把界写成 0.0、让它红一次才拿到（BACKLOG 357）。
    /// 这一格由 `testCaptureReadingsUseTheFileChannel` 扫源码钉住：本文件里一行裸 print 都不许有。
    static func emit(_ line: String) { CaptureReadings.emit(line) }

    private func emit(_ line: String) { Self.emit(line) }

    // MARK: - 判据

    /// 五档深浅 × 亮暗两种外观 × 两种采样率：未悬停与悬停之间，
    /// **描边那一条带**必须真的变了，而且方向要对（亮色下变暗、暗色下变亮）。
    ///
    /// 为什么要逐档：这一圈的对手不是「页面底色」，是**它自己压在上面的那块色**。
    /// 空档那格底色是 `primary.opacity(0.055)`，最深那格是 `accent.opacity(0.85)` ——
    /// 同一圈 0.55 的墨压在这两块上，一个几乎没对手，一个对手最强。
    /// 只量「一格」等于把整张图的 126 格当成同一格。
    ///
    /// 为什么连采样率一起量：跑测的机器与 runner 的 `backingScaleFactor` 不同
    /// （账本里「两台机器的读数不能当另一台机器的地板」那一族），而 1pt 的描边在 1× 屏上
    /// 就**只剩一个设备像素**，抗锯齿能把它抹掉一半 —— 那正是注释里「发丝线会消失」
    /// 该被验证的情形，不是该被 4× 渲染躲掉的麻烦。
    func testHoverRingIsVisibleOnEveryHeatLevelAndBothScales() throws {
        var readings: [String] = []
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for scale in [1, 2] {
                for level in Self.levels {
                    let still = try renderCell(level: level, hovered: false,
                                               appearance: appearance, scale: scale)
                    let hover = try renderCell(level: level, hovered: true,
                                               appearance: appearance, scale: scale)
                    let size = still.pixelsWide
                    let band = Self.ringBand(size: size, scale: scale)
                    let step = Self.meanChannelDelta(still, hover, over: band, size: size)
                    let darker = Self.meanLuma(hover, over: band, size: size)
                        < Self.meanLuma(still, over: band, size: size)
                    readings.append("HEAT_RING \(tag)/\(scale)x \(level.name) 像素\(band.count) "
                                    + "带内均值通道差=\(String(format: "%.2f", step))/255 "
                                    + "方向=\(darker ? "变暗" : "变亮") 令牌=\(String(format: "%.3f", level.opacity))")
                    XCTAssertGreaterThanOrEqual(step, Self.perceptibleBand255,
                        "\(tag)/\(scale)x 的 \(level.name) 那一格：悬停之后描边带只变了 "
                        + "\(String(format: "%.2f", step))/255，低于地板 \(Self.perceptibleBand255) ⇒ "
                        + "那一圈在屏幕上根本不存在，注释里那句「发丝线会消失」说的就是这个。"
                        + "要么把 `hoverRingOpacity` 提上来，要么撤掉这圈描边并承认悬停没有视觉反馈")
                    XCTAssertEqual(darker, appearance == .aqua,
                        "\(tag)/\(scale)x：描边的方向反了（亮色应当更暗、暗色应当更亮）。"
                        + "反向说明这一圈用的不是 `Color.primary` 那一族，而是某个不随外观翻转的固定色")
                }
            }
        }
        readings.forEach { emit($0) }
        XCTAssertEqual(readings.count, 20, "读数条数必须是 外观2 × 采样率2 × 档5，少一条就是有一档没被量")
    }

    /// 悬停**只**改描边那一条带（外加它自己的抗锯齿裙边）：格子内部、别处都不许被这圈墨碰到。
    ///
    /// 这条是上一半的反面，也是「不喧宾夺主」的可数版本：
    /// 如果悬停会推着别的像素一起变（比如实现成了「整格换色」或「带阴影」），
    /// 那 126 格之间读起来就不是「哪一格被指着」，而是「一片都在亮」。
    ///
    /// R308 把这一族切成三格，因为环搬到留白之后**旧的二分不成立了**：
    /// ① 数据像素（整格）—— 由 `testHoverLeavesTheDataPixelsUntouched` 判，现读 0.000；
    /// ② 环自己的裙边（外径 ±(stroke/2 + 1.5px)）—— 那是同一个物体的半个像素，不是"别处"，
    ///    现读 7.00/255，界给到 12；旧版把它当成"带外"判红，等于要求一条矢量描边没有抗锯齿；
    /// ③ 裙边**之外**—— 仍必须是 3/255 以内（那才是「整格换色 / 阴影 / 邻居一起亮」的形状）。
    func testHoverChangesOnlyTheRingBand() throws {
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for level in Self.levels {
                let still = try renderCell(level: level, hovered: false, appearance: appearance, scale: 2)
                let hover = try renderCell(level: level, hovered: true, appearance: appearance, scale: 2)
                let size = still.pixelsWide
                let band = Self.ringBand(size: size, scale: 2)
                let fringe = Self.haloFringe(size: size, scale: 2)
                XCTAssertTrue(fringe.isDisjoint(with: band), "裙边与带重叠 ⇒ 两格量的是同一批像素")
                var worstFringe: (index: Int, delta: Double) = (-1, 0)
                var worst: (index: Int, delta: Double) = (-1, 0)
                for index in 0..<(size * size) where !band.contains(index) {
                    let d = Self.pixelChannelDelta(still, hover, index: index, size: size)
                    if fringe.contains(index) {
                        if d > worstFringe.delta { worstFringe = (index, d) }
                    } else if d > worst.delta {
                        worst = (index, d)
                    }
                }
                emit("HEAT_RING_CONFINEMENT \(tag) \(level.name) 裙边最大变化="
                      + "\(String(format: "%.2f", worstFringe.delta))/255 @(\(Self.x(of: max(worstFringe.index, 0), size: size)),"
                      + " \(Self.y(of: max(worstFringe.index, 0), size: size)))"
                      + " 裙边外最大变化=\(String(format: "%.2f", worst.delta))/255"
                      + " @(\(Self.x(of: max(worst.index, 0), size: size)),"
                      + " \(Self.y(of: max(worst.index, 0), size: size)))")
                XCTAssertLessThanOrEqual(worstFringe.delta, Self.haloFringeTolerance255,
                    "\(tag) 的 \(level.name)：裙边里有一处变了 \(String(format: "%.2f", worstFringe.delta))/255"
                        + " ⇒ 那一圈的抗锯齿比半个像素还宽，已经不是描边本身了")
                XCTAssertLessThanOrEqual(worst.delta, Self.outsideBandTolerance255,
                    "\(tag) 的 \(level.name)：裙边之外有一处变了 \(String(format: "%.2f", worst.delta))/255"
                        + "，位置 (\(worst.index % size), \(worst.index / size)) ⇒ "
                        + "这一圈不止改了描边（喧宾夺主那一族）")
            }
        }
    }

    /// 环的抗锯齿裙边：外径 ±(stroke/2 + 1.5 设备像素) 之内、`ringBand` 之外。
    static func haloFringe(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let gapPx = Double(Int(VisualHeat.hoverRingGap) * scale)
        let radius = Double(Int(VisualRadius.heatCell + VisualHeat.hoverRingGap) * scale)
        let cellHalf = Double(cellPx) / 2.0
        let outerHalf = cellHalf + gapPx
        let band = ringBand(size: size, scale: scale)
        var fringe = Set<Int>()
        for py in 0..<size {
            for px in 0..<size {
                let sdf = roundedRectSDF(px: Double(px) + 0.5 - Double(inset) - cellHalf,
                                         py: Double(py) + 0.5 - Double(inset) - cellHalf,
                                         half: outerHalf, radius: radius)
                guard abs(sdf) <= strokePx / 2.0 + 1.5 else { continue }
                let index = py * size + px
                guard !band.contains(index) else { continue }
                fringe.insert(index)
            }
        }
        return fringe
    }

    /// 裙边的界（现读 7.00/255；给到 12 = 一半以上的余量，同时仍远低于"整格换色"那一族）。
    static let haloFringeTolerance255: Double = 12.0

    /// 「不喧宾夺主」那一半：**悬停那一下不许比这张图全部的数据幅度还响**。
    ///
    /// 这条是本轮看图之前没想到的，是那批读数逼出来的（实测，2x）：
    /// 亮色下鼠标划过一个**空格**，那一条带变了 `75.50/255`，
    /// 而这张图从"一次都没复制"到"最忙的一天"的全部幅度是 `100.92/255` —— 倍率 0.75。
    /// 也就是说悬停已经**接近**数据全幅度了：再重一档就会盖过深浅本身。
    /// 一张以深浅为唯一信息通道的图，交互层不许爬到数据层上面去，所以这里判 ≤ 1.0 倍。
    ///
    /// 轴要说清楚：比的是**通道差**的幅度，不是"谁面积大"。
    /// 分母取 empty↔bucket4 这两端，因为那是这张图能画出的最大数据差；
    /// 若哪天 `ladder` 改了，分母跟着改（它不是常数，这正是它比"写死一个 100"好的地方）。
    ///
    /// **R308 把两条带分开了**：旧画法下环就压在格子上，所以分子分母可以共用 `ringBand`
    /// （同一批像素：既是被环盖住的地方，也是数据的地方）。环搬到留白之后，
    /// 外径那条带上 empty 与 bucket4 **一模一样** ⇒ 分母恒为 0，倍率变成 −1（这条判据自己红出"没在量东西"，
    /// 这是它该有的行为：今天这一格红，是因为它里面的假设随产品变了，不是因为产品坏了）。
    /// 现在分子 = 环带（交互那一条），分母 = 填充带（数据那一片），两根带严格不相交，
    /// 由 `testAdjacentLevelRulersAreATruthTable` 与 `testRingBandSelectorIsATruthTable` 各自钉住。
    func testHoverIsNotLouderThanTheDataRange() throws {
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            let size = (Int(VisualHeat.cell) + 8) * 2
            let band = Self.ringBand(size: size, scale: 2)
            let dataBand = Self.fillBand(size: size, scale: 2)
            XCTAssertFalse(band.isEmpty, "\(tag)：环带是空的 ⇒ 分子没有对象")
            XCTAssertFalse(dataBand.isEmpty, "\(tag)：填充带是空的 ⇒ 分母没有对象")
            XCTAssertTrue(band.isDisjoint(with: dataBand),
                          "\(tag)：环带与填充带重叠 ⇒ 分子分母在量同一批像素，倍率说的是别的事")
            let empty = try renderCell(level: Self.levels[0], hovered: false,
                                       appearance: appearance, scale: 2)
            let busiest = try renderCell(level: Self.levels[Self.levels.count - 1], hovered: false,
                                         appearance: appearance, scale: 2)
            let dataRange = Self.meanChannelDelta(empty, busiest, over: dataBand,
                                                  size: empty.pixelsWide)
            for level in Self.levels {
                let still = try renderCell(level: level, hovered: false,
                                           appearance: appearance, scale: 2)
                let hover = try renderCell(level: level, hovered: true,
                                           appearance: appearance, scale: 2)
                let step = Self.meanChannelDelta(still, hover, over: band, size: still.pixelsWide)
                let ratio = dataRange > 0 ? step / dataRange : -1
                emit("HEAT_LOUDNESS \(tag) \(level.name) 悬停差=\(String(format: "%.2f", step))"
                      + " 数据全幅度=\(String(format: "%.2f", dataRange)) 倍率=\(String(format: "%.2f", ratio))")
                XCTAssertLessThanOrEqual(ratio, Self.louderThanDataAllowed,
                    "\(tag) 的 \(level.name)：鼠标划过的变化是这张图数据全幅度的 "
                        + "\(String(format: "%.2f", ratio)) 倍 ⇒ 交互盖过了数据。"
                        + "要么把 `hoverRingOpacity` 降下来，要么把这圈改成不吞掉深浅的画法"
                        + "（比如只描外圈不压内容）")
                XCTAssertGreaterThanOrEqual(ratio, 0,
                    "\(tag) 的 \(level.name)：倍率是负的 ⇒ 带或分母有一个已经空了，这条判据没在量东西")
            }
        }
    }

    /// 悬停那一圈**不许比「多做一次复制」更响**（R300 / BACKLOG 314 的下半）。
    ///
    /// 上面那条 `testHoverIsNotLouderThanTheDataRange` 的分母是**全幅度**（空 → 最忙）。那条等式很宽：
    /// 全幅度横跨四档，所以「环 ≤ 1.0 × 全幅度」实际允许环等于**四档**的变化量。而这张图唯一的
    /// 信息通道就是深浅一档一档的差别（`VisualHeat.ladder` 的注释自己就写着「分不开就等于少一档」），
    /// 于是真正该问的是：**鼠标划过一格，变化相当于几档数据？** 当它比最细的一档还粗，交互就在跟数据
    /// 抢同一根轴 —— 这才是目标里那句「不喧宾夺主」的可数版本。R264 看图时我只写下「那圈一眼可见」，
    /// 没有这一格，那句话到今天为止都只是形容词。
    ///
    /// 分母不是拍的，也不是外部惯例：**同一颗尺、同一条 render** 现量 —— 把五档挨个画成未悬停，
    /// 取相邻档在**填充带**上的档步（只收过噪声地板的真换档），再要求每一档悬停时在**描边带**上的变化
    /// 不超过 `heaviestDataStepAllowed × 最重的那一步`。两根带不重叠由
    /// `testAdjacentLevelRulersAreATruthTable` 钉着，所以分子分母量的不是同一块像素。
    /// 读数同时打印「对最重」与「对最细」两个倍率：后者今天过不了，那是**记在账上的形状限制**（356），
    /// 不是把它删掉的理由。
    func testHoverIsNotLouderThanOneDataStep() throws {
        var readings: [String] = []
        var spreadReadings: [String] = []
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for scale in [1, 2] {
                let size = (Int(VisualHeat.cell) + 8) * scale
                let fill = Self.fillBand(size: size, scale: scale)
                let ring = Self.ringBand(size: size, scale: scale)
                XCTAssertFalse(fill.isEmpty, "\(tag)/\(scale)x 的填充带是空的 ⇒ 分母没有对象")
                XCTAssertFalse(ring.isEmpty, "\(tag)/\(scale)x 的描边带是空的 ⇒ 分子没有对象")
                let stills = try Self.levels.map {
                    try renderCell(level: $0, hovered: false, appearance: appearance, scale: scale)
                }
                var steps: [Double] = []
                var maxSteps: [Double] = []
                var levelDeltas: [Double] = []
                for i in 1..<stills.count {
                    let d = Self.meanChannelDelta(stills[i - 1], stills[i], over: fill, size: size)
                    if d > Self.ringNoiseFloor255 { steps.append(d) }
                    maxSteps.append(Self.meanMaxChannelDelta(stills[i - 1], stills[i], over: fill, size: size))
                }
                XCTAssertFalse(steps.isEmpty,
                    "\(tag)/\(scale)x：一个正档步都没量到 ⇒ 分母是空的，这条判据不许把「没量到」读成合规")
                let minStep = steps.min()!
                let maxStep = steps.max()!
                let stepList = steps.map { String(format: "%.2f", $0) }.joined(separator: "/")
                XCTAssertEqual(steps.count, Self.levels.count - 1,
                    "\(tag)/\(scale)x：四对相邻档里只有 \(steps.count) 对被算进分母 ⇒ 有一对落在噪声地板以下，"
                    + "那正是上面那条档间判据该红的时候，不该在这里被悄悄丢掉")
                for (i, level) in Self.levels.enumerated() {
                    let hover = try renderCell(level: level, hovered: true,
                                               appearance: appearance, scale: scale)
                    let ringStep = Self.meanChannelDelta(stills[i], hover, over: ring, size: size)
                    // R308 第二遍：把**两根轴同时**量出来。本文件在相邻档那条判据里已经写过
                    // 「拿均值判『灰 vs 蓝』会低 3 倍」（`testAdjacentHeatLevelsAreSeparableOnTheRightAxis`），
                    // 而这一格的分母正是同一批灰→蓝的档步 ⇒ 只在均值上比，等于用一把自己承认过用错的轴
                    // 去判交互响不响。先都印出来，界怎么压由读数决定，不由愿望决定。
                    let ringMax = Self.meanMaxChannelDelta(stills[i], hover, over: ring, size: size)
                    let ratio = ringStep / maxStep
                    let vsMin = ringStep / minStep
                    let maxStepList = maxSteps.map { String(format: "%.2f", $0) }.joined(separator: "/")
                    readings.append("HEAT_RING_VS_STEP \(tag)/\(scale)x \(level.name) "
                                    + "环=\(String(format: "%.2f", ringStep)) "
                                    + "档步=[\(stepList)] "
                                    + "最细=\(String(format: "%.2f", minStep)) 最重=\(String(format: "%.2f", maxStep)) "
                                    + "倍率(对最重)=\(String(format: "%.2f", ratio)) "
                                    + "倍率(对最细)=\(String(format: "%.2f", vsMin)) "
                                    + "令牌=\(String(format: "%.3f", VisualHeat.hoverRingOpacity(isHovered: true))) "
                                    + "｜最大通道轴 环=\(String(format: "%.2f", ringMax)) "
                                    + "档步=[\(maxStepList)] "
                                    + "倍率(对最细那步)=\(String(format: "%.2f", ringMax / maxSteps.min()!))")
                    XCTAssertLessThanOrEqual(ratio, Self.heaviestDataStepAllowed,
                        "\(tag)/\(scale)x 的 \(level.name)：鼠标划过那一格改了 \(String(format: "%.2f", ringStep))/255，"
                        + "而这张图最重的一次数据变化只改 \(String(format: "%.2f", maxStep))/255"
                        + "（四对档步=[\(stepList)]）⇒ 交互比一次真实的数据变化还响。"
                        + "改 `VisualHeat.hoverRingOpacity`（或描边宽度），别把这条地板抬高；"
                        + "降下来之后 `testHoverRingIsVisibleOnEveryHeatLevelAndBothScales` 那根 18 的地板仍在，"
                        + "两条一起把这一圈夹在一个窗口里")
                    levelDeltas.append(ringStep)
                }
                // R308 新增的那一根轴：**同一个动作不许随数据深浅变响**。
                // 旧画法（环压在格子上）现读亮 2x 41.42…23.65 = 1.75 倍、亮 1x 32.60…18.87 = 1.73 倍，
                // 而且**最响的一臂正是空格**（那格里根本没有数据要保护）；
                // 环搬到留白之后同一批臂量出 1.00 —— 这一格就是把那个 1.00 钉成契约，
                // 谁把画法搬回格子里、或按档位改环的轻重，这里当场红（界给 1.05，只放得下测量噪声）。
                let spread = levelDeltas.max()! / levelDeltas.min()!
                spreadReadings.append("HEAT_RING_LEVEL_SPREAD \(tag)/\(scale)x 最响/最安静=\(String(format: "%.3f", spread)) "
                                + "各档=[\(levelDeltas.map { String(format: "%.2f", $0) }.joined(separator: "/"))]")
                XCTAssertLessThanOrEqual(spread, Self.ringLevelSpreadAllowed,
                    "\(tag)/\(scale)x：鼠标划过**同样一下**，在最深的格上只改 "
                        + "\(String(format: "%.2f", levelDeltas.min()!))/255，在最浅的格上改 "
                        + "\(String(format: "%.2f", levelDeltas.max()!))/255 ⇒ 差 \(String(format: "%.2f", spread)) 倍，"
                        + "交互的响度在跟着数据变（旧画法的形状）。改的是画法（环不许压数据像素），不是这条界")
            }
        }
        readings.forEach { emit($0) }
        spreadReadings.forEach { emit($0) }
        XCTAssertEqual(readings.count, 20, "读数必须是 外观2 × 尺度2 × 档5 = 20 条，少一条就是有一臂没被量")
        XCTAssertEqual(spreadReadings.count, 4, "档间离散必须是 外观2 × 尺度2 = 4 条 ⇒ 少一条就有一臂没算进离散")
    }

    /// 「同一个动作的响度不许随数据深浅变」的界（同一外观、同一尺度内，最响 ÷ 最安静）。
    ///
    /// 现读 1.000（环在留白里，五档给同一个数），界给 1.05 —— 那半成是测量噪声，不是余量：
    /// 旧画法是 1.73…1.75，把界放到 1.2 也照样拦得住，但**放那么宽就等于允许"按档微调"**，
    /// 而 `testHoverRingOpacityTruthTable` 第③格已经写明这一圈只能表达「被指着」，不许表达轻重。
    static let ringLevelSpreadAllowed: Double = 1.05

    /// 悬停**一个数据像素都不许动**（R308 / BACKLOG 356 的换形状落地）。
    ///
    /// 旧画法 `strokeBorder` 把那一圈画在形状**里面**：鼠标每划过一格，那一格外圈的
    /// **数据像素**就被灰色的环换掉 —— 而这张图唯一的信息服务于深浅。旧的三条判据对这件事是**盲的**：
    /// `fillBand` 刻意离边一条描边之远（为的是"两档差多少"不被抗锯齿污染），
    /// `ringBand` 又把那一圈当成"环"，于是"环压掉数据"正好落在两条带**之间**被缝掉 ——
    /// 本轮之前没有任何一格量过**整格**。这是"尺子只量它切好的地方"那一族（D-244 的反面：
    /// 不是判据不响，是根本没有判据对着这件事）。
    ///
    /// 分母是 `cellBoxBand`（整格 = cellPx²，由 `testAdjacentLevelRulersAreATruthTable` 钉着它自己），
    /// 分子沿用同一颗 `meanChannelDelta`，不新造尺。
    /// 上限不是口味：环搬到留白之后格内唯一可能的变化是 halo 的抗锯齿外溢，
    /// 界压到 1.0/255 —— 把画法改回 `strokeBorder` 会当场跳到 10 以上（刀 M889 钉的就是这件事）。
    func testHoverLeavesTheDataPixelsUntouched() throws {
        var readings: [String] = []
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for scale in [1, 2] {
                for level in Self.levels {
                    let still = try renderCell(level: level, hovered: false,
                                               appearance: appearance, scale: scale)
                    let hover = try renderCell(level: level, hovered: true,
                                               appearance: appearance, scale: scale)
                    let size = still.pixelsWide
                    let box = Self.cellDataBand(size: size, scale: scale)
                    XCTAssertFalse(box.isEmpty, "\(tag)/\(scale)x 的数据带是空的 ⇒ 这条判据没有对象")
                    let delta = Self.meanChannelDelta(still, hover, over: box, size: size)
                    XCTAssertGreaterThanOrEqual(delta, 0,
                        "\(tag)/\(scale)x 的 \(level.name)：整格差是负数 ⇒ 分母或取像素已经坏了，别拿它当「通过了」")
                    readings.append("HEAT_DATA_UNTOUCHED \(tag)/\(scale)x \(level.name) "
                                    + "数据像素均值通道差=\(String(format: "%.3f", delta))/255 "
                                    + "像素=\(box.count) 环距=\(String(format: "%.2f", VisualHeat.hoverRingGap))pt "
                                    + "环宽=\(String(format: "%.2f", VisualHeat.hoverStroke))pt")
                    XCTAssertLessThanOrEqual(delta, Self.hoverMustNotTouchDataInk255,
                        "\(tag)/\(scale)x 的 \(level.name)：鼠标划过那一格让**数据像素**均值改了 "
                            + "\(String(format: "%.3f", delta))/255 ⇒ 那一圈还在换掉数据像素。"
                            + "改的是画法（环要在格子外面的留白里，`stroke` + `padding(-hoverRingGap)`），"
                            + "不许把这条界抬高")
                }
            }
        }
        readings.forEach { emit($0) }
        XCTAssertEqual(readings.count, 20, "读数必须是 外观2 × 尺度2 × 档5 = 20 条，少一条就是有一臂没被量")
    }

    /// 「悬停不许动数据像素」的界（均值通道，0–255）。见上面那条的注释：1.0 给的是抗锯齿外溢的余量。
    static let hoverMustNotTouchDataInk255: Double = 1.0

    /// halo 分类器的容差（设备像素）。**不是半像素**：0.5 会把零覆盖的那一行算进带里稀释均值，
    /// 详见 `ringBand` 那段注释；这一格的实际落点由 `testRingBandSelectorIsATruthTable` ④b 按行号验。
    static let ringBandAllowance: Double = 0.4

    /// 「悬停不许比一次真实的数据变化更响」的允许倍率。1.0 的意思很直白：
    /// 鼠标划过一格带来的像素变化，不许超过这张图上**最重的一次数据变化**（第 3 档 → 第 4 档）。
    ///
    /// 为什么分母取最重的那一步而不是最细的那一步 —— 我第一版就是那么写的，然后被自己的读数驳回：
    /// 亮档四对档步 = 19.33 / 21.00 / 28.33 / 37.33，暗档 = 17.33 / 18.33 / 25.33 / 33.67，
    /// 而 `testHoverRingIsVisibleOnEveryHeatLevelAndBothScales` 那根 18 的地板要求这一圈在**最安静的那一档**
    /// （bucket4 / 1x）上至少改 18/255；那一臂在 0.55 时只改 36.10，按比例算出**能看见的下限是 0.274**，
    /// 而 0.274 的环在最响的一臂上是 0.274/0.55 × 75.50 = 37.6 —— 恰好等于**最重**的一次档步。
    /// 也就是说「环 ≤ 最细一档」在这套形状（11pt 格 + 4 档 + 描边环）下**数学上装不下**：
    /// 四步全要 ≥ 37.6 就得有 150 的总幅度，而整条梯子只有约 106。⇒ 这条界今天只能压在最重的一步上，
    /// 「要让它连最细的一步都不许超过」欠的是形状（档数 / 格子尺寸 / 悬停换通道），记在 BACKLOG 356，
    /// 不许把它写成"已达标"，也不许偷偷把倍率抬高去迁就现状。
    static let heaviestDataStepAllowed: Double = 1.0

    /// 什么算「一次真的换档」：与捕获卷那把带窗同一条界（`|Δ| > 2`），不是新发明的数。
    static let ringNoiseFloor255: Double = 2.0

    /// 分类器自己的真值表：带 = `strokeBorder` 实际覆盖的那一圈（SDF 判）。
    ///
    /// 为什么单独立：上面两条判据的全部含义都在「哪些像素算这条带」上。
    /// 带里混进底色像素，就会把「圈没画上」读成「圈画上了」；带里混进格子内部像素，
    /// 则会把「整格都在变」读成合规。而**带切掉了真描边**（本轮第一版干的就是这件事）
    /// 会让"悬停只改这一圈"报出一条根本不存在的缺陷 —— 这一族比假 ✓ 更浪费轮次。
    ///
    /// 坐标一律**从几何算出来**，不写死 22 这种数：写死一次，改了留白之后这一格就悄悄量的是别的地方。
    func testRingBandSelectorIsATruthTable() {
        // ① 真实几何：11pt 格 + 每边 4pt 留白，2x ⇒ 边长 38、格子占中间 22，
        //    而 R308 之后环画在格子**外面**的那 4pt 留白里（外径 = 22 + 2×gap）。
        let scale = 2
        let size = (Int(VisualHeat.cell) + 8) * scale
        let inset = 4 * scale
        let cellPx = size - inset * 2
        XCTAssertEqual(size, 38, "夹具几何变了而下面七格还在按老坐标判 ⇒ 先让这里红")
        XCTAssertEqual(cellPx, Int(VisualHeat.cell) * scale)

        let band = Self.ringBand(size: size, scale: scale)
        XCTAssertFalse(band.isEmpty, "带是空的 ⇒ 上面两条判据会拿着 0 个像素算均值，那等于没有判据")
        XCTAssertLessThan(band.count, cellPx * cellPx / 2,
                          "带占了半张格以上 ⇒ 量的已经不是那一圈，而是整格")
        // ② 带里没有一个像素落在**数据像素**上（格子真的画出来的那一片，圆角以内）。
        //    这一格与下面那条「悬停不许动数据像素」是一对：那格量产品，这格量尺子。
        let dataPixels = Self.cellDataBand(size: size, scale: scale)
        let insideData = band.filter { dataPixels.contains($0) }
        XCTAssertTrue(insideData.isEmpty,
                      "带伸进了数据像素 \(insideData.count) 个 ⇒ 它量的是格子画出来的地方，"
                    + "「环搬到留白」这件产品事实会被尺子抹掉")
        // ③ 带必须还在**夹具的留白**里：贴在位图边缘的环会被裁掉，读数看着"环很淡"，
        //    真相是那一圈根本没被画全（R209 那一族：组件的边不出现在帧里，尺子就瞎）。
        let clipped = band.filter {
            let x = Self.x(of: $0, size: size), y = Self.y(of: $0, size: size)
            return x < 1 || y < 1 || x > size - 2 || y > size - 2
        }
        XCTAssertTrue(clipped.isEmpty, "带贴到位图边缘 ⇒ 那一圈被裁了，量出来的差不是产品画的那一圈")
        // ④ 带里每个点都必须在「外径那一圈」的 ±(stroke/2 + 容差) 内 ——
        //    外径 = 格子半宽 + gap，半径**不跟着放大**（产品是在放大后的框上画同一个 cornerRadius），
        //    而**中心与格子同心**（`.padding` 四边等量外扩）。
        let gapPx = Double(Int(VisualHeat.hoverRingGap) * scale)
        let cellHalf = Double(cellPx) / 2.0
        let outerHalf = cellHalf + gapPx
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let radius = Double(Int(VisualRadius.heatCell + VisualHeat.hoverRingGap) * scale)
        let offRing = band.filter {
            let dx = Double(Self.x(of: $0, size: size)) + 0.5 - Double(inset) - cellHalf
            let dy = Double(Self.y(of: $0, size: size)) + 0.5 - Double(inset) - cellHalf
            return abs(Self.roundedRectSDF(px: dx, py: dy, half: outerHalf, radius: radius))
                > strokePx / 2.0 + Self.ringBandAllowance
        }
        XCTAssertTrue(offRing.isEmpty, "带里有 \(offRing.count) 个像素不在这条外径上 ⇒ 分类器量的不是那一圈")
        // ④c **同心**：带里每个点到「格子自己那条圆角路径」的距离都得是 gap ±(描边一半 + 容差)。
        //     半径不跟着外扩的写法（本轮第一版）在直边上是准的，只有 45° 角上外偏 0.41pt = 0.83 设备像素
        //     ⇒ 这一格专治角：直边的读数看不见它，肉眼在 11pt 的格子上也几乎挑不出来，
        //     但它就是"同一圈到格子的间距不统一"，而这一圈的全部作用就是把自己读成一圈。
        let cellRadiusPx = Double(Int(VisualRadius.heatCell) * scale)
        let uneven = band.filter {
            let dx = Double(Self.x(of: $0, size: size)) + 0.5 - Double(inset) - cellHalf
            let dy = Double(Self.y(of: $0, size: size)) + 0.5 - Double(inset) - cellHalf
            return abs(Self.roundedRectSDF(px: dx, py: dy, half: cellHalf, radius: cellRadiusPx) - gapPx)
                > strokePx / 2.0 + 0.5
        }
        XCTAssertTrue(uneven.isEmpty,
                      "环到格子边的距离不统一（\(uneven.count) 个像素偏出 gap ± 半个描边）"
                      + " ⇒ 角上的间距与直边不一样，那一圈不是同心的（圆角半径要跟着外扩）")
        // ④b **带的位置按行号点验**：中间那一列（x = inset + cellPx/2）会同时穿过**上、下两条**
        //     halo，2x 上应当是行 {5, 6}（外边距 8−2=6 为中心线 ±1）与 {31, 32}。
        //     第一版的 `ringBand` 把中心也外推了一个 gap ⇒ 带整体偏移 2px：真 halo 被算成带外
        //     （`testHoverChangesOnlyTheRingBand` 抓到 (11,5) 变了 65 却不在带里），
        //     而带里那些没画的像素把均值稀释 ⇒ 可见性地板会红在尺子上。这一格让那种整体偏移必红。
        let midColumnRows = Set(band.filter { Self.x(of: $0, size: size) == inset + cellPx / 2 }
                                   .map { Self.y(of: $0, size: size) })
        XCTAssertEqual(midColumnRows, Set([5, 6, 31, 32]),
                       "中间那一列带覆盖的行 = \(midColumnRows.sorted())，要 [5, 6, 31, 32]（上下两条 halo）"
                       + " ⇒ halo 的几何与产品画的不再是同一圈")
        XCTAssertEqual(band.filter { Self.x(of: $0, size: size) == inset + cellPx / 2 && Self.y(of: $0, size: size) == 8 }.count, 0,
                       "带压进了格子的第一行（y=8）⇒ 它会把数据像素算进「那一圈」")
        // ⑤ 四条边都得有人，**四个角也得有人**（角那一半是 R45 第一版切掉过的地方，留着当反面守卫）。
        //    R308 起"边"指的是留白里那四条 halo，**不是**格子的四条边 ——
        //    左边 = x < inset，右边 = x ≥ inset + cellPx，上下同理。
        let edges = [
            ("左边", band.filter { Self.x(of: $0, size: size) < inset }.count),
            ("右边", band.filter { Self.x(of: $0, size: size) >= inset + cellPx }.count),
            ("上边", band.filter { Self.y(of: $0, size: size) < inset }.count),
            ("下边", band.filter { Self.y(of: $0, size: size) >= inset + cellPx }.count),
        ]
        for (name, count) in edges {
            XCTAssertGreaterThan(count, 0, "\(name)一个像素都没有 ⇒ 这条带判不了那一边的圈")
        }
        let corners = [
            ("左上", band.filter { Self.x(of: $0, size: size) < inset && Self.y(of: $0, size: size) < inset }.count),
            ("右上", band.filter { Self.x(of: $0, size: size) >= inset + cellPx && Self.y(of: $0, size: size) < inset }.count),
            ("左下", band.filter { Self.x(of: $0, size: size) < inset && Self.y(of: $0, size: size) >= inset + cellPx }.count),
            ("右下", band.filter { Self.x(of: $0, size: size) >= inset + cellPx && Self.y(of: $0, size: size) >= inset + cellPx }.count),
        ]
        for (name, count) in corners {
            XCTAssertGreaterThan(count, 0, "角区 \(name) 一个带像素都没有 ⇒ 描边在角上被切掉了（第一版的毛病）")
        }
        // ⑥ 1× 屏（格宽就是 11 个设备像素，halo 只有 1 个像素宽）：带还得非空，四条边也得有人。
        //    这一格不是凑数 —— 若选择器在「带宽 ≈ 描边宽」这种退化几何上返回空，
        //    1× 那条判据臂会拿着 0 像素的均值「通过」。
        let oneXSize = Int(VisualHeat.cell) + 8
        let oneX = Self.ringBand(size: oneXSize, scale: 1)
        XCTAssertFalse(oneX.isEmpty, "1× 屏上带是空的 ⇒ 那一整臂什么都没量")
        XCTAssertTrue(oneX.filter(Self.cellDataBand(size: oneXSize, scale: 1).contains).isEmpty,
                      "1× 的带伸进了数据像素 ⇒ 与 2× 那条同一件事：halo 不许量格子画出来的地方")
        let oneXEdges = [
            oneX.filter { Self.x(of: $0, size: oneXSize) < 4 }.count,
            oneX.filter { Self.x(of: $0, size: oneXSize) >= 4 + 11 }.count,
            oneX.filter { Self.y(of: $0, size: oneXSize) < 4 }.count,
            oneX.filter { Self.y(of: $0, size: oneXSize) >= 4 + 11 }.count,
        ]
        XCTAssertTrue(oneXEdges.allSatisfy { $0 > 0 }, "1× 的带缺了某一条边：\(oneXEdges)")
        // ⑥ 退化几何必须是**空**而不是越界崩溃：留白比整张图还大的那一刻没有格子像素。
        XCTAssertTrue(Self.ringBand(size: 0, scale: 2).isEmpty)
        XCTAssertTrue(Self.ringBand(size: 8, scale: 2).isEmpty,
                      "留白吃掉整个边长 ⇒ 必须是空带，而不是把留白当格子")
        // ⑦ SDF 本体的符号：中心在形内（负）、远处在形外（正）、边线上约等于 0。
        //    符号反了整个带会挑到形外面去，而读数看着还挺"明显"。
        XCTAssertLessThan(Self.roundedRectSDF(px: 0, py: 0, half: 11, radius: 4), 0)
        XCTAssertGreaterThan(Self.roundedRectSDF(px: 20, py: 20, half: 11, radius: 4), 0)
        XCTAssertEqual(Self.roundedRectSDF(px: 11, py: 0, half: 11, radius: 4), 0, accuracy: 0.001,
                       "直边中点的 SDF 该是 0：这里偏了，带就会整体往里或往外挪一像素")
        _ = radius
    }

    /// `hoverRingOpacity` 的真值表（纯函数那一半）。
    func testHoverRingOpacityTruthTable() {
        XCTAssertEqual(VisualHeat.hoverRingOpacity(isHovered: true), 0.20, accuracy: 0.0001,
                       "悬停那一圈的透明度是量出来的那个数（R300 从 0.55 降到 0.30，"
                       + "R308 环搬到留白、档间离散归一之后降到 0.20）；改了令牌就得同时改判据里的说明")
        XCTAssertEqual(VisualHeat.hoverRingOpacity(isHovered: false), 0, accuracy: 0.0001,
                       "非悬停必须是 0，不是「几乎看不见」的 0.02：常驻淡描边会让 126 格同时开口说话")
        // ③ 只有两档：不许出现第三值（比如按 bucket 分轻重 —— 这张图的信息全在深浅上）。
        let values = [true, false].map { VisualHeat.hoverRingOpacity(isHovered: $0) }
        XCTAssertEqual(Set(values).count, 2, "这一圈不许随档位变色或变重：它唯一能表达的是「被指着」")
    }

    /// 源码守卫：网格那张图**确实**经过被我量的这个视图。
    ///
    /// 没有这一条，上面三判据测的就可能是一份产品根本不用的替身 ——
    /// 我把画法抽出来了，但如果 `gridSection` 还在原地自己再画一份，量的是影子。
    func testGridCellsRouteThroughTheProductCellView() throws {
        let source = try harnessSourceOfFile("DailyCopyHeatmapView.swift")
        // ① 网格里出现的是 `DailyCopyHeatmapCell(`，不是自己再画一遍。
        XCTAssertTrue(source.contains("DailyCopyHeatmapCell("),
                      "`cellView` 不再把格子交给 `DailyCopyHeatmapCell` ⇒ 判据量的是影子")
        // ② 那一圈的画法在文件里只有一处（两处就是两份会分叉的真值）。
        //    按完整串数，不按子串前缀（账本里「按名字查消费者会被前缀白拿」那一族）。
        //    R308 起画法是 `stroke` + `padding(-gap)`（环在格子**外面**），
        //    所以串的锚点跟着换了；旧锚 `.strokeBorder(` 现在必须是 0 次 ——
        //    这一格就是那把刀的替身：谁把画法搬回格子内侧，这里当场红，不必等到像素判据。
        let draws = Self.occurrences(of: ".stroke(Color.primary.opacity(VisualHeat.hoverRingOpacity",
                                     in: source)
        XCTAssertEqual(draws, 1, "悬停那一圈的画法出现 \(draws) 次 ⇒ 有两份会分叉的真值")
        XCTAssertEqual(Self.occurrences(of: ".strokeBorder(Color.primary.opacity(VisualHeat.hoverRingOpacity",
                                        in: source), 0,
                       "画法退回了 `strokeBorder`（画在形状里面）⇒ 那一圈会盖掉数据像素")
        XCTAssertEqual(Self.occurrences(of: ".padding(-VisualHeat.hoverRingGap)", in: source), 1,
                       "环的外推距离不再走令牌 ⇒ 尺子里的 halo 几何与画面上的环不是同一个数")
        // ③ 圈的那半只由 `hoverRingOpacity` 决定，不许有第二个裸数写进这一层。
        XCTAssertEqual(Self.occurrences(of: "Color.primary.opacity(0.55)", in: source), 0,
                       "调用点上有裸的 0.55 ⇒ 令牌与画面上不是同一个数")
        // ④ 未来的格子仍然**不画**（提取时最容易顺手丢掉的一条：把 Color.clear 那半也搬进 cell 视图）。
        XCTAssertTrue(source.contains("Color.clear.frame(width: VisualHeat.cell"),
                      "未来/窗口外那格的「不画」分支丢了 ⇒ 会画出一张骗人的日历（U-30 缺陷 5 那一族）")
    }

    /// 夹具自检：那两张 `heatmap-cell-strip-*` 帧里必须**真的有多种深浅**，
    /// 而且被悬停的那一格必须是一格**画得出来**的格子。
    ///
    /// 为什么要有这一条：第一版取 `prefix(3)`（最老三列），而夹具的计数只往回铺 126 天、
    /// 窗口是 182 天 ⇒ 那三列全是空档。拍出来的两张帧**都存在、都不为空、只差一圈墨**，
    /// 判据全绿，而我想看的那件事（深蓝格子上那一圈还在不在）根本没进画面。
    /// 「帧存在 ≠ 被摄对象在帧里」在 R28c 与批次 22 上各栽过一次，这次是第三次 ——
    /// 所以这一条判的是夹具自己，不是产品。
    ///
    /// 第二半是同一条规矩的另一个方向：如果 `hoveredIndex` 落在**未来格**上，
    /// 产品画的是 `Color.clear`，那一圈无处可画 ⇒ 两张帧会一模一样，
    /// "悬停有反馈"就会以"两帧相同"的形式被读成"判据说没变化"。
    func testHoverStripFixtureSpansSeveralHeatLevels() {
        let calendar = UICaptureTests.heatmapFixtureCalendar()
        let today = UICaptureTests.heatmapFixtureToday
        let counts = UICaptureTests.heatmapFixtureCounts(today: today, calendar: calendar)
        let cells = UICaptureTests.heatmapHoverStripCells(counts: counts, today: today,
                                                          calendar: calendar)
        XCTAssertEqual(cells.count, 21, "带是 3 列 × 7 行 ⇒ 21 格，少一格就是夹具与帧对不上")
        let drawable = Array(cells.enumerated().filter {
            $0.element.dayKey != nil && !$0.element.isFuture
        })
        emit("HEAT_STRIP n=\(cells.count) 可画=\(drawable.count) "
              + "档=\(Set(drawable.map { $1.bucket }).sorted()) 计数=\(cells.map { $0.count })")
        // 未来格留白是**对的**（画成灰格等于宣称那天没复制），所以这里不要求 21 格全可画，
        // 只要求可画的占多数 —— 少了这一半，那张带就退化成一片空白。
        XCTAssertGreaterThanOrEqual(drawable.count, cells.count * 2 / 3,
                                    "可画的格子只有 \(drawable.count)/\(cells.count) 格 ⇒ 那张带大半是留白")
        let buckets = Set(drawable.map { $1.bucket })
        XCTAssertGreaterThanOrEqual(buckets.count, 3,
            "这条带里只有 \(buckets.sorted()) 几档 ⇒ 那张帧回答不了「那一圈压在深色格上还在不在」，"
            + "换列（现在是 suffix(3)）而不是换判据")
        let hovered = UICaptureTests.heatmapHoverStripHoveredIndex
        XCTAssertTrue(drawable.contains { $0.offset == hovered },
                      "被悬停的第 \(hovered) 格是未来/窗口外的格子 ⇒ 产品对它画 Color.clear，"
                      + "那一圈无处可画，两张帧会一模一样")
    }

    // MARK: - 地板

    /// 色觉模拟之后，相邻两档**还分得开吗**（R198 / 结案 BACKLOG 221）。
    ///
    /// 为什么加这一根轴：R197 我先用**亮度比值**去质询 `空→第 1 档`（亮档比值只有 1.05），
    /// 那其实是把 R51/R53 已经证伪过的轴又提一遍 —— 那一步差的是**色相/彩度**不是明度
    /// （`VisualHeat.empty` 走 `primary` 灰，四档走 `accent` 蓝），所以"亮度几乎不动"是设计如此，不是缺陷。
    /// 但质询本身问对了另一半：**只靠彩度分开的两档，在色觉障碍下会不会并成一步？** 这个能测。
    ///
    /// **实测答案（本轮那 16 条 `HEAT_ADJACENT_CVD`）：不会并成一步** —— 最小的一格是 `light 空→第 1 档`
    /// 的 25.41/255，其余 15 格在 29.22…64.02，全部压在地板之上 ⇒ 梯子在绿色盲下仍是五档。
    /// 方向是量出来才看清的，而且和直觉相反：**暗档几乎不掉（保住 97–98%），亮档掉到 65–80%**。
    /// 两档的分离压在不同通道上：暗档 (41,41,41)→(25,47,71)→…→(4,108,221) 的差大头在**蓝**，
    /// 而 deuteranopia 矩阵对蓝几乎不动（`0.96 b + 0.04 g`）⇒ 蓝是这条轴的免疫通道；
    /// 亮档 (243,243,243)→(209,231,255)→…→(38,142,255) 的差里有大头在**红**，那正是被红绿混合压掉的那一根。
    /// ⇒ 结案 BACKLOG 221 时给的是**通道读数**，不是"彩度够不够"这种形容词。
    ///
    /// 1x 与 2x 给出**完全相同**的 16 个数（只有 `像素=49` 对 `像素=256` 不同）：静态色判据没有尺度依赖。
    /// 2x 留着不是为了多覆盖，是为了"哪天描边或圆角把填充带吃掉会立刻在像素数上被看见"。
    ///
    /// 地板**沿用同一把 `adjacentLevelFloor255`（=18，R45 从 20 条真读数推出来的"看得出来"线）**，
    /// 不新发明数，也不为这条新轴放宽：如果哪天它红了，改的是产品的梯子（`VisualHeat.ladder`/`empty`），
    /// 并且要同步帧基线 —— 与上面那条同规矩。**这条现在有正对照钉着**（`M735`：把模拟的两格换成同一格 ⇒ 立刻红）。
    ///
    /// **R198 第一版这条判据是红的，而红的是尺子、不是产品**：那版蓝通道漏了重新编码
    /// （红绿走 sRGB 编码、蓝留线性），同一个产品在暗档 `空→第 1 档` 读成 10.41（假红），
    /// 又在 `第 3→第 4 档` 读出 99.60 > 模拟前 65.00 —— "模拟之后反而更分得开"物理上不可能，
    /// 那就是同一颗尺两头用两种单位的证人。它由下面那条**与产品颜色无关**的真值表钉住，不许靠肉眼发现第二次。
    func testAdjacentHeatLevelsStaySeparableUnderDeuteranopia() throws {
        var readings: [String] = []
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for scale in [1, 2] {
                let renders = try Self.levels.map {
                    try renderCell(level: $0, hovered: false, appearance: appearance, scale: scale)
                }
                let size = renders[0].pixelsWide
                let band = Self.fillBand(size: size, scale: scale)
                XCTAssertFalse(band.isEmpty, "\(tag)/\(scale)x 的填充带是空的 ⇒ 这条判据没在量任何东西")
                // R202 的分辨实验读数。两条通道（判据读内存 rep / 脚本读落盘 PNG）对同一格
                // **只在 R 上不同**：按 gamma 混合反解出来的 accent 是 判据≈(0,122,255) 对 真帧≈(30,122,255)，
                // G/B 一模一样 ⇒ 既不是 alpha（两边都 255），也不是混合空间不同（那会三通道一起动，
                // 且暗档动得最多的会是 B 而不是 R）。剩下的候选是**同一种颜色被标注/解析成不同色彩空间**，
                // 所以这一行把 rep 自己的色彩标签与 `colorAt` 返回色的标签都打出来，让下一跑直接判掉它。
                let csRep = renders[0].colorSpace.localizedName ?? "无名"
                var csPix = "读不到"
                if let first = band.min() {
                    let p = (Self.x(of: first, size: size), Self.y(of: first, size: size))
                    if let c = renders[0].colorAt(x: p.0, y: p.1) {
                        csPix = c.colorSpace.localizedName ?? "无名"
                    }
                }
                emit("HEAT_INK_SPACE \(tag)/\(scale)x rep=\(csRep) 取色=\(csPix)")
                for i in 1..<Self.levels.count {
                    let a = Self.levels[i - 1], b = Self.levels[i]
                    let normal = Self.meanMaxChannelDelta(renders[i - 1], renders[i], over: band, size: size)
                    let simulated = Self.meanMaxChannelDeltaSimulated(renders[i - 1], renders[i], over: band, size: size)
                    let cvd = simulated.delta
                    // 两颗尺必须量同一批像素，否则"模拟前/模拟后"是两个数而不是一个比。
                    XCTAssertEqual(simulated.undecodable, 0,
                                   "\(tag)/\(scale)x 的 \(a.name)→\(b.name) 有 \(simulated.undecodable) 格像素转不成 sRGB ⇒ "
                                   + "模拟那一步跳过了它们，均值只剩 \(simulated.sampled)/\(band.count)，这条读数不可信")
                    XCTAssertEqual(simulated.sampled, band.count,
                                   "\(tag)/\(scale)x 的 \(a.name)→\(b.name)：填充带 \(band.count) 格只量到 \(simulated.sampled) 格 ⇒ 分母不是它自己说的那个")
                    readings.append("HEAT_ADJACENT_CVD \(tag)/\(scale)x \(a.name)→\(b.name) 像素=\(simulated.sampled) "
                                    + "前墨=\(Self.fillInk(renders[i - 1], over: band, size: size)) "
                                    + "后墨=\(Self.fillInk(renders[i], over: band, size: size)) "
                                    + "模拟前=\(String(format: "%.2f", normal)) "
                                    + "模拟后=\(String(format: "%.2f", cvd)) "
                                    + "保住=\(String(format: "%.0f%%", 100.0 * cvd / max(normal, 0.001)))")
                    XCTAssertGreaterThanOrEqual(cvd, Self.adjacentLevelFloor255,
                        "\(tag)/\(scale)x 的 \(a.name)→\(b.name)：绿色盲模拟之后整格填充只差 "
                            + "\(String(format: "%.2f", cvd))/255（最大通道那一根），低于地板 "
                            + "\(Self.adjacentLevelFloor255) ⇒ 这两档对色觉障碍用户是同一档。"
                            + "改 `VisualHeat.ladder`/`empty`（往低档里掺一点亮度，别只靠彩度）并同步帧基线；"
                            + "不许把地板调低，也不许把这条判据删掉。模拟前=\(String(format: "%.2f", normal))")
                }
            }
        }
        readings.forEach { emit($0) }
        XCTAssertEqual(readings.count, 16,
                       "读数必须是 4 对 × 2 外观 × 2 尺度 = 16 条，少一条就是有一对没被量")
    }

    /// 那矩阵本身接对了吗（R198 的正对照，输入是**合成的纯色**，与产品梯子无关）。
    ///
    /// 为什么必须有这条：上面那条判据只压一根地板，而"模拟被写成恒等变换"时 16 条读数会**原封不动等于模拟前**、
    /// 照样全绿 —— 那等于整条轴没接电却替产品签了字（R198 第一版的量纲 bug 也是同一族：产品测试照样全绿，
    /// 只有 `99.60 > 65.00` 那个形状露了一下，肉眼可见但判据不可见）。⇒ 判据要能分辨
    /// "梯子在色盲下挺住了" 与 "我压根没模拟"，就得有一根**不依赖产品颜色**的尺。
    ///
    /// 钉两件事，都不设经验阈值：
    /// 1. **红↔绿 的分离必须小于 蓝↔黄 的分离**（deuteranopia 的定义性后果：红绿混、蓝黄不混）。
    ///    恒等变换给 255 < 255 ⇒ 红。
    /// 2. **中性灰是不动点**：三行的系数各自和为 1 ⇒ 灰进灰出。这条专治 R198 第一版漏掉重新编码的那一路
    ///    （蓝留线性时 (128,128,128) 被读成 (128,128,55)，漂移 73/255）—— 它是矩阵自己的恒等式，不是容差。
    func testDeuteranopiaSimulationMatrixIsWired() throws {
        func rgb(_ r: Int, _ g: Int, _ b: Int) -> NSColor {
            NSColor(srgbRed: CGFloat(r) / 255.0, green: CGFloat(g) / 255.0, blue: CGFloat(b) / 255.0, alpha: 1.0)
        }
        func plain(_ c: NSColor) throws -> (r: Double, g: Double, b: Double) {
            let s = try XCTUnwrap(c.usingColorSpace(.sRGB), "合成色转不成 sRGB ⇒ 这条正对照没在量任何东西")
            return (Double(s.redComponent), Double(s.greenComponent), Double(s.blueComponent))
        }
        func sim(_ c: NSColor) throws -> (r: Double, g: Double, b: Double) {
            try XCTUnwrap(Self.simulateDeuteranopia(c), "合成色过不了模拟 ⇒ 矩阵那一步根本没跑")
        }
        func maxDelta(_ a: (r: Double, g: Double, b: Double),
                      _ b: (r: Double, g: Double, b: Double)) -> Double {
            255.0 * max(abs(a.r - b.r), max(abs(a.g - b.g), abs(a.b - b.b)))
        }

        let red = rgb(255, 0, 0), green = rgb(0, 255, 0)
        let blue = rgb(0, 0, 255), yellow = rgb(255, 255, 0)
        let grey = rgb(128, 128, 128)

        let rgBefore = maxDelta(try plain(red), try plain(green))
        let rgAfter = maxDelta(try sim(red), try sim(green))
        let byBefore = maxDelta(try plain(blue), try plain(yellow))
        let byAfter = maxDelta(try sim(blue), try sim(yellow))
        let g0 = try plain(grey), g1 = try sim(grey)
        let greyDrift = max(abs(g1.r - g0.r), max(abs(g1.g - g0.g), abs(g1.b - g0.b))) * 255.0

        emit("SIM_MATRIX 红↔绿 前=\(String(format: "%.2f", rgBefore)) 后=\(String(format: "%.2f", rgAfter)) "
              + "| 蓝↔黄 前=\(String(format: "%.2f", byBefore)) 后=\(String(format: "%.2f", byAfter)) "
              + "| 灰 \(Self.inkString(g0))→\(Self.inkString(g1)) 漂移=\(String(format: "%.2f", greyDrift))")

        XCTAssertLessThan(rgAfter, byAfter,
            "红绿那一对模拟后差 \(String(format: "%.2f", rgAfter))，蓝黄那一对差 \(String(format: "%.2f", byAfter)) ⇒ "
            + "模拟没有把红绿混起来，等于没模拟（恒等变换的签名）。这时候上面那条产品判据的 16 条读数会正好等于模拟前，"
            + "全绿而毫无意义 —— 所以这条正对照不许跟着一起删。")
        XCTAssertLessThan(rgAfter, rgBefore,
            "红绿分离模拟后 \(String(format: "%.2f", rgAfter)) 没有比模拟前 "
                + "\(String(format: "%.2f", rgBefore)) 小 ⇒ deuteranopia 的定义性后果没发生，矩阵没接电。")
        XCTAssertGreaterThanOrEqual(byAfter, byBefore - Self.deutanBlueRowSlack255,
            "蓝黄分离从 \(String(format: "%.2f", byBefore)) 掉到 \(String(format: "%.2f", byAfter)) ⇒ "
            + "这不再是 deuteranopia（蓝黄那一对本来就该几乎不动），矩阵里混进了别的通道的系数。"
            + "这根容差不是拍的：它由矩阵自己的蓝行推出来 —— b' = 0.96 b + 0.04 g ⇒ 分离全压在蓝通道时最多丢 4%，"
            + "再加 8 位量化取整 1/255，上界就是 " + String(format: "%.1f", Self.deutanBlueRowSlack255) + "。"
            + "本轮实测 蓝↔黄 前后都是 255.00：那一对的分离其实压在**红**通道上（黄 r=255、蓝 r=0），一点没丢。")
        XCTAssertLessThanOrEqual(greyDrift, 2.0,
            "中性灰 \(Self.inkString(g0)) 过完模拟变成 \(Self.inkString(g1))，漂移 "
                + "\(String(format: "%.2f", greyDrift))/255 ⇒ 三行系数不再各自和为 1，或者某一路的量纲没统一"
                + "（R198 第一版就是把蓝通道留在线性域，那一次这条会给出 73）。灰必须是不动点，与产品颜色无关。"
                + "2.0 是这条**恒等式**的量化上界（行和恰为 1 ⇒ 数学上是 0，本轮实测漂移 0.00，只留幂函数往返与 8 位取整的余量），不是经验阈值。")
    }

    /// deuteranopia 矩阵蓝行 `b' = 0.96 b + 0.04 g` 允许的最大通道损失，换算到 0…255：
    /// 分离全压在蓝通道时是 4%，再加 8 位量化取整的 1/255。上面那条"蓝黄必须保住"的容差由它推出来，
    /// 免得将来有人把这根数当成拍脑袋的经验阈值去调。
    static let deutanBlueRowSlack255: Double = 255.0 * 0.04 + 1.0

    /// 三元组 → 日志里那个 `(r,g,b)`（0…255 取整）。只印调色板数字，不含任何用户内容。
    static func inkString(_ c: (r: Double, g: Double, b: Double)) -> String {
        "(\(Int((255.0 * c.r).rounded())),\(Int((255.0 * c.g).rounded())),\(Int((255.0 * c.b).rounded())))"
    }

    /// Viénot–Brettel–Fagot 1999 的 deuteranopia 近似：**线性域里乘矩阵，三通道一律重新编码回 sRGB**。
    ///
    /// 三通道同量纲是这条的命门。R198 第一版只在红/绿那两路做了 `encoded()`，蓝那一路直接返回线性值，
    /// 于是"最大通道差"会在不同格子里混着两种单位比：暗档低亮度区蓝通道被线性化**压缩**
    /// （encoded 0.1→0.2 在线性域只有 0.010→0.033），`空→第 1 档` 读成 10.41（假红，看着像产品塌了）；
    /// 而高亮度区线性化是**放大**的（0.85→1.0 的线性差 0.31 > 编码差 0.15），`第 3→第 4 档` 读出 99.60 > 模拟前 65.00，
    /// "模拟之后反而更分得开"这种物理上不可能的形状，就是同一颗尺两头用两种单位的证人。
    /// ⇒ 现在三通道走同一个 `encodeSRGB`，与 `pixelMaxChannelDelta` 同量纲，"模拟前/模拟后"才真能相除。
    static func simulateDeuteranopia(_ c: NSColor) -> (r: Double, g: Double, b: Double)? {
        guard let lin = linearSRGB(c) else { return nil }
        return (encodeSRGB(0.625 * lin.r + 0.375 * lin.g),
                encodeSRGB(0.700 * lin.g + 0.300 * lin.r),
                encodeSRGB(0.960 * lin.b + 0.040 * lin.g))
    }

    /// sRGB 解码到线性 RGB（矩阵必须在亮度线性域里乘，这是色觉模拟的标准做法）。
    /// 转换失败返回 nil，由调用方**计数**而不是 `continue` 混进均值。
    static func linearSRGB(_ c: NSColor) -> (r: Double, g: Double, b: Double)? {
        guard let s = c.usingColorSpace(.sRGB) else { return nil }
        func lin(_ v: CGFloat) -> Double {
            let x = Double(max(0.0, min(1.0, Double(v))))
            return x <= 0.04045 ? x / 12.92 : pow((x + 0.055) / 1.055, 2.4)
        }
        return (lin(s.redComponent), lin(s.greenComponent), lin(s.blueComponent))
    }

    /// 线性 → sRGB 编码，返回 0…1 的 Double（与 `pixelMaxChannelDelta` 的 `*255` 口径对齐）。
    static func encodeSRGB(_ v: Double) -> Double {
        let x = max(0.0, min(1.0, v))
        return x <= 0.0031308 ? x * 12.92 : 1.055 * pow(x, 1.0 / 2.4) - 0.055
    }

    /// 两格先各自过一遍色觉模拟，再取逐像素最大通道差的均值 —— 与 `meanMaxChannelDelta` 同一颗尺，
    /// 唯一的区别是中间多了那一步模拟（这样"模拟前/模拟后"两个数才是可比的）。
    /// 返回三元组：均值 + 真正被量的像素数 + 转换失败的像素数，后两者由判据自己钉住，
    /// 不让"有一片像素没换算出来"稀释成一次假绿或假红。
    static func meanMaxChannelDeltaSimulated(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                             over band: Set<Int>, size: Int)
        -> (delta: Double, sampled: Int, undecodable: Int) {
        guard !band.isEmpty else { return (-1, 0, 0) }   // 空带 = 没量，与上面那颗尺同一规矩给负数
        var total = 0.0
        var sampled = 0
        var undecodable = 0
        for index in band {
            let point = (x(of: index, size: size), y(of: index, size: size))
            guard let pa = a.colorAt(x: point.0, y: point.1),
                  let pb = b.colorAt(x: point.0, y: point.1) else { undecodable += 1; continue }
            guard let sa = simulateDeuteranopia(pa), let sb = simulateDeuteranopia(pb) else { undecodable += 1; continue }
            total += max(abs(sa.r - sb.r), max(abs(sa.g - sb.g), abs(sa.b - sb.b)))
            sampled += 1
        }
        guard sampled > 0 else { return (-1, 0, undecodable) }
        return (255.0 * total / Double(sampled), sampled, undecodable)
    }

    /// 填充带的均值墨色（整数 0…255 的 r,g,b + **alpha**）—— 判据交出它自己读过的那四个数，
    /// 这样"哪一根通道在撑这次判定"与"这一格到底是半透明还是已压平"在日志里都可查。
    /// 带上 alpha 是 R202 补的：真帧（落盘 PNG，alpha 恒 255）与这条判据（内存 rep）
    /// 对同一格给出的 R 差 6…21/255 而 G/B 只差 ≤1，两种解释（rep 带 alpha vs 色彩标签不同）
    /// 分别指向不同的修法 ⇒ 不许把任何一种写进台账当机制，先把 alpha 打出来。
    /// 只印调色板数字，不含任何用户内容。
    static func fillInk(_ render: NSBitmapImageRep, over band: Set<Int>, size: Int) -> String {
        guard !band.isEmpty else { return "无" }
        var r = 0.0, g = 0.0, b = 0.0, a = 0.0
        var n = 0
        for index in band {
            let point = (x(of: index, size: size), y(of: index, size: size))
            guard let c = render.colorAt(x: point.0, y: point.1)?.usingColorSpace(.sRGB) else { continue }
            r += Double(c.redComponent); g += Double(c.greenComponent)
            b += Double(c.blueComponent); a += Double(c.alphaComponent); n += 1
        }
        guard n > 0 else { return "读不到" }
        return "(\(Int((255.0 * r / Double(n)).rounded())),\(Int((255.0 * g / Double(n)).rounded())),"
            + "\(Int((255.0 * b / Double(n)).rounded())),\(Int((255.0 * a / Double(n)).rounded())))"
    }

    /// 相邻两档**必须分得开**（R54 / BACKLOG 71 / U-79 的后续）。
    ///
    /// 为什么这条要到 R54 才立：R45 量的是「悬停那一圈相对于整条数据范围响不响」，
    /// 从来没有量过「第 1 档与空格子能不能分开」。而这张图上**深浅是唯一的信息通道**，
    /// 相邻档分不开就等于那张日历少一档。
    ///
    /// **轴是这一条的全部难点，而且是本轮踩出来的**：
    /// R51/R53 我先用 Rec.709 亮度量，得到"暗档 空→第 1 档 只差 4/255"，
    /// 于是写下"0 次与 1 次分不开"。那是**用错轴**：`VisualHeat.empty` 走 `primary`（灰），
    /// 四档数据走 `accent`（蓝），那一步差的是**色相**不是明度 ——
    /// 同一对像素在 B 通道上差 30。⇒ 这里判的是**逐像素取三通道最大差**（`meanMaxChannelDelta`），
    /// 并且把三条轴（最大通道 / 均值通道 / 亮度）一起打出来，让"用哪根轴"这件事在日志里可审计。
    ///
    /// 地板沿用本仓库那把 `perceptibleBand255 = 18`（R45 从 20 条真读数推导出来的"看得出来"线），
    /// **不是新发明的数**。如果哪一档过不了，改的是产品的梯子或 `empty`（并同步 `frame_baseline update`），
    /// 不是把地板调低 —— 那是"为过夹具改判据"。
    func testAdjacentHeatLevelsAreSeparableOnTheRightAxis() throws {
        var readings: [String] = []
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for scale in [1, 2] {
                // 每一档画一次，相邻两档再两两比 —— 20 次渲染换 4 对 × 2 外观 × 2 尺度 = 16 条读数。
                let renders = try Self.levels.map {
                    try renderCell(level: $0, hovered: false, appearance: appearance, scale: scale)
                }
                let size = renders[0].pixelsWide
                let band = Self.fillBand(size: size, scale: scale)
                XCTAssertFalse(band.isEmpty, "\(tag)/\(scale)x 的填充带是空的 ⇒ 这条判据没在量任何东西")
                for i in 1..<Self.levels.count {
                    let a = Self.levels[i - 1], b = Self.levels[i]
                    let maxDelta = Self.meanMaxChannelDelta(renders[i - 1], renders[i], over: band, size: size)
                    let meanDelta = Self.meanChannelDelta(renders[i - 1], renders[i], over: band, size: size)
                    let lumaDelta = abs(Self.meanLuma(renders[i], over: band, size: size)
                                        - Self.meanLuma(renders[i - 1], over: band, size: size))
                    readings.append("HEAT_ADJACENT \(tag)/\(scale)x \(a.name)→\(b.name) "
                                    + "像素\(band.count) 最大通道差=\(String(format: "%.2f", maxDelta)) "
                                    + "均值通道差=\(String(format: "%.2f", meanDelta)) "
                                    + "亮度差=\(String(format: "%.2f", lumaDelta)) "
                                    + "令牌=\(String(format: "%.3f", a.opacity))→\(String(format: "%.3f", b.opacity))")
                    XCTAssertGreaterThanOrEqual(maxDelta, Self.adjacentLevelFloor255,
                        "\(tag)/\(scale)x 的 \(a.name)→\(b.name)：整格填充只变了 "
                        + "\(String(format: "%.2f", maxDelta))/255（最大通道那一根），低于地板 "
                        + "\(Self.adjacentLevelFloor255) ⇒ 这两档在屏幕上是一档，那张日历少一档。"
                        + "改 `VisualHeat.ladder`/`empty` 并同步帧基线，不许把地板调低")
                    // 地板必须钉在**最大通道**那一根上；这一格防的是"以后有人把判据换成亮度差"：
                    // 暗档那一步亮度差只有 4，换过去就等于把这条判据删掉。
                    XCTAssertGreaterThanOrEqual(maxDelta, meanDelta,
                        "最大通道差不小于均值通道差是这把尺的定义；反了说明取错了轴")
                }
            }
        }
        readings.forEach { emit($0) }
        XCTAssertEqual(readings.count, 16,
                       "读数必须是 4 对 × 2 外观 × 2 尺度 = 16 条，少一条就是有一对没被量")
    }

    /// 新尺子自己的真值表：`fillBand` 的归属，与"最大通道差"到底在量什么。
    ///
    /// 为什么单独立：上面那条判据的全部含义都在两件事上 ——
    /// ① 量的是**格子内部**（不是描边带、不是窗口底色）；
    /// ② 取的是**最大通道**而不是均值（灰→蓝那一步，均值会把 30 冲淡成 15）。
    /// 这两件事任何一件错，判据都会变成"看着有数、其实在量别的东西"。
    func testAdjacentLevelRulersAreATruthTable() throws {
        // ① 真实几何：11pt 格 + 每边 4pt 留白，2x ⇒ 边长 38、格子占中间 22。
        let scale = 2
        let size = (Int(VisualHeat.cell) + 8) * scale
        let inset = 4 * scale
        let cellPx = size - inset * 2
        let fill = Self.fillBand(size: size, scale: scale)
        let ring = Self.ringBand(size: size, scale: scale)
        XCTAssertFalse(fill.isEmpty, "填充带是空的 ⇒ 那条判据拿着 0 个像素算均值")
        XCTAssertGreaterThan(fill.count, cellPx * cellPx / 3,
                             "填充带不到格子的三分之一 ⇒ 它量的已经不是格子内部")
        XCTAssertTrue(fill.isDisjoint(with: ring),
                      "填充带与描边带重叠 ⇒ 悬停那一圈会混进相邻档的比较里")
        // R308 公开更正旧契约「两个带加起来要几乎等于整格」：那条说的是 strokeBorder 时代的
        // **互补分格**（环在格子里，两带分掉整格）。现在环在格子外面的留白里，
        // 两带加起来只到格子的绝大部分 —— 按旧式判它就是把产品事实读成尺子坏了。
        // 取而代之的是两条各自更强的等式：整格带必须是完整的 cellPx²（"悬停不许动数据像素"的分母），
        // 而描边带与整格必须**严格不相交**（环真在外面；一旦重叠就说明它又压回数据像素上）。
        let box = Self.cellBoxBand(size: size, scale: scale)
        let data = Self.cellDataBand(size: size, scale: scale)
        XCTAssertEqual(box.count, cellPx * cellPx,
                       "方框带不是 \(cellPx * cellPx) 个像素 ⇒ 分母自己就不完整")
        let radiusPx = Int(VisualRadius.heatCell) * scale
        XCTAssertLessThan(data.count, box.count,
                          "数据带等于方框 ⇒ 圆角那四个角被当成数据像素了（产品根本没在那儿落墨）")
        XCTAssertGreaterThanOrEqual(data.count, box.count - 4 * radiusPx * radiusPx,
                                    "数据带比方框少太多（\(box.count - data.count) 个）⇒ 形状带切错了地方")
        XCTAssertTrue(ring.isDisjoint(with: data),
                      "描边带与数据像素有交集 ⇒ 环还在压数据，而这条尺会把那一片同时算进「深浅」与「那一圈」")
        // ② 填充带里每个点都在格子框内、且离边界超过一条描边（SDF 比 -stroke 更负）。
        let half = Double(cellPx) / 2.0
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let radius = Double(Int(VisualRadius.heatCell) * scale)
        let outside = fill.filter {
            let x = Self.x(of: $0, size: size), y = Self.y(of: $0, size: size)
            return !(x >= inset && x < inset + cellPx && y >= inset && y < inset + cellPx)
        }
        XCTAssertTrue(outside.isEmpty, "填充带跑到格子框外 ⇒ 那一片是窗口底色，与深浅无关")
        let tooShallow = fill.filter {
            let dx = Double(Self.x(of: $0, size: size) - inset) + 0.5 - half
            let dy = Double(Self.y(of: $0, size: size) - inset) + 0.5 - half
            return Self.roundedRectSDF(px: dx, py: dy, half: half, radius: radius) > -strokePx - 0.5
        }
        XCTAssertTrue(tooShallow.isEmpty, "填充带压到了描边上 ⇒ 两档之差会被那一圈的抗锯齿污染")
        // ③ 轴：只有 B 通道差 30 的一对，**最大通道差=30**、均值通道差=10。
        //    这一格就是本轮那次纠错的钉：拿均值或亮度判"灰 vs 蓝"会低 3 倍。
        let gray = Self.flatRep(red: 41, green: 41, blue: 41, size: size)
        let blueish = Self.flatRep(red: 41, green: 41, blue: 71, size: size)
        let whole = Set(0..<(size * size))
        XCTAssertEqual(Self.meanMaxChannelDelta(gray, blueish, over: whole, size: size),
                       30, accuracy: 0.5, "最大通道差该读到 B 通道那 30")
        XCTAssertEqual(Self.meanChannelDelta(gray, blueish, over: whole, size: size),
                       10, accuracy: 0.5, "均值通道差会把 30 冲淡成 10 —— 这就是用错轴的样子")
        // ④ 同一张图自己比自己 = 0（非 0 说明取像素时行列错位）。
        XCTAssertEqual(Self.meanMaxChannelDelta(gray, gray, over: whole, size: size), 0, accuracy: 0.001)
        // ⑤ 空带必须返回**负数**（让它一定过不了地板），不许返回 0（那会被读成"量过了，差为 0"）。
        XCTAssertEqual(Self.meanMaxChannelDelta(gray, blueish, over: [], size: size), -1, accuracy: 0.001)
        // ⑥ 1× 退化几何：填充带还得非空，否则那一整臂什么都没量。
        XCTAssertFalse(Self.fillBand(size: Int(VisualHeat.cell) + 8, scale: 1).isEmpty,
                       "1× 屏上填充带是空的 ⇒ 那一臂在拿 0 像素算均值")
        XCTAssertTrue(Self.fillBand(size: 0, scale: 2).isEmpty)
        XCTAssertTrue(Self.fillBand(size: 8, scale: 2).isEmpty,
                      "留白吃掉整个边长 ⇒ 必须是空带，而不是把留白当格子")
    }

    /// 造一张纯色图当尺子的夹具（**直接写字节**）。
    ///
    /// 为什么不用 `setColor(_:atX:y:)`：R54 第一版用的就是它，两幅"不同色"的图量出来差是
    /// **0.00** —— 那条 API 在整数格式的位图上不落地（而且它不报错）。
    /// 尺子的夹具读到 0 时最容易被读成"没差别"，所以这里走 `bitmapData` 直写，
    /// 格式与 `renderCell` 出来的那张（deviceRGB / 8bit / RGBA）保持一致。
    static func flatRep(red: Int, green: Int, blue: Int, size: Int) -> NSBitmapImageRep {
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 4 * size, bitsPerPixel: 32)!
        guard let data = rep.bitmapData else {
            XCTFail("造不出纯色位图 ⇒ 尺子的真值表没有夹具")
            return rep
        }
        let bytesPerPixels = rep.bitsPerPixel / 8
        let row = rep.bytesPerRow
        for y in 0..<size {
            for x in 0..<size {
                let offset = y * row + x * bytesPerPixels
                data[offset] = UInt8(red)
                data[offset + 1] = UInt8(green)
                data[offset + 2] = UInt8(blue)
                data[offset + 3] = 255
            }
        }
        return rep
    }

    /// 格子**内部**那一片（描边带以外、格子框以内）。
    ///
    /// 与 `ringBand` 共用同一套几何与同一个半像素容差：两个带必须严格互补地分掉格子里的像素，
    /// 否则"悬停只改一圈"与"相邻两档差多少"量的会是两块互相渗透的地方。
    static func fillBand(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let radius = Double(Int(VisualRadius.heatCell) * scale)
        let half = Double(cellPx) / 2.0
        let allowance = 0.5
        var band = Set<Int>()
        for dy in 0..<cellPx {
            for dx in 0..<cellPx {
                let sdf = roundedRectSDF(px: Double(dx) + 0.5 - half,
                                         py: Double(dy) + 0.5 - half,
                                         half: half, radius: radius)
                guard sdf < -strokePx - allowance else { continue }
                band.insert((dy + inset) * size + (dx + inset))
            }
        }
        return band
    }

    /// 逐像素取**三通道最大差**再对带内取均值。
    ///
    /// 为什么不用现成的 `meanChannelDelta`：它把三通道平均掉，于是"只有 B 通道变了 30"
    /// 那种差（正是 `empty` 灰 vs `accent` 蓝那一步）会被冲淡成 10。
    /// 人眼对色相差的敏感度不会替我做这个平均。
    static func meanMaxChannelDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                    over band: Set<Int>, size: Int) -> Double {
        guard !band.isEmpty else { return -1 }   // 空带 = 没量 ⇒ 负数，让它一定过不了地板
        var total = 0.0
        for index in band { total += pixelMaxChannelDelta(a, b, index: index, size: size) }
        return total / Double(band.count)
    }

    static func pixelMaxChannelDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                     index: Int, size: Int) -> Double {
        let point = (x(of: index, size: size), y(of: index, size: size))
        guard let pa = a.colorAt(x: point.0, y: point.1),
              let pb = b.colorAt(x: point.0, y: point.1) else { return 0 }
        return max(abs(pa.redComponent - pb.redComponent),
                   max(abs(pa.greenComponent - pb.greenComponent),
                       abs(pa.blueComponent - pb.blueComponent))) * 255.0
    }

    /// 相邻两档的地板（0–255，**最大通道**那一根）。
    ///
    /// 沿用 R45 那把 `perceptibleBand255 = 18`，不新发明数：那条线是"看得出来"，
    /// 与这里要判的是同一件事（只是轴换对了）。
    static let adjacentLevelFloor255: Double = perceptibleBand255

    /// 带内「看得出来」的地板（0–255 均值通道差）。
    ///
    /// **不是拍的**：本轮第一遍实测 20 条 `HEAT_RING` 读数，最小的一条是
    /// `dark/1x bucket4 = 36.10`（最大 `light/2x empty = 75.50`）。
    /// 地板 = 最小读数的一半 = **18**：它抓的是「这一圈整个没了」，
    /// 不是抓「这一档比那一档淡一点」（后者是口味，交给 `VisualHeat.ladder` 那条梯子判据）。
    /// 与 `PressFeedbackTests.perceptibleStep255 = 4`（大平面恰可察觉台阶）**同源但不同值**：
    /// 那是铺满一块控件的底色差，这是一条 1pt 的带 —— 视觉系统对轮廓更敏感，
    /// 拿大平面的地板判一条带会用错尺度。
    ///
    /// 顺带记一条本轮学到的：**1× 那一臂比 2× 系统性低 20%–25%**
    /// （bucket4：46.04 → 36.72；empty：75.50 → 59.54）。
    /// 也就是说"发丝线在非 Retina 屏上会消失"那句注释**方向是对的**，只是量级远没到看不见。
    /// 这一条只有把 1× 单独当一臂量才看得见 —— 第一版只量 2×，那批读数会一律偏高 20%。
    static let perceptibleBand255: Double = 18

    /// 「悬停不许比数据响」的允许倍率。1.0 的意思很直白：
    /// 鼠标划过的像素变化，最多等于这张图从"没复制"到"最忙"的全部幅度。
    /// 再往上就不是"指出哪一格"，是"这一格比所有格子的深浅加起来还重要"。
    static let louderThanDataAllowed: Double = 1.0

    /// 带外允许的噪声上限。实测是 **0.00/255**（10 条 `HEAT_RING_CONFINEMENT` 读数全为 0，
    /// 位置 (0,0) 那个"最坏点"其实是"从没找到过变化点"的初值）。
    /// 但地板不能写成 0：抗锯齿在第 8 位上就会把分类器淹掉（账本里那一族），
    /// 留 3/255 ≈ 一个 8bit 量化台阶的三倍，既放过噪声又抓得住"整格都变了"。
    static let outsideBandTolerance255: Double = 3

    // MARK: - 档位

    /// 这张图上所有**不同的画法**：空档走 `primary.opacity(empty)`，
    /// 其余四档走 `accent.opacity(ladder[i])`。五档就是全部，因为深浅只有这五种。
    struct Level {
        let name: String
        let count: Int
        let bucket: Int
        var opacity: Double { count == 0 ? VisualHeat.empty : VisualHeat.opacity(bucket: bucket) }
    }

    static let levels: [Level] = [
        Level(name: "empty", count: 0, bucket: 0),
        Level(name: "bucket1", count: 3, bucket: 1),
        Level(name: "bucket2", count: 8, bucket: 2),
        Level(name: "bucket3", count: 17, bucket: 3),
        Level(name: "bucket4", count: 40, bucket: 4),
    ]

    // MARK: - 渲染

    /// 把产品那一格画在**窗口底色**上（hovered 真/假各一次）。
    ///
    /// 刻意走 `NSHostingView` + `cacheDisplay`（与帧夹具同一套机器），而不是在 Core Graphics
    /// 里手搓一个「长得像」的圆角方块 —— 后者测的是替身
    /// （`PressFeedbackTests` 的 `renderFill` 开头那句是同一个理由）。
    private func renderCell(level: HeatmapHoverEvidenceTests.Level,
                            hovered: Bool,
                            appearance: NSAppearance.Name,
                            scale: Int) throws -> NSBitmapImageRep {
        let cell = DailyCopyHeatPolicy.Cell(dayKey: "2026-10-11",
                                           date: Date(timeIntervalSince1970: 1_760_000_000),
                                           isFuture: false,
                                           count: level.count,
                                           bucket: level.bucket)
        // `NSApp` 在这个套件里可能是 nil（`PressFeedbackTests` 为此崩过一次，信号 5 不是「没跑」）。
        let app = NSApplication.shared
        let previous = app.appearance
        app.appearance = NSAppearance(named: appearance)
        defer { app.appearance = previous }

        // 四周留 4pt：让描边带离位图边缘有距离，「带外」里才真的有底色与格间距可量。
        let side = Int(VisualHeat.cell) + 8
        let renderSize = NSSize(width: side, height: side)
        let pixels = side * scale
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil,
                                   pixelsWide: pixels, pixelsHigh: pixels,
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 0, bitsPerPixel: 0)!
        rep.size = renderSize
        let root = AnyView(
            ZStack {
                Color(nsColor: .windowBackgroundColor)
                DailyCopyHeatmapCell(cell: cell, isHovered: hovered,
                                     calendar: Calendar(identifier: .gregorian)) { _ in }
                    .frame(width: VisualHeat.cell, height: VisualHeat.cell)
            }
            .frame(width: renderSize.width, height: renderSize.height)
        )
        let host = NSHostingView(rootView: root)
        host.frame = NSRect(origin: .zero, size: renderSize)
        host.appearance = NSAppearance(named: appearance)
        host.cacheDisplay(in: NSRect(origin: .zero, size: renderSize), to: rep)
        return rep
    }

    // MARK: - 纯函数（分类器本体，可以直接喂坐标测）

    /// 描边带 = 落在 `strokeBorder` 实际覆盖的那一圈里的像素。
    ///
    /// 用**圆角矩形的符号距离**（SDF）判，不用「离边小于 strokePx 的方框减掉角块」：
    /// 第一版就是后者，它当场把这条判据打红了 —— 半径 2pt、2x ⇒ 角块是 4×4 个像素，
    /// 而描边在角上正好穿过那块，于是**真描边像素被当成角排除掉**，
    /// 「带外不许变」那条判据就把它们报成"越界"（读数 113/255，位置 (10,9)）。
    /// 这是账本里"框套在别的真实文字上报假 ✓"的反面：**框切在了真东西上面，报的是假 ✗**。
    /// SDF 一上来两件事同时对了：角上的描边像素算带内，格子内部与形外底色算带外。
    ///
    /// 返回**压平后的下标**（`y * size + x`）：带要被 `contains` 查两万次，
    /// 而元组不能 `Hashable`（Swift 只给未命名元组合成一致性）。
    /// 悬停那一圈**实际落在哪里**：R308 起在格子**外面**的留白里 ——
    /// 产品画的是「把圆角矩形放大 `hoverRingGap` 再描 `hoverStroke`」，
    /// 所以这条带 = 外径那一圈的 SDF ∈ [−w/2−容差, +w/2+容差]。
    ///
    /// 旧版切的是格子**里面**的一圈，因为那时产品用 `strokeBorder`（画在形状内侧）。
    /// **带的定义必须跟着被测物走**：产品换画法之后把带留在原地，量到的就是"环画过的那片空白"，
    /// 读数为 0 会被读成"环没了"（假红），或读数为大会被读成"环很响"（假绿）。
    static func ringBand(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let gapPx = Double(Int(VisualHeat.hoverRingGap) * scale)
        // 产品画的是「半径跟着外扩」的圆角矩形（`heatCell + gap`）—— 只有那样这一圈与格子才**同心**，
        // 直角边与 45° 角上的间距才都是 gap。尺子必须照抄这一点，否则角上量的会是别处。
        let radius = Double(Int(VisualRadius.heatCell + VisualHeat.hoverRingGap) * scale)
        let cellHalf = Double(cellPx) / 2.0
        let outerHalf = cellHalf + gapPx
        // 容差取 0.4（不是 0.5）：描边的几何覆盖正好落在 `|SDF| ≤ stroke/2`，
        // 半像素容差会把**零覆盖**的那一行也算进带里（2x 上就是 y=4 与 y=7），
        // 均值被稀释 ⇒ 可见性地板会红在尺子上。这一条由
        // `testRingBandSelectorIsATruthTable` 的第④b 格按行号点验。
        let allowance = Self.ringBandAllowance
        var band = Set<Int>()
        // 像素坐标一律相对**格子的中心**（外径与格子同心 —— `.padding` 是四边等量外扩）。
        // 第一版这里减的是 `inset + outerHalf`，等于把中心也往外推了一个 gap ⇒ 带整体偏移 2 个
        // 设备像素：真正的 halo 被算成"带外"，而带里混进的是没画的像素。
        // 这条偏移由下面 `testRingBandSelectorIsATruthTable` 的第④格钉住（它按行号点验带的位置）。
        for py in 0..<size {
            for px in 0..<size {
                let sdf = roundedRectSDF(px: Double(px) + 0.5 - Double(inset) - cellHalf,
                                         py: Double(py) + 0.5 - Double(inset) - cellHalf,
                                         half: outerHalf,
                                         radius: radius)
                guard abs(sdf) <= strokePx / 2.0 + allowance else { continue }
                band.insert(py * size + px)
            }
        }
        return band
    }

    /// **格子的方框**（cellPx² 个像素，含圆角切掉的那四个角）。只用来量"分母自己完不完整"。
    static func cellBoxBand(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        var band = Set<Int>()
        for dy in 0..<cellPx {
            for dx in 0..<cellPx {
                band.insert((dy + inset) * size + (dx + inset))
            }
        }
        return band
    }

    /// **数据像素** = 格子**真的画出来的**那一片（圆角矩形以内）。
    ///
    /// 为什么不是方框：`VisualRadius.heatCell` 把四个角切掉了，角上那几个像素是**背景**，
    /// 产品从来没在那里落过数据的墨。第一版拿方框当数据，于是"环不许动数据像素"这条尺
    /// 会在角上冤枉环 —— 实测 halo 与方框在角上重叠 4 个像素，而产品在那 4 个像素上
    /// 一个数据像素都没画。同心 halo 到格子边的距离是 gap，到**形状**边才是常数。
    static func cellDataBand(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        let radius = Double(Int(VisualRadius.heatCell) * scale)
        let half = Double(cellPx) / 2.0
        var band = Set<Int>()
        for dy in 0..<cellPx {
            for dx in 0..<cellPx {
                let sdf = roundedRectSDF(px: Double(dx) + 0.5 - half,
                                         py: Double(dy) + 0.5 - half,
                                         half: half, radius: radius)
                guard sdf < 0 else { continue }
                band.insert((dy + inset) * size + (dx + inset))
            }
        }
        return band
    }

    /// 圆角矩形 SDF：形内为负、形外为正、边界为 0（标准写法，`b = half - r` 那一支）。
    static func roundedRectSDF(px: Double, py: Double, half: Double, radius: Double) -> Double {
        let b = max(half - radius, 0)
        let qx = max(abs(px) - b, 0)
        let qy = max(abs(py) - b, 0)
        return hypot(qx, qy) + min(max(qx, qy), 0) - radius
    }

    static func x(of index: Int, size: Int) -> Int { index % size }
    static func y(of index: Int, size: Int) -> Int { index / size }

    static func meanChannelDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                 over band: Set<Int>, size: Int) -> Double {
        guard !band.isEmpty else { return -1 }   // 空带 = 没量 ⇒ 返回负数，让它一定过不了地板
        var total = 0.0
        for index in band { total += pixelChannelDelta(a, b, index: index, size: size) }
        return total / Double(band.count)
    }

    static func pixelChannelDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                  index: Int, size: Int) -> Double {
        let point = (x(of: index, size: size), y(of: index, size: size))
        guard let pa = a.colorAt(x: point.0, y: point.1),
              let pb = b.colorAt(x: point.0, y: point.1) else { return 0 }
        return (abs(pa.redComponent - pb.redComponent)
                + abs(pa.greenComponent - pb.greenComponent)
                + abs(pa.blueComponent - pb.blueComponent)) / 3.0 * 255.0
    }

    static func meanLuma(_ rep: NSBitmapImageRep, over band: Set<Int>, size: Int) -> Double {
        guard !band.isEmpty else { return -1 }
        var total = 0.0
        for index in band {
            guard let p = rep.colorAt(x: x(of: index, size: size), y: y(of: index, size: size)) else { continue }
            total += 0.299 * p.redComponent + 0.587 * p.greenComponent + 0.114 * p.blueComponent
        }
        return total / Double(band.count) * 255.0
    }

    /// 按**完整串**数出现次数（不是前缀匹配）。
    static func occurrences(of needle: String, in source: String) -> Int {
        source.components(separatedBy: needle).count - 1
    }

    private func harnessSourceOfFile(_ name: String) throws -> String {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // Tests/ClipboardHistoryAppTests/
            .deletingLastPathComponent()   // Tests/
            .deletingLastPathComponent()   // ClipboardHistory/
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views")
            .appendingPathComponent(name)
        return try String(contentsOf: root, encoding: .utf8)
    }
}
