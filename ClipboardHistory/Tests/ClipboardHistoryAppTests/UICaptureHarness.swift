import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 离屏渲染真实视图，产出 PNG 供肉眼审计 —— 不依赖屏幕录制授权，
/// 也不受"后台窗口动画时间线冻结"影响（那两类都会给出假空白帧）。
///
/// 用法：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`
/// 未设置该环境变量时整个套件 skip，不拖慢普通测试。
///
/// 三条防"假证据"的规矩（都来自踩过的坑）：
/// 1. 每帧都量化"未被绘制的像素比例"并打印。`cacheDisplay` 不会画 AppKit
///    滚动视图/分栏的底，未合成前暗色帧会呈现"白底 + 透明"，肉眼看就是
///    "详情区空白"的假缺陷。现在统一铺一层真实窗口底色再写 PNG。
/// 2. 比例超过 95% 直接判失败：那意味着整帧基本没画出来，不能当验收证据。
/// 3. 拍暗色时把 NSApp.appearance 一起改掉。只注入 `colorScheme` 的话，
///    List 这类 AppKit 承载控件仍按 aqua 取色，会拍出"深底黑字"的假不可读帧。
@MainActor
final class UICaptureTests: XCTestCase {
    /// 夹具时间戳的固定参考时刻（账本 R2-19）。
    ///
    /// 以前这里用 `Date()`：行里显示的时间会随真实时钟走，于是**跨分钟连拍两次，
    /// 时钟字符串自己就在变像素** —— 逐帧对比里混进一层与代码无关的差异
    /// （11pt 字号那轮 row 帧 3.3–13% 的差异里就有它）。固定之后，两帧的差异才只反映代码改动。
    static let referenceDate = Date(timeIntervalSince1970: 1_760_000_000)

    /// "未被绘制"的判定阈值，**两个读者共用同一把尺**：
    /// ①`testCaptureKeyViews` 里那条"有 N% 像素未被绘制即判捕获失效"的守卫；
    /// ②`testQuickPickOverlayCannotBeCapturedYet` 那条"浮层还拍不到"的判据。
    ///
    /// 为什么要是同一个常量：这两处其实在回答同一个问题（"这张帧到底画没画"）。
    /// 各写一个数字的话，某天把守卫松到 0.98 而判据还留在 0.9 ——
    /// 于是浮层那三张帧能被"拍出来"（不再触发守卫）却仍然全透明（判据也测不出它变没变），
    /// 而看起来像"补帧成功"。同一个阈值意味着这两件事只能一起变。
    static let transparentAlphaCeiling: UInt8 = 8

    /// alpha 小于 `transparentAlphaCeiling` 的像素占比。按行扫，`bytesPerRow` 由调用方给
    /// （位图缓存可能有 padding，硬写 `width * 4` 会读错行）。
    static func transparentFraction(bytes: UnsafePointer<UInt8>,
                                   width: Int, height: Int, bytesPerRow: Int) -> Double {
        var clear = 0
        var total = 0
        var y = 0
        while y < height {
            let row = y * bytesPerRow
            var x = 0
            while x < width {
                total += 1
                if bytes[row + x * 4 + 3] < transparentAlphaCeiling { clear += 1 }
                x += 1
            }
            y += 1
        }
        return Double(clear) / Double(max(total, 1))
    }

    /// 从位图缓存直接量。拿不到字节时返回 1.0 —— **按"整张没画"处理**，
    /// 而不是 0.0（那会把"量不到"伪装成"画满了"，正是这一族最常见的假绿）。
    static func transparentFraction(of rep: NSBitmapImageRep) -> Double {
        guard let base = rep.bitmapData else { return 1.0 }
        return transparentFraction(bytes: base,
                                  width: rep.pixelsWide,
                                  height: rep.pixelsHigh,
                                  bytesPerRow: rep.bytesPerRow)
    }

    /// 正对照帧：一张**已知底边有墨**的帧（列表在帧底被切一半是它的正常行为）。
    /// 存在的理由与 `materialBlindSpotFixtures` 同一族 —— 一把只在"该红的没红"上被检验的尺
    /// 没有被检验过；R22 这条 `contentMustFit` 的十张对照全读 0.0%，
    /// 所以必须有一张读得到墨的，否则"把阈值调到 100000"不会有任何测试红。
    static let bottomEdgeInkCanary = "sidebar-history"

    /// 已知"有一块材质在离屏窗口里画成纯黑"的夹具名单（R18 实测，逐帧量出来的，不是猜的）。
    ///
    /// 成因：系统 `List` 的**选中高亮**由 AppKit 画（账本 D-034 之后行自己不再画底色），
    /// 而那块底色是材质；没上过屏的窗口没有可合成的背景层 ⇒ 拍出来是 #000 的圆角块，
    /// 亮色暗色都一样。实测它**正好盖住被选中的那几行**：`sidebar-history`（1 行选中）
    /// 黑带 66pt，`sidebar-multi-select`（3 行选中）168pt —— 高度随选中行数增长，不是随机噪声。
    ///
    /// 这份名单存在的理由：`FRAME_BASELINE_CHANGED=0` 在这些帧上**不等于**"选中态被看着"。
    /// 选中是用户点名要审的状态之一，而它一直是量不到的 —— 先让它能被数出来，再想办法拍到。
    static let materialBlindSpotFixtures: Set<String> = [
        "content-with-history", "content-min", "content-wide", "content-with-notice",
        "content-with-two-notices",
        "sidebar-history", "sidebar-multi-select", "sidebar-multi-select-min", "sidebar-favorites",
    ]

    /// 从帧文件名还原夹具名：`sidebar-history-300x520-dark.png` → `sidebar-history`。
    static func fixtureName(fromFile file: String) -> String {
        let base = (file as NSString).deletingPathExtension
        guard let range = base.range(of: "-\\d+x\\d+-", options: .regularExpression) else { return base }
        return String(base[..<range.lowerBound])
    }

    /// 一帧的量尺结果：**画没画出来** + **有没有一块材质在离屏下画成纯黑**
    /// + **最底一行有多少墨**（夹具裁内容的信号）。
    struct CaptureMetrics {
        let transparent: Double
        /// 连续若干行里 ≥60% 像素是纯黑 ⇒ 认为这是一块**填充**（不是一行文字）。
        /// 返回这条填充带的最大高度，单位 pt。
        let blackBandPt: Double
        /// 最后一行里"偏离主色 >12"的像素占比。
        ///
        /// 为什么看**最后一行**：夹具把内容裁掉时，被切成半截的字形/边框一定压在底边上；
        /// 而一张"内容刚好放得下"的帧，底边应该是留白。
        /// 这条只给 `contentMustFit` 那批夹具用 —— 列表/滚动区那批**天生**会被裁，
        /// 判它们等于把"滚动视图的正常行为"报成缺陷（这正是 R18 没敢立这条守卫的原因）。
        let bottomInkFraction: Double
    }

    /// 纯黑填充带的最大高度（pt）。
    ///
    /// 为什么要量它：系统 `List` 的**选中高亮**是一块材质，而材质在没上过屏的窗口里
    /// 不可合成 —— 于是它画成一片纯黑（亮色、暗色都一样）。这类帧看着"有内容"，
    /// 实际上选中态那一行是黑的：文字压在黑底上，颜色、对比度、圆角、内边距
    /// **一个都没被量到**。以前这类事只能靠人眼在 96 张里翻，翻到算运气；
    /// 现在每张帧都报一个数，名单钉在判据里（见 `testCaptureKeyViews`）。
    ///
    /// 判据用**绝对宽度**而不是"这一行有百分之六是黑的"：
    /// 第一版用占比 60%，于是 `content-*` 那三张漏了 —— 选中块在 750pt 的帧里只占
    /// 侧栏那 250pt（33%），整行占比过不了 60% 的线，一块明明存在的黑被读成了 0。
    /// 改成"连续黑像素 ≥60pt"之后，块再窄也认得出来，而一行文字里最长的黑段
    /// 只是一个字形的笔画（1–2pt），离 60pt 很远。
    static func blackBandHeight(bytes: UnsafePointer<UInt8>,
                                width: Int, height: Int, bytesPerRow: Int,
                                backingScale: CGFloat,
                                minRunPt: Double = 60) -> Double {
        let minRun = max(Int(minRunPt * Double(backingScale)), 1)
        var bestRun = 0
        var run = 0
        var y = 0
        while y < height {
            let row = y * bytesPerRow
            var longest = 0
            var current = 0
            var x = 0
            while x < width {
                let o = row + x * 4
                // 三个通道都 <8 且**不透明**：透明的黑是"没画"，由 `transparentFraction` 管。
                if bytes[o] < 8, bytes[o + 1] < 8, bytes[o + 2] < 8, bytes[o + 3] > 240 {
                    current += 1
                    longest = max(longest, current)
                } else {
                    current = 0
                }
                x += 1
            }
            if longest >= minRun {
                run += 1
                bestRun = max(bestRun, run)
            } else {
                run = 0
            }
            y += 1
        }
        return Double(bestRun) / Double(max(backingScale, 0.001))
    }

    private enum CaptureError: Error {
        case noBitmap
        case noPNG
        /// R18：AppKit 夹具建不出视图。已经 XCTFail 过了，抛这个错只是为了**不再往下拍**
        /// —— 继续拍会得到一张空窗，而它会被当成基线钉住。
        case emptyAppKitFixture
    }

    private var outputDirectory: URL? {
        guard let path = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"], !path.isEmpty else {
            return nil
        }
        let url = URL(fileURLWithPath: path, isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    /// 浮层**还是**拍不到，但 R18 写下的那句原因是错的 —— 这条判据把原因钉成实测数字（R19 / U-41）。
    ///
    /// R18 记的根因是"浮层背景是 `NSVisualEffectView`，离屏没有可合成层"。两半都被推翻：
    /// ① 读代码：`ensurePanel()` 里根本没有材质视图 —— 普通 contentView +
    ///    `drawsBackground=false` 的滚动视图 + `backgroundColor=.clear` 的表格；
    /// ② 做实验：裸 `NSVisualEffectView` 离屏**画得出来**（spike 读数 `mid=(58,58,58,a=255)`）。
    /// 真正的现象（这一条是量出来的，不是猜的）：产品的 `NSStackView` 在捕获环境里
    /// 是 **24×49**（真实 App 里它撑满 420×300），于是 `NSScrollView` 0×0、
    /// `NSTableView.visibleRect` 0×0 —— 表格有 5 行，一行都画不出来。
    ///
    /// 三层断言各管一件事，红得不一样的时候读的是不同的话：
    ///   · `rows > 0` 守**所有权**：`NSTableView.dataSource` 是弱引用，控制器一旦被释放，
    ///     行数静默掉成 0，而帧仍然"合法"（见 `QuickPickCapturePanel`）；
    ///   · `transparent > 0.9` 是标题：还能不能拍。它红了就去补那三张夹具；
    ///   · 补一条**原因**断言：拍不到时必须仍然是 stack 塌着导致的。
    ///     哪天 stack 撑开了却还拍不到，这条会红着说"解释过期了，去查新的原因" ——
    ///     而不是让一句已经作废的根因继续在账本里当结论用。
    func testQuickPickOverlayCannotBeCapturedYet() throws {
        let store = makePopulatedStore()
        let build = QuickPickCapturePanel.builder(store: store, query: "")
        guard let panel = build(), let content = panel.contentView else {
            return XCTFail("捕获入口建不出浮层窗口 ⇒ 这条判据失去了对象，必须红")
        }
        _ = NSApplication.shared
        let previousAppearance = NSApplication.shared.appearance
        NSApplication.shared.appearance = NSAppearance(named: .darkAqua)
        defer {
            NSApplication.shared.appearance = previousAppearance
            panel.orderOut(nil)
        }
        content.appearance = NSAppearance(named: .darkAqua)
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        Self.tileScrollViews(in: content)
        panel.display()
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))

