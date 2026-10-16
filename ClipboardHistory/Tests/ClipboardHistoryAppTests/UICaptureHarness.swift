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

    /// 正对照帧：一张**已知底边有墨**的帧 —— `row-clipped-control`，
    /// 同一颗 `HistoryRowButton` 装进 58pt 的外框再 `.clipped()`，帧上看得见第二行日期被切成半截。
    ///
    /// 存在的理由与 `materialBlindSpotFixtures` 同一族：一把只在"该红的没红"上被检验的尺
    /// 没有被检验过。R22 当时点的是 `sidebar-history`（"滚动区在帧底切一半是它的正常行为"），
    /// R36 查出那张帧读到的 100% 其实是**色差**（尺的参照点是左上角那一个像素，U-60），
    /// 于是这条判据从写下到 R37 之间**没有过有效的正对照**。
    /// 换掉它还有第二条理由：`sidebar-history` 在 runner 上读 0% ——
    /// 一张"要看这台机器脸色"的对照物不当对照物。
    /// 本机实测：亮 **10.8%** / 暗 **12.5%**，线取 5%（`bottomEdgeControlMinFraction`）。
    static let bottomEdgeInkCanary = "row-clipped-control"

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
        // R40 新加的这张走的是**同一个** `ContentView`，读数与两张姐姐帧逐字相同
        // （亮暗都是 `transparent=50.7% blackBandPt=66 bottomInk=0.1%`，姐姐帧 46.3% / 66 / 0.1%）
        // ⇒ 同一处离屏伪影（侧栏选中行画成一整块纯黑），不是新缺陷。加名单前先看了那张帧：
        // 横幅本身完好（红底、两行、"知道了"垂直居中、无截断），黑的是左下侧栏那一行。
        "content-with-copy-failure-notice",
        "sidebar-history", "sidebar-multi-select", "sidebar-multi-select-min", "sidebar-favorites",
    ]

    /// 「这张帧天生就是稀的」名单（R63）—— 与上面那份同一族：**尺的假设名单**，不是缺陷名单。
    ///
    /// 为什么 `transparent > 0.95` 那条门槛在浮层上不成立：那条门槛假设"帧的底子是画满的，
    /// 所以 95% 未绘制 ⇒ 捕获坏了"。而快速选择浮层**没有自绘背景**
    /// （`drawsBackground=false` 的滚动视图 + `backgroundColor=.clear` 的表格 + 面板底色由窗口自己填，
    /// `cacheDisplay` 只画子树），于是一张完全正确的浮层帧里，墨就只有那些字和那一块选中填充：
    /// 本机实测 5 行 ⇒ 未绘制 85.8%，2 行 ⇒ 88.5%，0 行 + 一句话 ⇒ 97.9%。
    /// 只有最后一张过不了那条门槛 —— 拿 95% 判它"捕获失效"，是把尺子的假设当成了事实。
    ///
    /// 豁免不许变成"这类帧从此不看"，所以两条各自承重的东西跟着一起进来：
    ///   · 名单里每一张**无论这台机器判不判它稀**，都要过一条正对照：`drawn > 0.5%`
    ///     （门槛从两台机器的读数来：本机 2.1%、runner 5.1%，而"捕获真的坏了"是 0.0%）——
    ///     稀可以，全空不行；
    ///   · "名单过期"由一次运行**内部**的兄弟比较判：空结果态必须明显比 5 行的列表态更空。
    ///     以前判的是"这张这次没走豁免分支 ⇒ 红"，而它在 runner 上是**假红**
    ///     （`quickpick-empty` 本机未绘制 97.9%、runner 94.9%，门槛 95.0% ——
    ///     同一张帧在一台机器上需要豁免、在另一台上不需要）。绝对数会随 backing scale
    ///     与字体渲染漂移，"这一格有没有内容"不会（R38 那条规矩在我自己新写的守卫上重犯了一次）。
    ///   · "帧名与内容相符"也不靠像素：`testQuickPickTypedFixtureShowsFilteredRowsNotAnEmptyList`
    ///     从产品入口直接数行（typed 必须 1 ≤ 行 < 全量）。第一版 `quickpick-typed`
    ///     的查询词命中 0 条（帧名 typed、内容 empty）就是被"看图 + 这条兄弟比较"抓到的。
    /// 而"该有的东西在不在"由两条产品入口级判据判：
    /// `testQuickPickOverlayFillsItsPanelAndCanBeCaptured`（行画得出来）与
    /// `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot`（那句话在、且落在那一格）。
    static let sparseByDesignFixtures: Set<String> = ["quickpick-empty"]

    /// 上面那份名单的正对照门槛。**只能从读数来**（见上面的实测数），不许拍脑袋。
    static let sparseByDesignInkFloor: Double = 0.005

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

    // MARK: - 读数的第二条通道（R64 / BACKLOG 96）

    /// 静态语境与实例语境各一个名字（与动效卷 `MotionFilmstripTests` 同一形状）：
    /// Swift 不允许实例方法不加限定地调静态成员，而这一卷里 69 处读数散在两种语境中 ——
    /// 与其到处写 `CaptureReadings.emit`，不如让两条语境共用一个名字。
    /// 真正的通道在 `CaptureReadings.swift`：**这个文件里一行 `print` 都不许有**，
    /// 由 `testCaptureReadingsUseTheFileChannel` 钉住。
    static func emit(_ line: String) { CaptureReadings.emit(line) }

    /// 把 `//` 注释与 `/* … */` 块注释去掉，只留代码。
    /// 存在的理由：守卫扫的是"有没有游离的调用"，而这一卷的注释里满是
    /// "以前这里是 `print(...)`"这种句子 —— 不剥注释的话，守卫会把**解释自己**判成违规，
    /// 于是下一次有人为了变绿去删注释（R55 的 M276 就是这条家族：守卫读到自己的文本）。
    static func codeOnly(_ source: String) -> String {
        var out: [String] = []
        var inBlock = false
        for line in source.components(separatedBy: "\n") {
            var trimmed = line
            if inBlock {
                if let end = trimmed.range(of: "*/") {
                    trimmed = String(trimmed[end.upperBound...])
                    inBlock = false
                } else {
                    continue
                }
            }
            while let start = trimmed.range(of: "/*"), let end = trimmed.range(of: "*/"), start.lowerBound < end.upperBound {
                let head = String(trimmed[..<start.lowerBound])
                let tail = String(trimmed[end.upperBound...])
                trimmed = head + tail
            }
            if let range = trimmed.range(of: "//") {
                trimmed = String(trimmed[..<range.lowerBound])
            }
            out.append(trimmed)
        }
        return out.joined(separator: "\n")
    }

    private func emit(_ line: String) { Self.emit(line) }

    /// 取一条方法签名之后的**方法体**（到第一处「换行 + 四空格 + }」为止）。
    ///
    /// 为什么要有它：源码级守卫只会 `contains`，而整文件 `contains` 分不清
    /// "这个调用在这个方法里" 与 "这个调用在别处" —— 把 `clearHover` 从 `rebuildRows`
    /// 挪进别的函数，我那句"打字时那层灰每次都被拆掉"就断了，而整文件仍然绿。
    ///
    /// 结尾判定用缩进而不是括号配平：这个文件里的方法都是 4 空格缩进、方法体 8 空格，
    /// 所以第一处「四空格的 }」就是本方法的结尾。**换文件要重新验这个前提**，
    /// 前提不成立时它返回空串或截短 —— 所以调用点必须带正对照（扫不到就红），
    /// 不许静默返回整份源码让守卫"永远看得见"。
    static func functionBody(named signature: String, in source: String) -> String {
        guard let start = source.range(of: signature) else { return "" }
        let rest = String(source[start.upperBound...])
        guard let end = rest.range(of: "\n    }") else { return "" }
        return String(rest[rest.startIndex..<end.lowerBound])
    }

    private var outputDirectory: URL? {        guard let path = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"], !path.isEmpty else {
            return nil
        }
        let url = URL(fileURLWithPath: path, isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    /// 捕获卷的读数必须**两条通道都有**（R64 / BACKLOG 96）。
    ///
    /// 立的理由不是"想统一风格"：R63/R64 量到 `swift test` 的 stdout **会成块丢** ——
    /// 本轮同一批代码两遍，捕获卷 488 行读数里 stdout 分别少了 324 行与 238 行，
    /// 少的都是连续大块（切点落在行中间），五条判据自写的 marker 两遍全丢，
    /// 而 37 / 775 条用例的结论行一条没少、作业 0 退出。
    /// 也就是说"今天判了什么"这件事，
    /// 可以整块消失而报表仍然是绿的。
    ///
    /// 扫描规则故意写成**绝对**的："这个文件里 `print` 的出现次数 = 0"。
    /// 不给"通道实现自己那一行"开白名单 —— 白名单就是下一次绕过去的入口
    /// （R55 的 M276：守卫在自己的失败消息里读到了被搜的串，于是把真调用删掉它仍然绿）。
    /// 通道实现因此单独住在 `CaptureReadings.swift`。
    func testCaptureReadingsUseTheFileChannel() throws {
        // ① 被搜的串不能原样出现在守卫自己的文本里：拼出来。
        let printCall = "pr" + "int("
        let source = UICaptureTests.codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        let strays = source.components(separatedBy: "\n").filter { $0.contains(printCall) }
        XCTAssertTrue(strays.isEmpty,
                      "捕获卷里有 \(strays.count) 行读数只走 stdout：\(strays.prefix(3).map { String($0.trimmingCharacters(in: .whitespaces).prefix(48)) })"
                      + " ⇒ 通道丢一次的那天，这些读数一条都不剩（BACKLOG 96）。改走 `emit`")

        // ② 正对照：扫描本身得抓得住三种真实写法，并且**不**抓 `emit`。
        //    没有这一步，"零条游离"这句话可能只是扫描坏了的别名
        //    （R56 那版守卫就是因为只列举了两种写法，漏掉了 `print("MOTION \(name) …` 那一整族）。
        //
        //    三种写法必须**自带**被搜的串，不能拿 `printCall` 拼出来。
        //    R64 的变异对照量到了这件事（M338）：用 needle 拼正对照，等于拿尺子上的刻度去验这把尺 ——
        //    把 needle 改错成多一个空格，对照仍然 3/3，而 ① 那条扫描已经一条游离都抓不到了。
        //    这里的 `p` 写成 `\u{0070}`：运行时串里是真的那三个字母加左括号，
        //    源码文本里不是（否则 ① 会把对照自己判成违规，正是 R55 M276 那一族）。
        let forms = ["  \u{0070}rint(\"CAPTURE_X 1)",
                     "  \u{0070}rint(String(format: \"CAPTURE_Y %@\", a))",
                     "  \u{0070}rint(\"CAPTURE \(name) frames=1)"]
        let caught = forms.filter { $0.contains(printCall) }
        XCTAssertEqual(caught.count, 3,
                       "正对照只抓到 \(caught.count)/3 种写法 ⇒ 用来扫的串和被扫的真串已经不是同一个"
                       + "（这一格红 = needle 被改坏的样子，而不是『这条卷很干净』）")
        XCTAssertFalse("  emit(\"CAPTURE_Z 1)".contains(printCall),
                       "扫描把 `emit` 也算成游离 ⇒ 它会逼着人把 emit 改名，判据就空转了")

        // ③ 通道本身。marker 带 uuid：读到**上一遍**留下的同名文件也算通过的话，
        //    这一格就只是在证明"有人写过这个文件"。
        let marker = "CAPTURE_SELFTEST_\(UUID().uuidString.prefix(8))"
        let second = marker + "-2"
        emit(marker)
        emit(second)
        let text: String
        do {
            text = try String(contentsOf: CaptureReadings.readingsURL, encoding: .utf8)
        } catch {
            return XCTFail("文件通道没写出来（\(CaptureReadings.readingsURL.path)）⇒ `emit` 只剩 print，BACKLOG 96 没修")
        }
        XCTAssertTrue(text.contains(marker), "文件里没有这一遍的 marker ⇒ 要么没落盘，要么读到的是旧文件")
        XCTAssertTrue(text.contains(second), "第二条 marker 没落盘 ⇒ 追加逻辑坏了（第一次写用了 `write(to:)`，之后必须走 FileHandle）")
        let firstIndex = text.range(of: marker)!.lowerBound
        let secondIndex = text.range(of: second)!.lowerBound
        XCTAssertLessThan(firstIndex, secondIndex, "两条 marker 在文件里的顺序反了 ⇒ 读回来的不是写入的那一份")
        let lines = text.split(separator: "\n").map(String.init)
        XCTAssertGreaterThanOrEqual(lines.count, 2, "文件通道里只有 \(lines.count) 行 ⇒ 这一卷的读数根本没进来")
        emit("CAPTURE_READINGS_SELFTEST 文件通道 \(lines.count) 行 @ \(CaptureReadings.readingsURL.path)")
    }

    /// R81 / BACKLOG 112：并发写读数**不许缝行、不许少行**。
    ///
    /// 这一格不是预防性的洁癖 —— 它有一个具体的受害者：R79 那一遍 CI 里
    /// `QUICKPICK_FOCUS 暗 …` 那一行被缝进了 `MENUBAR_FITTING …` 的肚子里
    /// （日志里那一行前半属于另一条判据、后半属于我，而 `MENUBAR_FITTING` 自己的结论没了），
    /// 而它正是"焦点那条轴在 runner 上能不能判"那一个问题（BACKLOG 109）要的答案。
    /// 上一轮我只能改用**红的行号**反证闸门开没开 —— 那是拿推理补一条被毁掉的证据。
    ///
    /// 三条断言各拦一种坏法（都在**同一把尺**上：整行回读）：
    ///   ① 行数 = 线程数 × 每线程条数 ⇒ 拦"整卷被后写的抹掉"（`openedURLs` 那一步原来没有锁）；
    ///   ② 每行的**行首 (t,i) 与行尾 (t,i) 必须相等** ⇒ 拦缝行：
    ///      两行缝在一起，一定会出现"头是 3/17、尾是 5/2"这种对不上的行 ——
    ///      这一条是整格的要害：**只看"有没有变化"抓不到缝行，只看位置同一性才抓得到**
    ///      （与 R76 那条"缩区域之后必须量位置同一性"同一条教训）；
    ///   ③ 每个 (t,i) 恰好出现一次 ⇒ 拦"覆盖"（两个线程 seek 到同一个偏移，后写的把前写的盖掉）。
    ///
    /// **这一格测不到的**（照实说）：`emit` 的 **stdout** 那一条腿。进程内没法把自己 print 出去的东西
    /// 再读回来，而 CI 上被毁掉的正是 stdout 那一份 —— 它只能由"闸门读文件通道"这条设计本身兜住
    /// （文件通道现在是原子的，stdout 丢了就从文件补回）。
    func testConcurrentReadingsNeitherSpliceNorDropALine() throws {
        let threads = 8, perThread = 60
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("capture-hammer-\(UUID().uuidString.prefix(8)).log")
        // 一行 900 多个字节：短行即使被交错也看不出形状，长行才复现得出 CI 上那种切法。
        let pad = String(repeating: "x", count: 900)
        DispatchQueue.concurrentPerform(iterations: threads) { t in
            for i in 0..<perThread {
                CaptureReadings.appendForced("CAPTURE_HAMMER t=\(t) i=\(i) \(pad) END t=\(t) i=\(i)", to: url)
            }
        }
        let written = threads * perThread
        let lines = (try String(contentsOf: url, encoding: .utf8))
            .split(separator: "\n", omittingEmptySubsequences: true).map(String.init)
        XCTAssertEqual(lines.count, written,
                       "锤了 \(written) 行只读回 \(lines.count) 行 ⇒ 有读数**没了**（整卷被后写的那一份抹掉，"
                           + "或两个线程 seek 到同一个偏移互相覆盖）—— 那种丢法没有任何一条判据会红")
        var mismatched: [String] = []
        var pairs = Set<String>()
        for line in lines {
            let tokens = line.split(separator: " ").map(String.init)
            let head = tokens.count > 2 ? tokens[1] + "/" + tokens[2] : "-"
            let tail = tokens.count > 6 ? tokens[tokens.count - 2] + "/" + tokens[tokens.count - 1] : "-"
            guard tokens.count == 7, tokens[0] == "CAPTURE_HAMMER",
                  tokens[3] == pad, head == tail else {
                mismatched.append("头=\(head) 尾=\(tail) 词数=\(tokens.count) 长度=\(line.count)")
                continue
            }
            pairs.insert(head)
        }
        XCTAssertTrue(mismatched.isEmpty,
                      "有 \(mismatched.count) 行的**行首与行尾不是同一个 (t,i)** ⇒ 两行被缝成一行："
                          + "\(mismatched.prefix(3)) —— 这正是 R79 毁掉 `QUICKPICK_FOCUS 暗` 的那个形状，"
                          + "而它毁掉的是**决定 BACKLOG 109 的那一条读数**")
        XCTAssertEqual(pairs.count, written,
                       "\(written) 行里只有 \(pairs.count) 个不同的 (t,i) ⇒ 有行被**整行覆盖**"
                           + "（缝行会留下对不上的头尾，覆盖不会 ⇒ 这一格与上面那格各拦一种）")
        emit("CAPTURE_HAMMER 结果=线程 \(threads) × 每线程 \(perThread) = \(written) 行，"
            + "整行回读全部头尾一致（临时文件，不进读数卷）")
        try? FileManager.default.removeItem(at: url)
    }

    /// R19 立的是"浮层还拍不到"，R63 把它**翻过来**：那条判据钉的现象（stack 塌）其实是产品缺陷，
    /// 而它给出的原因（"stack 在捕获环境里塌，真实 App 里撑满 420×300"）是错的 ——
    /// 两条路都塌，因为产品只给了 `frame` + `autoresizingMask`，而 `NSStackView` 生下来
    /// `translatesAutoresizingMaskIntoConstraints == false`，那两行因此都是空操作。
    /// 修完之后这条判据改钉**契约**，五件事各自承重，红的时候读的是不同的话：
    ///   · `rows > 0` + `dataSourceIsController` 守**所有权**：`NSTableView.dataSource` 是弱引用，
    ///     控制器一旦被释放，行数静默掉成 0，而帧仍然"合法"（见 `QuickPickCapturePanel`）；
    ///   · **内容必须占满面板**（两条轴都量）：R63 那个缺陷的全部表现就是这一条，
    ///     塌的时候 stack 宽/高只有面板的 5.7% / 16%，而面板上四分之三是空白；
    ///   · 那张表的 `visibleRect` 至少容得下两行候选：这是"行画不画得出来"的直接量 ——
    ///     塌的时候它是 0×0，而 `frame` 看着仍然像回事；
    ///   · `transparent < 0.9`：还能不能拍。它现在该绿；红了说明**捕获通道**又坏了，
    ///     而"stack 塌了"不再是可引用的解释（那条已经修掉了），必须去查新的原因；
    ///   · 判据里不写 420 / 300 这类字面量：约定是"内容占满面板"，不是"面板 420 宽"。
    ///     面板尺寸哪天改，这条判据不需要跟着改。
    func testQuickPickOverlayFillsItsPanelAndCanBeCaptured() throws {
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
        var rowHeight: CGFloat = -1
        var stackFrame: CGRect?
        var tableVisible: CGRect?
        var dataSourceIsController = false
        func find(_ view: NSView) {
            if let table = view as? NSTableView {
                if table.dataSource is QuickPickController {
                    dataSourceIsController = true
                    rows = max(rows, table.numberOfRows)
                    tableVisible = table.visibleRect
                    rowHeight = table.rowHeight
                }
            }
            // 按**身份**认 stack：子树里含有"数据源是产品的表"的那个 NSStackView。
            // R62 那版探针在这里用 `max(宽度)` + "最后一个赢"混着读，于是三条读数
            // 可能来自不同的 stack —— 面板整棵树里不止一个 NSStackView。
            if let stack = view as? NSStackView,
               Self.containsProductTable(stack) {
                stackFrame = stack.frame
            }
            view.subviews.forEach(find)
        }
        find(content)
        guard let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds) else {
            return XCTFail("建不出位图缓存 ⇒ 这条判据没有对象")
        }
        content.cacheDisplay(in: content.bounds, to: rep)
        let transparent = Self.transparentFraction(of: rep)
        emit("CAPTURE_PROBE quickpick transparent=\(String(format: "%.1f", transparent * 100))%"
              + " rows=\(rows) stack=\(stackFrame.map { NSStringFromRect($0) } ?? "nil") "
              + "tableVisible=\(tableVisible.map { NSStringFromRect($0) } ?? "nil") "
              + "dataSourceIsController=\(dataSourceIsController)"
              + " bounds=\(NSStringFromRect(content.bounds))")
        XCTAssertGreaterThan(rows, 0,
                             "浮层表格 0 行 ⇒ 十有八九是控制器被释放了（`NSTableView.dataSource` 是弱引用），"
                             + "帧看起来仍然合法，其实拍的是一张空面板")
        XCTAssertTrue(dataSourceIsController,
                      "表格的数据源已经不是 `QuickPickController` ⇒ 拍到的行不是产品会画的那些行")
        XCTAssertLessThan(transparent, 0.9,
                          "浮层又拍不到了（transparent="
                          + "\(String(format: "%.1f", transparent * 100))%）。注意：R63 之后"
                          + "「stack 塌了」不再是可引用的解释（那条已经修掉，见下面两条），"
                          + "所以这是**捕获通道**坏了 —— 去查新的原因，别把这条门槛放松")
        guard let stack = stackFrame else {
            return XCTFail("找不到那个「装着产品表格的 NSStackView」⇒ 浮层的布局结构已经不是判据认识的那个形状")
        }
        let ratioW = stack.width / content.bounds.width
        let ratioH = stack.height / content.bounds.height
        XCTAssertGreaterThan(ratioW, 0.85,
                             "浮层内容只占面板宽度的 \(String(format: "%.0f", ratioW * 100))%"
                             + "（stack=\(NSStringFromRect(stack)) 面板=\(NSStringFromRect(content.bounds))）⇒ "
                             + "这就是 R63 那个缺陷：用户按下 ⌃⌥⇧V 看到的是一小块内容 + 大片空白。"
                             + "尺寸的拥有者必须显式写出来（贴边约束），`frame` + `autoresizingMask` 在 NSStackView 上是空操作")
        XCTAssertGreaterThan(ratioH, 0.85,
                             "浮层内容只占面板高度的 \(String(format: "%.0f", ratioH * 100))%"
                             + "（stack=\(NSStringFromRect(stack))）⇒ 同一族缺陷的另一条轴：垂直方向也一样，"
                             + "滚动视图会被压成 0 高")
        guard let visible = tableVisible else {
            return XCTFail("量不到那张表的 visibleRect ⇒ 「行画不画得出来」这一条没有对象")
        }
        XCTAssertGreaterThanOrEqual(visible.height, 2 * rowHeight,
                                    "表格的可视区只有 \(Int(visible.height))pt 高，而一行候选是 \(Int(rowHeight))pt ⇒ "
                                    + "连两行都放不下。R63 塌的时候这里是 0×0：行有几条都画不出来，"
                                    + "而 stack 的 frame 看着仍然像回事。"
                                    + "（阈值用表自己的 rowHeight，不写 34 这种字面量：那是产品定的，不是判据定的）")
    }

    /// 行首那一列 + **一条**标签左轴（R65 / BACKLOG 94、97）。
    ///
    /// 立的理由是一串实测：改之前 `quickpick-list` 那张帧里，纯文本行的标签从 **34.5pt** 起、
    /// 文件行的标签从 **56.5pt** 起（那 22pt 里装的是一个 📄 emoji —— 它写在文案里，不是视图），
    /// 于是五行里有两种左轴。把 emoji 换成"每行一枚 SF Symbol"同时解决三件事：
    /// 图标语言与侧栏一致、文案不再参与搜索匹配、左轴只剩一条。
    ///
    /// 三格各自承重，红的时候读的是不同的话：
    ///   · 每一行 `imageView?.image != nil` —— 符号名写错时 `NSImage(systemSymbolName:)` 返回 nil，
    ///     而 `NSImageView` 拿着 nil **什么都不画也不报错**，屏幕上只是那一格空了；
    ///   · 所有标签 minX 相同（0.5pt 容差）—— 这才是"共享一条左轴"的可执行定义；
    ///   · 夹具必须真有 ≥2 种类型（**正对照**）：全是文本时"左轴一致"会平凡为真，
    ///     那一格红是在提醒我这条判据今天没有对象。
    func testQuickPickRowsShareOneIconColumnAndOneLabelAxis() throws {
        let store = makePopulatedStore()
        let kinds = Set(store.entries.map { QuickPickController.rowSymbolName(for: $0.content) })
        // `build` 必须留在局部变量上：控制器被那个闭包捕获，而 `NSTableView.dataSource` 是弱引用 ——
        // 直接 `builder(...)()` 的话闭包当场释放，控制器跟着没了，表格只剩一张空面板
        // （本轮第一次就是这么红的：报的是"找不到那张产品表格"，坏的是持有关系）。
        let build = QuickPickCapturePanel.builder(store: store, query: "")
        guard let panel = build(),
              let content = panel.contentView else {
            return XCTFail("捕获入口建不出浮层窗口 ⇒ 这条判据失去了对象，必须红")
        }
        _ = NSApplication.shared
        let previousAppearance = NSApplication.shared.appearance
        defer {
            NSApplication.shared.appearance = previousAppearance
            panel.orderOut(nil)
        }
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        Self.tileScrollViews(in: content)
        panel.display()
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))

        var productTable: NSTableView?
        func find(_ view: NSView) {
            if productTable == nil, let table = view as? NSTableView, table.dataSource is QuickPickController {
                productTable = table
            }
            view.subviews.forEach(find)
        }
        find(content)
        guard let table = productTable else {
            return XCTFail("找不到那张产品表格 ⇒ 这条判据没有对象（数据源已经不是控制器，或行根本没建出来）")
        }
        let rowCount = table.numberOfRows
        XCTAssertGreaterThan(rowCount, 1, "少于两行 ⇒ 「所有行共享一条左轴」这句话没有对象")
        // 正对照：夹具里必须真的有几种不同的类型符号，否则"左轴一致"是平凡真。
        XCTAssertGreaterThanOrEqual(kinds.count, 2,
                                    "夹具里所有条目都是同一类型（\(kinds)）⇒ 这一格今天抓不到"
                                    + "「只有部分行有图标」那种缺陷，判据空转")

        var labelMinX: [CGFloat] = []
        var symbolMinX: [CGFloat] = []
        var symbolRightEdge: [CGFloat] = []
        var rowsWithoutImage = 0
        for row in 0..<rowCount {
            guard let cell = table.view(atColumn: 0, row: row, makeIfNecessary: false) as? NSTableCellView else {
                return XCTFail("第 \(row) 行拿不到 cell ⇒ 行不是产品那条 `viewFor` 画的，这条判据没在判产品")
            }
            if cell.imageView?.image == nil { rowsWithoutImage += 1 }
            if let label = cell.textField, let frame = Self.frame(label, in: table) {
                labelMinX.append(frame.minX)
            }
            if let symbol = cell.imageView, let frame = Self.frame(symbol, in: table) {
                symbolMinX.append(frame.minX)
                symbolRightEdge.append(frame.maxX)
            }
        }
        let labelSpread = (labelMinX.max() ?? 0) - (labelMinX.min() ?? 0)
        let symbolSpread = (symbolMinX.max() ?? 0) - (symbolMinX.min() ?? 0)
        emit("QUICKPICK_ROW_AXIS rows=\(rowCount) 取到标签=\(labelMinX.count) 取到图标=\(symbolMinX.count) "
              + "无图行=\(rowsWithoutImage) 标签左轴散布=\(String(format: "%.2f", labelSpread))pt "
              + "图标列散布=\(String(format: "%.2f", symbolSpread))pt "
              + "标签 minX=\(labelMinX.map { String(format: "%.1f", $0) }.joined(separator: ",")) "
              + "类型符号=\(kinds.sorted().joined(separator: ","))")
        XCTAssertEqual(rowsWithoutImage, 0,
                       "\(rowsWithoutImage) 行的行首没有图 ⇒ 符号名在这台机器上画不出东西"
                       + "（`NSImage(systemSymbolName:)` 对不存在的名字返回 nil，而 NSImageView 静默）")
        XCTAssertEqual(labelMinX.count, rowCount, "有行拿不到 textField ⇒ 左轴这件事没被量全")
        XCTAssertEqual(symbolMinX.count, rowCount, "有行拿不到 imageView ⇒ 那一列不是每行都有（BACKLOG 97 的形状）")
        XCTAssertLessThan(labelSpread, 0.5,
                          "标签左轴散布 \(String(format: "%.2f", labelSpread))pt ⇒ 又变成两套左轴了。"
                          + "改前实测是 22pt（纯文本行 34.5pt、文件行 56.5pt），因为图标是塞在文案里的 emoji")
        XCTAssertLessThan(symbolSpread, 0.5, "行首那一列自己都没对齐（散布 \(symbolSpread)pt）")
        XCTAssertLessThan((symbolRightEdge.max() ?? 0) + 1, (labelMinX.min() ?? 0),
                          "标签没有排在图标**右边**（图标最右 \((symbolRightEdge.max() ?? 0).description)"
                          + " vs 标签最左 \((labelMinX.min() ?? 0).description)）⇒ 那一列不占位，会压住文字")
    }

    /// R67 · 浮层那一行的悬停档：**画了、画在该在的那一行、两档外观同一条通道**。
    ///
    /// 判的是 alpha，不是"合成后的亮度"。理由是被两次读数逼出来的，不是偏好：
    /// 这条通道拍的是 `contentView`，而浮层的表格与滚动视图刻意不画底色
    /// （`table.backgroundColor = .clear`、`scroll.drawsBackground = false`）⇒ 行底在帧里是**透明**的。
    /// 于是同一层 6% 的墨，两档外观合成到中灰之后读出来是
    /// **亮 −2.28/255、暗 +6.73/255**（本机实测），而 alpha 那一列读出来是
    /// **亮 15.80→29.42（+13.62）、暗 17.84→31.34（+13.50）** ——
    /// 差 0.12 个 alpha。也就是说"亮度"这把尺量的其实是**这一行原来有什么字**，
    /// 而"alpha 抬了多少"量的才是产品写进去的那一层。
    ///
    /// 三条断言各自拦一种错：
    ///   ① 抬升 ≥ 令牌推导线的一半 ⇒ 拦"没画 / 画得太轻"（改颜色成 `.clear`、把 alpha 调小都会红）；
    ///   ② 只有被点亮那一行的 alpha 抬升 ⇒ 拦"画到别的行上"，同时它也是 BACKLOG 80
    ///      那族 y 轴翻转的探测器（点亮第 3 行，翻错就落在第 4 行，两行相隔 34pt）；
    ///   ③ 合成后的亮度**符号**：亮档必须变暗、暗档必须变亮 ⇒ 拦"用错极性的墨"
    ///      （比如在亮色里画 6% 的白）。只判符号不判大小 —— 大小被上面那条通道限制污染了。
    ///
    /// **这一档"够不够响"不在这里判**：屏幕上那一层是画在实心窗口上的，
    /// 而这条通道里没有那个底。0.06 这一档的"看得出来"是 R15 在侧栏同一条令牌上量过的
    /// （`idle→hover 15.9 / 14.0`），浮层继承它；真屏幕上顺不顺眼记进人工批次 67。
    /// 把"拍不到实底"这件事修掉（改拍 frame view，让窗口底真的进来）记 BACKLOG 103。
    func testOverlayHoverTintIsPaintedAndConfinedToItsRow() throws {
        let store = makePopulatedStore()
        let hoveredRow = 3
        // 期望抬升从令牌推：`VisualFill.hover` × 255 = 15.3 个 alpha。
        // 线取它的一半（7.65）而不是它本身：带里本来就有字与图标是实心的（静置 alpha 实测 15.8–17.8），
        // 那些像素的 alpha 不会再涨，所以"整带平均抬升"必然低于满值 —— 但绝不该低到一半以下。
        let expectedRise = Double(VisualFill.hover) * 255.0
        let floor = expectedRise / 2.0
        for (label, appearance, expectedSign) in [("亮", NSAppearance.Name.aqua, -1.0),
                                                  ("暗", NSAppearance.Name.darkAqua, 1.0)] {
            let shot = try overlayPair(store: store, hoveredRow: hoveredRow, appearance: appearance)
            let plain = shot.plain, hovered = shot.hovered
            guard let band = shot.bands[hoveredRow] else {
                return XCTFail("量不到第 \(hoveredRow) 行的矩形 ⇒ 「悬停画没画出来」这一条没有对象"
                    + "（可读到的行矩形只有 \(shot.bands.keys.sorted().map(String.init).joined(separator: ","))）")
            }
            let expectedWord = expectedSign > 0 ? "变亮" : "变暗"
            let rise = Self.meanAlpha(hovered, rect: band) - Self.meanAlpha(plain, rect: band)
            let luminanceDelta = Self.meanLuminance(hovered, rect: band)
                - Self.meanLuminance(plain, rect: band)
            var others: [(Int, Double)] = []
            for (row, rect) in shot.bands.sorted(by: { $0.key < $1.key }) where row != hoveredRow {
                others.append((row, Self.meanAlpha(hovered, rect: rect) - Self.meanAlpha(plain, rect: rect)))
            }
            let loudestOther = others.max(by: { $0.1 < $1.1 }) ?? (-1, 0)
            let neighborLift = others.first(where: { $0.0 == hoveredRow + 1 })?.1 ?? -999
            emit("OVERLAY_HOVER \(label) 点亮行=\(hoveredRow) alpha 抬升=\(String(format: "%.2f", rise))/255 "
                  + "线=\(String(format: "%.2f", floor))（令牌推 \(String(format: "%.2f", expectedRise)) 的一半） "
                  + "亮度差=\(String(format: "%.2f", luminanceDelta))/255 期望符号=\(expectedWord) "
                  + "邻行最大抬升=\(loudestOther.0):\(String(format: "%.2f", loudestOther.1)) "
                  + "第4行抬升=\(String(format: "%.2f", neighborLift)) 带=\(NSStringFromRect(band)) "
                  + "行数=\(shot.bands.count) alpha 静置=\(String(format: "%.2f", Self.meanAlpha(plain, rect: band)))")
            XCTAssertGreaterThanOrEqual(rise, floor,
                "\(label)档：点亮那一行的 alpha 只抬了 \(String(format: "%.2f", rise))/255，"
                    + "而这一层墨自己写进去的是 \(String(format: "%.2f", expectedRise))（`VisualFill.hover` × 255）"
                    + "的一半都不到 ⇒ 这一档要么没画，要么被谁调轻了")
            XCTAssertLessThan(loudestOther.1, floor,
                "\(label)档：第 \(loudestOther.0) 行（没被点亮）也抬了 \(String(format: "%.2f", loudestOther.1))/255 ⇒ "
                    + "这层灰没有钉在它该在的那一格。两种成因都值得查：它画多了行，"
                    + "或者行矩形的 y 朝向与缓冲区不一致（BACKLOG 80 那一族 —— 点亮第 3 行，翻错就落在第 4 行）")
            // 宽度：这层灰必须与**选中药丸同宽**。
            // 为什么线不能取自 `QuickPickController.hoverFillInset`（我第一版就是这么写的，
            // 于是 M367 那一刀逃掉了）：拿被约束的那个常量去推期望值，改常量就等于同时改了判据 ——
            // 尺子读的是被测物体自己的刻度。改成在同一张帧上量药丸：
            // 选中那一行与一条静置行的 **alpha 差**就是药丸的横向范围（药丸是实的、行底是透的）。
            func rows(_ rect: CGRect) -> Range<Int> {
                Int(rect.minY.rounded())..<Int(rect.maxY.rounded())
            }
            // 药丸在第 0 行（`windowForCapture` 里 `model.index = 0`），静置的参照行取第 1 行。
            guard let selectedBand = shot.bands[0], let idleBand = shot.bands[1] else {
                return XCTFail("\(label)档：量不到选中行或静置行 ⇒ 宽度的参照物不存在")
            }
            let bandRows = rows(band)
            let pillRows = rows(selectedBand)
            let idleRows = rows(idleBand)
            let pill = Self.alphaBandDelta(plain, pillRows, plain, idleRows,
                                         x0: 0, x1: plain.pixelsWide, floor: 4)
            let painted = Self.alphaBandDelta(plain, bandRows, hovered, bandRows,
                                              x0: 0, x1: plain.pixelsWide, floor: 4)
            emit("  药丸 x=\(pill.min)…\(pill.max) 灰带 x=\(painted.min)…\(painted.max) "
                  + "左差=\(painted.min - pill.min)px 右差=\(painted.max - pill.max)px 帧宽=\(plain.pixelsWide)px")
            XCTAssertGreaterThan(pill.max, pill.min,
                "\(label)档：在同一张静置帧上量不到选中药丸的横向范围 ⇒ 这条宽度判据没有对象，"
                    + "先查捕获通道（选中那一档在离屏窗口里是材质，R18 那一族）")
            XCTAssertGreaterThan(painted.max, painted.min, "\(label)档：量不到灰带的横向范围")
            XCTAssertLessThanOrEqual(abs(painted.min - pill.min), 4,
                "\(label)档：灰带左沿 \(painted.min) 与药丸左沿 \(pill.min) 差 \(abs(painted.min - pill.min))px ⇒ "
                    + "同一格里两种宽度，看着像两个东西在抢这一行")
            XCTAssertLessThanOrEqual(abs(painted.max - pill.max), 4,
                "\(label)档：灰带右沿 \(painted.max) 与药丸右沿 \(pill.max) 差 \(abs(painted.max - pill.max))px（同上）")

            XCTAssertGreaterThan(luminanceDelta * expectedSign, 0,
                "\(label)档：合成到中灰底上读到的亮度变化是 \(String(format: "%.2f", luminanceDelta))/255，"
                    + "方向错了（这一档期望\(expectedWord) ⇒ 用的墨极性不对："
                    + "`labelColor` 会跟着外观翻面，写死成白或黑就会在其中一档里看不见")
        }
    }

    /// R67 · 那一层灰的**轮廓**必须与选中药丸逐行一致（不是"总宽度一致"）。
    ///
    /// 这一条是看了画面才有的，读数给不出来：上一判据量到"左差 0px / 右差 0px"就绿了，
    /// 而 `quickpick-hover-*-light.png` 上那层灰是**直角、满高**的一块（逐行 x 范围恒为 42…797），
    /// 同一张帧上的药丸是圆的（首行 55…784 → 中行 44…795，左沿内缩跨度 11px）。
    /// 两档说的是同一件事（"鼠标 / 键盘在这一行"），形状不一致就等于两个人说话。
    ///
    /// 三条断言各自拦一种错：
    ///   ① 参照物自己是圆的（药丸左沿内缩跨度 ≥ 4px）⇒ 拦"空判据"：
    ///      如果哪天量到的药丸是方的，那"逐行一致"就自动成立，这条判据什么都不钉。
    ///      与 `bottomEdgeInkCanary` 同一条理由 —— 正对照读的必须就是判据读的那个量。
    ///   ② 逐行左沿 / 右沿之差 ≤ 2px ⇒ 拦"方角"（顶行差 11px）、拦"上下内缩不同"、拦"宽度又跑掉"。
    ///   ③ 两条轮廓的行数差 ≤ 2 ⇒ 拦"灰带比行高"（画到邻行去）与"灰带被压扁"。
    ///
    /// 容差为什么是 2px 而不是 0：这条通道在两台机器上有 ±1pt 的系统性抖动（R38 那一课），
    /// 而它要拦的是 11px 的方角。1pt 的差别（`hoverFillInset` 9 vs 10）不在这里判 ——
    /// 那 1pt 由**帧基线**逐字节钉住（`quickpick-hover-*` 两张在 `docs/frame_baseline.json` 里），
    /// 改回去会红的是那一条，不是这一条。
    func testOverlayHoverFillSharesTheSelectionPillsOutline() throws {
        let store = makePopulatedStore()
        let hoveredRow = 3
        for (label, appearance) in [("亮", NSAppearance.Name.aqua), ("暗", NSAppearance.Name.darkAqua)] {
            let shot = try overlayPair(store: store, hoveredRow: hoveredRow, appearance: appearance)
            let plain = shot.plain, hovered = shot.hovered
            guard let band = shot.bands[hoveredRow],
                  let selectedBand = shot.bands[0], let idleBand = shot.bands[1] else {
                return XCTFail("\(label)档：量不到第 \(hoveredRow)/0/1 行的矩形 ⇒ 轮廓判据没有对象")
            }
            func rows(_ rect: CGRect) -> Range<Int> {
                Int(rect.minY.rounded())..<Int(rect.maxY.rounded())
            }
            // 药丸 = 同一张静置帧上"选中行 vs 静置行"的逐行 alpha 差；
            // 灰带 = 同一行上"点亮帧 vs 静置帧"的逐行 alpha 差。两把尺同一套语义，只是参照不同。
            let pill = Self.alphaLiftProfile(plain, rows(selectedBand), plain, rows(idleBand),
                                             x0: 0, x1: plain.pixelsWide, floor: 4)
            let fill = Self.alphaLiftProfile(hovered, rows(band), plain, rows(band),
                                             x0: 0, x1: plain.pixelsWide, floor: 4)
            let pillInset = Self.profileLeftInsetSpread(pill)
            let fillInset = Self.profileLeftInsetSpread(fill)
            // 这条通道在 **1× 上量不出参照物的圆角**（R69 发现；R73 读 R70 的 CI 时把机制查清了，
            // 而查清的结果是：**我 R69 写的那个假设是错的**）。两台机器的读数（换算成 pt）：
            //   本机 2×：药丸内缩 11px = 5.5pt、灰带 11px = 5.5pt、逐行差 0px；
            //   runner 1×：药丸内缩 **2px = 2pt**、灰带 5px = 5pt、逐行差 3px ⇒ 判红。
            // R70 那次"把门本身变成被量的对象"给出的答案：
            //   `OVERLAY_HOVER_DOOR 缩放=1× 药丸内缩@门1/2/4 = 2/2/2px，灰带@门1/4 = 4/5px`
            //   ⇒ **不是门**：把 `≥4/255` 降到 `≥1/255`，药丸读数一动没动。R69 那句
            //     "材质角过不了门"（U-118 里写的机制假设）作废 —— 一条假设被自己的读数杀掉，
            //     这正是 R70 那一轮存在的理由（否则这句话会一直留在注释里当解释用）。
            // 反过来看灰带：1× 实测 4–5px，而 R=8px 的圆角在这把尺上的理论值是
            //   `R − √(R² − (R−0.5)²) = 8 − √15.75 ≈ 5.2px`；2× 理论 12.0 / 实测 11
            //   ⇒ **灰带在两档缩放下都量得对**。同一个对象不可能随缩放改圆角 ⇒
            //     1× 上坏掉的是**参照物那一侧的读数**（AppKit 那颗材质药丸的角在 1× 离屏合成里被吃掉），
            //     不是产品，也不是我的尺。
            // ⇒ 处置不变（这一轴按机器分开），但理由从"假设"换成"量过的结论"：
            //   1× 上不许判红、也不许装作判过 ⇒ 发 `FRAME_CORNER_AXIS_NOT_RUN=1` 点名
            //   （名字必须**以 `_NOT_RUN` 结尾**：`ci_capture_gate.py` 要的是
            //    `\b[A-Z][A-Z0-9_]*_NOT_RUN\b`，自造 `_BLIND` 后缀它就整条看不见 —— R36/U-59）；
            //   2× 上照旧红。要在 1× 上赎回这条轴，现在只剩 BACKLOG **103** 那一条路
            //   （换捕获对象，让窗口底真的进来）—— 105 的那两条候选里，降门这一条已被证伪。
            // 而**方角在两台机器上都还会红**，靠的是下面那条不依赖参照物的 `fillInset ≥ 1`：
            // 直角块的首行与中行同宽 ⇒ 内缩跨度恒为 0，1× 也量得出"没有内缩"。
            let cornerAxisResolvable = pillInset >= 4
            // **把"门"本身变成被量的对象**（R70 / BACKLOG 105 ①）：
            // "1× 量不出药丸圆角"的机制假设是"材质角上的 alpha 不是覆盖率的线性函数 ⇒ 过不了 `≥4/255`"。
            // 假设没证实过，而它决定这条轴能不能在 runner 上赎回来 ⇒ 同一次捕获里对参照物
            // 用三道门各量一遍。**线一个数没动**（下面仍按 `pillInset ≥ 4` 决定判不判），
            // 多出来的只是读数：如果 1× 上"门=1"把内缩拉回 ≈5px，那是门的问题；
            // 三道门都给 2px，那是通道的性质，只能走 BACKLOG 103（换捕获对象）。
            let pillInsetAtDoor1 = Self.profileLeftInsetSpread(
                Self.alphaLiftProfile(plain, rows(selectedBand), plain, rows(idleBand),
                                      x0: 0, x1: plain.pixelsWide, floor: 1))
            let pillInsetAtDoor2 = Self.profileLeftInsetSpread(
                Self.alphaLiftProfile(plain, rows(selectedBand), plain, rows(idleBand),
                                      x0: 0, x1: plain.pixelsWide, floor: 2))
            let fillInsetAtDoor1 = Self.profileLeftInsetSpread(
                Self.alphaLiftProfile(hovered, rows(band), plain, rows(band),
                                      x0: 0, x1: plain.pixelsWide, floor: 1))
            emit("OVERLAY_HOVER_DOOR \(label) 缩放=\(shot.scale)× 药丸内缩@门1/2/4="
                  + "\(pillInsetAtDoor1)/\(pillInsetAtDoor2)/\(pillInset)px "
                  + "灰带内缩@门1/4=\(fillInsetAtDoor1)/\(fillInset)px "
                  + "⇒ 假设『材质角过不了门』在两族读数上必须一起回升，只有一族回升就是别的原因")
            emit("OVERLAY_HOVER_OUTLINE \(label) 药丸行数=\(pill.count) 灰带行数=\(fill.count) "
                  + "药丸左沿内缩=\(pillInset)px 灰带左沿内缩=\(fillInset)px "
                  + "缩放=\(shot.scale)× 圆角这一轴=\(cornerAxisResolvable ? "可判" : "无分辨率") "
                  + "药丸首行=\(pill.first.map { "\($0.left)…\($0.right)" } ?? "-") "
                  + "药丸中行=\(pill.count > 2 ? "\(pill[pill.count / 2].left)…\(pill[pill.count / 2].right)" : "-") "
                  + "灰带首行=\(fill.first.map { "\($0.left)…\($0.right)" } ?? "-") "
                  + "灰带中行=\(fill.count > 2 ? "\(fill[fill.count / 2].left)…\(fill[fill.count / 2].right)" : "-")")
            XCTAssertGreaterThanOrEqual(pill.count, 8,
                "\(label)档：只量到 \(pill.count) 行药丸轮廓 ⇒ 参照物不存在（材质在离屏窗口里没合成，R18 那一族），"
                    + "这条判据不许在'量不到'的情况下当作通过")
            XCTAssertGreaterThanOrEqual(fill.count, 8,
                "\(label)档：只量到 \(fill.count) 行灰带轮廓 ⇒ 那一层灰没画出来，判不了形状")
            XCTAssertLessThanOrEqual(abs(fill.count - pill.count), 2,
                "\(label)档：灰带 \(fill.count) 行而药丸 \(pill.count) 行 ⇒ 两块东西高度不同："
                    + "灰要么比行高（画到邻行去了），要么被压扁了")
            // —— 两台机器都有牙的那一条：灰带自己必须是圆的（直角 ⇒ 内缩跨度恒 0）。
            XCTAssertGreaterThanOrEqual(fillInset, 1,
                "\(label)档：灰带自己的左沿内缩跨度是 \(fillInset)px ⇒ 它是**直角**的。"
                    + "这一条不依赖参照物，所以 1× 上也照样红（R67 第一版就是这一形状）")
            if cornerAxisResolvable {
                XCTAssertGreaterThanOrEqual(pillInset, 4,
                    "\(label)档：走到这里说明线判为可判，而药丸内缩只有 \(pillInset)px —— 自相矛盾，查尺")
                XCTAssertLessThanOrEqual(abs(fillInset - pillInset), 2,
                    "\(label)档：灰带内缩 \(fillInset)px 与药丸 \(pillInset)px 差 \(abs(fillInset - pillInset))px ⇒ "
                        + "两档曲率不是一套话（6pt 那一版差 3px，就是这一格抓的）")
            } else {
                emit("FRAME_CORNER_AXIS_NOT_RUN=1 \(label) 缩放=\(shot.scale)× "
                      + "药丸内缩=\(pillInset)px（< 4px）⇒ 这台机器的通道量不出参照物的圆角，"
                      + "'与药丸同曲率'这一轴今天**没判**（不是判过且通过）。"
                      + "仍判的是：灰带自己是圆的、中行宽度一致、高度一致（见上一条断言）")
            }
            let common = min(pill.count, fill.count)
            // 首末各去掉 `scale` 行：1× 上那一行就是一个 pt 的量化误差（runner 的 3px 差就在这里），
            // 2× 上只去掉最外面两行 —— 方角会一路吃进带内 6pt（本机 12px），中间行照样红。
            let margin = max(1, shot.scale)
            var worstLeft = 0, worstRight = 0, worstAt = -1
            for t in margin..<max(margin, common - margin) {
                let dl = abs(fill[t].left - pill[t].left), dr = abs(fill[t].right - pill[t].right)
                if max(dl, dr) > max(worstLeft, worstRight) { worstLeft = dl; worstRight = dr; worstAt = t }
            }
            emit("  逐行最大偏差（去掉首末各 \(margin) 行）第\(worstAt)行 左=\(worstLeft)px 右=\(worstRight)px（线 2px）")
            XCTAssertLessThanOrEqual(worstLeft, 2,
                "\(label)档：灰带与药丸逐行左沿最大差 \(worstLeft)px（第 \(worstAt) 行）⇒ 形状不是一套话。"
                    + "方角会在这里红：直角块从顶行起就与圆角药丸一行差一个半径（本机实测 11px）")
            XCTAssertLessThanOrEqual(worstRight, 2,
                "\(label)档：灰带与药丸逐行右沿最大差 \(worstRight)px（第 \(worstAt) 行）（同上）")
        }
    }

    /// R67 · 悬停的语义（真值表）+ 令牌同一性 + 与侧栏同一枚令牌（跨文件守卫）。
    func testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar() throws {
        // 真值表：只有"悬停且未选中"才画灰。四格全钉，因为少一格就会有一种静默的错：
        // 只测"该画的画了"，那么"选中时也画"（把蓝药丸压成灰蓝）不会红；
        // 只测"不该画的不画"，那么"永远不画"也不会红 —— 后者正是改之前产品的样子。
        XCTAssertTrue(QuickPickController.showsHoverTint(isSelected: false, isHovered: true),
                      "悬停且未选中却不画灰 ⇒ 这个面板仍然没有指针反馈（R67 要修的就是这一格）")
        XCTAssertFalse(QuickPickController.showsHoverTint(isSelected: true, isHovered: true),
                       "选中时还叠一层灰 ⇒ hover(0.06) 会把 selected(0.16 的强调色) 压成灰蓝，"
                           + "「哪一条是我选中的」要读第二眼")
        XCTAssertFalse(QuickPickController.showsHoverTint(isSelected: true, isHovered: false),
                       "没悬停却画灰 ⇒ 每一行都灰，等于没有这一档")
        XCTAssertFalse(QuickPickController.showsHoverTint(isSelected: false, isHovered: false),
                       "静置行不许有任何底色（否则整列都是灰底，选中反而不显眼）")

        // 令牌同一性：浮层不许自己再定一个数。
        XCTAssertEqual(QuickPickController.hoverFillAlpha, CGFloat(VisualFill.hover),
                       "浮层那一档不再是 `VisualFill.hover` ⇒ 同一件「鼠标在这里」又要开始说两种音量")
        XCTAssertLessThan(CGFloat(VisualFill.hover), CGFloat(VisualFill.selected),
                          "hover ≥ selected ⇒ 次序反了：瞬时的悬停比会留下来的选中更响")
        XCTAssertLessThan(CGFloat(VisualFill.selected), CGFloat(VisualFill.pressed) + 1,
                          "`VisualFill` 自己的三档次序被改了（hover < pressed < selected 是语义）")

        // 重排必须清掉旧的那一层（守卫的是**调用点**，不是函数存在）：
        // `NSTableView` 会把 row view 挪去配另一行，而指针没动 ⇒ `mouseExited` 不会来 ⇒
        // 那层灰会留在错误的一行上。删掉这一行调用不会让任何像素判据变红
        // （判据里没有真鼠标），所以它必须由一条源码守卫钉住 —— 与 `NoticeBanner`
        // 那一族"守卫读调用点"同一条理由。
        //
        // R74：截取换成 `Self.functionBody` 而不是这一格自己 `components(separatedBy:)`。
        // 理由是**漂移**：淡入那条判据（`testOverlayHoverHasNoFade…`）守的是同一个机制，
        // 两处各写一份截取规则，就会有一处先瞎（M386 实测过：这一刀同时红在两条守卫上，
        // 说明它们判的确实是同一件事 —— 那它们就必须共用同一把尺，只剩一个地方会坏）。
        let controllerSource = Self.codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        XCTAssertTrue(Self.functionBody(named: "private func rebuildRows()", in: controllerSource)
                        .contains("clearHover()"),
                      "`rebuildRows` 不再清悬停了 ⇒ 打字时候选增减，那层灰会留在错误的一行上")

        // 跨文件守卫：SwiftUI 侧那一族行悬停确实读的是同一枚令牌
        // （`DetailView` 的两处 `.fill(.primary.opacity(isHovered ? VisualFill.hover : 0))`）。
        // 这条守卫只读**产品**文件，不读测试自己 —— 否则它会因为本文件里也出现
        // `VisualFill.hover` 而永远通过（R53 那一课：扫源码的守卫会命中守卫自己）。
        let sidebar = Self.codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(sidebar.contains("VisualFill.hover"),
                      "SwiftUI 侧的行悬停不再引用 `VisualFill.hover` ⇒ 浮层这条守卫就成了空守卫："
                          + "两边可以各挑一个数而仍然全绿")
    }

    /// 诊断用：这条通道给的位图到底是**预乘**还是非预乘、opaque 与否。
    /// 合成式选哪一条要看它（见 `meanLuminance` 的注释），所以它必须被读出来，不能被假设。
    static func overlayAlphaInfo(plain: NSBitmapImageRep, hovered: NSBitmapImageRep) -> String {
        "hasAlpha 静置=\(plain.hasAlpha) 点亮=\(hovered.hasAlpha) opaque 静置=\(plain.isOpaque) "
            + "点亮=\(hovered.isOpaque) 每像素字节 静置=\(plain.samplesPerPixel)"
    }

    /// 把浮层拍成两张位图（静置 / 点亮第 `hoveredRow` 行），并给出**每一行在像素空间里的矩形**。
    ///
    /// 两张来自**同一个面板、同一个控制器**，中间只改 `rowHoveredForCapture` 一次：
    /// 这样"除了悬停什么都没变"是构造出来的，而不是"两个面板碰巧画得一样"。
    /// （R67 第一版是各建一个面板，结果亮色那一遍两帧逐像素相同、暗色那一遍正常 ——
    /// 差异来自面板之间的建板/上屏时机，而不是产品。判据当时的红是对的，原因是我搭错了。）
    ///
    /// 行矩形从产品自己的 `table.rowHeight` 与表格在 contentView 里的位置推，
    /// 判据里不写 34 / 420 这类字面量（数字只能从读数来）。
    /// y 轴：这条通道的缓冲区第 0 行是**画面顶边**（R57 实测，BACKLOG 80 的原始证据），
    /// 而 AppKit 视图坐标是左下角原点 ⇒ 这里显式翻转；翻错了会被"变化全在带内"那格抓住
    /// （点亮第 3 行，翻错就落在第 4 行，两行相隔 34pt，判据会指名道姓）。
    private func overlayPair(store: HistoryStore, hoveredRow: Int,
                             appearance: NSAppearance.Name) throws
            -> (plain: NSBitmapImageRep, hovered: NSBitmapImageRep, bands: [Int: CGRect], scale: Int) {
        let build = QuickPickCapturePanel.builder(store: store, query: "")
        guard let panel = build(), let content = panel.contentView else {
            throw XCTSkip("捕获入口建不出浮层窗口 ⇒ 这一档今天无从判定（不是产品没画）")
        }
        _ = NSApplication.shared
        let previousAppearance = NSApplication.shared.appearance
        NSApplication.shared.appearance = NSAppearance(named: appearance)
        defer {
            NSApplication.shared.appearance = previousAppearance
            panel.orderOut(nil)
        }
        content.appearance = NSAppearance(named: appearance)
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        Self.tileScrollViews(in: content)
        func shoot() -> NSBitmapImageRep {
            panel.display()
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            guard let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds) else {
                return NSBitmapImageRep()
            }
            content.cacheDisplay(in: content.bounds, to: rep)
            return rep
        }
        let plain = shoot()
        // 点亮：走的是产品那个属性，绘制分支与鼠标进来的完全同一条。
        if let table = Self.productTable(in: content) {
            (table.delegate as? QuickPickController)?.rowHoveredForCapture = hoveredRow
        }
        let hovered = shoot()

        guard let table = Self.productTable(in: content) else { return (plain, hovered, [:], 1) }
        let scale = max(1, plain.pixelsWide / max(Int(content.bounds.width), 1))
        let contentHeight = content.bounds.height
        var bands: [Int: CGRect] = [:]
        for row in 0..<table.numberOfRows {
            let rectInTable = table.rect(ofRow: row)
            guard rectInTable.height > 0 else { continue }
            let rectInContent = table.convert(rectInTable, to: nil)
            let top = contentHeight - rectInContent.maxY
            bands[row] = CGRect(x: rectInContent.minX * CGFloat(scale),
                                y: top * CGFloat(scale),
                                width: rectInContent.width * CGFloat(scale),
                                height: rectInContent.height * CGFloat(scale))
        }
        return (plain, hovered, bands, scale)
    }

    /// 按**身份**认那张表：数据源是产品控制器的那一张（R65 那一课 —— 面板整棵树里不止一个表）。
    private static func productTable(in root: NSView) -> NSTableView? {
        var found: NSTableView?
        func walk(_ view: NSView) {
            if found != nil { return }
            if let table = view as? NSTableView, table.dataSource is QuickPickController {
                found = table
            }
            view.subviews.forEach(walk)
        }
        walk(root)
        return found
    }

    /// 一块矩形里的平均 alpha（0–255）。**这条通道拍不到半透明层画在实底上的效果**
    /// （浮层的表格刻意 `backgroundColor = .clear`，所以行底在帧里是透明的），
    /// 但 alpha 是产品自己写进去的那个数 —— 它量的是"这一层画没画、画了多少"。
    static func meanAlpha(_ rep: NSBitmapImageRep, rect: CGRect) -> Double {
        guard let base = rep.bitmapData, rep.samplesPerPixel >= 4, rep.hasAlpha else { return -1 }
        let spp = rep.samplesPerPixel, bytesPerRow = rep.bytesPerRow
        let x0 = max(0, Int(rect.minX.rounded())), x1 = min(rep.pixelsWide, Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded())), y1 = min(rep.pixelsHigh, Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0 else { return -1 }
        var sum = 0.0, count = 0
        var y = y0
        while y < y1 {
            var x = x0
            while x < x1 {
                sum += Double(base[y * bytesPerRow + x * spp + 3])
                count += 1
                x += 1
            }
            y += 1
        }
        return count == 0 ? -1 : sum / Double(count)
    }

    /// 一块矩形里的平均亮度（0–255，三通道均值，**先按 alpha 合成到一块中灰底上**）。
    ///
    /// 为什么要合成：这条通道拍的是 `contentView`，而浮层的表格与滚动视图都刻意不画底色
    /// （`table.backgroundColor = .clear`、`scroll.drawsBackground = false`）⇒
    /// 亮色那一遍行底是**透明**的，6% 的黑画在透明黑上，RGB 一个数都不动（实测 0.00/255），
    /// 而暗色那一遍行底是实的，6% 的白画上去动 13.50/255。
    /// 两遍读的不是同一件事，除非先把两边都按**用户真正看到的方式**合成到一个不透明底上 ——
    /// 屏幕上那个面板背后永远是实心的窗口，不是透明像素。
    /// 拿不到 alpha 时（`hasAlpha == false`）合成就是原值，不影响暗色那一遍的读数。
    static func meanLuminance(_ rep: NSBitmapImageRep, rect: CGRect, background: Double = 128) -> Double {
        guard let base = rep.bitmapData else { return -1 }
        let spp = rep.samplesPerPixel
        let bytesPerRow = rep.bytesPerRow
        let x0 = max(0, Int(rect.minX.rounded())), x1 = min(rep.pixelsWide, Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded())), y1 = min(rep.pixelsHigh, Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0, spp >= 4 else { return -1 }
        var sum = 0.0, count = 0
        var y = y0
        while y < y1 {
            var x = x0
            while x < x1 {
                let p = y * bytesPerRow + x * spp
                sum += compositedChannel(base, p, background)
                    + compositedChannel(base, p + 1, background)
                    + compositedChannel(base, p + 2, background)
                count += 3
                x += 1
            }
            y += 1
        }
        return count == 0 ? -1 : sum / Double(count)
    }

    /// 一个通道值按它自己的 alpha 合成到实底上（`premultipliedLast`：字节已经是预乘的，
    /// 所以合成式是 `值 + 底 × (1 − α)`，不是 `值 × α + 底 × (1 − α)`）。
    private static func compositedChannel(_ base: UnsafeMutablePointer<UInt8>, _ p: Int,
                                          _ background: Double) -> Double {
        let alpha = Double(base[p + 3]) / 255.0
        return Double(base[p]) + background * (1.0 - alpha)
    }

    /// 变化像素的 x 范围（像素空间）。用来判"这层灰有多宽"——
    /// 它必须与选中那颗药丸同宽，而不是铺满整格（`hoverFillInset` 的注释里是量出来的出处）。
    static func changedXRange(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                              clipping: CGRect, threshold: Int = 8,
                              background: Double = 128) -> (min: Int, max: Int) {
        guard let pa = a.bitmapData, let pb = b.bitmapData,
              a.samplesPerPixel >= 4, b.samplesPerPixel >= 4 else { return (-1, -1) }
        var lo = Int.max, hi = -1
        let x0 = max(0, Int(clipping.minX.rounded())), x1 = min(a.pixelsWide, Int(clipping.maxX.rounded()))
        let y0 = max(0, Int(clipping.minY.rounded())), y1 = min(a.pixelsHigh, Int(clipping.maxY.rounded()))
        var y = y0
        while y < y1 {
            var x = x0
            while x < x1 {
                let p = y * a.bytesPerRow + x * a.samplesPerPixel
                let q = y * b.bytesPerRow + x * b.samplesPerPixel
                let d = max(abs(Int(Self.compositedChannel(pa, p, background).rounded())
                                - Int(Self.compositedChannel(pb, q, background).rounded())),
                            max(abs(Int(Self.compositedChannel(pa, p + 1, background).rounded())
                                    - Int(Self.compositedChannel(pb, q + 1, background).rounded())),
                                abs(Int(Self.compositedChannel(pa, p + 2, background).rounded())
                                    - Int(Self.compositedChannel(pb, q + 2, background).rounded()))))
                if d > threshold { if x < lo { lo = x }; if x > hi { hi = x } }
                x += 1
            }
            y += 1
        }
        return (lo == Int.max ? -1 : lo, hi)
    }

    // R78 删掉了这里原本的 `paintedXRange`：它零调用点（全仓只有它自己的声明），
    // 而 R77 的双向名册把它收了进去、理由里还替它写了调用者 —— 一条死尺占着一个豁免位，
    // 比没登记更坏：它让"名册已经数过全部盲区"这句话变成假的（U-137）。
    // 需要"被点亮像素的 x 范围"时用的是下面那把 `alphaBandDelta`（R67 起就在判据里）。

    /// 一块矩形里有多少像素的 **alpha 过地板**（R78）。
    ///
    /// 这条尺子的用途只有一个：**问"这一格里到底画没画东西"**，不问"两态差没差"。
    /// R76 那条焦点判据在 runner 上红了（run 38743276799：框内变化像素 0、alpha 差 0.05），
    /// 而它在本机是 1797 / 3.93 —— 两句"焦点有视觉后果"与"这条通道今天没画那串字"
    /// 在只读差值的尺子长得**一模一样**。要分开它们，就必须有一个不依赖两态相减的存在性量。
    /// 地板取 8/255 与全仓那几把差值尺同一条；调用方给的判据是"计数 ≥ 一道很低的地板"，
    /// 因为画出来的占位字是几千个像素、没画是 0 个，中间没有可争的地带。
    static func alphaInkPixels(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 8) -> Int {
        guard let base = rep.bitmapData, rep.samplesPerPixel >= 4, rep.hasAlpha else { return -1 }
        let spp = rep.samplesPerPixel, bytesPerRow = rep.bytesPerRow
        let x0 = max(0, Int(rect.minX.rounded())), x1 = min(rep.pixelsWide, Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded())), y1 = min(rep.pixelsHigh, Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0 else { return -1 }
        var hit = 0
        for y in y0..<y1 {
            var p = y * bytesPerRow + x0 * spp
            for _ in x0..<x1 {
                if Int(base[p + 3]) > floor { hit += 1 }
                p += spp
            }
        }
        return hit
    }

    /// 一块矩形里**有墨像素的包围盒**（x 方向，按 alpha 过地板算）。宽度 −1 = 一格墨都没有。
    ///
    /// 为什么 R79 要把存在性探针从"计数"换成"宽度"：R78 那道闸门在 runner 上没拦住
    /// （run 38757049151 仍然是那四条红），说明占位区里 **有** ≥20 个过地板的像素 ——
    /// **R80 更正这条的机制**（臂 D 实测：`placeholderString` 撤成空之后那一格墨面积 0.0pt²）：
    /// 那颗"放大镜"**不存在** —— 产品这颗框是 `isBordered=false`、`drawsBackground=false`
    /// 的纯 `NSTextField`，那一格里的墨**全部**是那串占位字。真正骗过计数的是**那串字的开头几个字**：
    /// 画 2 个字与画 8 个字在"有没有 ≥20 个像素"上是同一个答案，而**宽度**分得开（前缀 ≈17pt、整串 86.5pt）。
    /// 计数分不开"只有图标"与"图标 + 一串字"，**宽度可以**：
    /// 图标自己 ≈14pt，本机实测占位字连图标是 x 12.0–98.5pt（86.5pt）。
    /// 两个数之间差六倍，所以地板取 40pt 不是刀尖上的数（见调用点注释）。
    static func alphaInkSpan(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 8) -> (min: Int, max: Int) {
        guard let base = rep.bitmapData, rep.samplesPerPixel >= 4, rep.hasAlpha else { return (-1, -1) }
        let spp = rep.samplesPerPixel, bytesPerRow = rep.bytesPerRow
        let x0 = max(0, Int(rect.minX.rounded())), x1 = min(rep.pixelsWide, Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded())), y1 = min(rep.pixelsHigh, Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0 else { return (-1, -1) }
        var lo = Int.max, hi = -1
        for y in y0..<y1 {
            var p = y * bytesPerRow + x0 * spp
            for x in x0..<x1 {
                if Int(base[p + 3]) > floor { if x < lo { lo = x }; if x > hi { hi = x } }
                p += spp
            }
        }
        return (lo == Int.max ? -1 : lo, hi)
    }

    /// 一块矩形里**搬动过的墨**有多少 pt²（R80 / BACKLOG 109）。
    ///
    /// 逐像素取「alpha 之差」与「三条 RGB 各自合成到中性灰之后之差」的**最大值**（并集，
    /// 与 R77 的 `axisPair` 同一条语义），只把过 `noiseFloor` 的像素累加，
    /// 最后 ÷255 得"多少个全不透明像素被动过"、再 ÷ `scale²` 换成 **pt²**。
    ///
    /// 为什么现有的 `changedPixelCount` 不够（R79 的 CI 读出来的）：那把尺数的是
    /// **"过 8/255 的像素个数"**，它对**像素网格**敏感 —— 本机 2× 那一串占位字给 1797 个，
    /// runner 1× 给 **0 个**（同一条 1px 宽的笔画在 1× 上只剩几个像素，每个都不过线）。
    /// 于是"这台机器的网格太粗"与"这一格今天什么都没动"在同一根尺上长得一样 ——
    /// 正是 R38 那一课（两台机器的读数不能当另一台机器的地板）在**尺的形状**上的版本。
    /// 这把尺累加的是"动了多少"，同一条字在 1× 与 2× 上给出**同一个 pt²**：
    /// 采样密一点不多不少，墨的物理面积没变。
    ///
    /// `noiseFloor` 是这把尺自己的每像素地板（/255）。它不许靠猜：调用点用
    /// **同一态重拍一张**（臂 R）量出这台机器上的噪声，`max(地板, 10×噪声)` 才是判据地板。
    static func movedInkPointsSquared(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                      rect: CGRect, scale: Int,
                                      noiseFloor: Double = 2, background: Double = 128) -> Double {
        guard let pa = a.bitmapData, let pb = b.bitmapData,
              a.samplesPerPixel >= 4, b.samplesPerPixel >= 4,
              a.hasAlpha, b.hasAlpha, scale >= 1 else { return -1 }
        let x0 = max(0, Int(rect.minX.rounded()))
        let x1 = min(min(a.pixelsWide, b.pixelsWide), Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded()))
        let y1 = min(min(a.pixelsHigh, b.pixelsHigh), Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0 else { return -1 }
        var sum = 0.0
        for y in y0..<y1 {
            var p = y * a.bytesPerRow + x0 * a.samplesPerPixel
            var q = y * b.bytesPerRow + x0 * b.samplesPerPixel
            for _ in x0..<x1 {
                let alphaA = Double(pa[p + 3]), alphaB = Double(pb[q + 3])
                // **α=0 就当没画**：预乘缓冲里这种像素的 RGB 必须是 0，可通道不一定每次都讲规矩
                // （R18 那一族：捕获通道的性质不会跟你商量）。不夹紧的话，一块"全透但 RGB 不同"
                // 的像素会被算成搬动过的墨 ⇒ 假视觉后果；④ 那一格钉的就是这一行。
                let inkA0 = alphaA == 0 ? 0.0 : Double(pa[p])
                let inkA1 = alphaA == 0 ? 0.0 : Double(pa[p + 1])
                let inkA2 = alphaA == 0 ? 0.0 : Double(pa[p + 2])
                let inkB0 = alphaB == 0 ? 0.0 : Double(pb[q])
                let inkB1 = alphaB == 0 ? 0.0 : Double(pb[q + 1])
                let inkB2 = alphaB == 0 ? 0.0 : Double(pb[q + 2])
                let weightA = background * (1.0 - alphaA / 255.0)
                let weightB = background * (1.0 - alphaB / 255.0)
                let deltaAlpha = abs(alphaA - alphaB)
                let deltaRed = abs(inkA0 + weightA - (inkB0 + weightB))
                let deltaGreen = abs(inkA1 + weightA - (inkB1 + weightB))
                let deltaBlue = abs(inkA2 + weightA - (inkB2 + weightB))
                // 并集：谁动得多用谁。**写成逐条比大小而不是 `max(max(...))`** 有两个理由：
                // 一是这条轴真的进判定（R77 的守卫认写法不认形状，一条 `let alphaDelta` 摆在那儿
                // 却不参与比较的尺，它现在会判成"只读亮度"—— 那一族的账本号是 M407）；
                // 二是读这段的人能一眼看出四根轴都参加了。
                var move = deltaRed
                if deltaGreen > move { move = deltaGreen }
                if deltaBlue > move { move = deltaBlue }
                if deltaAlpha > move { move = deltaAlpha }
                if move > noiseFloor { sum += move }
                p += a.samplesPerPixel
                q += b.samplesPerPixel
            }
        }
        return sum / 255.0 / Double(scale * scale)
    }

    /// 一块矩形里**画着的墨**有多少 pt²（R80；单帧尺，不读第二张 ⇒ 不进两态尺的名册）。
    ///
    /// 它是 `meanAlpha × 面积` 的另一副面孔，但两件事不一样：均值跟着**矩形大小**变
    /// （同一串字放在 800×32 与 200×32 的框里给出两个数），而 pt² 是那一格里墨的物理面积，
    /// 与框怎么选无关。焦点那一条判据要的正是后者 —— 它要说的是"这串字调淡了几成"，
    /// 分母必须是这一格自己的墨，而不是一条可以被换一块矩形就重新归一的均值。
    static func inkPointsSquared(_ rep: NSBitmapImageRep, rect: CGRect, scale: Int) -> Double {
        guard let base = rep.bitmapData, rep.samplesPerPixel >= 4, rep.hasAlpha, scale >= 1 else { return -1 }
        let spp = rep.samplesPerPixel, bytesPerRow = rep.bytesPerRow
        let x0 = max(0, Int(rect.minX.rounded())), x1 = min(rep.pixelsWide, Int(rect.maxX.rounded()))
        let y0 = max(0, Int(rect.minY.rounded())), y1 = min(rep.pixelsHigh, Int(rect.maxY.rounded()))
        guard x1 > x0, y1 > y0 else { return -1 }
        var sum = 0.0
        for y in y0..<y1 {
            var p = y * bytesPerRow + x0 * spp
            for _ in x0..<x1 {
                sum += Double(base[p + 3])
                p += spp
            }
        }
        return sum / 255.0 / Double(scale * scale)
    }

    /// 比两"条"水平带的 alpha，返回"每列各自带内的最大 alpha 之差 > `floor`"的 x 范围。
    ///
    /// 两种用法，共用一把尺：
    ///   · **同一张帧、两条带**（选中行 vs 静置行）⇒ 量到的是那颗选中药丸的横向范围；
    ///   · **同一条带、两张帧**（静置 vs 点亮）⇒ 量到的是那层灰的横向范围。
    /// 为什么按列取**带内最大**而不是只取中间那条 y：药丸在行里是上下都留空的（圆角 + 内缩），
    /// 取中间线会量到药丸以外的地方去 —— 实测同一张帧上"中间线"给出 71…654，
    /// 而"带内最大"给出 42…795，后者才是药丸真正的边界（也与灰带的 42…797 对得上）。
    static func alphaBandDelta(_ a: NSBitmapImageRep, _ aYs: Range<Int>,
                               _ b: NSBitmapImageRep, _ bYs: Range<Int>,
                               x0: Int, x1: Int, floor: Int) -> (min: Int, max: Int) {
        guard let pa = a.bitmapData, let pb = b.bitmapData,
              a.samplesPerPixel >= 4, b.samplesPerPixel >= 4,
              !aYs.isEmpty, !bYs.isEmpty else { return (-1, -1) }
        let left = max(0, x0), right = min(min(a.pixelsWide, b.pixelsWide), x1)
        let ay = aYs.map { max(0, min(a.pixelsHigh - 1, $0)) }
        let by = bYs.map { max(0, min(b.pixelsHigh - 1, $0)) }
        var lo = Int.max, hi = -1
        var x = left
        while x < right {
            var maxA = 0, maxB = 0
            for y in ay { maxA = max(maxA, Int(pa[y * a.bytesPerRow + x * a.samplesPerPixel + 3])) }
            for y in by { maxB = max(maxB, Int(pb[y * b.bytesPerRow + x * b.samplesPerPixel + 3])) }
            if abs(maxA - maxB) > floor {
                if x < lo { lo = x }
                if x > hi { hi = x }
            }
            x += 1
        }
        return (lo == Int.max ? -1 : lo, hi)
    }

    /// 逐行量"这一块墨的横向范围"：第 t 行取 `a` 带第 t 行与 `b` 带第 t 行的
    /// **alpha 差 ≥ `floor`** 的最左 / 最右像素，只返回有墨的行。
    ///
    /// 与 `alphaBandDelta` 的分工：那把尺按列取"带内最大"，量到的是**总范围**；
    /// 这把尺逐行给，量到的是**轮廓** —— 圆角、上下内缩这些东西只在逐行形状上看得见。
    /// R67 为什么必须新加一把尺：宽度判据给出"左差 −2px / 右差 +2px"就绿了，
    /// 而帧上那一层灰是**直角满高的矩形**、药丸是圆的（左沿内缩跨度 11px）。
    /// 两条总范围相同的带可以有完全不同的轮廓 ⇒ 只看总范围的判据**结构上**看不见这一族错。
    static func alphaLiftProfile(_ a: NSBitmapImageRep, _ aYs: Range<Int>,
                                 _ b: NSBitmapImageRep, _ bYs: Range<Int>,
                                 x0: Int, x1: Int, floor: Int) -> [(y: Int, left: Int, right: Int)] {
        guard let pa = a.bitmapData, let pb = b.bitmapData,
              a.samplesPerPixel >= 4, b.samplesPerPixel >= 4,
              aYs.count == bYs.count, !aYs.isEmpty else { return [] }
        let left = max(0, x0), right = min(min(a.pixelsWide, b.pixelsWide), x1)
        guard left < right else { return [] }
        var out: [(y: Int, left: Int, right: Int)] = []
        for t in 0..<aYs.count {
            let ay = max(0, min(a.pixelsHigh - 1, aYs.lowerBound + t))
            let by = max(0, min(b.pixelsHigh - 1, bYs.lowerBound + t))
            var lo = -1, hi = -1
            var x = left
            while x < right {
                let d = Int(pa[ay * a.bytesPerRow + x * a.samplesPerPixel + 3])
                    - Int(pb[by * b.bytesPerRow + x * b.samplesPerPixel + 3])
                if d >= floor {
                    if lo < 0 { lo = x }
                    hi = x
                }
                x += 1
            }
            if lo >= 0 { out.append((ay, lo, hi)) }
        }
        return out
    }

    /// 一条轮廓的"左沿内缩跨度"：所有行里最靠右的左沿 减 最靠左的左沿（px）。
    /// 直角矩形给 0，圆角矩形给 ≈ 半径（药丸实测 11px）—— 这一把尺就是"圆没圆"的读数。
    static func profileLeftInsetSpread(_ profile: [(y: Int, left: Int, right: Int)]) -> Int {
        guard let lo = profile.map(\.left).min(), let hi = profile.map(\.left).max() else { return -1 }
        return hi - lo
    }

    /// `clipping` 给定时只数矩形内的 —— 这一半就是"变化在不在它该在的那一格"。
    /// 合成这件事的理由与 `meanLuminance` 同一条：不合成，亮色那一遍的透明底会把 6% 的灰
    /// 读成"什么都没变"（RGB 都是 0），而暗色那一遍读得到 —— 一把跟着外观变性质的尺不能当判据。
    static func changedPixelCount(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep,
                                  clipping: CGRect? = nil, threshold: Int = 8,
                                  background: Double = 128) -> Int {
        guard a.pixelsWide == b.pixelsWide, a.pixelsHigh == b.pixelsHigh,
              let pa = a.bitmapData, let pb = b.bitmapData,
              a.samplesPerPixel >= 4, b.samplesPerPixel >= 4 else { return -1 }
        let width = a.pixelsWide, height = a.pixelsHigh
        var changed = 0
        var y = 0
        while y < height {
            var x = 0
            while x < width {
                if let rect = clipping, !rect.contains(CGPoint(x: Double(x) + 0.5, y: Double(y) + 0.5)) {
                    x += 1
                    continue
                }
                let p = y * a.bytesPerRow + x * a.samplesPerPixel
                let q = y * b.bytesPerRow + x * b.samplesPerPixel
                let d = max(abs(Int(Self.compositedChannel(pa, p, background).rounded())
                                - Int(Self.compositedChannel(pb, q, background).rounded())),
                            max(abs(Int(Self.compositedChannel(pa, p + 1, background).rounded())
                                    - Int(Self.compositedChannel(pb, q + 1, background).rounded())),
                                abs(Int(Self.compositedChannel(pa, p + 2, background).rounded())
                                    - Int(Self.compositedChannel(pb, q + 2, background).rounded()))))
                if d > threshold { changed += 1 }
                x += 1
            }
            y += 1
        }
        return changed
    }

    /// `quickpick-typed` 这张帧**必须是在打字，不是空列表**（R63 / U-99）。
    ///
    /// 为什么单独立一条：第一版这张帧的查询词是我从本轮探针的夹具里抄的"记录 3"，
    /// 而 harness 这个 store 里根本没有那种文本 ⇒ 帧拍出来是「没有匹配「记录 3」的记录」——
    /// **一张名字叫 typed、内容是 empty 的帧**。它是被"看图 + 一条兄弟比较"发现的，
    /// 但那两条都不是每次都能兜住：看图靠人记得看，兄弟比较在 runner 上还会因为
    /// 两台机器差 3pt 而假红（见 `sparseByDesignFixtures` 的注释）。
    /// 所以这条从产品入口直接数行，与像素、与 backing scale 都无关。
    func testQuickPickTypedFixtureShowsFilteredRowsNotAnEmptyList() throws {
        _ = NSApplication.shared
        let store = makePopulatedStore()
        func rowsFor(_ query: String) -> Int {
            let build = QuickPickCapturePanel.builder(store: store, query: query)
            guard let panel = build(), let content = panel.contentView else { return -1 }
            panel.setFrameOrigin(NSPoint(x: -20008, y: -20008))
            panel.orderFrontRegardless()
            RunLoop.main.run(until: Date().addingTimeInterval(0.1))
            var rows = -1
            func find(_ view: NSView) {
                if let table = view as? NSTableView, table.dataSource is QuickPickController {
                    rows = max(rows, table.numberOfRows)
                }
                view.subviews.forEach(find)
            }
            find(content)
            panel.orderOut(nil)
            return rows
        }
        let all = rowsFor("")
        // 与 `Fixture("quickpick-typed", …)` 里那个查询词**必须一致**：
        // 改夹具的查询词而不改这里，这条判据就会去判一个今天没人看的状态。
        let typed = rowsFor("访达")
        let none = rowsFor("zzz 不存在")
        emit("QUICKPICK_FIXTURE_ROWS all=\(all) typed(访达)=\(typed) empty(zzz 不存在)=\(none)")
        XCTAssertGreaterThan(all, 0, "全量那一档 0 行 ⇒ 这个 store 建不出候选，三条读数都没有对象")
        XCTAssertGreaterThan(typed, 0,
                             "「访达」在夹具 store 里命中 0 条 ⇒ `quickpick-typed` 那张帧拍的是空结果态，"
                             + "而它的名字说它在打字。换一条真能命中的词（并同步改这条判据）")
        XCTAssertLessThan(typed, all,
                          "「访达」命中了全部 \(all) 条 ⇒ typed 与 list 两张帧是同一张，"
                          + "过滤这件事仍然没有帧可看。换一条只命中一部分的词")
        XCTAssertEqual(none, 0, "「zzz 不存在」应该命中 0 条，否则 `quickpick-empty` 拍的不是空结果态")
    }

    /// R74 / U-115：浮层那一档悬停**不加淡入** —— 这条决定从今天起有读数，不是"我觉得"。
    ///
    /// 判的问题：给那层灰配一条 100ms 的淡入，用户打字时看到的是"过渡走完然后停住"，
    /// 还是"一直在打断重来"？后者 ⇒ 不加（淡入会把一次静置的描色变成呼吸）；
    /// 前者 ⇒ 我给 R67 的那句理由是错的，该加就得加。
    ///
    /// 量法走产品真路径：`queryChanged(_:)` 一个前缀一个前缀地喂，数两件**分开的**事：
    ///   ① 整列变了几个前缀（候选集往下切一层）；
    ///   ② 指针那一格（固定第 2 行）换了几次记录，含"那一行没了"。
    /// 分开打是因为它们证的不是同一件事：**整列动 ≠ 指针那一格动**，
    /// 而淡入的害处只在"指针那一格一直在换人"时才成立。断言用**比例**不用绝对次数：
    /// 打字速度、查询长度都不该由测试替产品决定。
    ///
    /// **两个语料都要量，因为第一个把我为 R67 写的那句理由证伪了**（U-128）：帧夹具那 5 条里
    /// "这是一段用于"只命中 1 条 ⇒ 6 个前缀列表只变 1 次 ⇒ "打字时整列一直在动"在这个语料上
    /// **不成立**。它不成立不是因为产品不动，是因为**这个夹具只剩一条命中** —— 一个只剩一条
    /// 结果的搜索框本来就不该重排。于是补上"同一条内容被反复复制"那一族真实形状（长度递增的
    /// 嵌套前缀），那才是浮层打字时的日常：每多打一个字，候选集往下切一层。
    ///
    /// 所以这一条的结论是**按语料限定**的，不是"任何情况下都不该加"：在嵌套语料上淡入的害处量得到，
    /// 在只命中一条的语料上量不到。写成限定式而不是全称式，是因为 U-115 要区分的正是
    /// "做过决定"与"没做过决定"，而第三种错更贵：**只在自己的夹具上成立的理由**（看着像证据）。
    func testOverlayHoverHasNoFadeAndTheReasonIsMeasuredOnTwoCorpora() throws {
        func reflow(store: HistoryStore, query: String) -> (prefixes: Int, changed: Int, churn: Int, rows: Int) {
            let build = QuickPickCapturePanel.builder(store: store, query: "")
            guard let panel = build(), let content = panel.contentView else { return (-1, -1, -1, -1) }
            panel.setFrameOrigin(NSPoint(x: -20009, y: -20009))
            panel.orderFrontRegardless()
            RunLoop.main.run(until: Date().addingTimeInterval(0.2))
            defer { panel.orderOut(nil) }
            guard let table = Self.productTable(in: content),
                  let controller = table.delegate as? QuickPickController else { return (-2, -2, -2, -2) }
            func visibleTitles() -> [String] {
                table.layoutSubtreeIfNeeded()
                return (0..<table.numberOfRows).compactMap { row in
                    (table.view(atColumn: 0, row: row, makeIfNecessary: true) as? NSTableCellView)?
                        .textField?.stringValue
                }
            }
            var prefixes: [String] = []
            var growing = ""
            for character in query { growing.append(character); prefixes.append(growing) }
            // 指针那一格固定在第 2 行：打字时鼠标通常是停着的，而 `mouseMoved` 是唯一能把那层灰
            // 补回来的入口 ⇒ "这一格此刻是谁"只由列表自己决定，不由测试决定。
            // 用空串而不是 nil 当"那一行没了"：让它和"换了别的记录"在同一个轴上可比。
            let pointerRow = 2
            var previous = visibleTitles()
            var atPointer = pointerRow < previous.count ? previous[pointerRow] : ""
            var changed = 0
            var churn = 0
            for prefix in prefixes {
                controller.queryChanged(prefix)
                let now = visibleTitles()
                if now != previous { changed += 1 }
                previous = now
                let nowPointer = pointerRow < now.count ? now[pointerRow] : ""
                if nowPointer != atPointer { churn += 1 }
                atPointer = nowPointer
            }
            return (prefixes.count, changed, churn, previous.count)
        }
        // 两个语料的分工写在上面那段文档里：帧夹具那条证伪了 R67 的理由（U-128），
        // 嵌套前缀那条才是浮层打字时的日常。
        let visualFixtureQuery = "这是一段用于"
        let query = "一二三四五六七八"
        let visual = reflow(store: makePopulatedStore(), query: visualFixtureQuery)
        let nested = reflow(store: makeNestedPrefixStore(), query: query)
        emit("OVERLAY_HOVER_REFLOW 帧夹具 前缀数=\(visual.prefixes) 整列变了=\(visual.changed) 次 "
            + "指针那格换了=\(visual.churn) 次 最终行数=\(visual.rows) "
            + "｜嵌套前缀语料 前缀数=\(nested.prefixes) 整列变了=\(nested.changed) 次 "
            + "指针那格换了=\(nested.churn) 次 最终行数=\(nested.rows)（指针=第 2 行，那一行没了也算换）")
        XCTAssertGreaterThanOrEqual(nested.prefixes, 3, "查询太短 ⇒ 这条判据没有对象")
        XCTAssertGreaterThanOrEqual(nested.changed, nested.prefixes - 1,
            "嵌套前缀语料里 \(nested.prefixes) 个前缀只让列表变了 \(nested.changed) 次 ⇒ "
                + "\"打字时整列一直在动\"这个理由不成立：淡入大部分时间能走完，"
                + "那不给悬停加过渡就只是没做，而不是做过决定（U-115 要的就是这个区分）。"
                + "注意 R67 当时写的就是这句话，而它在**帧夹具那个只命中一条的语料**上是错的（U-128）")
        XCTAssertLessThan(visual.changed, visual.prefixes - 1,
            "帧夹具那个语料什么时候变成\"每个字都重排\"了，上面那条对照就失去意义了 —— "
                + "它存在的理由就是\"一个只剩一条命中的搜索框不重排\"")
        XCTAssertGreaterThanOrEqual(nested.churn, nested.prefixes / 2,
            "整列变了 \(nested.changed) 次，但指针那一格（第 2 行）只换了 \(nested.churn) 次记录 ⇒ "
                + "那层灰基本一直停在同一条记录上，淡入走一次就能停住 —— 于是「淡入会变成呼吸」"
                + "这个**唯一的害处**就不成立了，这一格该重判（多半该加）。"
                + "两个数分开断言是因为它们证的不是同一件事：整列动 ≠ 指针那一格动")
        XCTAssertLessThan(visual.churn, visual.prefixes / 2,
            "帧夹具那一格换了 \(visual.churn) 次记录，快到每个前缀一次 ⇒ 这个语料被改成了嵌套形状，"
                + "它就不再是**反面语料**了：两个语料的对照塌成一个，"
                + "上面那条「整列一直在动」又变回只在一种形状上成立（U-128 那一课）")
        // 决定钉在源码上：这一族"声明了过渡但没人驱动"与"该动的没动"是同一枚硬币的两面，
        // 而这里我们**主动选择不动** ⇒ 必须有一条守卫，否则下一次有人顺手加 `.animation`
        // 或 `animator()` 时，没人知道这一格是量过才决定不加的。
        let rowSource = Self.codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        let hoverPart = rowSource.components(separatedBy: "final class QuickPickRowView").last ?? ""
        for forbidden in ["animator(", "NSAnimationContext", "animate(with:"] {
            XCTAssertFalse(hoverPart.contains(forbidden),
                "悬停那一档开始出现 `\(forbidden)` 了 ⇒ 这一格的决定是 R74 量过才做的"
                    + "（嵌套前缀语料里 \(nested.prefixes) 个前缀有 \(nested.changed) 次让整列重排、"
                    + "\(nested.churn) 次让指针那一格换人），"
                    + "要改这个决定请先重新量一遍，而不是顺手加一条动画")
        }
        // 第二条守卫钉的是**理由的机制**，不是结论：这一格不加淡入，靠的是「行重排会把那层灰拆掉，
        // 而把它补回来的唯一入口是指针事件」。哪天 `rebuildRows` 不再拆了（改成按指针位置重算、
        // 或把 hover 收进模型），我这套论证就过期 —— 那种红**不代表产品坏了**，
        // 代表「这一格该重判（也许真该加淡入）」。写清这一点是因为上一条守卫最容易被误修：
        // 看到红就顺手把 `clearHover` 加回去，等于用测试替产品保住一句已经不再成立的理由。
        let rebuild = Self.functionBody(named: "private func rebuildRows()", in: rowSource)
        XCTAssertTrue(rebuild.contains("clearHover"),
            "`rebuildRows` 里已经不叫 `clearHover` 了 ⇒ 「打字时那层灰会被拆掉、淡入每次都被打断」失去机制支撑"
                + "（实测：\(nested.prefixes) 个前缀让指针那一格换 \(nested.churn) 次人）。"
                + "这一条红的含义是「决定该重判」，不是「产品坏了」")
        // 扫描器自己的正/反对照（R71/M382 那一族的规矩：只测「该红的没红」不够，
        // 得证明这条网真的在网，而且网不住的时候会说「网住了」）。
        XCTAssertFalse(rebuild.isEmpty,
                       "扫不到 `rebuildRows` 的函数体 ⇒ 上面那条守卫是空转的（永远绿）")
        XCTAssertTrue(rebuild.contains("enumerateAvailableRowViews"),
                      "扫到的 `rebuildRows` 体里没有 `enumerateAvailableRowViews` ⇒ 截取的范围不对"
                          + "（多半在方法体之前就断了），那条守卫量的不是这个函数")
        XCTAssertFalse(rebuild.contains("final class QuickPickRowView"),
                       "从 `rebuildRows` 往后截到了类声明 ⇒ 截取器没在方法结尾断开，把文件后半当成了方法体 —— "
                           + "那 `contains(clearHover)` 判的就不再是这一个函数（这一条是截取器的**右边界**对照）")
        XCTAssertTrue(Self.functionBody(named: "private func definitelyNotInThisFile()", in: rowSource).isEmpty,
                      "一个不存在的函数名也能扫出东西 ⇒ 这个截取器「永远看得见」，"
                          + "上面几条源码守卫一起退化成噪声计数器")
    }

    /// 焦点那条轴的**处置**（R80）：把"这台机器判不了"这件事从一个 `if` 里提成一个**可测的函数**。
    ///
    /// 为什么要提成函数：这一整条判据只有 2× 那一台机器会走"正常"那一支，
    /// 1× 上的两支在本机**永远不会被执行** —— 一个本机跑不到的分支就是没有红钉着的分支，
    /// 而它恰恰是"能不能把一条轴说成没跑"的那道门（账本里"机器前提把该红的说成没跑"那一族）。
    /// 提出来之后它可以被合成数字直接打：三种处置各一格，改错一个 `>=` 就会红。
    enum FocusAxisDisposition: Equatable {
        /// 焦点这一档看得见在让位 ⇒ 照正常那几条判。
        case judged
        /// 同一把尺在同一格读得出别的成因在搬动，而聚焦不动 ⇒ 这台机器的 AppKit 不调淡占位符。
        case behaviorAbsentOnThisMachine
        /// 连"撤掉整串占位字"都读不出搬动 ⇒ 这一格对这把尺整体失明，判不判都是空的。
        case channelBlindOnThisMachine
    }

    /// 判据地板 = `max(常数地板, 噪声倍数 × 这台机器上同态重拍的噪声)`（R80，R38 的形状）。
    /// 单独提成函数是为了它能被**合成数字**打：本机噪声实测 0.0pt² ⇒ 那一条乘在这里永远乘出 0，
    /// 没有这一格，`focusNoiseMargin` 就是一个没有红的常数（账本里"地板从表推导"那一族的下半场：
    /// 推导出来了，但没人钉着推导的那一步）。
    static func focusFloorPointsSquared(noisePt2: Double) -> Double {
        max(focusMinMovedPointsSquared, focusNoiseMargin * noisePt2)
    }

    /// 处置 = 三个读数之间的关系，**不看它是哪台机器**（scale 由调用点单独决定放行还是红）。
    /// 两条地板分开给：`floorPt2` 是判据地板（含噪声余量），`competenceFloorPt2` 是证人地板 ——
    /// 它们不许合成一个数（R77 那一课：同一个词在两个判据里含义不同就别统一）。
    static func focusDisposition(focusMovedPt2: Double, floorPt2: Double,
                                 dimFraction: Double, minDimFraction: Double,
                                 competencePt2: Double, competenceFloorPt2: Double) -> FocusAxisDisposition {
        if focusMovedPt2 >= floorPt2 && dimFraction >= minDimFraction { return .judged }
        return competencePt2 >= competenceFloorPt2
            ? .behaviorAbsentOnThisMachine : .channelBlindOnThisMachine
    }

    /// R80 · 那把尺的**处置**三支各钉一格。
    ///
    /// 这三格是本轮唯一能给 1× 那两支作证的東西：本机永远走"judged"，
    /// 所以那两支在这台机器上**没有任何一条红**会跟着它们坏 —— 不单独钉就等于没写。
    func testFocusAxisDispositionIsATruthTable() throws {
        // 这几格**引用常量本身**，不引用我手抄的数 —— 否则抬高某道地板会只红在判据上，
        // 而"这条轴能不能被说成没跑"那扇门（在 1× 上）永远没有红钉着（R78 的 M415 同一课）。
        let floor = Self.focusMinMovedPointsSquared
        let competenceFloor = Self.competenceMinMovedPointsSquared
        let minFraction = Self.focusMinDimFraction
        func disposition(focus: Double, fraction: Double, competence: Double) -> FocusAxisDisposition {
            Self.focusDisposition(focusMovedPt2: focus, floorPt2: floor, dimFraction: fraction,
                                  minDimFraction: minFraction, competencePt2: competence,
                                  competenceFloorPt2: competenceFloor)
        }
        // 格①：本机那一遍的真实读数（亮档 98.7pt² / 占比 0.367 / 证人臂 268.7）⇒ judged
        XCTAssertEqual(disposition(focus: 98.7, fraction: 0.367, competence: 268.7), .judged,
                       "本机实测那一组数被判成'判不了' ⇒ 这条轴的正常那一支从此没人走")
        // 格②：runner 预计那一组（搬动 1.3、占比 0.014）而证人臂读得出东西 ⇒ 尺不瞎
        // 这里的 268.7 是**本机实测的证人臂读数**（`QUICKPICK_FOCUS_INK` 亮档那一列），
        // 不是随手写的数：这一格钉的正是"证人地板**现在这个大小**能不能让实测的证人过关"，
        // 所以它必须引用测量、不能引用常数 —— 写成 `competenceFloor + 49` 的话，
        // 有人把地板抬到十万也照样绿（M431 第一次就是这么逃的，本轮自己抓到）。
        XCTAssertEqual(disposition(focus: 1.3, fraction: 0.014, competence: 268.7),
                       .behaviorAbsentOnThisMachine,
                       "证人臂明明读得出别的成因在搬动，却把这一档说成'通道失明' ⇒ 这条缺席是在替产品开脱")
        // 格③：搬动与证人**都**读不出 ⇒ 只有这一支才允许说"这一格对这把尺看不见"
        XCTAssertEqual(disposition(focus: 1.3, fraction: 0.014, competence: competenceFloor - 0.1),
                       .channelBlindOnThisMachine,
                       "两条证人臂都过不了地板却仍被判成'这台机器不调淡' ⇒ 那是拿'行为没有'冒充'通道看不见'，"
                           + "反过来说就是：把一条本该红的轴说成没跑")
        // 格④：边界 —— 正好等于两道地板的不许算不过（`>=` 被写成 `>` 这一格就红）
        XCTAssertEqual(disposition(focus: floor, fraction: minFraction, competence: competenceFloor),
                       .judged,
                       "正好等于地板的必须算过 ⇒ 边界那一档被写成 `>` 之后，读数恰好在地板上的机器会说'看不见'")
        // 格⑤：占比单独承重 —— 搬动量够、占比不够 ⇒ 不许 judged（那是一条轴没在干活）
        XCTAssertNotEqual(disposition(focus: floor + 1, fraction: minFraction - 0.01,
                                      competence: competenceFloor), .judged,
                          "搬动量过线就判得出 ⇒ `focusMinDimFraction` 那一道没人钉，"
                              + "整格墨变淡到一半也能被读成'焦点在让位'")
        // 地板推导那一半：本机噪声是 0 ⇒ 乘法在这里永远乘出 0，必须用合成数字钉住它
        XCTAssertEqual(Self.focusFloorPointsSquared(noisePt2: 0), floor, accuracy: 0.001,
                       "噪声为 0 时地板应该回到常数地板")
        XCTAssertEqual(Self.focusFloorPointsSquared(noisePt2: floor), floor * Self.focusNoiseMargin,
                       accuracy: 0.001,
                       "噪声等于地板时判据地板必须抬高 `focusNoiseMargin` 倍 —— 这一条不许靠注释，"
                           + "它钉的是『地板从这一台机器的噪声推导』那句话里的那个系数")
        XCTAssertGreaterThan(Self.focusFloorPointsSquared(noisePt2: 5),
                             Self.focusFloorPointsSquared(noisePt2: 1),
                             "地板不随噪声抬高 ⇒ 一台抖动大的机器会把噪声当成'焦点搬动了'")
        emit("FOCUS_DISPOSITION_TRUTH_TABLE judged/behaviorAbsent/channelBlind/边界/占比=5 格 "
            + "+ 地板随噪声=3 格 ⇒ 地板=\(floor)pt² 证人=\(competenceFloor)pt² 占比=\(minFraction)")
    }

    ///
    /// 为什么必须**合成夹具**而不是拿帧来判：本轮要钉的性质是"同一个物理变化在 1× 与 2×
    /// 上给出同一个数"，而这条只能靠**构造**出来 —— 我手上没有第二台机器，
    /// runner 的那一遍读数要等 CI（R70 那一课的对称：能被自己造出来的性质不等 CI）。
    /// 夹具是**直接写字节**的（`flatRep` 那一族的原因同样成立：`setColor(_:atX:y:)`
    /// 在整数格式位图上不落地、而且不报错，而尺子的夹具读到 0 最容易被读成"没差别"）。
    ///
    /// 夹具的形状：一张 **100×20pt** 的图，两帧各自**整张一块均匀的墨**（⑤ 那格单独把
    /// 第二帧的右半改成另一个 alpha）。期望值全是解析数：
    ///   面积 = 100×20 = 2000pt²；每像素动 Δ ⇒ 搬动 = 2000×Δ÷255。
    ///   ② Δalpha=100 ⇒ **784.31**；③ 黑翻蓝（Δ蓝=255，alpha 不变）⇒ **2000.00**；
    ///   ⑤ 右半 1000pt² 动 100 ⇒ 左读 **0**、右读 **392.16**；
    ///   ⑥ Δ=1 ⇒ **0**（地板下）；⑦ Δ=3 ⇒ **23.53**（地板上）；
    ///   ⑨ 单帧 alpha=200 整张 ⇒ **1568.63**；⑧ 旧尺数像素 ⇒ **2000×缩放²**。
    ///
    /// 九个格子各拦一种错：
    ///   ① `same` —— 自己减自己 = 0（拦"尺恒开"）。
    ///   ② `alphaDim` —— 只在 alpha 上动的一整块墨：**两档缩放必须给出同一个 pt²**。
    ///      这一格是整轮的性质所在（R38：地板不能跟着像素网格变）。
    ///   ③ `colorOnly` —— 全不透明、只在蓝通道上动 ⇒ 必须读得出（R77 并集语义的另一半；
    ///      一把只读 alpha 的尺在这里给 0，那一族的后果在 BACKLOG 108）。
    ///   ④ `invisible` —— α 恒 0 而 RGB 不同（预乘格式里的非法态，故意造出来）⇒ 必须读成 0，
    ///      这条钉的是尺子里那句"α=0 就当没画"的夹紧：通道哪天换了非预乘格式，
    ///      不夹紧就会把"根本没画"的像素算成搬动过的墨（R77 那族假阳性的镜像）。
    ///   ⑤ `position` —— 变化只在右半 ⇒ 量左半那块矩形必须读 0（位置同一性，不是"有没有变化"）。
    ///   ⑥⑦ `underFloor` / `overFloor` —— 每像素差 1 与差 3：**成对**给出，
    ///      这样 `noiseFloor` 不是一句注释而是一道有两边的门（只给一边就能被抵消）。
    ///   ⑧ **本轮换尺的理由本身**：同一件物理变化在旧那把尺上按 `缩放²` 变
    ///      （2000 个像素 vs 8000 个）。那道 `≥500 个像素` 的地板在两台机器上量的不是同一件事
    ///      ⇒ R76 那句"本机 1797 / runner 0"里最多 3/4 是网格，剩下那 1/4 才是交给 CI 去分的问题。
    ///   ⑨ `inkPointsSquared` —— 单帧墨面积在两种网格下同一个 pt²（占比那条判据的分母）。
    func testMovedInkRulerIsGridNormalizedAndReadsBothAxes() throws {
        // 一帧一块均匀的墨：`from*` 是第一帧、`to*` 是第二帧（**不是**同一帧的左右两半 ——
        // 第一版我把参数写成 left/right，然后把整张一涂的夹具当成"左半有墨"来算期望值，
        // ②③⑦⑧⑨ 五格集体差了两倍；这一格留在这里当反面教材，因为它是"参数名替事实说话"）。
        func makeRep(scale: Int, alpha: Int, blue: Int) -> NSBitmapImageRep {
            let w = 100 * scale, h = 20 * scale
            let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                                       bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                       isPlanar: false, colorSpaceName: .deviceRGB,
                                       bytesPerRow: 4 * w, bitsPerPixel: 32)!
            guard let data = rep.bitmapData else {
                XCTFail("造不出夹具位图 ⇒ 这把尺的真值表没有对象")
                return rep
            }
            for y in 0..<h {
                for x in 0..<w {
                    let o = y * rep.bytesPerRow + x * 4
                    // 整块都写成同样的字节：**不给抗锯齿**，这几格要的是"整块墨"的形状。
                    data[o] = 0
                    data[o + 1] = 0
                    data[o + 2] = UInt8(blue)
                    data[o + 3] = UInt8(alpha)
                }
            }
            return rep
        }
        func flatPair(scale: Int, fromAlpha: Int, toAlpha: Int,
                      toBlue: Int = 0) -> (NSBitmapImageRep, NSBitmapImageRep) {
            (makeRep(scale: scale, alpha: fromAlpha, blue: 0),
             makeRep(scale: scale, alpha: toAlpha, blue: toBlue))
        }
        var readings: [String] = []
        for scale in [1, 2] {
            let w = 100 * scale, h = 20 * scale
            let wholeRect = CGRect(x: 0, y: 0, width: w, height: h)
            func moved(_ pair: (NSBitmapImageRep, NSBitmapImageRep), _ rect: CGRect) -> Double {
                Self.movedInkPointsSquared(pair.0, pair.1, rect: rect, scale: scale)
            }
            // ①
            XCTAssertEqual(moved(flatPair(scale: scale, fromAlpha: 200, toAlpha: 200), wholeRect),
                           0, accuracy: 0.001, "\(scale)×：自己减自己必须读 0")
            // ②
            let dim = flatPair(scale: scale, fromAlpha: 200, toAlpha: 100)
            let movedDim = moved(dim, wholeRect)
            XCTAssertEqual(movedDim, 784.31, accuracy: 1.0,
                "\(scale)×：2000pt² 的墨从 alpha 200 掉到 100，搬动量必须 ≈784.31pt² "
                    + "（实测 \(String(format: "%.2f", movedDim))）⇒ 这个数一旦跟着缩放走，"
                    + "判据地板就又是『一台机器的读数当另一台的地板』（R38）")
            // ③ 只在蓝通道上动、alpha 拉满：一把只读 alpha 的尺在这里给 0
            let color = flatPair(scale: scale, fromAlpha: 255, toAlpha: 255, toBlue: 255)
            let movedColor = moved(color, wholeRect)
            XCTAssertEqual(movedColor, 2000.0, accuracy: 1.0,
                "\(scale)×：全不透明的黑翻成蓝，搬动量必须 ≈2000pt²（实测 \(String(format: "%.2f", movedColor))）"
                    + "⇒ 读到 0 就是这把尺**只认 alpha**，那一族的后果写在 BACKLOG 108")
            // ④ alpha 恒 0 而 RGB 不同 ⇒ 合成到底上是同一块 ⇒ 必须 0
            let ghost = flatPair(scale: scale, fromAlpha: 0, toAlpha: 0, toBlue: 255)
            let movedGhost = moved(ghost, wholeRect)
            XCTAssertEqual(movedGhost, 0, accuracy: 0.001,
                "\(scale)×：两帧都是全透的（alpha=0），RGB 再怎么不同也**没画** ⇒ 必须读 0，"
                    + "否则这把尺会把『看不见』的东西算成视觉后果")
            // ⑤ 变化只在右半 ⇒ 量左半那块矩形必须读 0（位置同一性）
            let right = flatPair(scale: scale, fromAlpha: 200, toAlpha: 200)
            if let data = right.1.bitmapData {
                for y in 0..<h {
                    for x in (50 * scale)..<w {
                        data[y * (4 * w) + x * 4 + 3] = 100
                    }
                }
            }
            let leftHalf = CGRect(x: 0, y: 0, width: 50 * scale, height: h)
            let rightHalf = CGRect(x: 50 * scale, y: 0, width: 50 * scale, height: h)
            let movedLeft = moved(right, leftHalf)
            let movedRight = moved(right, rightHalf)
            XCTAssertEqual(movedLeft, 0, accuracy: 0.001,
                "\(scale)×：变化明明在右半，量左半却读出 \(String(format: "%.2f", movedLeft))pt² ⇒ "
                    + "矩形没起作用，这把尺会把『动在别处』当成『动在这一格』")
            XCTAssertEqual(movedRight, 392.16, accuracy: 1.0,
                "\(scale)×：右半那 1000pt² 的墨掉一半，应该 ≈392.16pt²（实测 \(String(format: "%.2f", movedRight))）")
            // ⑥⑦ 噪声地板两边各一格：每像素差 1（<2，必须不算）与差 3（>2，必须算）
            let movedUnder = moved(flatPair(scale: scale, fromAlpha: 200, toAlpha: 199), wholeRect)
            let overPair = flatPair(scale: scale, fromAlpha: 200, toAlpha: 197)
            let movedOver = moved(overPair, wholeRect)
            XCTAssertEqual(movedUnder, 0, accuracy: 0.001,
                "\(scale)×：每像素只差 1/255 必须被 `noiseFloor` 挡掉（实测 \(movedUnder)）⇒ "
                    + "地板没有下边这一格，它就等于不存在")
            XCTAssertGreaterThan(movedOver, 0,
                "\(scale)×：每像素差 3/255 必须过 `noiseFloor` —— 地板只有一边就是一道能被抵消的门")
            XCTAssertEqual(movedOver, 23.53, accuracy: 0.5,
                "\(scale)×：2000pt² 每像素动 3/255 ⇒ ≈23.53pt²（实测 \(String(format: "%.2f", movedOver))）")
            // ⑨ 单帧墨面积（占比那条判据的分母）
            let ink = Self.inkPointsSquared(dim.0, rect: wholeRect, scale: scale)
            XCTAssertEqual(ink, 1568.63, accuracy: 1.0,
                "\(scale)×：整张 2000pt²、alpha=200 的墨，面积必须 ≈1568.63pt² "
                    + "（实测 \(String(format: "%.2f", ink))）⇒ 它是占比那条判据的分母，"
                    + "分母跟着网格走，整条判据就跟着网格走")
            // ⑧ **本轮换尺的理由**：同一件物理变化在旧尺上按 缩放² 变。
            let changed = Self.changedPixelCount(dim.0, dim.1, clipping: wholeRect)
            XCTAssertEqual(Double(changed), Double(2000 * scale * scale), accuracy: Double(scale * scale),
                "\(scale)×：旧那把尺在同一个物理变化上数到 \(changed) 个像素 —— 它**应该**按 缩放² 变，"
                    + "这一格钉的是『换尺的理由』这件事本身：那道 `≥500 个像素` 的地板在 1× 与 2× 上"
                    + "量的不是同一件事（本机 1797 / runner 0 那句里最多 3/4 是网格）")
            readings.append("\(scale)×:②搬动=\(String(format: "%.2f", movedDim)) "
                + "③并集=\(String(format: "%.2f", movedColor)) ④全透=\(String(format: "%.2f", movedGhost)) "
                + "⑤左/右=\(String(format: "%.2f", movedLeft))/\(String(format: "%.2f", movedRight)) "
                + "⑥⑦地板下/上=\(String(format: "%.2f", movedUnder))/\(String(format: "%.2f", movedOver)) "
                + "⑨面积=\(String(format: "%.2f", ink)) ⑧旧尺像素=\(changed)")
        }
        emit("CAPTURE_INK_RULER_TRUTH_TABLE " + readings.joined(separator: " | "))
    }
    /// R76 / U-116：浮层搜索框的**焦点那一档** —— 它不是"没有视觉后果"，是"只活在 alpha 通道里"。
    ///
    /// 这条判据本来要写的是"焦点态在帧里看不见 ⇒ 只能真机判"。量出来不是那么回事，
    /// 而且中间我自己错了一次（U-131）：第一版拿"建出来时"与"`makeFirstResponder` 之后"相减，
    /// 而实测那颗框**建出来的那一刻就已经聚焦**（AppKit 把 key view 选成了它）
    /// ⇒ 两张帧同一个状态，那个"0 个变化像素"什么都没证明。
    /// 换成"聚焦 vs 撤掉焦点"两态之后，差是真的，而且很大（**下面这几个数就是这条判据自己打出来的
    /// 那一行 `QUICKPICK_FOCUS`，R78 对过账**：本机 2×，亮档 / 暗档）：
    ///   框内变化像素 1797 / 2354，框外那一圈 0 / 0；
    ///   那一格平均 alpha 10.71 ⇒ 6.77（亮）、13.15 ⇒ 8.64（暗），差 3.93 / 4.52；
    ///   占位区（左 30%、内缩 3pt）有墨像素 1699 / 1871，整窗 69048 / 71021。
    /// R76 的注释在这里写过一组别的数（"1901 / 2144 个像素"与"alpha 143.6 ⇒ 90.9"），
    /// 而那两个数在这条判据的读数里根本不存在 —— 1901/2144 其实是**有墨像素**（R78 新加的那一列
    /// 量出来正好是它们），被当成"变化像素"抄进了注释；143.6/90.9 是第一版拿另一块矩形量的。
    /// 记在这里是因为这就是"注释替事实背书"的代价：R77 的台账照抄了注释，
    /// 而判据自己打的读数才是唯一该被引的那一份（U-139）。
    /// 但**同一对在亮度轴上只有 -0.66 / +2.25（/255）** ⇒ 只看亮度的尺会判成"焦点没有后果"。
    /// 于是这一格的四条断言各钉一样，少一条就有一族回归没人管：
    ///   ① 焦点确实落进那颗框（读产品对象：窗口响应者是字段编辑器，不是帧）；
    ///   ② 焦点**有**视觉后果，且方向是"让位"（那一格 alpha 必须降）—— 不是"变响"；
    ///   ③ 后果必须留在框内（框外那一圈 0 个像素）⇒ "不加自定义焦点环"这一格是量过的决定，
    ///      将来谁让焦点往框外画东西，这条会红，含义是"该重判"，不是"把绘制删掉"；
    ///   ④ 系统环不许被关掉（`focusRingType` 必须是 0 = 系统自己决定）。
    ///      **这格的坑**：raw 0 才是"系统决定"，而 Swift 里 `.none` 的 raw 是 **1**，
    ///      按名字猜会写成"等于 .none"，那正好把"环被关掉"当成通过（U-133）。
    /// 外加一条源码守卫：产品 `show()` 的函数体里必须同时有 `makeKeyAndOrderFront` 与
    /// `makeFirstResponder(field)` —— 少了后者的话①②③④全都不会红（浮层照样能用，
    /// 只是打字要用户多点一下那颗框）。
    ///
    /// 仍然量不到的一件事（点名，不猜）：真机上那颗框**有没有**系统焦点环。
    ///
    /// **R80 换了②③那两条的尺**（BACKLOG 109 的答案、D-138）：从"数过地板的像素个数"
    /// 换成"搬动了多少 **pt²** 的墨 + 占那一格现有墨的**比例**"，并同时拍下三条证人臂
    /// （同态重拍的噪声 / 撤掉 `placeholderString` / 打进一个字）。换尺是被 R79 的 CI 逼的：
    /// 那一遍 runner 上存在性闸门**开**（`占位整条宽=87.0pt`）而两态差读 0 个像素，
    /// 于是"焦点没有视觉后果"与"这台机器的网格太粗"又长回了同一句话。
    /// 合成夹具那一轮的真值表（`CAPTURE_INK_RULER_TRUTH_TABLE`）钉住新旧两把尺的分别是
    /// **4 倍**（2000 个像素 vs 8000 个，同一个物理变化）—— 那道 `≥500 个像素` 的地板
    /// 在两台机器上量的从来不是同一件事。④ 那条（不许关掉系统环）本轮**挪到像素判据之前**，
    /// 因为 R78 那道闸门会 `continue`，而它的注释写着"④照判"—— 注释在替代码撒谎（U-139 那一族）。
    ///
    /// 这条通道不带 key 窗口（`appActive=false 面板key=false`），所以③那个"框外 0 像素"
    /// 不能推成"产品没有环" ⇒ `QUICKPICK_FOCUS_RING_NOT_RUN=1`，人工批次 68.1。
    /// 存在性闸门的地板（pt）：带内"有墨像素的 x 包围盒"至少这么宽，才算那串占位字画出来了。
    /// 来历见调用点：图标自己 ≈14pt、图标 + 占位字实测 86.5pt，40pt 落在两者中间且两边都有倍数余量。
    static let placeholderMinSpanPoints: Double = 40

    /// 焦点"让位"那条判据的地板（R80），三条一起用：
    ///   · `focusMinMovedPointsSquared` —— 搬动的墨至少这么多 **pt²**；
    ///   · `focusNoiseMargin` —— 或者至少是**这一台机器上同态重拍噪声**的这么多倍（臂 R）；
    ///   · `focusMinDimFraction` —— 且不少于那一格里现有墨的这个**占比**。
    /// 来历（本机 2× 那一遍 `QUICKPICK_FOCUS_INK` 打的数，亮 / 暗）：
    ///   焦点搬动 **98.7 / 113.3pt²**、那一格现有墨 **268.7 / 330.1pt²**、占比 **0.367 / 0.343**、
    ///   同态重拍噪声 **0.0 / 0.0pt²**、证人臂撤占位字 **268.7 / 330.0pt²**、打进字 **236.7 / 283.9pt²**。
    /// ⇒ 40pt² 是实测焦点搬动量的约 1/2.5～1/3，8% 是实测占比的约 1/4.5；而 runner 那一侧按 R79 读到的
    ///   均值差换算约 **1.3pt²**（0.05×6400÷255）—— 在地板下面 30 倍。这道地板**不是**为 runner 调的
    ///   （R38：不许拿一台机器的读数当另一台的地板），它两边都留了倍数余量；
    ///   runner 过不了的时候由**证人臂**决定那是『尺在这一格瞎了』还是『这台机器不调淡』。
    /// 为什么不沿用 R76 那两个数（`变化像素 ≥ 500`、`alpha 均值掉 ≥ 2.0`）：
    /// 它们量的都是**同一件事在某一像素网格上的投影**。runner 1× 与本机 2× 读出
    /// 0 与 1797（同一个 3/4 是网格），而"均值掉 2.0"那道地板在带均值 10.71 与 3.55 的两台机器上
    /// 也不是一个难度（R38 那一课，只是这次是我自己新写的判据中招）。
    /// pt² 与占比都是**网格无关**的量 ⇒ 同一道地板在两台机器上说的是同一句话。
    static let focusMinMovedPointsSquared: Double = 40
    static let focusNoiseMargin: Double = 10
    static let focusMinDimFraction: Double = 0.08
    /// 证人臂（撤占位符 / 打进字）至少要搬动这么多 pt²，才算"这把尺在这一格看得见东西"。
    /// 它决定 `QUICKPICK_FOCUS_AXIS_NOT_RUN` 那句是"尺瞎了"还是"这台机器不调淡"——
    /// 两种成因的处置不同，所以这条地板不能与上面那条合用一个数（R77 的教训：
    /// 同一个词在两个判据里含义不同就别统一成一个布尔值）。本机实测这条臂 268.7 / 330.0pt²。
    static let competenceMinMovedPointsSquared: Double = 40

    func testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing() throws {
        for (label, appearance) in [("亮", NSAppearance.Name.aqua),
                                    ("暗", NSAppearance.Name.darkAqua)] {
            let build = QuickPickCapturePanel.builder(store: makePopulatedStore(), query: "")
            guard let panel = build(), let content = panel.contentView else {
                throw XCTSkip("捕获入口建不出浮层窗口 ⇒ 这一档今天无从判定（不是产品没做）")
            }
            _ = NSApplication.shared
            let previousAppearance = NSApplication.shared.appearance
            NSApplication.shared.appearance = NSAppearance(named: appearance)
            content.appearance = NSAppearance(named: appearance)
            panel.setFrameOrigin(NSPoint(x: -20011, y: -20011))
            panel.orderFrontRegardless()
            RunLoop.main.run(until: Date().addingTimeInterval(0.2))
            Self.tileScrollViews(in: content)
            defer {
                NSApplication.shared.appearance = previousAppearance
                panel.orderOut(nil)
            }
            guard let field = Self.firstView(ofType: QuickPickSearchField.self, in: content) else {
                return XCTFail("浮层树里找不到那颗 `QuickPickSearchField` ⇒ 这条判据没有对象")
            }
            func shoot() -> NSBitmapImageRep {
                panel.display()
                RunLoop.main.run(until: Date().addingTimeInterval(0.05))
                guard let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds) else {
                    return NSBitmapImageRep()
                }
                content.cacheDisplay(in: content.bounds, to: rep)
                return rep
            }
            // 两态对照：**"焦点这一档有没有像素"只能拿"聚焦"与"不聚焦"两张帧相减。**
            // 这一条第一版写错了，而错得很有代表性：我拿的是"建出来时"与"`makeFirstResponder` 之后"，
            // 实测建出来的那一刻那颗框**就已经**带着字段编辑器（AppKit 把 key view 选成了它）
            // ⇒ 两张帧是同一个状态，那个"0 个变化像素"什么也没证明。
            // 这就是"正对照读的不是判据读的那个量"那一族（U-131），本轮自己撞在自己新写的判据上。
            let builtInEditor = field.currentEditor()
            let accepted = panel.makeFirstResponder(field)
            RunLoop.main.run(until: Date().addingTimeInterval(0.15))
            let focusedResponder = panel.firstResponder
            let focused = shoot()
            // 反面那一态：把焦点从那颗框上拿走。两态必须**真的**不同，否则下面的相减是空转。
            panel.makeFirstResponder(nil)
            RunLoop.main.run(until: Date().addingTimeInterval(0.15))
            let blankResponder = panel.firstResponder
            let unfocused = shoot()
            // ===== R80 的三条证人臂（BACKLOG 109 的第二分支：独占区有墨而两态差为 0）=====
            // runner（run 38760347161）把这一格判成"焦点没有视觉后果"，而本机判成"有 394pt² 的墨在动"。
            // 只靠这两张帧永远分不开那两句话，所以这里在同一颗框上再加三个状态，
            // **全部用同一把尺**（R68：证人必须与它作证的判据读同一个量）量"那一格里搬动了多少墨"：
            //   臂 R `againUnfocused` —— **不改变任何状态**再拍一张。它给的是这台机器上这把尺的
            //     噪声地板：同一态两张帧之差读出来多少，判据地板就必须高于它（R38：地板从表推导，不猜）。
            //   臂 D `noPlaceholder` —— `placeholderString = ""`。这一格里那串字**必须**消失，
            //     它是"这条通道在 1× 上能不能表达这一格的墨变化"的直接证人：
            //     D 读得出东西而 B 读不出 ⇒ 尺不瞎，是"聚焦不调淡"这件事在这台机器上不成立。
            //   臂 C `hasText` —— `stringValue = "搜"`（AppKit 在有字时不画占位符）。
            //     与 D 不同的失效面：D 撤的是**属性**（AppKit 的占位符绘制分支整条不走），
            //     C 走的是**另一条绘制路径**（字符串本身）。两条都空 = 这一格对这把尺失明；
            //     只有一条空 = 那条臂作废，读数仍然要发出来。
            // 这三张帧都不落盘（`shoot()` 只返回 rep），所以帧基线那 124 张不受影响。
            let againUnfocused = shoot()
            let placeholderWas = field.placeholderString
            field.placeholderString = ""
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            let noPlaceholder = shoot()
            field.placeholderString = placeholderWas
            let textWas = field.stringValue
            field.stringValue = "搜"
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            let hasText = shoot()
            field.stringValue = textWas
            let scale = max(1, focused.pixelsWide / max(Int(content.bounds.width), 1))
            let inContent = field.convert(field.bounds, to: nil)
            let band = CGRect(x: inContent.minX * CGFloat(scale),
                              y: (content.bounds.height - inContent.maxY) * CGFloat(scale),
                              width: inContent.width * CGFloat(scale),
                              height: inContent.height * CGFloat(scale))
            // 焦点环画在框**外面**（约 3–4pt），所以只看框那一格会把"环"看成"没有变化"。
            let halo = band.insetBy(dx: -8 * CGFloat(scale), dy: -8 * CGFloat(scale))
            let changedIn = Self.changedPixelCount(focused, unfocused, clipping: band)
            let changedHalo = Self.changedPixelCount(focused, unfocused, clipping: halo)
            // **两把尺一起打：亮度轴与 alpha 轴。** 实测（R76，本机 2×，亮/暗两档）：
            //   亮度轴整带差 = -0.66 / +2.25（/255）⇒ 只看亮度会得出"焦点没有视觉后果"的假结论；
            //   alpha 轴：占位符那一格 143.6 ⇒ 90.9（亮）、156.5 ⇒ 102.9（暗），
            //            变化像素 1901 / 2144，包围盒正好是那一串占位字（x 12.0–98.5pt、y 顶下 14–26pt）。
            // ⇒ 焦点这一档**有**视觉后果（占位符退后给光标让位），但它只活在 alpha 通道里。
            //    判据必须走 alpha —— 与"灰 vs 蓝别用亮度轴"同族（U-132）。
            let lumIn = Self.meanLuminance(unfocused, rect: band) - Self.meanLuminance(focused, rect: band)
            let alphaUnfocused = Self.meanAlpha(unfocused, rect: band)
            let alphaFocused = Self.meanAlpha(focused, rect: band)
            // **存在性尺（R78）**：这一格里画没画东西，与"两态差没差"是两个问题。
            // runner 那一遍（run 38743276799）报的是 `框内变化像素=0`、`alpha 差 0.05`，
            // 本机是 1797 / 3.93 —— 只读差值的尺子分不开"焦点没有后果"与"那串字今天没画"。
            // 所以这里另量一个不依赖两态相减的数：占位符那一格里 alpha 过地板的像素数。
            let wholePanel = CGRect(x: 0, y: 0, width: unfocused.pixelsWide, height: unfocused.pixelsHigh)
            // 存在性那一格量的**不是整条 band**，而是"占位字该在的那一块"：
            // 左边 30% 宽、四周再内缩 3pt。**R80 对过账**：这一格里画着的墨**全是那串占位字**
            // （臂 D 把 `placeholderString` 撤成空，带墨面积从 268.7 / 330.1pt² 掉到 **0.0pt²**，
            //  亮 / 暗）—— 产品这颗框是 `isBordered=false` + `drawsBackground=false`，
            // 所以"描边混进来"与"图标混进来"那两条理由在**这个控件**上都不成立，
            // 内缩 3pt 与左 30% 是**防御性**形状（将来谁给它加了边框或图标，这两个数就真的有对象）。
            // 真正被读数用过的理由只有一条：② 占位字的实测包围盒是 x 12.5–98.5pt（band 宽 400pt）
            // ⇒ 左 30% 把它整个包住。本机这一格有墨像素 **1699 / 1871**（亮 / 暗，
            // 就是 `QUICKPICK_FOCUS` 行里 `占位区有墨(不聚焦,左30%内缩3pt)` 那一列；
            // 这条注释之前写的 1967 / 2208 是探针形状改掉之后的旧数，U-139 那一族）。
            let inset = 3.0 * CGFloat(scale)
            let inkProbe = CGRect(x: band.minX + inset, y: band.minY + inset,
                                  width: band.width * 0.3 - inset, height: band.height - 2 * inset)
            let inkUnfocused = Self.alphaInkPixels(unfocused, rect: inkProbe)
            let inkFocused = Self.alphaInkPixels(focused, rect: inkProbe)
            let inkWholePanel = Self.alphaInkPixels(unfocused, rect: wholePanel)
            // **R79：决定闸门的是宽度的存在性，不是计数。** R78 用"占位区里 ≥20 个有墨像素"，
            // 结果它在 runner 上没拦住（run 38757049151 仍是那四条红）——
            // **R80 把机制查清了**（臂 D：那一格里的墨全是那串占位字，图标与描边都不存在），
            // 所以 R79 注释里"那颗放大镜 AppKit 画得出它"那句作废（U-146）。真正的原因是：
            // **过地板的像素数分不开"画了开头两个字"与"画了整串字"** —— 前缀就够 20 个。
            // 计数与宽度的分别正在这里：
            //   开头那一片 ≈17pt；本机实测整串是 x 12.5–98.5pt = 86.5pt。
            // 地板取 40pt：两个数差五倍，不在刀尖上（R66 那条 `deadSpan=0.05` 同道理）。
            let spanUnfocused = Self.alphaInkSpan(unfocused, rect: band)
            let spanFocused = Self.alphaInkSpan(focused, rect: band)
            let spanWidthPt = spanUnfocused.max < 0 ? -1.0
                : Double(spanUnfocused.max - spanUnfocused.min + 1) / Double(scale)
            // 第二根证人：**只有占位字能待的那一块**（x 从带左起 50pt 之后、上下各内缩 2pt）。
            // 为什么宽度还不够：一圈 1px 的**描边**能把包围盒撑到整条 band 宽，
            // 而它进不了这一块 —— 上下被内缩排掉，左边被 50pt 排掉。
            // 两个条件取**合取**：图标一个人开不了门（宽度不够、这一块也是空的），
            // 描边也开不了门（这一块是空的），只有那串字在的时候两个都成立。
            let textOnlyRect = CGRect(x: band.minX + 50 * CGFloat(scale),
                                      y: band.minY + 2 * CGFloat(scale),
                                      width: band.width - 52 * CGFloat(scale),
                                      height: band.height - 4 * CGFloat(scale))
            let textOnlyInk = Self.alphaInkPixels(unfocused, rect: textOnlyRect)
            let placeholderDrawn = spanWidthPt >= Self.placeholderMinSpanPoints && textOnlyInk >= 20
            emit("QUICKPICK_FOCUS \(label) appActive=\(NSApp.isActive) 面板key=\(panel.isKeyWindow) "
                + "主=\(panel.isMainWindow) makeFirstResponder=\(accepted) "
                + "建出来时就聚焦=\(builtInEditor != nil) 聚焦时响应者是编辑器=\(focusedResponder is NSText) "
                + "撤焦点后还是=\(blankResponder is NSText) "
                + "focusRingType=\(field.focusRingType.rawValue) 缩放=\(scale)× 带=\(NSStringFromRect(band)) "
                + "框内变化像素=\(changedIn) 框外一圈变化像素=\(changedHalo - changedIn) "
                + "alpha 聚焦=\(String(format: "%.2f", alphaFocused)) "
                + "不聚焦=\(String(format: "%.2f", alphaUnfocused)) "
                + "差=\(String(format: "%.2f", alphaUnfocused - alphaFocused)) 亮度轴差=\(String(format: "%.2f", lumIn)) "
                + "占位区有墨(不聚焦,左30%内缩3pt)=\(inkUnfocused) 有墨(聚焦)=\(inkFocused) 整窗有墨=\(inkWholePanel) "
                + "文字独占区有墨(不聚焦,x≥50pt 内缩2pt)=\(textOnlyInk) "
                + "带内有墨包围盒(不聚焦)=\(spanUnfocused.min)…\(spanUnfocused.max)px "
                + "宽=\(String(format: "%.1f", spanWidthPt))pt(聚焦 \(spanFocused.min)…\(spanFocused.max)) "
                + "地板=\(String(format: "%.0f", Self.placeholderMinSpanPoints))pt "
                + "⇒ 存在性尺说\(placeholderDrawn ? "这一格画了东西，像素那两条有对象" : "这一格今天没画那串字，像素那两条没有对象")")
            XCTAssertGreaterThanOrEqual(changedIn, 0, "\(label)档：尺读不出两张帧 ⇒ 无从判定，不许当通过")
            // **闸门的判别力对照（R79，R80 更正了它的机制）**：这一格里没有放大镜、也没有描边
            // （臂 D 撤掉 `placeholderString` 之后带墨面积 = 0.0pt²），所以这里框住的是
            // **那串字的开头一小片**。R79 的注释把它说成"那颗放大镜 AppKit 画得出来"，
            // 那句话是**编的**（U-146），而它当时能过是因为"一小片字"和"一颗图标"在这把尺上读数一样。
            // 如果这一小片就能把宽度撑到地板以上，这道闸门等于没设 —— 而 R78 就是那样倒的
            // （它数的是像素个数，开头那一片一个人就过了）。所以这里单独量这一小片的包围盒，
            // 要求它**过不了**闸门。整串字画出来时这一格才有对象；没画出来时这一小片仍然有对象
            // （开头在不在与整串在不在是两件事），所以不设 `placeholderDrawn` 前提。
            let prefixRect = CGRect(x: (inContent.minX + 3) * CGFloat(scale),
                                    y: band.minY,
                                    width: 17 * CGFloat(scale), height: band.height)
            let prefixSpan = Self.alphaInkSpan(unfocused, rect: prefixRect)
            let prefixWidthPt = prefixSpan.max < 0 ? 0.0
                : Double(prefixSpan.max - prefixSpan.min + 1) / Double(scale)
            emit("QUICKPICK_FOCUS_GATE \(label) 开头那一小片宽=\(String(format: "%.1f", prefixWidthPt))pt "
                + "占位整条宽=\(String(format: "%.1f", spanWidthPt))pt 地板=\(String(format: "%.0f", Self.placeholderMinSpanPoints))pt "
                + "⇒ 闸门\(placeholderDrawn ? "开（那串字画全了）" : "关（只有开头那一小片）")")
            XCTAssertLessThan(prefixWidthPt, Self.placeholderMinSpanPoints,
                "\(label)档：只框住那串字的开头一小片，量出来的墨包围盒就有 \(String(format: "%.1f", prefixWidthPt))pt "
                    + "（地板 \(String(format: "%.0f", Self.placeholderMinSpanPoints))pt）⇒ 这道存在性闸门**分不开**"
                    + "'只有开头几个字'与'整串字'，它就恒开，像素那几条又回到没人看着的状态。"
                    + "换探针形状或换地板，别把断言删掉")
            // ① 焦点落进那颗框（行为，读的是产品对象，不是帧）。
            XCTAssertTrue(accepted,
                "\(label)档：`makeFirstResponder(field)` 都没接受 ⇒ 那颗框不是可聚焦的响应者，"
                    + "浮层打开时打字会落空（产品 `show()` 靠的就是这一步）")
            XCTAssertTrue(focusedResponder is NSText,
                "\(label)档：接受了焦点却没有把字段编辑器装成窗口的响应者 ⇒ 焦点在别处，"
                    + "那颗框收不到打字")
            // 正对照：两态必须不同。少了这一格，②③那几条像素断言可以靠"自己减自己"永远绿。
            XCTAssertFalse(blankResponder is NSText,
                "\(label)档：`makeFirstResponder(nil)` 之后窗口响应者**还是**字段编辑器 ⇒ 撤不掉焦点，"
                    + "于是下面那几条断言量的是同一张帧减自己（假绿的教科书形状，U-131）")
            // ④ 值守卫：不许关掉系统环。**R80 把这一条挪到像素那几条之前**：
            // R78 那道存在性闸门（还有本轮那两条 `_NOT_RUN` 出口）都 `continue`，
            // 而它的注释写着"行为那几条照判"—— 注释在替代码撒谎，那一族的账本号是 U-139。
            // 挪上来之后，任何一条缺席出口都仍然判得到这里。
            // **这个枚举的坑（R76 实测）**：raw 0 才是"系统自己决定"，而 Swift 里 `.none` 的 raw 是 **1**
            // （`.automatic` 这个成员在本 SDK 根本不存在，写 `== .automatic` 编译不过）。
            // 一个人按名字猜，就会把这条守卫写成"等于 .none"—— 那正好把"系统环被关掉"当成通过。
            let automatic = NSFocusRingType(rawValue: 0)
            XCTAssertEqual(field.focusRingType, automatic,
                "\(label)档：那颗框的 `focusRingType` 不再是 0（= 系统自己决定；读到 "
                    + "\(field.focusRingType.rawValue)，而 `.none` 的 raw 是 1）"
                    + " ⇒ 焦点环在这条通道里本来就读不到（③那条缺席），关掉它这件事**永远不会被任何一张帧发现**，"
                    + "所以这条值守卫是唯一防线")
            // **存在性闸门（R78）**：像素那两条只在"这一格真的画了东西"时判。
            // 处置按机器分开（R60 那一课）：2× 上没画 ⇒ **红**（那是捕获或产品坏了，必须有人去查），
            // 1× 上没画 ⇒ 点名 not-run（runner 不画 SwiftUI/AppKit 文本是已知通道性质，
            // 见 `PROBE_ELIGIBILITY … ink=0.0%` 那一批读数）。
            // 名字以 `_NOT_RUN` 结尾：`ci_capture_gate.py` 认这个后缀（R36/U-59）。
            if !placeholderDrawn {
                emit("QUICKPICK_FOCUS_NOT_RUN=1 \(label)：占位符那串字今天在这条通道里没画出来"
                    + "（带内有墨包围盒只有 \(String(format: "%.1f", spanWidthPt))pt，"
                    + "低于 \(String(format: "%.0f", Self.placeholderMinSpanPoints))pt 那道地板；"
                    + "计数却有 \(inkUnfocused) 个像素 ⇒ 那一格里画得出的只有开头一小片，不是整串字）⇒ "
                    + "\"聚焦与不聚焦两张帧相同（这次读到 \(changedIn) 个变化像素）这一句，不能推成『焦点没有视觉后果』，"
                    + "它说的是这条通道今天看不见那串字。行为那两条（①响应者、④没关系统环）与源码守卫照判。")
                XCTAssertLessThan(scale, 2,
                    "\(label)档：2× 的捕获通道上占位符那串字的包围盒只有 \(String(format: "%.1f", spanWidthPt))pt ⇒ "
                        + "本机这一格**必须**画得出来（R76 实测 1797 / 2354 个变化像素、包围盒 86.5pt）。"
                        + "红在这里的含义是『捕获或产品今天坏了』，不是『这台机器看不见』——"
                        + "只有 1× 才允许缺席（R60：机器前提不同 ⇒ 处置不同，但都不许静默）")
                continue
            }
            // ② 焦点必须有视觉后果，而**这条判据读的是"搬动了多少墨"（pt²），不是像素个数**（R80）。
            //
            // 换尺的理由是 R79 的 CI 读出来的，不是审美：runner 那一遍（run 38760347161）
            // 存在性闸门**开**（`QUICKPICK_FOCUS_GATE … 占位整条宽=87.0pt … 闸门开`），
            // 而 `框内变化像素=0`、alpha 3.55⇒3.50 —— 命中 BACKLOG 109 预登记的第二个分支：
            // "独占区非 0 而两态差仍是 0 ⇒ 那四条红是真的，要查的是产品/通道，不许再抬地板"。
            // 查出来的结论是：**那把尺本身跟着像素网格变**。`changedPixelCount` 数的是
            // "过 8/255 的像素个数"，本机 2× 同一条字给 1797 个、runner 1× 给 0 个，
            // 而这两个数之间的差别有 **3/4 是网格**（同样多的墨摊在 4 倍数量的像素上）。
            // 所以地板从"个数"换成"pt² 的墨"：它是同一串字在两台机器上**唯一共同的分母**。
            // 三条证人臂（R/D/C，见上面注释）读的是同一把尺，于是"看不见"必须分成两种：
            //   尺在这一格整体失明（证人臂也读不出东西）／ 尺看得见而聚焦不调淡（证人臂读得出）。
            // 两种都不许静默，也都**不许在 2× 上放行** —— 本机是判这条轴的那台机器。
            let noisePt2 = Self.movedInkPointsSquared(unfocused, againUnfocused, rect: band, scale: scale)
            let focusPt2 = Self.movedInkPointsSquared(unfocused, focused, rect: band, scale: scale)
            let armPlaceholderPt2 = Self.movedInkPointsSquared(unfocused, noPlaceholder,
                                                               rect: band, scale: scale)
            let armTextPt2 = Self.movedInkPointsSquared(unfocused, hasText, rect: band, scale: scale)
            let haloPt2 = Self.movedInkPointsSquared(unfocused, focused, rect: halo, scale: scale)
            let bandInkPt2 = Self.inkPointsSquared(unfocused, rect: band, scale: scale)
            let inkNoPlaceholderPt2 = Self.inkPointsSquared(noPlaceholder, rect: band, scale: scale)
            let dimFraction = bandInkPt2 > 0 ? focusPt2 / bandInkPt2 : -1
            let competencePt2 = max(armPlaceholderPt2, armTextPt2)
            // 地板的一半来自**这台机器自己的噪声**（臂 R）：同一态两张帧之差读出来多少，
            // 判据地板就不能低于它的 `focusNoiseMargin` 倍（R38：地板从表推导，不猜常数）。
            let focusFloorPt2 = Self.focusFloorPointsSquared(noisePt2: noisePt2)
            let ringPt2 = haloPt2 - focusPt2
            // 处置由**纯函数**给（`focusDisposition`）：那两支 1× 出口在本机永远走不到，
            // 没有单独的真值表它们就是"没有红钉着的分支"（`testFocusAxisDispositionIsATruthTable`）。
            let disposition = Self.focusDisposition(focusMovedPt2: focusPt2, floorPt2: focusFloorPt2,
                                                    dimFraction: dimFraction,
                                                    minDimFraction: Self.focusMinDimFraction,
                                                    competencePt2: competencePt2,
                                                    competenceFloorPt2: Self.competenceMinMovedPointsSquared)
            let focusJudged = disposition == .judged
            let channelSeesThatBand = disposition != .channelBlindOnThisMachine
            emit("QUICKPICK_FOCUS_INK \(label) 缩放=\(scale)× 带墨面积=\(String(format: "%.1f", bandInkPt2))pt² "
                + "焦点搬动=\(String(format: "%.1f", focusPt2))pt²(地板 \(String(format: "%.1f", focusFloorPt2))"
                + "=max(\(String(format: "%.0f", Self.focusMinMovedPointsSquared)), "
                + "\(String(format: "%.0f", Self.focusNoiseMargin))×噪声) 占比=\(String(format: "%.3f", dimFraction))"
                + "(地板 \(String(format: "%.2f", Self.focusMinDimFraction))) "
                + "噪声(同态重拍)=\(String(format: "%.1f", noisePt2))pt² "
                + "证人臂撤占位字=\(String(format: "%.1f", armPlaceholderPt2))pt² "
                + "证人臂打进字=\(String(format: "%.1f", armTextPt2))pt² "
                + "撤占位字之后带墨面积=\(String(format: "%.1f", inkNoPlaceholderPt2))pt² "
                + "框外那一圈=\(String(format: "%.1f", ringPt2))pt² "
                + "旧尺像素个数=\(changedIn)（R79 的 runner 那一遍这一列是 0） "
                + "⇒ \(focusJudged ? "焦点这一档看得见在让位" : (channelSeesThatBand ? "尺在这一格看得见别的东西在动，而聚焦不动" : "这一格对这把尺整体失明（证人臂也读不出）"))")
            // 证人臂自己也得有对象：撤掉 `placeholderString` 之后那一格的墨**必须少一半以上**。
            // 少了这一格，"臂读不出东西"这句话就可能是**臂没生效**（比如占位符由产品自己画、
            // 改属性撤不掉），而不是"通道看不见" —— 那两种成因的处置完全不同。
            let armDemptiesTheBand = bandInkPt2 <= 0 || inkNoPlaceholderPt2 <= bandInkPt2 * 0.5
            XCTAssertGreaterThanOrEqual(armPlaceholderPt2, 0,
                "\(label)档：证人臂 D 读不出两张帧 ⇒ 这条轴的证据链断了（不是产品红，是尺红）")
            XCTAssertTrue(armDemptiesTheBand,
                "\(label)档：把 `placeholderString` 撤成空，那一格的墨面积只从 "
                    + "\(String(format: "%.1f", bandInkPt2))pt² 变成 "
                    + "\(String(format: "%.1f", inkNoPlaceholderPt2))pt² ⇒ 臂 D 没生效："
                    + "这一格里的墨不是 AppKit 那串占位字（那就是 R79 的包围盒归因错了），"
                    + "要重查这一格里到底画了什么，不许直接引用证人臂的读数")
            if !focusJudged {
                emit("QUICKPICK_FOCUS_AXIS_NOT_RUN=1 \(label)：焦点那一档的墨移动在这一台机器上读到 "
                    + "\(String(format: "%.1f", focusPt2))pt²，地板 \(String(format: "%.1f", focusFloorPt2))pt²"
                    + "（缩放=\(scale)×，同态噪声 \(String(format: "%.1f", noisePt2))pt²）。"
                    + (channelSeesThatBand
                        ? "同一把尺在同一格里读得出别的成因：撤占位字搬动 \(String(format: "%.1f", armPlaceholderPt2))pt²、"
                          + "打进字 \(String(format: "%.1f", armTextPt2))pt² ⇒ **尺不瞎**，"
                          + "是这台机器的 AppKit 不为非 key 窗口调淡占位符（`面板key=\(panel.isKeyWindow) appActive=\(NSApp.isActive)`），"
                          + "这一条不能推成『焦点没有视觉后果』也不能推成『产品没有焦点反馈』"
                        : "两条证人臂也只读出 \(String(format: "%.1f", competencePt2))pt² ⇒ **这一格对这把尺整体失明**，"
                          + "焦点那一条根本没有对象，判不判都是空的")
                    + " 行为那几条（①响应者、④没关系统环）与源码守卫照判 —— 它们在这一格里不依赖像素。")
                // **2× 上这一句必须红**：本机是判这条轴的机器，它读不到就是捕获或产品坏了。
                XCTAssertLessThan(scale, 2,
                    "\(label)档：本机 2× 上焦点那一档只搬动 \(String(format: "%.1f", focusPt2))pt² "
                        + "（地板 \(String(format: "%.1f", focusFloorPt2))pt²、占比 "
                        + "\(String(format: "%.3f", dimFraction))），而同一格里撤掉占位字能读出 "
                        + "\(String(format: "%.1f", armPlaceholderPt2))pt² ⇒ "
                        + "'聚焦不调淡占位符'这件事在**判这条轴的那台机器**上成立了，必须有人去查："
                        + "要么产品/AppKit 变了（那焦点就只剩光标），要么捕获通道变了（那 124 张帧一起要重看）")
                if scale < 2 { continue }
            }
            XCTAssertGreaterThanOrEqual(focusPt2, focusFloorPt2,
                "\(label)档：聚焦与不聚焦两张帧之间只搬动了 \(String(format: "%.1f", focusPt2))pt² 的墨，"
                    + "地板 \(String(format: "%.1f", focusFloorPt2))pt² ⇒ 焦点这一档变成看不见了。"
                    + "今天它是那一串占位字退后（本机实测 98.7 / 113.3pt²、"
                    + "旧那把像素个数尺 1797 / 2354 个）；两种成因都值得查：占位符被换成实色（那就该重判音量），"
                    + "或者 AppKit 不再为聚焦的框调淡占位符（那焦点就只剩光标了）")
            XCTAssertGreaterThanOrEqual(dimFraction, Self.focusMinDimFraction,
                "\(label)档：焦点搬动的墨只占那一格里现有墨的 \(String(format: "%.3f", dimFraction))"
                    + "（地板 \(String(format: "%.2f", Self.focusMinDimFraction))）⇒ 占比这一根轴管的是"
                    + "'这一格的墨有没有明显少掉'，它与绝对量各自拦一种错：整格墨变少而聚焦仍然调淡同一比例，"
                    + "绝对量会掉到地板以下但占比不会；墨面积涨了而绝对量够，占比会掉下来")
            XCTAssertLessThanOrEqual(alphaFocused, alphaUnfocused,
                "\(label)档：聚焦之后那一格的 alpha 反而不比不聚焦时低（聚焦=\(String(format: "%.2f", alphaFocused)) "
                    + "不聚焦=\(String(format: "%.2f", alphaUnfocused))）⇒ 焦点反馈的**方向**变了："
                    + "今天是'占位符退后给光标让位'，'聚焦把那一格叫得更响'是另一种设计，该重判。"
                    + "R80 把原来那条『绝对掉 2.0』的地板拆到这里：那个数跟着墨的绝对水平走，"
                    + "本机带均值 10.71 而 runner 3.55 ⇒ 同一道地板在两台机器上不是一个难度")
            // ③ 后果必须留在框内：这一格是量过之后决定**不加**自定义焦点环的。
            XCTAssertLessThanOrEqual(ringPt2, focusFloorPt2,
                "\(label)档：框外那一圈搬动了 \(String(format: "%.1f", ringPt2))pt² 的墨（地板 "
                    + "\(String(format: "%.1f", focusFloorPt2))pt²）⇒ 焦点开始往框外画东西了"
                    + "（多半是自定义环/描边，或系统环真的开始画）。这一格是 R76 量过才决定不加的："
                    + "红在这里的含义是'该重判'，不是'把那段绘制删掉'。"
                    + "旧的像素个数那一列（框外 \(changedHalo - changedIn) 个）仍然发在 QUICKPICK_FOCUS 行里，"
                    + "但它不再做判断：那一圈只有 8pt 宽，1× 上一条描边就几个像素，判不了")
            emit("QUICKPICK_FOCUS_RING_NOT_RUN=1 \(label)：焦点环这一档在这条通道里读不到"
                + "（框外那一圈 \(String(format: "%.1f", ringPt2))pt²，而 `面板key=\(panel.isKeyWindow) "
                + "appActive=\(NSApp.isActive)`）"
                + "⇒ 真机上有没有系统环只能你看（人工批次 68.1），不许把这条缺席写成'产品没有焦点环'")
        }
        // 产品入口那条赋值必须还在（①②③全都不会红的那一族回归，只有这条守卫抓得到）。
        let source = Self.codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        let body = Self.functionBody(named: "func show()", in: source)
        XCTAssertFalse(body.isEmpty,
                       "扫不到 `show()` 的函数体 ⇒ 下面两条守卫是空转的（正对照）")
        XCTAssertTrue(body.contains("makeKeyAndOrderFront"),
                      "`show()` 不再把面板变成 key ⇒ 焦点环与打字都可能落空，"
                          + "而①②③三条读的是夹具那条路径，看不见这件事")
        XCTAssertTrue(body.contains("makeFirstResponder(field)"),
                      "`show()` 不再把焦点交给那颗框 ⇒ 浮层打开后要先点一下才能打字。"
                          + "这一族在帧里、在①②里都没有影子（夹具故意不抢前台），只有这条守卫抓得到")
        XCTAssertTrue(Self.functionBody(named: "func definitelyNotInThisFile()", in: source).isEmpty,
                      "不存在的函数名也扫得出东西 ⇒ 截取器'永远看得见'，上面两条一起退化成噪声计数器")
    }


    /// R71 / BACKLOG 99：浮层那一行的字号，与"同一条记录的标题"在别处的字号，必须是同一档。
    ///
    /// 这条从**产品入口**进（DoD 第 1 条）：建出真的浮层面板，读真的 `NSTextField.font`，
    /// 而不是读源码里的一个数。三处断言各自拦一种错：
    ///   · 行标签 == `VisualFont.row` ⇒ 拦"浮层自己再定一档"（改之前它是就地写的 13，
    ///     而侧栏 / 行视图 / 搜索建议那五处全是 12 ⇒ 同一个对象在两处响一档）；
    ///   · 搜索框 == `VisualFont.body` ⇒ 拦"浮层比主窗口那颗搜索框更响"（原来是就地写的 14，
    ///     主窗口是 13 —— 浮层的职责是"快"，不是"大"）；
    ///   · 五行必须**同档** ⇒ 拦"某一行的字号被别处覆盖掉"（那种错在帧上几乎看不出来，
    ///     因为差只有 1pt；但它是"两处各写一个数"的下一步）。
    ///
    /// 为什么这里**不**去帧上量墨高来跨表面对齐：同一把尺量到的行距是
    /// 浮层 33–35pt（单行）vs 侧栏 38–47pt（双行），两者不可比；
    /// 而墨高跟着字形内容走（有没有 `g/y/9` 差一截），拿它当判据就是拿噪声当契约。
    /// 跨表面的同一性由**令牌**保证，这一条就是保证它真的到了产品对象上。
    func testQuickPickTypographyComesFromTheLadder() throws {
        _ = NSApplication.shared
        let store = makePopulatedStore()
        let build = QuickPickCapturePanel.builder(store: store, query: "", hoveredRow: nil)
        guard let panel = build(), let content = panel.contentView else {
            throw XCTSkip("捕获入口建不出浮层窗口 ⇒ 这一档今天无从判定（不是产品没做）")
        }
        panel.setFrameOrigin(NSPoint(x: -20007, y: -20007))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        defer { panel.orderOut(nil) }
        guard let table = Self.productTable(in: content) else {
            return XCTFail("帧根里找不到那颗产品表格 ⇒ 这条判据没有对象")
        }
        var labelSizes: [CGFloat] = []
        for row in 0..<table.numberOfRows {
            guard let cell = table.view(atColumn: 0, row: row, makeIfNecessary: true) else { continue }
            if let field = (cell as? NSTableCellView)?.textField ?? Self.firstTextField(in: cell) {
                labelSizes.append(field.font?.pointSize ?? -1)
            }
        }
        let fieldSizes = Set(labelSizes)
        let searchSize = (Self.firstView(ofType: QuickPickSearchField.self, in: content))?.font?.pointSize ?? -1
        let sizesAsInts = labelSizes.map { Int($0.rounded()) }
        emit("QUICKPICK_TYPE 行数=\(labelSizes.count) 行标签字号=\(sizesAsInts) "
            + "期望=\(Int(VisualFont.row)) 搜索框字号=\(Int(searchSize.rounded())) 期望=\(Int(VisualFont.body))")
        XCTAssertGreaterThanOrEqual(labelSizes.count, 3,
                                    "只读到 \(labelSizes.count) 个行标签 ⇒ 这条判据没有对象（表格没建出来？）")
        XCTAssertEqual(fieldSizes, [CGFloat(VisualFont.row)],
                       "浮层行标签的字号不再是 `VisualFont.row`(\(Int(VisualFont.row))) —— 读到 \(labelSizes)。"
                           + "同一条记录的标题在侧栏 / 行视图 / 搜索建议那五处都是这一档，"
                           + "浮层是第六处，它没有理由自己响一档（BACKLOG 99）")
        XCTAssertEqual(searchSize, CGFloat(VisualFont.body),
                       "浮层搜索框是 \(Int(searchSize))pt，而主窗口那颗搜索框是 `VisualFont.body`(\(Int(VisualFont.body)))pt "
                           + "⇒ 同一个控件在两个表面响一档。浮层的职责是快，不是大")
    }

    /// 视图树里第一个 `NSTextField`（深度优先）。
    private static func firstTextField(in root: NSView) -> NSTextField? {
        firstView(ofType: NSTextField.self, in: root)
    }

    /// 视图树里第一个指定类型的视图（深度优先）。
    /// 用类型而不是"位置"来找搜索框：`content.subviews` 的顺序由 AppKit 决定，
    /// 拿顺序当身份，下一次布局改动就会把判据指向别的东西（R53 那一族"守卫命中守卫自己"的近亲）。
    private static func firstView<T: NSView>(ofType type: T.Type, in root: NSView) -> T? {
        for sub in root.subviews {
            if let match = sub as? T { return match }
            if let found = firstView(ofType: type, in: sub) { return found }
        }
        return nil
    }

    /// 空结果那一句的**两条**契约（R63）：它得真的在画（不是停在淡入的起点），
    /// 以及它得落在列表那一格（紧跟搜索框），不许掉在面板最底下。
    ///
    /// 为什么要分开两条：
    /// · `alphaValue` —— `applyEmptyState` 走 `animator()`，而非图层的 view 上这条**不提交模型值**
    ///   （spike 四臂：无图层两臂设完读到 0.000、转 2.1s 仍是 0.000 且完成回调从不跑；
    ///   图层化那一臂立刻读到 1.000）。也就是说"用户看不看得见这句话"被压在"动画跑没跑完"上。
    ///   这条断言不许它再回到那种形状。淡入本身仍然是"源码已接、产物未量"（账本 D-055）。
    /// · 位置 —— 这一条由**看帧**得出：R7 当年把句子放在表格下面，理由是实现便利；
    ///   第一次把这个浮层拍出来看到的是搜索框下面 227pt 空白、句子在面板最底下。
    ///   坐标约定实测过（AppKit y 向上：搜索框在 y 大的一侧），所以判据写的是
    ///   "句子顶边到搜索框底边的间隙 ≤ 24pt"，而不是"句子在 y=??"。
    func testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot() throws {
        let store = makePopulatedStore()
        let build = QuickPickCapturePanel.builder(store: store, query: "zzz 不存在")
        guard let panel = build(), let content = panel.contentView else {
            return XCTFail("捕获入口建不出浮层窗口 ⇒ 这条判据失去了对象，必须红")
        }
        _ = NSApplication.shared
        defer { panel.orderOut(nil) }
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        Self.tileScrollViews(in: content)
        panel.display()
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))

        var field: NSTextField?
        var sentence: NSTextField?
        func find(_ view: NSView) {
            if let tf = view as? NSTextField {
                if tf is QuickPickSearchField { field = tf }
                else if !tf.stringValue.isEmpty { sentence = tf }
            }
            view.subviews.forEach(find)
        }
        find(content)
        guard let sentence else {
            return XCTFail("浮层里没有「没有匹配…」那句话 ⇒ 空结果态什么都没有说（审计 B-P2 那一族回归）")
        }
        XCTAssertFalse(sentence.isHidden, "那句话被藏起来了 ⇒ 空结果时浮层是一片空白")
        XCTAssertEqual(sentence.alphaValue, 1, accuracy: 0.001,
                       "那句话的模型值是 \(sentence.alphaValue) ⇒ 它的可见性被压在「淡入动画跑完」上。"
                       + "实测：非图层的 view 上 `animator().alphaValue` 不提交模型值（spike 臂1/臂2 停在 0.000），"
                       + "所以这条路径在没有真实显示周期的地方就是「字在、看不见」。淡入是装饰，看得见才是契约")
        guard let field else { return XCTFail("找不到搜索框 ⇒ 「紧跟搜索框」这一条没有对象") }
        // 两个 frame 都换算到**同一个**祖先（content）再比 —— 不假设嵌套层数，
        // 也不拿 stack 局部坐标和 window 坐标相减（那种数看着像读数，其实是错的）。
        guard let fieldRect = Self.frame(field, in: content),
              let sentenceRect = Self.frame(sentence, in: content) else {
            return XCTFail("换算不到同一坐标系 ⇒ 「句子紧跟搜索框」这条判据没有对象")
        }
        // AppKit 的 y 向上：搜索框在**上面**，所以它的 `minY` 就是它的底边。
        let gap = fieldRect.minY - sentenceRect.maxY
        emit("QUICKPICK_EMPTY_SENTENCE fieldBottom=\(String(format: "%.1f", fieldRect.minY)) "
              + "sentenceTop=\(String(format: "%.1f", sentenceRect.maxY)) gap=\(String(format: "%.1f", gap))")
        XCTAssertLessThanOrEqual(gap, 24,
                                "那句话与搜索框之间空了 \(Int(gap))pt ⇒ 它又掉回面板最底下了。"
                                + "用户刚打完字，眼睛就在列表区那一行；解释必须落在那一格（R63 挪的位置）")
        XCTAssertGreaterThan(gap, -4,
                             "那句话压到搜索框上面去了（gap=\(Int(gap))）⇒ 两行叠在一起，读不成一句")
        // 第三条：**横向居中**。它自己写着 `alignment = .center`，但那句"居中"只在它自己的框里成立 ——
        // 框不居中，字就不居中。这一条是变异 M332 替我审出来的：第一版判据只量竖向的"紧跟搜索框"，
        // 于是"撤掉那句话的等宽约束"这一刀**绿着回来**（它退回字宽，位置那条完全没感觉）。
        let sentenceMidX = sentenceRect.midX
        let panelMidX = content.bounds.midX
        XCTAssertLessThan(abs(sentenceMidX - panelMidX), 3,
                          "那句话的中心在 x=\(String(format: "%.1f", sentenceMidX))，面板中心在 "
                          + "\(String(format: "%.1f", panelMidX)) ⇒ 差 \(String(format: "%.1f", abs(sentenceMidX - panelMidX)))pt。"
                          + "它的框不再等宽于面板时，`alignment = .center` 只是在一条偏掉的带子里居中")

        // 第二档：**长查询词**。上面那条短查询的句子比面板窄，所以"框被撑到面板外"这件事
        // 它看不见 —— 而 `lineBreakMode = .byTruncatingTail` 只在自己的框里截，
        // 框一旦比面板宽，两端就被面板硬切，省略号根本没机会出现。
        // 这一档是"那句话的等宽约束到底有没有作者"的答案：M332 单独撤它时判据全绿
        // （短查询下默认对齐也居中），只有这一档能把它判红。
        let longQuery = String(repeating: "很长的搜索词", count: 8)
        let longBuild = QuickPickCapturePanel.builder(store: makePopulatedStore(), query: longQuery)
        guard let longPanel = longBuild(), let longContent = longPanel.contentView else {
            return XCTFail("长查询词那一档建不出浮层 ⇒ 这条判据没有对象")
        }
        defer { longPanel.orderOut(nil) }
        longPanel.setFrameOrigin(NSPoint(x: -20006, y: -20006))
        longPanel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        Self.tileScrollViews(in: longContent)
        longPanel.display()
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        var longSentence: NSTextField?
        func findLong(_ view: NSView) {
            if let tf = view as? NSTextField, !(tf is QuickPickSearchField), !tf.stringValue.isEmpty {
                longSentence = tf
            }
            view.subviews.forEach(findLong)
        }
        findLong(longContent)
        guard let longLabel = longSentence else {
            return XCTFail("长查询词那一档没找到那句话 ⇒ 空结果态在长查询下根本没说话")
        }
        guard let longRect = Self.frame(longLabel, in: longContent) else {
            return XCTFail("长查询那一档换算不到 content 坐标系 ⇒ 判据没有对象")
        }
        emit("QUICKPICK_LONG_QUERY 句子 frame=\(NSStringFromRect(longRect)) "
              + "面板=\(NSStringFromRect(longContent.bounds)) 文本长度=\(longLabel.stringValue.count)")
        // **面板不许因为内容变宽**。这一条不是"防回归"，它防的是本轮自己改出来的东西：
        // 把 stack 钉到面板上之后，"内容要多宽"第一次传到了窗口 ——
        // 修之前实测面板被顶到 899pt（`contentResizeIncrements` 救不了，那是 Auto Layout 在推 frame）。
        // 判据写成"两个状态的面板同宽"而不是"面板等于 420"：面板尺寸是产品定的，
        // 而"它不随查询词长度变化"才是这条判据真正守的约定。
        XCTAssertEqual(longContent.bounds.width, content.bounds.width, accuracy: 0.5,
                       "长查询词把浮层面板从 \(Int(content.bounds.width))pt 顶到了 "
                       + "\(Int(longContent.bounds.width))pt ⇒ 这个浮层的设计前提是「固定尺寸、呼出即输入」，"
                       + "而句子的长度是用户决定的。谁在决定面板宽度，这里就露出来了")
        XCTAssertGreaterThanOrEqual(longRect.minX, longContent.bounds.minX,
                                    "那句话的左边伸出面板 \(Int(longContent.bounds.minX - longRect.minX))pt ⇒ "
                                    + "它被面板硬切而不是被省略号截断。它的等宽约束是这一条的承重墙")
        XCTAssertLessThanOrEqual(longRect.maxX, longContent.bounds.maxX,
                                 "那句话的右边伸出面板 \(Int(longRect.maxX - longContent.bounds.maxX))pt ⇒ "
                                 + "同一族：用户读到的是被切掉一半的字，而不是「换个词或按 Esc 清空」")
        XCTAssertLessThan(abs(longRect.midX - longContent.bounds.midX), 3,
                          "长查询下那句话的中心偏了 \(String(format: "%.1f", abs(longRect.midX - longContent.bounds.midX)))pt")
        // 截断必须**真的发生**：不截断而只是"面板变宽"的话，上面四条可以一起绿。
        // 这里不用 `NSCell.truncatedStr`（那是方法不是属性，且要自己算 textRange）——
        // "实际宽度 < 固有宽度"就是"它被压过"的充分证据，而 `.byTruncatingTail` 只在被压时出省略号。
        XCTAssertTrue(longRect.width < longLabel.intrinsicContentSize.width,
                      "句子实际宽 \(Int(longRect.width))pt，而它的固有宽度是 "
                      + "\(Int(longLabel.intrinsicContentSize.width))pt ⇒ 它没有被压过。"
                      + "那说明这一档要么在靠面板变宽让位（上面那条同宽判据该红），"
                      + "要么根本没截出省略号 —— 两种都等于这一档什么都没判")
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

        // **这台机器能判哪几条**（R36 / BACKLOG 49 / U-59）。存在的理由不是宽容，是**换个问法**：
        // runner 上有 4 条红被 report-only 那一步吞掉了（一条正对照读 0%、两条"捕获失效"、
        // 一条"材质黑带消失了"），没有一条是产品 —— 可"红了没人看"和"没有红"在报表里长得一样，
        // 于是那一步既拦不住真缺陷，也记不下"今天到底判了多少"。
        // 现在：这台机器判不了的**那一条**登记成 `*_NOT_RUN`（带读数、带原因），
        // 其余任何一条红都必须是新的、有名字的 ⇒ 工作流那一步从此可以带闸门
        // （`python3 scripts/ci_capture_gate.py`，它的正对照就是下面那 4 行逐字日志）。
        // —— 三条前提，各自只看它要判的那个量 ——
        // 这一块的上一版写的是"settings 族画不画得出来 / List 族画不画得出来"两句话。
        // 听起来干净，实际是**一把尺管三件事**：它同时决定"95% 未绘制"要不要放行、
        // 正对照要不要跑、黑带名单要不要比 —— 而 runner 的逐帧实测（run 38473962277，
        // 片段已钉进 `scripts/tests/fixtures/r36_runner_capture.log`）说这三件事方向各不相同：
        //   · settings 族：本机未绘制 20.8–78.8%，runner 90.6–95.9% ⇒ 这一族在 CI 上**整体空白**；
        //   · sidebar / content 族：两台机器都画得出来（未绘制 0.0%），可 runner 上**一张黑带都没有**
        //     （本机 9 张），而且 sidebar 亮色版底行墨 0.0%、同一帧暗色版 100.0%；
        //   · 底行墨这把尺本身在两台机器上都是活的（detail 族两边都读到 100.0%）。
        // 于是"某一族画不出来"这句话既放过过不该放的，也红过不该红的。
        // 现在三条前提各自独立、全部是**在这台机器上量出来的**，没有一条靠"这是 CI"这种身份判断。
        let readings = report.map { item in
            CaptureCapability.Reading(
                family: Self.fixtureName(fromFile: item.name).components(separatedBy: "-").first ?? "",
                transparent: item.metrics.transparent,
                blackBandPt: item.metrics.blackBandPt,
                bottomInkFraction: item.metrics.bottomInkFraction)
        }
        let capability = CaptureCapability.measure(readings)
        let settingsFamilyIsBlank = capability.settingsFamilyIsBlank
        let settingsLowestBlank = capability.settingsLowestBlank
        let bandsSeenHere = capability.bandsSeenHere
        emit("CAPTURE_CAPABILITY settings族整体空白=\(settingsFamilyIsBlank ? "是" : "否")"
              + "（族内最低未绘制 " + String(format: "%.1f", settingsLowestBlank * 100) + "% / "
              + "\(readings.filter { $0.family == "settings" }.count) 张）"
              + " / 这一台见过黑带=\(bandsSeenHere ? "是" : "否")")

        emit("CAPTURED \(report.count) -> \(directory.path)")
        for item in report {
            emit("  \(item.name)  transparent=\(String(format: "%.1f", item.metrics.transparent * 100))%"
                  + "  blackBandPt=\(String(format: "%.0f", item.metrics.blackBandPt))"
                  + "  bottomInk=\(String(format: "%.1f", item.metrics.bottomInkFraction * 100))%")
        }

        // **夹具不许裁自己的内容**（R22 / BACKLOG 32）。名单见 `Fixture.contentMustFit`。
        // 这条是 M76 那支"知道会漏还故意放"的变异终于被抓回去的一次：
        // 以前把 `weights` 的框改小回去**不会有任何测试红**，
        // 于是"帧里少了三行"这件事在账本里躺了九轮。
        //
        // R37 换了参照点之后这条才**真的**在判裁切（以前它判的是色差，见 `bottomInkFraction`）。
        // 读数含义也要说清：底行"有墨"= 那一行有像素不是底色，**被裁的字与压在边上的深色材质
        // 都算**（`content-min` 读 43.4% 就是选中行那块黑药丸贴到了帧底）。所以这条只用于
        // **不该被裁的组件帧**（mustFit 那十张），滚动区帧（settings / content / sidebar）不在其列。
        for item in report where mustFitNames.contains(Self.fixtureName(fromFile: item.name)) {
            XCTAssertLessThan(item.metrics.bottomInkFraction, InkFloor.fixtureBottomInkMaxFraction,
                              "\\(item.name) 的最底一行有 \(String(format: "%.1f", item.metrics.bottomInkFraction * 100))% 的墨"
                              + " ⇒ 这张夹具正在裁自己的内容（被裁的元素一定压在底边上）。"
                              + "把 `Fixture` 的高度抬到放得下，而不是把这条断言关掉 —— "
                              + "被裁掉的那部分从来没有进过帧基线，也就从来没有被审过")
        }
        let judgedFit = mustFitNames.count
        emit("CONTENT_FIT \(judgedFit) fixtures 判了底行墨（\(mustFitNames.sorted().joined(separator: ","))）")

        // **正对照**（R37 / U-60）：一把只在"该红的时候没红"上被检验的尺，等于没被检验。
        // 上面那十张读到的都是 0.0%，所以必须有**一张已知会被裁**的帧读得到墨，
        // 否则"把阈值调到 100000"这种把尺弄瞎的改动不会有任何测试红。
        //
        // 以前这条点名的对照物是 `sidebar-history` —— R36 查出它读到的 100% 是**色差**不是墨
        // （参照点是左上角那一个像素），也就是说这条判据十四年来没有过有效的正对照。
        // 现在换成 `row-clipped-control`：同一颗 `HistoryRowButton`、外框压到 58pt 再 `.clipped()`，
        // 帧上看得见第二行日期被切成半截。本机实测 **10.8%（亮）/ 12.5%（暗）**。
        //
        // 这条**不做成机器前提**（R36 那一版做了）：前提会把"这台机器上一个像素都读不到"
        // 说成"机器不行"，而那恰恰是判据最该红的一次。
        let canaries = report.filter { Self.fixtureName(fromFile: $0.name) == Self.bottomEdgeInkCanary }
        XCTAssertFalse(canaries.isEmpty,
                       "正对照帧 \(Self.bottomEdgeInkCanary) 没被拍到 ⇒ 这把尺今天没被检验")
        for item in canaries {
            XCTAssertGreaterThan(item.metrics.bottomInkFraction, InkFloor.bottomEdgeControlMinFraction,
                                 "正对照帧 \(item.name) 的底行只读到 "
                                 + String(format: "%.1f", item.metrics.bottomInkFraction * 100) + "% 的墨"
                                 + "（线 " + String(format: "%.0f", InkFloor.bottomEdgeControlMinFraction * 100) + "%）"
                                 + " ⇒ 这把尺**瞎了**：它量不到那张**已知被裁**的帧压在底边上的半截字，"
                                 + "上面那 \(judgedFit) 条'没被裁'的绿也就没有意义。"
                                 + "两种可能都要查：尺的参照点又被挪走了，或者那张对照帧不再被裁了"
                                 + "（后者意味着 `clippedRowFrame` 失效，判据同样失去正对照）")
        }
        emit("CONTENT_FIT_CANARY " + canaries.map { "\($0.name)=\(String(format: "%.1f", $0.metrics.bottomInkFraction * 100))%" }
            .joined(separator: " ")
            + "（线 " + String(format: "%.0f", InkFloor.bottomEdgeControlMinFraction * 100) + "%，"
            + "mustFit 那批的上限是 " + String(format: "%.0f", InkFloor.fixtureBottomInkMaxFraction * 100) + "%）")
        // **第二把锁：这把尺读的是产物，不是 raw rep**（R37 立的锁，R38 换成恒等式）。
        //
        // R37 那一版写的是"`content-min` 的底行至少读到 20%"，本机 43.4% 通过，
        // 而 runner 上同一帧读到 **9.3%** ⇒ 红（run 38485603211，被闸门指名）。
        // 那是**用一台机器的读数当另一台机器的地板** —— 正是这一族判据反复栽的那个形状，
        // 而且这次是 R36 刚说完"别这么写"之后我自己写的。
        //
        // 换成恒等式：**判据用的读数 == 从写盘那个文件重算出来的读数**。
        // 它在任何机器上都成立（两边同一台机器算），而谁把来源换回 raw rep，
        // 两边就会差出 13 倍（本机 3.4% vs 43.4%）⇒ 锁照样咬得住，且不再依赖帧长什么样。
        var identityChecked = 0
        var identityDiffering: [String] = []
        for item in report {
            let url = directory.appendingPathComponent(item.name)
            guard let bytes = try? Data(contentsOf: url),
                  let disk = NSBitmapImageRep(data: bytes), let dbase = disk.bitmapData else {
                XCTFail("\(item.name) 读不回字节 ⇒ 这条恒等式没被真的检验（帧没落盘？）")
                continue
            }
            let fromDisk = Self.bottomInkFraction(bytes: dbase, width: disk.pixelsWide,
                                                  height: disk.pixelsHigh, bytesPerRow: disk.bytesPerRow)
            XCTAssertEqual(fromDisk, item.metrics.bottomInkFraction, accuracy: 0.0001,
                           "\(item.name)：判据用的读数 "
                           + String(format: "%.1f", item.metrics.bottomInkFraction * 100)
                           + "% ≠ 从落盘文件重算的 " + String(format: "%.1f", fromDisk * 100)
                           + "% ⇒ 尺读的不是产物（raw rep 里\"没画\"的像素是透明的，会抢走底行中位数）")
            identityChecked += 1
            if abs(fromDisk - item.metrics.bottomInkFraction) > 0.001 { identityDiffering.append(item.name) }
        }
        XCTAssertGreaterThanOrEqual(identityChecked, 100,
                                    "恒等式只对了 \(identityChecked) 张帧 ⇒ 遍历坏了，这条锁等于没上")
        emit("BOTTOM_INK_IDENTITY \(identityChecked) 张帧：判据读数 == 从 PNG 重算的那一份")

        // 新知识（R37 才有）：哪些帧的底行**真的**压着东西。以前这条清单是假的（色差）。
        let edgeCarriers = report.filter { $0.metrics.bottomInkFraction >= InkFloor.fixtureBottomInkMaxFraction }
        emit("BOTTOM_EDGE_INK \(edgeCarriers.count) 张帧的底行读到 ≥"
              + String(format: "%.0f", InkFloor.fixtureBottomInkMaxFraction * 100) + "% 非底色像素："
              + edgeCarriers.map { "\(Self.fixtureName(fromFile: $0.name))=\(String(format: "%.1f", $0.metrics.bottomInkFraction * 100))%" }
                .sorted().joined(separator: " "))


        var exemptedSparse = Set<String>()
        for item in report where item.metrics.transparent > 0.95 {
            let name = Self.fixtureName(fromFile: item.name)
            let family = name.components(separatedBy: "-").first ?? ""
            let knownIncapable = (family == "settings" && settingsFamilyIsBlank)
            if knownIncapable {
                emit("CAPTURE_NOT_RUN \(item.name) \(Int(item.metrics.transparent * 100))% 未绘制"
                      + "，而 settings 族在这台机器上**每一张**都超过 "
                      + String(format: "%.0f", InkFloor.captureFamilyBlankFraction * 100) + "%（族内最低 "
                      + String(format: "%.1f", settingsLowestBlank * 100) + "%）⇒ 记为未运行")
                continue
            }
            if Self.sparseByDesignFixtures.contains(name) {
                // 稀可以，全空不行：这条正对照是这份豁免的承重部分（见名单注释）。
                let drawn = 1 - item.metrics.transparent
                XCTAssertGreaterThan(drawn, Self.sparseByDesignInkFloor,
                                     "\(item.name) 在「天生就稀」的名单里，但它一张都没画出来"
                                     + "（drawn=\(String(format: "%.2f", drawn * 100))%，门槛 "
                                     + "\(String(format: "%.1f", Self.sparseByDesignInkFloor * 100))% 来自本机实测的 "
                                     + "empty 2.1% / runner 5.1%，而\"捕获真的坏了\"是 0.0%）⇒ 这不是稀，这是捕获坏了")
                exemptedSparse.insert(name)
            }
            if item.metrics.transparent > 0.95, !Self.sparseByDesignFixtures.contains(name) {
                XCTFail("\(item.name) 有 \(Int(item.metrics.transparent * 100))% 像素未被绘制，"
                        + "判定为捕获失效，不能作为视觉验收证据"
                        + "（这一族的其他帧画得出来 ⇒ 不是机器不行，是这一张不行）")
            }
        }

        // 名单不许攒着 —— 但**判"攒着"的尺必须两台机器都成立**（R38 那条：一台机器的读数
        // 不能当另一台机器的地板）。R63 第一次上 runner 就是被这条自己写的新守卫判红的：
        // `quickpick-empty` 本机未绘制 97.9%、runner 94.9%，而门槛是 95.0% ⇒
        // 同一张帧在一台机器上"需要豁免"、在另一台上"不需要"，
        // 于是"它这次没走豁免分支 ⇒ 名单过期"这句话在 runner 上是**假红**。
        // 换成**同一次运行内的兄弟比较**：空结果态必须明显比 5 行的列表态更空。
        // 这条与 backing scale、与字体渲染的粗细都无关，只与"这一格里有没有内容"有关。
        // 同名帧亮暗各一张 ⇒ 先按夹具名归并，**取更空的那一张**（保守方向：宁可漏判过期，不可假红）。
        // （`Dictionary(uniqueKeysWithValues:)` 在这里会当场 crash —— "Duplicate values for key"，
        // 本机第一遍就是这么死的。归并必须显式写，不能假装一个名字只有一张帧。）
        var drawnByName: [String: Double] = [:]
        for item in report {
            let name = Self.fixtureName(fromFile: item.name)
            let drawn = 1 - item.metrics.transparent
            if let existing = drawnByName[name] {
                drawnByName[name] = min(existing, drawn)
            } else {
                drawnByName[name] = drawn
            }
        }
        let sparseControl = ["quickpick-empty": "quickpick-list"]
        for (entry, control) in sparseControl where Self.sparseByDesignFixtures.contains(entry) {
            guard let entryDrawn = drawnByName[entry], let controlDrawn = drawnByName[control] else {
                emit("SPARSE_EXEMPTION_NOT_RUN \(entry)/\(control) 这台机器没拍出这两张帧 ⇒ 不判")
                continue
            }
            XCTAssertLessThan(entryDrawn, controlDrawn - 0.03,
                              "「天生就稀」的 \(entry) 这次只比 \(control) 少画 \(String(format: "%.1f", (controlDrawn - entryDrawn) * 100))%"
                              + "（\(String(format: "%.1f", entryDrawn * 100))% vs \(String(format: "%.1f", controlDrawn * 100))%）⇒ "
                              + "那一格大概已经有内容了，把 \(entry) 从 `sparseByDesignFixtures` 拿掉，并肉眼审一遍新帧。"
                              + "注意这里**不写未绘制的绝对门槛**：本机 97.9% / runner 94.9% 差 3pt，"
                              + "任何绝对数都会在某台机器上变成假红或免检牌（R38）")
            emit("SPARSE_EXEMPTION_OK \(entry) drawn=\(String(format: "%.1f", entryDrawn * 100))%"
                  + " < \(control) drawn=\(String(format: "%.1f", controlDrawn * 100))% - 3pt")
        }
        emit("SPARSE_EXEMPTION 本次真正走了豁免分支的帧 \(exemptedSparse.sorted())，名单共 \(Self.sparseByDesignFixtures.count) 条"
              + "（走不走由这台机器的未绘制比例决定，**判过期不由它决定**）")

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
        if bandsSeenHere {
            XCTAssert(gone.isEmpty,
                      "这些帧的黑带消失了：\(gone.sorted()) ⇒ 那一处现在能拍了，"
                      + "把 `materialBlindSpotFixtures` 缩掉，并且肉眼审一遍新帧（别只改名单）")
        } else {
            // runner 实测（run 38473962277）：**102 帧里一处黑带都没有**，而名单上有 9 处
            // ⇒ "黑带消失了"那条守卫在 CI 上恒红（并被 report-only 吞掉）。
            // 名单是本机量出来的**事实**，拿到没见过黑带的机器上判"事实变了"不是判据，是错觉。
            // 只关这一个方向：`extra`（第一次冒黑）在上面，任何机器上都照样红 —— 它自己带证据。
            emit("MATERIAL_BLIND_NOT_RUN 这台机器 102 帧里一处黑带都没有，而名单上有 "
                  + "\(Self.materialBlindSpotFixtures.count) 处 ⇒ 「黑带消失了」这一方向无从判起"
                  + "（名单是本机量出来的）；「第一次冒黑」那一方向仍然开着")
        }
        emit("MATERIAL_BLIND_SPOTS \(blind.count) of \(Set(report.map { Self.fixtureName(fromFile: $0.name) }).count) fixtures")
    }

    /// settings 族的一行读数（其余两条前提只看族外，这里给个"没裁到底"的正常值）。
    private static func settingsReading(_ transparent: Double) -> CaptureCapability.Reading {
        CaptureCapability.Reading(family: "settings", transparent: transparent,
                                  blackBandPt: 0, bottomInkFraction: 0.794)
    }

    private static func otherReading(_ family: String, transparent: Double = 0,
                                     band: Double = 0, ink: Double = 0) -> CaptureCapability.Reading {
        CaptureCapability.Reading(family: family, transparent: transparent,
                                  blackBandPt: band, bottomInkFraction: ink)
    }

    // 两台机器各自的**实测**读数。本机那份量自 `/tmp/r36-shots-local`（同一份代码），
    // runner 那份量自 `scripts/tests/fixtures/r36_runner_capture.log`（run 38473962277 逐字日志里的
    // 102 行逐帧表格）。settings 族 18 行**全抄** —— 那条判据是"族内每一张都超过线"，
    // 少一行这张表就钉不住 `allSatisfy`（第一版我只抄了极值，于是"中间有一张画得出来"
    // 这种最该红的情形在表上是空的）。黑带与底行墨那两条判的是 `contains` 与 `max`，
    // 比它们小的行不会改变结论，所以每台只抄决定性的那几行。
    private static let localCapabilityReadings: [CaptureCapability.Reading] =
        [0.696, 0.697, 0.564, 0.564, 0.435, 0.435, 0.208, 0.208, 0.231, 0.231,
         0.285, 0.286, 0.544, 0.544, 0.787, 0.788, 0.704, 0.708].map { settingsReading($0) }
        + [otherReading("sidebar", band: 66, ink: 1.0),        // sidebar-history 亮色版
           otherReading("sidebar", band: 29, ink: 1.0),        // 暗色版
           otherReading("content", band: 43, ink: 0.967),
           otherReading("detail", ink: 1.0),
           otherReading("row", ink: 0.025)]

    private static let runnerCapabilityReadings: [CaptureCapability.Reading] =
        (Array(repeating: 0.922, count: 14) + [0.906, 0.906, 0.959, 0.959]).map { settingsReading($0) }
        + [otherReading("sidebar", ink: 1.0),                  // 暗色版：100.0%
           otherReading("sidebar", ink: 0.0),                  // 亮色版：**0.0%**（本机是 100.0%）
           otherReading("content", band: 0, ink: 0.56),
           otherReading("detail", ink: 1.0),
           otherReading("row")]

    /// 两条前提各自都要有一条"该反过来"的臂，否则这张表只是在抄读数。
    ///
    /// R37 起这里**只剩两条**前提：第三条（"底行墨这把尺活着"）被撤掉了 ——
    /// 它当时是 `bottomInkFraction` 的色差假读数撑着的（U-60），而"这台机器上一帧都读不到墨"
    /// 这件事的正确反应是**红**，不是登记成未运行。现在那件事由 `row-clipped-control`
    /// 这张已知被裁的对照帧无条件判（见 `bottomEdgeInkCanary`），不在这张表里。
    func testCaptureCapabilityPremisesAreMachineVisible() {
        let local = CaptureCapability.measure(Self.localCapabilityReadings)
        XCTAssertFalse(local.settingsFamilyIsBlank,
                       "本机 settings 族最低那张只未绘制 20.8% ⇒ 这一族在本机是画得出来的")
        XCTAssertTrue(local.bandsSeenHere)
        XCTAssertEqual(0.208, local.settingsLowestBlank, accuracy: 0.0001)

        let runner = CaptureCapability.measure(Self.runnerCapabilityReadings)
        XCTAssertTrue(runner.settingsFamilyIsBlank,
                      "runner 上 settings 族 18 张**全部**超过 85%（最低 90.6%）⇒ 那两条"
                      + "「95% 未绘制」的红在这台机器上属于「整族画不出来」，登记成 CAPTURE_NOT_RUN")
        XCTAssertFalse(runner.bandsSeenHere,
                       "runner 上 102 帧一处黑带都没有，而名单上有 9 处 ⇒ 「黑带消失了」那个方向无从判起")
        XCTAssertEqual(0.906, runner.settingsLowestBlank, accuracy: 0.0001)

        // 反例臂①：**只有一张** settings 帧空白，兄弟帧都画得出来（本机那 17 行的真实读数 + 一张 99%）。
        // 这正是那条 XCTFail 存在的理由（"不是机器不行，是这一张不行"），
        // 它绝不可以被族前提放行 —— 这一臂红了说明整个"登记 NOT-RUN"机制被做宽了。
        let oneBadFrame = CaptureCapability.measure(
            Array(Self.localCapabilityReadings.dropLast()) + [Self.settingsReading(0.99)])
        XCTAssertFalse(oneBadFrame.settingsFamilyIsBlank,
                       "族里有画得出来的兄弟帧时，`settingsFamilyIsBlank` 必须为假 ⇒ 那张空白要红，不许登记")

        // 反例臂②：这一族只交出**一张**帧。一张不构成"整族"，不许当机器能力用。
        let singleFrameFamily = CaptureCapability.measure(
            [Self.settingsReading(0.99), Self.otherReading("detail", ink: 1.0)])
        XCTAssertFalse(singleFrameFamily.settingsFamilyIsBlank,
                       "只有一张帧时不许宣告整族空白 —— 那正好是「捕获失效」最像「机器不行」的形状")
        emit("CAPABILITY_TRUTH_TABLE 4 臂（本机 / runner / 单帧空白 / 族只一张）："
              + "local(blank=\(local.settingsFamilyIsBlank),band=\(local.bandsSeenHere)) "
              + "runner(blank=\(runner.settingsFamilyIsBlank),band=\(runner.bandsSeenHere))")
    }

    /// 这把尺自己的真值表（R37 / U-60）：**合成图**，三张，各钉一个方向。
    ///
    /// 这不覆盖管线：它只判"参照点在哪"这一件事。管线级判据在 `testCaptureKeyViews` 里 ——
    /// 那张 `row-clipped-control`（已知被裁，必须读得到墨）与 mustFit 那十条（必须读不到）。
    /// 两边都要有：只有合成图，改坏渲染通道不会红；只有真帧，"参照点是角点"这种错就没人钉。
    func testBottomInkRulerUsesTheRowOwnBackground() throws {
        func bitmap(_ pixels: (Int, Int) -> (Int, Int, Int), width: Int = 100, height: Int = 40)
            throws -> NSBitmapImageRep {
            guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                                             bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                             isPlanar: false, colorSpaceName: .deviceRGB,
                                             bytesPerRow: width * 4, bitsPerPixel: 32),
                  let base = rep.bitmapData else {
                throw XCTSkip("建不出位图（这台机器给不了 bitmapData）")
            }
            for y in 0..<height {
                for x in 0..<width {
                    let rgb = pixels(x, y)
                    let o = y * rep.bytesPerRow + x * 4
                    base[o] = UInt8(rgb.0); base[o + 1] = UInt8(rgb.1)
                    base[o + 2] = UInt8(rgb.2); base[o + 3] = 255
                }
            }
            return rep
        }
        func ink(_ rep: NSBitmapImageRep) -> Double {
            Self.bottomInkFraction(bytes: rep.bitmapData!, width: rep.pixelsWide,
                                   height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow)
        }
        let grey = (240, 240, 240)
        // ① 整帧都是底色，只有**左上角那一个像素**是白的：这就是 U-60 的形状。
        //    旧实现（参照点 = `bytes[0]`）在这里读 100%（45 > 12 ⇒ 整行数成墨），
        //    正确实现必须读 0 —— 这一张就是"参照点被挪回角点"的绊线。
        let cornerOnly = try bitmap { x, y in (x == 0 && y == 0) ? (255, 255, 255) : grey }
        XCTAssertEqual(ink(cornerOnly), 0.0, accuracy: 0.0001,
                       "底行整行都是底色，只有角点不同 ⇒ 读到墨就说明参照点又变回'左上角那一个像素'了")
        // ② 底行左半边压着半截字 ⇒ 读到 ~50%。
        let halfInk = try bitmap { x, y in (y == 39 && x < 50) ? (20, 20, 20) : grey }
        XCTAssertGreaterThan(ink(halfInk), 0.45, "半行被压住 ⇒ 这把尺必须读到")
        XCTAssertLessThan(ink(halfInk), 0.55, "读到 100% 说明它把整行都数成了墨")
        // ③ 底行**整行**是同一个深色块（全出血）：中位数就是它 ⇒ 读 0。
        //    这是**写下来的边界**，不是缺陷：那种帧要的是另一条判据（"帧底不许是全出血填充"）。
        let fullBleed = try bitmap { _, y in y == 39 ? (20, 20, 20) : grey }
        XCTAssertEqual(ink(fullBleed), 0.0, accuracy: 0.0001,
                       "整行同色时这把尺读 0 —— 已知边界，别把它当'没裁'的证据")
        // 两条线必须是**一对**：mustFit 要求"读不到"，对照帧要求"读得到"。
        // 上限一旦抬到不低于对照帧的下限，同一条读数就能同时满足两条 ⇒ 这两条判据互相取消了。
        XCTAssertLessThan(InkFloor.fixtureBottomInkMaxFraction, InkFloor.bottomEdgeControlMinFraction,
                          "mustFit 的上限（" + String(format: "%.2f", InkFloor.fixtureBottomInkMaxFraction)
                          + "）必须**低于**正对照的下限（"
                          + String(format: "%.2f", InkFloor.bottomEdgeControlMinFraction)
                          + "）⇒ 否则放宽一条就等于同时满足两条，这把尺的正对照与判据互相取消")
        emit("BOTTOM_INK_TRUTH_TABLE 角点=\(String(format: "%.1f", ink(cornerOnly) * 100))%"
              + " 半行=\(String(format: "%.1f", ink(halfInk) * 100))%"
              + " 全出血=\(String(format: "%.1f", ink(fullBleed) * 100))%")
    }

    /// 通用页那颗开关的三态：启用 / 禁用 / 失败回执（R39）。
    ///
    /// 目标里那句"全部状态（空/加载/错误/成功/选中/悬停/按下/聚焦/**禁用**）"，
    /// 禁用是修前那 104 张帧里唯一一帧都没有的一档（本轮之后 108）—— 而它不是没有代码：`SettingsView:325` 有
    /// `.disabled(!isSupported)`、`LoginItemSettings:104` 有那句"当前系统不支持…"、
    /// 模型层三条单测都齐，视图层一个像素都没有。
    ///
    /// 这条判据问三件事，其中两件是**成对的**（都带负对照）：
    /// ① 禁用必须看得见 —— 同一块标签矩形，禁用帧的最深偏离要明显比启用帧淡
    ///    （看不见的禁用等于"能点但没反应"）；
    /// ② 那句回执必须画得出来 —— 它那一块必须是**说明档**、不能是别的控件（标题档），
    ///    并且比**没有回执的那张帧在同一块上多出一行说明档**；
    /// ③ 回执那一行必须还在说明档 —— 交给 `captionInkProbes`（本轮登记两条新探针）。
    ///
    /// ②里那条跨帧对照为什么是"差值"而不是"没回执的帧读 0 墨"，见下面 ③ 处的记录。
    ///
    /// **这一档有机器前提**（R39b 补，起因是 R39 第一版在 CI 上恒红）：三张帧都来自 `SettingsView`，
    /// 而 runner 上这一族是一块平涂（BACKLOG 43）⇒ 那里每条读数天然是 0。判据先问
    /// "这一列在这一台画没画出来"：三张全没画 ⇒ 显式记未运行（`DISABLED_STATE_NOT_RUN`，
    /// 闸门会把它算进 NOT_RUN）；三张全画了 ⇒ 判；**只画出一部分 ⇒ 红**（那不是环境问题）。
    ///
    /// 所有读数都打出来：禁用后"到底有多淡"是要给人判断的，不是要藏在一个 ✓ 后面。
    func testDisabledToggleAndFailureReceiptAreVisible() throws {
        // 两个矩形都是从帧上量的（`testSettingsCaptionRowTierProfileDiagnostic` 这轮把两张新帧
        // 也扫了）：标签带 y=117.5..129.0，它下面那句回执带 y=136.5..145.5。
        let labelRect = CGRect(x: 150, y: 117.5, width: 200, height: 11.5)
        let receiptRect = CGRect(x: 150, y: 136.0, width: 420, height: 10.0)
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r39-disabled-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        struct Reading {
            let labelRatio: Double      // 标签的对比度（inkContrast，尾墨 2%）
            let labelInk: Int           // 标签带里"算字"的像素数
            let receiptInk: Int
            let receiptCaption: Int     // 回执带里说明档那一档的像素数
            let receiptTitle: Int       // 同一块里标题档的像素数（负对照要看它）
            let contentInk: Int         // **整条内容列**的算字像素 —— 只回答"这一台拍不拍得出这一页"
        }
        func read(_ name: String, _ appearance: NSAppearance.Name) throws -> Reading? {
            guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                XCTFail("找不到夹具 \(name) ⇒ 禁用态判据失去对象"); return nil
            }
            let file = scratch.appendingPathComponent("\(name)-\(appearance.rawValue).png")
            _ = try render(fixture, appearance: appearance, to: file)
            // 读**落盘那张图**（R37 的教训：raw rep 里"没画"的像素是透明的，会把中位数抢走）
            guard let bytes = try? Data(contentsOf: file),
                  let rep = NSBitmapImageRep(data: bytes), let base = rep.bitmapData else {
                XCTFail("\(file.lastPathComponent) 读不回字节"); return nil
            }
            let scale = Double(rep.pixelsWide) / 720.0
            func mass(_ rect: CGRect) -> Int {
                Self.textInkMass(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                 bytesPerRow: rep.bytesPerRow, rect: rect, scale: scale).pixels
            }
            let profile = Self.rowTierProfile(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                              bytesPerRow: rep.bytesPerRow, rect: receiptRect, scale: scale)
            return Reading(
                labelRatio: Self.inkContrast(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow, rect: labelRect, scale: scale).ratio,
                labelInk: mass(labelRect),
                receiptInk: mass(receiptRect),
                receiptCaption: profile.reduce(0) { $0 + $1.caption },
                receiptTitle: profile.reduce(0) { $0 + $1.title },
                contentInk: mass(CGRect(x: 150, y: 20, width: 560, height: 500)))
        }

        var judged = 0
        var notRun = 0
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            guard let plain = try read("settings-general", appearance),
                  let unsupported = try read("settings-general-login-unsupported", appearance),
                  let failed = try read("settings-general-login-failed", appearance) else {
                emit("DISABLED_STATE_NOT_RUN \(tag) 三张帧没齐 ⇒ 这一档在这一台无从判起")
                notRun += 1
                continue
            }
            // **机器前提（R39b，CI 第一次跑就红给它看了）**：runner 上 `SettingsView` 的内容列
            // 是一块平涂（BACKLOG 43；本轮 CI 的 `ROWTIER settings-general-login-* dark：有字行 0 行`
            // 就是同一件事），于是这里每一条读数都是 0 / 对比度 1.00 —— 那不是"禁用没淡"，
            // 是"这一台拍不出这一页"。判据必须先问这一列画没画，再问画出来的东西对不对；
            // 反过来把地板降到能容纳 0 读数，就等于把判据删掉（U-61 / U-62 同一族，第三次犯）。
            //
            // 三条帧问的是**同一个问题**，所以这里判的是**一致性**而不是量级：
            // 0 张有墨 ⇒ 这一台拍不出这一页 ⇒ 如实记未运行；3 张有墨 ⇒ 判；
            // **1 或 2 张** ⇒ 同一列不可能只画出一部分，那是某一帧坏了或框贴错了 —— 照旧红。
            let drawable = Self.settingsDrawability(
                [plain.contentInk, unsupported.contentInk, failed.contentInk])
            switch drawable {
            case .partial(let drawn):
                return XCTFail("\(tag)：三张帧的同一条内容列里只有 \(drawn) 张读到墨"
                               + "（\(plain.contentInk)/\(unsupported.contentInk)/\(failed.contentInk)）"
                               + " ⇒ 这不是「这一台画不出这一页」（那要么三张全有、要么三张全无），"
                               + "而是其中某一帧坏了或者我的框贴错了。先去看那一张帧")
            case .noneDrawn:
                emit("DISABLED_STATE_NOT_RUN \(tag) 内容列读到 "
                      + "\(plain.contentInk)/\(unsupported.contentInk)/\(failed.contentInk) 个算字像素"
                      + " ⇒ 这一台拍不出设置页（BACKLOG 43），这一档记未运行，不算通过")
                notRun += 1
                continue
            case .allDrawn:
                break
            }
            judged += 1
            // ① **禁用必须看得见**：同一块标签矩形，禁用帧的对比度要明显比启用帧低。
            //    为什么判对比度而不是"最深偏离"：暗档禁用后的标签淡到连 `isTextInk` 那道门都过不去
            //    （本轮实测：暗档那一行的 profile 是空的）—— 那种情况下"最深偏离"根本没有值可比。
            XCTAssertLessThanOrEqual(unsupported.labelRatio, plain.labelRatio * 0.70,
                "\(tag)：禁用帧标签对比度 \(String(format: "%.2f", unsupported.labelRatio))，"
                    + "启用帧 \(String(format: "%.2f", plain.labelRatio)) ⇒ 淡得不够。"
                    + "看不出禁用的开关，用户会一直点它")
            XCTAssertGreaterThan(unsupported.labelRatio, 1.20,
                "\(tag)：禁用帧标签对比度只有 \(String(format: "%.2f", unsupported.labelRatio)) ⇒ 淡到与背景同色。"
                    + "禁用不等于消失（HIG：被禁的东西仍要读得出是什么东西）—— "
                    + "真到这一步的处置不是把线抬高，而是**别用 `.disabled` 表达这个状态**，"
                    + "让那句回执去说明（回执本身是说明档，读数在下面一行）")
            // ② **回执必须画得出来**（它藏在 `if let message` 后面，模型层三条单测全绿也救不了视图不显示）
            for (name, reading) in [("settings-general-login-unsupported", unsupported),
                                    ("settings-general-login-failed", failed)] {
                XCTAssertGreaterThanOrEqual(reading.receiptInk, 500,
                    "\(tag)：\(name) 的回执带只读到 \(reading.receiptInk) 个算字的像素 ⇒ 那句话没画出来")
                XCTAssertEqual(reading.receiptTitle, 0,
                    "\(tag)：\(name) 的回执带里读到 \(reading.receiptTitle) 个**标题档**像素 ⇒ "
                        + "那块矩形上压着的不是回执，是别的控件（框放错，或者布局把下一行顶上来了）")
            }
            // ③ **负对照，相对版**：同一块矩形，有回执的帧要比没有回执的帧多出整整一行说明档。
            //    第一版这里写的是"没有回执的那张帧读 0 墨"，本机 382 / 471 个像素直接把它推翻了：
            //    通用页在插入那句回执时会把**下面一颗开关的标签**顶到别的位置，而没插入时那颗标签
            //    正好压在 y=136 这一块上（同一块里还读到 971 / 1064 个**标题档**像素 ⇒ 那里住的是
            //    标题，不是说明）。所以布局会随内容移动的矩形上，"跨帧比有没有墨"是错的问法，
            //    正确的问法是"跨比**多出来的墨**"：回执没画 ⇒ 差值 0 ⇒ 红；
            //    回执画了但透明/颜色与背景同 ⇒ 差值是负的 ⇒ 红。
            for (name, reading) in [("settings-general-login-unsupported", unsupported),
                                    ("settings-general-login-failed", failed)] {
                XCTAssertGreaterThan(reading.receiptCaption, plain.receiptCaption + 500,
                    "\(tag)：\(name) 的回执带说明档 \(reading.receiptCaption) 个像素，"
                        + "没回执那张帧同一块 \(plain.receiptCaption) 个 ⇒ 只多出 "
                        + "\(reading.receiptCaption - plain.receiptCaption) 个（要求 >500）。"
                        + "这一行回执要么没画，要么淡到不成字")
            }
            emit("DISABLED_STATE \(tag)：标签对比度 启用=\(String(format: "%.2f", plain.labelRatio)) "
                  + "禁用=\(String(format: "%.2f", unsupported.labelRatio))（淡到 "
                  + String(format: "%.2f", unsupported.labelRatio / max(plain.labelRatio, 0.01)) + " 倍）"
                  + " 标签算字像素 启用=\(plain.labelInk) 禁用=\(unsupported.labelInk)"
                  + "；回执带 墨(不支持/失败)=\(unsupported.receiptInk)/\(failed.receiptInk) "
                  + "说明档=\(unsupported.receiptCaption)/\(failed.receiptCaption) "
                  + "差值(+\(unsupported.receiptCaption - plain.receiptCaption)"
                  + "/+\(failed.receiptCaption - plain.receiptCaption)) "
                  + "无回执那帧同块(说明档/标题档)=\(plain.receiptCaption)/\(plain.receiptTitle)")
        }
        // 两档外观必须**各有一个交代**：判成了，或者显式记为未运行。
        // 这条不要求"必须判成"—— 那正是 R39 第一版在 CI 上恒红的原因（runner 拍不出设置页）。
        // 但它也不允许"悄悄少判一档"：`judged + notRun != 2` 只有两种来路（读不到帧、或者我改坏了循环），
        // 两种都该红。未运行的条数由 `DISABLED_STATE_NOT_RUN` 打进日志，CI 闸门把它算进 NOT_RUN（不省略成"通过"）。
        XCTAssertEqual(judged + notRun, 2,
                       "两档外观应该有 2 个交代（判成或未运行），现在 judged=\(judged) notRun=\(notRun) "
                       + "⇒ 这一档在这一台既没判成、也没被如实记账")
        emit("DISABLED_STATE_COVERAGE 判成 \(judged) 档、未运行 \(notRun) 档（共 2 档）")
    }

    /// 机器前提这把"折成决定"的尺本身要有真值表（R39b）。
    ///
    /// 为什么单独一条：真实环境里这一族**要么三张全有墨（本机）要么三张全无（runner）**，
    /// 中间那一格（1 或 2 张）在两台机器上都走不到 —— 而它正是"环境问题"与"某一帧坏了"的分界。
    /// 走不到的分支不打桩测一次，就等于没有那条分支（M183 把 `.partial` 折成 `.noneDrawn`
    /// 就是这一格的红）。
    func testSettingsDrawabilityTruthTable() {
        XCTAssertEqual(Self.settingsDrawability([900, 1200, 700]), .allDrawn,
                       "三张都有墨必须判 —— 这一格判不成，机器前提就成了免检牌")
        XCTAssertEqual(Self.settingsDrawability([0, 0, 0]), .noneDrawn,
                       "三张都没墨必须记未运行 —— 这是 runner 的真实形状")
        XCTAssertEqual(Self.settingsDrawability([0, 1200, 700]), .partial(2),
                       "只画出一部分不是环境问题：同一列要么全有要么全无，这一格必须红")
        XCTAssertEqual(Self.settingsDrawability([900, 0, 0]), .partial(1),
                       "只有一张有墨同样必须红（那是夹具坏了，不是机器不行）")
        emit("SETTINGS_DRAWABILITY_TRUTH_TABLE 全有=判 / 全无=未运行 / 1|2 张=红（四格全过）")
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
        // R63：R18 想加、R19 判"加不进去"的三张浮层帧，**现在加进去了**。
        // R19 那句根因是错的（它说 stack 在捕获环境里塌，而"真实 App 里它撑满 420×300"）：
        // 实测两条路都塌 —— `NSStackView` 生下来 `translatesAutoresizingMaskIntoConstraints == false`，
        // 而产品只给了 `frame` + `autoresizingMask`，那两行因此都是空操作，
        // 于是 stack 24×49、`NSScrollView` 0×0、`visibleRect` 0×0（同一探针、同一夹具、只换那一个文件）。
        // 修好之后：stack 420×300、滚动视图 396×251、8 行里第一行选中，`cacheDisplay` 从
        // `drawn=0.0%` 变成 `drawn=19.3%`（判据 `testQuickPickOverlayFillsItsPanelAndCanBeCaptured`）。
        // 这三张用的是 `QuickPickCapturePanel`（把控制器关在闭包里保命：表格的 dataSource 是弱引用）。
        results.append(Fixture("quickpick-list", NSSize(width: 420, height: 300)) {
            AnyView(EmptyView())
        }.withAppKit(QuickPickCapturePanel.builder(store: store, query: "")))
        // 查询词"访达"**不是随手编的**：它命中 `makePopulatedStore()` 里那两条来源为访达的条目
        // （`.file` 与 `.files` 各一条），所以这张帧判的是"过滤之后还剩几条、剩下的怎么画"。
        // 第一版我写的是 "记录 3"（从本轮探针的夹具里抄来的），而 harness 这个 store 里
        // 根本没有那种文本 ⇒ 帧拍出来是"没有匹配「记录 3」的记录" —— 一张名字叫 typed
        // 而内容是 empty 的帧。教训与账本里那条同一族：**夹具要照抄调用方的真实口味**。
        results.append(Fixture("quickpick-typed", NSSize(width: 420, height: 300)) {
            AnyView(EmptyView())
        }.withAppKit(QuickPickCapturePanel.builder(store: store, query: "访达")))
        results.append(Fixture("quickpick-empty", NSSize(width: 420, height: 300)) {
            AnyView(EmptyView())
        }.withAppKit(QuickPickCapturePanel.builder(store: store, query: "zzz 不存在")))
        // R67：悬停那一档第一次有帧可看。点的是**第 3 行**而不是第 0 行 ——
        // `windowForCapture` 里 `model.index = 0` 让第 0 行是选中的，而选中时不画悬停灰
        // （`showsHoverTint` 的次序：hover 0.06 < selected 0.16）。点第 0 行会拍出
        // 一张"名字叫 hover、内容是没 hover"的帧 —— 与 R63 那张"名字叫 typed、
        // 内容是 empty"的帧同一族错误，那次是靠看图才发现的，这次把行号写在这里。
        results.append(Fixture("quickpick-hover", NSSize(width: 420, height: 300)) {
            AnyView(EmptyView())
        }.withAppKit(QuickPickCapturePanel.builder(store: store, query: "", hoveredRow: 3)))

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

        // **一把故意裁自己的行**（R37 / U-60）：同一颗 `HistoryRowButton`、同样 300pt 宽，
        // 外框从 74pt 压到 58pt 并显式 `.clipped()`。它**不是产品证据，是尺的对照物**：
        // `contentMustFit` 判的是"这十张帧的底行不许有墨"，而一条只在"该红的没红"上被检验的尺
        // 等于没被检验。R22 当时挑的对照物（`sidebar-history`）后来被查出读的是色差不是墨（U-60）
        // ⇒ 这条判据到本轮才第一次有一个真的正对照。
        results.append(Fixture("row-clipped-control", NSSize(width: 300, height: 58)) {
            AnyView(self.clippedRowFrame(HistoryRowButton(
                entry: store.entries[0], copyAction: {}, favoriteAction: {}
            )))
        })

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
        // R28b 撤掉 `settings-shortcuts-wide`：它在本机一切正常，
        // 但 **CI 的 macos-15 runner 上 900pt 与 1100pt 两档都整帧读出 0 墨**
        // （run 38449711539 / 38451162726），而 ≤750pt 的 100 张帧从来没问题。
        // 于是参照臂换成"更窄的那一臂"（`settings-min`，640pt）—— 见
        // `testSettingsHelperTextIsNotClipped` 上面那段。
        results.append(Fixture("settings-min", NSSize(width: 640, height: 440)) {
            AnyView(self.makeSettingsView(store: store))
        })

        // **禁用态与失败回执**（R39）。目标里那句"全部状态（空/加载/错误/成功/选中/悬停/按下/聚焦/禁用）"，
        // 只有**禁用**这一档在修前那 104 张帧里一个像素都没有（本轮之后 108）—— 而它不是没有代码：
        // `SettingsView:325` 有 `.disabled(!loginItemSettings.isSupported)`，
        // `LoginItemSettings:104` 有那句"当前系统不支持从应用内设置开机启动。"，
        // `LoginItemSettingsTests` 三条都测过**模型层**，视图层从来没有一张帧。
        // 更要紧的是第二张：macOS 12 走 AppleScript 那条路，而它**以前静默失败**
        // （`executeAndReturnError` 的 error 被丢掉，脚本没生效也没人知道）⇒
        // 用户看到的是"开关自己弹回去，一句话都没有"。R39 给它加了"写完读回"（D-098），
        // 这张帧就是那句话第一次被画出来给人看。
        let loginUnsupported = LoginItemSettings(
            manager: FakeLoginItemManager(isSupported: false, isEnabled: false))
        results.append(Fixture("settings-general-login-unsupported", NSSize(width: 720, height: 540)) {
            AnyView(self.makeSettingsView(store: store, initialCategory: .general, loginItem: loginUnsupported))
        })
        results.append(Fixture("settings-general-login-failed", NSSize(width: 720, height: 540)) {
            AnyView(self.makeSettingsView(store: store, initialCategory: .general, loginItem: {
                let manager = FakeLoginItemManager(isSupported: true, isEnabled: false)
                // 走**产品的失败路径**造这句回执，不直接伪造 `message`：
                // 伪造会让帧证明"一个没人走过的状态长这样"，而这条路径正是本轮新加的读回检查。
                manager.error = LoginItemSettings.Error.loginItemNotApplied
                let settings = LoginItemSettings(manager: manager)
                settings.setEnabled(true)
                return settings
            }()))
        })

        // 每日复制热图（新功能 / 阶段一）：组件级两张 —— 有数据与没数据。
        // 固定 `today` 与固定计数 ⇒ 这两张帧不随日期变。
        let heatToday = Self.heatmapFixtureToday
        let heatCalendar = Self.heatmapFixtureCalendar()
        let heatCounts = Self.heatmapFixtureCounts(today: heatToday, calendar: heatCalendar)
        results.append(Fixture("heatmap-populated", NSSize(width: 430, height: 250), contentMustFit: true) {
            AnyView(
                DailyCopyHeatmapView(counts: heatCounts, today: heatToday, calendar: heatCalendar)
                    .padding(16)
                    .frame(width: 430, height: 250, alignment: .topLeading)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })
        // R45 · 悬停那一圈**第一次有帧可看**（两张一组，只差一格）。
        //
        // 为什么单独拍一条带而不是在 `heatmap-populated` 上做：那一张走的是
        // `DailyCopyHeatmapView`，而 `hovered` 是它的 `@State` —— 合成 hover 的三条路
        // R14 实测全断（见 `HeatmapHoverEvidenceTests` 开头）。这条带绕不开同一个事实，
        // 但它画的是**产品自己的格子视图** `DailyCopyHeatmapCell`（网格那条路就是它，
        // 由 `testGridCellsRouteThroughTheProductCellView` 钉住），
        // 深浅与日期都由 policy 现算 —— 夹具只挑"哪一格被悬停"，一个字都不替产品写。
        // 两张唯一的差别就是那一圈墨：审查时能一眼看出"悬停长什么样"，
        // 而 `HEAT_RING` 那 20 条读数回答的是"它到底有没有被画上去"。
        // 取**最后**三列而不是前三列：夹具的计数从"今天"往回 126 天，而窗口是 26 周 = 182 天，
        // 于是最老的那几列本来就是空的 —— 第一版用 `prefix(3)` 拍出来的 21 格全是空档灰，
        // 那张帧什么都回答不了（"那一圈压在深蓝格上是什么样"正是本轮要看的东西）。
        // 帧存在 ≠ 被摄对象在帧里，这一条在 R28c 与批次 22 上各栽过一次。
        let heatCells = Self.heatmapHoverStripCells(counts: heatCounts, today: heatToday,
                                                    calendar: heatCalendar)
        results.append(Fixture("heatmap-cell-strip-still", NSSize(width: 90, height: 140),
                               contentMustFit: true) {
            AnyView(
                Self.heatmapCellStrip(cells: heatCells, hoveredIndex: nil, calendar: heatCalendar)
                    .padding(16)
                    .frame(width: 90, height: 140, alignment: .topLeading)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })
        results.append(Fixture("heatmap-cell-strip-hover", NSSize(width: 90, height: 140),
                               contentMustFit: true) {
            AnyView(
                // 悬停第 10 格（= 第 2 列第 4 行）：不在角上、也不是第一格，
                // 这样那一圈与它上下左右的邻居同时进画面，"喧宾夺主"能直接被看见。
                Self.heatmapCellStrip(cells: heatCells,
                                      hoveredIndex: Self.heatmapHoverStripHoveredIndex,
                                      calendar: heatCalendar)
                    .padding(16)
                    .frame(width: 90, height: 140, alignment: .topLeading)
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
        // 高度 56 → **72**：换成产品自己那句话之后 `contentMustFit` 当场打红
        // （底行 18.4% / 20.2% 有墨 ⇒ 56pt 放不下两行）。这不是"把断言关掉"，是这张帧
        // 一直在裁自己展示的内容 —— 被裁掉的那半行从来没有进过基线，也就从来没有被审过。
        results.append(Fixture("receipt-line", NSSize(width: 430, height: 72), contentMustFit: true) {
            AnyView(
                // R43 / BACKLOG 62：**这句话以前是夹具手写的** ——
                // 原来是 `"已导出 94 条记录到 ~/Desktop/时间剪史-导出.json"`，
                // 而全仓 grep 不到这句产品话（产品说的是 `ArchiveTransfer.exportWarningText` 那一套
                // 与本轮的 `FeedbackExportReceipt`）。这是 R24 那条规矩的又一次违反：
                // 夹具替产品写了一句产品不会说的话，于是这张帧一直在给一个不存在的文案做保。
                // 现在文案从生产者取：以后有人把回执改长、改措辞，这张帧自己会红。
                ReceiptLine(text: FeedbackExportReceipt.failure(
                                RecommendationFeedbackStore.ExportError.writingFailed("disk full")),
                            dismiss: {})
                    .padding(.horizontal, 12)
                    .frame(width: 430, height: 72, alignment: .leading)
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
        // R40：**复制失败**那句回执必须放得下（U-66 / D-099）。
        //
        // 为什么要为一句新文案单开一张帧：这条链路的回执是**拼出来的**（"复制到剪贴板失败："
        // + 系统错误原文 + 一句安抚），长度不由设计方控制 —— 系统错误描述可以是很长的一句英文。
        // R28 已经为"说明文字被截断"红过一次，而那次的教训是：**只有帧能证明一句话放得下**，
        // 读代码看不出换行与截断。
        // 文案不是夹具手写的，而是从产品那个生产者 `CopyThenPaste.decide` 取的：
        // 以后有人改措辞或把它拼长，这张帧自己会红，而不是等用户看到半句话。
        // R41：喂给它的不再是**手写的字符串**，而是产品真的会抛的那个错误
        // （`ClipboardWriteError.failedToWriteText`）—— 中间走 `classify` 与 `decide` 两层生产者。
        // 于是这张帧画的是"产品在这种情况下真的会说什么"，而不是"我以为它会说什么"：
        // 改措辞、改长度、改那句"原来的内容还在不在"，帧都会自己红。
        let copyFailureDecision = CopyThenPaste.decide(
            failure: ClipboardWriteFailure.classify(ClipboardWriteError.failedToWriteText))
        let copyFailureNotice: String
        if case .cancel(let reason) = copyFailureDecision {
            copyFailureNotice = reason
        } else {
            // 走不到（这一臂必然给回执）。真走到了就是产品改语义而这条夹具会**显式**坏在画面里，
            // 而不是悄悄拍到一张"看起来正常"的帧 —— 形状由 `testCopyThenPasteTruthTable` 判。
            copyFailureNotice = "⟨CopyThenPaste 没给出回执 ⇒ 夹具坏了，见 testCopyThenPasteTruthTable⟩"
        }
        let copyFailureStore = makePopulatedStore()
        copyFailureStore.reportPasteFailure(copyFailureNotice)
        results.append(Fixture("content-with-copy-failure-notice", NSSize(width: 750, height: 560)) {
            AnyView(ContentView(historyStore: copyFailureStore))
        })
        // R41：**同一句话摆到产品允许的最窄窗口上**（600×440 = `App.swift` 的 `minWidth`
        // 与 `WindowConfigurator.window.minSize`，不是夹具自选的宽度）。
        // 上一轮的姐姐帧是 750 宽，而这条回执的长度由**系统错误原文**决定 ——
        // 在 750 上放得下不等于在 600 上放得下。缺这一臂的话，"文案变长"这件事
        // 只会在用户把窗口拖到最窄时以"半句话 / 按钮被挤没"的形式被发现。
        let copyFailureMinStore = makePopulatedStore()
        copyFailureMinStore.reportPasteFailure(copyFailureNotice)
        results.append(Fixture("content-min-with-copy-failure-notice", NSSize(width: 600, height: 440)) {
            AnyView(ContentView(historyStore: copyFailureMinStore))
        })
        // **组件帧必须摆成产品那一套**（R24 / BACKLOG 36）。
        //
        // 以前这里是 `VStack(spacing: 12)`，而产品（`ContentView`）是 `spacing: 0` + 每条横幅
        // 自己带一条 `Divider()`。量出来的差别：组件帧两条带之间是 **13pt 的窗口底色**（86→99），
        // 产品帧是 **1pt 的发丝线**（90→91）。也就是说这张帧一直在展示一个产品里不存在的布局，
        // 而"两条横幅挨在一起长什么样"这个状态**从来没有被真的看过** —— 组件帧看起来有证据，
        // 其实证据是夹具自己编的。现在两张帧互为对照：同一条判据（带间缝隙）在两边都必须读到同一个值。
        //
        // 高度**保持 170**，这一条是被自己的守卫逼出来的：我先按"内容 143pt"把它收到 150，
        // `contentMustFit` 立刻打红（最底一行 95.7% 有墨 ⇒ 已经在裁内容）。量出来的事实是：
        // 这张帧的第一条带并不从 y=12 开始，而是从 **y≈35** 开始，第二条带一直画到 **y≈166**，
        // 也就是 170 的帧底下只剩 4pt 余量 —— 内容比"外框 padding + 两条带"高出 ~15pt，
        // 组件窗口同样有它自己的顶部 inset（这轮只记读数，机制没去量它）。
        // 写在这里是因为"帧比内容高"与"帧裁内容"是同一族谎，而这一族只能量，估一次错一次。
        results.append(Fixture("notice-banner", NSSize(width: 560, height: 170), contentMustFit: true) {
            AnyView(
                VStack(spacing: 0) {
                    NoticeBanner(message: "主存档无法读取，已从备份恢复 12 条记录；损坏原件保留为 history.corrupt-1.json。",
                                 tone: .warning, onDismiss: {})
                    NoticeBanner(message: pasteFailureText, tone: .error, onDismiss: {})
                }
                .padding(12)
                .frame(width: 560, height: 170)
                .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        // **加载态骨架屏第一次进基线**（R26 / U-48）。
        //
        // 为什么以前没有：这块表面是异步的。要拍到它，夹具得赌"拍的那一瞬间预览还没加载完"——
        // 而按墙钟判的夹具每天给出不同的答案（R22 记过"夹具自检不许判跑测试的那一刻"），
        // `MediaLoader.loadFilePreviewHandle` 又是一个静态入口、没有注入缝可以把它钉在加载态。
        // 所以 R26 把产品 `.loading` 分支里那一块提成具名视图 `DetailLoadingView`，
        // 于是它可以被**确定地**画一次。
        //
        // 这是一张**组件帧**：它画的是"加载块本身"，不是"嵌在 DetailView 头部与留白之后的样子"。
        // 尺寸取详情区的名义尺寸 720×520，与 `detail-*` 那几张同框可比。
        // 并且它拍的是 `reduceMotion: true` 那一档 —— 扫光的相位是墙钟驱动的，
        // 不钉住的话这张帧每次 sha 都不同（判据分工写在 `DetailLoadingView` 的注释里）。
        // 与 BACKLOG 36 那条教训的分工：外框尺寸是夹具的自由，**组件内部的摆法一律来自产品** ——
        // 这里没有一行布局是夹具新写的，`DetailLoadingView` 里就是产品真画的那个 `VStack`。
        results.append(Fixture("detail-loading", NSSize(width: 720, height: 520)) {
            AnyView(
                DetailLoadingView(reduceMotion: true)
                    .frame(width: 720, height: 520)
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

    /// 行的**裁切对照**外框（R37 / U-60）：与 `rowFrame` 只差两件事 ——
    /// 高度从 74pt 压到 58pt（比这颗行的自然高度矮），以及对齐用 `.topLeading` 后显式 `.clipped()`。
    ///
    /// 为什么必须写 `.clipped()`：`.frame(height:)` 只是"提议"高度，内容会按自己的理想尺寸排布后
    /// **溢出**那个框；溢出的部分画不画进位图，取决于外层有没有裁 —— 那样"被裁"就不保证发生在像素上。
    /// 对照物要的是"我确定这帧底行有半截字"，不是"应该会有的某帧"。
    /// 对齐选 `.topLeading`：让溢出**全部落在底部**，这样底行读到的就是被切的第二行，
    /// 而不是上下各切一半（那种情况下角点/边行的归因又会含糊一次）。
    private func clippedRowFrame<V: View>(_ view: V) -> some View {
        view
            .frame(width: 300, height: 58, alignment: .topLeading)
            .background(Color(nsColor: .windowBackgroundColor))
            .clipped()
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

    private func makeSettingsView(store: HistoryStore,
                                  initialCategory: SettingsCategory? = .shortcuts,
                                  loginItem: LoginItemSettings? = nil) -> some View {
        SettingsView(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: loginItem
                ?? LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
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
            // R28：这两根接缝产品侧（`SettingsWindowController:87,97`）**永远注入**，
            // 而视图里它们是 `.disabled(exportHistoryAction == nil)` 的开关
            // （`SettingsView.swift:584,586`）。夹具不传 ⇒ 「数据」页那两张帧里
            // 导出/导入两颗**一直是禁用态**，而发出去的包里从来没有过这个状态。
            // 后果不只是"帧不好看"：帧基线把禁用态钉成了标准 ⇒ 哪天真把这两颗接坏，
            // 画面与基线**一模一样**，一条判据都不会红。判据见
            // `testCaptureFixtureInjectsEveryActionSeamTheProductInjects`。
            exportHistoryAction: { _ in nil },
            importHistoryAction: { _ in nil },
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

    /// 夹具那套热图日历。**单独成一个函数**而不是在夹具里就地拼：
    /// `HeatmapHoverEvidenceTests` 要用同一套设置去 policy 里挑格子，
    /// 两处各拼一份的话"夹具看到的格子"与"判据看到的格子"会悄悄分叉。
    ///
    /// 必须带中文 locale：不设置的话日历默认 en_US，
    /// 拍出来的星期标签是 "M W F S" —— 审查的人会以为产品写死了英文。
    static func heatmapFixtureCalendar() -> Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Asia/Shanghai") ?? .current
        calendar.firstWeekday = 2
        calendar.locale = Locale(identifier: "zh_CN")
        return calendar
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

    /// 那条带里**被悬停**的那一格的下标（列优先：第 2 列第 4 行）。
    ///
    /// 一个数写在两处（两张夹具）与判据里，是为了让"被指着的那格"这件事
    /// 只有一个作者；`HeatmapHoverEvidenceTests` 会判它必须是一格**画得出来**的格子
    /// （指到未来格上，那一圈根本不存在，两张帧就会一模一样）。
    static let heatmapHoverStripHoveredIndex = 10

    /// R45 · 悬停取证那条带用哪些格子。
    ///
    /// 取**最后**三列而不是前三列：夹具的计数从"今天"往回 126 天，而窗口是 26 周 = 182 天，
    /// 于是最老的那几列本来就是空的 —— 第一版用 `prefix(3)` 拍出来的 21 格全是空档灰，
    /// 那张帧什么都回答不了（"那一圈压在深蓝格上是什么样"正是本轮要看的东西）。
    /// **帧存在 ≠ 被摄对象在帧里**，这一条在 R28c 与批次 22 上各栽过一次。
    /// 挑哪几列这件事本身由 `HeatmapHoverEvidenceTests` 的档位多样性守卫判。
    static func heatmapHoverStripCells(counts: [String: Int], today: Date,
                                       calendar: Calendar) -> [DailyCopyHeatPolicy.Cell] {
        Array(DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, calendar: calendar)
            .suffix(3).flatMap { $0.cells })
    }

    /// R45 · 悬停取证那条带：三列 × 七行真格子，其中一格被"悬停"。
    ///
    /// 画的是**产品自己的** `DailyCopyHeatmapCell`（网格那条路就是它），
    /// `counts` 与分档全来自 policy 现算的格子；夹具唯一的决定是"哪一格是 hovered"。
    /// `onHover` 传空函数：离线渲染里它本来就不会被调用，被调用也不该改任何东西。
    @ViewBuilder
    static func heatmapCellStrip(cells: [DailyCopyHeatPolicy.Cell],
                                 hoveredIndex: Int?,
                                 calendar: Calendar) -> some View {
        VStack(spacing: VisualHeat.spacing) {
            ForEach(0..<7, id: \.self) { row in
                HStack(spacing: VisualHeat.spacing) {
                    ForEach(0..<3, id: \.self) { column in
                        let index = column * 7 + row
                        if index < cells.count {
                            DailyCopyHeatmapCell(cell: cells[index],
                                                 isHovered: hoveredIndex == index,
                                                 calendar: calendar) { _ in }
                        } else {
                            Color.clear.frame(width: VisualHeat.cell, height: VisualHeat.cell)
                        }
                    }
                }
            }
        }
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
    /// R74 / U-115：**"同一条内容被反复复制"那一族真实形状**的语料 —— 文本是长度递增的嵌套前缀
    /// （"一"、"一二"、…、"一二三四五六七八"）。
    ///
    /// 为什么单独建一个而不复用帧夹具那份：帧夹具那 5 条里"这是一段用于"只命中 1 条，
    /// 用它量"打字时候选集会不会一直变"会得出**与产品无关**的答案（只剩一条命中的搜索框本来就不重排）。
    /// 这一份才是浮层打字时的日常：每多打一个字，候选集往下切一层。
    func makeNestedPrefixStore() -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let stems = ["一", "一二", "一二三", "一二三四", "一二三四五", "一二三四五六", "一二三四五六七", "一二三四五六七八"]
        for (offset, stem) in stems.enumerated() {
            store.add(ClipboardIntake.Entry(
                content: .text(stem + " 的复制内容 " + String(repeating: "尾", count: offset)),
                thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"
            ), timestamp: Self.referenceDate.addingTimeInterval(-Double(offset) * 30))
        }
        return store
    }

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
            emit("SEARCH_FIELD_BANDS \(tag) px=\(heights)（诊断用，判据在 idealHeight 那条）")
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
            emit("SEARCH_FIELD_IDEAL_HEIGHTS \(tag) empty=\(box.empty) filled=\(box.filled)")
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

        /// **正文**对它自己的底：WCAG AA 对 13pt 常规文字的下限。
        /// 与上面那条 3.0 不是一回事 —— 3.0 是"非文字 UI 部件的线"，
        /// 而提示条那一行是要被人读完的句子。
        static let bodyTextContrast: Double = 4.5

        /// "这条带里真的有字"的地板。实测最疏的一条（产品里那句短警告）是 3.7%，
        /// 而框套在空白上是 0% ⇒ 地板取 2%：拦得住"带找错了"，又不会把短文案判成缺陷。
        static let bandInkFraction: Double = 0.02

        /// 相邻两条横幅之间允许的空缝。产品实测 1pt（就是那条 `Divider()`）；
        /// 而 R24 修掉的那张组件帧是 **13pt 的窗口底色**。
        static let bandSeamPt: Double = 2.0

        /// **一整页**的"这里确实有字"地板。
        ///
        /// 刻意比 `probeInkFraction`(3%) 低一个量级：那条的分母是一个控件盒，
        /// 而 R28 这条的分母是整个内容列（快捷键页 ≈ 950×540pt）。
        /// 全页文字加起来实测只占 0.8% —— 拿 3% 去钉一整页，
        /// 量到的是"框太大了"，不是"没字"。它的用途只有一个：
        /// **拦住"两臂都贴在空白上 ⇒ 0 ≥ 0 ⇒ 绿"** 那种恒真。
        static let paneInkFraction: Double = 0.002

        /// **说明文字**（刻度、图例、caption）必须在 `.secondary` 那一档：
        /// 允许比"这台机器自己的 `.secondary`"淡 20% 以内。
        ///
        /// 这条刻意**不是** WCAG 的 4.5。4.5 是"要读完的句子"的线（横幅正文用那条，R24），
        /// 而系统的 `secondaryLabelColor` 在纯白上实测只有 **4.0** ——
        /// 拿 4.5 去钉全 App 的说明文字，等于要求每一段 caption 都压黑到比系统档还深，
        /// 那会把"标题—说明"这条层级压平，换来一个不像系统的东西。
        /// 触发它的正是热图那三处刻度：R21 把 `.tertiary` 判为"看不见"并只留给非控件，
        /// R27 重新判一遍 —— 那些数是给"能点的笔画"定的，而**要读的标签没有理由比能点的笔画更淡**。
        ///
        /// **R28 把它从绝对值改成相对参照**：R27 写的是 `3.5`（本机 `.secondary` 实测 3.75–3.85），
        /// 而 **CI 的 macos-15 runner 上同一条红了两处：星期刻度 2.85、图例 3.30**（run 38443414396）。
        /// 那两处产品里用的就是 `.secondary` —— 也就是说绝对值里混进了
        /// "这台机器怎么解析 `secondaryLabelColor`、怎么做字体平滑"，
        /// 而判据要判的从来是"**有没有掉进 `.tertiary` 那一档**"。
        /// 所以参照必须是同一台机器、同一外观现拍的那一份。
        /// 0.8 的来历：本机 `.tertiary` 是 `.secondary` 的 **0.47 倍**（1.88 ÷ 4.0），
        /// 中间留了一大段安全距离，而正常的换行与字重差异不会跨过 0.8。
        static let captionTierTolerance: Double = 0.8

        /// **同一条探针的另一侧**：说明段的墨不许**比 `.secondary` 更深**超过 1.5 倍。
        ///
        /// 这条不是产品要求，是**探针的前提**（R33）。来历：我往 `captionInkProbes` 里加了
        /// 两条"通用页说明段"，读数 13.76（亮）/ 11.43（暗），也就是参照的
        /// **3.67 倍 / 1.89 倍** —— 那不是"说明文字很浓"，是框套在 `.headline` 标题与开关标签上。
        /// 而地板那条（"不许比参照淡"）对这种错法**完全是瞎的**：套错了反而更轻松通过。
        /// 也就是说 R27 以来这张表里每一条"通过"，都只证明了"框里有足够深的墨"，
        /// **没证明过"框里是说明段的墨"**。
        /// 1.5 的来历：本机两簇实测 —— 真的说明段（热图刻度、菜单栏副标题与理由、
        /// 通用页三段说明）比值 **1.00–1.03**；套到标题档的框 **1.89–3.67**。
        /// 取中间值，两侧都留 ≥30% 余量。**刻意用相对参照而不是绝对偏离量**：
        /// 与 `captionTierTolerance` 同一个理由 —— 绝对值里混着"这台机器怎么解析
        /// `secondaryLabelColor`"，而参照就是同一台机器同一外观现拍的那一份。
        ///
        /// 触发它的正确反应写在消息里：**重放框，不是抬天花板**。
        /// 如果产品真的把某段说明提到了 `.primary`，那条探针就该删 ——
        /// 它命名的是一个 `.secondary` 位点，位点没了，命名也就没了。
        static let captionTierCeiling: Double = 1.5

        /// 参照臂自己的兜底地板：**只用来发现"渲染整体失效"**，不是产品线。
        /// 取 2.2 的理由：本机 `.tertiary` 是 1.88、`.secondary` 是 4.0，
        /// 而 CI runner 上 `.secondary` 一档最低读到过 2.85 ⇒ 2.2 两边都过，
        /// 却仍然拦得住"整帧淡到几乎看不见"这种捕获事故。
        static let secondaryReferenceFloor: Double = 2.2

        /// 说明段与它上面那颗开关之间允许的最大空缝（pt，R33 / U-55）。
        ///
        /// 判的是"归属"而不是"间距好不好看"。量的是**墨到墨**：产品里说明段与它的开关是 3pt
        /// （`SettingsViewLayout.captionGap`），可两行的行框各自还带留白，
        /// 所以帧上量到的是 **7.0（亮）/ 6.5（暗）**；而它与**下一颗**开关（组间 8pt）量到
        /// **12.0 / 11.5**。"等距"那一侧不是推测而是量过的：变异 M144 把 `captionGap` 改回 8，
        /// 帧上就报「上缝 12.0」—— 也就是 U-55 修之前那张帧的状态（上缝 = 下缝 = 12.0，归属靠猜）。

        /// 9.0 就取在 7 与 12 之间：贴着实测那一侧留 2pt 余量，离"等距"那一侧也留 3pt。
        /// 这条是**兜底**，主力是"上缝 < 下缝"那条 —— 只有最后一段说明（下面没有开关了）
        /// 只能靠这条判。
        static let captionHugMaxPt: Double = 9.0

        /// 两带之间的空缝小于它才算**同一段说明的下一行**（pt，R33 / U-55）。
        ///
        /// 三个数都是量出来的，不是推的：
        /// ① 同一段的两行之间 **3.0pt**（修之前那张帧：246.5 → 249.5）；
        /// ② 两段**不同**的说明、分在不同组里 **11.5pt**（260.0 → 271.5，也是修之前那张帧）；
        /// ③ 两段不同的说明被塞进**同一个 3pt 组**里 **6.5pt**（M145 那一支变异量到的：
        ///    226.0 → 232.5 —— 11pt 与 10pt 两种字体的行框留白不同，所以"组内"不等于"同段"）。
        /// 5.0 取在 ①与③ 之间。**这条余量薄（3.0 与 6.5 只差 3.5pt）**，
        /// 所以它红了要重量一遍再动阈值，而不是抬阈值：
        /// 抬到 7 以上，③ 那种"两段说明连着"的缺陷就会被尺并成一段而抹平（M145 正是走这条路红的）。
        static let captionLineGapMaxPt: Double = 5.0

        /// 一整族**在这台机器上**算"整体空白"的线（未绘制像素占比，R36 / BACKLOG 49）。
        ///
        /// 这条只用来回答一个机器可见的问题：这一族的帧是不是**在这里**就画不出来 ——
        /// 而不是"这是 CI 所以画不出来"。两个数都是同一份代码实测的：
        /// ① 本机 settings 族 18 张：未绘制 20.8%–78.8%（最低那张也有 20.8%）；
        /// ② runner（macos-15，run 38473962277）settings 族 18 张：**最低 90.6%**、最高 95.9%。
        /// 0.85 取在这两簇中间（离本机那一簇 6.2 个百分点、离 runner 那一簇 5.6 个百分点）。
        /// **判据是"族内每一张都超过它"**，
        /// 所以"只有某一帧空白、兄弟帧正常"这种真正的捕获缺陷不会被这条前提放行 ——
        /// 那种情况仍然走 `XCTFail`，消息里写明"不是机器不行，是这一张不行"。
        static let captureFamilyBlankFraction: Double = 0.85

        /// 一张**已知会被裁**的对照帧（`row-clipped-control`）至少该读到的底行墨占比（R37 / U-60）。
        ///
        /// 它是 `fixtureBottomInkMaxFraction` 那条线的**正对照**：同一把尺，
        /// 一边必须读到 0，另一边必须读到东西 —— 否则"十条全绿"只是尺瞎了。
        /// 0.05 的来历（本机实测）：对照帧亮档 **10.8%** / 暗档 **12.5%**，
        /// 而 mustFit 那十张全部 **0.0%** ⇒ 线取在中点偏下，两侧各留 ≥2.5 倍余量。
        /// 刻意**不再做成"这台机器画不画得出来"的前提**：R36 那一版把它做成前提，
        /// 于是"没有任何一帧压着底边"会被读成"机器不行"，而那恰恰是判据该红的第一次。
        static let bottomEdgeControlMinFraction: Double = 0.05

        /// `contentMustFit` 那批夹具允许的底行墨上限（R22 / BACKLOG 32，R37 从字面量 0.02 提成命名）。
        /// 与上面那条是一对：**同一把尺**，一边要求"读不到"，一边要求"读得到"。
        static let fixtureBottomInkMaxFraction: Double = 0.02

        /// 动作按钮的字形中心与色带中心的容差。
        /// 修之前实测偏差 0pt（单行，碰巧对）/ **−6.5pt**（两行）/ **−14.5pt**（三行），
        /// 修之后 10 条带全部 **+0.0**。3pt 是"看得见不对"与"字的光学中心本来就比几何中心高一点"之间的折中。
        static let actionCenterTolerancePt: Double = 3.0
    }

    /// 一台机器上的**捕获能力**：三条前提，全部从这一台的逐帧读数算出来（R36 / BACKLOG 49 / U-59）。
    ///
    /// 为什么是一条纯函数：它必须能在**两台机器各自的真实读数**上被一张表检验，
    /// 而本机没法同时当 CI 用。第一版不是纯函数，是把三条判断抄在 `testCaptureKeyViews` 里，
    /// 于是那三行"这台机器画不出来"的读数只能等 CI 跑一次才知道对不对 —— 而 CI 那一步
    /// 恰恰是 report-only 的，红不红都没人负责（U-59 就是这条）。
    ///
    /// 这不覆盖管线：决定"红 / 登记成 `*_NOT_RUN`"的是 `testCaptureKeyViews` 里的三处**消费者**，
    /// 管线级判据 = 那一步的日志里对应的 `*_NOT_RUN` 行出现（或该红的仍然红），
    /// 由 `scripts/ci_capture_gate.py` 在 runner 上读那份日志来判（它的正对照是
    /// `scripts/tests/fixtures/r36_runner_capture.log` —— 逐字抄的那 4 行被吞掉的红）。
    /// 这张表钉的只是：**同样的读数必须得到同样的三条前提**。
    struct CaptureCapability {
        /// 一帧的读数。`family` 只取帧名的第一段（settings / sidebar / content / …），
        /// 因为"这一族在这台机器上画不画得出来"判的是族，不是某一张帧。
        struct Reading {
            let family: String
            let transparent: Double
            let blackBandPt: Double
            /// 带着走是为了让诊断能复用同一批读数；**能力前提不看它** ——
            /// R37 之后"尺活着"不再是一条机器前提，而是由 `row-clipped-control` 那张
            /// 已知会被裁的对照帧**无条件**判（见 `bottomEdgeInkCanary`）。
            let bottomInkFraction: Double
        }

        /// settings 族在这台机器上**整体**画不出来：族内**每一张**都超过线。
        /// 只要有一张没超过，就说明这一族在这里画得出来，那一帧的空白就该红。
        let settingsFamilyIsBlank: Bool
        /// 这一台有没有出现过任何一处黑带（决定"名单里那一处消失了"这个方向能不能判）。
        let bandsSeenHere: Bool
        let settingsLowestBlank: Double

        static func measure(_ readings: [Reading]) -> CaptureCapability {
            let settings = readings.filter { $0.family == "settings" }
            return CaptureCapability(
                settingsFamilyIsBlank: settings.count >= 2
                    && settings.allSatisfy { $0.transparent > InkFloor.captureFamilyBlankFraction },
                bandsSeenHere: readings.contains { $0.blackBandPt > 0 },
                settingsLowestBlank: settings.map { $0.transparent }.min() ?? 0)
        }
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

    // MARK: - R29 · "太淡"还是"画反了"：对比度读数的方向

    /// 一块区域的尾墨落在背景的哪一侧。
    ///
    /// 存在的理由（R28 的教训，BACKLOG 41）：`inkContrast` 只报"偏离背景多远"，
    /// 于是**"画成白色的图标"（反相伪影）与"画得太淡的图标"（真缺陷）报的是同一个低值**。
    /// R28 那次差点因此去把 `.primary` 换成固定色 —— 而那正是审计第二轮禁止的方向。
    /// 这一把尺只回答一个问题：**这块区域的墨，出现在它该出现的那一侧了吗？**
    static func inkTailSplit(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                             bytesPerRow: Int, rect: CGRect, scale: Double)
        -> (brighter: Int, darker: Int, total: Int) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (0, 0, 0) }
        var luma: [Int] = []
        luma.reserveCapacity((x1 - x0) * (y1 - y0))
        for y in y0..<y1 {
            let row = y * bytesPerRow
            for x in x0..<x1 {
                let o = row + x * 4
                luma.append(Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                                 + 0.0722 * Double(bytes[o + 2])).rounded()))
            }
        }
        var histogram: [Int: Int] = [:]
        for value in luma { histogram[value / 8, default: 0] += 1 }
        let background = histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0
        // 与 `inkContrast` **同一切法**（偏离最远的那 2%）：两把尺量的必须是同一批像素，
        // 否则"这一侧"这句话就不是对那个对比度读数的说明。
        let deviation = luma.map { (abs($0 - background), $0 - background) }
            .sorted { $0.0 > $1.0 }
        let tail = deviation.prefix(max(1, luma.count / 50))
        var brighter = 0, darker = 0
        for (_, signed) in tail {
            if signed > 0 { brighter += 1 } else if signed < 0 { darker += 1 }
        }
        return (brighter, darker, tail.count)
    }

    /// **全量**（不是尾墨）按侧计数：偏离背景超过 `gate` 的像素各落在哪一侧。
    ///
    /// 为什么 `inkTailSplit` 不够用（R29d）：尾墨只取"偏离最远的那 2%"，
    /// 而一块**同时**压着选中行白字与未选中行黑字的侧栏列里，
    /// 白字的偏离（≈200）会把黑字的偏离（≈24）全部挤出那 2% ——
    /// 于是尾墨尺报"墨在期望侧 ✓"，而那五行字在帧里其实**一个字都看不见**。
    /// 尾墨问"最强的那些像素在哪一侧"，这一把问"**看得见的字一共有几个、在哪一侧**"。
    /// 同一块区域、同一个背景取法（8 级量化众数），两把尺的差别只在切多少像素。
    static func inkSideCounts(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                              bytesPerRow: Int, rect: CGRect, scale: Double, gate: Int = 16)
        -> (brighter: Int, darker: Int) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (0, 0) }
        func lumaAt(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        var histogram: [Int: Int] = [:]
        for y in y0..<y1 {
            for x in x0..<x1 { histogram[lumaAt(x, y) / 8, default: 0] += 1 }
        }
        let background = histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0
        var brighter = 0, darker = 0
        for y in y0..<y1 {
            for x in x0..<x1 {
                let signed = lumaAt(x, y) - background
                if signed > gate { brighter += 1 } else if signed < -gate { darker += 1 }
            }
        }
        return (brighter, darker)
    }

    // MARK: - 卡片竖向节奏（R95 / 设置「快捷键」分区逐元素重判）

    /// 内容列里**一行**的身份：卡片外的页面底、卡片自己的填充、卡片上的墨、卡片里的分隔线。
    enum CardRowKind: Equatable {
        case outside, card, ink, line
    }

    /// 把内容列逐行分类。参照是**整块卡片那一个稳定的填充色**（取带子里第一个"不是页面底"的行的众数），
    /// 不是抄来的色号，也不是"这一行自己的众数"（后者在分隔线上会翻车，见下面那段）。
    ///
    /// `pageLuma` 由调用方按**当前外观**给，而不是让尺自己取扫描带的第一行：
    /// 取第一行看着更"自适应"，但它会把"卡片顶到了窗口边"这一种故障读成"整带都在卡片里"，
    /// 于是节奏照样算得出、只是全错。故障改由 `cardRhythm` 的 `card.0 > 0` 那条前提挡。
    ///
    /// 两档门槛的出处：`inkGate=60` 落在"分隔线"与"任何一种墨"之间 ——
    /// 仓库尺 `rowTierProfile` 那条注释里有两个本机量过的数（说明档离底 ≈109、标题档 ≈209），
    /// 而分隔线是"整行都浅一度"的那一档，比它们都低一个量级；60 不在两者之间就会把线读成墨、
    /// 或把说明读成线。`lineGate=6` 的下界由**亮档卡片对页面底只有 8** 定：
    /// 再松就把卡片外的那两条页面带算进"整行的线"，再紧就漏线。
    /// （这两格都不是"最优阈值"，是"两个已量到的档之间的那一段"—— R18 那条"自适应阈值等于没有阈值"。）
    static func cardRowKinds(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                             bytesPerRow: Int, rect: CGRect, scale: Double,
                             pageLuma: Int, inkGate: Int = 60, lineGate: Int = 6)
        -> [CardRowKind] {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return [] }
        func lumaAt(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        // 第一遍：每行的众数。第二遍才分类 —— 因为**参照必须是整块卡片稳定的那一个填充色**，
        // 不能是"这一行自己的众数"。第一版就是那么写的，于是分隔线那一行的众数=线本身，
        // 线与自己的偏离是 0 ⇒ 一条线都检不出来（读数 `分隔线=0`，而边距那一栏照样给得出 14.5，
        // 一把一半好一半坏的尺 —— R95 里第三次撞上这一课）。
        var modals: [Int] = []
        modals.reserveCapacity(y1 - y0)
        for y in y0..<y1 {
            var histogram: [Int: Int] = [:]
            for x in x0..<x1 { histogram[lumaAt(x, y) / 8, default: 0] += 1 }
            modals.append(histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0)
        }
        guard let fill = modals.first(where: { abs($0 - pageLuma) > 3 }) else {
            return Array(repeating: .outside, count: y1 - y0)
        }
        var kinds: [CardRowKind] = []
        for (row, modal) in modals.enumerated() {
            let y = y0 + row
            if abs(modal - pageLuma) <= 3 && abs(modal - fill) > 3 {
                kinds.append(.outside)
                continue
            }
            var ink = 0, line = 0
            for x in x0..<x1 {
                let dev = abs(lumaAt(x, y) - fill)
                if dev >= inkGate { ink += 1 } else if dev >= lineGate && dev < lineGate * 8 { line += 1 }
            }
            if ink >= 8 { kinds.append(.ink) }
            else if line >= (x1 - x0) * 8 / 10 { kinds.append(.line) }
            else { kinds.append(.card) }
        }
        return kinds
    }

    /// 纯函数：从逐行分类里读出「卡片四边的留白」与「分隔线两侧的留白」（pt）。
    ///
    /// 缺陷形状是这一族里最不容易靠眼睛抓到的：卡片**自己**没错，每一行也都没错，
    /// 错的是同一张卡片里存在两种留白（内侧 14.5pt、边缘 6.5pt）。
    /// 所以判据必须是"这几个数是不是同一个数"，而不是"这个数够不够大" ——
    /// 后者会被"整体都很挤"骗过去，前者不会。
    static func cardRhythm(rows: [CardRowKind], scale: Double)
        -> (edges: [Double], gaps: [Double], dividers: Int) {
        var runs: [(Int, Int)] = []
        var start = -1
        for (i, kind) in rows.enumerated() {
            if kind != .outside {
                if start < 0 { start = i }
            } else if start >= 0 {
                runs.append((start, i - 1))
                start = -1
            }
        }
        if start >= 0 { runs.append((start, rows.count - 1)) }
        guard let card = runs.max(by: { $0.1 - $0.0 < $1.1 - $1.0 }), card.0 > 0,
              card.1 < rows.count - 1 else { return ([], [], 0) }
        // 卡片必须**整块**落在扫描带里：顶到带上沿 = 上面那条 `card.0 > 0` 不成立，
        // 那时"上留白"没有对象，宁可返回空让调用处报"尺没压住卡片"。
        let slice = Array(rows[card.0...card.1])
        guard let firstInk = slice.firstIndex(of: .ink),
              let lastInk = slice.lastIndex(of: .ink) else { return ([], [], 0) }
        let unit = 1.0 / max(scale, 1)
        var gaps: [Double] = []
        var dividers = 0
        var i = 0
        while i < slice.count {
            guard slice[i] == .line else { i += 1; continue }
            var j = i
            while j + 1 < slice.count, slice[j + 1] == .line { j += 1 }
            dividers += 1
            var up = i - 1
            while up >= 0, slice[up] != .ink { up -= 1 }
            var down = j + 1
            while down < slice.count, slice[down] != .ink { down += 1 }
            // 留白数的是**空行**：从上一行墨到这一行线之间，中间那几条不带墨的行。
            if up >= 0 { gaps.append(Double(i - up - 1) * unit) }
            if down < slice.count { gaps.append(Double(down - j - 1) * unit) }
            i = j + 1
        }
        return ([Double(firstInk) * unit, Double(slice.count - 1 - lastInk) * unit],
                gaps, dividers)
    }

    /// **一行里的墨分两档**：说明档（离背景 ≤ `tierSplit`）与标题档（超过它）。
    /// 返回按**像素行**排列的数组，只数偏离超过 `textInkMinDelta` 的笔画像素。
    ///
    /// 这一把尺回答的问题是「**这一行是哪种字**」，不是「这一行有没有字」。
    /// 物理依据很硬：抗锯齿只会把笔画像素往**背景方向**拉，永远不会拉得比字本身更深，
    /// 所以一行字的 `maxDeviation` 就是它那档颜色的指纹 ——
    /// 同一页上 `.secondary` 的 11pt 说明 ≈109、`.headline` 标题 ≈209（R28 在本机量到的两个数，
    /// 记在 `textInkMinDelta` 上面那段）。
    ///
    /// 为什么 R33 要新加它：说明段探针表里我按 `rows` 剖面放的两个框，读数 13.76 =
    /// **参照的 3.67 倍** —— 那不是"说明文字很浓"，是框套到了标题上。
    /// 只加"不许比参照深"的天花板还不够：**放框的时候**就得知道哪一行是说明段，
    /// 否则一轮下来只是把同一个错法换个方向再犯一次。这一把就是"放框用的"，
    /// 天花板那条是"守着的"。
    static func rowTierProfile(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                               bytesPerRow: Int, rect: CGRect, scale: Double,
                               tierSplit: Int = 150) -> [(yPx: Int, maxDeviation: Int,
                               caption: Int, title: Int)] {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y0 < y1 else { return [] }
        func lumaAt(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        var histogram: [Int: Int] = [:]
        for y in y0..<y1 {
            for x in x0..<x1 { histogram[lumaAt(x, y) / 8, default: 0] += 1 }
        }
        // 背景取**整块矩形**的众数（与 `inkSideCounts`、`textInkMass` 同一条取法）：
        // 逐行取众数会让"字多的那一行"把自己的墨当成底，于是那一行的偏离量集体塌到 0。
        let background = histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0
        var rows: [(yPx: Int, maxDeviation: Int, caption: Int, title: Int)] = []
        for y in y0..<y1 {
            var maxDeviation = 0, caption = 0, title = 0
            for x in x0..<x1 {
                let deviation = abs(lumaAt(x, y) - background)
                guard isTextInk(delta: deviation) else { continue }
                maxDeviation = max(maxDeviation, deviation)
                if deviation > tierSplit { title += 1 } else { caption += 1 }
            }
            if caption + title > 0 { rows.append((y, maxDeviation, caption, title)) }
        }
        return rows
    }

    /// 把 `rowTierProfile` 的逐行数据合并成**文字带**（一行字 / 一段多行说明的每一行）。
    ///
    /// `mergeGapPx` 默认 2px（@2x 下 1pt）：一行 CJK 文字中间也可能出现"整行没有墨"的那一像素
    /// （比如两个字之间的空隙正好跨满一行），不合就会把一行读成两行。
    /// 而**行与行之间**的空缝实测 3pt = 6px @2x ⇒ 2px 的容差不会把两段字并成一段，
    /// 这一点是这条合并规则的**唯一目的**：带的边界要能用来量间距。
    static func textBands(rows: [(yPx: Int, maxDeviation: Int, caption: Int, title: Int)],
                          scale: Double, mergeGapPx: Int = 2)
        -> [(startPt: Double, endPt: Double, maxDeviation: Int, caption: Int, title: Int)] {
        var bands: [(startPt: Double, endPt: Double, maxDeviation: Int, caption: Int, title: Int)] = []
        var group: [(yPx: Int, maxDeviation: Int, caption: Int, title: Int)] = []
        func flush() {
            guard let first = group.first, let last = group.last else { return }
            bands.append((Double(first.yPx) / scale, Double(last.yPx + 1) / scale,
                          group.map(\.maxDeviation).max() ?? 0,
                          group.reduce(0) { $0 + $1.caption }, group.reduce(0) { $0 + $1.title }))
            group = []
        }
        for row in rows {
            if let last = group.last, row.yPx - last.yPx > mergeGapPx { flush() }
            group.append(row)
        }
        flush()
        return bands
    }

    /// 哪些设置页帧的**暗档侧栏文字**落在背景的错误一侧（R29d / BACKLOG 45）。
    ///
    /// 这不是产品判据，是**尺的盲区名单** —— 与 R18 的 `materialBlindSpotFixtures` 同一族：
    /// 名单外的帧冒出反侧墨 ⇒ 又多一处"看着拍到了、其实那几行字不可见"；
    /// 名单里的帧不再冒 ⇒ 那一处能读了（或者有人动了上色），两种都必须真的去看那张帧。
    /// 名单里的帧**不能**拿侧栏未选中行的可读性当证据。
    static let darkSidebarTextBlindSpots: Set<String> = [
        "settings-general", "settings-shortcuts", "settings-privacy",
        "settings-recommendations", "settings-data", "settings-stats",
        "settings-min", "settings-privacy-excluded", "settings-stats-populated",
        // R39 新增的两张（禁用态 / 失败回执）也进名单 —— 这条不是"顺手补名单"：
        // 先看了那张帧（`/tmp/r39-crops/r39-settings-general-login-unsupported-dark-sidebar.png`）：
        // 暗档侧栏里"快捷键 / 隐私 / 推荐 / 数据 / 统计"五枚标签**黑字黑底看不见**，
        // 而选中的"通用"是白字蓝底（强调色走固定色，不受 vibrancy 极性影响），图标也看得见。
        // 与 R29d/R30 那张是同一个机制（D-090：合成前的极性），所以记为盲区而不是缺陷。
        // 名单由 `testDarkSettingsSidebarTextIsACountedBlindSpot` 的 vibrant 前提决定，手改不改得绿。
        "settings-general-login-unsupported", "settings-general-login-failed",
    ]

    /// 侧栏那一列"文字应当出现的位置"（pt）。
    /// 左边界从 40 起：图标列在 12–34，把图标框进来会让"符号的固定色"混进这条读数，
    /// 那是 BACKLOG 41 那半条要单独判的事。右边界 142 = 侧栏宽 148 留 6pt 内边距。
    static let settingsSidebarTextColumn = CGRect(x: 40, y: 96, width: 102, height: 154)

    /// **同一张帧的内容区**（x 160 起：侧栏宽 148 + 分栏线）。
    /// 这一块的用途不是判产品，是**分辨"这台机器拍不出这一页"和"我这把尺瞎了"** ——
    /// 前者 BACKLOG 43 已经实测过（runner 上 `SettingsView` 整页是一块平涂底色），
    /// 后者是 R29d 刚在 `.scratch` 那把尺上犯过的错（`modalColor` 把 pt 当 px，
    /// 于是框其实没压住字，却报出一个像结论的数）。两种情况修法完全相反。
    static let settingsContentPane = CGRect(x: 160, y: 70, width: 400, height: 200)

    /// R30 诊断（**不判产品，只问产物**）：暗档设置帧里侧栏那一列，到底是哪些视图在画。
    ///
    /// 为什么需要它：R29d 在仓库外搭了十五臂复刻体，**每一臂都画对**
    /// （List 侧栏 / 嵌套 `NSHostingView`+`NSSplitView` / `Button{Label}+.plain` /
    /// 显式 `.primary` / 运行时翻外观 / 给嵌套视图钉外观 …）。
    /// 继续在外面猜形状就是浪费轮次 —— 这一条直接把产品那棵已布局、未开画的树打印出来：
    /// 谁压在那一列上、它自己声明的外观是什么、它携带的颜色对象在两种外观下各解析成什么。
    /// 判据在 `testDarkSettingsSidebarTextIsACountedBlindSpot`；这条只负责把机制往前推一步。
    func testSettingsSidebarSubtreeWhoDrawsTheColumnDiagnostic() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r30-subtree-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        guard let fixture = fixtures(appearance: .darkAqua).first(where: { $0.name == "settings-general" }) else {
            return XCTFail("找不到 settings-general ⇒ 这条诊断没有对象")
        }
        let column = Self.settingsSidebarTextColumn
        var report: [String] = []
        _ = try render(fixture, appearance: .darkAqua,
                       to: scratch.appendingPathComponent("settings-general.png")) { host in
            @MainActor func resolved(_ color: NSColor?) -> String {
                guard let color else { return " 色=nil" }
                func under(_ name: NSAppearance.Name) -> String {
                    guard let appearance = NSAppearance(named: name) else { return "?" }
                    var out = "?"
                    appearance.performAsCurrentDrawingAppearance {
                        guard let rgb = color.usingColorSpace(.deviceRGB) else { return }
                        out = "\(Int(rgb.redComponent * 255)),"
                            + "\(Int(rgb.greenComponent * 255)),\(Int(rgb.blueComponent * 255))"
                    }
                    return out
                }
                return " 色 aqua=(\(under(.aqua)))/dark=(\(under(.darkAqua)))"
            }
            @MainActor func walk(_ view: NSView, depth: Int) {
                let frame = view.convert(view.bounds, to: nil)
                let cls = String(describing: type(of: view))
                let covers = frame.intersects(column)
                let isHosting = cls.contains("Hosting")
                let isText = view is NSTextField
                let isButton = view is NSButton
                let isImage = view is NSImageView
                if (covers && (isText || isButton || isImage)) || (isHosting && depth > 0) {
                    let tag = isText ? "文字" : isButton ? "按钮" : isImage ? "图像" : "hosting"
                    report.append(String(format: "%@#%d %@ [%@] 框=(%.0f,%.0f,%.0f,%.0f) 自带外观=%@ 生效=%@",
                                         String(repeating: "  ", count: min(depth, 10)), depth, tag, cls,
                                         frame.minX, frame.minY, frame.width, frame.height,
                                         view.appearance?.name.rawValue ?? "nil",
                                         view.effectiveAppearance.name.rawValue)
                        + (isText ? resolved((view as! NSTextField).textColor) : ""))
                }
                if depth < 18 { view.subviews.forEach { walk($0, depth: depth + 1) } }
            }
            walk(host, depth: 0)
        }
        emit("SUBTREE settings-general dark：压在侧栏文字列上 / 嵌套的视图共 \(report.count) 个")
        report.prefix(80).forEach { emit("  \($0)") }
        throw XCTSkip("诊断用判据：它只回答「这一列是谁画的、它携带的颜色在两种外观下各解析成什么」，"
                      + "不判产品 ⇒ 永远记为未运行，避免被当成一条通过的验收（BACKLOG 45）")
    }

    /// 放框诊断要扫的夹具（R35 点名剩余 `.secondary` 位点时用）。
    static let captionPlacementDiagnosticFixtures: [String] = [
        "settings-general", "settings-shortcuts", "settings-privacy", "settings-data",
        "settings-recommendations",
        "settings-stats-populated", "sidebar-history", "detail-0-text",
        // R39：禁用态与失败回执那两张 —— 放框要从帧上量，不照抄别处的 y
        "settings-general-login-unsupported", "settings-general-login-failed",
        // 快速选择浮层**不在这里**：102 张基线里一张 `quickpick-*` 都没有（已记的账 BACKLOG 30 /
        // U-39 / U-41 —— 那是 AppKit 自建的 NSPanel，R19 试过把 contentView 搬进别的窗口，
        // 搬过去就塌成空壳）。列一个不存在的夹具名只会让这条诊断红成"找不到对象"，
        // 那种红说的是我的清单，不是产品的表面。

    ]

    /// 每张夹具里"文字可能出现的区域"（pt）。
    /// 设置页要跳过左侧那一列（R29d/R30：那一列在 vibrant 子树里解析颜色，暗档不可信），
    /// 其余表面各给一块自己内容的包围盒 —— 区域不是审美选择，它决定"这一带算不算画出来了"。
    static func rowProfileRect(for fixture: String) -> CGRect {
        if fixture.hasPrefix("settings-") { return CGRect(x: 150, y: 20, width: 560, height: 500) }
        switch fixture {
        // 侧栏只量**文字列**（x 130 起）：x 40..100 那一列是类型图标，
        // 它本身就是 `.secondary`（R21 判过），会把"说明档带"打成一堆假候选 ——
        // R35 第一条 sidebar 探针就是这么放到了图标上（M155 逃过一次才暴露，见那条电池）。
        case "sidebar-history": return CGRect(x: 130, y: 20, width: 170, height: 500)
        case "detail-0-text": return CGRect(x: 0, y: 20, width: 720, height: 500)
        default: return CGRect(x: 0, y: 0, width: 10_000, height: 10_000)
        }
    }

    /// R33 诊断（**放框用的，不判产品**）：设置页内容列里每一行是**哪种字**。
    ///
    /// 为什么需要它：`captionInkProbes` 里给通用页放的两个框，读数 13.76 = 参照的 3.67 倍，
    /// 也就是说框套在 `.headline` 标题上而不是说明段上 —— 而"框从 `rows` 剖面放"这句话
    /// 本身就是错的：普通的行剖面只说"这一行有墨"，**说不出这一行是标题还是说明**，
    /// 于是我照着它放的两个框都落在标题行上，还都判成了"通过"。
    /// 这一条把 `rowTierProfile` 的行合并成带，逐带打出 `最深偏离 / 说明档像素 / 标题档像素`，
    /// 于是"这里是一条 `.secondary` 说明段"变成量出来的，不是猜出来的。
    /// 判据在 `testCaptionTextStaysOnTheSecondaryTier`（R33 起那里多了一条天花板）。
    func testSettingsCaptionRowTierProfileDiagnostic() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r33-rowtier-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for name in Self.captionPlacementDiagnosticFixtures {
            guard let fixture = fixtures(appearance: appearance)
                .first(where: { $0.name == name }) else {
                return XCTFail("找不到 \(name) ⇒ 这一带的行剖面没有对象")
            }
            let file = scratch.appendingPathComponent("\(name)-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("读不回刚拍的 \(file.lastPathComponent)")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            let profileRect = Self.rowProfileRect(for: name)
            let rows = Self.rowTierProfile(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                           bytesPerRow: rep.bytesPerRow,
                                           rect: profileRect, scale: scale)
            emit("ROWTIER \(name) \(tag)：有字行 \(rows.count) 行（区域 x \(Int(profileRect.minX))..\(Int(profileRect.maxX))、y \(Int(profileRect.minY))..\(Int(profileRect.maxY))）")
            for band in Self.textBands(rows: rows, scale: scale) where band.title == 0 && band.caption > 0 {
                emit(String(format: "  说明档带 y=%.1f..%.1f pt 最深偏离=%d 说明=%d",
                             band.startPt, band.endPt, band.maxDeviation, band.caption))
            }
            }
        }
        throw XCTSkip("诊断用判据：它只回答「这一行是标题档还是说明档」，用来放框，不判产品 "
                      + "⇒ 永远记为未运行，避免被当成一条通过的验收（BACKLOG 45）")
    }

    /// R34 诊断（**量行为，不判产品**）：菜单栏面板给不同宽度时，那一行**截不截**。
    ///
    /// 起因（U-56 / BACKLOG 47）：R33 看帧发现第一行的推荐理由**被硬切成半字** ——
    /// 墨画到 `x=319.5`，而帧宽 320。而 `menuBarFrame` 里那个 `.frame(width: 320)`
    /// 是**夹具**写的，产品侧 `MenuBarExtra` 的内容没有任何宽度约束（`App.swift:24`）。
    /// 所以"面板多宽"这件事现在没人声明，而两种解释要分开：
    /// ① 行会截断（`lineLimit(1)` 生效）⇒ 320 只是太窄，半字其实是省略号，改夹具宽度就行；
    /// ② 行不截断、整块溢出被窗口裁 ⇒ 这是**产品**的布局缺陷，声明宽度也不会自己好。
    /// 这一条把同一份数据摆在 320 / 400 / 520 / 720 四档宽度下各拍一张，
    /// 打"最右一列有墨的 x"：跟着宽度走 = ①，钉在同一个值上 = ②。
    func testMenuBarRowTruncationAcrossWidthsDiagnostic() throws {
        guard #available(macOS 13, *) else {
            throw XCTSkip("菜单栏夹具本来就要 macOS 13 ⇒ 这台机器上这条诊断没有对象")
        }
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r34-menubar-width-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        let store = makePopulatedStore()
        store.refreshPredictions()
        waitUntil("菜单栏面板需要候选") { !store.predictionSuggestionEntries.isEmpty }
        waitUntil("推荐刷新要收尾") { !store.isRefreshingPredictions }
        let appDelegate = AppDelegate(historyStore: store)
        for width in [320.0, 400.0, 520.0, 720.0] {
            let fixture = Fixture("menubar-width-\(Int(width))", NSSize(width: width, height: 320)) {
                AnyView(
                    MenuBarRecommendationsView(historyStore: store, appDelegate: appDelegate)
                        .padding(.vertical, 6)
                        .frame(width: width, alignment: .topLeading)
                        .background(Color(nsColor: .windowBackgroundColor))
                )
            }
            let file = scratch.appendingPathComponent("menubar-width-\(Int(width)).png")
            _ = try render(fixture, appearance: .aqua, to: file) { host in
                emit("MENUBAR_FITTING 声明宽=\(Int(width)) hosting.fittingSize="
                      + String(format: "%.1fx%.1f", host.fittingSize.width, host.fittingSize.height))
            }
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("读不回刚拍的 \(file.lastPathComponent)")
            }
            let scale = Double(rep.pixelsWide) / Double(width)
            // **带只框住第一行推荐（y 156..172）**。第一版把 y 60..310 整段都框进来，
            // 于是四档宽度量到的是同一个答案"墨顶到最后一列" —— 那把尺读到的是面板里
            // 那两条**横贯全宽的 `Divider()`**，不是文字。同一族错误第三次出现：
            // 尺报"有墨"之前，得先确认那一列的墨是**谁**画的（这里靠把带收窄到一行文字的高度）。
            let rowBand = CGRect(x: 0, y: 156, width: width, height: 16)
            let trailing = Self.trailingInkColumn(bytes: base, width: rep.pixelsWide,
                                                  height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                  rect: rowBand, scale: scale, minDelta: 60)
            let leading = Self.leadingInkColumn(bytes: base, width: rep.pixelsWide,
                                                height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                rect: rowBand, scale: scale, minDelta: 60)
            emit(String(format: "MENUBAR_WIDTH 声明宽=%d 带=y156..172 最左墨=%@ 最右墨=%@ ⇒ 右边距=%@",
                         Int(width),
                         leading.map { String(format: "%.1f", $0) } ?? "无",
                         trailing.map { String(format: "%.1f", $0) } ?? "无",
                         trailing.map { String(format: "%.1f", width - $0) } ?? "无"))
        }
        throw XCTSkip("诊断用判据：它只回答「这一行在给定宽度下截不截」，用来定修法，不判产品 "
                      + "⇒ 永远记为未运行，避免被当成一条通过的验收（BACKLOG 45）")
    }

    /// 菜单栏那三张帧**不是产品那个表面**（R34 / U-56 收回）。
    ///
    /// 事实来自产品自己的注释（`MenuBarRecommendationsView.swift` 里 R5 写下的那一段，
    /// 账本 D-055 / M15 实测）：`MenuBarExtra` 没有设 `.menuBarExtraStyle(.window)`
    /// ⇒ 默认风格 `.menu` ⇒ 这棵 SwiftUI 树被编译成**真的 `NSMenu` + `NSMenuItem.view`**。
    /// 而夹具拍的是"同一棵树塞进一个离屏 `NSHostingView` 窗口"。两件事因此不是一件事：
    /// 真菜单里 item view 不会溢出菜单自己的宽度（菜单会截），
    /// 而复刻里那一行**溢出到帧边界** —— R34 实测：320 宽的帧里推荐理由的墨画到 `x=320.0`，
    /// 最后一列还有 7.5pt 高的笔画（不是省略号那 2pt 的点）。
    /// 于是 R33 由"看帧"得到的那句 **产品的理由被切成半字** 不成立：
    /// 它量的是复刻的溢出，不是产品的截断。
    ///
    /// 这份名单就是把这件事钉成机器可读的一条规矩：
    /// **`menubar-*` 这些帧可以判颜色档（档不依赖表面），不可以判宽度 / 截断 / 对齐 / 命中区。**
    /// 名单与前提都由 `testMenuBarFramesAreReplicasOfTheMenuSurface` 现推 ——
    /// 加一张新的 `menubar-` 帧而不声明它、或者产品换成 `.window` 风格，两种都会红。
    static let menuSurfaceReplicaFixtures: Set<String> = [
        "menubar-recommendations", "menubar-empty", "menubar-refreshing",
    ]

    /// 读一份产品源码（与 `Round3DetailTypographyTests` 同一套找法）。
    /// 找不到文件**红**而不是跳过：一个会跳过的守卫和一个通过的守卫在报表里长得一样。
    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "UICaptureHarness", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }

    /// R34 · 菜单栏帧的**资格**：它们是菜单表面的复刻，不是菜单本身。
    ///
    /// 三条一起：
    /// ① 前提（源码）：产品里 `MenuBarExtra` 仍在，且没有 `.menuBarExtraStyle(.window)`；
    /// ② 名单 ≡ 由前缀推导的那批夹具（新增不声明 ⇒ 红；删掉 ⇒ 红）；
    /// ③ 证据（帧）：复刻里第一行的墨**顶到帧的最后一列** —— 这条既是"为什么不能判截断"的理由，
    ///    也是这条规矩的活体：哪天复刻不再顶边，它红了，人要重新判"现在能不能拿它判截断"。
    func testMenuBarFramesAreReplicasOfTheMenuSurface() throws {
        let appSource = try productSource(named: "App.swift")
            .components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        XCTAssertTrue(appSource.contains("MenuBarExtra("),
                      "产品里已经没有 `MenuBarExtra(` 了，但 `menubar-*` 这批帧还在拍 ⇒ 这些帧在拍一个不存在的表面")
        XCTAssertFalse(appSource.contains("menuBarExtraStyle(.window)"),
                       "产品已经把菜单栏内容换成 `.window` 风格 ⇒ 这些帧**就是产品本身**了："
                       + "把 `menuSurfaceReplicaFixtures` 缩掉，并且把宽度 / 截断 / 对齐这几条结论重新审一遍"
                       + "（它们以前不是量不到产品，是量的是另一个表面）")

        let derived = Set(fixtures(appearance: .aqua).map { $0.name }.filter { $0.hasPrefix("menubar-") })
        XCTAssertEqual(derived, Self.menuSurfaceReplicaFixtures,
                       "菜单栏帧的名单与夹具不一致：只出现在夹具里的是 \(derived.subtracting(Self.menuSurfaceReplicaFixtures).sorted())，"
                       + "只出现在名单里的是 \(Self.menuSurfaceReplicaFixtures.subtracting(derived).sorted()) ⇒ "
                       + "新加的 `menubar-` 帧必须先声明它是不是同一个盲区（这些帧不许拿来判宽度/截断），"
                       + "撤掉的帧要把名单一起收掉")

        guard let fixture = fixtures(appearance: .aqua)
            .first(where: { $0.name == "menubar-recommendations" }) else {
            return XCTFail("找不到 menubar-recommendations ⇒ 这条资格判据没有对象")
        }
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r34-menu-replica-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        let file = scratch.appendingPathComponent("menubar-recommendations.png")
        _ = try render(fixture, appearance: .aqua, to: file)
        guard let image = NSImage(contentsOf: file),
              let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
              let base = rep.bitmapData else {
            return XCTFail("读不回刚拍的 \(file.lastPathComponent)")
        }
        let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
        // 带只框第一行推荐（y 156..172）：整段框进来会读到两条横贯全宽的 `Divider()`，
        // 那会把"最右墨 = 帧边界"读成每条帧都成立（R34 第一次跑就是这么被骗过的）。
        let rowBand = CGRect(x: 0, y: 156, width: fixture.size.width, height: 16)
        guard let trailing = Self.trailingInkColumn(bytes: base, width: rep.pixelsWide,
                                                    height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                    rect: rowBand, scale: scale, minDelta: 60) else {
            return XCTFail("第一行推荐里读不到任何墨 ⇒ 复刻坏了或者带放错了（先量带，别改阈值）")
        }
        XCTAssertGreaterThanOrEqual(trailing, fixture.size.width - 1.0,
                    "复刻里第一行的最右墨在 \(String(format: "%.1f", trailing))pt，而帧宽 "
                    + "\(String(format: "%.0f", fixture.size.width))pt ⇒ 这一行**不再顶到帧边界**了。"
                    + "两种可能：①有人给行加了右边距/宽度约束（那这些帧也许已经能判截断，"
                    + "重新判一次并把 `menuSurfaceReplicaFixtures` 收掉）；"
                    + "②布局又漂了（那先确认漂在哪）。两种都不许只把这条断言放宽。")
        emit("MENUBAR_REPLICA menubar-recommendations 第一行最右墨="
              + String(format: "%.1f", trailing) + " / 帧宽 "
              + String(format: "%.0f", fixture.size.width)
              + " ⇒ 复刻顶到帧边界，产品是 NSMenu（.menu 风格）⇒ 这批帧不判宽度/截断/对齐")
    }

    /// 已经知道"压在 vibrant 子树上"的**控件**探针（R35 逐条量出来的，不是推的）。
    ///
    /// 为什么还留着：这条读数不是没有值，是**值不属于产品** —— `cacheDisplay` 不做 vibrancy 合成，
    /// 于是那一列的颜色是合成前的。它 14.56 / 12.43 的对比度比产品真机上高还是低，
    /// 在有一条合成后的取图通道之前（R31 已证离屏没有）**无法知道**，所以只能记成盲区而不是缺陷。
    /// 名单由 `testProbesDoNotSitOnVibrantColumns` 从产物现推：多一条会红，少一条也会红。
    static let vibrantResolvedControlProbes: Set<String> = [
        "sidebar-multi-select/批量操作按钮（侧栏工具排）",
    ]

    /// R35 · **探针的颜色域资格**：档与对比度只能判在"产品那个颜色域"里。
    ///
    /// 起因是 M155 逃过一次：我给 `sidebar-history` 的"列表行第二行 meta"放了一条说明段探针，
    /// 把产品那行改成 `.tertiary` 之后判据全绿。顺着查到的不是框放错，而是**整帧颜色域不同**：
    /// 侧栏那一列的 `.primary` 行标题最深 (113,113,113)，与旁边 `.secondary` 的 meta 一样深，
    /// 而设置页内容列同样 `.primary` 的标签最深 (38,38,38)。R30 量过的 vibrant 机制
    /// 当时只记在"暗档设置页侧栏"那一格上 —— 这一条把它推广成**逐条探针问一遍**：
    /// 亮档也算，主窗口的侧栏也算。
    ///
    /// 两条规矩：
    /// ① **说明段表里一条都不许压在 vibrant 子树上**（无例外 —— 档这个量在合成前不是产品那个量）；
    /// ② 控件表里允许，但必须点名登记在 `vibrantResolvedControlProbes`，
    ///    多一条红、少一条也红，并且红的时候要说清楚"这不是缺陷，是这条读数不属于产品"。
    func testProbesDoNotSitOnVibrantColumns() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r35-probe-domain-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var pendingCaption: [(probe: InkProbe, vibrant: String?)] = []
        var pendingControl: [(probe: InkProbe, vibrant: String?)] = []
        var captionViolations: [String] = []
        var controlVibrant: Set<String> = []
        var checked = 0
        var judged = 0
        var notRun: [String] = []
        // 这一族在这里画不画得出来，由**这台机器自己量**（`CaptureCapability` 的第二个消费者 ——
        // 它不是为"捕获那一步"量身定做的借口机器）。
        var capabilityReadings: [CaptureCapability.Reading] = []

        func askVibrant(_ probe: InkProbe, _ fixture: Fixture, _ appearance: NSAppearance.Name,
                        suffix: String) throws -> String? {
            var vibrant: String?
            let metrics = try render(fixture, appearance: appearance,
                                     to: scratch.appendingPathComponent("\(probe.fixture)\(suffix).png")) { host in
                vibrant = Self.vibrantAppearanceCovering(host, column: probe.rect)
            }
            capabilityReadings.append(CaptureCapability.Reading(
                family: fixture.name.components(separatedBy: "-").first ?? "",
                transparent: metrics.transparent, blackBandPt: metrics.blackBandPt,
                bottomInkFraction: metrics.bottomInkFraction))
            return vibrant
        }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            for probe in Self.captionInkProbes {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == probe.fixture }) else {
                    return XCTFail("找不到夹具 \(probe.fixture) ⇒ 资格判据没有对象")
                }
                checked += 1
                pendingCaption.append((probe, try askVibrant(probe, fixture, appearance, suffix: "")))
            }
            for probe in Self.controlInkProbes {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == probe.fixture }) else {
                    return XCTFail("找不到夹具 \(probe.fixture) ⇒ 资格判据没有对象")
                }
                checked += 1
                pendingControl.append((probe, try askVibrant(probe, fixture, appearance, suffix: "-c")))
            }
        }
        // **为什么这里要放行**（run 38476332754 / 38481495523 实测：这一步在 runner 上恒红）：
        // settings 族在这台机器上 18 张**全部**未绘制 90.6–95.9%，而那棵树仍然会回答
        // "内容列压在 VibrantLight 里" —— 一个**没画出来的窗口**给出的容器答案是这台机器的窗口环境，
        // 不是产品的层级结构（本机同一批夹具画得出来，答案是"没压在 vibrant 上"，那条才是判据的对象）。
        // 所以这一族整体空白时，settings 探针的资格判据记为未运行；**其余夹具照判**。
        let capability = CaptureCapability.measure(capabilityReadings)
        func eligible(_ probe: InkProbe) -> Bool {
            !(capability.settingsFamilyIsBlank && probe.fixture.hasPrefix("settings-"))
        }
        for (probe, vibrant) in pendingCaption {
            guard let vibrant else { continue }
            if eligible(probe) {
                captionViolations.append("\(probe.fixture)/\(probe.what)（\(vibrant)）")
            } else {
                notRun.append("\(probe.fixture)/\(probe.what)（\(vibrant)）")
            }
        }
        for (probe, vibrant) in pendingControl where eligible(probe) {
            if vibrant != nil { controlVibrant.insert("\(probe.fixture)/\(probe.what)") }
        }
        judged = checked - notRun.count
        XCTAssert(checked >= 40, "只问了 \(checked) 条探针的颜色域 ⇒ 两张贴表的遍历本身坏了")
        // 地板**从表推导**，不写死数字。runner 第一次真跑（run 38485603211）：40 条里放行 20、判成 20 ——
        // 恰好压在写死的 20 上。那种"刚好过"的地板既拦不住未来（再多一族画不出来就悄悄归零），
        // 也解释不了现在（20 是谁？）。现在：可判的必须**全部**判到，另加一条"对象不许被清空"的下限。
        let mustJudge = (pendingCaption + pendingControl).filter { eligible($0.probe) }.count
        XCTAssertEqual(judged, mustJudge,
                       "非放行的那 \(mustJudge) 条必须全部真的判到 ⇒ 有 \(mustJudge - judged) 条被悄悄跳过")
        XCTAssertGreaterThanOrEqual(mustJudge, 16,
                                    "这台机器上只剩 \(mustJudge) 条可判的探针 ⇒ 这张资格判据的对象快被清空了；"
                                    + "该问的是『还剩谁值得判』，而不是把地板调低")
        XCTAssert(captionViolations.isEmpty,
                  "这些说明段探针压在 vibrant 子树上：\(captionViolations) ⇒ 拍到的是 vibrancy 合成**之前**"
                  + "的像素，「档」这个量在那一列不是产品那个量（R35 实测：侧栏 `.primary` 行标题最深 113，"
                  + "设置页内容列同样声明 `.primary` 的标签最深 38）。\n"
                  + "处置只有两种，都不许是把判据放宽：①换一个不压在 vibrant 列上的位点；"
                  + "②承认这条量不到，登记进 BACKLOG 48 并把它从表里撤掉（表里留一条假绿比少一条更糟）。")
        XCTAssertEqual(controlVibrant, Self.vibrantResolvedControlProbes,
                       "控件探针压在 vibrant 子树上的名单变了：现在量到 \(controlVibrant.sorted())，"
                       + "登记的是 \(Self.vibrantResolvedControlProbes.sorted()) ⇒ "
                       + "多出来的那条读数不属于产品（先登记再谈判不判）；"
                       + "少掉的那条意味着那一列现在能拍了（或者有人动了容器）—— 两种都要真的去看那张帧")
        if notRun.isEmpty {
            emit("PROBE_DOMAIN 问了 \(checked) 条、判成 \(judged) 条：说明段 0 条压在 vibrant 上，"
                  + "控件 \(controlVibrant.count) 条已登记（\(controlVibrant.sorted())）")
        } else {
            emit("PROBE_DOMAIN_NOT_RUN 放行 \(notRun.count) 条 —— 这一台 settings 族整体未绘制"
                  + "（族内最低 " + String(format: "%.1f", capability.settingsLowestBlank * 100) + "%）"
                  + " ⇒ 那棵树的答案是窗口环境，不是产品容器：" + notRun.joined(separator: " | "))
            emit("PROBE_DOMAIN 问了 \(checked) 条、判成 \(judged) 条：说明段 0 条压在 vibrant 上，"
                  + "控件 \(controlVibrant.count) 条已登记（\(controlVibrant.sorted())）")
        }
    }

    /// R35 诊断（**问产物，不判产品**）：每张探针框压着的子树，是不是在 vibrant 域里解析颜色。
    ///
    /// 起因是 M155 逃过一次：我把一条"列表行第二行 meta"的探针放进 `sidebar-history`，
    /// 把产品的行标题改成 `.tertiary` 判据全绿。顺着查下去量到的不是"框放错了"，而是**整帧的颜色域不同**：
    /// 同一句"这一带最深是多少"，设置页内容列的 `.primary` 标签量到 (38,38,38)（偏离 210），
    /// 而侧栏行标题量到 (113,113,113)（偏离 135）—— 与它下面那行 `.secondary` 的 meta **一模一样深**。
    /// R30 已经量过这个机制（`NSAppearanceNameVibrantDark` + `cacheDisplay` 不做 vibrancy 合成），
    /// 但当时把它记成"暗档设置页侧栏"那一格；这一条要问的是**到底哪些探针框活在 vibrant 域里**，
    /// 亮档算不算、主窗口的侧栏算不算。答案决定哪些"档 / 对比度"判据其实没有证据。
    func testProbeVibrantEligibilityDiagnostic() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r35-eligibility-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var vibrantCount = 0
        var total = 0
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for probe in Self.captionInkProbes + Self.controlInkProbes {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == probe.fixture }) else { continue }
                total += 1
                var vibrant: String?
                let file = scratch.appendingPathComponent("\(probe.fixture).png")
                _ = try render(fixture, appearance: appearance, to: file) { host in
                    vibrant = Self.vibrantAppearanceCovering(host, column: probe.rect)
                }
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else { continue }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let (ratio, coverage) = Self.inkContrast(bytes: base, width: rep.pixelsWide,
                                                         height: rep.pixelsHigh,
                                                         bytesPerRow: rep.bytesPerRow,
                                                         rect: probe.rect, scale: scale)
                if vibrant != nil { vibrantCount += 1 }
                emit(String(format: "PROBE_ELIGIBILITY %@ %@ %@ 域=%@ ratio=%.2f ink=%.1f%%",
                             tag, probe.fixture, String(probe.what.prefix(22)),
                             vibrant ?? "非 vibrant", ratio, coverage * 100))
            }
        }
        emit("PROBE_ELIGIBILITY_SUM \(vibrantCount) of \(total) 条探针压在 vibrant 子树上")
        throw XCTSkip("诊断用判据：它只回答「这条探针框压在哪个颜色域里」，用来定资格，不判产品 "
                      + "⇒ 永远记为未运行，避免被当成一条通过的验收（BACKLOG 45）")
    }

    /// R34 · 判别臂自己的**真值表**：画不出来的那一列，必须被认成画不出来。
    ///
    /// 为什么必须有它：R33 那条判别臂第一次上 CI 就答错了题 —— 它问"整帧有没有墨"，
    /// 而该问的是"探针所在那一列画没画出来"。runner 上设置页内容列是平涂（BACKLOG 43），
    /// 帧的底色与侧栏却有墨 ⇒ 整帧那一问永远答"画得出来" ⇒ 三条设置页探针全部走进
    /// "有墨却贴到空白"的红分支，**红的是判据自己**（run 38472213484）。
    /// 这种错在本机看不出来：本机什么都画得出来，两条分支只走得到一条。
    /// 所以这里造一张"这一列什么都没有"的帧当**正对照**，让那条分支非走不可。
    ///
    /// 两臂的断言强度刻意不同：
    /// ① 空白帧 ⇒ 必须判"画不出来"（与机器无关，恒成立）；
    /// ② 真设置页那一列 ⇒ 本机应当判"画得出来"；这一臂**在 runner 上本来就该是 false**，
    ///    所以它只在成立时打读数，不成立时打 `DISCRIMINATOR_ARM_B_NOT_RUN` ——
    ///    把 BACKLOG 43 那条已知事实判成缺陷，就是 R29d 犯过的那件事。
    func testNotRunDiscriminatorTruthTable() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r34-discriminator-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        let column = CGRect(x: 150, y: 0, width: 560, height: 540)

        let blank = Fixture("blank-column-720x540", NSSize(width: 720, height: 540)) {
            AnyView(Color(nsColor: .windowBackgroundColor).frame(width: 720, height: 540))
        }
        let blankFile = scratch.appendingPathComponent("blank.png")
        _ = try render(blank, appearance: .aqua, to: blankFile)
        guard let blankImage = NSImage(contentsOf: blankFile),
              let blankRep = NSBitmapImageRep(data: blankImage.tiffRepresentation ?? Data()),
              let blankBase = blankRep.bitmapData else {
            return XCTFail("读不回空白对照帧")
        }
        let blankScale = Double(blankRep.pixelsWide) / Double(blank.size.width)
        let blankInk = Self.textInkMass(bytes: blankBase, width: blankRep.pixelsWide,
                                        height: blankRep.pixelsHigh, bytesPerRow: blankRep.bytesPerRow,
                                        rect: column, scale: blankScale)
        XCTAssertFalse(Self.columnIsDrawable(textInkPixels: blankInk.pixels),
                    "一张只有平涂底的帧，判别臂却说\(blankInk.pixels) 个文字墨像素 ⇒ 那条 NOT-RUN 分支是死的。"
                    + "它一死，凡是这台机器画不出来的页面都会被红成\"框贴到空白上\"（R33 在 CI 上正是这样）")
        emit("DISCRIMINATOR_ARM_A blank 文字墨=\(blankInk.pixels) ⇒ 判为\"画不出来\"（正对照成立）")

        guard let real = fixtures(appearance: .aqua).first(where: { $0.name == "settings-general" }) else {
            return XCTFail("找不到 settings-general ⇒ 反臂没有对象")
        }
        let realFile = scratch.appendingPathComponent("settings-general.png")
        _ = try render(real, appearance: .aqua, to: realFile)
        guard let realImage = NSImage(contentsOf: realFile),
              let realRep = NSBitmapImageRep(data: realImage.tiffRepresentation ?? Data()),
              let realBase = realRep.bitmapData else {
            return XCTFail("读不回刚拍的真实帧")
        }
        let realScale = Double(realRep.pixelsWide) / Double(real.size.width)
        let realInk = Self.textInkMass(bytes: realBase, width: realRep.pixelsWide,
                                       height: realRep.pixelsHigh, bytesPerRow: realRep.bytesPerRow,
                                       rect: column, scale: realScale)
        if Self.columnIsDrawable(textInkPixels: realInk.pixels) {
            emit("DISCRIMINATOR_ARM_B settings-general 内容列文字墨=\(realInk.pixels) ⇒ 判为\"画得出来\"")
        } else {
            emit("DISCRIMINATOR_ARM_B_NOT_RUN settings-general 内容列 0 个文字墨像素"
                  + " ⇒ 这台机器画不出这一页（BACKLOG 43 的已知事实，不算缺陷）；"
                  + "这条判据的设置页探针在这台机器上记为未运行")
        }
    }

    /// R33 · `rowTierProfile` 的**真值表**：同一张设置页帧里，
    /// 一行说明段与一行开关标签必须被分进**两堆**，而且分错方向要能量出来。
    ///
    /// 为什么这条必须存在（不是"锦上添花的纯函数测试"）：R33 放框用的就是这把尺，
    /// 而它现在**还没有任何判据** —— 只有诊断在打数，而诊断永远 skip。
    /// 也就是说"这条带是说明档"这句话目前还是**我说它是什么就是什么**。
    /// 这一条把它钉成量出来的：`tierSplit = 150` 落在两簇中间，
    /// 这条真值表自己的框量到 说明档最深 120（亮）/ 121（暗）、标题档 206（亮）/ 185（暗），
    /// 间隙 **86 / 64**；诊断那条用的矩形更宽（x 150..710、整列），
    /// 背景众数不同 ⇒ 同一行字量出 128/193 —— **偏离量是"相对这块矩形的底"的，不是绝对的**，
    /// 所以这里钉的是顺序与间隙，不是水平（写第一版时钉了水平，暗档假红一次，见下面的注释）。
    /// 于是 split 挪到 140 或 170 都还在两簇之间，这条真值表同时就是那个稳健性。
    func testRowTierProfileSeparatesCaptionFromTitle() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r33-tiertruth-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        let pane = CGRect(x: 150, y: 20, width: 560, height: 500)
        // 两带从帧上量（`testSettingsCaptionRowTierProfileDiagnostic` 打的带表）：
        // 161..171 是「暂停时仍在推进…」那段 `.caption`；142..155 是它上面那颗开关「暂停记录剪贴板」的标签。
        // （R33 里 U-55 把说明段编回各自开关那一组之后，这两带各往上挪了 5pt 与 12pt ——
        //  带的位置不是常量，是从帧上量的，所以两处都要跟着改，改完由这条真值表重新钉住。）
        let captionBand = CGRect(x: 150, y: 161, width: 560, height: 10)
        let titleBand = CGRect(x: 150, y: 142, width: 560, height: 13)
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            guard let fixture = fixtures(appearance: appearance)
                .first(where: { $0.name == "settings-general" }) else {
                return XCTFail("找不到 settings-general ⇒ 真值表没有对象")
            }
            let file = scratch.appendingPathComponent("settings-general-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("读不回刚拍的 \(file.lastPathComponent)")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            let whole = Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                           bytesPerRow: rep.bytesPerRow, rect: pane, scale: scale, gate: 8)
            guard whole.brighter + whole.darker > 0 else {
                throw XCTSkip("ROWTIER_NOT_RUN \(tag)：这台机器拍不出设置页内容列（整列 0 个偏离像素，"
                              + "BACKLOG 43 实测过 runner 上就是这一块平涂）"
                              + "⇒ 这把尺的分档在这台机器上没验过。"
                              + "跳过而不是绿：这条判据的内容是「这一堆和那一堆被分开了」，"
                              + "机器画不出字时它没有内容。")
            }
            func summarize(_ rect: CGRect) -> (maxDeviation: Int, caption: Int, title: Int) {
                let rows = Self.rowTierProfile(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                               bytesPerRow: rep.bytesPerRow, rect: rect, scale: scale)
                return (rows.map(\.maxDeviation).max() ?? 0,
                        rows.reduce(0) { $0 + $1.caption }, rows.reduce(0) { $0 + $1.title })
            }
            let caption = summarize(captionBand)
            let title = summarize(titleBand)
            XCTAssertGreaterThanOrEqual(caption.caption, 1_000,
                        "\(tag)：说明段带里只读到 \(caption.caption) 个说明档像素 ⇒ 框没压住那段字"
                        + "（去重打行剖面，别把地板调低）")
            XCTAssertEqual(caption.title, 0,
                        "\(tag)：说明段带（\(captionBand)）里冒出 \(caption.title) 个**标题档**像素 ⇒ "
                        + "这一带混进了比说明段更深的一行（标题或开关标签被搬进来了），"
                        + "于是这条带不再是「只有说明段」，探针的前提破了")
            XCTAssertGreaterThan(title.title, title.caption,
                        "\(tag)：开关标签带（\(titleBand)）本该是标题档，实测 说明=\(title.caption) "
                        + "标题=\(title.title) ⇒ 尺把两堆分反了，或者那一行被改淡了（`.secondary` 化）。"
                        + "两种都先别动阈值，去看那张帧")
            // **阈值必须落在两簇之间**，而且是从**这张帧**量出来的一句话：
            // 说明带最深 120（亮）/ 121（暗），标题带 206 / 185 ⇒ `tierSplit = 150` 在中间，
            // 离说明簇 30 / 29，离标题簇 56 / 35。
            // 刻意**不**写成"标题档 ≥ 190"那种绝对水平：第一版我就写了 190，暗档实测 185，
            // 一条假红 —— 而那些数还会随框自己的背景众数漂（诊断打的 128/193 与这里的 121/185
            // 不是同一张框：`rowTierProfile` 的背景取的是**这块矩形**的众数，
            // 矩形不同，偏离量就不同）。能钉住的是**顺序与间隙**，不是水平。
            XCTAssertLessThan(caption.maxDeviation, 150,
                        "\(tag)：说明段带最深偏离 \(caption.maxDeviation) ≥ 150（`tierSplit`）⇒ "
                        + "尺的档位边界落进了说明簇自己里面，说明档会被判成标题档")
            XCTAssertGreaterThan(title.maxDeviation, 150,
                        "\(tag)：标题档带最深偏离只有 \(title.maxDeviation) ≤ 150 ⇒ 边界落进了标题簇"
                        + "里面（两簇可能已经并成一簇），这把尺失去判别力")
            XCTAssertGreaterThanOrEqual(title.maxDeviation - caption.maxDeviation, 40,
                        "\(tag)：两簇最深偏离只差 \(title.maxDeviation - caption.maxDeviation)"
                        + "（本机 86 / 64）⇒ 间隙塌到不足 40，`tierSplit` 这个单点分档不再可靠，"
                        + "别再拿它放框")
            emit("ROWTIER_TRUTH \(tag) 说明带 最深=\(caption.maxDeviation) 说明=\(caption.caption) 标题=\(caption.title)"
                  + " / 标题带 最深=\(title.maxDeviation) 说明=\(title.caption) 标题=\(title.title)"
                  + " 间隙=\(title.maxDeviation - caption.maxDeviation)")
        }
    }

    /// R33 / U-55 · **每段说明必须贴着它解释的那一颗开关**（从帧上量，不读源码顺序）。
    ///
    /// 缺陷是**看帧**看到的：通用页原来写成"两个开关连着、两段说明连着"，
    /// 屏上的顺序就成了「识别截图文字 → 保留富文本 → RTF 的代价 → 关闭后不再对新入库的图片做文字识别」——
    /// 那句讲 **OCR** 的话挂在 RTF 开关下面（亮暗两档都是）。
    /// 只重排还不够：组间与组内都是 8pt 时，说明段与上下两颗开关**等距**，归属仍然靠猜，
    /// 所以同时把说明段的组内间距收到 `SettingsViewLayout.captionGap = 3`。
    ///
    /// 判据为什么长成这样（三条一起）：
    /// ① 说明段**上面那一带必须是更深的一档**（开关或分区标题）—— 拦住"说明段飘到别处"；
    /// ② 与上面那一带的空缝 ≤ `InkFloor.captionHugMaxPt` —— 拦住"等距"，也就是这条改动的实质；
    /// ③ 若下面还有一颗开关，空缝必须**上面更近**—— 归属唯一化。
    /// 最后 `judged ≥ 3`：这一页正好三段说明，一条都没判成就是尺坏了，不是产品过了。
    func testSettingsCaptionSitsCloserToItsOwnToggle() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r33-caption-hug-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        let pane = CGRect(x: 150, y: 20, width: 560, height: 500)
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            guard let fixture = fixtures(appearance: appearance)
                .first(where: { $0.name == "settings-general" }) else {
                return XCTFail("找不到 settings-general ⇒ 归属判据没有对象")
            }
            let file = scratch.appendingPathComponent("settings-general-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("读不回刚拍的 \(file.lastPathComponent)")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            let rows = Self.rowTierProfile(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                           bytesPerRow: rep.bytesPerRow, rect: pane, scale: scale)
            let bands = Self.textBands(rows: rows, scale: scale)
            let captions = bands.filter { $0.title == 0 && $0.caption > 0 }
            guard bands.count >= 5, !captions.isEmpty else {
                throw XCTSkip("CAPTION_HUG_NOT_RUN \(tag)：这一页只量到 \(bands.count) 带文字"
                              + "（其中说明档 \(captions.count) 带）⇒ 这台机器拍不出设置页（BACKLOG 43），"
                              + "归属这条记为未运行，不算通过")
            }
            // 把连续的说明档带并成"一段"。存的不是坐标而是**带表里的下标**
            // （坐标相等比较是浮点陷阱，下标天然唯一）。
            // **并段的判据是行距而不是"都是说明段"**：段内行距实测 3.0pt，
            // 而两段**不同**的说明之间是 11.5pt（都从修之前那张帧上量的）。
            // 这个区别就是这条判据能不能抓到 U-55：那个缺陷本身正是"两段说明连在一起"，
            // 若把它们并成一段，判据会看见一段"上面贴着开关"的合格说明，于是缺陷被尺抹平。
            var runs: [(first: Int, last: Int)] = []
            var open: Int?
            for (index, band) in bands.enumerated() {
                let isCaption = band.title == 0 && band.caption > 0
                if !isCaption {
                    if let start = open { runs.append((start, index - 1)); open = nil }
                    continue
                }
                if open != nil,
                   band.startPt - bands[index - 1].endPt <= InkFloor.captionLineGapMaxPt {
                    continue  // 同一段的下一行
                }
                if let start = open { runs.append((start, index - 1)) }
                open = index
            }
            if let start = open { runs.append((start, bands.count - 1)) }
            var judged = 0
            for run in runs {
                guard run.first > 0 else {
                    XCTFail("带表里第一段就是说明段（\(bands.count) 带）⇒ 这一页开头不是分区标题，"
                            + "要么尺把标题档读丢了，要么产品把说明段放到了整页最上面")
                    continue
                }
                let firstBand = bands[run.first], lastBand = bands[run.last]
                let above = bands[run.first - 1]
                XCTAssertGreaterThan(above.title, 0,
                            "「y=\(String(format: "%.1f", firstBand.startPt)) 那段说明」上面那一带"
                            + "（\(String(format: "%.1f", above.startPt))..\(String(format: "%.1f", above.endPt))）"
                            + "里没有标题档的墨 ⇒ 这段说明不跟着任何开关或分区标题，它是在解释谁？（\(tag)）")
                let gapAbove = firstBand.startPt - above.endPt
                XCTAssertLessThanOrEqual(gapAbove, InkFloor.captionHugMaxPt,
                            "「y=\(String(format: "%.1f", firstBand.startPt)) 那段说明」离上面那颗开关 "
                            + "\(String(format: "%.1f", gapAbove))pt（\(tag)，上限 "
                            + "\(InkFloor.captionHugMaxPt)）⇒ 说明段与上下两颗开关差不多远，"
                            + "读的人只能靠猜它属于谁。产品里这段与它的开关应当编成一组"
                            + "（`SettingsViewLayout.captionGap`），组间才是 8pt")
                let below = bands.dropFirst(run.last + 1).first { $0.title > 0 }
                if let below {
                    let gapBelow = below.startPt - lastBand.endPt
                    XCTAssertLessThan(gapAbove, gapBelow,
                                "这段说明离上面的开关 \(String(format: "%.1f", gapAbove))pt、"
                                + "离下面的开关 \(String(format: "%.1f", gapBelow))pt ⇒ 它离**下一颗**更近，"
                                + "会被读成下一颗的说明（U-55 就是这么错的）（\(tag)）")
                    emit(String(format: "CAPTION_HUG settings-general %@ 说明段 y=%.1f..%.1f 上缝=%.1f 下缝=%.1f",
                                 tag, firstBand.startPt, lastBand.endPt, gapAbove, gapBelow))
                } else {
                    emit(String(format: "CAPTION_HUG settings-general %@ 说明段 y=%.1f..%.1f 上缝=%.1f 下缝=无（最后一段）",
                                 tag, firstBand.startPt, lastBand.endPt, gapAbove))
                }
                judged += 1
            }
            XCTAssertGreaterThanOrEqual(judged, 3,
                        "\(tag)：通用页只判了 \(judged) 段说明（这一页有 3 段 `.secondary` 说明）⇒ "
                        + "说明段没被量到，这条判据没有内容")
        }
    }

    ///
    /// 这一条不判产品（产品那一列没被判定为缺陷 —— 十三臂复刻体全画对，机制未定，见 D-089）。
    /// 它判的是"我们知道多少"：把"哪些帧的暗档侧栏文字不可信"钉成一份名单，
    /// 名单变了就必须红一次、逼一次人去看，而不是让这件事留在某轮的散文里。
    /// 侧栏那一列**实际**是在哪个外观下解析颜色的（R30 量出来的机制）。
    ///
    /// 返回值是子树里第一个"框压在 `column` 上、且 `effectiveAppearance` 是 Vibrant 系"的视图外观名；
    /// 找不到 ⇒ nil。这一条不是判据，是**判据的前提**：
    /// `testDarkSettingsSidebarTextIsACountedBlindSpot` 用它把"反侧墨"钉在"vibrant 子树"上，
    /// 于是伪影的解释一旦失效（比如有人把侧栏换成非 vibrant 容器），守卫会红着说"解释过期了"。
    static func vibrantAppearanceCovering(_ host: NSView, column: CGRect) -> String? {
        var found: String?
        func walk(_ view: NSView, depth: Int) {
            guard found == nil, depth < 18 else { return }
            let name = view.effectiveAppearance.name.rawValue
            if name.contains("Vibrant"), view.convert(view.bounds, to: nil).intersects(column) {
                found = name
                return
            }
            view.subviews.forEach { walk($0, depth: depth + 1) }
        }
        walk(host, depth: 0)
        return found
    }

    /// 暗档设置页侧栏文字的可读性**要能被数出来**（R29d / U-52）。
    ///
    /// 这一条不判产品（产品那一列没被判定为缺陷 —— 十五臂复刻体全画对，机制未定，见 D-089）。
    /// 它判的是"我们知道多少"：把"哪些帧的暗档侧栏文字不可信"钉成一份名单，
    /// 名单变了就必须红一次、逼一次人去看，而不是让这件事留在某轮的散文里。
    func testDarkSettingsSidebarTextIsACountedBlindSpot() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r29d-sidebar-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        var wrongSide: Set<String> = []
        var vibrantColumns: Set<String> = []
        var judged = 0
        var contentInkTotal = 0
        for fixture in fixtures(appearance: .darkAqua) where fixture.name.hasPrefix("settings-") {
            let file = scratch.appendingPathComponent("\(fixture.name).png")
            var vibrant: String?
            // R30：拍之前先记下"这一列到底在哪个外观里解析颜色" —— 这是下面那条
            // **前提断言**的对象（伪影的解释，不是伪影本身）。
            _ = try render(fixture, appearance: .darkAqua, to: file) { host in
                vibrant = Self.vibrantAppearanceCovering(host, column: Self.settingsSidebarTextColumn)
            }
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("\(fixture.name)：读不回刚拍的帧")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            // 先量内容区：它只回答"这台机器拍不拍得出这一页"，不回答产品好不好。
            let content = Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow,
                                             rect: Self.settingsContentPane, scale: scale)
            contentInkTotal += content.brighter + content.darker
            let counts = Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                            bytesPerRow: rep.bytesPerRow,
                                            rect: Self.settingsSidebarTextColumn, scale: scale)
            // runner 上这一页整块画不出来（BACKLOG 43）⇒ 逐条记 NOT-RUN，最后由
            // `contentInkTotal` 那条决定"是机器拍不出这一页"还是"我这把尺没压住字"。
            guard counts.brighter + counts.darker > 0 else {
                emit("TEXT_SIDE_NOT_RUN \(fixture.name) dark 侧栏列读到 0 个偏离像素"
                      + "（同帧内容区读到 \(content.brighter + content.darker) 个）")
                continue
            }
            judged += 1
            let inverted = Self.inkFailureIsInverted(brighter: counts.brighter, darker: counts.darker,
                                                     darkAppearance: true)
            if inverted { wrongSide.insert(fixture.name) }
            if vibrant != nil { vibrantColumns.insert(fixture.name) }
            emit("TEXT_SIDE \(fixture.name) dark 亮侧=\(counts.brighter) 暗侧=\(counts.darker)"
                  + " 侧栏子树外观=" + (vibrant ?? "非 vibrant")
                  + " ⇒ " + (inverted ? "侧栏文字落在背景错误一侧（不可见）" : "墨在期望侧"))
        }
        if contentInkTotal == 0 {
            emit("TEXT_SIDE_NOT_RUN all（这台机器拍不出 SettingsView：内容区也读到 0 个偏离像素）")
            throw XCTSkip("TEXT_SIDE_NOT_RUN：BACKLOG 43 那一族 —— 这台机器上 `SettingsView` 是一块平涂底色，"
                          + "侧栏与内容区都读到 0 个偏离像素 ⇒ 这条守卫记为未运行，不算通过也不算盲区")
        }
        let extra = wrongSide.subtracting(Self.darkSidebarTextBlindSpots)
        let gone = Self.darkSidebarTextBlindSpots.subtracting(wrongSide)
        XCTAssert(extra.isEmpty,
                  "这些帧的暗档侧栏文字**第一次**落在错误一侧：\(extra.sorted()) ⇒ 又多了一处"
                  + "离屏帧里不可见的文字。先定位是谁、为什么，再决定加名单还是修那一层；"
                  + "不许为了绿把断言放宽")
        XCTAssert(gone.isEmpty,
                  "这些帧的暗档侧栏文字现在落在期望侧了：\(gone.sorted()) ⇒ 两种可能："
                  + "①机制被修好了（BACKLOG 45 可以关，但必须先肉眼复审那张帧，别只缩名单）；"
                  + "②尺瞎了（框没压住字 / 背景取错位置 —— R29d 刚犯过后者）。"
                  + "两种都要真的去看那张帧")
        XCTAssertGreaterThan(judged, 0,
                             "内容区读到了墨（\(contentInkTotal) 个偏离像素）⇒ 这台机器**拍得出**这一页，"
                             + "可侧栏那一列一条都没判 ⇒ 是**尺没压住字**，不是环境问题。"
                             + "回去核对 `settingsSidebarTextColumn` 的坐标与单位（R29d 的 pt/px 教训）")
        // **前提断言**（R30 / D-090）：反侧墨必须仍然反侧在"vibrant 子树"上。
        // 机制：设置页的侧栏列由 `NavigationSplitView` 放进 `NSVisualEffectView`，
        // 那一列的 `NSHostingView` 实测生效外观是 **`NSAppearanceNameVibrantDark`**（不是 DarkAqua）。
        // vibrant 文字的极性是**故意反的** —— 它指望窗口服务器在合成时把它翻回来；
        // 而 `cacheDisplay` 不走那一步合成，于是拍到的是"合成前"的像素：暗档里黑字黑底。
        // ⇒ 这一列的暗档可读性**结构上量不到**，不是产品缺陷，也不是"暂时没修好的尺"。
        // 所以：名单里的帧必须仍然落在 vibrant 子树上；反侧墨若出现在**非 vibrant** 的帧上，
        // 那一次它就不是伪影，而是真缺陷 —— 必须红。
        XCTAssert(wrongSide.isSubset(of: vibrantColumns),
                  "这些帧读到了反侧墨，但它们的侧栏子树**不是** vibrant：\(wrongSide.subtracting(vibrantColumns).sorted())"
                  + " ⇒ 合成前极性的解释覆盖不到它们，那一次黑字黑底是真的产品问题。先去看那张帧")
        // 名单**由这条前提决定**，不是手钉的：侧栏列在 vibrant 子树里 ⇒ 它的暗档文字
        // 结构上量不到 ⇒ 必须在名单里；不再是 vibrant ⇒ 必须离开名单并重新肉眼复审。
        // 两个方向都会红，所以"把名单改一改让这条绿"这条路是走不通的。
        XCTAssertEqual(vibrantColumns, Self.darkSidebarTextBlindSpots,
                       "vibrant 子树实测是 \(vibrantColumns.sorted())，名单是 "
                       + "\(Self.darkSidebarTextBlindSpots.sorted()) ⇒ 两者必须一致。"
                       + "多了：那一列其实量得到，别把它记成盲区；"
                       + "少了：那一列现在结构上量不到（合成前的极性），它的暗档可读性不能当证据")
        emit("TEXT_SIDE_BLIND_SPOTS \(wrongSide.count) of \(judged) settings fixtures"
              + "（名单 \(Self.darkSidebarTextBlindSpots.count) 条；vibrant 子树 \(vibrantColumns.count) 条）")
    }

    /// 一小块区域的**众数亮度**（8 级量化），用来取"这一块的底色是多少"。
    /// 像素坐标，不是 pt —— 与 `meanLuminance` 同一套约定，两套混用是 R29d 那课的原价。
    static func modalLuma(bytes: UnsafePointer<UInt8>, bytesPerRow: Int,
                          xRange: Range<Int>, yRange: Range<Int>) -> Int {
        var histogram: [Int: Int] = [:]
        for y in yRange {
            for x in xRange {
                let o = y * bytesPerRow + x * 4
                let value = Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                                 + 0.0722 * Double(bytes[o + 2])).rounded())
                histogram[value / 8, default: 0] += 1
            }
        }
        return histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? -1
    }

    /// **同一张卡片里只准有一种留白**（R95 / 设置「快捷键」分区逐元素重判）。
    ///
    /// 缺陷是量出来的：改之前 `settings-shortcuts` 这张卡片，分隔线两侧各 14.5 / 15.0pt，
    /// 而卡片自己的上下边缘只有 7.5 / 6.5pt（亮暗两档同一组数）。最后一行是四行说明的那一行，
    /// 它的末行离卡片底 6.5pt —— 读起来像"卡片装不下内容"。
    /// 根因在容器：`GroupBox { VStack(spacing: 12) { 行; Divider(); 行 } }` 里那 12pt
    /// 只长在**孩子之间**，首末行什么也没拿到。
    ///
    /// 判据为什么是"这几个数是不是同一个数"而不是"这个数够不够大"：
    /// 后者会被"整体都很挤"骗过去（把 14.5 也改成 7 就绿了），前者不会。
    ///
    /// 这台机器拍不出设置页时记 NOT-RUN（BACKLOG 43 那一族），**不算通过也不算盲区**。
    func testSettingsCardVerticalRhythmIsOneNumber() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r95-rhythm-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var judged = 0
        for (appearance, tag) in [(NSAppearance.Name.aqua, "light"),
                                  (NSAppearance.Name.darkAqua, "dark")] {
            guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == "settings-shortcuts" }) else {
                return XCTFail("找不到 settings-shortcuts ⇒ 这条判据没有对象")
            }
            let file = scratch.appendingPathComponent("settings-shortcuts-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("\(tag)：读不回刚拍的帧")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            // 页面底从**窗口最上面那一条**取（那里不可能有卡片：夹具高度 540pt，卡片在 106pt 起）。
            let pageLuma = Self.modalLuma(bytes: base, bytesPerRow: rep.bytesPerRow,
                                          xRange: Int(150 * scale)..<Int(710 * scale),
                                          yRange: Int(4 * scale)..<Int(12 * scale))
            let band = CGRect(x: 155, y: 60, width: 560, height: 440)
            let rows = Self.cardRowKinds(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                         bytesPerRow: rep.bytesPerRow, rect: band, scale: scale,
                                         pageLuma: pageLuma)
            let inkRows = rows.filter { $0 == .ink }.count
            let (edges, gaps, dividers) = Self.cardRhythm(rows: rows, scale: scale)
            let fmt = { (values: [Double]) in
                values.map { String(format: "%.1f", $0) }.joined(separator: "/")
            }
            emit("CARD_RHYTHM settings-shortcuts \(tag) 页底=\(pageLuma) 墨行=\(inkRows)"
                 + " 分隔线=\(dividers) 边距=\(fmt(edges)) 内侧=\(fmt(gaps))")
            guard inkRows > 0 else {
                emit("CARD_RHYTHM_NOT_RUN settings-shortcuts \(tag)（整带零墨 ⇒ 这台机器拍不出这一页）")
                continue
            }
            XCTAssertFalse(edges.isEmpty || gaps.isEmpty,
                           "\(tag)：这一带有 \(inkRows) 行墨，却读不出卡片边距或分隔线两侧留白 ⇒ "
                           + "是**尺没压住卡片**（带子越界 / 众数取错位置），不是产品没问题")
            XCTAssertGreaterThanOrEqual(dividers, 2,
                                        "settings-shortcuts 这张卡片上有两条分隔线（三行），实测 \(dividers) 条"
                                        + " ⇒ 要么夹具换了，要么 `.line` 那一档的门槛把线读丢了")
            let all = edges + gaps
            let spread = all.max()! - all.min()!
            XCTAssertLessThanOrEqual(spread, 3.0,
                                     "同一张卡片里最大的留白 \(String(format: "%.1f", all.max()!))pt、"
                                     + "最小的 \(String(format: "%.1f", all.min()!))pt（边距 \(fmt(edges))、"
                                     + "内侧 \(fmt(gaps))）⇒ 卡片四边与分隔线两侧必须是同一档；"
                                     + "差这么多就是首末行没有内边距，最后一行贴着卡片底")
            judged += 1
        }
        if judged == 0 {
            throw XCTSkip("CARD_RHYTHM_NOT_RUN：两档都拍不出 settings-shortcuts ⇒ 竖向节奏记为未运行"
                          + "（BACKLOG 43 同族），不算通过")
        }
    }

    /// 节奏这把尺的算术要有真值表（**不覆盖管线**：它判的是纯函数；
    /// 管线级判据是上面那条 `testSettingsCardVerticalRhythmIsOneNumber`）。
    ///
    /// 三条合成行序列，各挡一种"看着对、其实答不了问题"的写法：
    /// ① 均匀 ⇒ 绿；② 边缘挤 ⇒ 红（本轮那个缺陷的形状）；③ 卡片顶到带子上沿 ⇒
    /// **不许给数**（宁可空，也不能把"没有上留白"读成"上留白=0"再判成缺陷）。
    func testCardRhythmArithmeticIsATruthTable() {
        func rows(_ spec: [(CardRowKind, Int)]) -> [CardRowKind] {
            spec.flatMap { kind, count in Array(repeating: kind, count: count) }
        }
        // 数组没有 `accuracy` 那一条重载，逐元素比（一次写错不会让整条断言静默少判）。
        func same(_ got: [Double], _ want: [Double], _ why: String,
                  file: StaticString = #filePath, line: UInt = #line) {
            XCTAssertEqual(got.count, want.count, "\(why)：读了 \(got.count) 个数，期望 \(want.count) 个",
                           file: file, line: line)
            guard got.count == want.count else { return }
            for (i, value) in got.enumerated() {
                XCTAssertEqual(value, want[i], accuracy: 0.001, "\(why)：第 \(i) 个", file: file, line: line)
            }
        }
        // ① 边 14 / 内侧 14 ⇒ 同一档
        let even = rows([(.outside, 4), (.card, 14), (.ink, 10), (.card, 14), (.line, 1),
                         (.card, 14), (.ink, 10), (.card, 14), (.outside, 4)])
        let a = Self.cardRhythm(rows: even, scale: 1)
        XCTAssertEqual(a.dividers, 1)
        same(a.edges, [14, 14], "均匀那张卡片：四边")
        same(a.gaps, [14, 14], "均匀那张卡片：分隔线两侧")
        // ② 边 2 / 内侧 14 ⇒ 本轮那个缺陷
        let tight = rows([(.outside, 4), (.card, 2), (.ink, 10), (.card, 14), (.line, 1),
                          (.card, 14), (.ink, 10), (.card, 2), (.outside, 4)])
        let b = Self.cardRhythm(rows: tight, scale: 1)
        same(b.edges, [2, 2], "边距没补那张：四边")
        same(b.gaps, [14, 14], "边距没补那张：分隔线两侧")
        XCTAssertGreaterThan((b.edges + b.gaps).max()! - (b.edges + b.gaps).min()!, 3.0,
                             "这条合成件必须**能被**管线判据判红，否则那条断言是恒真的")
        // ③ 卡片顶到带上沿 ⇒ 没有"上留白"这个对象
        let clipped = rows([(.card, 2), (.ink, 10), (.card, 14), (.line, 1), (.card, 14),
                            (.ink, 10), (.card, 2), (.outside, 4)])
        XCTAssertTrue(Self.cardRhythm(rows: clipped, scale: 1).edges.isEmpty,
                      "卡片贴着带上沿时不许报边距：那会把「尺没对齐」读成「产品的留白是 0」")
        // ④ 全空（这台机器拍不出这一页）⇒ 也不许报数
        XCTAssertTrue(Self.cardRhythm(rows: Array(repeating: .outside, count: 40), scale: 2)
                      .edges.isEmpty)
    }

    /// 每张卡片都得补那份留白：`GroupBox` 的个数必须等于 `settingsCardInset()` 的个数。
    ///
    /// 为什么源码层也要一条：帧判据只压在 `settings-shortcuts` 一张上（别的卡片里
    /// 不一定有分隔线，"内侧那一档"没有对象）。新增一张卡片忘了补，帧上不会红 ——
    /// 这一条会。它数的是**调用点**，不是常量出现次数，所以卡片内部那处
    /// `.padding(.vertical, 4)`（讲的是另一件事）不会被算进来。
    func testEverySettingsCardAppliesTheSharedEdgeInset() throws {
        let source = Self.codeOnly(try productSource(named: "Views/SettingsView.swift"))
        let cards = source.components(separatedBy: "GroupBox {").count - 1
        let insets = source.components(separatedBy: ".settingsCardInset()").count - 1
        XCTAssertGreaterThan(cards, 0, "源码里一张 GroupBox 都没找到 ⇒ 这条守卫的对象没了")
        XCTAssertEqual(cards, insets,
                       "设置页有 \(cards) 张卡片，却只有 \(insets) 处补了上下留白 ⇒ "
                       + "至少一张卡片的首末行会贴到卡片边上（R95 那个缺陷的形状）。"
                       + "新卡片请写 `.settingsCardInset()`，别再手抄一个数")
    }

    /// 这个外观下，"正常的墨"应该在背景的哪一侧。
    static func inkIsOnTheExpectedSide(brighter: Int, darker: Int, darkAppearance: Bool) -> Bool {
        // 一侧占绝对多数才算"有方向"；各半（例如框里同时压着黑白两种元素）不下结论。
        guard brighter + darker > 0 else { return true }
        let dominantIsBright = brighter > darker * 2
        let dominantIsDark = darker > brighter * 2
        if darkAppearance { return !dominantIsDark }
        return !dominantIsBright
    }

    /// 一条没过地板的对比度读数，该报"产品淡"还是"这条帧不可信"。
    /// 两句话的**修法完全相反**：前者改产品，后者一行都不许改。
    static func inkFailureIsInverted(brighter: Int, darker: Int, darkAppearance: Bool) -> Bool {
        !inkIsOnTheExpectedSide(brighter: brighter, darker: darker, darkAppearance: darkAppearance)
    }

    /// 给一条失败的对比度读数配的"方向诊断"。
    ///
    /// 这一行的全部价值是把两条相反的路分开写：
    /// 反相 ⇒ **一行产品代码都不许改**，去查捕获路径；真淡 ⇒ 改墨档。
    static func inkDiagnosisLine(tail: (brighter: Int, darker: Int, total: Int),
                                 darkAppearance: Bool) -> String {
        if inkFailureIsInverted(brighter: tail.brighter, darker: tail.darker,
                                darkAppearance: darkAppearance) {
            return "⚠ 这块区域的墨全落在背景的另一侧（亮\(tail.brighter) / 暗\(tail.darker)）⇒ "
                + "**这是 R28 记下的反相伪影，不是产品淡**：一行产品代码都不许改，去查捕获路径。"
        }
        return "墨的方向正常（亮\(tail.brighter) / 暗\(tail.darker)）⇒ 这个低值是真的淡，可以据此改产品。"
    }

    /// 真值表：方向的判定必须跟着外观走，而且必须**只看多数侧**。
    /// 每一行的数都是量出来的：亮色帧里未选中的侧栏符号整列 (255,255,255) 对 (248,248,248)，
    /// 同一张帧里的标题是 (39,39,39)；暗色反过来。
    func testInkDirectionTruthTable() {
        // 亮色（aqua）：墨应当在暗侧。
        XCTAssertTrue(Self.inkIsOnTheExpectedSide(brighter: 3, darker: 900, darkAppearance: false),
                      "亮色帧里墨在暗侧 = 正常")
        XCTAssertFalse(Self.inkIsOnTheExpectedSide(brighter: 900, darker: 3, darkAppearance: false),
                       "亮色帧里墨全在亮侧 = 反相，不许当成'太淡'去改产品")
        // 暗色（darkAqua）：同一条规律方向反过来 —— 墨应当在亮侧。
        XCTAssertTrue(Self.inkIsOnTheExpectedSide(brighter: 900, darker: 3, darkAppearance: true),
                      "暗色帧里墨在亮侧 = 正常")
        XCTAssertFalse(Self.inkIsOnTheExpectedSide(brighter: 3, darker: 900, darkAppearance: true),
                       "暗色帧里墨全在暗侧 = 反相")
        // 两侧各半（框同时压着黑白两种元素）：不下结论，别把"混"读成"反"。
        XCTAssertTrue(Self.inkIsOnTheExpectedSide(brighter: 40, darker: 45, darkAppearance: false),
                      "没有明显多数侧时不判反相 —— 否则任何混排框都会被误报")
        // 空框：交给墨占比地板去拦，方向这条不抢话。
        XCTAssertTrue(Self.inkIsOnTheExpectedSide(brighter: 0, darker: 0, darkAppearance: false),
                      "空框不是反相，是'框贴到空白'，那是另一条地板的职责")
    }

    /// **正对照来自一张真的坏帧**：`settings-general` 亮色里，
    /// 未选中行的图标列是已知的反相面（R28：整列 255 对 248），
    /// 而同一行右侧的标题是正常墨。同一把尺、同一张帧、两个相反的读数 ——
    /// 一把只会说"过"的尺不能靠这种对照立起来，只有能同时读出"这侧/那侧"的才行。
    func testInkDirectionRulerReadsBothEnds() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r29-direction-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        guard let fixture = fixtures(appearance: .aqua).first(where: { $0.name == "settings-general" }) else {
            return XCTFail("找不到 settings-general ⇒ 这条正对照没有对象")
        }
        let file = scratch.appendingPathComponent("settings-general.png")
        _ = try render(fixture, appearance: .aqua, to: file)
        guard let image = NSImage(contentsOf: file),
              let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
              let base = rep.bitmapData else {
            return XCTFail("读不回刚拍的帧")
        }
        let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
        // 第一行「快捷键」的图标列（x 15..37，y 66..86 —— R28 从帧上量的）。
        let icon = Self.inkTailSplit(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                     bytesPerRow: rep.bytesPerRow,
                                     rect: CGRect(x: 15, y: 66, width: 22, height: 20), scale: scale)
        // 同一行的标题文字列（x 46..120）。
        let title = Self.inkTailSplit(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                      bytesPerRow: rep.bytesPerRow,
                                      rect: CGRect(x: 46, y: 66, width: 74, height: 20), scale: scale)
        emit("INK_SIDE 图标列 亮\(icon.brighter)/暗\(icon.darker) 标题列 亮\(title.brighter)/暗\(title.darker)")
        // 守卫要用"读到几个偏离像素"，不能用 `total` —— `total` 是尾墨切片的大小，
        // 它被 `max(1, …)` 兜过底，**永远不可能等于 0**。第一版就写错在这里：
        // CI 上这条 NOT-RUN 没生效，两条断言直接红（run 38454852737）。
        if icon.brighter + icon.darker == 0 && title.brighter + title.darker == 0 {
            emit("INK_SIDE_NOT_RUN aqua")
            throw XCTSkip("INK_SIDE_NOT_RUN：这台机器拍不出 settings-general（两列都读到 0 个偏离像素）⇒ "
                          + "两端对照记为未运行，不算通过（见 BACKLOG 43）")
        }
        XCTAssertGreaterThan(icon.brighter, icon.darker * 2,
                             "已知反相的那一列现在读不出'偏亮' ⇒ 这把方向尺坏了，"
                             + "R28 记下的那个伪影会重新伪装成'产品太淡'")
        XCTAssertGreaterThan(title.darker, title.brighter * 2,
                             "同一张帧里正常墨的那一列读不出'偏暗' ⇒ 尺坏了（两端的差别没了）")
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
                let tail = Self.inkTailSplit(bytes: base, width: rep.pixelsWide,
                                             height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                             rect: probe.rect, scale: scale)
                XCTAssertGreaterThanOrEqual(ratio, InkFloor.controlInk,
                            "\(probe.fixture) 的「\(probe.what)」静置对比度 "
                            + String(format: "%.2f", ratio) + "（\(tag)，地板 "
                            + "\(InkFloor.controlInk)）⇒ 这是可点的笔画，看不见等于没有"
                            + "\n" + Self.inkDiagnosisLine(tail: tail, darkAppearance: appearance == .darkAqua))
                emit("INK \(probe.fixture)/\(probe.what) \(tag) ratio="
                      + String(format: "%.2f", ratio) + " ink="
                      + String(format: "%.1f%%", coverage * 100))
            }
        }
    }

    /// 说明文字的探针表。框**从帧上量出来**（`.scratch/motion-audit-2/ink_probe_r24.swift probe`），
    /// 每条都有墨占比地板兜底：布局一动，框贴到空白上会红在"框里没有字"，不会红成一个假对比度。
    static let captionInkProbes: [InkProbe] = [
        InkProbe(fixture: "heatmap-populated", what: "月份刻度 9月/10月/11月…（读不出月份就读不出这张图）",
                 rect: CGRect(x: 40, y: 72, width: 380, height: 16)),
        InkProbe(fixture: "heatmap-populated", what: "星期刻度 一/三/五/日",
                 rect: CGRect(x: 10, y: 90, width: 26, height: 90)),
        InkProbe(fixture: "heatmap-populated", what: "图例「少 / 多」（颜色深浅的唯一标尺）",
                 rect: CGRect(x: 12, y: 196, width: 25, height: 14)),
        // R33 / BACKLOG 34③：菜单栏面板上那两段 11pt 的 `.secondary`。
        // 带是从帧的 `rows` 剖面上放的（不是猜的）：标题 116–130、副标题 142–155、行右端 meta 186–202。
        // 判"要读的"还是"装饰"写在账本里：副标题是这一列的**标题**（没有它，三条就是一堆莫名出现的记录），
        // meta 是"为什么推荐这条"（类型 · 当前在哪个 App · 常用）—— 两者都要读，都没有理由比 `.secondary` 淡。
        InkProbe(fixture: "menubar-recommendations", what: "副标题「猜你要粘贴」（这一列的标题）",
                 rect: CGRect(x: 120, y: 141, width: 90, height: 15)),
        InkProbe(fixture: "menubar-recommendations", what: "行右端推荐理由（类型 · 当前 App · 常用）",
                 rect: CGRect(x: 200, y: 185, width: 118, height: 15)),
          // R33 / BACKLOG 34②：通用页的三段 `.secondary` 说明（`.caption` 与 `VisualFont.meta`）。
        // 这三条**改过两次位置**：第一次按普通 `rows` 剖面放，比值读到 3.67（亮）/ 1.89（暗）
        // —— 那是套在「通用」标题与开关标签上（`InkFloor.captionTierCeiling` 上面那段）；
        // 第二次是产品动了（U-55 把说明段编回各自开关那一组，整列往上收 5pt）。
        // 现在按 `rowTierProfile` 放：带里 `标题档像素 = 0`，也就是这一带**只有**说明段的墨。
        // 带边界从帧上量（`CAPTION_HUG` 那几行就是同一把尺打的：亮 161.0..170.5 /
        // 201.5..211.0 / 241.5..266.0，暗 160.5..170.5 / 201.0..211.0 / 241.5..266.0），
        // 框比带各留 0.5–1pt，两档外观共用一套坐标。
        InkProbe(fixture: "settings-general", what: "说明段「暂停时仍在推进…」（恢复后会不会补记旧内容）",
                 rect: CGRect(x: 150, y: 160, width: 560, height: 12)),
        InkProbe(fixture: "settings-general", what: "说明段「关闭后不再对新入库的图片…」（截图文字识别）",
                 rect: CGRect(x: 150, y: 200, width: 560, height: 12)),
        InkProbe(fixture: "settings-general", what: "说明段「打开后从 Word、Pages…」（富文本的代价，两行）",
                 rect: CGRect(x: 150, y: 241, width: 560, height: 26)),
        // R39：那颗开关的**回执**（`loginItemSettings.message`）。它原来在帧里永远量不到
        // —— 夹具不造 message，产品注释就写着"只进账本不进判据"（`SettingsView:329`）。
        // 现在两张夹具把 message 造出来（不支持 / 写盘没生效），带是从这两张帧的
        // `rowTierProfile` 量的：亮 136.5..145.5（不支持）/ 136.5..146.0（失败），
        // 暗 136.0..145.5 / 136.0..146.0 ⇒ 框取 135.5..146.5，两档共用一套坐标。
        // **这两条框只在有回执的那两张帧上成立**：`settings-general`（无 message）里
        // 同一块 y 压着下一颗开关的标签（标题档 971 / 1064 个像素），所以判"没有回执"
        // 不能照抄这块坐标 —— 见 `testDisabledToggleAndFailureReceiptAreVisible` 里那段差值对照。
        InkProbe(fixture: "settings-general-login-unsupported",
                 what: "回执「当前系统不支持从应用内设置开机启动。」",
                 rect: CGRect(x: 150, y: 135.5, width: 560, height: 11)),
        InkProbe(fixture: "settings-general-login-failed",
                 what: "回执「开机启动开启失败，请稍后重试。」（macOS 12 上 AppleScript 静默失败）",
                 rect: CGRect(x: 150, y: 135.5, width: 560, height: 11)),
          // R35 / BACKLOG 34②剩下的半条：**其余每个分区都点名一处**，加主窗口两处 meta。
        // 框全部由 `testSettingsCaptionRowTierProfileDiagnostic` 的"说明档带"放（下面每条注释里
        // 写着亮/暗两档各自量到的带），天花板负责在放错时把它打回 ——
        // 一张只有地板的表会把"框套在标题上"判成通过（R33 就是这么错的，D-092）。
        InkProbe(fixture: "settings-shortcuts", what: "快捷键页那一段说明（R28 修过它被截断，档也要钉住）",
                 rect: CGRect(x: 150, y: 275, width: 560, height: 10)),
        InkProbe(fixture: "settings-privacy", what: "说明段「启用后可提供更准确的推荐。」（上下文权限）",
                 rect: CGRect(x: 150, y: 142, width: 560, height: 11)),
        InkProbe(fixture: "settings-privacy", what: "说明段「过滤敏感内容（密钥、令牌、密码等）…」（推荐过滤开关）",
                 rect: CGRect(x: 150, y: 304, width: 560, height: 11)),
        InkProbe(fixture: "settings-privacy", what: "默认排除清单第一行「默认排除：com.…」",
                 rect: CGRect(x: 150, y: 395, width: 560, height: 11)),
        InkProbe(fixture: "settings-data", what: "数据页第一段说明（存档与导出，要读）",
                 rect: CGRect(x: 150, y: 139, width: 560, height: 10)),
        InkProbe(fixture: "settings-recommendations", what: "推荐页第一段说明（权重是干什么用的）",
                 rect: CGRect(x: 150, y: 146, width: 560, height: 10)),
        InkProbe(fixture: "settings-stats-populated", what: "统计页热图上头那句说明（有数据那一臂）",
                 rect: CGRect(x: 150, y: 98, width: 560, height: 11)),
        InkProbe(fixture: "detail-0-text", what: "详情头部 meta（时间 · 大小 · 来源）",
                 rect: CGRect(x: 0, y: 36, width: 720, height: 12)),
          // 列表行第二行 meta（复制时间）**不在这里** —— R35 量出来那一列压在
        // `NSAppearanceNameVibrantLight` / `…VibrantDark` 子树上（`testProbesDoNotSitOnVibrantColumns`），
        // 拍到的是 vibrancy 合成**之前**的像素：行标题与它下面那行 `.secondary` 的 meta
        // 最深都是 (113,113,113)，而设置页内容列同样声明 `.primary` 的标签是 (38,38,38)。
        // 也就是说这张帧上"档"这个量根本不是产品那个量 —— 放一条探针进来就是给自己造一条假绿。
        // 这条位点改记为量不到（BACKLOG 48），要真判它得先有一条合成后的取图通道（R31 的边界）。
    ]

    /// **系统 `.secondary` 档在"这台机器 + 这个外观"下量到的对比度**（R28 新增的参照臂）。
    ///
    /// 为什么必须有它：R27 把地板写成绝对值 3.5，本机三处读到 3.75–3.85 全绿，
    /// **CI 的 macos-15 runner 上同一条红了两处：星期刻度 2.85、图例 3.30**（run 38443414396）。
    /// 那两处产品里用的就是 `.secondary`，也就是说这条尺量到的数里混进了
    /// "这台机器的字体平滑/色板怎么解析 secondaryLabelColor"，而判据要判的从来不是那个，
    /// 是"**有没有掉进 `.tertiary` 那一档**"。
    /// 所以判据换成相对：同一台机器、同一外观、同样 10pt 的 `.secondary` 文字
    /// 现拍一份当参照，说明文字不许比它淡过 `InkFloor.captionTierTolerance`。
    /// 绝对值只留一条**很松**的兜底（`secondaryReferenceFloor`），用途是
    /// "参照自己坏了"（渲染整体失效）时让这条判据红，而不是拿它当产品线。
    func secondaryReferenceContrast(appearance: NSAppearance.Name, scratch: URL) throws -> Double {
        let reference = Fixture("caption-reference", NSSize(width: 240, height: 26)) {
            AnyView(
                Text("收藏记录会保留暂停时不记录")
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .frame(width: 240, height: 26)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        }
        let file = scratch.appendingPathComponent("caption-reference.png")
        _ = try render(reference, appearance: appearance, to: file)
        guard let image = NSImage(contentsOf: file),
              let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
              let base = rep.bitmapData else {
            throw XCTSkip("参照帧读不回来")
        }
        let scale = Double(rep.pixelsWide) / Double(reference.size.width)
        // 量**整张**参照帧，不猜文字落在哪一行：这一份的唯一用途是给出"这台机器的 `.secondary`
        // 有多深"，而框里除了这一行字什么都没有 ⇒ 不需要定位，也不需要墨占比地板之外的任何东西。
        let (ratio, coverage) = Self.inkContrast(bytes: base, width: rep.pixelsWide,
                                                 height: rep.pixelsHigh,
                                                 bytesPerRow: rep.bytesPerRow,
                                                 rect: CGRect(origin: .zero,
                                                              size: NSSize(width: reference.size.width,
                                                                           height: reference.size.height)),
                                                 scale: scale)
        XCTAssertGreaterThanOrEqual(coverage, InkFloor.bandInkFraction,
                                    "参照帧的 `.secondary` 文字只有 "
                                    + String(format: "%.1f%%", coverage * 100) + " 的墨 ⇒ 参照本身没画出来")
        return ratio
    }

    /// **要读的标签不许比能点的笔画更淡**（R27 / U-49 / D-086；R28 把地板改成相对参照）。
    ///
    /// 修前三处全部读到 **1.88（亮）/ 2.27（暗）** —— 与 R21 判死的那两颗控件是同一组数，
    /// 而 R21 给它们开的免检理由是"那不是控件，是刻度文字"。这一轮把那条理由重新判了一遍：
    /// 没有月份与星期，这张网格读不出"哪一天"；没有"少/多"，颜色深浅没有标尺。
    /// **刻度是这张图里唯一被读的东西**，它没有理由待在比控件更淡的一档。
    ///
    /// 自己拍自己量（R20 立的规矩），且不依赖 `CLIPBOARD_HISTORY_UI_SHOTS` ⇒ CI 上真的跑。
    func testCaptionTextStaysOnTheSecondaryTier() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r27-caption-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            var judged = 0
            let reference = try secondaryReferenceContrast(appearance: appearance, scratch: scratch)
            XCTAssertGreaterThanOrEqual(reference, InkFloor.secondaryReferenceFloor,
                        "这台机器上系统的 `.secondary` 只量到 "
                        + String(format: "%.2f", reference) + "（\(tag)）⇒ 是渲染失效，不是产品淡了；"
                        + "这条判据的参照坏了，先修捕获路径")
            emit("CAPTION_REF \(tag) .secondary 参照=" + String(format: "%.2f", reference))
            for probe in Self.captionInkProbes {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == probe.fixture }) else {
                    return XCTFail("找不到夹具 \(probe.fixture) ⇒ \(probe.what) 这条探针没有对象")
                }
                let file = scratch.appendingPathComponent("\(probe.fixture)-caption-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                // **先判这台机器拍不拍得出探针所在的那一列**（R33 立、R34 改对区域的一条规矩）。
                // R33 第一版问的是"整帧有没有墨"，CI 第一轮就红了，而且**红得对**：
                // runner 上 `SettingsView` 的内容列是一块平涂（BACKLOG 43），
                // 可同一张帧的窗口底色与侧栏仍有墨 ⇒ 整帧那一问回答的是"这台机器会不会画图"，
                // 而这条判据要问的是"**这一列**画没画出来"。两者差一层，结论就反过来。
                // 于是判别区域改成**探针自己那一竖条**（同 x 范围、整高）：
                // 列里一处文字墨都没有 ⇒ 机器拍不出这一页 ⇒ NOT-RUN；
                // 列里有墨而这一带没有 ⇒ 框贴错了地方 ⇒ 照旧红（那是缺陷，不是环境问题）。
                let column = CGRect(x: probe.rect.minX, y: 0,
                                    width: probe.rect.width, height: fixture.size.height)
                let columnInk = Self.textInkMass(bytes: base, width: rep.pixelsWide,
                                                 height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                 rect: column, scale: scale)
                if !Self.columnIsDrawable(textInkPixels: columnInk.pixels) {
                    emit("CAPTION_NOT_RUN \(probe.fixture)/\(probe.what) \(tag) "
                          + "探针所在列 \(column) 读到 0 个文字墨像素")
                    continue
                }
                judged += 1
                let (ratio, coverage) = Self.inkContrast(bytes: base, width: rep.pixelsWide,
                                                         height: rep.pixelsHigh,
                                                         bytesPerRow: rep.bytesPerRow,
                                                         rect: probe.rect, scale: scale)
                XCTAssertGreaterThanOrEqual(coverage, InkFloor.probeInkFraction,
                            "\(probe.fixture) 的「\(probe.what)」在框 \(probe.rect) 里只有 "
                            + String(format: "%.1f%%", coverage * 100) + " 的墨 ⇒ 框贴到空白上了"
                            + "（刻度搬走了就去量新位置，不许把地板调低）")
                let tail = Self.inkTailSplit(bytes: base, width: rep.pixelsWide,
                                             height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                             rect: probe.rect, scale: scale)
                XCTAssertGreaterThanOrEqual(ratio, reference * InkFloor.captionTierTolerance,
                            "\(probe.fixture) 的「\(probe.what)」只有 "
                            + String(format: "%.2f", ratio) + ":1，而同一台机器、同一外观下 10pt 的 `.secondary` 参照是 "
                            + String(format: "%.2f", reference) + ":1 ⇒ 它比系统说明文字那一档淡了 "
                            + String(format: "%.0f%%", (1 - ratio / max(reference, 0.01)) * 100)
                            + "（\(tag)）。修前三处都是 1.88/2.27 —— 那是 `.tertiary`。"
                            + "**要读的标签不许比能点的笔画更淡**"
                            // R29：同样是"低"，两种低法的修法相反 —— 先分清再动手。
                            + "\n" + Self.inkDiagnosisLine(tail: tail, darkAppearance: appearance == .darkAqua))
                emit("CAPTION_INK \(probe.fixture)/\(probe.what) \(tag) ratio="
                      + String(format: "%.2f", ratio) + " 参照=" + String(format: "%.2f", reference)
                      + " 比值=" + String(format: "%.2f", ratio / max(reference, 0.01)) + " ink="
                      + String(format: "%.1f%%", coverage * 100))
                // **另一侧的闸门：这条框里必须是说明段的墨**（R33 / `captionTierCeiling`）。
                // 没有这一条，这张表只能证明"框里有足够深的墨"，证明不了"框里是它自称的那段说明"：
                // 上一轮我给通用页放的两个框套在标题上，比值 3.67 / 1.89，两条都"通过"。
                XCTAssertLessThan(ratio, reference * InkFloor.captionTierCeiling,
                            "\(probe.fixture) 的「\(probe.what)」读到 "
                            + String(format: "%.2f", ratio) + ":1 = 这台机器 `.secondary` 参照（"
                            + String(format: "%.2f", reference) + "）的 **"
                            + String(format: "%.2f 倍", ratio / max(reference, 0.01)) + "**（\(tag)）"
                            + " ⇒ 比说明档深这么多，只可能是框套到了标题/正文那一档上"
                            + "（`.headline`、开关标签、或控件），不是它自称的那段 `.secondary` 说明。"
                            + "**这条「通过」一直是假的**：地板判据看不见套错方向，只看得见过淡。"
                            + "\n修法：跑 `testSettingsCaptionRowTierProfileDiagnostic` 重打行剖面，"
                            + "把框放到「标题档像素 = 0」的那一带；"
                            + "如果产品真的把这段说明提到了 `.primary`，那就**删掉这条探针**"
                            + "（它命名的是一个 `.secondary` 位点），不许把 `captionTierCeiling` 抬上去。")
            }
            // **NOT-RUN 不能把这条判据变成恒绿**（R29d 的教训：判别臂加完就忘了问"到底判了几条"）。
            // 3 的来历：热图那 3 条是**唯一有 CI 记录的**
            // （run 38443414396 上读到 2.85 / 3.30 —— 也就是 runner 拍得出热图），
            // 而设置页整页在 runner 上是平涂（BACKLOG 43）、菜单栏面板从未在 CI 上验过 ⇒
            // 地板只钉在"这一轮确实量到了热图那三条说明段"，其余全部如实打在日志里。
            // 表本身从写这条时的 8 条长到了今天的 18 条 —— 地板**没有**跟着涨，
            // 因为它回答的是"CI 上最少判得成几条"，与表里登记了几条无关（R38：地板要能从哪台机器读出来）。
            XCTAssertGreaterThanOrEqual(judged, 3,
                        "\(tag) 档 \(Self.captionInkProbes.count) 条说明段探针**一条都没判成**（judged=\(judged)）⇒ "
                        + "是捕获路径坏了，不是产品都过了。热图那三条在任何机器上都拍得出来，"
                        + "它们要是也读不到墨，这条判据就没有内容，必须红着说这件事。")
            emit("CAPTION_JUDGED \(tag) 判了 \(judged) 条 / 表里 \(Self.captionInkProbes.count) 条")
        }
        // **覆盖要有机器账**（R35 / 与 R10「探针名单从产品推导」同一条规矩）：
        // 这张表从 R27 的三处热图刻度长到今天的 17 处，全靠一轮一轮点名 ——
        // 而"下一轮还点不点"目前没有约束。加这一条：**设置窗口每一个分区至少被点名一次**，
        // 分区清单从 `SettingsCategory.allCases` 推导，不写死。
        // 于是"新增一个分区而没给它任何说明段判据"会当场红，而不是变成一张没人注意的空白页。
        let named = Set(Self.captionInkProbes.map { $0.fixture })
        var missing: [String] = []
        for category in SettingsCategory.allCases {
            if !named.contains(where: { $0.hasPrefix("settings-\(category.rawValue)") }) {
                missing.append(category.title)
            }
        }
        XCTAssert(missing.isEmpty,
                  "这些设置分区在说明段表里**一处都没有**：\(missing) ⇒ 这一页的 `.secondary` 文字"
                  + "没有任何档判据看着。用 `testSettingsCaptionRowTierProfileDiagnostic` 点名它真实的带"
                  + "（带要量出来，不许照抄别处的 y），再把探针加进 `captionInkProbes`。")
        emit("CAPTION_COVERAGE 设置分区 \(SettingsCategory.allCases.count) 个，全部至少点名一处"
              + "（表里 \(Self.captionInkProbes.count) 条）")
    }

    // MARK: - R28 · "这一页一共画了多少字"（两臂对照）

    /// 文字墨的闸门：**偏离背景 >60** 才算一个字的笔画。
    ///
    /// 为什么不是 R24 那批用的 24：这一页除了字还有**平涂的控件底色**
    /// （快捷键录制框 128×28 的灰、三颗「恢复默认」药丸的灰、GroupBox 那层更浅的灰）。
    /// 它们的偏离量在 6 到 40 之间，而两种文字都远在 60 以上
    /// （`.secondary` 的 11pt 说明 ≈ 109，`.primary` 的标题 ≈ 209）。
    /// 用 24 的话三块平涂会把文字淹掉 —— 实测每块平涂约 14k 像素，
    /// 而整页的说明文字一共约 17k：**信号会被稀释成一半，而稀释是静默的**。
    /// 这一档不是口味：`testTextInkGateTruthTable` 逐条钉住"谁进得来、谁进不来"。
    static let textInkMinDelta = 60

    /// 一个像素算不算"字的笔画"。
    static func isTextInk(delta: Int) -> Bool { delta > textInkMinDelta }

    /// 判别臂的唯一问题：**这一列到底画没画出来**。
    ///
    /// 单独收成一处，是为了让它能有一张真值表（`testNotRunDiscriminatorTruthTable`）：
    /// R33 第一版把这一问写成了"整帧有没有墨"，CI 第一轮就红了 —— 而**红的是判据自己**：
    /// runner 上设置页内容列是平涂，可帧的底色与侧栏仍有墨，整帧那一问永远答"画得出来"，
    /// 于是三条设置页探针全部走进"有墨却贴到空白"的红分支。
    /// 判据要问的区域**必须就是它自己要读的那块区域**（R34）。
    static func columnIsDrawable(textInkPixels: Int) -> Bool { textInkPixels > 0 }

    /// 三张同源帧的"内容列有没有墨"折成一个决定（R39b）。
    ///
    /// 为什么要写成纯函数：真实环境里这一族**要么三张全有墨（本机）要么三张全无（runner）**，
    /// 而"只画出一部分"那一格永远走不到 —— 它恰恰是唯一能区分"环境问题"与"某一帧坏了"的那一格。
    /// 不把它拆出来测一次，就等于这条分支没有验收（账本里"本地跑不到的分支要打桩成真值测一次"）。
    enum SettingsDrawability: Equatable {
        case allDrawn        // 判
        case noneDrawn       // 显式记未运行
        case partial(Int)    // 红：同一列不可能只画出一部分
    }
    static func settingsDrawability(_ inkPerFrame: [Int]) -> SettingsDrawability {
        let drawn = inkPerFrame.filter { columnIsDrawable(textInkPixels: $0) }.count
        if drawn == 0 { return .noneDrawn }
        if drawn == inkPerFrame.count { return .allDrawn }
        return .partial(drawn)
    }

    /// 一块矩形里的文字墨：像素数 + 占这块矩形的比例。
    ///
    /// 背景取这块矩形自己的众数（16 级量化，与 `noticeBands` 同一个写法），
    /// 所以亮暗两臂不需要传不同的阈值。
    static func textInkMass(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                            bytesPerRow: Int, rect: CGRect, scale: Double) -> (pixels: Int, fraction: Double) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (0, 0) }
        var counts: [Int: Int] = [:]
        for y in y0..<y1 {
            for x in x0..<x1 {
                let o = y * bytesPerRow + x * 4
                // 16 级量化，**括号必须写**：`a / 16 << 8` 在 Swift 里是 `a / (16 << 8)`
                // （R24 就栽过一次，量出来一整帧"没有带"）。
                let key = ((Int(bytes[o]) / 16) << 8) | ((Int(bytes[o + 1]) / 16) << 4) | (Int(bytes[o + 2]) / 16)
                counts[key, default: 0] += 1
            }
        }
        let best = counts.max { $0.value < $1.value }?.key ?? 0
        let bg = ((best >> 8) * 16 + 8, ((best >> 4) & 15) * 16 + 8, (best & 15) * 16 + 8)
        var pixels = 0
        for y in y0..<y1 {
            for x in x0..<x1 {
                let o = y * bytesPerRow + x * 4
                let d = max(abs(Int(bytes[o]) - bg.0),
                            max(abs(Int(bytes[o + 1]) - bg.1), abs(Int(bytes[o + 2]) - bg.2)))
                if isTextInk(delta: d) { pixels += 1 }
            }
        }
        return (pixels, Double(pixels) / Double(x1 - x0) / Double(y1 - y0))
    }

    /// **说明文字必须画全**（R28 / U-50 / D-087；R28b 把参照臂从"更宽"换成"更窄"）。
    ///
    /// 缺陷：`HotKeySettingsRow` 的说明带着 `.lineLimit(1)`，三行说明里被切掉的恰好是
    /// 最长、也最有信息量的那一条 —— `HotKeyAction.quickPick.description` 后半句
    /// 是"默认 ⌃⌥⇧V，刻意不是 ⌘⇧V（那是浏览器/编辑器的粘贴并匹配样式）"，
    /// 屏幕上只剩"…直接粘回原应用。…"。写进文案的理由一个字都没露。
    ///
    /// **为什么不是"拿一张不可能被截断的宽帧当参照"**：那是第一版，本机全绿，
    /// 而 CI 的 macos-15 runner 上 1100pt 与 900pt 两档**整帧读出 0 墨**
    /// （run 38449711539 / 38451162726）；仓库里 ≤750pt 的 100 张帧从来没有过这个问题
    /// （R3-D11 记的 `content-wide-1100x800` 95% 未绘制是同一族）。
    /// 我当时猜"越过 2048px 的离屏上限"，**900pt 那一档把它证伪了** —— 所以这里只记现象。
    ///
    /// 换成方向相反的对照：`settings-min`（640pt）与产品默认宽（720pt）都在 runner 拍得出来的那一档。
    /// 说明文字要占的列宽随窗口走，所以
    /// **只要有任何一行被截断，窄的那一臂一定比宽的那一臂少画字**；
    /// 而两臂都画全时，同一批字换行位置不同、墨量相同 ⇒ 比值 1.0。
    /// 地板 0.97：允许 3% 的行末留白与抗锯齿差。实测：修后 0.999 / 1.001，
    /// 装回 `.lineLimit(1)`（变异 M123）掉到 0.925。
    ///
    /// 这条对照抓不住"两臂被截得一模一样"的那种坏（那需要一个真正不受宽度约束的参照），
    /// 那句话写在 `AGENT_UI_AUDIT` 第 30 轮末尾，别让下一轮把它当成那个用。
    func testSettingsHelperTextIsNotClipped() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r28-clip-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            var masses: [String: Int] = [:]
            var fractions: [String: Double] = [:]
            for name in ["settings-shortcuts", "settings-min"] {
                guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                    return XCTFail("找不到夹具 \(name) ⇒ 这条两臂对照没有对象")
                }
                // 两臂都必须落在 runner 拍得出来的那一档（R28b 实测 900pt 就已经读 0 墨）。
                XCTAssertLessThanOrEqual(fixture.size.width, 750,
                            "\(name) 宽 \(fixture.size.width)pt ⇒ 超出 CI runner 拍得出来的那一档，"
                            + "这条对照会在 CI 上恒红（或在被放宽之后恒绿）")
                let file = scratch.appendingPathComponent("\(name)-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(name) 读不回来 ⇒ 捕获路径坏了")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                // 这一行是 BACKLOG 43 的实验本体：三种可能（没画 / 画成一块底色 /
                // 位图字节布局与尺的假设不符）各自会留下不同的指纹。
                // CI 第一次的读数（run 38454852737）已经排掉一种：**px=720x540 scale=1.0**
                // ⇒ runner 是 @1x 截图，本机是 @2x —— 这也顺带解释了 R27 那两处"低对比度"。
                emit("TEXT_INK_FRAME \(name) \(tag) px=\(rep.pixelsWide)x\(rep.pixelsHigh) "
                      + "scale=\(scale) bpp=\(rep.bitsPerPixel) samples=\(rep.samplesPerPixel) "
                      + "bpr=\(rep.bytesPerRow) transparent="
                      + String(format: "%.1f%%", Self.transparentFraction(of: rep) * 100)
                      + " " + Self.lumaHistogram(bytes: base, width: rep.pixelsWide,
                                                height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow))
                // 只量内容列：侧栏那一列不参与比较（它的图标是已知不可信的反相面，
                // 见 `OffscreenSymbolInkProbeTests`）。
                let rect = CGRect(x: CGFloat(SettingsViewLayout.sidebarWidth), y: 0,
                                  width: fixture.size.width - SettingsViewLayout.sidebarWidth,
                                  height: fixture.size.height)
                let (pixels, fraction) = Self.textInkMass(bytes: base, width: rep.pixelsWide,
                                                          height: rep.pixelsHigh,
                                                          bytesPerRow: rep.bytesPerRow,
                                                          rect: rect, scale: scale)
                masses[name] = pixels
                fractions[name] = fraction
            }
            guard let wide = masses["settings-shortcuts"], let narrow = masses["settings-min"] else {
                return XCTFail("两臂质量没拿到 ⇒ 循环写坏了")
            }
            if wide == 0 || narrow == 0 {
                // **这台机器拍不出「设置」这一页**（CI 的 macos-15 runner 实测：
                // `settings-*` 整帧均匀一色，而 430/750pt 的其它帧正常 —— run 38453566489）。
                // 这不是产品缺陷，也不是"判据通过"，是**观测不到** ⇒ 明确记 NOT-RUN，
                // 并把诊断打出来让下一次 CI 替我们回答"那一帧到底是什么"。
                // 记账在 BACKLOG 43；本机这条是实跑的（wide=23889 / narrow=23868）。
                emit("TEXT_INK_NOT_RUN \(tag) 720=\(wide) 640=\(narrow) "
                      + "⇒ 这台机器拍不出设置页，这条对照没有对象")
                throw XCTSkip("TEXT_INK_NOT_RUN：本机/本平台无法渲染 settings-* 帧 ⇒ "
                              + "对照判据记为未运行，不算通过（见 BACKLOG 43）")
            }
            XCTAssertGreaterThanOrEqual(fractions["settings-shortcuts"] ?? 0, InkFloor.paneInkFraction,
                                        "内容列的墨只有 "
                                        + String(format: "%.2f%%", (fractions["settings-shortcuts"] ?? 0) * 100)
                                        + " ⇒ 量错了地方，不是产品截断了字")
            // **两臂必须真的差一截**：同一宽度自比 ⇒ 比值恒等于 1，而全仓没有第二条会红。
            // 60pt 是"至少能多切掉两三个汉字"的下限（说明文字约 10.4pt/字）。
            guard let wideFixture = fixtures(appearance: appearance).first(where: { $0.name == "settings-shortcuts" }),
                  let narrowFixture = fixtures(appearance: appearance).first(where: { $0.name == "settings-min" }) else {
                return XCTFail("两臂夹具缺一即判据无对象")
            }
            XCTAssertLessThanOrEqual(narrowFixture.size.width, wideFixture.size.width - 60,
                        "窄臂 \(narrowFixture.size.width)pt 与产品臂 \(wideFixture.size.width)pt 差得不够 ⇒ "
                        + "两臂自比，这条对照恒真")
            let ratio = Double(narrow) / Double(wide)
            emit("TEXT_INK \(tag) 产品宽 720=\(wide) 窄臂 640=\(narrow) ratio=\(String(format: "%.3f", ratio))")
            XCTAssertGreaterThanOrEqual(ratio, 0.97,
                        "窗口从 720pt 收到 640pt 之后，这一页少画了 "
                        + String(format: "%.1f%%", (1 - ratio) * 100)
                        + " 的字（\(tag)，720=\(wide) / 640=\(narrow)）⇒ 有说明文字被截断了。"
                        + "（R28 装回 `.lineLimit(1)` 的变异实测 0.925）。"
                        + "被切掉的正是「刻意不是 ⌘V」那半句理由")
        }
    }

    /// 真值表：`textInkMinDelta` 这一道闸门放谁进来。
    ///
    /// 每条都是**量出来的数**，不是编的：亮色背景 248 上
    /// GroupBox 底 242 / 录制框底 222 / `.secondary` 说明文字 139 / `.primary` 标题 39。
    /// 这一档一旦挪到 24（R24 那批用的值），第 ② 条会红 —— 那正是"平涂把信号淹掉"的形状。
    func testTextInkGateTruthTable() throws {
        XCTAssertEqual(Self.isTextInk(delta: 6), false, "GroupBox 底色不许算成字")
        XCTAssertEqual(Self.isTextInk(delta: 26), false, "录制框/药丸的平涂底色不许算成字")
        XCTAssertEqual(Self.isTextInk(delta: 60), false, "等于地板不算（闸门是严格大于）")
        XCTAssertEqual(Self.isTextInk(delta: 109), true, ".secondary 的说明文字必须算成字")
        XCTAssertEqual(Self.isTextInk(delta: 209), true, ".primary 的标题必须算成字")
        // 暗色同一组：背景 30，平涂 55，次级文字 140，主文字 235。
        XCTAssertEqual(Self.isTextInk(delta: 25), false, "暗色的控件平涂底色不许算成字")
        XCTAssertEqual(Self.isTextInk(delta: 110), true, "暗色的说明文字必须算成字")
    }

    /// **夹具必须注入产品在注入的每一根 `*Action` 接缝**（R28）。
    ///
    /// 起因：`makeSettingsView` 没传 `exportHistoryAction` / `importHistoryAction`，
    /// 而视图里它们是 `.disabled(x == nil)` 的开关 ⇒ 「数据」页那两张帧里
    /// 导出/导入两颗**一直是禁用态**，产品里从来没有这个状态。
    /// 于是帧基线把禁用态钉成了"标准"，真接坏了反而**画面一模一样、一条不红**。
    ///
    /// 名单从产品的调用点推导，不手抄（R21 那条"手抄名单漂了两次"的教训）：
    /// 读 `SettingsWindowController` 里 `SettingsView(` 那一段的实参标签，
    /// 取以 `Action` 结尾的那些，逐个要求在夹具里出现。
    /// 以后产品再加一根接缝而夹具忘了跟，这条会红。
    func testCaptureFixtureInjectsEveryActionSeamTheProductInjects() throws {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // Tests/ClipboardHistoryAppTests
            .deletingLastPathComponent()   // Tests
            .deletingLastPathComponent()   // ClipboardHistory
            .appendingPathComponent("Sources/ClipboardHistoryApp/Managers/SettingsWindowController.swift")
        guard let controller = try? String(contentsOf: root, encoding: .utf8) else {
            return XCTFail("读不到 \(root.lastPathComponent) ⇒ 这条守卫没有对象，等于恒真")
        }
        // 只看产品构造 SettingsView 的那一段，别把文件里其它闭包算进来。
        guard let start = controller.range(of: "SettingsView(") else {
            return XCTFail("产品里找不到 `SettingsView(` 的构造点 ⇒ 名单无从推导")
        }
        let call = controller[start.lowerBound...]
        let labels = ["clearHistoryAction", "exportHistoryAction", "importHistoryAction"]
            .filter { call.contains("\($0):") }
        XCTAssertGreaterThanOrEqual(labels.count, 3,
                    "从产品调用点只数出 \(labels.count) 根 `*Action` 接缝 "
                    + "⇒ 要么构造点被搬走了，要么这段解析已经不对，两种情况这条守卫都不再有用")

        let harness = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        guard let at = harness.range(of: "private func makeSettingsView") else {
            return XCTFail("找不到夹具构造函数 ⇒ 这条守卫没有对象")
        }
        let fixtureCall = harness[at.lowerBound...]
        for label in labels {
            XCTAssertTrue(fixtureCall.contains("\(label):"),
                          "产品注入的接缝「\(label)」夹具没注入 ⇒ 帧里那颗控件是**禁用态**，"
                          + "而发出去的包里没有这个状态；帧基线会把禁用态钉成标准")
        }
    }

    /// 整帧的粗灰度直方图（8 档 × 百分比）。用途只有一个：
    /// 分清"整帧一个颜色"（一档 100%）与"有内容但我的尺看不见"（多档分布）。
    static func lumaHistogram(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                              bytesPerRow: Int) -> String {
        var buckets = [Int](repeating: 0, count: 8)
        var total = 0
        var y = 0
        while y < height {
            var x = 0
            while x < width {
                let o = y * bytesPerRow + x * 4
                let l = (Int(bytes[o]) * 3 + Int(bytes[o + 1]) * 6 + Int(bytes[o + 2])) / 10
                buckets[min(7, l / 32)] += 1
                total += 1
                x += 4   // 每 4 个像素采一个，够分辨"一块底色"了
            }
            y += 4
        }
        guard total > 0 else { return "hist=empty" }
        return "hist=" + buckets.map { String(format: "%.0f", Double($0) * 100 / Double(total)) }
                                 .joined(separator: "/") + "%"
    }

    /// 一块矩形里"红减蓝"的均值 —— 分得出"中性灰/白"与"橙 12%/红 10%"的那根轴。
    ///
    /// 为什么不用亮度：标题栏后那条底色与它自己的底色在亮度上只差 4，
    /// 而 R-B 差 26 对 0。**轴的分辨率必须配得上要分的表面**
    /// （账本里"只用亮度判两态可分辨是用错轴"的同族）。
    static func redMinusBlue(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                             bytesPerRow: Int, rect: CGRect, scale: Double) -> Double {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return 0 }
        var total = 0.0
        var count = 0
        for y in y0..<y1 {
            var x = x0
            while x < x1 {
                let o = y * bytesPerRow + x * 4
                total += Double(bytes[o]) - Double(bytes[o + 2])
                count += 1
                x += 1
            }
        }
        return count == 0 ? 0 : total / Double(count)
    }

    /// 哪些横幅帧要判"底色不许涂到标题栏后面"（R23）。
    static let noticeChromeFixtures: [String] = ["content-with-notice", "content-with-two-notices"]

    /// **提示条的底色不许越进窗口装饰那一条**（R23 / U-45 / D-082）。
    ///
    /// 缺陷是 R22 新增那张"两条横幅同时在"的帧里量出来的：
    /// 一条文字的警告横幅占了 88pt，其中 y 0–52 **只有底色、没有内容** ——
    /// 也就是颜色涂到了透明标题栏与红绿灯后面，而文字被安全区顶到 y≈60 才开始。
    /// 根因是 SwiftUI 4 起 `.background(ShapeStyle)` 默认 `ignoresSafeAreaEdges: .all`。
    /// 修完之后同一条带是 52–90（38pt），上面那条 0–48 是纯白。
    ///
    /// 这条判据**同时带正对照**：它先要求"横幅自己那条带确实是橙/红的"（R-B ≥ 8），
    /// 否则一张空白帧也能让"顶部没色"这条绿着通过 —— 与 R22 那条 `contentMustFit`
    /// 的正对照同一个理由。
    ///
    /// 自己拍自己量（R20 立的规矩）。
    func testNoticeTintDoesNotReachTheTitlebar() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r23-chrome-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for name in Self.noticeChromeFixtures {
                guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                    return XCTFail("找不到夹具 \(name) ⇒ 这条判据没有对象")
                }
                let file = scratch.appendingPathComponent("\(name)-judged-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                // 窗口装饰那一条：0–46pt（实测安全区 52pt，留 6pt 余量给边框抗锯齿）。
                let chrome = CGRect(x: 40, y: 4, width: 300, height: 42)
                // 横幅自己那一条：安全区之下、第一行文字之上（实测 56–86pt）。
                let band = CGRect(x: 40, y: 56, width: 300, height: 30)
                let bandTint = Self.redMinusBlue(bytes: base, width: rep.pixelsWide,
                                                 height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                 rect: band, scale: scale)
                let chromeTint = Self.redMinusBlue(bytes: base, width: rep.pixelsWide,
                                                   height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                   rect: chrome, scale: scale)
                // ① 正对照：横幅那条带必须有暖色，否则"顶上没色"这句话没有对照物。
                XCTAssertGreaterThan(bandTint, 8,
                                     "\(name)（\(tag)）在 y 56–86 只读到 R-B=\(String(format: "%.1f", bandTint))"
                                     + " ⇒ 这里本该是警告/错误的底色。**尺读不到底色时，下面那条'标题栏没被涂'的绿没有意义**")
                // ② 判据：装饰那一条必须是中性底。
                XCTAssertLessThan(abs(chromeTint), 4,
                                  "\(name)（\(tag)）的窗口装饰区（y 4–46）读到 R-B=\(String(format: "%.1f", chromeTint))"
                                  + " ⇒ 提示条的底色涂到了标题栏/红绿灯后面（横幅自己那一条是 "
                                  + String(format: "%.1f", bandTint) + "）。"
                                  + "修法见 `NoticeBanner`：`.background(_, ignoresSafeAreaEdges: [])")
                emit("NOTICE_CHROME \(name) \(tag) bandR-B=\(String(format: "%.1f", bandTint)) "
                      + "chromeR-B=\(String(format: "%.1f", chromeTint))")
            }
        }
    }

    // MARK: - 横幅正文的对比度（R24 / BACKLOG 34 + 36）

    /// 一条被涂了色的带（= 一条横幅）在帧里的位置，加上**它自己那段文字**的读数。
    struct NoticeBand {
        let startPt: Double
        let endPt: Double
        let chroma: Double
        let ratio: Double
        let inkFraction: Double
        /// 动作按钮那三个字（"知道了"）的行的中心；没找到按钮就是 nil。
        let actionCenterPt: Double?
        /// 判据实际量文字的那块矩形（夹具坐标，pt）。带着它是因为"文字必须从这一列的
        /// 左起三分之一里开始"这条地板要用到它的宽度（R26 / BACKLOG 38）。
        let textColumn: CGRect
        /// `textColumn` 里最左的强墨列；整列没有墨就是 nil。
        let textLeadingPt: Double?

        var centerPt: Double { (startPt + endPt) / 2 }
    }

    /// 一块矩形里**最左的有墨列**（夹具坐标，pt）。找不到返回 nil。
    ///
    /// `minDelta` 是这根尺的"什么算墨"：文字要用 40（强墨，避开抗锯齿），
    /// 而骨架条带只有 6 —— 它的底与面板差 13 个亮度级，用 40 去量会得到"条带不存在"，
    /// 那正是"把尺调瞎然后宣布没问题"（R24 的 M107 同一族）。
    /// 一列至少要有 `minInkPerColumn` 个墨像素才算，避免一个坏点决定整条左轴。
    static func leadingInkColumn(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                 bytesPerRow: Int, rect: CGRect, scale: Double,
                                 minDelta: Int = 40, minInkPerColumn: Int = 3) -> Double? {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return nil }
        func luma(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return (Int(bytes[o]) * 299 + Int(bytes[o + 1]) * 587 + Int(bytes[o + 2]) * 114) / 1000
        }
        // 底取整块矩形的众数亮度（不是逐行）：一条横幅/一块骨架只有一个底。
        var histogram: [Int: Int] = [:]
        for y in stride(from: y0, to: y1, by: 2) {
            for x in stride(from: x0, to: x1, by: 2) { histogram[luma(x, y) / 4, default: 0] += 1 }
        }
        let background = (histogram.max { $0.value < $1.value }?.key ?? 0) * 4 + 2
        for x in x0..<x1 {
            var ink = 0
            for y in y0..<y1 where abs(luma(x, y) - background) > minDelta { ink += 1 }
            if ink >= minInkPerColumn { return Double(x) / scale }
        }
        return nil
    }

    /// `leadingInkColumn` 的**右镜像**：一块矩形里最后一列有墨的 x（pt）。
    ///
    /// 为什么 R34 才加：左边界能判"对齐"，右边界能判的是**截断有没有留痕迹**。
    /// 一行 `lineLimit(1)` 的文字如果被容器切掉，它会以"…"收尾；如果是整块被裁，
    /// 那**最后一个字的笔画会正好停在帧的最后一列** —— 这两种"放不下"在像素上的区别
    /// 只有右边界看得见（R33 在菜单栏面板上第一次撞到：理由的墨画到 x=319.5，而帧宽 320）。
    /// 读法与 `leadingInkColumn` 完全一致（同一块底、同一个 `minDelta`、同一档每列最少墨数），
    /// 所以两条可以拿同一张帧对账。
    static func trailingInkColumn(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                  bytesPerRow: Int, rect: CGRect, scale: Double,
                                  minDelta: Int = 40, minInkPerColumn: Int = 3) -> Double? {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return nil }
        func luma(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return (Int(bytes[o]) * 299 + Int(bytes[o + 1]) * 587 + Int(bytes[o + 2]) * 114) / 1000
        }
        var histogram: [Int: Int] = [:]
        for y in stride(from: y0, to: y1, by: 2) {
            for x in stride(from: x0, to: x1, by: 2) { histogram[luma(x, y) / 4, default: 0] += 1 }
        }
        let background = (histogram.max { $0.value < $1.value }?.key ?? 0) * 4 + 2
        for x in stride(from: x1 - 1, through: x0, by: -1) {
            var ink = 0
            for y in y0..<y1 where abs(luma(x, y) - background) > minDelta { ink += 1 }
            if ink >= minInkPerColumn { return Double(x + 1) / scale }
        }
        return nil
    }

    /// 一块矩形里"有墨的行"从第几行到第几行（夹具坐标系，pt）。
    ///
    /// 按行而不是按整体包围盒：动作位只有一个文字块，取"首末有墨行的中点"就是它的光学中心，
    /// 而整体包围盒会被按钮的圆角底/阴影拉大 —— 那 2pt 的差别正好是这条判据的分辨率。
    /// 一行至少要有 `minInkPerRow` 个墨像素才算有墨：抗锯齿的一两个点不算字。
    static func inkRowSpan(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                           bytesPerRow: Int, rect: CGRect, scale: Double,
                           minInkPerRow: Int = 3) -> (startPt: Double, endPt: Double)? {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0 + 4, y1 > y0 else { return nil }
        var first = -1, last = -1
        for y in y0..<y1 {
            let row = y * bytesPerRow
            var histogram: [Int: Int] = [:]
            var x = x0
            while x < x1 {
                let o = row + x * 4
                histogram[(Int(bytes[o]) + Int(bytes[o + 1]) + Int(bytes[o + 2])) / 3, default: 0] += 1
                x += 1
            }
            let background = histogram.max { $0.value < $1.value }?.key ?? 0
            var ink = 0
            x = x0
            while x < x1 {
                let o = row + x * 4
                let luma = (Int(bytes[o]) + Int(bytes[o + 1]) + Int(bytes[o + 2])) / 3
                if abs(luma - background) > 40 { ink += 1 }
                x += 1
            }
            if ink >= minInkPerRow {
                if first < 0 { first = y }
                last = y
            }
        }
        guard first >= 0, last > first else { return nil }
        return (Double(first) / scale, Double(last + 1) / scale)
    }

    /// **自己找带、自己分段、自己量对比**的尺。
    ///
    /// 为什么不让判据写死 y 区间：写死等于把"布局今天长什么样"钉进判据 —— 布局一动，
    /// 框就套到空白上，而它报回来的数仍然"像模像样"（R21 那两个贴空的框就是这么把
    /// 一次假结论读成"清除 × 只有 1.9:1"的）。现在带在哪、有几条、缝多宽，全是量出来的。
    ///
    /// 分带规则：逐行取该行的**众数颜色** ⇒ R−B > 6 算"这一行被涂了暖色"；
    /// 同一带内众数亮度变化 > 1 就断开（警告 12% 橙与错误 10% 红的底色差 3 个亮度级，
    /// 正好能把挨着的两条分开 —— 产品帧实测 243 / 240）。
    /// 文字列避开两端：左边 36pt 之后（图标占 14–30，那颗饱和的橙/红图标不是"正文"），
    /// 右边留 95pt（那枚"知道了"是 `.primary` 的，混进来会把弱正文抬过线 —— 正是要防的"用错对照物"）。
    static func noticeBands(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                            bytesPerRow: Int, scale: Double) -> [NoticeBand] {
        func rowModal(_ y: Int) -> (r: Int, g: Int, b: Int) {
            var histogram: [Int: Int] = [:]
            var x = 0
            while x < width {
                let o = y * bytesPerRow + x * 4
                // 16 级量化：不量化的话抗锯齿会把每个颜色摊薄成"只出现一次"，众数就没意义了。
                // **括号是必需的**：Swift 里 `<<` 的优先级高于 `/`，
                // `Int(bytes[o]) / 16 << 8` 会被读成 `255 / (16 << 8)` = 0 ——
                // 我第一次移植这版时没加括号，于是"整把尺永远找不到带"，
                // 而它表现成"0 条带"而不是崩溃（正对照那条才把它逼出来）。
                let key = ((Int(bytes[o]) / 16) << 8) | ((Int(bytes[o + 1]) / 16) << 4) | (Int(bytes[o + 2]) / 16)
                histogram[key, default: 0] += 1
                x += 1
            }
            let key = histogram.max { $0.value < $1.value }?.key ?? 0
            return ((key >> 8) * 16 + 8, ((key >> 4) & 0xF) * 16 + 8, (key & 0xF) * 16 + 8)
        }
        func lumaOf(_ c: (r: Int, g: Int, b: Int)) -> Int {
            Int((0.2126 * Double(c.r) + 0.7152 * Double(c.g) + 0.0722 * Double(c.b)).rounded())
        }
        let frameWidthPt = Double(width) / scale
        var bands: [NoticeBand] = []
        var start = -1
        var anchorLuma = 0
        var anchorChroma = 0.0
        func close(_ end: Int) {
            defer { start = -1 }
            guard start >= 0 else { return }
            let startPt = Double(start) / scale, endPt = Double(end) / scale
            guard endPt - startPt >= 12 else { return }   // 发丝线与投影边缘不算一条带
            let rect = CGRect(x: 36, y: startPt + 2,
                              width: max(20, frameWidthPt - 95 - 36), height: endPt - startPt - 4)
            let (ratio, inkFraction) = Self.inkContrast(bytes: bytes, width: width, height: height,
                                                        bytesPerRow: bytesPerRow, rect: rect, scale: scale)
            let textLeading = Self.leadingInkColumn(bytes: bytes, width: width, height: height,
                                                    bytesPerRow: bytesPerRow, rect: rect, scale: scale)
            // 动作按钮那一块：**只取最右侧 50pt**（帧宽 −60 … −10）。
            // 第一版取的是右侧 95pt，结果在产品那张 750pt 宽的帧上量出 −4.2pt 的"偏上"，
            // 而同一套代码在 560pt 宽的组件帧上量出 +0.0 —— 差的不是布局，是**框里混进了正文**：
            // 长句的第一行一直排到 x≈670，正好落进 655 起的那个数框里，
            // 于是"首末有墨行"被正文的第一行抬上去了。⇒ 与 R24 的 M108 同一族：
            // 数框的边界必须由"被量对象的实际位置"决定，不能由一个看起来够宽的常数决定。
            let actionRect = CGRect(x: max(36, frameWidthPt - 60), y: startPt,
                                    width: min(50, frameWidthPt - max(36, frameWidthPt - 60) - 10),
                                    height: endPt - startPt)
            let span = Self.inkRowSpan(bytes: bytes, width: width, height: height,
                                       bytesPerRow: bytesPerRow, rect: actionRect, scale: scale)
            bands.append(NoticeBand(startPt: startPt, endPt: endPt, chroma: anchorChroma,
                                    ratio: ratio, inkFraction: inkFraction,
                                    actionCenterPt: span.map { ($0.startPt + $0.endPt) / 2 },
                                    textColumn: rect, textLeadingPt: textLeading))
        }
        for y in 0..<height {
            let modal = rowModal(y)
            let chroma = Double(modal.r - modal.b)
            let l = lumaOf(modal)
            if chroma > 6 {
                if start < 0 { start = y; anchorLuma = l; anchorChroma = chroma }
                else if abs(l - anchorLuma) > 1 { close(y); start = y; anchorLuma = l; anchorChroma = chroma }
            } else if start >= 0 {
                close(y)
            }
        }
        if start >= 0 { close(height) }
        return bands
    }

    /// 哪些帧要判"横幅正文读不读得出来"，以及每张帧**应该**有几条带。
    /// 条数写在这里而不是"找到几条判几条"：两条同时在的那张帧如果只找到一条，
    /// 说明其中一条的底色没了（或被并成一条），那是缺陷，不是"少判一条"。
    static let noticeTextFixtures: [(name: String, minBands: Int)] = [
        ("content-with-notice", 1),
        ("content-with-two-notices", 2),
        ("content-with-copy-failure-notice", 1),
        // R41：同一句话在最窄窗口那一臂。条数仍是 1（一条横幅），判的是
        // "换行之后读不读得出来、按钮还在不在它该在的地方"。
        ("content-min-with-copy-failure-notice", 1),
        ("notice-banner", 2),
    ]

    /// **横幅正文必须比它自己那枚按钮更显眼，至少不能读不出来**（R24 / U-46 / D-083）。
    ///
    /// 修之前量到的（`/tmp/r24-shots`，逐带自动定位）：
    /// 亮色 3.90 / 3.85（组件帧两条）、3.92 / 3.82（产品两张帧），
    /// 而同一帧里那枚"知道了"是 **12.28** —— 同一条横幅内，"下一步"比"发生了什么"清楚三倍，
    /// 并且 4.5:1 的 AA 线**没过**。暗色 5.26–5.58 本来就过，所以这不是"修暗色"，
    /// 是把"这条文案有多重要"这件事从 `StatePresentation` 里补出来（见 `messageInk(for:)`）。
    ///
    /// 同一条判据顺手管住了 BACKLOG 36：带与带之间的**无底色空缝**必须 ≤ 2pt。
    /// 组件帧以前写的是 `VStack(spacing: 12)`，量出来缝 13pt，而产品是 1pt 的发丝线 ——
    /// 也就是说那张帧一直在展示一个产品里不存在的布局。
    ///
    /// 自己拍自己量（R20 立的规矩）：判据自己起进程拍帧，不读上一轮的 PNG。
    func testNoticeBodyTextStaysReadable() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r24-notice-text-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for (name, minBands) in Self.noticeTextFixtures {
                guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                    return XCTFail("找不到夹具 \(name) ⇒ 这条判据没有对象")
                }
                let file = scratch.appendingPathComponent("\(name)-judged-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let bands = Self.noticeBands(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow, scale: scale)
                XCTAssertGreaterThanOrEqual(bands.count, minBands,
                                            "\(name)（\(tag)）只找到 \(bands.count) 条色带，期望 ≥ \(minBands)"
                                            + " ⇒ 要么某条横幅的底色没了，要么尺瞎了（先跑 `testNoticeBandFinderReadsBothEnds`）")
                for (index, band) in bands.enumerated() {
                    let where_ = "\(name)（\(tag)）第 \(index + 1) 条带 y \(String(format: "%.0f", band.startPt))–\(String(format: "%.0f", band.endPt))"
                    XCTAssertGreaterThanOrEqual(band.inkFraction, InkFloor.bandInkFraction,
                                                "\(where_) 文字列里只有 "
                                                + String(format: "%.1f%%", band.inkFraction * 100) + " 的墨"
                                                + " ⇒ 这条带里没有字，对比度判据对它没有意义（框找错了，不许调地板）")
                    // ①b **左锚定**（R26 / BACKLOG 38）：左对齐的正文必须在文字列的左起三分之一里开始。
                    //     R24 的 M108 证伪过"带里有墨"这条地板 —— 框挪到按钮上时墨占比 10.9% 照样过，
                    //     也就是说它只挡"框套在纯底色上"，挡不住"框里躺着别的控件"。这一条补的正是那道缝：
                    //     消息整条不见了、只剩右边那颗按钮时，量到的墨仍然"够"，但它不在左边。
                    XCTAssertLessThanOrEqual(band.textLeadingPt ?? .infinity,
                                             band.textColumn.minX + band.textColumn.width / 3,
                                             "\(where_) 最左的墨出现在 x="
                                             + String(format: "%.1f", band.textLeadingPt ?? -1)
                                             + "，而文字列从 "
                                             + String(format: "%.1f", band.textColumn.minX)
                                             + " 起、宽 "
                                             + String(format: "%.1f", band.textColumn.width)
                                             + " ⇒ 这一列里没有正文，量到的墨是别的东西（按钮/图标）。"
                                             + "R24 的 M108 就是这一族：'带里有墨'挡不住'框里有按钮'")
                    // R29b：正文这条也挂上方向诊断。挂之前先**量过**（不是假设）：
                    // 彩色带上的深字在亮色里尾墨落暗侧、暗色里落亮侧，
                    // 实测读数由下面这条打印给出（`NOTICE_SIDE`）。
                    let noticeTail = Self.inkTailSplit(bytes: base, width: rep.pixelsWide,
                                                       height: rep.pixelsHigh,
                                                       bytesPerRow: rep.bytesPerRow,
                                                       rect: band.textColumn, scale: scale)
                    emit("NOTICE_SIDE \(name) \(tag) 尾墨 亮\(noticeTail.brighter)/暗\(noticeTail.darker)")
                    XCTAssertTrue(Self.inkIsOnTheExpectedSide(brighter: noticeTail.brighter,
                                                             darker: noticeTail.darker,
                                                             darkAppearance: appearance == .darkAqua),
                                  "\(where_) 横幅正文的墨落在背景的**另一侧**"
                                  + "（亮\(noticeTail.brighter)/暗\(noticeTail.darker)）⇒ 这是反相，不是淡："
                                  + "一行产品代码都不许改，去查捕获路径（R28 的侧栏图标就是这一族）")
                    XCTAssertGreaterThanOrEqual(band.ratio, InkFloor.bodyTextContrast,
                                                "\(where_) 正文对底色只有 "
                                                + String(format: "%.2f", band.ratio) + ":1（地板 "
                                                + "\(InkFloor.bodyTextContrast)，13pt 常规文字要过 WCAG AA）。"
                                                + "以前这四个读数是 3.82–3.92，而同一帧的按钮是 12.28。"
                                                + "墨色归 `StatePresentation.messageInk(for:)` 管"
                                                + "\n" + Self.inkDiagnosisLine(tail: noticeTail,
                                                                               darkAppearance: appearance == .darkAqua))
                    guard index > 0 else { continue }
                    let seam = band.startPt - bands[index - 1].endPt
                    XCTAssertLessThanOrEqual(seam, InkFloor.bandSeamPt,
                                             "\(name)（\(tag)）两条横幅之间有 \(String(format: "%.1f", seam))pt "
                                             + "**没有底色的空缝** ⇒ 有人往横幅之间塞了 spacing。"
                                             + "产品的语言是 `VStack(spacing: 0)` + 每条自带一条 `Divider()`（实测缝 1pt）")
                }
                emit("NOTICE_TEXT \(name) \(tag) bands=\(bands.count) "
                      + bands.map { String(format: "y%.0f-%.0f ratio=%.2f ink=%.1f%%",
                                           $0.startPt, $0.endPt, $0.ratio, $0.inkFraction * 100) }
                      .joined(separator: " | "))
            }
        }
    }

    /// **动作按钮要垂直居中在它那条带里**（R25 / U-47 / D-084 / BACKLOG 37）。
    ///
    /// 修之前的实测偏差（字形行的中心 vs 带中心，两外观一致）：
    /// 单行 **0pt**（碰巧对，所以这张帧从来没暴露过它）、两行 **−6.5pt**、三行 **−14.5pt**。
    /// 这两个数是两条独立的尺互相核过的：CLI（`.scratch/motion-audit-2/ink_probe_r24.swift rows`）
    /// 在修前的帧上读出 71.0/118.0 对带中心 77.5/132.5，仓库内判据在变异 M110 里读出 −6.5。
    /// 根因是 `StateLine` 整行按 `.firstTextBaseline` 排，于是两三行正文时
    /// 那颗"知道了"跟着**第一行**走 —— 读起来像"这个动作只管第一句"，
    /// 而系统那类顶部提示条的动作位都是垂直居中的。
    ///
    /// 判据不写死按钮坐标：带的位置由 `noticeBands` 自己找，按钮的位置由 `inkRowSpan`
    /// 在带的右侧 95pt 里自己找。⇒ 布局漂移时它会红在"没找到按钮"，而不是绿在"读到 0 偏差"。
    func testNoticeActionIsVerticallyCenteredInItsBand() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r25-action-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for (name, _) in Self.noticeTextFixtures {
                guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                    return XCTFail("找不到夹具 \(name) ⇒ 这条判据没有对象")
                }
                let file = scratch.appendingPathComponent("\(name)-action-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("刚拍出来的 \(file.lastPathComponent) 读不回来 ⇒ 捕获路径坏了")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let bands = Self.noticeBands(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow, scale: scale)
                XCTAssertFalse(bands.isEmpty, "\(name)（\(tag)）一条带都没找到 ⇒ 尺没有对象")
                for (index, band) in bands.enumerated() {
                    let where_ = "\(name)（\(tag)）第 \(index + 1) 条带 y \(String(format: "%.0f", band.startPt))–\(String(format: "%.0f", band.endPt))"
                    guard let action = band.actionCenterPt else {
                        XCTFail("\(where_) 在带的右侧没找到动作按钮的字形 ⇒ 要么按钮不在了，"
                                + "要么它不在右侧 95pt 里（判据的位置假设需要重看）")
                        continue
                    }
                    let offset = action - band.centerPt
                    XCTAssertLessThanOrEqual(abs(offset), InkFloor.actionCenterTolerancePt,
                                             "\(where_) 的动作按钮偏了 \(String(format: "%.1f", offset))pt"
                                             + "（容差 \(InkFloor.actionCenterTolerancePt)）⇒ 它跟着第一行走，"
                                             + "读起来像只管第一句话。修前实测：单行 0pt / 两行 −6.5pt / 三行 −14.5pt")
                    emit("NOTICE_ACTION \(name) \(tag) band#\(index + 1) center="
                          + String(format: "%.1f", band.centerPt) + " action="
                          + String(format: "%.1f", action) + " offset="
                          + String(format: "%+.1f", offset))
                }
            }
        }
    }

    /// 新尺子的正对照：**同一套几何，好墨读过、坏墨必须读不过**。
    ///
    /// 一把只在缺陷上红的尺，与一把永远绿的尺一样没有信息量（R21 的探针表同一个理由）。
    /// 这里不碰产品，只喂两块自造像素：唯一变量是"字的颜色"。
    /// 这一条**不覆盖管线**（判的是纯函数），管线级判据是上面那条 `testNoticeBodyTextStaysReadable`。
    func testNoticeBandFinderReadsBothEnds() {
        let width = 400, height = 60, bytesPerRow = width * 4
        func buffer(textInk: (Int, Int, Int)) -> [UInt8] {
            var bytes = [UInt8](repeating: 0, count: height * bytesPerRow)
            for y in 0..<height {
                let tinted = y >= 10 && y < 40
                for x in 0..<width {
                    var (r, g, b) = tinted ? (255, 235, 230) : (255, 255, 255)
                    // "文字"：x 40..<290 之间每 6px 一道 2px 竖笔，y 15..<35
                    if tinted, x >= 40, x < 290, (x - 40) % 6 < 2, y >= 15, y < 35 {
                        (r, g, b) = textInk
                    }
                    let o = y * bytesPerRow + x * 4
                    bytes[o] = UInt8(r); bytes[o + 1] = UInt8(g); bytes[o + 2] = UInt8(b); bytes[o + 3] = 255
                }
            }
            return bytes
        }
        let goodPixels = buffer(textInk: (30, 30, 30))
        let weakPixels = buffer(textInk: (215, 205, 200))
        func read(_ bytes: [UInt8]) -> [NoticeBand] {
            bytes.withUnsafeBufferPointer { Self.noticeBands(bytes: $0.baseAddress!, width: width,
                                                             height: height, bytesPerRow: bytesPerRow, scale: 1.0) }
        }
        let goodBands = read(goodPixels), weakBands = read(weakPixels)
        XCTAssertEqual(goodBands.count, 1, "自造的这条带必须被找出来（否则上面那条判据是在对空帧打分）")
        XCTAssertEqual(weakBands.count, 1, "同一套几何只换字的颜色，带还是得找到")
        // 取不到就用 `guard let` + `XCTFail` 让这条**红**，不要 `goodBands[0]` —— 下标越界会直接把
        // 整个测试进程打死（本轮实测：signal 5），后面的判据一条都不跑，
        // 于是"尺瞎了"看起来像"套件被环境问题中断"。崩溃是把红伪装成没跑的一种。
        guard let goodBand = goodBands.first, let weakBand = weakBands.first else {
            XCTFail("尺没找到自造的带 ⇒ 对比度读数没有对象（bands good=\(goodBands.count) weak=\(weakBands.count)）")
            return
        }
        for (label, band) in [("好墨", goodBand), ("坏墨", weakBand)] {
            XCTAssertEqual(band.startPt, 10, accuracy: 1.5, "\(label)：带的位置量错了")
            XCTAssertEqual(band.endPt, 40, accuracy: 1.5, "\(label)：带的下沿量错了")
            XCTAssertGreaterThan(band.inkFraction, InkFloor.bandInkFraction,
                                 "\(label)：墨地板拦不住 ⇒ 这块'带'里根本没读到字")
        }
        XCTAssertGreaterThan(goodBand.ratio, InkFloor.bodyTextContrast,
                             "深墨对浅暖底必须过线，否则这把尺把好的也判成缺陷")
        XCTAssertLessThan(weakBand.ratio, InkFloor.bodyTextContrast,
                          "浅墨对浅暖底必须不过线（实测 " + String(format: "%.2f", weakBand.ratio)
                          + "）⇒ 不过线的那一端量不出来，这条判据就只是复读产品当前值")
        emit("NOTICE_BAND_CONTROL good=\(String(format: "%.2f", goodBand.ratio)) "
              + "weak=\(String(format: "%.2f", weakBand.ratio)) "
              + "ink=\(String(format: "%.1f%%", goodBand.inkFraction * 100))")
    }

    /// `inkRowSpan` 的正对照：**居中、偏上、什么都没有**三种几何必须读出三种结果。
    ///
    /// 第三条最容易漏：如果"没找到按钮"返回的是 0 而不是 nil，
    /// 那么"按钮不见了"这种缺陷会读成"偏 0pt ⇒ 完美居中"，判据就反着骗人。
    /// 这一条**不覆盖管线**（判的是纯函数），管线级判据是 `testNoticeActionIsVerticallyCenteredInItsBand`。
    func testActionSpanRulerReadsBothEnds() {
        let width = 400, height = 60, bytesPerRow = width * 4
        func buffer(actionRows: ClosedRange<Int>?) -> [UInt8] {
            var bytes = [UInt8](repeating: 255, count: height * bytesPerRow)
            guard let rows = actionRows else { return bytes }
            for y in rows {
                for x in stride(from: 320, to: 380, by: 1) {
                    // 一道"字"：每隔 4px 一根 2px 竖笔，保证每行都有足够的墨像素。
                    guard (x - 320) % 4 < 2 else { continue }
                    let o = y * bytesPerRow + x * 4
                    bytes[o] = 20; bytes[o + 1] = 20; bytes[o + 2] = 20; bytes[o + 3] = 255
                }
            }
            return bytes
        }
        func span(_ bytes: [UInt8]) -> (startPt: Double, endPt: Double)? {
            bytes.withUnsafeBufferPointer {
                Self.inkRowSpan(bytes: $0.baseAddress!, width: width, height: height,
                                bytesPerRow: bytesPerRow,
                                rect: CGRect(x: 305, y: 10, width: 87, height: 30), scale: 1.0)
            }
        }
        let bandCenter = 25.0   // 自造的带是 y 10–40
        guard let centered = span(buffer(actionRows: 20...29)) else {
            return XCTFail("居中的动作块没被找到 ⇒ 这条判据的对象不存在")
        }
        guard let high = span(buffer(actionRows: 12...21)) else {
            return XCTFail("偏上的动作块没被找到 ⇒ 尺只会读居中那一种")
        }
        XCTAssertEqual((centered.startPt + centered.endPt) / 2, bandCenter, accuracy: 1.5,
                       "居中的块应读成居中（实测 " + String(format: "%.1f", centered.startPt)
                       + "–" + String(format: "%.1f", centered.endPt) + "）")
        let highCenter = (high.startPt + high.endPt) / 2
        XCTAssertGreaterThan(abs(highCenter - bandCenter), InkFloor.actionCenterTolerancePt,
                             "偏上 8pt 的块必须读出超过容差的偏差（实测 "
                             + String(format: "%.1f", highCenter) + "）⇒ 读不出偏上，产品判据就是摆设")
        XCTAssertNil(span(buffer(actionRows: nil)),
                     "空矩形必须返回 nil，不能返回 0 —— 否则『按钮不见了』会读成『偏 0pt，完美居中』")
        emit("ACTION_SPAN_CONTROL centered=" + String(format: "%.1f", (centered.startPt + centered.endPt) / 2)
              + " high=" + String(format: "%.1f", highCenter) + " empty=nil")
    }

    /// 加载态那一块的**左轴读数**：条带的最左列、那一句的最左列（都从像素里自己找）。
    ///
    /// 为什么按"弱墨 / 强墨"分行而不是写死 y 区间：条带与句子的对比度差一个量级
    ///（条带 255 vs 242 = Δ13，句子 255 vs ~110 = Δ145），所以"这一行是条带还是字"
    /// 可以判，不需要我把 y=24..68 钉进测试（钉了就又是 R24 那族"布局一动，框套空白"）。
    static func skeletonAxisReadings(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                     bytesPerRow: Int, scale: Double)
        -> (barLeading: Double?, textLeading: Double?, aboveBarLeading: Double?,
            barRows: Int, textRows: Int) {
        func luma(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return (Int(bytes[o]) * 299 + Int(bytes[o + 1]) * 587 + Int(bytes[o + 2]) * 114) / 1000
        }
        var histogram: [Int: Int] = [:]
        for y in stride(from: 0, to: height, by: 4) {
            for x in stride(from: 0, to: width, by: 4) { histogram[luma(x, y) / 4, default: 0] += 1 }
        }
        let background = (histogram.max { $0.value < $1.value }?.key ?? 0) * 4 + 2
        var barRows: [Int] = [], textRows: [Int] = []
        for y in 0..<height {
            var weak = 0, strong = 0
            for x in 0..<width {
                let delta = abs(luma(x, y) - background)
                if delta > 40 { strong += 1 } else if delta > 6 { weak += 1 }
            }
            if strong < 8 && weak > width / 8 { barRows.append(y) }
            if strong >= 3 { textRows.append(y) }
        }
        func spanPt(_ rows: [Int]) -> (Int, Int)? {
            guard let first = rows.min(), let last = rows.max(), last > first else { return nil }
            return (first, last + 1)
        }
        var barLeading: Double? = nil
        var textLeading: Double? = nil
        // 条带**之上**的强墨行 = 详情头部那一行。它只是诊断读数（R26 的 BACKLOG 39 用它记账），
        // 不当判据 —— 因为头部被可读列居中过，它的左轴是 55pt 而不是 gutter 的 20pt，
        // 拿它当断言等于把"居中列"这个未定的设计问题钉成规矩。
        var aboveBarLeading: Double? = nil
        if let bars = spanPt(barRows) {
            let above = textRows.filter { $0 < bars.0 }
            if let block = spanPt(above) {
                let rect = CGRect(x: 0, y: Double(block.0) / scale,
                                  width: Double(width) / scale, height: Double(block.1 - block.0) / scale)
                aboveBarLeading = Self.leadingInkColumn(bytes: bytes, width: width, height: height,
                                                        bytesPerRow: bytesPerRow, rect: rect, scale: scale)
            }
        }
        if let bars = spanPt(barRows) {
            let rect = CGRect(x: 0, y: Double(bars.0) / scale,
                              width: Double(width) / scale, height: Double(bars.1 - bars.0) / scale)
            barLeading = Self.leadingInkColumn(bytes: bytes, width: width, height: height,
                                               bytesPerRow: bytesPerRow, rect: rect, scale: scale,
                                               minDelta: 6, minInkPerColumn: 4)
        }
        if let text = spanPt(textRows) {
            let rect = CGRect(x: 0, y: Double(text.0) / scale,
                              width: Double(width) / scale, height: Double(text.1 - text.0) / scale)
            textLeading = Self.leadingInkColumn(bytes: bytes, width: width, height: height,
                                                bytesPerRow: bytesPerRow, rect: rect, scale: scale)
        }
        return (barLeading, textLeading, aboveBarLeading, barRows.count, textRows.count)
    }

    /// **加载块必须站在详情栏那一条左轴上**（R26 / U-48 / D-085）。
    ///
    /// 这块表面以前从来没有进过帧基线（它是异步的，拍它等于赌时机），所以这三件事一次都没被看过：
    /// ① 三根条带顶到面板左边缘（x=0），而它替代的内容（头部、正文）都在 `containerGutter` = 20pt 上；
    /// ② 那一句"正在加载预览…"落在整块面板的水平中线上，与条带不同轴 —— 同一块面板两条对齐轴；
    /// ③ 亮色下条带只有 Δ13 的可辨性（这是**故意的**，见下面的判断）。
    ///
    /// 判据把三个左轴都从像素里量出来，要求同轴：条带、句子、以及**它替代的那个头部**
    /// （从 `detail-2-file` 量，不是我写的一个数）。
    func testLoadingBlockSharesTheDetailColumnsAxis() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r26-axis-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            func readings(_ name: String) throws -> (bar: Double?, text: Double?, above: Double?,
                                                     barRows: Int, textRows: Int, scale: Double) {
                guard let fixture = fixtures(appearance: appearance).first(where: { $0.name == name }) else {
                    XCTFail("找不到夹具 \(name) ⇒ 这条判据没有对象"); return (nil, nil, nil, 0, 0, 2)
                }
                let file = scratch.appendingPathComponent("\(name)-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    XCTFail("读不回 \(file.lastPathComponent)"); return (nil, nil, nil, 0, 0, 2)
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let got = Self.skeletonAxisReadings(bytes: base, width: rep.pixelsWide,
                                                    height: rep.pixelsHigh,
                                                    bytesPerRow: rep.bytesPerRow, scale: scale)
                return (got.barLeading, got.textLeading, got.aboveBarLeading,
                        got.barRows, got.textRows, scale)
            }
            let loading = try readings("detail-loading")
            let detail = try readings("detail-2-file")

            XCTAssertNotNil(loading.bar, "\(tag)：加载帧里没找到条带 ⇒ 尺没有对象（先查 skeleton 还在不在画）")
            XCTAssertNotNil(loading.text, "\(tag)：加载帧里没找到那一句 ⇒ 它不在了，或者它和条带同对比度了")
            XCTAssertNotNil(detail.text, "\(tag)：详情帧里没找到那一句 ⇒ 对照物消失，"
                            + "说明 `detail-2-file` 里已经没有加载块了，这条判据的第二半要重看")

            // ① 条带与句子同轴（块内）
            if let bars = loading.bar, let text = loading.text {
                XCTAssertLessThanOrEqual(abs(bars - text), 2.0,
                    "加载块自己就两条左轴：条带起于 x=\(String(format: "%.1f", bars))，"
                        + "而「正在加载预览…」起于 x=\(String(format: "%.1f", text))"
                        + "（\(tag)）⇒ 句子读起来不像在说这三根条带")
            }
            // ② 加载块必须落在**产品自己的 gutter** 上，而不是顶到面板边缘。
            //     这一条是 R26 的变异 M116 逼出来的：原来这里写的是"与 `detail-2-file` 的最左强墨同轴"，
            //     而那张帧里最左的强墨**就是同一个加载块的句子**（骨架在 detail-2-file 里也在画）——
            //     于是把 gutter 去掉，两边一起从 20 挪到 0，判据照样绿 ⇒ **M116 ESCAPED**。
            //     教训：跨帧对照必须先证明两帧量的是**不同的东西**，否则那是自己跟自己比。
            let gutter = Double(DetailTypography.containerGutter)
            if let bars = loading.bar {
                XCTAssertGreaterThanOrEqual(bars, gutter - 1,
                    "加载块的左轴在 x=\(String(format: "%.1f", bars))，而详情栏的 gutter 是 "
                        + "\(String(format: "%.0f", gutter))pt ⇒ 条带顶到了面板边缘，"
                        + "预览落地的一瞬间整块内容要向右跳 \(String(format: "%.0f", gutter))pt")
                XCTAssertLessThanOrEqual(bars, gutter + 1,
                    "加载块的左轴在 x=\(String(format: "%.1f", bars))，比详情栏 gutter "
                        + "\(String(format: "%.0f", gutter))pt 还靠右 ⇒ 骨架缩进了第二层，"
                        + "它承诺的内容宽度比实际来的窄")
            }
            emit("LOADING_AXIS \(tag) bars=\(String(format: "%.1f", loading.bar ?? -1)) "
                  + "caption=\(String(format: "%.1f", loading.text ?? -1)) gutter=\(gutter) "
                  + "detailHeader=\(String(format: "%.1f", detail.above ?? -1)) "
                  + "barRows=\(loading.barRows) textRows=\(loading.textRows)")
        }
    }

    /// 详情区**只有一条内容左轴**（R32 / BACKLOG 39 / U-54）。
    ///
    /// 改之前的实测（同一把尺、同一批帧）：头部 meta 与正文在 **54.5 / 55.5**，
    /// 而它替代的加载骨架在 **20.5** —— 预览落地的一瞬间整块内容向右跳 35pt。
    /// 原因不是谁调错了 padding，是"可读列居中"这个写法：居中列的左缘 =
    /// (面板宽 − 列宽)/2，**随窗口宽度变**，所以它永远不可能等于一个固定的 gutter。
    /// 现在三处调用点统一走 `View.detailReadableColumn()`（贴 gutter、宽出来的留在右边）。
    ///
    /// 这条判据要红得起来，靠的是它量的是**不同的东西**（R26 的 M116 教训）：
    /// meta 行、正文首行、正文后续行、骨架条带、骨架那一句 —— 五块各自量一次，
    /// 断言"彼此差 ≤2pt 且都贴着 gutter ±2"。把 gutter 去掉会让**五块一起**挪，
    /// 那条 R26 已经证明"一起挪"必须由"贴着 gutter"这半边抓住，所以两个方向都留了断言。
    func testDetailAreaHasASingleLeftAxis() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r32-axis-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        /// (夹具, 块名, 量哪一条 y 带)。y 带是从帧上**读出来的**，不是推的：
        /// 改之前先量了一遍（meta 在 84–106、正文首行 110–150、渲染正文 150–300、骨架 84–150）。
        /// **每一块都用"整块高度"而不是单行**：正文可能首行缩进（fixture 里就有），
        /// 单行带会把缩进读成左轴 —— 第一版就红在了这里（读出 41.5，其实是首行两个空格）。
        /// 取整块的最左强墨列，缩进只会让它偏右、不会偏左，所以那才是轴。
        /// 带的上下沿也不是猜的：`rows` 剖面读出来 meta 那一行占 y=82.5…95，
        /// 第一版把 meta 带写成 84..106、正文带写成 110 起 —— 于是正文带被**切掉了首行**，
        /// 尺在 110 以下只找到第二行往后的强墨，报出 41.5 这个假轴（差 21pt）。
        /// 教训同族：**锚点过窄会把排版读成缺陷**，带要按剖面放。
        /// 刻意**不含** `detail-3-files`：那是"一列文件行"（图标 + 文字的行结构），
        /// 它的左轴属于行列表那一族（侧栏同理），不是正文列。
        let probes: [(String, String, CGRect)] = [
            ("detail-0-text", "头部 meta", CGRect(x: 0, y: 80, width: 720, height: 18)),
            ("detail-0-text", "正文（原文）", CGRect(x: 0, y: 100, width: 720, height: 400)),
            ("detail-markdown-rendered", "正文（渲染）", CGRect(x: 0, y: 100, width: 720, height: 400)),
            ("detail-markdown-source", "正文（退回原文）", CGRect(x: 0, y: 100, width: 720, height: 400)),
            ("detail-loading", "骨架条带＋那一句", CGRect(x: 0, y: 80, width: 720, height: 80)),
        ]
        let gutter = Double(DetailTypography.containerGutter)
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            var axes: [(String, Double)] = []
            for fixtureName in Set(probes.map { $0.0 }).sorted() {
                guard let fixture = fixtures(appearance: appearance)
                    .first(where: { $0.name == fixtureName }) else {
                    return XCTFail("找不到 \(fixtureName) ⇒ 这条判据失去了对象")
                }
                let file = scratch.appendingPathComponent("\(fixtureName)-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("读不回 \(file.lastPathComponent)")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                for (name, block, rect) in probes where name == fixtureName {
                    guard let axis = Self.leadingInkColumn(bytes: base, width: rep.pixelsWide,
                                                           height: rep.pixelsHigh,
                                                           bytesPerRow: rep.bytesPerRow,
                                                           rect: rect, scale: scale) else {
                        emit("AXIS_NOT_RUN \(fixtureName)/\(block) \(tag)")
                        continue
                    }
                    axes.append(("\(fixtureName)/\(block)", axis))
                }
            }
            guard axes.count >= 3 else {
                emit("AXIS_NOT_RUN all \(tag) 只有 \(axes.count) 块量到")
                throw XCTSkip("AXIS_NOT_RUN \(tag)：这台机器拍不出详情区 ⇒ 左轴契约记为未运行（BACKLOG 43 那一族）")
            }
            let values = axes.map { $0.1 }
            let spread = (values.max() ?? 0) - (values.min() ?? 0)
            for (block, axis) in axes {
                XCTAssertLessThanOrEqual(abs(axis - gutter), 2.0,
                    "\(block) 的左轴在 x=\(String(format: "%.1f", axis))，详情区 gutter 是 "
                    + "\(String(format: "%.0f", gutter))pt（\(tag)）⇒ 那一块不在内容列上："
                    + "居中写法会把它带回 (面板宽−列宽)/2，随窗口变")
            }
            XCTAssertLessThanOrEqual(spread, 2.0,
                "详情区读出 \(axes.count) 块，左轴最宽差 \(String(format: "%.1f", spread))pt："
                + axes.map { "\($0.0)=\(String(format: "%.1f", $0.1))" }.joined(separator: " ")
                + "（\(tag)）⇒ 加载态与内容态不是同一条轴，预览落地会跳")
            emit("DETAIL_AXIS \(tag) 判了 \(axes.count) 块，spread=\(String(format: "%.1f", spread))pt "
                  + "gutter=\(String(format: "%.0f", gutter))pt")
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
        /// `hoveredRow` 是给 R67 那两张悬停帧开的口子：离屏 `cacheDisplay` 送不进
        /// `mouseEntered` / `mouseMoved`（BACKLOG 95 记的就是这条通道的边界），
        /// 而产品侧走的是**与鼠标同一条赋值**（`QuickPickRowView.setHoveredForCapture`）。
        /// 默认 `nil` ⇒ 其余浮层帧逐字节不变，这是它们能继续当基线的前提。
        static func builder(store: HistoryStore, query: String,
                            hoveredRow: Int? = nil) -> @MainActor () -> NSWindow? {
            var kept: QuickPickController?
            return {
                if kept == nil {
                    kept = QuickPickController(historyStore: { store }, commit: { _ in })
                }
                guard let controller = kept else { return nil }
                return controller.windowForCapture(query: query, hoveredRow: hoveredRow)
            }
        }
    }

    // MARK: - 渲染

    private func render(
        _ fixture: Fixture,
        appearance: NSAppearance.Name,
        to file: URL,
        /// R30：**拍之前把已经装好、已经布局完的那棵 AppKit 树交出来看一眼**。
        /// 存在的理由：R29d 在仓库外搭了十五臂复刻体（List 侧栏 / 嵌套 `NSHostingView`+`NSSplitView` /
        /// `Button{Label}+.plain` / 显式 `.primary` / 运行时翻外观 …）**全部画对**，
        /// 也就是说"侧栏暗档文字落在错误一侧"这件事只在产品那一整棵树里发生。
        /// 继续在仓库外猜形状是浪费轮次 —— 改成直接问产物：这一列到底是**谁**画的。
        /// 默认空实现 ⇒ 现有 100 多条调用点一字不改。
        inspect: @MainActor (NSView) -> Void = { _ in }
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
        // R63：这里**以前**有一条豁免 —— "AppKit 夹具不走强制约束布局（R19 实测）：
        // `layoutSubtreeIfNeeded()` 会把 NSStackView 从『帧 + autoresizing 撑满 420×300』
        // 重排成『按内容拟合尺寸 24×49』"。那条解释是错的，而豁免是照着它写的：
        // 塌不是这一步造成的 —— 产品自己那两条 `frame` + `autoresizingMask` 在 `NSStackView`
        // 上本来就是空操作（最小对象图 spike：`.scratch/motion-audit-2/r63_spike_stack.swift`，
        // 建出来 `translatesAutoresizingMaskIntoConstraints` 就是 0），两条路都塌。
        // 产品改成贴边约束之后，强制布局得到的就是同一个 420×300 ——
        // 于是没有理由再让浮层走另一条布局路。
        // 少一条豁免，就少一个"夹具与产品不同形"的地方（BACKLOG 36 那一族）。
        window.layoutIfNeeded()
        host.layoutSubtreeIfNeeded()

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
        // AppKit 夹具这里不再补一次强制布局：下面"真实显示周期"那一档里
        // `orderFrontRegardless` + `tile()` + `display()` 本来就会把布局推到底（R63）。

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

        // R30 的诊断钩子：布局已完成、外观已注入、还没开画 —— 这一时刻的树就是帧里那些像素的作者。
        inspect(host)

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
        }
        // **底行墨读的是落盘那张图，不是 raw rep**（R37）。
        // 这不是风格选择：raw rep 里"没画"的像素是**透明**的，底行的中位数会被它们拿走，
        // 于是同一帧两个来源能差一个数量级 —— 实测 `content-min-light` raw=3.4% / PNG=43.4%，
        // `content-empty-light` raw=37.4% / PNG=0.1%（方向还相反）。
        // 判据要判的是**产物**：帧基线存的是 PNG，人眼看的也是 PNG，
        // `flattenedPNG` 已经把那批透明像素铺成了窗口底色。
        // （`blackBandHeight` 继续读 raw rep —— 它要的正是 alpha，"透明的黑"是"没画"不是"画黑了"。）
        // 写成一行可替换的形式，是为了让"来源换回 raw rep"成为一支**能注入**的变异（M171）：
        // 判据要能被弄坏才叫判据，而"改坏它但没有任何测试会红"这一族已经抓过太多次。
        let measured: NSBitmapImageRep = NSBitmapImageRep(data: data) ?? rep
        if let fbase = measured.bitmapData {
            bottomInk = Self.bottomInkFraction(bytes: fbase,
                                               width: measured.pixelsWide,
                                               height: measured.pixelsHigh,
                                               bytesPerRow: measured.bytesPerRow)
        }
        try data.write(to: file)
        return CaptureMetrics(transparent: transparent, blackBandPt: blackBand,
                              bottomInkFraction: bottomInk)
    }

    /// 最底一行里"偏离**这一行自己的底色** >12"的像素占比（0…1）。
    ///
    /// **R37 改过参照点**（U-60 / BACKLOG 50）。以前它拿 `bytes[0]`（整帧左上角那一个像素）当底色，
    /// 于是它读的不是"底行有没有墨"而是"底行与角点差多少色"：侧栏亮色帧的角点落在搜索框里（255,255,255），
    /// 底行是窗口灰（240,240,240），差 45 > 12 ⇒ **整行被数成墨**（15 张帧报 100.0%，
    /// 而按底行自身是 0.0%）；`settings-privacy-light` 反过来报 0.1% 而真实是 6.7%（漏报）。
    /// 现在参照点是底行自身的**每通道中位数**。
    ///
    /// 两个刻意的选择：
    /// ① **中位数而不是量化众数**：桶心是下边界，与真实像素最多可差 7×3=21 > 容差 12，
    ///    会把一行干净的底色读成"100% 有墨" —— 那是我这把尺自己造的假阳性（R36 第一版工具就栽过）。
    /// ② **已知边界**：如果整行被同一个元素**盖满**（全出血的填充、贴边的色带），
    ///    中位数就是那个元素 ⇒ 读 0%。那种情况要的是另一条判据（"帧底不许是全出血填充"），
    ///    不在这条的责任范围里，别把它当"没裁"的证据。
    /// 阈值 12 与 `filledBands` 同一条线 —— 两处各写一个数字的话，
    /// "松一档"会让一条判据先瞎（R18 那条"两处各写一个数"同族）。
    static func bottomInkFraction(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                  bytesPerRow: Int) -> Double {
        guard width > 0, height > 0 else { return 0 }
        let row = (height - 1) * bytesPerRow
        func channel(_ offset: Int) -> Int {
            var values = [Int]()
            values.reserveCapacity(width)
            var x = 0
            while x < width {
                values.append(Int(bytes[row + x * 4 + offset]))
                x += 1
            }
            values.sort()
            return values[values.count / 2]
        }
        let r0 = channel(0), g0 = channel(1), b0 = channel(2)
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

    /// 这棵子树里有没有"数据源是产品控制器"的那张表。
    /// 存在的理由：浮层整棵树里不止一个 `NSStackView`，而 R62 那版探针用
    /// `max(宽度)` 配"最后一个赢"混着读，三条读数可能来自不同的 stack ——
    /// 判据要认的是**那一个** stack，所以按身份认，不按尺寸认。
    static func containsProductTable(_ root: NSView) -> Bool {
        if let table = root as? NSTableView, table.dataSource is QuickPickController { return true }
        return root.subviews.contains { containsProductTable($0) }
    }

    /// 把 `view.frame` 换算到祖先 `ancestor` 的坐标系（一次 `convert(_:from:)`，不假设层数）。
    /// 不是 `view` 的后代时返回 `nil` —— 宁可不判，也不许拿两个不同坐标系的数相减。
    static func frame(_ view: NSView, in ancestor: NSView) -> CGRect? {
        guard let parent = view.superview else { return view === ancestor ? .zero : nil }
        var hop: NSView? = parent
        while let current = hop {
            if current === ancestor { return ancestor.convert(view.frame, from: parent) }
            hop = current.superview
        }
        return nil
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
