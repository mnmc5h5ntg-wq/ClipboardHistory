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
        readings.forEach { print($0) }
        XCTAssertEqual(readings.count, 20, "读数条数必须是 外观2 × 采样率2 × 档5，少一条就是有一档没被量")
    }

    /// 悬停**只**改描边那一条带：格子内部、格间距、页面底色都不许被这圈墨碰到。
    ///
    /// 这条是上一半的反面，也是「不喧宾夺主」的可数版本：
    /// 如果悬停会推着别的像素一起变（比如实现成了「整格换色」或「带阴影」），
    /// 那 126 格之间读起来就不是「哪一格被指着」，而是「一片都在亮」。
    func testHoverChangesOnlyTheRingBand() throws {
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for level in Self.levels {
                let still = try renderCell(level: level, hovered: false, appearance: appearance, scale: 2)
                let hover = try renderCell(level: level, hovered: true, appearance: appearance, scale: 2)
                let size = still.pixelsWide
                let band = Self.ringBand(size: size, scale: 2)
                var worst: (index: Int, delta: Double) = (-1, 0)
                for index in 0..<(size * size) where !band.contains(index) {
                    let d = Self.pixelChannelDelta(still, hover, index: index, size: size)
                    if d > worst.delta { worst = (index, d) }
                }
                print("HEAT_RING_CONFINEMENT \(tag) \(level.name) 带外最大变化="
                      + "\(String(format: "%.2f", worst.delta))/255"
                      + " @(\(Self.x(of: max(worst.index, 0), size: size)),"
                      + " \(Self.y(of: max(worst.index, 0), size: size)))")
                XCTAssertLessThanOrEqual(worst.delta, Self.outsideBandTolerance255,
                    "\(tag) 的 \(level.name)：带外有一处变了 \(String(format: "%.2f", worst.delta))/255"
                        + "，位置 (\(worst.index % size), \(worst.index / size)) ⇒ "
                        + "这一圈不止改了描边（喧宾夺主那一族）")
            }
        }
    }

    /// 「不喧宾夺主」那一半：**悬停那一下不许比这张图全部的数据幅度还响**。
    ///
    /// 这条是本轮看图之前没想到的，是那批读数逼出来的（实测，2x）：
    /// 亮色下鼠标划过一个**空格**，那一条带变了 `75.50/255`，
    /// 而这张图从"一次都没复制"到"最忙的一天"的全部幅度是 `100.92/255` —— 倍率 0.75。
    /// 也就是说悬停已经**接近**数据全幅度了：再重一档就会盖过深浅本身。
    /// 一张以深浅为唯一信息通道的图，交互层不许爬到数据层上面去，所以这里判 ≤ 1.0 倍。
    ///
    /// 轴要说清楚：比的是**同一批像素上的通道差**，不是"谁面积大"。
    /// 分母取 empty↔bucket4 这两端，因为那是这张图能画出的最大数据差；
    /// 若哪天 `ladder` 改了，分母跟着改（它不是常数，这正是它比"写死一个 100"好的地方）。
    func testHoverIsNotLouderThanTheDataRange() throws {
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            let band = Self.ringBand(size: (Int(VisualHeat.cell) + 8) * 2, scale: 2)
            let empty = try renderCell(level: Self.levels[0], hovered: false,
                                       appearance: appearance, scale: 2)
            let busiest = try renderCell(level: Self.levels[Self.levels.count - 1], hovered: false,
                                         appearance: appearance, scale: 2)
            let dataRange = Self.meanChannelDelta(empty, busiest, over: band,
                                                  size: empty.pixelsWide)
            for level in Self.levels {
                let still = try renderCell(level: level, hovered: false,
                                           appearance: appearance, scale: 2)
                let hover = try renderCell(level: level, hovered: true,
                                           appearance: appearance, scale: 2)
                let step = Self.meanChannelDelta(still, hover, over: band, size: still.pixelsWide)
                let ratio = dataRange > 0 ? step / dataRange : -1
                print("HEAT_LOUDNESS \(tag) \(level.name) 悬停差=\(String(format: "%.2f", step))"
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

    /// 分类器自己的真值表：带 = `strokeBorder` 实际覆盖的那一圈（SDF 判）。
    ///
    /// 为什么单独立：上面两条判据的全部含义都在「哪些像素算这条带」上。
    /// 带里混进底色像素，就会把「圈没画上」读成「圈画上了」；带里混进格子内部像素，
    /// 则会把「整格都在变」读成合规。而**带切掉了真描边**（本轮第一版干的就是这件事）
    /// 会让"悬停只改这一圈"报出一条根本不存在的缺陷 —— 这一族比假 ✓ 更浪费轮次。
    ///
    /// 坐标一律**从几何算出来**，不写死 22 这种数：写死一次，改了留白之后这一格就悄悄量的是别的地方。
    func testRingBandSelectorIsATruthTable() {
        // ① 真实几何：11pt 格 + 每边 4pt 留白，2x ⇒ 边长 38、格子占中间 22。
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
        // ② 带里每个点都在格子框内（描边是 `strokeBorder`，画在形状**里面**）。
        let outsideBox = band.filter {
            let x = Self.x(of: $0, size: size), y = Self.y(of: $0, size: size)
            return !(x >= inset && x < inset + cellPx && y >= inset && y < inset + cellPx)
        }
        XCTAssertTrue(outsideBox.isEmpty, "带跑到了格子框外 ⇒ 那一片是窗口底色，量出来的差与那一圈无关")
        // ③ 带里没有一个点**压不到边界**：每个点到圆角矩形边界的距离都小于 stroke + 容差。
        //    这一格就是把第一版打红的那一格的反面守卫（第一版用的是方框减角块）。
        let half = Double(cellPx) / 2.0
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let radius = Double(Int(VisualRadius.heatCell) * scale)
        let tooDeep = band.filter {
            let dx = Double(Self.x(of: $0, size: size) - inset) + 0.5 - half
            let dy = Double(Self.y(of: $0, size: size) - inset) + 0.5 - half
            return Self.roundedRectSDF(px: dx, py: dy, half: half, radius: radius) < -strokePx - 0.5
        }
        XCTAssertTrue(tooDeep.isEmpty, "带伸进了格子内部 \(tooDeep.count) 个像素 ⇒ 「整格换色」会被读成合规")
        // ④ 四条边都得有人，**四个角也得有人**。
        //    角那一半就是本轮的靶：`strokeBorder` 沿圆角走，真描边在角上是连续的，
        //    旧版按「离边小于 stroke 的方框减角块」切，把角上的真描边切掉了。
        let edges = [
            ("左边", band.filter { Self.x(of: $0, size: size) == inset }.count),
            ("右边", band.filter { Self.x(of: $0, size: size) == inset + cellPx - 1 }.count),
            ("上边", band.filter { Self.y(of: $0, size: size) == inset }.count),
            ("下边", band.filter { Self.y(of: $0, size: size) == inset + cellPx - 1 }.count),
        ]
        for (name, count) in edges {
            XCTAssertGreaterThan(count, 0, "\(name)一个像素都没有 ⇒ 这条带判不了那一边的圈")
        }
        let corners = [
            ("左上", band.filter { Self.x(of: $0, size: size) <= inset + 2 && Self.y(of: $0, size: size) <= inset + 2 }.count),
            ("右上", band.filter { Self.x(of: $0, size: size) >= inset + cellPx - 3 && Self.y(of: $0, size: size) <= inset + 2 }.count),
            ("左下", band.filter { Self.x(of: $0, size: size) <= inset + 2 && Self.y(of: $0, size: size) >= inset + cellPx - 3 }.count),
            ("右下", band.filter { Self.x(of: $0, size: size) >= inset + cellPx - 3 && Self.y(of: $0, size: size) >= inset + cellPx - 3 }.count),
        ]
        for (name, count) in corners {
            XCTAssertGreaterThan(count, 0, "角区 \(name) 一个带像素都没有 ⇒ 描边在角上被切掉了（第一版的毛病）")
        }
        // ⑤ 1× 屏（格宽就是 11 个设备像素）：带还得非空，四条边也得有人。
        //    这一格不是凑数 —— 若选择器在「带宽 ≈ 描边宽」这种退化几何上返回空，
        //    1× 那条判据臂会拿着 0 像素的均值「通过」。
        let oneXSize = Int(VisualHeat.cell) + 8
        let oneX = Self.ringBand(size: oneXSize, scale: 1)
        XCTAssertFalse(oneX.isEmpty, "1× 屏上带是空的 ⇒ 那一整臂什么都没量")
        let oneXEdges = [
            oneX.filter { Self.x(of: $0, size: oneXSize) == 4 }.count,
            oneX.filter { Self.x(of: $0, size: oneXSize) == 4 + 11 - 1 }.count,
            oneX.filter { Self.y(of: $0, size: oneXSize) == 4 }.count,
            oneX.filter { Self.y(of: $0, size: oneXSize) == 4 + 11 - 1 }.count,
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
        XCTAssertEqual(VisualHeat.hoverRingOpacity(isHovered: true), 0.55, accuracy: 0.0001,
                       "悬停那一圈的透明度是本轮量出来的那个数，改了令牌就得同时改判据里的说明")
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
        let draws = Self.occurrences(of: ".strokeBorder(Color.primary.opacity(VisualHeat.hoverRingOpacity",
                                     in: source)
        XCTAssertEqual(draws, 1, "悬停那一圈的画法出现 \(draws) 次 ⇒ 有两份会分叉的真值")
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
        print("HEAT_STRIP n=\(cells.count) 可画=\(drawable.count) "
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
    static func ringBand(size: Int, scale: Int) -> Set<Int> {
        guard size > 0, scale > 0 else { return [] }
        let inset = 4 * scale
        let cellPx = size - inset * 2
        guard cellPx > 0 else { return [] }
        let strokePx = Double(max(1, Int(VisualHeat.hoverStroke) * scale))
        let radius = Double(Int(VisualRadius.heatCell) * scale)
        let half = Double(cellPx) / 2.0
        // `strokeBorder` 画在形状**里面**：带 = SDF ∈ [-stroke, 0]。
        // 留半像素容差给抗锯齿（容差 0 会让分类器判在噪声上，账本里有这一族）。
        let allowance = 0.5
        var band = Set<Int>()
        for dy in 0..<cellPx {
            for dx in 0..<cellPx {
                let sdf = roundedRectSDF(px: Double(dx) + 0.5 - half,
                                         py: Double(dy) + 0.5 - half,
                                         half: half,
                                         radius: radius)
                guard sdf <= allowance, sdf >= -strokePx - allowance else { continue }
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