        var rows = -1
        var stackWidth: CGFloat = -1
        var dataSourceIsController = false
        func find(_ view: NSView) {
            if let table = view as? NSTableView {
                rows = max(rows, table.numberOfRows)
                if table.dataSource is QuickPickController { dataSourceIsController = true }
            }
            if view is NSStackView { stackWidth = max(stackWidth, view.frame.width) }
            view.subviews.forEach(find)
        }
        find(content)
        guard let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds) else {
            return XCTFail("建不出位图缓存 ⇒ 这条判据没有对象")
        }
        content.cacheDisplay(in: content.bounds, to: rep)
        let transparent = Self.transparentFraction(of: rep)
        print("CAPTURE_PROBE quickpick transparent=\(String(format: "%.1f", transparent * 100))%"
              + " rows=\(rows) stackWidth=\(Int(stackWidth)) dataSourceIsController=\(dataSourceIsController)"
              + " bounds=\(NSStringFromRect(content.bounds))")
        XCTAssertGreaterThan(rows, 0,
                             "浮层表格 0 行 ⇒ 十有八九是控制器被释放了（`NSTableView.dataSource` 是弱引用），"
                             + "帧看起来仍然合法，其实拍的是一张空面板")
        XCTAssertTrue(dataSourceIsController,
                      "表格的数据源已经不是 `QuickPickController` ⇒ 拍到的行不是产品会画的那些行")
        XCTAssertGreaterThan(transparent, 0.9,
                             "浮层现在拍得出来了（transparent="
                             + "\(String(format: "%.1f", transparent * 100))%）⇒ "
                             + "把 quickpick-list / -typed / -empty 三张夹具加回去，别只改这条门槛")
        XCTAssertLessThan(stackWidth, 100,
                          "拍不到，但 `NSStackView` 已经撑到 \(Int(stackWidth))pt ⇒ "
                          + "账本里那条原因过期了。别把上面那条门槛放松，去查新的原因")
    }

    func testCaptureKeyViews() throws {
        guard let directory = outputDirectory else {
            throw XCTSkip("未设置 CLIPBOARD_HISTORY_UI_SHOTS，跳过离屏渲染")
        }
        var report: [(name: String, metrics: CaptureMetrics)] = []
        /// 哪些夹具声明了"内容必须整块放得下"。**从夹具自己读**，不在判据里另抄一份名单
        /// （两处各写一份的话，加一条夹具只会红一半 —— R18 那条"两处各写一个数"同族）。
        var mustFitNames: Set<String> = []
        /// 夹具机械自己也要有一条判据：**谁种了默认值，谁必须还原**。
        /// 不还原的污染是静默的 —— 后面的帧照样画得出来，只是多了两行本来不在那一页的东西，
        /// 而基线会把那份污染当成"产品长这样"钉住（`--against working` 从此永远比不回来）。
        var originalSeeds: [String: String?] = [:]
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for fixture in fixtures(appearance: appearance) {
                let file = directory.appendingPathComponent(
                    "\(fixture.name)-\(Int(fixture.size.width))x\(Int(fixture.size.height))-\(tag).png"
                )
                var previousSeed: (key: String, value: String?)? = nil
                if let seed = fixture.seed {
                    if originalSeeds[seed.key] == nil {
                        originalSeeds[seed.key] = UserDefaults.standard.string(forKey: seed.key)
                    }
                    previousSeed = (seed.key, UserDefaults.standard.string(forKey: seed.key))
                    UserDefaults.standard.set(seed.value, forKey: seed.key)
                }
                let metrics = try render(fixture, appearance: appearance, to: file)
                if fixture.contentMustFit { mustFitNames.insert(fixture.name) }
                if let restored = previousSeed {
                    if let value = restored.value {
                        UserDefaults.standard.set(value, forKey: restored.key)
                    } else {
                        UserDefaults.standard.removeObject(forKey: restored.key)
                    }
                }
                report.append((file.lastPathComponent, metrics))
            }
        }

        for (key, original) in originalSeeds {
            XCTAssertEqual(UserDefaults.standard.string(forKey: key), original,
                           "种子键 \(key) 拍完之后没还原 ⇒ 同一进程里后面的测试与下一轮帧都会读到上一张帧的夹具")
        }

        print("CAPTURED \(report.count) -> \(directory.path)")
        for item in report {
            print("  \(item.name)  transparent=\(String(format: "%.1f", item.metrics.transparent * 100))%"
                  + "  blackBandPt=\(String(format: "%.0f", item.metrics.blackBandPt))"
                  + "  bottomInk=\(String(format: "%.1f", item.metrics.bottomInkFraction * 100))%")
        }

        // **夹具不许裁自己的内容**（R22 / BACKLOG 32）。名单见 `Fixture.contentMustFit`。
        // 这条是 M76 那支"知道会漏还故意放"的变异终于被抓回去的一次：
        // 以前把 `weights` 的框改小回去**不会有任何测试红**，
        // 于是"帧里少了三行"这件事在账本里躺了九轮。
        for item in report where mustFitNames.contains(Self.fixtureName(fromFile: item.name)) {
            XCTAssertLessThan(item.metrics.bottomInkFraction, 0.02,
                              "\(item.name) 的最底一行有 \(String(format: "%.1f", item.metrics.bottomInkFraction * 100))% 的墨"
                              + " ⇒ 这张夹具正在裁自己的内容（被裁的元素一定压在底边上）。"
                              + "把 `Fixture` 的高度抬到放得下，而不是把这条断言关掉 —— "
                              + "被裁掉的那部分从来没有进过帧基线，也就从来没有被审过")
        }
        let judgedFit = mustFitNames.count
        print("CONTENT_FIT \(judgedFit) fixtures 判了底行墨（\(mustFitNames.sorted().joined(separator: ","))）")
        // **正对照**：一把只在"该红的时候没红"上被检验的尺，等于没被检验。
        // 上面那十张读到的都是 0.0%（正确 —— 它们没被裁），所以必须另有一张**已知有墨**的帧，
        // 否则"把阈值调到 100000"这种把尺弄瞎的改动不会有任何测试会红。
        // 选它是因为它是**天生会被裁**的那一族（列表在帧底被切一半），
        // 也就是说它的底行有墨不是缺陷，是滚动视图的正常行为 —— 正好当对照物。
        let canaries = report.filter { Self.fixtureName(fromFile: $0.name) == Self.bottomEdgeInkCanary }
        XCTAssertFalse(canaries.isEmpty, "正对照帧 \(Self.bottomEdgeInkCanary) 没被拍到 ⇒ 这把尺今天没被检验")
        for item in canaries {
            XCTAssertGreaterThan(item.metrics.bottomInkFraction, 0.5,
                                 "正对照帧 \(item.name) 的底行只读到 "
                                 + String(format: "%.1f", item.metrics.bottomInkFraction * 100) + "% 的墨"
                                 + " ⇒ 这把尺**瞎了**（它量不到任何压在底边上的内容），"
                                 + "上面那十条'没被裁'的绿也就没有意义")
        }
        print("CONTENT_FIT_CANARY " + canaries.map { "\($0.name)=\(String(format: "%.1f", $0.metrics.bottomInkFraction * 100))%" }
            .joined(separator: " "))

        for item in report where item.metrics.transparent > 0.95 {
            XCTFail("\(item.name) 有 \(Int(item.metrics.transparent * 100))% 像素未被绘制，判定为捕获失效，不能作为视觉验收证据")
        }

        // **材质盲区要能被数出来**（R18）。
        // 名单外的帧冒出黑带 ⇒ 又多了一处"看着拍到了、其实那块是黑的"，先红再说；
        // 名单里的帧不再冒黑 ⇒ 那一处现在能拍了（或者有人把选中底色改回自绘了），
        // 两种情况都必须**真的去看那张帧**，而不是把名单一行删掉了事。
        let blind = Set(report.map { (Self.fixtureName(fromFile: $0.name), $0.metrics.blackBandPt) }
                            .filter { $0.1 > 0 }
                            .map { $0.0 })
        let extra = blind.subtracting(Self.materialBlindSpotFixtures)
        let gone = Self.materialBlindSpotFixtures.subtracting(blind)
        XCTAssert(extra.isEmpty,
                  "这些帧第一次出现纯黑填充带：\(extra.sorted()) ⇒ 有一处材质在离屏下画成了黑，"
                  + "它的视觉状态从此量不到。先确认是谁、为什么黑，再决定是加进名单还是修掉黑的那一层")
        XCTAssert(gone.isEmpty,
                  "这些帧的黑带消失了：\(gone.sorted()) ⇒ 那一处现在能拍了，"
                  + "把 `materialBlindSpotFixtures` 缩掉，并且肉眼审一遍新帧（别只改名单）")
        print("MATERIAL_BLIND_SPOTS \(blind.count) of \(Set(report.map { Self.fixtureName(fromFile: $0.name) }).count) fixtures")
    }

    /// 夹具图片的字节**不能**随系统外观变。
    ///
    /// 这条是给"帧基线能不能当证据"加的：本轮实测到开发机开着自动切换外观，
    /// 傍晚从浅切到深之后，**同一份代码两次捕获有 18 帧自己变了**
    /// （`row-image` / `detail-1-image` / `sidebar-*` 的图片区域，最大通道差 17）。
    /// 那种漂移会让"改了界面要更新基线"这条硬门变成看天吃饭，
    /// 所以把外观钉死在 `makeStoredImage` 里，并由这条用例钉住它没被改回去。
    func testFixtureImageBytesDoNotDependOnAmbientAppearance() throws {
        // `NSApp` 是隐式解包的可选值：测试进程里没人创建过共享应用，直接读它就是崩溃
        // （本轮第一次跑就是这么挂的）。`render()` 里那行 `_ = NSApplication.shared` 是同一个原因。
        _ = NSApplication.shared
        let size = NSSize(width: 24, height: 16)
        // 阳性对照：先证明"不钉外观就会漂"这件事本身是真的。
        let rawLight = try fillUnderAmbient(.labelColor, appearance: .aqua, size: size)
        let rawDark = try fillUnderAmbient(.labelColor, appearance: .darkAqua, size: size)
        XCTAssertFalse(rawLight.isEmpty)
        XCTAssertNotEqual(rawLight, rawDark,
                          "前提变了：动态色不再随外观解析，这条守卫就没有判别力了（要改写而不是删掉）")

        let previous = NSApp.appearance
        defer { NSApp.appearance = previous }
        NSApp.appearance = NSAppearance(named: .aqua)
        let light = try XCTUnwrap(makeStoredImage(color: .systemTeal, size: size).pngData())
        NSApp.appearance = NSAppearance(named: .darkAqua)
        let dark = try XCTUnwrap(makeStoredImage(color: .systemTeal, size: size).pngData())
        XCTAssertEqual(light, dark,
                       "同一份夹具代码在两种外观下生成了不同字节 ⇒ 帧基线会随系统外观漂移")
    }

    /// 在**给定外观**下裸填充一次（不经过 `makeStoredImage` 的钉死），用来证明漂移的机制。
    private func fillUnderAmbient(_ color: NSColor, appearance name: NSAppearance.Name, size: NSSize) throws -> Data {
        let image = NSImage(size: size)
        NSAppearance(named: name)!.performAsCurrentDrawingAppearance {
            image.lockFocus()
            color.setFill()
            NSRect(origin: .zero, size: size).fill()
            image.unlockFocus()
        }
        return image.tiffRepresentation ?? Data()
    }

    // MARK: - 夹具（用闭包延迟求值：否则四个 detail 拍到的都是"最后一次选中"）

    struct Fixture {
        let name: String
        let size: NSSize
        /// 布局完成之后、按快门之前跑一次。给"内容要等一次异步刷新才落定"的视图用：
        /// 不 settle 就只能拍到刷新途中的那一帧，而那一帧是不是最终态取决于机器快慢。
        let settle: (() -> Void)?
        let build: () -> AnyView
        /// 按快门之前临时写进 `UserDefaults.standard` 的一个键，拍完立刻还原。
        ///
        /// 为什么要有这一层：`SettingsView` 里那几处 `@AppStorage` 状态（用户自己加的排除名单）
        /// **没有别的注入点** —— 它不是参数、不是 store 字段，而离屏窗口又不建无障碍树，
        /// 没法"点一下添加"。没有这一层，那一行与它右边那颗「移除」就永远进不了帧基线
        /// （R13 改它样式时正是"源码已接、产物未量"）。
        /// 还原是必须的：不还原的话同一次运行里 `settings-privacy` 那张也会被带脏。
        let seed: (key: String, value: String)?
        /// R18 加通路、R19 才拍到位：AppKit 表面的夹具入口返回**产品自己的窗口**。
        /// 返回 `NSView` 的第一版失败得很安静 —— 把浮层的 contentView 摘进另一个窗口之后，
        /// `NSStackView` 塌成 24×49、滚动视图 0×0，帧仍然"拍得出来"，只是拍的是空壳。
        ///
        /// 为什么要有这一条：快速选择浮层是 `QuickPickController` 自建的 `NSPanel` + `NSTableView`，
        /// 而 96 张基线**一张都没有它** —— 于是关于这个浮层的每一句观感结论只能停在"胶片 + 人眼"。
        /// 更要紧的是：`FRAME_BASELINE_CHANGED=0` 在这种表面上**不是**"没有视觉变化"，
        /// 而是"这里根本没有帧"。这两件事必须能分开（账本 BACKLOG 30 / U-39 / U-41）。
        let appKit: (@MainActor () -> NSWindow?)?
        /// 这张夹具的**内容必须整块放得下**（R22 / BACKLOG 32）。
        ///
        /// 为什么现在才立：这条守卫的代价是"会误报滚动区"，所以必须点名。
        /// 而它要抓的事已经发生过两次，两次都是**靠人眼**：
        /// R18 —— `weights` 用 560 高的框套 850 高的内容，标题与「恢复默认」按钮
        /// 九轮以来从来不在帧里；R20 —— `search-field` 320×96 一直在裁自己的下半条。
        /// 两次的共同点是**改小回去不会有任何测试红**（变异 M76 当年就是 ESCAPED）。
        ///
        /// 判法：帧的**最底一行**不该有墨（被裁的元素一定压在底边上）。
        /// 列表 / 滚动区那批天生会被裁 ⇒ 它们**不进**这个名单，
        /// 否则就是把"滚动视图的正常行为"报成缺陷。
        let contentMustFit: Bool

        init(_ name: String, _ size: NSSize, settle: (() -> Void)? = nil,
             seed: (key: String, value: String)? = nil,
             contentMustFit: Bool = false,
             appKit: (@MainActor () -> NSWindow?)? = nil, _ build: @escaping () -> AnyView) {
            self.name = name
            self.size = size
            self.settle = settle
            self.seed = seed
            self.contentMustFit = contentMustFit
            self.appKit = appKit
            self.build = build
        }

        /// 给一个已经建好的夹具补上 AppKit 入口（其余字段原样带走）。
        /// 存在的理由：`appKit` 与 `build` 是同一个结构体里的两个入口，
        /// 而 Swift 的成员式初始化器没有"只改一个字段"的写法 ——
        /// 没有这个 helper，加一条浮层帧就要把整条夹具重抄一遍，
        /// 而重抄的那份迟早和原件漂开。
        func withAppKit(_ buildAppKit: @escaping @MainActor () -> NSWindow?) -> Fixture {
            Fixture(name, size, settle: settle, seed: seed, contentMustFit: contentMustFit,
                    appKit: buildAppKit, build)
        }
    }

    private func fixtures(appearance: NSAppearance.Name) -> [Fixture] {
        let store = makePopulatedStore()
        let empty = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let searching = makePopulatedStore()
        searching.perform(.updateSearch("不存在的词"))

        var results: [Fixture] = [
            Fixture("content-with-history", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-min", NSSize(width: 600, height: 440)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-wide", NSSize(width: 1100, height: 800)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-empty", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: empty)) },
            Fixture("content-no-results", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: searching)) },
        ]

        // 菜单栏面板的内容层。以前这里一直标 NOT-RUN（D-019：整块 NSMenu 离屏画不出材质表面，
        // 97.7% 像素未绘制，会被本文件第 2 条规矩拦下 —— 那层判断本身没错）。
        // 但真正上线的是 macOS 13+ 的 SwiftUI `MenuBarExtra`，它的内容就是一个普通 View
        // （`MenuBarRecommendationsView`），可以和其他夹具一样离屏渲染：字号、层级、间距、
        // 空态文案、脱敏标签都拍得到；**拍不到的仍然是系统菜单的材质与圆角**（那层由系统画）。
        // 可复现性：reason 文案会带"当前在<App 名>"，取自 `effectiveFrontmostApp()`；
        // 测试进程从不 `startMonitoring()` ⇒ `lastFrontmostBundleID` 恒为 nil ⇒ 走"第一条记录的来源 App"，
        // 由夹具固定（Safari），所以这些帧仍可做逐字节比对。
        if #available(macOS 13, *) {
            let recommendationStore = makePopulatedStore()
            recommendationStore.refreshPredictions()
            waitUntil("菜单栏面板需要候选") { !recommendationStore.predictionSuggestionEntries.isEmpty }
            results.append(Fixture("menubar-recommendations", NSSize(width: 320, height: 320), settle: {
                self.waitUntil("推荐刷新要收尾") { !recommendationStore.isRefreshingPredictions }
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: recommendationStore,
                    appDelegate: AppDelegate(historyStore: recommendationStore)
                )))
            })

            // 刷新途中的那一帧：视图 `onAppear` 自己会发起一次刷新，所以不 settle，
            // 并在快门前一瞬**断言它仍在途中** —— 否则这帧的名字就在说谎，
            // 而"名字说正在算、画面上却写着暂无推荐"这种错用肉眼比对很难发现。
            let refreshingStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
            )
            results.append(Fixture("menubar-refreshing", NSSize(width: 320, height: 120), settle: {
                XCTAssertTrue(refreshingStore.isRefreshingPredictions,
                              "这一帧叫「正在整理推荐」，拍的时候刷新必须仍在途中")
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: refreshingStore,
                    appDelegate: AppDelegate(historyStore: refreshingStore)
                )))
            })

            // 算完确实没有推荐：settle 到刷新收尾，必须说"暂无推荐"而不是整段消失。
            let emptyMenuBarStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
            )
            results.append(Fixture("menubar-empty", NSSize(width: 320, height: 120), settle: {
                self.waitUntil("空库的预测刷新要收尾") { !emptyMenuBarStore.isRefreshingPredictions }
                XCTAssertTrue(emptyMenuBarStore.predictionSuggestionEntries.isEmpty,
                              "空库不该有候选，否则这帧拍的不是空态")
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: emptyMenuBarStore,
                    appDelegate: AppDelegate(historyStore: emptyMenuBarStore)
                )))
            })
        }

        // 侧栏脱离分栏器单独拍：实测 NavigationSplitView 的 sidebar 列在离屏
        // cacheDisplay 下不跟随强制暗色（同一帧里详情列是白字、侧栏列是黑字），
        // 所以 content-* 帧只能用来核对几何与布局，颜色验收看 sidebar-*。
        let multiSelected = makePopulatedStore()
        multiSelected.perform(.selectOnly(multiSelected.entries[0]))
        multiSelected.perform(.toggleSelection(multiSelected.entries[1]))
        multiSelected.perform(.toggleSelection(multiSelected.entries[2]))
        let favorited = makePopulatedStore()
        favorited.perform(.toggleFavorite(favorited.entries[0]))
        favorited.perform(.updateFilter(.favorites))

        results.append(Fixture("sidebar-history", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: store)))
        })
        results.append(Fixture("sidebar-multi-select", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: multiSelected)))
        })
        // R15：多选条的图标加了 `labelPadding`（药丸与命中区一起长），
        // 整排宽了约 18pt。"最窄侧栏放得下"这句话不能靠算 ——
        // `ContentView` 给侧栏的是 `minWidth: 250`，所以这张帧就是那条算式的判据。
        results.append(Fixture("sidebar-multi-select-min", NSSize(width: 250, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: multiSelected), width: 250))
        })
        // R18 想加、当时判"加不进去"的三张浮层帧：R19 把那条根因**推翻**了，
        // 但帧**仍然加不进去**，而且现在知道为什么了（`testQuickPickOverlayCannotBeCapturedYet`
        // 里带着实测的视图树，不再是猜的）：
        //   · 浮层里没有 `NSVisualEffectView`，裸材质离屏也画得出来 ⇒ R18 那句"材质不可合成"是错的；
        //   · 真正的现象是产品的 `NSStackView` 在捕获环境里塌成 24×49
        //     （真实 App 里它撑满 420×300），于是 `NSScrollView` 0×0、
        //     `NSTableView.visibleRect` 0×0 —— 表格有 5 行，一行都画不出来。
        // 两条候选路都没走：让面板 `makeKeyAndOrderFront` 会抢用户前台（测试套件的硬边界），
        // 而从夹具侧把 stack 的 frame 按回去，等于**让帧去画夹具想要的布局** ——
        // 那正是这两轮一直在抓的那类假证据。所以这三张继续缺席，判据盯着。

        results.append(Fixture("sidebar-favorites", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: favorited)))
        })
        results.append(Fixture("sidebar-no-results", NSSize(width: 300, height: 520)) {            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: searching)))
        })

        for entry in store.entries.prefix(4) {            let captured = entry
            results.append(Fixture("row-\(rowKind(captured))", NSSize(width: 300, height: 74)) {
                AnyView(self.rowFrame(HistoryRowButton(
                    entry: captured, copyAction: {}, favoriteAction: {}
                )))
            })
        }

        // 行首星标两个状态各拍一张。以前这颗星在未收藏时是 `.clear`（等于这个控件不存在），
        // 现在它是真按钮，两种状态都必须看得见 —— 这条帧就是那件事的证据。
        let starTarget = store.entries[0]
        let starOn = starTarget.updating(timestamp: starTarget.timestamp, isFavorite: true)
        let starOff = starTarget.updating(timestamp: starTarget.timestamp, isFavorite: false)
        results.append(Fixture("row-favorite-on", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starOn, copyAction: {}, favoriteAction: {}
            )))
        })
        results.append(Fixture("row-favorite-off", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starOff, copyAction: {}, favoriteAction: {}
            )))
        })

        results.append(Fixture("row-pinned-on", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starTarget.updating(isPinned: true), copyAction: {}, favoriteAction: {}
            )))
        })
        results.append(Fixture("row-pinned-off", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starTarget.updating(isPinned: false), copyAction: {}, favoriteAction: {}
            )))
        })

        // 图片**文件**条目带缩略图的一行（用户报的缺陷：详情区看得到图，列表里只有文档符号）。
        // 这条帧存在的意义是：行首视觉列"有缩略图就用图"这件事从此有像素可查，
        // 不再只能靠真机眼睛看。PDF/多文件那两条仍然没有缩略图，保持文档符号是对的。
        let fileThumb = try! makeStoredImage(color: .systemIndigo, size: NSSize(width: 200, height: 150))
        let fileWithThumb = ClipboardEntry(
            content: .file(URL(fileURLWithPath: "/Users/tester/Desktop/board-icon-fullbleed.png")),
            timestamp: Self.referenceDate.addingTimeInterval(-60),
            thumbnail: fileThumb,
            sourceURL: URL(fileURLWithPath: "/Users/tester/Desktop/board-icon-fullbleed.png"),
            sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        )
        results.append(Fixture("row-file-thumb", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: fileWithThumb, copyAction: {}, favoriteAction: {}
            )))
        })

        // 每个详情都用"重建同一份数据 + 按序号选中"，因为重建会生成新的 UUID
        for (index, entry) in store.entries.prefix(4).enumerated() {
            let kind = rowKind(entry)
            results.append(Fixture("detail-\(index)-\(kind)", NSSize(width: 720, height: 520)) {
                let target = self.makePopulatedStore(selectingIndex: index)
                return AnyView(DetailView(historyStore: target))
            })
        }

        // 一颗浮层药丸一张帧。以前两张挤在 200pt 高的框里（四颗按钮 + 分隔线 + padding 实际
        // 需要 ~187pt，加上 32pt padding 就被裁掉了），加了固定按钮后更放不下 ——
        // 被裁的帧会让人误判"按钮少了"，所以一种状态一帧，高度按内容给足。
        // 搜索命中高亮 + 可读行长（审计 §4 U-4）。
        // 这一帧存在的意义是把两件事变成像素：正文列被限制在一个可读宽度内、
        // 以及当前搜索词在正文里真的被涂了底色。判据在 `Round3DetailTypographyTests` 里，
        // 它先钉住夹具前提（确有这条含"视觉验收"的条目，且设了搜索词之后它仍是选中项）。
        results.append(Fixture("detail-text-highlight", NSSize(width: 720, height: 520)) {
            let target = self.makePopulatedStore(selectingIndex: nil)
            if let hit = target.entries.first(where: { $0.shortPreview.contains("视觉验收") }) {
                target.perform(.selectOnly(hit))
                target.perform(.updateSearch("视觉"))
            }
            return AnyView(DetailView(historyStore: target))
        })

        // 第四轮新功能：右侧预览渲染 Markdown。**一对帧**而不是单独一张 ——
        // 只拍"渲染"那一侧的话，"切换有效"这件事就只剩控件标题这个证据；两帧相减还能把
        // 「原文里那些 # 和 * 在渲染态确实没了、而正文一个字没少」量成像素差。
        // 夹具前提由 `Round4MarkdownTests.testTheMarkdownFrameFixtureIsNotLying` 钉住。
        results.append(Fixture("detail-markdown-rendered", NSSize(width: 720, height: 520)) {
            let target = self.makeMarkdownStore()
            self.assertMarkdownFixturePremise(target, role: "detail-markdown-rendered")
            return AnyView(DetailView(historyStore: target, initialMarkdownMode: .rendered))
        })
        results.append(Fixture("detail-markdown-source", NSSize(width: 720, height: 520)) {
            let target = self.makeMarkdownStore()
            self.assertMarkdownFixturePremise(target, role: "detail-markdown-source")
            return AnyView(DetailView(historyStore: target, initialMarkdownMode: .source))
        })

        results.append(Fixture("glass-pill", NSSize(width: 120, height: 232), contentMustFit: true) {
            AnyView(
                GlassPill(isFavorite: false, favoriteAction: {},
                          isPinned: false, pinAction: {},
                          copyAction: {}, deleteAction: {})
                    .padding(16)
                    .frame(width: 120, height: 232)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        results.append(Fixture("glass-pill-states", NSSize(width: 120, height: 232), contentMustFit: true) {
            AnyView(
                GlassPill(isFavorite: true, favoriteAction: {},
                          isPinned: true, pinAction: {},
                          copyAction: {}, deleteAction: {})
                    .padding(16)
                    .frame(width: 120, height: 232)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        // 高度 96 → 112（R20）：96 是"两态各 31pt"那个年代记下来的数
        // （12 + 31 + 8 + 31 + 12 = 94，刚好塞进 96）。
        // 清除 × 的命中区抬到 22pt 之后两态各要 32pt，总高 96 正好顶满 ⇒
        // 下面那颗框被裁掉约 4.5pt，而 `testSearchFieldKeepsTheSameHeightInBothStates`
        // 报的是"两态不等高"。**这条判据先抓到的其实是夹具自己裁了内容** ——
        // 与 R18 那批"夹具尺寸是记的数"同一族，只是这次是新加的守卫把它逼出来的。
        results.append(Fixture("search-field", NSSize(width: 320, height: 112), contentMustFit: true) {
            AnyView(
                VStack(spacing: 8) {
                    SearchField(text: .constant(""))
                    SearchField(text: .constant("搜索内容"))
                }
                .padding(12)
                .frame(width: 320, height: 112)
                .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        results.append(Fixture("empty-state", NSSize(width: 320, height: 160), contentMustFit: true) {
            AnyView(
                EmptyStateView(systemName: "doc.on.clipboard", title: "选择一条记录查看详情")
                    .frame(width: 320, height: 160)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        let weightsStore = store.weightsStore
        // R18：高度从 560 改成 880。
        // 560 是**很久以前**内容还短的时候记下的数；现在这一页有 9 个因子行，
        // 实测内容要 850pt（把同一份内容放进 1200pt 的框里、量墨迹最后一行得到的数）。
        // `.frame(height: 560)` 是居中的 ⇒ 上下各裁 145pt：
        // 标题「推荐权重客制化」、「恢复默认」那颗按钮、说明文字「0% = 禁用，100% = 默认…」
        // 连同**第一行因子**全部在帧外，最后一行也被切了一半。
        // 也就是说：这张帧从来没有拍到过它名字里那一页的头部，
        // 而 `FRAME_BASELINE_CHANGED=0` 让人以为整页都被看着了。
        // 这一条和上面"窗口被内容顶大"是同一族缺陷的两个方向：**夹具的尺寸是记的数，不是量的数**。
        results.append(Fixture("weights", NSSize(width: 520, height: 880), contentMustFit: true) {
            AnyView(
                RecommendationWeightsView(store: weightsStore)
                    .padding(20)
                    .frame(width: 520, height: 880)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })
        // R18：新颜色梯子的**第二态**。
        //
        // 本轮把权重数值从"三档语义色"改成"动过 = 主色 / 没动过 = 次级色"，
        // 而帧基线里这一页 9 行**全部**处于"没动过"—— 于是一个"只有动过才看得见"的改动，
        // 在产物里根本没有对应的像素。与 R14 那两条"从未存在过的帧"同一族，
        // 也是 `FRAME_BASELINE_CHANGED=0` 最擅长骗人的一种情形。
        results.append(Fixture("weights-adjusted", NSSize(width: 520, height: 880), contentMustFit: true) {
            // 种 → 建视图 → 立刻还原。规矩与 `Fixture.seed` 同一条：种过必须还原，
            // 否则同一次运行里后面的帧会读到这一张的夹具值（而基线会把污染当成长相）。
            let key = "RecommendationWeights.store"
            let original = UserDefaults.standard.data(forKey: key)
            let adjusted = RecommendationWeightsStore()
            var weights = adjusted.weights
            weights[.recency] = 1.6      // 抬高：以前会被涂成"警示橙"
            weights[.favorite] = 0.4     // 压低：以前会被涂成"弱化灰"
            adjusted.weights = weights
            // 夹具前提：我存/还原的那个键**就是** store 自己读写的键。
            // 键名哪天改了，这条会红 —— 而不是安静地把污染留给后面的帧。
            XCTAssertEqual(RecommendationWeightsStore().weights[.recency], 1.6, accuracy: 0.001,
                           "夹具写的键与 store 读的键不是同一个 ⇒ 种下的值还原不掉，后面的帧会被带脏")
            if let original {
                UserDefaults.standard.set(original, forKey: key)
            } else {
                UserDefaults.standard.removeObject(forKey: key)
            }
            return AnyView(
                RecommendationWeightsView(store: adjusted)
                    .padding(20)
                    .frame(width: 520, height: 880)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        // 设置页：5 个分类逐个拍。分类是 SettingsView 的私有 @State，
        // 离屏窗口又不会建无障碍树（试过：BFS 只能走到根节点），
        // 所以用 initialCategory 注入，而不是靠"点一下"。
        for category in SettingsCategory.allCases {
            results.append(Fixture("settings-\(category.rawValue)", NSSize(width: 720, height: 540)) {
                AnyView(self.makeSettingsView(store: store, initialCategory: category))
            })
        }
        results.append(Fixture("settings-min", NSSize(width: 640, height: 440)) {
            AnyView(self.makeSettingsView(store: store))
        })

        // 每日复制热图（新功能 / 阶段一）：组件级两张 —— 有数据与没数据。
        // 固定 `today` 与固定计数 ⇒ 这两张帧不随日期变。
        let heatToday = Self.heatmapFixtureToday
        var heatCalendar = Calendar(identifier: .gregorian)
        heatCalendar.timeZone = TimeZone(identifier: "Asia/Shanghai") ?? .current
        heatCalendar.firstWeekday = 2
        // 夹具必须带中文 locale：不设置的话日历默认 en_US，
        // 拍出来的星期标签是 "M W F S" —— 审查的人会以为产品写死了英文。
        heatCalendar.locale = Locale(identifier: "zh_CN")
        let heatCounts = Self.heatmapFixtureCounts(today: heatToday, calendar: heatCalendar)
        results.append(Fixture("heatmap-populated", NSSize(width: 430, height: 250), contentMustFit: true) {
            AnyView(
                DailyCopyHeatmapView(counts: heatCounts, today: heatToday, calendar: heatCalendar)
                    .padding(16)
                    .frame(width: 430, height: 250, alignment: .topLeading)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })
        // 设置页里的**有数据**版本：组件帧看不出布局问题（分区标题、说明文字、
        // 与侧栏的关系），所以这一张必须有。账本指向一个预先写好计数的临时文件 ——
        // 捕获套件仍然不碰用户数据。
        let populatedLedgerURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("capture-ledger-populated.json")
        try? DailyCopyLedger.write(heatCounts, to: populatedLedgerURL)
        let populatedLedger = DailyCopyLedger(fileURL: populatedLedgerURL,
                                              calendar: heatCalendar,
                                              debounceSeconds: 3600,
                                              now: { heatToday })
        // R14 · 两张"从来没有存在过的帧"。
        //
        // ①「移除」这颗破坏性按钮只在**用户自己加过**排除 App 之后才存在；
        // ② 回执行的 × 只在**刚导出 / 刚清空 / 刚改过排除名单**之后才存在。
        // 90 帧夹具里这两种状态一个都没有，于是 R13 把这两处的样式从 `.borderless`
        // 换成有按压/悬停的一档时，`FRAME_BASELINE_CHANGED` 里根本没有它们 ——
        // 那叫"源码已接、产物未量"，账本里这一族已经记过太多次。
        // 高度取 1040 而不是真实窗口的 540：**为的是把「移除」那颗拍进画面**。
        // 用户自己加的排除项排在 10 行默认列表之后，540 高的那一帧里它在折叠线以下 ——
        // 也就是说"这张帧存在"并不等于"这颗按钮被拍到了"（第一次审查就栽在这上面）。
        // 排序本身要不要反过来（自己的列表在前、默认清单在后）记 BACKLOG 27，不在本轮改。
        results.append(Fixture("settings-privacy-excluded", NSSize(width: 720, height: 1040),
                               // 种子串**由产品自己的编码器生成**，不是手写的：
                               // 第一版这里写的是 "a,b"，而分隔符其实是 ";" ——
                               // 于是画面上出现一整行 `com.example.writer,com.example.design`
                               // 加**一颗**「移除」。产品没错（它照格式解出来一个 ID），
                               // 错的是夹具自带了一份"长得像"的格式。看帧的人会把这读成
                               // "这行坏了"，而它其实是夹具坏了。
                               seed: (CapturePolicy.userExcludedKey,
                                      CapturePolicy.encodeUserExcluded(["com.example.writer",
                                                                        "com.example.design"]))) {
            AnyView(self.makeSettingsView(store: store, initialCategory: .privacy))
        })
        results.append(Fixture("receipt-line", NSSize(width: 430, height: 56), contentMustFit: true) {
            AnyView(
                ReceiptLine(text: "已导出 94 条记录到 ~/Desktop/时间剪史-导出.json", dismiss: {})
                    .padding(.horizontal, 12)
                    .frame(width: 430, height: 56, alignment: .leading)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })
        results.append(Fixture("settings-stats-populated", NSSize(width: 720, height: 540)) {
            AnyView(SettingsView(
                showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
                repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
                loginItemSettings: LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
                contextPreferences: ContextPreferenceSettings(),
                weightsStore: store.weightsStore,
                feedbackStore: store.feedbackStore,
                dailyCopyLedger: populatedLedger,
                clearHistoryAction: { nil },
                initialCategory: .stats
            ))
        })
        results.append(Fixture("heatmap-empty", NSSize(width: 430, height: 150), contentMustFit: true) {
            AnyView(
                DailyCopyHeatmapView(counts: [:], today: heatToday, calendar: heatCalendar)
                    .padding(16)
                    .frame(width: 430, height: 150, alignment: .topLeading)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        // R-13/R-02 的提示条：既拍组件本身，也拍它插进 ContentView 之后
        // 会不会把 NavigationSplitView 的布局挤坏。
        let pasteFailureText = "系统未授权本 App 控制「System Events」，无法自动粘贴。请在「系统设置 → 隐私与安全性 → 自动化」里允许后重试；记录本身已复制到剪贴板，可手动粘贴。"
        let noticeStore = makePopulatedStore()
        noticeStore.reportPasteFailure(pasteFailureText)
        results.append(Fixture("content-with-notice", NSSize(width: 750, height: 560)) {
            AnyView(ContentView(historyStore: noticeStore))
        })
        // **两条横幅同时在**的那张帧（R22 / U-44）。
        //
        // 为什么以前没有：`content-with-notice` 只挂一条，而 `ContentView` 里五条横幅是
        // 直接并排放进 `VStack(spacing: 0)` 的 —— 于是"两条挨在一起长什么样"**从来没有进过帧基线**。
        // 更糟的是组件那张帧（`notice-banner`）自己写了 `VStack(spacing: 12)`，
        // 也就是说**夹具替产品做了一个产品没做的决定**：帧里那 12pt 的缝在真窗口里不存在。
        // 这一条是给"夹具不能替产品决定布局"立的证据，两条都走产品入口（粘贴失败 + 拖入非本机文件）。
        let twoNoticeStore = makePopulatedStore()
        twoNoticeStore.reportPasteFailure(pasteFailureText)
        twoNoticeStore.addDroppedFiles(urls: [URL(string: "https://example.com/远程图.png")!])
        results.append(Fixture("content-with-two-notices", NSSize(width: 750, height: 560)) {
            AnyView(ContentView(historyStore: twoNoticeStore))
        })
        results.append(Fixture("notice-banner", NSSize(width: 560, height: 170), contentMustFit: true) {
            AnyView(
                VStack(spacing: 12) {
                    NoticeBanner(message: "主存档无法读取，已从备份恢复 12 条记录；损坏原件保留为 history.corrupt-1.json。",
                                 tone: .warning, onDismiss: {})
                    NoticeBanner(message: pasteFailureText, tone: .error, onDismiss: {})
                }
                .padding(12)
                .frame(width: 560, height: 170)
                .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        return results
    }

    /// 侧栏夹具的外框。宽度是**参数**：
    /// R15 第一版加窄帧时忘了这里，300 的框套在 250 的画布上 ⇒ 拍出来两边各裁掉 25pt，
    /// 看起来像"产品在窄侧栏下溢出"，其实是夹具在撒谎（量出来的 extent 正好等于整幅宽）。
    /// 一个把尺寸写死的外框，等于取消了"换个尺寸拍一张"这件事。
    private func sidebarFrame<V: View>(_ view: V, width: CGFloat = 300) -> some View {
        view
            .frame(width: width, height: 520, alignment: .top)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 单行夹具的外框。拍的是 `HistoryRowButton`（带星标与悬停底色的那一层）而不是裸内容，
    /// 这样行上新增的可点控件会真的进帧。
    private func rowFrame<V: View>(_ view: V) -> some View {
        view
            .frame(width: 300, height: 74, alignment: .leading)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 菜单栏面板的离屏外框。真实面板由系统给宽度和材质，这里只固定宽度并铺一层窗口底色，
    /// 让内容层的排版与对比度可测；材质本身不在这帧的责任范围内。
    private func menuBarFrame<V: View>(_ view: V) -> some View {
        view
            .padding(.vertical, 6)
            .frame(width: 320, alignment: .topLeading)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 等异步预测落地。超时是**失败**而不是"那就拍没候选的帧"：
    /// 后者会让"有推荐"这一帧在退化时静默变成"暂无推荐"，像素仍然合法、缺陷却被吞掉。
    private func waitUntil(_ description: String, timeout: TimeInterval = 5.0, condition: @MainActor () -> Bool) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立，这一帧不能拍")
    }

    private func makeSettingsView(store: HistoryStore, initialCategory: SettingsCategory? = .shortcuts) -> some View {
        SettingsView(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
            contextPreferences: ContextPreferenceSettings(),
            weightsStore: store.weightsStore,
            feedbackStore: store.feedbackStore,
            // 「统计」那一页要有账本才拍得出东西。指向**临时目录**里一个空账本：
            // 捕获套件绝不许碰用户 `~/Library/Application Support/时间剪史/` 里的真数据
            //（D-002 的边界，与 `CLIPBOARD_HISTORY_DATA_DIR` 同一个理由）。
            dailyCopyLedger: DailyCopyLedger(
                fileURL: FileManager.default.temporaryDirectory
                    .appendingPathComponent("capture-ledger-empty.json"),
                debounceSeconds: 3600),
            clearHistoryAction: { nil },
            initialCategory: initialCategory
        )
    }

    /// 热图夹具的数据。`today` 固定 ⇒ 这张帧**永远长一样**。
    ///
    /// 为什么不让它跟着真实日期走：帧基线是逐字节比的，用"今天"当锚点的话
    /// 这张图每天自己变形状，第二天就是一条与任何改动无关的红。
    static func heatmapFixtureCounts(today: Date, calendar: Calendar) -> [String: Int] {
        var counts: [String: Int] = [:]
        for offset in 0..<126 {
            guard let date = calendar.date(byAdding: .day, value: -offset, to: today) else { continue }
            let weekday = calendar.component(.weekday, from: date)
            let base = (weekday == 1 || weekday == 7) ? 1 : 6
            counts[DailyCopyHeatPolicy.dayKey(for: date, calendar: calendar)] = base + (offset * 7) % 13
        }
        return counts
    }

    static var heatmapFixtureToday: Date {
        var components = DateComponents()
        components.year = 2026
        components.month = 3
        components.day = 12
        components.hour = 12
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Asia/Shanghai") ?? .current
        return calendar.date(from: components) ?? Date()
    }

    private func rowKind(_ entry: ClipboardEntry) -> String {
        switch entry.content {
        case .text: return "text"
        case .image: return "image"
        case .file: return "file"
        case .files: return "files"
        }
    }

    /// 详情区 Markdown 夹具的正文。固定内容、固定时间戳，所以两帧可以做逐字节比对。
    /// 覆盖的是"渲染到底改变了什么"的每一个可量测面：字阶、字重、斜体/字重分叉、
    /// 行内码底色、围栏代码、任务项勾选、有序编号、引用弱化、表格等宽、链接色。
    static let markdownFixtureBody = """
    # 发布时间剪史 1.4.9

    这一段里有 **粗体**、一个 *emphasis*，还有行内 `swift build`。

    - [x] 解析层完成
    - [ ] 视觉复核待办
    3. 第三步的内容不能被吃掉

    > 引用里的话
    > 第二行也要跟着缩进

    ```swift
    let release = Version(1, 4, 9)
    ```

    | 名称 | 数量 |
    | --- | --- |
    | 苹果 | 3 |

    ## 安装

    参考 [官方文档](https://example.com/doc) 与 <https://bare.example>。
    中文的 *强调* 不能用合成斜体。
    """

    /// 夹具前提：这一帧拍的那条记录，按策略确实有渲染入口，正文里也确实带 Markdown 标记。
    /// 前提不成立时必须**红** —— 一张名字叫 `detail-markdown-rendered` 却拍着普通文本的帧
    /// 看着像证据，其实什么都没说（D-038 那一族；`detail-text-highlight` 同样有这条前置断言）。
    private func assertMarkdownFixturePremise(_ store: HistoryStore, role: String,
                                              file: StaticString = #filePath, line: UInt = #line) {
        guard let entry = store.selectedEntry else {
            XCTFail("\(role)：Markdown 夹具没有选中项", file: file, line: line)
            return
        }
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: entry.content),
                      "\(role)：选中的这条按策略根本不该给渲染入口 —— 那这一帧的名字在说谎",
                      file: file, line: line)
        guard case .text(let body) = entry.content else {
            XCTFail("\(role)：选中的不是文本条目", file: file, line: line)
            return
        }
        XCTAssertTrue(body.contains("## 安装"),
                      "\(role)：正文里没有 Markdown 标记，两帧会是同一张照片", file: file, line: line)
        XCTAssertEqual(MarkdownParser.parse(body).blocks.first?.kind, .heading(level: 1),
                       "\(role)：解析结果的第一块不是 h1，帧上要核对的东西就换了", file: file, line: line)
    }

    private func makeMarkdownStore() -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        store.add(ClipboardIntake.Entry(
            content: .text(Self.markdownFixtureBody),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"
        ), timestamp: Self.referenceDate)
        return store
    }

    /// internal 是刻意的：`detail-text-highlight` 这类夹具的**前提**需要被另一套用例断言
    /// （夹具里到底有没有那条含"视觉验收"的正文、设了搜索词之后选中项有没有换人）。
    /// 前提不成立时帧是白的或量的不是命中 —— 那种帧看着像证据，其实什么都没说。
    func makePopulatedStore(selectingIndex index: Int? = nil) -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let image = try! makeStoredImage(color: .systemTeal, size: NSSize(width: 240, height: 140))
        store.add(ClipboardIntake.Entry(
            content: .text("这是一段用于视觉验收的普通文本记录，包含足够长度以便观察截断与换行表现 abcdefghijklmnop"),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
        ), timestamp: Self.referenceDate.addingTimeInterval(-30))
        store.add(ClipboardIntake.Entry(
            content: .image(image), thumbnail: image, sourceUTIs: ["public.png"],
            sourceAppBundleID: "com.apple.Preview", sourceAppName: "预览"
        ), timestamp: Self.referenceDate.addingTimeInterval(-120))
        store.add(ClipboardIntake.Entry(
            content: .file(URL(fileURLWithPath: "/Users/tester/Desktop/合同 终版 v3.pdf")),
            thumbnail: nil, sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        ), timestamp: Self.referenceDate.addingTimeInterval(-300))
        store.add(ClipboardIntake.Entry(
            content: .files([
                URL(fileURLWithPath: "/Users/tester/Downloads/IMG_0201.HEIC"),
                URL(fileURLWithPath: "/Users/tester/Downloads/IMG_0202.HEIC"),
                URL(fileURLWithPath: "/Users/tester/Downloads/说明.md"),
            ]),
            thumbnail: nil, sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        ), timestamp: Self.referenceDate.addingTimeInterval(-600))
        store.add(ClipboardIntake.Entry(
            content: .text("ghp_" + String(repeating: "A", count: 36)),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Terminal", sourceAppName: "终端"
        ), timestamp: Self.referenceDate.addingTimeInterval(-900))
        if let index, index < store.entries.count {
            store.perform(.selectOnly(store.entries[index]))
        }
        return store
    }

    /// 判据自己拍的那张帧叫什么。它带着尺寸段，所以夹具改框时这里对不上就会红
    /// （红的是"读不回来"，不是安静跳过）。
    static let searchFieldFixtureSize = "320x112"

    /// `search-field` 这张夹具**确实把两颗框都画出来了**（R20 立、R21b 改判法）。
    ///
    /// 这一条从"我自己改出来的回归"长出来：给清除 × 加 4pt 命中区之后，有字那颗框被顶高约 5pt、
    /// 空框反而矮了 4pt（实测 31→27 / 31→32）⇒ **打字时搜索框自己跳**。
    ///
    /// **等高这件事不在这里判**（R21b）：CI 打红过一次 —— 本机像素带高读 32.5/33.0，
    /// 无头 runner 读 15.5/17.0，因为那儿的窗口底色让 3.5% 的框填充落不进"偏离 >12"，
    /// 带子从"框"塌成"有墨的行"。**同一把尺在两台机器上量的不是同一件事**，
    /// 把判据建在它上面就是让 CI 的绿取决于底色。等高改由
    /// `testSearchFieldIdealHeightIsStateIndependent` 判布局事实（环境无关）。
    /// 这里只留两条**跨机器稳定**的前提：夹具存在、帧里确实有两条带（否则"两态"根本没进画面）。
    ///
    /// 它仍然**自己拍自己量**（R20 预检立的规矩：不许读别的测试写好的 PNG）。
    func testSearchFieldFixtureShowsBothStates() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r20-height-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == "search-field" }) else {
                return XCTFail("找不到 search-field 夹具 ⇒ 这条判据没有对象")
            }
            let file = scratch.appendingPathComponent("search-field-\(Self.searchFieldFixtureSize)-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
            }
            let bands = Self.filledBands(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                         bytesPerRow: rep.bytesPerRow)
            XCTAssertEqual(bands.count, 2,
                           "帧里应该正好有两颗框（空 / 有字），实测 \(bands.count) 条：\(bands) ⇒ 夹具或布局变了")
            let heights = bands.map { $1 - $0 }
            // **带高只打印，不判**（R21b，CI 打红的就是这一条）：
            // 本机读 32.5 / 33.0，无头 runner 读 15.5 / 17.0 —— 同一把尺在两台机器上
            // 量的**不是同一件事**（那儿的窗口底色不同 ⇒ 3.5% 的框填充落不进"偏离 >12"，
            // 于是带子塌成"有墨的行"）。把判据建在它上面，等于让 CI 绿不绿取决于底色。
            // 等高这条改成量**布局本身**（下面 `idealHeight`），它是环境无关的。
            print("SEARCH_FIELD_BANDS \(tag) px=\(heights)（诊断用，判据在 idealHeight 那条）")
        }
    }

    /// 把视图**自己算出来的布局高度**写进一个盒子（R21b）。
    ///
    /// 为什么不用 `NSHostingView.fittingSize`：那条路我试过，两次都不行 ——
    /// 裸 hosting view（无窗口）读回来是 0，而按 `render()` 那样现建一个离屏窗口去读
    /// 会让测试进程 **SIGSEGV**。更重要的是：`fittingSize` 在 R19 已经被证明是
    /// "内容钉了高度就恒真"的尺。
    ///
    /// 这条路判的是**布局事实**：`GeometryReader` 挂在 `.background` 上，
    /// 拿到的就是 SwiftUI 给这个视图的实排尺寸，与底色、字体渲染、机器快慢都无关。
    private struct HeightWriter: View {
        let onMeasure: (CGFloat) -> Void

        var body: some View {
            GeometryReader { proxy in
                Color.clear.onAppear { onMeasure(proxy.size.height) }
            }
        }
    }

    /// 搜索框两态的**布局高度**必须相等（R20 的回归，R21b 换成环境无关的判法）。
    ///
    /// 为什么换判法：CI 把原来那条像素带高判据打红过一次 ——
    /// 本机读 32.5 / 33.0pt，无头 runner 读 **15.5 / 17.0pt**，差一倍。
    /// 根因不是噪声：这张框的填充是 `VisualFill.fieldIdle`=0.035、描边是
    /// `VisualTint.fieldIdleStroke`=0.05，在 runner 那块纯白底上**都低于任何可用的像素阈值**，
    /// 于是"框"塌成"有墨的行"。**同一把尺在两台机器上量的不是同一件事**，
    /// 把"打字时框会不会跳"建在它上面，就是让 CI 的绿取决于底色。
    ///
    /// 现在判的是布局：两态各自实排高度，容差 0.2pt。
    /// 之所以敢收到这么紧：× 的字形与文本列**都钉死了**（14pt + 4pt 命中区 = 22pt，
    /// 文本列声明 22pt），所以高度不再依赖 SF Symbol 的字形度量 —— 那正是本机与 CI 会分叉的地方。
    /// 而这一族真实缺陷的量级是 5pt。
    /// 变异 **M95** 就是把文本列的 22pt 改回 17pt —— 那条判据必须红。
    @MainActor
    func testSearchFieldIdealHeightIsStateIndependent() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r21b-height-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            let box = HeightBox()
            let fixture = Fixture("search-field-height-probe", NSSize(width: 320, height: 160)) {
                AnyView(
                    VStack(spacing: 8) {
                        SearchField(text: .constant(""))
                            .background(HeightWriter { box.empty = $0 })
                        SearchField(text: .constant("搜索内容"))
                            .background(HeightWriter { box.filled = $0 })
                    }
                    .padding(12)
                    .frame(width: 320, height: 160)
                    .background(Color(nsColor: .windowBackgroundColor))
                )
            }
            _ = try render(fixture, appearance: appearance,
                           to: scratch.appendingPathComponent("probe-\(tag).png"))
            XCTAssertGreaterThan(box.empty, 10,
                                 "\(tag)：空框量到 \(box.empty)pt ⇒ 布局根本没跑起来，这条判据在判空气")
            XCTAssertGreaterThan(box.filled, 10,
                                 "\(tag)：有字框量到 \(box.filled)pt ⇒ 布局根本没跑起来")
            // 容差 0.2pt，不是 1.5pt：两态的高度现在**只由钉死的数决定**
            // （文本列声明 22pt；× 的字形被 `.frame(14×14)` 锁住，加 4pt 命中区正好 22pt），
            // 所以任何不对称都是真回归 —— 连"去掉那个 14×14 之后漂的 0.5pt"都要红
            // （变异 M96 干的就是这件事）。留 0.2 只给浮点，不给字形度量。
            XCTAssertLessThanOrEqual(abs(box.empty - box.filled), 0.2,
                                     "\(tag) 下空框 \(box.empty)pt、有字框 \(box.filled)pt"
                                     + "（差 \(abs(box.empty - box.filled))pt）⇒ 打字时整颗搜索框会自己跳："
                                     + "这一行的定高者不是文本列")
            print("SEARCH_FIELD_IDEAL_HEIGHTS \(tag) empty=\(box.empty) filled=\(box.filled)")
        }
    }

    /// `@MainActor` 的闭包只能捕获引用类型，所以用类盒子（不是可变状态设计，是语法约束）。
    final class HeightBox {
        var empty: CGFloat = 0
        var filled: CGFloat = 0
    }

    /// 按行找"整行大部分像素都偏离主色"的连续带（用于量同一帧里两块控件的高度）。
    static func filledBands(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                            bytesPerRow: Int) -> [(Int, Int)] {
        // 主色：取四个角的中位近似（这里用左上角即可，帧的四角都是窗口底色）
        let r0 = Int(bytes[0]), g0 = Int(bytes[1]), b0 = Int(bytes[2])
        var bands: [(Int, Int)] = []
        var start = -1
        var previous = -1
        for y in 0..<height {
            let row = y * bytesPerRow
            var off = 0
            var x = 0
            while x < width {
                let o = row + x * 4
                if abs(Int(bytes[o]) - r0) + abs(Int(bytes[o + 1]) - g0) + abs(Int(bytes[o + 2]) - b0) > 12 {
                    off += 1
                }
                x += 1
            }
            let filled = Double(off) / Double(max(width, 1)) > 0.5
            if filled {
                if start < 0 { start = y }
                previous = y
            } else if start >= 0, previous >= 0, y - previous > 6 {
                bands.append((start, previous))
                start = -1
                previous = -1
            }
        }
        if start >= 0 { bands.append((start, previous)) }
        return bands
    }

    // MARK: - 笔画对比度探针（R21）

    /// 判据自己的地板。它们**不在产品令牌文件里**：
    /// `VisualTokens` 那条"只有声明没有消费者的令牌会打红"（R15 立的）在我把地板放进去时
    /// 立刻红了三条，而它抓得对 —— 地板不是产品画的东西，产品侧该有的是"控件穿哪一档"
    /// （`VisualInk`，两处真的在用它）。判据的参数就该住在判据旁边。
    enum InkFloor {
        /// 可点笔画对它自己的底：至少 3:1（WCAG 对非文字 UI 部件的线）。
        static let controlInk: Double = 3.0

        /// 探针盒里"这块区域真的有墨"的地板：低于它说明框贴到了空白处，
        /// 那条判据就退化成恒真（R18 那条"自适应阈值等于没有阈值"同族）。
        static let probeInkFraction: Double = 0.03
    }

    /// 一块帧上的一个**可点笔画**，用夹具内的 pt 坐标框出来。
    struct InkProbe {
        let fixture: String
        let what: String
        /// 夹具坐标系（pt，左上原点）。**必须是从帧上量出来的**，不是估的 ——
        /// 本轮五个候选框里有两个贴在空白上（`receipt` 的 × 与行首星标），
        /// 如果只报对比度，那两处会读到"背景 vs 背景 = 1.0"而红成一条假缺陷；
        /// 有了 `inkFloor` 才会红成它真正的意思："框贴到空白了，去看元素搬到哪儿了"。
        let rect: CGRect
    }

    /// 探针表。这张表**是起点不是全集**：加一处要先从帧上量出框（量法见
    /// `.scratch/motion-audit-2/inspect_r20.swift crop|stats`），估的框会被墨地板打回。
    ///
    /// 为什么表里既有已知过线的也有已知不过线的：一把只会被动在缺陷上的尺，
    /// 与一把永远绿的尺一样没有信息量 —— 它必须能同时说"这里 4.3，过"和"这里 1.9，不过"。
    static let controlInkProbes: [InkProbe] = [
        InkProbe(fixture: "search-field", what: "清除 ×（静置）",
                 rect: CGRect(x: 286, y: 80, width: 22, height: 22)),
        InkProbe(fixture: "detail-3-files", what: "多文件行的展开箭头（整行唯一的可展开记号）",
                 rect: CGRect(x: 29, y: 145, width: 14, height: 14)),
        InkProbe(fixture: "glass-pill", what: "药丸里的收藏星（`.secondary` 那一档的参照）",
                 rect: CGRect(x: 50, y: 38, width: 20, height: 20)),
        InkProbe(fixture: "sidebar-multi-select", what: "批量操作按钮（侧栏工具排）",
                 rect: CGRect(x: 200, y: 113, width: 20, height: 20)),
    ]

    /// 一块区域里"墨 vs 它自己的底"的 WCAG 对比度，以及这块里有多少墨。
    ///
    /// 三个设计决定：
    /// - **背景取众数**而不是四角：探针框可能整块压在控件上，四角与它不同底；
    /// - **字形取偏离最远的那 2%**而不是最值：一个抗锯齿亮点不该决定整颗按钮的可读性，
    ///   而"最暗的那个像素"恰恰最容易是噪声（R19 记过"像素容差为 0 时抗锯齿会淹没分类器"）；
    /// - 亮度用 WCAG 的 sRGB 线性化，不用"三通道总差" —— 后者在暗色下会系统性高估。
    static func inkContrast(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                            bytesPerRow: Int, rect: CGRect, scale: Double)
        -> (ratio: Double, inkFraction: Double) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (1.0, 0.0) }
        var luma: [Int] = []
        luma.reserveCapacity((x1 - x0) * (y1 - y0))
        for y in y0..<y1 {
            let row = y * bytesPerRow
            var x = x0
            while x < x1 {
                let o = row + x * 4
                luma.append(Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                                 + 0.0722 * Double(bytes[o + 2])).rounded()))
                x += 1
            }
        }
        // 众数按 8 级量化找：不量化的话，抗锯齿会把每个亮度值都摊薄成"只出现一次"。
        var histogram: [Int: Int] = [:]
        for value in luma { histogram[value / 8, default: 0] += 1 }
        let background = histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0
        let deviation = luma.map { (abs($0 - background), $0) }
            .sorted { $0.0 > $1.0 }
        let inkCount = max(1, luma.count / 50)
        let ink = deviation.prefix(inkCount)
        let inkLuma = ink.map { $0.1 }.reduce(0, +) / ink.count
        let coverage = Double(luma.filter { abs($0 - background) > 16 }.count) / Double(luma.count)
        return (Self.contrastRatio(inkLuma, background), coverage)
    }

    /// WCAG 2.x 的亮度比（1…21）。同色=1，纯黑/纯白=21。
    static func contrastRatio(_ a: Int, _ b: Int) -> Double {
        func channel(_ v: Int) -> Double {
            let c = Double(v) / 255
            return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
        }
        let la = channel(a) + 0.05, lb = channel(b) + 0.05
        return max(la, lb) / min(la, lb)
    }

    /// 尺的算术本身要有判据：一把没人验算过的尺，报出来的数字没有意义。
    /// 这一条**不覆盖管线**（它判的是纯函数），管线级判据是下面那条 `testActionableInk...`。
    func testContrastRulerArithmetic() {
        XCTAssertEqual(Self.contrastRatio(255, 0), 21.0, accuracy: 0.01, "黑白必须是 21:1")
        XCTAssertEqual(Self.contrastRatio(128, 128), 1.0, accuracy: 0.001, "同色必须是 1:1")
        // 中间档拿 WCAG 的公开算例核：#767676 对纯白是 4.54:1（网页正文的及格线就定在这）。
        XCTAssertEqual(Self.contrastRatio(118, 255), 4.54, accuracy: 0.05)
        // 单调性：**方向要跟着底走**。亮底上墨越暗越显眼，暗底上墨越亮越显眼。
        // 这条一开始写反了（我在暗底那一支也写成"越暗越高"），是这把尺自己打红的：
        // contrastRatio(180, 0)=10.13 而 contrastRatio(100, 0)=3.55 —— 黑底上"更亮"才是"更对比"。
        // 记下来是因为这一族的错长得像笔误，实际是"把一句只对一半的话当成普适规律"。
        XCTAssertGreaterThan(Self.contrastRatio(100, 255), Self.contrastRatio(180, 255),
                             "亮底上：墨越暗，对比度越高")
        XCTAssertGreaterThan(Self.contrastRatio(180, 0), Self.contrastRatio(100, 0),
                             "暗底上：墨越亮，对比度越高（与上面同一条规律，方向跟着底走）")
    }

    /// **可点的笔画必须过可辨线**（R21 / U-43）。
    ///
    /// 缺陷是**看着帧**发现的：清除 × 静置 1.86（亮）/ 2.22（暗），而它旁边占位符文字是 9.42 ——
    /// 同一帧、同一把尺、两个答案，说明尺没坏，是那两颗字用了给"注释"的颜色档。
    /// 详情区多文件行那颗展开箭头是同一族：它是**整行唯一的"我能展开"记号**，
    /// 却比旁边"这是什么类型"的图标更淡（1.88 / 2.27 vs 3.95 / 5.9）。
    ///
    /// 与 R20 那条命中区改动连起来读：**命中区抬大只解决点得中，不解决看得见**。
    ///
    /// 这条**自己拍自己量**（R20 预检立的规矩）：不许读 `testCaptureKeyViews` 写好的 PNG。
    func testActionableInkStaysAboveTheLegibilityFloor() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r21-ink-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for probe in Self.controlInkProbes {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == probe.fixture }) else {
                    return XCTFail("找不到夹具 \(probe.fixture) ⇒ \(probe.what) 这条探针没有对象")
                }
                let file = scratch.appendingPathComponent("\(probe.fixture)-judged-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
                }
                // 缩放比从**帧与夹具**算出来，不写死 2：夹具改尺寸时尺要跟着走，
                // 而不是悄悄按 @2x 去读一张 @1x 的图（那会把每个框都放大一倍）。
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let (ratio, coverage) = Self.inkContrast(bytes: base, width: rep.pixelsWide,
                                                         height: rep.pixelsHigh,
                                                         bytesPerRow: rep.bytesPerRow,
                                                         rect: probe.rect, scale: scale)
                XCTAssertGreaterThanOrEqual(coverage, InkFloor.probeInkFraction,
                            "\(probe.fixture) 的「\(probe.what)」在框 \(probe.rect) 里只有 "
                            + String(format: "%.1f%%", coverage * 100) + " 的墨 ⇒ 框贴到空白上了"
                            + "（元素搬走了就去量新位置，不许把地板调低）")
                XCTAssertGreaterThanOrEqual(ratio, InkFloor.controlInk,
                            "\(probe.fixture) 的「\(probe.what)」静置对比度 "
                            + String(format: "%.2f", ratio) + "（\(tag)，地板 "
                            + "\(InkFloor.controlInk)）⇒ 这是可点的笔画，看不见等于没有")
                print("INK \(probe.fixture)/\(probe.what) \(tag) ratio="
                      + String(format: "%.2f", ratio) + " ink="
                      + String(format: "%.1f%%", coverage * 100))
            }
        }
    }

    /// 造浮层夹具的入口，并且**把控制器关在闭包里保命**（R19）。
    ///
    /// 为什么需要这一层：`NSTableView` 的 `dataSource` / `delegate` 都是**弱引用**，
    /// 而 `QuickPickController` 正是它们。如果闭包里"现造一个控制器 → 返回面板 → 出作用域"，
    /// 控制器会被释放，表格的 dataSource 静默变成 nil ⇒ 0 行 ⇒ 帧仍然拍得出来，
    /// 只是拍到一张空面板，而它名字写着"这就是浮层"。
    /// 这一族的坑叫"载荷绿、消费侧坏"，这次坏的是所有权。
    enum QuickPickCapturePanel {
        static func builder(store: HistoryStore, query: String) -> @MainActor () -> NSWindow? {
            var kept: QuickPickController?
            return {
                if kept == nil {
                    kept = QuickPickController(historyStore: { store }, commit: { _ in })
                }
                guard let controller = kept else { return nil }
                return controller.windowForCapture(query: query)
            }
        }
    }

    // MARK: - 渲染

    private func render(
        _ fixture: Fixture,
        appearance: NSAppearance.Name,
        to file: URL
    ) throws -> CaptureMetrics {
        let size = fixture.size
        // 放进真实（离屏）窗口：裸 NSHostingView 没有 window 时 SwiftUI 的
        // GeometryReader / maxWidth 会退化，整块内容被压到左下角。
        _ = NSApplication.shared
        // 必须同时改"进程外观"：List 这类由 AppKit 承载的控件，其嵌套 hosting view
        // 解析颜色时看的是 NSApp.effectiveAppearance，而不是我们注入的 colorScheme。
        // 只注入 colorScheme 会拍出"深色底 + 黑色列表文字"的假不可读帧。
        let previousApplicationAppearance = NSApp.appearance
        NSApp.appearance = NSAppearance(named: appearance)
        defer { NSApp.appearance = previousApplicationAppearance }

        // 两族夹具的差别**只有"窗口是谁建的"**：
        // SwiftUI 夹具由这里建一个离屏窗口；AppKit 夹具（浮层）拍的是**产品自己的那个窗口**。
        // 这不是风格选择：R19 第一版把浮层的 `contentView` 摘出来搬进新窗口，
        // 结果 `NSStackView` 塌成 24×49、`NSScrollView` 变成 0×0、
        // `table.visibleRect` 是 0×0（行有 5 条，一条都画不出来）——
        // 拍到的是一张被搬家弄坏的空面板，而它的名字写着"这就是浮层"。
        let window: NSWindow
        let host: NSView
        if let buildAppKit = fixture.appKit {
            guard let product = buildAppKit(), let content = product.contentView else {
                // 建不出窗口必须**当场红**：安静地跳过的话，基线里会少一张没人注意的帧，
                // 而"少了两帧"与"换了两帧"是两回事（R13 核老账时刚记过）。
                XCTFail("AppKit 夹具没建出窗口（\(file.lastPathComponent)）⇒ 宁可红，也不许拍一张空窗当浮层")
                throw CaptureError.emptyAppKitFixture
            }
            window = product
            host = content
            window.appearance = NSAppearance(named: appearance)
        } else {
            let themed = fixture.build().environment(\.colorScheme, appearance == .darkAqua ? .dark : .light)
            let hosting = NSHostingView(rootView: themed)
            // R18：**不让内容反过来改窗口尺寸**。
            // `NSHostingView` 在 macOS 13+ 默认带 `.idealSize` 的 sizingOptions，会把
            // "内容的理想高度"写回窗口的 min/max content size —— 于是夹具声明的
            // `NSSize(width:height:)` 只是**一个建议**。实测有 6 张帧的名字在撒谎：
            //   content-with-notice-750x560 → 实际 750x1304（提示条把理想高度顶高了，窗口跟着长）
            //   menubar-recommendations-320x320 → 实际 320x170（内容比框矮，窗口缩了）
            //   menubar-empty-320x120 → 实际 320x86
            // 最要紧的是第一条：那张帧的**职责**是"提示条插进 ContentView 会不会把布局挤坏"，
            // 而窗口偷偷长到 1304 ⇒ 它从来没有挤过，问题被量尺自己绕开了。
            if #available(macOS 13.0, *) {
                hosting.sizingOptions = []
            }
            let created = NSWindow(
                contentRect: NSRect(origin: .zero, size: size),
                styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                backing: .buffered,
                defer: false
            )
            created.appearance = NSAppearance(named: appearance)
            created.titlebarAppearsTransparent = true
            hosting.frame = NSRect(origin: .zero, size: size)
            hosting.autoresizingMask = [.width, .height]
            created.contentView = hosting
            // 12.x 没有 `sizingOptions`，用 min/max 把窗口钉在夹具给的尺寸上（同一件事的旧写法）。
            // 浮层那一路**不设 min/max**：那个尺寸是产品自己定的（420×300），
            // 夹具只能核对它、不能改写它 —— 下面那条尺寸断言因此才有意义。
            created.contentMinSize = size
            created.contentMaxSize = size
            created.setContentSize(size)
            window = created
            host = hosting
        }
        // AppKit 夹具**不走强制约束布局**（R19 实测）：`layoutSubtreeIfNeeded()` 会把
        // `NSStackView` 从"帧 + autoresizing 撑满 420×300"重排成"按内容拟合尺寸 24×49"，
        // 于是滚动视图 0×0、表格 `visibleRect` 0×0 —— 行有 5 条，一条都画不出来。
        // 真实 App 里这一步从来不做：面板靠 `makeKeyAndOrderFront` 走自己的显示周期。
        if fixture.appKit == nil {
            window.layoutIfNeeded()
            host.layoutSubtreeIfNeeded()
        }

        // 内容要等一次异步刷新才落定的夹具在这里 settle（会转 runloop）。
        // 放在"关 caret"之前：转完 runloop 可能装出新的 field editor，必须让后面的静默与重排照常生效。
        fixture.settle?()

        // 拍帧前先把插入点 caret 清掉：field editor 的光标是**闪烁**的，
        // 同一份代码连拍两次会因此出现最大 251 的通道差（实测：亮色 content 帧 x≈262 处
        // 一条约 100 像素高的竖线时有时无，30/58 帧都受这层噪声影响）。
        // 噪声在，"改动前后逐帧对比"就没有判别力 —— 所以先让窗口交出第一响应者，
        // 再递归把子树里所有 NSTextView 的插入点关掉。
        window.makeFirstResponder(nil)
        Self.silenceCarets(in: host)
        if fixture.appKit == nil {
            host.layoutSubtreeIfNeeded()
        }

        // R19：**只给 AppKit 夹具**补一次"真实显示周期"。
        //
        // 仓库外 spike（`.scratch/motion-audit-2/spike_r19_capture.md`）的读数：
        // 同一棵 `NSScrollView > NSTableView` 树，窗口没上屏时 `cacheDisplay` 得到
        // **0 个不透明像素**；orderFront 到屏幕外 + 转一圈 runloop + `tile()` 之后是 12291，
        // 再选中一行是 61142（差的 4.9 万像素就是选中行那块填充）。
        // 而 `NSScrollView` 不上屏时 `documentView.visibleRect` 是 0×0 ——
        // 表格不是"画不出"，是**还没轮到它画**。
        //
        // 为什么只作用于 AppKit 夹具：先量过再决定范围。把这一套加在 SwiftUI 路径上跑一遍
        // 96 帧，`transparent` 与 `blackBandPt` 逐帧不变（SwiftUI 的 List 自己会走布局），
        // 既然没有收益就不给既有帧引入任何风险。
        // 顺带这条实验也**否掉了 R18 写下的机制**：`List` 的选中黑块在上屏之后仍然是黑块，
        // 因为要 key window 才有 emphasized 高亮，而测试进程 `isKeyWindow=false` ——
        // 那是"拿不到前台"的限制，不是"材质不可合成"。
        if fixture.appKit != nil {
            window.setFrameOrigin(NSPoint(x: -20000, y: -20000))
            window.orderFrontRegardless()
            RunLoop.main.run(until: Date().addingTimeInterval(0.2))
            Self.tileScrollViews(in: host)
            window.display()
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }

        guard let contentView = window.contentView else {
            throw XCTSkip("窗口没有 contentView（\(file.lastPathComponent)）")
        }
        // **帧的名字必须等于帧的尺寸**（R18）。
        // 文件名里的 `WxH` 是审查者唯一的尺寸线索；窗口被内容偷偷改过之后，
        // 这个名字就从"证据"变成了"猜测"。所以量一次，不符就红 ——
        // 而不是"反正 sha 会变，有人会发现"（sha 变了只会让人以为界面改了）。
        let honored = contentView.bounds.size
        XCTAssertLessThan(abs(honored.width - size.width), 0.5,
                          "\(fixture.name)：夹具要 \(Int(size.width))pt 宽，窗口实际 \(Int(honored.width))pt ⇒ "
                          + "帧名与实际尺寸不符，这张帧不能证明它声称的那件事")
        XCTAssertLessThan(abs(honored.height - size.height), 0.5,
                          "\(fixture.name)：夹具要 \(Int(size.height))pt 高，窗口实际 \(Int(honored.height))pt ⇒ "
                          + "内容把窗口顶大/缩小了，"
                          + "例如「提示条会不会挤坏布局」这类判据会在一个从未被挤的窗口上判通过")
        let bounds = contentView.bounds
        // 不要手工改 rep.size：bitmapImageRepForCachingDisplay 已按 backing scale 建好尺寸，
        // 改它会让内容只画进 1/4 画面（我第一次拍到的"大片空白"就是这个假象）。
        guard let rep = contentView.bitmapImageRepForCachingDisplay(in: bounds) else {
            throw XCTSkip("无法创建位图缓存（\(file.lastPathComponent)）")
        }
        // 关键：cacheDisplay 期间必须把 appearance 设为"当前绘制外观"，
        // 否则只有 window 自身变暗、SwiftUI 子树仍按 aqua 解析颜色，
        // 会拍出"半明半暗"的假帧（第一次拍设置页就踩到了）。
        if #available(macOS 11.0, *) {
            window.appearance?.performAsCurrentDrawingAppearance {
                contentView.cacheDisplay(in: bounds, to: rep)
            }
        } else {
            NSAppearance.current = window.appearance
            contentView.cacheDisplay(in: bounds, to: rep)
            NSAppearance.current = nil
        }

        let (data, transparent) = try flattenedPNG(from: rep, appearance: appearance)
        var blackBand = 0.0
        var bottomInk = 0.0
        if let base = rep.bitmapData {
            blackBand = Self.blackBandHeight(bytes: base,
                                             width: rep.pixelsWide,
                                             height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow,
                                             backingScale: CGFloat(rep.pixelsWide) / max(size.width, 1))
            bottomInk = Self.bottomInkFraction(bytes: base,
                                               width: rep.pixelsWide,
                                               height: rep.pixelsHigh,
                                               bytesPerRow: rep.bytesPerRow)
        }
        try data.write(to: file)
        return CaptureMetrics(transparent: transparent, blackBandPt: blackBand,
                              bottomInkFraction: bottomInk)
    }

    /// 最底一行里"偏离主色 >12"的像素占比（0…1）。
    ///
    /// 主色取左上角：这批夹具的底都是整块 `windowBackgroundColor`，
    /// 而**被裁的元素一定会压在底边上**（半截字形、半截描边），底边留白则说明放得下。
    /// 阈值 12 与 `filledBands` 同一条线 —— 两处各写一个数字的话，
    /// "松一档"会让一条判据先瞎（R18 那条"两处各写一个数"同族）。
    static func bottomInkFraction(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                  bytesPerRow: Int) -> Double {
        guard width > 0, height > 0 else { return 0 }
        let r0 = Int(bytes[0]), g0 = Int(bytes[1]), b0 = Int(bytes[2])
        let row = (height - 1) * bytesPerRow
        var ink = 0
        var x = 0
        while x < width {
            let o = row + x * 4
            if abs(Int(bytes[o]) - r0) + abs(Int(bytes[o + 1]) - g0) + abs(Int(bytes[o + 2]) - b0) > 12 {
                ink += 1
            }
            x += 1
        }
        return Double(ink) / Double(width)
    }

    /// 递归 `tile()` 子树里所有滚动视图。
    /// `NSScrollView` 的 `documentView` 只在 tile 之后才有有效的 `visibleRect`，
    /// 而 `visibleRect` 为空 ⇒ `NSTableView` 一行都不准备 ⇒ `cacheDisplay` 画不出东西。
    /// 这一步在真实 App 里由"窗口上一次屏"顺带做掉，所以只有离屏捕获需要补。
    private static func tileScrollViews(in view: NSView) {
        if let scroll = view as? NSScrollView {
            scroll.tile()
            scroll.reflectScrolledClipView(scroll.contentView)
        }
        view.subviews.forEach { tileScrollViews(in: $0) }
    }

    /// 递归关掉子树里所有文本视图的插入点（含 `NSTextField` 的 field editor）。
    /// 只 `makeFirstResponder(nil)` 不够：SwiftUI 包着的 `NSTextField` 可能已经装好了 field editor，
    /// 而闪烁由定时器驱动，两次拍摄落在闪/不闪的两拍上就会出现整条竖线的差异。
    /// 注意 `shouldDrawInsertionPoint` 是只读的，所以用"把插入点画成透明"这一条路径。
    private static func silenceCarets(in view: NSView) {
        if let textView = view as? NSTextView {
            textView.insertionPointColor = .clear
            textView.needsDisplay = true
        }
        if let textField = view as? NSTextField, let editor = textField.currentEditor() as? NSTextView {
            editor.insertionPointColor = .clear
            editor.needsDisplay = true
        }
        view.subviews.forEach { silenceCarets(in: $0) }
    }

    /// 量出"没被画出来的像素"比例，并把帧铺到真实窗口底色上。
    /// 不铺底的话，暗色帧里未绘制的区域会被看图器合成成白色，
    /// 于是"白底 + 白字"的详情区看起来像整块空白（真实假缺陷来源）。
    private func flattenedPNG(from rep: NSBitmapImageRep, appearance: NSAppearance.Name) throws -> (Data, Double) {
        guard let source = rep.cgImage else { throw CaptureError.noBitmap }
        let width = source.width
        let height = source.height
        let rect = CGRect(x: 0, y: 0, width: width, height: height)
        let space = CGColorSpace(name: CGColorSpace.sRGB) ?? CGColorSpaceCreateDeviceRGB()
        let contextInfo = CGImageAlphaInfo.premultipliedLast.rawValue

        func makeContext() -> CGContext? {
            CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                      bytesPerRow: width * 4, space: space, bitmapInfo: contextInfo)
        }

        // 1) 探针：只画内容，空着的地方 alpha 仍是 0。
        //    计数交给 `Self.transparentFraction(bytes:...)` —— 与浮层那条判据同一把尺、
        //    同一个阈值，不在这里留第二份内联循环（两份循环会各自漂）。
        var transparentFraction = 0.0
        if let probe = makeContext() {
            probe.draw(source, in: rect)
            if let base = probe.data {
                transparentFraction = Self.transparentFraction(
                    bytes: base.bindMemory(to: UInt8.self, capacity: width * height * 4),
                    width: width, height: height, bytesPerRow: width * 4
                )
            }
        }

        // 2) 合成：铺一层该外观下的窗口底色
        guard let out = makeContext() else { throw CaptureError.noBitmap }
        out.setFillColor(windowBackgroundColor(for: appearance))
        out.fill(rect)
        out.draw(source, in: rect)
        guard let flat = out.makeImage() else { throw CaptureError.noBitmap }
        guard let data = NSBitmapImageRep(cgImage: flat).representation(using: .png, properties: [:]) else {
            throw CaptureError.noPNG
        }
        return (data, transparentFraction)
    }

    private func windowBackgroundColor(for appearance: NSAppearance.Name) -> CGColor {
        var resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
        if #available(macOS 11.0, *) {
            NSAppearance(named: appearance)?.performAsCurrentDrawingAppearance {
                resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
            }
        } else {
            let previous = NSAppearance.current
            NSAppearance.current = NSAppearance(named: appearance)
            resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
            NSAppearance.current = previous
        }
        return resolved.cgColor
    }
}
