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
        // R206 / BACKLOG 229：新夹具 `content-with-dropped-unreadable-notice` 第一次拍就冒黑带，
        // 分辨实验的读数是「三张暗帧的纯黑带**高度都是 132px（66pt @2x）**、只有 y 不同」：
        // `content-with-notice` y=896..1027、`content-with-two-notices` y=974..1105、本帧 y=872..1003。
        // ⇒ 同一处已登记的盲区（侧栏最后一行的选中材质在离屏下画成黑），横幅只是把它推上/推下；
        //   登记的是**这一处**，不是给老毛病起一个新名字（名单里每一条都要能被这样追问）。
        "content-with-dropped-unreadable-notice",
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
        /// **画到的包围盒高**（pt）—— BACKLOG 194 欠的那根分辨轴（R168）。
        ///
        /// 三种读法互不重叠，这是它有用的全部理由：
        /// * `-1` = 拿不到字节 ⇒ **量不到**，不许当成"没画"（R130 的哨兵规矩：漏掉那格会掉进哪个出口要先想清楚）；
        /// * `0`  = 一个有墨的像素都没有 ⇒ **根本没渲染**；
        /// * `≈ 屏幕可视高` 而需求是 1040 ⇒ **渲染了但被裁**；`≈ 需求高` ⇒ 画满了。
        ///
        /// 它读的是 **raw rep 的 alpha**，与 `transparent` 同一来源、同一常数
        /// （`transparentAlphaCeiling`）：一个说"多少像素没画"、一个说"画到的最远的那行在哪"，
        /// 两边若用了不同的"什么算画过"，runner 上的空帧就会出现"占比说空、包围盒说满"这种自相矛盾。
        let drawnBoxPt: Double
        /// 最下面一条有墨的行（pt）；`drawnBoxPt == 0` 时是 `-1`（没有这样的行）。
        let drawnBottomPt: Double
    }

    /// 画到的包围盒：第一条 / 最后一条"有墨"的行，以及它们之间的高（pt）。
    ///
    /// "有墨" = 这一行至少有一个像素 `alpha >= transparentAlphaCeiling`。门槛取**一个像素**：
    /// 要分开的是 0 / ≈681 / 1040 这种**几百像素**的差，不是一把 1pt 的杂点；
    /// 若将来要分辨的是"某几行有没有被裁"，门槛就得重量（别沿用这里的 1）。
    static func drawnBoundingBox(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                                 bytesPerRow: Int, backingScale: CGFloat)
            -> (topPt: Double, bottomPt: Double, heightPt: Double) {
        var top = -1
        var bottom = -1
        var y = 0
        while y < height {
            let row = y * bytesPerRow
            var inked = false
            var x = 0
            while x < width {
                if bytes[row + x * 4 + 3] >= transparentAlphaCeiling { inked = true; break }
                x += 1
            }
            if inked {
                if top < 0 { top = y }
                bottom = y
            }
            y += 1
        }
        guard top >= 0 else { return (topPt: -1, bottomPt: -1, heightPt: 0) }
        let scale = Double(backingScale > 0 ? backingScale : 1)
        return (topPt: Double(top) / scale,
                bottomPt: Double(bottom + 1) / scale,
                heightPt: Double(bottom - top + 1) / scale)
    }

    /// 从帧文件名读**需求高**：`settings-privacy-tall-720x1040-light.png` → 1040。
    /// 读不出来返回 `nil`（调用点不许把 nil 当成 0 —— 那会让"没尺寸"看起来像"矮帧"）。
    static func requestedHeightPt(fromFile file: String) -> CGFloat? {
        let base = (file as NSString).deletingPathExtension
        guard let range = base.range(of: "-\\d+x(\\d+)-", options: .regularExpression) else { return nil }
        let digits = base[range].dropFirst().dropLast().split(separator: "x")[1]
        return CGFloat(Int(digits) ?? 0)
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

    /// R167 / BACKLOG 194：**每一次 render 的几何，按帧名留着**，好让"未画"那一格能引用同源读数。
    /// 只在这一整个测试实例活着的时候有效（XCTest 每个用例一个新实例），不跨用例、不跨机器。
    /// 键是文件名（含尺寸与档位），值是那一次捕获里量到的四个数。
    var capturedGeometry: [String: (requested: CGFloat, content: CGFloat, host: CGFloat, screen: CGFloat)] = [:]

    /// R168 / BACKLOG 194：把"这张空帧该不该算这台机器画不出来"抽成**纯谓词**。
    ///
    /// 为什么单独抽：本机拍不出"高帧全空"那种形状（六张 `-1040-` 本机 `blank=0.0%`），
    /// 于是放行条件**没法**靠"在真帧上跑一遍循环"来验收。R167 我就是这么造正对照的 ——
    /// 把有对象的帧强行塞进未画循环，两种实现都绿，那两格是空的（空对账）。
    /// 抽成纯函数之后，对照建在谓词自己身上：每一格都必须让它真的做决定
    /// （`CaptureBlankFrameGapTests` 三格：三轴齐 ⇒ 放行；任一根轴不齐 ⇒ 不放行；没有读数 ⇒ 不放行）。
    ///
    /// **这一版开始接线放行了**，但只放行 R168 那根分辨轴**实测到**的那一种形状（run `39152321051`）：
    /// 六张高帧全部 `drawnBoxPt=205 / drawnBottomPt=1040 / transparent=95.9% / screenVisibleHeightPt=681`
    /// ⇒ 画出了一条**比需求窄、又不等于屏幕可视高**的带。这个读数把 R162 预登记的三种解释处理掉了：
    /// * 「窗口被收小」「内容视图没铺满」：被几何那三边（`content == host == requested == 1040`）排除（R167 已排除过一次）；
    /// * 「根本没渲染」：被 `drawnBoxPt > 0` 排除 —— 那 205pt 里确实有墨；
    /// * 「被屏幕裁到可视高」：被 `drawnBoxPt ≠ screenVisibleHeightPt`（205 vs 681）且带落在**图的下沿**排除。
    /// 剩下的读法是"这台机器的高窗捕获通道只画出一条窄带"，机制**仍未命名**（本机可视高 850 < 1040 却画满，
    /// 所以"与屏幕相交"那条猜测在自己身上就不成立 —— 不许写进账当结论）。
    /// 因此这里的判据不是"我知道为什么"，而是"**同一份二进制、同一批夹具，本机 box=1040 且 blank≈0，
    /// runner box=205 且 blank=95.9%**"——这是通道性质，不是产品缺陷（闸门也只要两种处置之一，R170 / BACKLOG 194）。
    /// 两种形状仍**不放行**，红照旧：`drawnBoxPt == 0`（一张都没画 = 捕获坏了，没为它签过字）；
    /// `drawnBoxPt == requested`（画满了却报 95% 未画 = 两把尺自相矛盾，先修尺）。
    static func shouldRegisterBlankAsMachineGap(family: String,
                                               requestedHeightPt: CGFloat?,
                                               contentHeightPt: CGFloat,
                                               hostHeightPt: CGFloat,
                                               drawnBoxPt: CGFloat) -> Bool {
        guard family == "settings", let requested = requestedHeightPt,
              requested >= tallFixtureHeightFloor else { return false }
        guard contentHeightPt == requested, hostHeightPt == requested else { return false }
        return drawnBoxPt > 0 && drawnBoxPt < requested
    }

    /// 「高帧」的下界：`render` 里留几何读数的门槛与谓词用的是**同一个常数**，
    /// 两处各写一遍字面量的那天，就是出口悄悄换档的那天。
    static let tallFixtureHeightFloor: CGFloat = 1000

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
    /// R104 · BACKLOG 148：搜索那一行的**第一个墨列**必须站在列表自己那一列里。
    ///
    /// 参照物是同一张帧上那颗选中药丸的左沿（`overlayPill`，量的就是画面上那条灰带的边），
    /// **不是面板边，也不是产品里那个 `searchFieldLeadingInset` 常数** ——
    /// M367 那一课：拿被约束的常量去推期望值，改常量等于同时改了判据。
    ///
    /// 为什么走**落盘的 PNG**而不是 R67 那条 alpha 通道：这一格的另一边是**字**。
    /// 实测（本机第一版判据，走 `overlayPair` 那个 live rep）：搜索那一条带里
    /// **一个 alpha ≥ 0.5 的像素都没有** ⇒ 那条通道上字不落地（面板本身透明），
    /// 于是"第一个墨列"无从谈起。PNG 那一条是合成过背景的，字与灰带都在。
    /// 这一格记进 U-314：**换判据的一边之前，先确认另一边活在哪条通道上。**
    ///
    /// 三条断言各自拦一种错：
    ///   ① 参照物自己要有对象（读不到药丸就红）；
    ///   ② 搜索那一行必须有墨（读不到就红）—— 这是 D-168 那条规矩的正向用法：
    ///      等式的任何一边不存在，这条判据就什么都不判，不许把它记成通过；
    ///   ③ 两边之差 ≤ 2px（= 1pt）。容差不放大到 ±2pt：R67 记过"±2px 容差把 9pt 与 10pt
    ///      的差当成对上"，而这条要拦的是改之前实测的 19px。
    func testQuickPickSearchLineSharesTheRowsColumn() throws {
        // 这里**不**自己建 store：走的是 `fixtures(appearance:)` 里那张 `quickpick-list` 夹具，
        // 它自带 store ⇒ 判据读的就是进帧基线的那一张图（同一颗尺、同一份对象）。
        var candidates = 0, judged = 0, declined: [String] = []
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r104-axis-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        for (tag, appearance) in [("light", NSAppearance.Name.aqua),
                                  ("dark", NSAppearance.Name.darkAqua)] {
            let fixtures = self.fixtures(appearance: appearance)
            guard let fixture = fixtures.first(where: { $0.name == "quickpick-list" }) else {
                return XCTFail("\(tag)：找不到 `quickpick-list` 夹具 ⇒ 这条判据没有对象")
            }
            let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("\(tag)：读不回刚拍的帧")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            let page = Self.modalLuma(bytes: base, bytesPerRow: rep.bytesPerRow,
                                      xRange: 0..<rep.pixelsWide, yRange: 0..<rep.pixelsHigh)
            guard let pill = Self.overlayPill(bytes: base, width: rep.pixelsWide,
                                              height: rep.pixelsHigh,
                                              bytesPerRow: rep.bytesPerRow,
                                              pageLuma: page) else {
                return XCTFail("\(tag)：这张帧上读不到选中药丸（页底档=\(page)）⇒ 参照物不存在，"
                    + "先查捕获通道，不要把等式放宽")
            }
            // 搜索那一行 = 药丸**之上**那一条带（留 2px 不吃进药丸的圆角上沿）。
            let stripBottom = max(0, pill.top - 2)
            guard stripBottom > 4 else {
                return XCTFail("\(tag)：药丸顶在 \(pill.top)px，它上面没有带子可扫 ⇒ 布局不对")
            }
            candidates += 1
            // 同一颗尺（R103 的 `textInkWitness`）：它给的不只是"有没有"，还有**最大偏离**——
            // 这一格是本轮被 runner 教出来的：那一台机器上浮层的占位语**一个像素都不落地**，
            // 而没有 `最大偏离` 就分不清"它没画字"与"我的门限太高"（BACKLOG 158）。
            let stripRect = CGRect(x: 0, y: 0, width: fixture.size.width,
                                   height: CGFloat(stripBottom) / CGFloat(scale))
            let strip = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                            height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                            rect: stripRect, scale: scale,
                                            fill: page, pageLuma: page)
            // R106 / 158 的答案：地板从**这一条带自己有多强**推出来，不再抄本机的 60。
            // runner 实测（run `38984669003`）：`最大偏离=58`（亮）/ `49`（暗）而门限 60 ⇒
            // 占位语**画了**，只是那台机器的面板底更暗（页底 236/52 对本机 252/28），
            // 对比度落在全局地板之下 —— 那是①"没画"被误读成②"我的尺太高"的那一格（158 三成因里的②）。
            // 20 这一档不是新的绝对地板，而是"这条带里到底有没有任何东西"的下界：
            // 带里最大偏离 < 20 ⇒ 真的什么都没画 ⇒ 不判（点名），而不是判红。
            let bandFloor = max(20, strip.maxDelta / 2)
            let search = Self.firstInkColumnInStrip(bytes: base, width: rep.pixelsWide,
                                                    bytesPerRow: rep.bytesPerRow,
                                                    yRange: 0..<stripBottom, background: page,
                                                    deltaFloor: bandFloor)
            let pillPt = Double(pill.left) / scale
            let searchText = search.map { String(format: "%.1f", Double($0) / scale) + "pt" } ?? "没有"
            let diffText = search.map { "\($0 - pill.left)px" } ?? "-"
            // **结论行排在闸门与 skip 之前**（D-166 第三次记这条：闸门一挡，读数就没了）。
            emit("QUICKPICK_SEARCH_AXIS \(tag) 药丸左沿=\(String(format: "%.1f", pillPt))pt"
                 + " 搜索第一列墨=\(searchText) 差=\(diffText)"
                 + " 带子 y=0..\(stripBottom)px 带内墨行=\(strip.rows) 墨像素=\(strip.pixels)"
                 + " 最大偏离=\(strip.maxDelta)（全局门限 \(Self.textInkMinDelta)，本条带用 \(bandFloor)）"
                 + " 页底档=\(page) 倍率=\(String(format: "%.1f", scale))x 帧宽=\(rep.pixelsWide)px")
            guard strip.maxDelta >= 20, let ink = search else {
                declined.append("\(tag)[原因=搜索那一行读不到字：带内墨行=\(strip.rows)、"
                                + "墨像素=\(strip.pixels)、最大偏离=\(strip.maxDelta)，"
                                + "而这一档用的地板是 \(bandFloor)（带里最大偏离的一半，下界 20）]")
                continue
            }
            judged += 1
            // ① 参照物必须真的是那颗内缩过的药丸，不是行边界、也不是图标那一列。
            XCTAssertGreaterThan(pillPt, 15.0,
                "\(tag)：参照物读到 \(String(format: "%.1f", pillPt))pt。本机实测药丸左沿 22.0pt；"
                + "≈12pt 说明量到的是**行边界**（药丸没画），那时等式会退化成『12 与 12 相等』的假绿")
            XCTAssertLessThan(pillPt, 30.0,
                              "\(tag)：参照物读到 \(String(format: "%.1f", pillPt))pt ⇒ 那已经不是药丸的左沿"
                              + "（更像行内图标那一列 35.5pt），参照点错了等式就不成立")
            // ③ 等式本身。
            XCTAssertLessThanOrEqual(abs(ink - pill.left), 2,
                "\(tag)：搜索那一行的第一个墨列在 \(ink)px（\(String(format: "%.1f", Double(ink) / scale))pt），"
                + "而同一张帧上药丸的左沿在 \(pill.left)px（\(String(format: "%.1f", pillPt))pt）"
                + "⇒ 差 \(abs(ink - pill.left))px。改之前实测差 19px（12.5pt 对 22.0pt）："
                + "占位语比它正下方那一列的可见边往左突出，那一行字像贴在面板毛边上")
        }
        emit("QUICKPICK_AXIS_CAPABILITY 候选=\(candidates) 有对象=\(judged) 未判=\(declined.count)"
             + "（未判名单只在**这台机器画得出占位语**时才要求为空）")
        if !declined.isEmpty { emit("QUICKPICK_AXIS_DECLINED " + declined.joined(separator: " ")) }
        if judged == 0 {
            throw XCTSkip("这台机器上浮层搜索那一行画不出字（\(declined.joined(separator: " "))）"
                          + " ⇒ 这条左轴等式没有对象，**不判（不是通过）**，见 BACKLOG 158。"
                          + "参照物（药丸）在两档都读得到，坏的是字那一侧的通道。")
        }
        // 有一档画得出、另一档画不出 ⇒ 红。这不是吹毛求疵：占位语在某一档不可见**就是**观感缺陷，
        // 而且没有这一格，"整机归零 ⇒ skip" 会变成一张万能挡箭牌（D-166 后半条）。
        XCTAssertTrue(declined.isEmpty,
                      "这台机器**画得出**占位语（有对象=\(judged)），却有一档读不到 ⇒ 坏的是尺或那一档的通道，"
                      + "必须点名：\(declined.joined(separator: " "))")
    }

    /// R106 · BACKLOG 159 结案：`quickpick-typed` 那张帧上不许有**用户看不到的选中底**。
    ///
    /// 这一条先当探针跑过一遍、拿到机制，再变成判据（机制没证实之前写断言就是猜，D-163 那一族）。
    /// 读数走 `render(...)` 的 `inspect:` 钩子 ⇒ 看的就是**画出那张帧的同一棵树**（R30 立的这个钩子），
    /// 不是另建一棵。
    ///
    /// 两格断言各拦一种坏法，**不是冗余**：
    ///   ① 机制那一侧 —— 字段选中区间的长度必须为 0（拦"通道又给字段装了个全选"这件事本身）；
    ///   ② 像素那一侧 —— 顶部带子里不许有"只有灰、零个墨"且**比最宽那行墨还宽**的行
    ///     （拦"哪天这块填充换个来源画出来"，比如字段自己 `drawsBackground` —— 那时①仍然绿）。
    /// ②读的是**两个宽度的比**而不是灰像素绝对数：本机 2x 对 runner 1x，绝对量会跟着倍率走（R38）。
    /// 实测（本机 2x）：改之前 `纯灰行最宽=52px` 对 `最宽墨行=37px` ⇒ 红；
    /// 修之后 `1px` 对 `33px`（亮）、`0px` 对 `35px`（暗）⇒ 绿，余量是 33 倍而不是 1 像素。
    ///
    /// 隐私：只打**长度、类名、坐标**，一个字的内容都不打（帧与日志里不许出现用户剪贴板内容）。
    func testOverlayTypedFrameCarriesNoPhantomSelectionFill() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r106-band-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var sawField = 0, judged = 0
        var declined: [String] = []
        for (tag, appearance) in [("light", NSAppearance.Name.aqua),
                                  ("dark", NSAppearance.Name.darkAqua)] {
            let fixtures = self.fixtures(appearance: appearance)
            guard let fixture = fixtures.first(where: { $0.name == "quickpick-typed" }) else {
                return XCTFail("\(tag)：找不到 `quickpick-typed` 夹具 ⇒ 这条读数没有对象")
            }
            var state = "\(tag) 字段=没找到"
            var hasEditor = false, selectionLength = -1, stringLength = -1
            let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file) { host in
                guard let f = Self.firstOverlayTextField(in: host) else { return }
                sawField += 1
                // 先把每一项算成**普通量**再拼字符串：这一族的长插值会让类型检查超时（本机实测）。
                let editor = f.currentEditor() as? NSTextView
                let selected = editor?.selectedRange ?? NSRange(location: -1, length: -1)
                let length = f.stringValue.utf16.count
                let selIsWholeString = selected.length == length
                let responder = host.window?.firstResponder
                let responderName = responder.map { String(describing: type(of: $0)) } ?? "无"
                let responderIsEditor = responder != nil && responder === editor
                let isKey = host.window?.isKeyWindow ?? false
                let highlighted = f.isHighlighted
                let bezled = f.isBezeled
                let draws = f.drawsBackground
                hasEditor = editor != nil
                selectionLength = selected.length
                stringLength = length
                state = "\(tag) 字段类名=\(type(of: f)) 串长=\(length)"
                    + " 有editor=\(hasEditor)"
                    + " editor选中=(\(selected.location),\(selected.length))"
                    + " 选中覆盖整串=\(selIsWholeString)"
                    + " firstResponder=\(responderName)"
                    + " firstResponder就是editor=\(responderIsEditor)"
                    + " 窗口是key=\(isKey)"
                    + " 字段高亮=\(highlighted)"
                    + " 有边框=\(bezled) 画底色=\(draws)"
            }
            emit("QUICKPICK_FIELD_STATE \(state)")
            // 像素那一侧：同一张帧上那块灰到底占多少像素 —— 修完之后这个数必须归零，
            // 而字（墨档）不许跟着一起没。
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let bytes = rep.bitmapData else {
                return XCTFail("\(tag)：读不回刚拍的帧 ⇒ 像素那一侧没有对象")
            }
            let page = Self.modalLuma(bytes: bytes, bytesPerRow: rep.bytesPerRow,
                                      xRange: 0..<rep.pixelsWide, yRange: 0..<rep.pixelsHigh)
            // `modalLuma` 给的是 Int，而下面每一项都是 Double：混着写会让类型检查炸掉
            // （本机实测：`unable to type-check this expression in reasonable time`）。先换算成普通量。
            let pageLuma = Double(page)
            var greyRows = 0, greyPixels = 0, widest = 0, widestX = "", inkRows = 0, greyNoInkRows = 0
            var widestGreyNoInk = 0, widestInk = 0
            // R108：R106 修完之后本机还剩 **1 个纯灰像素**，这一格只问一件事 —— 它在不在字形的足迹里。
            // 只测不判（判法写进 BACKLOG 161：`落在其x内=false` ⇒ 那不是抗锯齿，要回来开修；
            // `=true` ⇒ 结案成"字形自己的边"）。两台机器都要打这一行，下一跑 CI 给对面那个数。
            var greyOnlyY = -1, greyOnlyFirst = -1, greyOnlyLast = -1
            var inkRowYs: [Int] = []
            var inkRowFirst: [Int] = []
            var inkRowLast: [Int] = []
            for y in 0..<min(rep.pixelsHigh, Int(CGFloat(40) * Double(rep.pixelsWide) / fixture.size.width)) {
                var g = 0, first = -1, last = -1, ink = 0, inkFirst = -1, inkLast = -1
                for x in 0..<rep.pixelsWide {
                    let i = y * rep.bytesPerRow + x * rep.samplesPerPixel
                    let a = bytes[Int(i) + 3]
                    guard a > 250 else { continue }
                    let r = bytes[Int(i)], gg = bytes[Int(i) + 1], b = bytes[Int(i) + 2]
                    let luma = 0.299 * Double(r) + 0.587 * Double(gg) + 0.114 * Double(b)
                    let delta = abs(luma - pageLuma)
                    if delta >= 8 && delta <= 45 {
                        g += 1
                        if first < 0 { first = x }
                        last = x
                    } else if delta > 60 {
                        ink += 1
                        if inkFirst < 0 { inkFirst = x }
                        inkLast = x
                    }
                }
                if g > 0 { greyRows += 1; greyPixels += g }
                // **那一块填充的形状签名**：一行里只有"灰"、一个墨像素都没有。
                // 字本身的抗锯齿永远与墨同一行，所以"纯灰行"只能是**画在字后面的东西**
                // （色块比字高，上下各露几行）—— 这条与倍率、与两台机器的底色都无关，
                // 而"灰像素总数"那种绝对量有（R38 那一课：别拿一台机器的读数当另一台的地板）。
                if g > 0 && ink == 0 {
                    greyNoInkRows += 1
                    widestGreyNoInk = max(widestGreyNoInk, g)
                    if greyOnlyY < 0 {
                        greyOnlyY = y
                        greyOnlyFirst = first
                        greyOnlyLast = last
                    }
                }
                widestInk = max(widestInk, ink)
                if g > widest {
                    widest = g
                    widestX = "x=\(first)..\(last)"
                }
                if ink > 0 {
                    inkRows += 1
                    inkRowYs.append(y)
                    inkRowFirst.append(inkFirst)
                    inkRowLast.append(inkLast)
                }
            }
            // R108：那 1 个纯灰像素**落在谁的字形足迹里**（判法写在 BACKLOG 161，本轮只测不判）。
            var residualGrey = "这一档没有纯灰行"
            if greyOnlyY >= 0 {
                var nearY = -1, nearFirst = 0, nearLast = 0, bestGap = Int.max
                for k in 0..<inkRowYs.count {
                    let gap = abs(inkRowYs[k] - greyOnlyY)
                    if gap < bestGap {
                        bestGap = gap
                        nearY = inkRowYs[k]
                        nearFirst = inkRowFirst[k]
                        nearLast = inkRowLast[k]
                    }
                }
                let inside = nearFirst >= 0 && greyOnlyFirst >= nearFirst && greyOnlyLast <= nearLast
                residualGrey = "纯灰行 y=\(greyOnlyY)px x=\(greyOnlyFirst)..\(greyOnlyLast) "
                    + "最近墨行 y=\(nearY)px(差\(bestGap)px) x=\(nearFirst)..\(nearLast) 落在其x内=\(inside)"
            }
            emit("QUICKPICK_GREY_BAND \(tag) 灰档行数=\(greyRows) 灰档像素=\(greyPixels) "
                 + "最宽一行=\(widest)px \(widestX) 纯灰行无墨=\(greyNoInkRows) "
                 + "纯灰行最宽=\(widestGreyNoInk)px 最宽墨行=\(widestInk)px 墨档行数=\(inkRows) 页底档=\(page) "
                 + "带子=顶部40pt 门限=8..45灰阶 残余灰=\(residualGrey)")
            // —— 收场按 D-170：能力读数排在闸门与 skip 之前，未判要带成因数字。
            guard hasEditor else {
                declined.append("\(tag)[原因=这台机器上那枚字段没有 field editor ⇒ "
                                + "『整串被选中』这一族现象在捕获通道里不存在，两条判据都没有对象]")
                continue
            }
            judged += 1
            // ① 机制那一侧：从**画出这张帧的同一棵树**读，选中区间必须长度 0。
            XCTAssertEqual(selectionLength, 0,
                "\(tag)：字段的选中区间长度是 \(selectionLength)（串长 \(stringLength)）⇒ "
                    + "查询整条被选中，而离屏窗口不是 key（本机读数 `窗口是key=false`），"
                    + "于是选中底画成**灰** —— 真实用户逐字敲，从来没有这一刻（BACKLOG 159）。")
            // ② 像素那一侧：不许有"只有灰、没有墨"的行。字必须在（否则抹掉一切就能通过）。
            XCTAssertGreaterThan(inkRows, 0,
                "\(tag)：顶部那一条带里一个墨像素都没有 ⇒ 查询没画出来，这条判据失去对象，"
                    + "先查捕获通道（与 BACKLOG 158 同一族），不要来放宽这里。")
            // 判据读的是**两个宽度的比**，不是灰像素的绝对数：倍率与底色在两台机器上都不一样（R38），
            // 而"填充比字宽"这件事在任何倍率下都成立 —— 改之前本机是 52px 对 37px，1x 下会等比缩。
            XCTAssertLessThanOrEqual(widestGreyNoInk, widestInk,
                "\(tag)：有一条**只有灰、零个墨**的行宽 \(widestGreyNoInk)px，比最宽的那行墨（\(widestInk)px）还宽 ⇒ "
                    + "字后面有一块比字还宽的填充。改之前本机实测 32 行 / 1115 像素 / 纯灰行最宽 52px "
                    + "对最宽墨行 37px —— 那就是 BACKLOG 159 的灰块（整条查询被选中，而窗口不是 key 所以底是灰的）。"
                    + "残余的几像素是字形抗锯齿，它永远不可能比自己的那行墨更宽。")
        }
        emit("QUICKPICK_PHANTOM_CAPABILITY 候选=2 有对象=\(judged) 未判=\(declined.count)"
             + "（未判名单只在**这台机器装得出 field editor** 时才要求为空）")
        if !declined.isEmpty { emit("QUICKPICK_PHANTOM_DECLINED " + declined.joined(separator: " ")) }
        XCTAssertEqual(sawField, 2,
            "两档里读到搜索字段的档数=\(sawField)（期望 2）⇒ 视图树里根本没有 NSTextField，"
                + "上面那些读数是在猜，159 的机制也就无从判起")
        if judged == 0 {
            throw XCTSkip("这台机器上那枚字段没有 field editor（\(declined.joined(separator: " "))）"
                          + " ⇒ 『幻影选中底』这一族没有对象，**不判（不是通过）**")
        }
        XCTAssertTrue(declined.isEmpty,
                      "这台机器**装得出** editor（有对象=\(judged)），却有一档没判 ⇒ 坏的是尺或那一档的通道："
                    + "\(declined.joined(separator: " "))")
    }

    /// R109 / BACKLOG 162：分栏**每一列**的数值矩形（顶向下，pt）+ 类名。
    ///
    /// 为什么要有它：157 的 CI 答案说臂 2 在 runner 上"整窗有墨（70 行）、带子里 0 墨"，
    /// 而这一句同时兼容两种事实 —— ① 详情那一列**根本没被实例化**，② 详情画了但带子又放错了。
    /// 两种的处置相反（① 夹具忠实性，② 尺），分开它们只需要一行"每一列自己有多少墨"的读数。
    static func splitColumnRects(in host: NSView) -> [(name: String, rect: CGRect)] {
        var out: [(String, CGRect)] = []
        func name(_ v: NSView) -> String { String(describing: type(of: v)) }
        func walk(_ view: NSView) {
            let isSplit = view is NSSplitView || name(view).contains("SplitView")
            if isSplit {
                for sub in view.subviews where name(sub).contains("_NSSplitViewItemViewWrapper") {
                    if let r = Self.topDownRect(of: sub, in: host)?.rect, r.width > 2, r.height > 2 {
                        out.append((name(sub), r))
                    }
                }
            }
            view.subviews.forEach { walk($0) }
        }
        walk(host)
        // 外层与内层分栏会给出互相包含的列；按 x 与宽去重，留下彼此不同的那些。
        var kept: [(String, CGRect)] = []
        for item in out.sorted(by: { $0.1.width < $1.1.width }) {
            if kept.contains(where: { abs($0.1.minX - item.1.minX) < 1 && abs($0.1.width - item.1.width) < 1 }) {
                continue
            }
            kept.append(item)
        }
        // 162 要问的是"侧栏**右边**那一格里有没有东西"，而视图树只给出两块 wrapper：
        // 一块 0..148（侧栏）、一块 0..720（整个内容，详情没有自己单独的 wrapper）。
        // 所以详情那一格必须**推**出来：外列减去侧列。不推的话这行读数只会重复侧栏与整窗，
        // 而 runner 上那一跑仍然分不开"详情没实例化"与"带子放错"。
        if kept.count >= 2 {
            let sorted = kept.sorted { $0.1.minX < $1.1.minX }
            let sidebar = sorted[0].1
            let outer = sorted.last!.1
            let x0 = max(outer.minX, sidebar.maxX)
            if outer.maxX - x0 > 2 {
                kept.append(("详情(外列−侧栏)", CGRect(x: x0, y: outer.minY,
                                                       width: outer.maxX - x0, height: outer.height)))
            }
        }
        return kept.sorted { $0.1.minX < $1.1.minX }
    }

    /// 标题栏在与某一 x 带相交的那一段里**最低**的那条边（pt，顶向下），找不到就 nil。
    ///
    /// 为什么判据要它（R108）：页底被排除之后，"最彩的一行"完全可能是**红绿灯**那一行，
    /// 而不是侧栏选中那一行 —— 那就是假绿的一种标准形状（读数对、对象错）。
    /// 所以列表那一臂的扫描带从"标题栏下沿"开始，纵向位置由被测的视图树自己说，
    /// 不是我按 28pt 猜的常数（装饰高度是**机器相关**的，R107 刚为此栽过一次）。
    static func titlebarBottom(in host: NSView, xRange: Range<CGFloat>) -> CGFloat? {
        var bottom: CGFloat?
        func walk(_ view: NSView) {
            if String(describing: type(of: view)).contains("NSTitlebarBackgroundView"),
               let r = Self.topDownRect(of: view, in: host)?.rect,
               r.minX < xRange.upperBound, r.maxX > xRange.lowerBound {
                if bottom == nil || r.maxY > bottom! { bottom = r.maxY }
            }
            view.subviews.forEach { walk($0) }
        }
        walk(host)
        return bottom
    }

    /// 把 `view` 自己的 bounds 换成**顶向下**的矩形（pt，host 坐标系），并带上 host 是否 flipped。
    ///
    /// 为什么单独有它（本轮实测出来的坑）：`columnBoxes` 那串的"顶向下"用的是
    /// `rootHeight - maxY`，那是**非 flipped** 视图的换算；而 SwiftUI 的 `NSHostingView` 是 flipped 的
    /// ⇒ 同一个数在两种 host 上方向相反。本轮的现场证据：`cardprobe-split-groupbox` 的
    /// `NSTitlebarBackgroundView`（高 52、x 正好在 148pt 的侧栏边界上断开）被打成
    /// `顶向下y=248.0..300.0`，而帧里标题栏明明在最上面（选中胶囊在 92..124pt，正好落在它下面）。
    /// U-305 那一课的形状：**关于中线对称的量永远不会暴露镜像错** —— 所以判据不自己猜方向，
    /// 交给这颗尺，并且每条被扫的带都要能通过"带里必须有墨"这一格证人，否则就是带放错了。
    static func topDownRect(of view: NSView, in host: NSView) -> (rect: CGRect, flipped: Bool)? {
        let f = view.convert(view.bounds, to: host)
        guard f.width > 1, f.height > 1 else { return nil }
        if host.isFlipped { return (f, true) }
        let h = host.bounds.height
        return (CGRect(x: f.minX, y: h - f.maxY, width: f.width, height: f.height), false)
    }

    /// 把顶向下矩形夹到帧的像素范围里（越界不是错误，是"这东西有一半不在帧内"—— 由调用方读数报出去）。
    static func clampBand(_ r: CGRect, scale: Double, pixelsWide: Int, pixelsHigh: Int)
        -> (x: Range<Int>, y: Range<Int>, clipped: Bool) {
        let rawX0 = Int((r.minX * scale).rounded(.down))
        let rawX1 = Int((r.maxX * scale).rounded(.up))
        let rawY0 = Int((r.minY * scale).rounded(.down))
        let rawY1 = Int((r.maxY * scale).rounded(.up))
        let x0 = max(0, min(rawX0, max(0, pixelsWide - 1)))
        let x1 = max(x0 + 1, min(rawX1, pixelsWide))
        let y0 = max(0, min(rawY0, max(0, pixelsHigh - 1)))
        let y1 = max(y0 + 1, min(rawY1, pixelsHigh))
        let clipped = rawX0 < 0 || rawX1 > pixelsWide || rawY0 < 0 || rawY1 > pixelsHigh
        return (x0..<x1, y0..<y1, clipped)
    }

    /// R108 / BACKLOG 160：**"非 key ⇒ 选中一律画成灰"这句今天被拆成两半**。
    /// 同一棵离屏窗口（两臂都是 `窗口是key=false`、同一个 `windowForCapture`）里：
    ///   臂 S = SwiftUI `List(selection:)` 的侧栏选中行 ⇒ 量得**有彩度**（本机 亮 34 / 暗 36）；
    ///   臂 F = `NSTextField` 的 field editor 选中区 ⇒ 量得**无彩度**
    ///        （R106 记的是 亮 `220,220,220` / 暗 `70,70,70`，色度 0）。
    /// 臂 F **刻意把整串选中装回去**，这一臂问的是通道不是产品：产品路径 `show()` 赋空串、
    /// 用户逐字敲，从来没有"整串被选中"这一刻（那正是 R106 / 159 从帧里抹掉的东西）。
    /// 之所以还要装回来：159 修的是"帧里有用户看不到的东西"，而 160 要问的是
    /// "这一刻真的出现时，那一族控件画什么颜色" —— 把对象抹掉之后问不了，所以按臂分开记账。
    ///
    /// 为什么值得单独一条判据：我上一轮解释 159 时把"非 key ⇒ 灰"当成**全局**事实用了，
    /// 而它只在字段那一侧成立。130 / 148① / 批次 82.2 问的"活动与非活动之间那颗蓝会不会变"
    /// 按全局规则问就是一次问六个表面，按本判据问就是**按表面**各问各的。
    ///
    /// 判据走**色度轴**（`max(r,g,b) - min(r,g,b)`），不是亮度轴 —— R38 那一课：
    /// 暗档 `rgb(70,70,70)` 与 `rgb(28,43,64)` 亮度只差约 27，用亮度判必然读成"差不多"，
    /// 而色度是 0 对 36。两道门限**成对**（各 8，一侧 `>` 一侧 `≤`），
    /// 8 来自本机分布而不是印象：色度最大的那一行众数占该行的 0.77，而抗锯齿行的色度都在个位数。
    /// 小面积彩点由"众数必须占该行的三成"筛掉 —— 红绿灯只有几十像素宽，
    /// 它所在那一行的众数还是页底（本轮实测：色度扫描没有把标题栏那几行选出来）。
    ///
    /// 收场按 D-170：能力行与未判名单排在闸门与 skip 之前；只有**两臂都没有对象**才 skip。
    /// runner 上的判法（开跑之前写死，不许看完再定）：
    ///   ① 两臂都无对象 ⇒ 未判 + skip，不算答案；
    ///   ② 列表有色度、字段无 ⇒ 160 的"按控件"结论两台都成立 ⇒ 结案；
    ///   ③ 列表**也**是无彩度 ⇒ 本机那句"非 key 时侧栏仍然是蓝"是那台机器的通道事实
    ///      （与 130 / 147 的"accent 在离屏通道不解析"同族），红要读成"两台的通道不同"，
    ///      **不许**在这里换成"取两臂的比"把 ③ 悄悄吃掉。
    /// 隐私：只打尺寸、坐标、类名、色号，一个字的内容都不打。
    func testSelectionFillUnderInactiveWindowIsPerSurface() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r108-surface-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var declined: [String] = []
        var judged = 0
        for (tag, appearance) in [("light", NSAppearance.Name.aqua),
                                  ("dark", NSAppearance.Name.darkAqua)] {
            let all = self.fixtures(appearance: appearance)
            guard let split = all.first(where: { $0.name == "cardprobe-split-groupbox" }),
                  let pick = all.first(where: { $0.name == "quickpick-typed" }) else {
                return XCTFail("\(tag)：`cardprobe-split-groupbox` 或 `quickpick-typed` 不在名册"
                               + " ⇒ 这条判据没有对象，先查夹具而不是放宽判据")
            }
            // —— 臂 S：什么都不做，产品/通道怎么画就怎么拍。
            var sidebar: (rect: CGRect, kind: String)?
            var titleBottom: CGFloat?
            let sFile = scratch.appendingPathComponent("r108-list-\(tag).png")
            _ = try render(split, appearance: appearance, to: sFile) { host in
                let column = Self.sidebarColumnRect(in: host)
                sidebar = column
                if let c = column {
                    titleBottom = Self.titlebarBottom(in: host, xRange: c.rect.minX..<c.rect.maxX)
                }
            }
            var listScan = SurfaceScan()
            var listBand = ""
            var listMinRun = 0
            var listOK = false
            if let found = sidebar, let image = NSImage(contentsOf: sFile),
               let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
               let bytes = rep.bitmapData {
                let scale = Double(rep.pixelsWide) / Double(split.size.width)
                // 段长的地板用 **pt** 定（4pt），再按这一跑的倍率换算成像素：
                // 2× 上是 8px、1× 上是 4px —— R38 那一课，像素数不能当两台机器的地板。
                listMinRun = max(4, Int((4.0 * scale).rounded(.up)))
                let band = Self.clampBand(found.rect, scale: scale,
                                          pixelsWide: rep.pixelsWide, pixelsHigh: rep.pixelsHigh)
                let page = Self.modalLuma(bytes: bytes, bytesPerRow: rep.bytesPerRow,
                                          xRange: band.x, yRange: band.y)
                // 从"标题栏下沿"开始扫：页底被排除后，红绿灯那一行的彩度比胶囊还高，
                // 让它当选就是假绿（读数对、对象错）。装饰高度由视图树自己说，不是我猜的常数。
                let yStart = max(0, min(Int(((titleBottom ?? 0) * scale).rounded(.up)), rep.pixelsHigh - 1))
                listScan = Self.surfaceScan(bytes: bytes, bytesPerRow: rep.bytesPerRow,
                                            samplesPerPixel: rep.samplesPerPixel,
                                            xRange: band.x, yRange: yStart..<rep.pixelsHigh,
                                            pageLuma: Double(page), minRunPx: listMinRun)
                let tb = titleBottom.map { String(format: "%.1f", $0) } ?? "没有"
                listBand = "列=\(found.kind) x带=\(band.x.lowerBound)..\(band.x.upperBound)px "
                    + "y从=\(yStart)px 标题栏底=\(tb)pt 缩放=\(String(format: "%.2f", scale))x "
                    + "越界=\(band.clipped)"
                listOK = listScan.rows > 0
            }
            if listOK {
                let cRGB = "rgb(\(listScan.chromaticR),\(listScan.chromaticG),\(listScan.chromaticB))"
                let aRGB = "rgb(\(listScan.achromaticR),\(listScan.achromaticG),\(listScan.achromaticB))"
                emit("SELECTION_CHROMA \(tag) 臂=列表 \(listBand) 段长地板=\(listMinRun)px "
                    + "有填充段行=\(listScan.rows) 彩度行=\(listScan.chromaticRows) "
                    + "无彩度行=\(listScan.achromaticRows) "
                    + "最彩段=y=\(listScan.chromaticY)px 宽=\(listScan.chromaticRun)px \(cRGB) "
                    + "色度=\(listScan.chromaticSpread) "
                    + "最宽无彩段=y=\(listScan.achromaticY)px 宽=\(listScan.achromaticRun)px \(aRGB)")
            }
            // —— 臂 F：把选中装回去，再问那一块填充是什么颜色。
            var installed = false
            var fieldBandPt = ""
            var fieldRect: CGRect?
            let fFile = scratch.appendingPathComponent("r108-field-\(tag).png")
            _ = try render(pick, appearance: appearance, to: fFile) { host in
                guard let field = Self.firstOverlayTextField(in: host),
                      let editor = field.currentEditor() as? NSTextView else { return }
                let length = field.stringValue.utf16.count
                editor.setSelectedRange(NSRange(location: 0, length: length))
                editor.needsDisplay = true
                // 用 `topDownRect` 而不是自己减一次高度：host 是否 flipped 决定方向（U-40x）。
                fieldRect = Self.topDownRect(of: field, in: host)?.rect
                installed = length > 0 && fieldRect != nil
                fieldBandPt = "字段类名=\(type(of: field)) 装回选中长度=\(length)"
            }
            guard installed, let rect = fieldRect,
                  let image = NSImage(contentsOf: fFile),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let bytes = rep.bitmapData else {
                let why = installed ? "帧读不回来" : "这一档装不出 field editor（或串长为 0、或字段不在 host 的坐标系里）"
                declined.append("\(tag)[臂=字段 原因=\(why) ⇒ 字段那一侧没有对象，色度对比不判]")
                continue
            }
            let scale = Double(rep.pixelsWide) / Double(pick.size.width)
            let minRun = max(4, Int((4.0 * scale).rounded(.up)))
            let band = Self.clampBand(rect, scale: scale,
                                      pixelsWide: rep.pixelsWide, pixelsHigh: rep.pixelsHigh)
            let page = Self.modalLuma(bytes: bytes, bytesPerRow: rep.bytesPerRow,
                                      xRange: band.x, yRange: band.y)
            let fieldScan = Self.surfaceScan(bytes: bytes, bytesPerRow: rep.bytesPerRow,
                                             samplesPerPixel: rep.samplesPerPixel,
                                             xRange: band.x, yRange: band.y, pageLuma: Double(page),
                                             minRunPx: minRun)
            let aRGB = "rgb(\(fieldScan.achromaticR),\(fieldScan.achromaticG),\(fieldScan.achromaticB))"
            let peak = "y=\(fieldScan.peakY)px 非页底=\(fieldScan.peakOffPage) "
                + "距页底=\(String(format: "%.1f", fieldScan.peakDistance)) 众数=\(fieldScan.peakTop)"
            emit("SELECTION_CHROMA \(tag) 臂=字段 \(fieldBandPt) x带=\(band.x.lowerBound)..\(band.x.upperBound)px "
                + "y带=\(band.y.lowerBound)..\(band.y.upperBound)px 越界=\(band.clipped) "
                + "段长地板=\(minRun)px 有填充段行=\(fieldScan.rows) "
                + "彩度行=\(fieldScan.chromaticRows) 无彩度行=\(fieldScan.achromaticRows) "
                + "最宽无彩段=y=\(fieldScan.achromaticY)px 宽=\(fieldScan.achromaticRun)px \(aRGB) "
                + "最彩段=y=\(fieldScan.chromaticY)px 宽=\(fieldScan.chromaticRun)px 色度=\(fieldScan.chromaticSpread) "
                + "诊断峰行=\(peak) 页底档=\(page)")
            guard listOK else {
                declined.append("\(tag)[臂=列表 原因=这一档没找到侧栏那一列或帧读不回来]")
                continue
            }
            // 证人（R68：证人必须与判据同一颗尺）：这条带里必须有墨 —— 带放错了地方就会露馅。
            XCTAssertGreaterThan(fieldScan.rows, 0,
                "\(tag)：字段那条带里一个 ≥4pt 的同色段都没有 ⇒ 带子放错（纵向约定或 x 带），"
                    + "不是『选中没画』：先看上面那行 `SELECTION_CHROMA 臂=字段` 的 y 带、越界标记与诊断峰行")
            // 段的**宽度**也要有地板：选中底盖住整串（本机 26pt），而字形的一横最多几 pt。
            // 这一格是给 M591（撤掉"装回选中"）准备的牙 —— 只数"有没有 ≥4pt 的同色段"的话，
            // 字形的横画也能凑数，那一臂就变成恒有对象。
            XCTAssertGreaterThanOrEqual(fieldScan.achromaticRun, Int((12.0 * scale).rounded()),
                "\(tag)：字段那一臂最宽的无彩度段只有 \(fieldScan.achromaticRun)px（地板 12pt），"
                    + "不到选中底的宽度（本机实测 52px = 26pt）⇒ 这一臂没有对象")
            XCTAssertGreaterThanOrEqual(fieldScan.achromaticRows, 4,
                "\(tag)：刻意装回的选中区里只有 \(fieldScan.achromaticRows) 行是"
                    + "『与页底亮度差 ≥8 而色度 ≤4』的无彩度填充 ⇒ 这一臂没有对象（通道又变了），"
                    + "两臂的对比无从判起（本机实测 亮/暗 都是 31~32 行 × 52px 宽）。")
            judged += 1
            XCTAssertGreaterThanOrEqual(listScan.chromaticRun, listMinRun,
                "\(tag)：侧栏那一列里没有一段 ≥\(listMinRun)px（4pt）的**同色填充** ⇒ "
                    + "选中行根本没画填充，色度那一格就无从判起")
            XCTAssertGreaterThan(listScan.chromaticSpread, 8,
                "\(tag)：侧栏选中那一行的色度只有 \(listScan.chromaticSpread)（本机看图量的是 亮 34 / 暗 36）"
                    + " ⇒ 这一台机器上 `List` 的选中在非 key 窗口里**也是灰的**。"
                    + "按开跑前写死的判法，这读成「160 的按控件结论在这台机器上变成按机器」，"
                    + "不是尺坏（同一臂的字段那一侧仍按下面那条判）。")
            // 反向牙（不是恒真式）：字段那一臂**不许**出现一段 ≥地板宽且有彩度的填充。
            // 第一版我顺手写成 `chromaticRun ≥ 0` —— 那是永远绿的句子，删掉。
            XCTAssertEqual(fieldScan.chromaticRows, 0,
                "\(tag)：字段那一臂量到 \(fieldScan.chromaticRows) 行**有彩度**的填充段"
                    + "（最宽一段 y=\(fieldScan.chromaticY)px 宽 \(fieldScan.chromaticRun)px "
                    + "色度 \(fieldScan.chromaticSpread)）⇒ 『非 key 时字段选中画成灰』这条前提被推翻，"
                    + "R106/159 那一段的解释要重写（BACKLOG 160 的字段那一侧）")
            XCTAssertLessThanOrEqual(fieldScan.chromaticSpread, 8,
                "\(tag)：字段 editor 的选中底色度是 \(fieldScan.chromaticSpread)，超过无彩度门限 8 ⇒ "
                    + "『字段选中在非 key 时画灰』这条前提被推翻，159 那一段解释要重写（BACKLOG 160）。")
        }
        emit("SELECTION_KEYSTATE_CAPABILITY 候选=2 有对象=\(judged) 未判=\(declined.count)"
             + "（未判名单只在**这台机器两臂都装得出对象**时才要求为空）")
        if !declined.isEmpty { emit("SELECTION_KEYSTATE_DECLINED " + declined.joined(separator: " ")) }
        if judged == 0 {
            throw XCTSkip("两臂都没有对象（\(declined.joined(separator: " "))）"
                          + " ⇒ 160 这条『按表面』的对比在本机判不了，**不判（不是通过）**")
        }
        XCTAssertTrue(declined.isEmpty,
            "这台机器**装得出**对象（有对象=\(judged)），却有一臂没判 ⇒ 坏的是尺或那一档的通道："
                + "\(declined.joined(separator: " "))")
    }

    /// 药丸尺与"第一条墨列"尺的**真值表**（R104）：五格合成件，各钉一道地板。
    ///
    /// 为什么必须有它（R92 那一课）：`overlayPill` 要读真帧的字节，而"漏检"与"这里本来就没有
    /// 药丸"在真帧读数上**一模一样**。没有合成件的话，②那一格（读不到 ⇒ nil）永远无法被证明。
    func testOverlayPillAndStripRulersReadStructure() {
        let width = 840, height = 200, stride4 = 840 * 4
        func buffer(_ page: Int) -> [UInt8] {
            var b = [UInt8](repeating: 0, count: width * height * 4)
            for i in Swift.stride(from: 0, to: b.count, by: 4) {
                b[i] = UInt8(page); b[i + 1] = UInt8(page); b[i + 2] = UInt8(page); b[i + 3] = 255
            }
            return b
        }
        func paint(_ b: inout [UInt8], _ x: Int, _ y: Int, _ w: Int, _ h: Int, _ value: Int) {
            for row in y..<min(height, y + h) {
                for col in x..<min(width, x + w) {
                    let o = row * stride4 + col * 4
                    b[o] = UInt8(value); b[o + 1] = UInt8(value); b[o + 2] = UInt8(value)
                }
            }
        }
        func pill(_ b: [UInt8], page: Int) -> (left: Int, top: Int, bottom: Int)? {
            var copy = b
            return copy.withUnsafeMutableBufferPointer { raw in
                Self.overlayPill(bytes: raw.baseAddress!, width: width, height: height,
                                 bytesPerRow: stride4, pageLuma: page)
            }
        }
        func firstInk(_ b: [UInt8], range: Range<Int>, page: Int) -> Int? {
            var copy = b
            return copy.withUnsafeMutableBufferPointer { raw in
                Self.firstInkColumnInStrip(bytes: raw.baseAddress!, width: width,
                                           bytesPerRow: stride4, yRange: range, background: page)
            }
        }
        // ① 正对照：亮档药丸的真实几何（44…795、行 100 起、60 行高）+ 第 25 列起的字
        var good = buffer(255)
        paint(&good, 44, 100, 751, 60, 220)
        paint(&good, 25, 20, 40, 12, 60)
        XCTAssertEqual(44, pill(good, page: 255)?.left, "药丸左沿必须读在 44px（= 22.0pt @2x）")
        XCTAssertEqual(100, pill(good, page: 255)?.top, "药丸顶读在带子的第一行")
        XCTAssertEqual(159, pill(good, page: 255)?.bottom)
        XCTAssertEqual(25, firstInk(good, range: 0..<98, page: 255), "搜索那一行的第一条墨列")
        // ② 纯色帧 ⇒ 两把尺都读不到（**不许把"读不到"报成 0**：0 会被读成"贴着边"）
        let flat = buffer(255)
        XCTAssertNil(pill(flat, page: 255), "没有带子 ⇒ nil")
        XCTAssertNil(firstInk(flat, range: 0..<98, page: 255), "没有字 ⇒ nil")
        // ③ 带子太窄（30% 帧宽）⇒ 不算药丸（钉 55% 那道地板：行内图标/文字都是短段）
        var narrow = buffer(255)
        paint(&narrow, 44, 100, 252, 60, 220)
        XCTAssertNil(pill(narrow, page: 255), "30% 宽的一段不是药丸")
        // ④ 与页底只差 8 灰阶 ⇒ 不算药丸（钉 `minDelta` 那道地板）。
        //    这一格就是 R100 那把 python 尺翻车的地方：它用"与填充差 ≥40"，
        //    于是亮档那对 35 灰阶的差**整档读不到**（悬崖不是平台）。12 这一档必须有反方向的牙。
        var faint = buffer(255)
        paint(&faint, 44, 100, 751, 60, 247)
        XCTAssertNil(pill(faint, page: 255), "差 8 灰阶不算药丸（地板之下宁可说读不到）")
        var just = buffer(255)
        paint(&just, 44, 100, 751, 60, 243)      // 差 12 ⇒ 正好踩线，要算
        XCTAssertEqual(44, pill(just, page: 255)?.left, "12 是闭区间的下沿")
        // ⑤ 只有一列里一个像素过门限 ⇒ 那是抗锯齿，不是笔画（钉 minPixels=2）
        var single = buffer(255)
        paint(&single, 25, 20, 1, 1, 60)
        XCTAssertNil(firstInk(single, range: 0..<98, page: 255), "单像素不算一列墨")
        // ⑥ 参照色给错档时不许"顺手对上"：把背景当 255 而帧其实是 30 的暗档
        var darkish = buffer(30)
        paint(&darkish, 44, 100, 751, 60, 70)
        paint(&darkish, 25, 20, 40, 12, 235)
        XCTAssertEqual(44, pill(darkish, page: 30)?.left, "暗档同一把尺（差 40）也要读得出药丸")
        XCTAssertEqual(25, firstInk(darkish, range: 0..<98, page: 30), "暗档的字在同一个列")
        // ⑥b **参照色给错档时，这把尺不是"读不到"，而是"整帧都是带子"**（左沿 0、顶 0、底=满高）。
        //    这一格本来我写的是 `XCTAssertNil` —— 那是**我以为的尺的行为**，不是尺的行为（U-315）。
        //    实情记在这里，因为它正是判据里那条正对照（药丸左沿必须落在 15…30pt）存在的理由：
        //    参照色错了，尺会自信地给出一个 0，而 0 看起来像"药丸贴着面板边"，不像"我瞎了"。
        let wrongReference = pill(darkish, page: 255)
        XCTAssertEqual(0, wrongReference?.left, "页底档给错 ⇒ 整帧都算带子，左沿读成 0（不是 nil）")
        XCTAssertEqual(0, wrongReference?.top)
        XCTAssertEqual(height - 1, wrongReference?.bottom)

        // ⑦ R106 / BACKLOG 158 那一格：同一枚字，**对比度低的那台机器**上尺必须还认得它。
        //    合成件照 runner 的档来画：页底 236、字 178 ⇒ 偏离 58（< 全局地板 60），
        //    而本机那一档是页底 252 / 字 128 ⇒ 偏离 124。两块的**列位置相同**（x=25）。
        //    期望两句话：全局地板下低对比那块读不到（nil）—— 这就是 158 在 runner 上的现场；
        //    而 `deltaFloor` 给到该带自己的一半（29）时，两块必须给出**同一个列**。
        var lowContrast = buffer(236)
        paint(&lowContrast, 25, 20, 2, 60, 178)
        var highContrast = buffer(252)
        paint(&highContrast, 25, 20, 2, 60, 128)
        XCTAssertNil(firstInk(lowContrast, range: 0..<98, page: 236),
            "低对比那块（偏离 58）在全局地板 60 下**应该**读不到 —— 这一格钉的就是 158 在 runner 上的形状；"
                + "如果它哪天读得到了，说明全局地板被改低了，那要去看别的判据有没有跟着失去判别力")
        var lowWithFloor: Int?
        var highWithFloor: Int?
        do {
            var copy = lowContrast
            lowWithFloor = copy.withUnsafeMutableBufferPointer { raw in
                Self.firstInkColumnInStrip(bytes: raw.baseAddress!, width: width,
                                           bytesPerRow: stride4, yRange: 0..<98,
                                           background: 236, deltaFloor: 29)
            }
            var copy2 = highContrast
            highWithFloor = copy2.withUnsafeMutableBufferPointer { raw in
                Self.firstInkColumnInStrip(bytes: raw.baseAddress!, width: width,
                                           bytesPerRow: stride4, yRange: 0..<98,
                                           background: 252, deltaFloor: 62)
            }
        }
        XCTAssertEqual(25, lowWithFloor ?? -1,
            "把地板换成「这一条带自己的一半」之后，低对比那台也必须读到同一列（runner 那一档的出路）")
        XCTAssertEqual(lowWithFloor, highWithFloor,
            "两档对比度差一倍，读到的**列**必须相同 —— 这条判据量的是位置，不是强弱")
    }

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
                /// R98：这里**不再种、也不再还原** —— 那两件事搬进了 `render`（见那里的注释）。
                /// 留下来的只有"记一下种之前是什么"，因为最后那条断言要拿它对照：
                /// 现在它判的是 `render` 有没有还原，而不是"调用方有没有记得还原"。
                if let seed = fixture.seed, !originalSeeds.keys.contains(seed.key) {
                    originalSeeds[seed.key] = UserDefaults.standard.string(forKey: seed.key)
                }
                let metrics = try render(fixture, appearance: appearance, to: file)
                if fixture.contentMustFit { mustFitNames.insert(fixture.name) }
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
        // R168 / BACKLOG 194：这一格循环是"空帧"唯一被处置的地方，所以放行谓词的**活体调用点**
        // 就建在这里 —— 计数器不是装饰：本机 `loop_items` 必须 ≥1（`quickpick-empty` 本机 97.9% 未绘制），
        // 为 0 就说明这条分支在这台机器上根本没有证人，谓词接没接线都看不出来。
        var blankLoopItems = 0
        var blankLoopWithGeometry = 0
        var blankLoopWouldRelease = 0
        for item in report where item.metrics.transparent > 0.95 {
            let name = Self.fixtureName(fromFile: item.name)
            let family = name.components(separatedBy: "-").first ?? ""
            let knownIncapable = (family == "settings" && settingsFamilyIsBlank)
            blankLoopItems += 1
            if let geometry = capturedGeometry[item.name] {
                blankLoopWithGeometry += 1
                let would = Self.shouldRegisterBlankAsMachineGap(
                    family: family, requestedHeightPt: geometry.requested,
                    contentHeightPt: geometry.content, hostHeightPt: geometry.host,
                    drawnBoxPt: item.metrics.drawnBoxPt)
                if would { blankLoopWouldRelease += 1 }
                emit("BLANK_GAP_WOULD_RELEASE \(item.name) release=\(would)"
                     + " requested=\(Int(geometry.requested)) content=\(Int(geometry.content))"
                     + " host=\(Int(geometry.host)) drawnBoxPt=\(Int(item.metrics.drawnBoxPt))"
                     + " drawnBottomPt=\(Int(item.metrics.drawnBottomPt))"
                     + " screenVisibleHeightPt=\(Int(geometry.screen))")
                if would {
                    // R170：这条出口**只认实测到的那一种形状**（画出一条比需求窄、又不等于屏幕可视高的带）。
                    // 名字必须是 `*_NOT_RUN` 全大写，`scripts/ci_capture_gate.py` 才把它算成"这台机器判不了"，
                    // 而不是"被吞掉的红"（闸门自己写的处置只有这两种，见 STEP[15] 的正文）。
                    emit("CAPTURE_BLANK_NOT_RUN \(item.name) 高窗在这台机器上只画出一条窄带："
                         + "drawnBoxPt=\(Int(item.metrics.drawnBoxPt)) < requested=\(Int(geometry.requested))"
                         + " 且 ≠ screenVisibleHeightPt=\(Int(geometry.screen))，而同一份二进制本机 box=1040/blank≈0"
                         + " ⇒ 通道性质，记未运行（BACKLOG 194 / R170），机制未命名")
                    continue
                }
            } else {
                emit("BLANK_GAP_WOULD_RELEASE \(item.name) would=no-reading"
                     + "（这一张没进同源几何读数：它的高 <\(Int(Self.tallFixtureHeightFloor))）")
            }
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
        // R168：这一行是谓词**活体调用**的证人。它不判产品，只说明这台机器上
        // 这条分支有没有被真的走过 —— 没有证人的接线与没接线同形（R167 空对账那一族）。
        // 本机与 runner 目前都有证人（本机 `quickpick-empty` 未绘制 ≈97.9%、runner 另有六张高帧），
        // 所以这里**不加地板**：零证人是"这台机器测不到"，不是产品缺陷，写成 skip 名字而不是红。
        if blankLoopItems == 0 {
            emit("BLANK_GAP_WOULD_RELEASE_NOT_RUN 这次捕获一张未绘制帧都没有 ⇒ "
                 + "放行谓词在本机没有活体调用，只有单测那三格（不许据此说出口已验收）")
        } else {
            emit("BLANK_GAP_WOULD_RELEASE_CENSUS loop_items=\(blankLoopItems)"
                 + " with_geometry=\(blankLoopWithGeometry) would_release=\(blankLoopWouldRelease)"
                 + "（with_geometry=0 ⇒ 本机没有高帧空图，放行条件只能靠 CaptureBlankFrameGapTests 那几格（本轮 10 格））")
        }

        // R168 / BACKLOG 194：**分辨轴**。runner 上六张高帧剩下的两种解释（被屏幕裁 / 根本没渲染）
        // 由这一行的 `drawnBoxPt` 分开：`0` ⇒ 没渲染，`≈ screenVisibleHeightPt` ⇒ 被裁，`≈ requested` ⇒ 画满。
        // 依旧**只出读数，不放行、不 skip、不豁免**（R162 的规矩）；本机的高帧是"画满"那一侧的标定样本，
        // 所以两边一起看才知道这把尺在两种形状上都会说话。
        var tallReadings = 0
        for item in report {
            guard let requested = Self.requestedHeightPt(fromFile: item.name),
                  requested >= Self.tallFixtureHeightFloor else { continue }
            tallReadings += 1
            let screenPt = capturedGeometry[item.name]?.screen ?? -1
            emit("CAPTURE_DRAW \(item.name) requested=\(Int(requested))"
                 + " drawnBoxPt=\(Int(item.metrics.drawnBoxPt))"
                 + " drawnBottomPt=\(Int(item.metrics.drawnBottomPt))"
                 + " transparent=\(String(format: "%.1f", item.metrics.transparent * 100))%"
                 + " screenVisibleHeightPt=\(Int(screenPt))")
        }
        emit("CAPTURE_DRAW_CENSUS tall=\(tallReadings)"
             + "（tall=0 ⇒ 这台机器一张高帧都没拍出来，这根轴等于没接，不许读成\"轴已验收\"）")

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
        /// R145 / BACKLOG 177：布局与 caret 静默**之后**、按快门之前，对真实窗口做一次产品入口操作。
        ///
        /// 为什么不能复用 `settle`：捕获路径在 `settle` 之后还会 `makeFirstResponder(nil)` 清闪烁光标，
        /// 而录制态靠第一响应者活着（`HotKeyRecorderButton.resignFirstResponder` 会 `cancelRecording`）
        /// ⇒ 先点再清 caret，等于自己把刚点出来的状态取消掉（本轮实测撞到的）。
        /// 为什么不是"在 build 里造一个已经在录制的视图"：那拍的是我搭的样子，不是产品的入口
        /// （AGENTS.md 第 1 条：验收必须从产品入口进入）。
        let interact: (@MainActor (NSWindow) -> Void)?
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
             interact: (@MainActor (NSWindow) -> Void)? = nil,
             seed: (key: String, value: String)? = nil,
             contentMustFit: Bool = false,
             appKit: (@MainActor () -> NSWindow?)? = nil, _ build: @escaping () -> AnyView) {
            self.name = name
            self.size = size
            self.settle = settle
            self.interact = interact
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

        /// 给一张已建好的夹具补上「按快门前的一次产品入口操作」（其余字段原样带走）。
        /// 为什么要 helper 而不是直接写参数：`build` 是**无标签**的最后一个参数，
        /// 前面一旦出现带标签的 `interact:`，尾随闭包就不再映射到它（编译器报 `expected ')'`）。
        func withInteract(_ action: @escaping @MainActor (NSWindow) -> Void) -> Fixture {
            Fixture(name, size, settle: settle, interact: action, seed: seed,
                    contentMustFit: contentMustFit, appKit: appKit, build)
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

        // R110 / BACKLOG 164：macOS 12 那棵状态项图标的**素材本身**。
        // 12 的分支在本机（13+）永远不会执行，而 `MenuBarExtra` 的图标是系统画的，
        // 所以我让夹具**直接问产品工厂要那张图**（`makeStatusBarIcon()` 为此放宽成 internal，
        // 与 `populate` 同一条先例）。
        // 拍得到：笔画粗细、留白、是否出框、明暗两档的染色（模板图随前景色走）。
        // **拍不到**：`NSStatusItem` 的材质、点击高亮、以及真菜单栏里的基线对齐
        // —— 那三样只有真机能看，登记成批次 85。
        // 名字刻意不是 `menubar-` 前缀：`menuSurfaceReplicaFixtures` 那份名单说的是
        // 「菜单表面的复刻，不许拿来判宽度/截断」，这张是**素材特写**，不是复刻。
        results.append(Fixture("statusitem-glyph", NSSize(width: 160, height: 90)) {
            let glyph = MenuBarController().makeStatusBarIcon()
            return AnyView(
                HStack(alignment: .center, spacing: 18) {
                    Image(nsImage: glyph)
                        .renderingMode(.template)
                        .resizable()
                        .frame(width: 72, height: 72)
                    Image(nsImage: glyph)
                        .renderingMode(.template)
                        .frame(width: 18, height: 18)
                }
                .padding(9)
                .frame(width: 160, height: 90, alignment: .leading)
            )
        })

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
        // R145 / BACKLOG 177：**录制态第一次进帧基线**（136 → 138）。
        // 为什么非拍不可：这颗按钮会吃掉所有按键，而它最重要的那一档状态在 136 张帧里一张都没有 ——
        // R141 加上那一圈描边之后，"它在屏幕上长什么样"只有组件级渲染与一次性的真机截图作过证。
        // R143 撤回 U-470 时确认了离屏通道看得见那一圈，同日 spike 又确认非 key 窗口进得了录制态
        // ⇒ 这一格现在可做，没有"通道拍不到"这个前提。
        results.append(Fixture("settings-shortcuts-recording", NSSize(width: 720, height: 540)) {
            AnyView(self.makeSettingsView(store: store, initialCategory: .shortcuts))
        }.withInteract { window in
            // 深度优先找那颗录制器。**按类名匹配**而不是写 `HotKeyRecorderButton.self`：
            // 在 @MainActor 逃逸闭包里写「类型.self」会被判成 implicit use of self（本轮实测撞到）。
            var stack: [NSView] = window.contentView.map { [$0] } ?? []
            var found: NSControl?
            while found == nil, let view = stack.popLast() {
                if String(describing: type(of: view)) == "HotKeyRecorderButton" {
                    found = view as? NSControl
                }
                stack.append(contentsOf: view.subviews)
            }
            guard let button = found else {
                return XCTFail("录制态夹具在产品视图树里找不到那颗 `HotKeyRecorderButton` ⇒ 这一帧拍的是空气")
            }
            button.performClick(nil)
            RunLoop.current.run(until: Date().addingTimeInterval(0.35))
            XCTAssert(window.firstResponder === button,
                      "点下去之后第一响应者不是那颗录制器 ⇒ 这一帧拍不到录制态"
                          + "（要么 F7 那道守卫拒了，要么夹具与产品不同形）")
        })

        // BACKLOG 140 ①：**隐私**与**推荐**各再拍一档 1040 高的。
        //
        // 为什么是这两屏、为什么非补不可：竖向节奏那把尺现在扫到窗口底，
        // 于是这两档报出"卡片底 == 带子下沿 == 540"（`CARD_RHYTHM settings-privacy light 段1/1
        // y=106.0..539.5pt`、`settings-recommendations light 段1/1 y=171.0..539.5pt`）——
        // 那句话的意思不是"卡片刚好装满"，是**下半截从来没有一张帧看过**。
        // 其余几屏在同一档都自己收了底（快捷键 304.5、数据 324.5、通用 282.0），不需要高夹具。
        // 高度取 1040 而不是新试一个数：`settings-privacy-excluded` 已经在这档上跑了十几轮，
        // 本机与 runner 的行为都是已知的（R28b 撤的是**宽度** 900/1100，与这一档无关）。
        for category in [SettingsCategory.privacy, .recommendations] {
            results.append(Fixture("settings-\(category.rawValue)-tall",
                                   NSSize(width: 720, height: 1040)) {
                AnyView(self.makeSettingsView(store: store, initialCategory: category))
            })
        }
        // R100 / BACKLOG 138 的**系统参照**：一个不加任何水平内边距的 `GroupBox`。
        // 为什么要有它：138 那句"macOS 自己的分组卡通常 16–20pt"没有出处（是印象，不是读数），
        // 而这一扇窗口里七张卡片的水平内缩全部来自 GroupBox 的默认值 ⇒ 唯一合法的对照
        // 是**在同一台机器、同一档外观下**把系统那个值量出来，而不是去借一个别处的常数。
        results.append(Fixture("cardprobe-groupbox-default",
                               NSSize(width: 720, height: 140)) {
            AnyView(GroupBox {
                Text("系统默认内缩")
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(24))
        })
        // R102 / BACKLOG 150 的**容器梯子**：147 结案说"runner 上这扇设置窗口的卡片没有材质层"，
        // 而同一份日志里裸 `GroupBox` 的参照**有** ⇒ 成因在容器，不在 `GroupBox`。
        // **先把上一版写错的地方纠正过来**：150 里那句"装进 `Form` 再跑一次"问错了对象 ——
        // 这扇设置窗口**根本没有 `Form`**（`SettingsView.settingsContent` 是
        // `NavigationSplitView { 侧栏 } detail: { ScrollView { VStack { 分区 } } }`）。
        // 所以实验不是"加一个 Form"，而是**把产品真正用到的容器一层一层加回去**，看哪一层吃掉材质：
        //   臂 0 `cardprobe-groupbox-default`  裸 `GroupBox` + `.padding(24)`        已知：本机两档都有材质
        //   臂 1 `cardprobe-scroll-groupbox`   再多一层 `ScrollView`                 只加滚动容器
        //   臂 2 `cardprobe-split-groupbox`    再加真的 `NavigationSplitView` + 真侧栏  与产品同一棵树
        // 每一臂都在**同一台机器、同一次 run**里由同一颗尺量（`cardRowKinds` + `cardSegments`），
        // 结论由 `CARD_PROBE_ARM` 那几行交出：
        //   臂 1 就没材质 ⇒ 滚动容器是成因；臂 1 有、臂 2 没有 ⇒ 分栏/侧栏是成因；
        //   三臂全有 ⇒ 150 的"容器"这一支被否，嫌疑回到 `Settings` 场景本身（另开一条）。
        results.append(Fixture("cardprobe-scroll-groupbox",
                               NSSize(width: 720, height: 140)) {
            AnyView(ScrollView {
                GroupBox {
                    Text("滚动容器里")
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding(24)
            })
        })
        if #available(macOS 13.0, *) {
            // R107：这一臂的高度从 140pt 改成 **300pt**，理由是量出来的，不是"想让它画出来"：
            // 本轮给臂 2 装了视图树包围盒读数（`CARD_PROBE_GEOMETRY`），它报的是
            // `列0:_NSSplitViewItemViewWrapper[x=0.0..720.0 顶向下y=-85.0..173.0 宽=720.0 高=258.0]`
            // —— 分栏自己的内容盒是 **258pt 高**，而夹具只给 140pt ⇒
            // 帧上看到的是"从一块 258pt 的内容里裁出来的一条 140pt 窗口"，
            // 而那条窗口摆在哪儿**取决于窗口装饰（标题栏）的高度**，也就是**取决于机器**。
            // 这正好是 157 那三成因里"带子没盖住内容"的形状：本机填充行落在 `y=48..68.5pt`，
            // 带子 `24..124pt` 盖得住；换一台装饰更高的机器就会盖不住，而读数长得和
            // "容器吃掉了材质"一模一样（`墨行=0 最大偏离=2`）。
            // 所以先把**实验对象本身**修到不被装饰高度摆布（内容不裁），再来问容器。
            // R119：高度 300 → **600**。理由是被量的，不是猜的：
            // R117 的 CI 上臂 2 的详情列**在树里有东西**（`嵌套hosting=4 列内视图数=7`，本机 6/16），
            // 却整带读出 0 墨 —— 而同一天 `SIDEBAR_ROSTER_RECT` 报出 runner 上整列往下挪了 **282pt**。
            // 两件事合起来只剩一种解释：内容被挪到 300pt 的帧外面去了（被裁），不是容器吃掉材质。
            // ⇒ 把帧加高到任何一台机器都装得下，再问容器。
            results.append(Fixture("cardprobe-split-groupbox",
                                   NSSize(width: 720, height: 600)) {
                AnyView(NavigationSplitView {
                    SettingsSidebarView(selectedCategory: .constant(.general))
                        .navigationSplitViewColumnWidth(min: SettingsViewLayout.sidebarWidth,
                                                        ideal: SettingsViewLayout.sidebarWidth,
                                                        max: 180)
                } detail: {
                    ScrollView {
                        GroupBox {
                            Text("分栏详情里")
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .padding(24)
                    }
                })
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
        // R206 / BACKLOG 228① + 229：D-4 另一半那条回执**第一次进帧基线**。
        //
        // 为什么非要有这张帧：R205 修的那一格是「provider 声称是文件、`loadItem` 却解出 0 个 URL」，
        // 判据三条对照全绿、刀两把全 CAUGHT，可 `frame_baseline compare` 打的是 `CHANGED=0` ——
        // 那一句的真实含义是**这条新代码根本没被拍到**（新分支不在任何夹具里）。
        // 文案与那个数都由产品生产者给（`addDroppedFiles(urls:attemptedCount:)` 自己写 `droppedFilesNotice`），
        // 夹具不手写句子 ⇒ 以后改措辞、改个数、或者干脆不回执了，这张帧自己会红。
        //
        // 第一版被 `testCaptureKeyViews` 的「第一次出现纯黑填充带」拦下（BACKLOG 229）。分辨实验做完了，答案是**候选②**：
        // 逐行扫 x=20..520、三张暗帧各有一条**同样高度**的纯黑带 —— `content-with-notice` y=896..1027、
        // `content-with-two-notices` y=974..1105、本帧 y=872..1003，**高度都是 132px（=66pt @2x）**，只是被横幅推上/下移。
        // ⇒ 黑带不是这张新帧带来的，是"侧栏最后一行的选中材质在离屏下画成黑"这一处**已登记**的盲区（R18 那一族），
        //   新帧只是第一次走到"名单里没有这个名字"那一格。所以登记进 `materialBlindSpotFixtures` 并带上这条读数，
        //   而不是放宽守卫、也不是给同一处盲区换一个新名字。
        let droppedUnreadableStore = makePopulatedStore()
        _ = droppedUnreadableStore.addDroppedFiles(urls: [], attemptedCount: 2)
        results.append(Fixture("content-with-dropped-unreadable-notice", NSSize(width: 750, height: 560)) {
            AnyView(ContentView(historyStore: droppedUnreadableStore))
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

        // R211 / BACKLOG 233：**组合帧** —— 头部 + 分隔线 + 骨架一次拍全。
        // 上面那张 `detail-loading` 画的是 `DetailLoadingView` 一个视图，所以它只能回答
        // "这块骨架长什么样"，回答不了"它在真实详情区里长什么样"——
        // 我看图时因此说错过一句"加载时头部消失了"（D-206 记的就是这个机制）。
        // 这一张从产品入口（`DetailView`）进，靠 `freezeLoadingForCapture` 把异步冻住，
        // 于是"头部与骨架同不同轴"这件事第一次能在**同一张帧**里被量，而不是跨两张帧比。
        let loadingComposedStore = makePopulatedStore(selectingIndex: 2)
        results.append(Fixture("detail-loading-composed", NSSize(width: 720, height: 520)) {
            AnyView(
                DetailView(historyStore: loadingComposedStore, freezeLoadingForCapture: true)
                    .frame(width: 720, height: 520)
            )
        })

        // 行为证人的**不冻臂**住在判据里而不是夹具名单里（R217 / BACKLOG 240）：
        // 它只服务那一条两臂对照，不该进帧基线名单 —— 进了就是多两张帧、动 142 的地板，
        // 而两臂的画实测完全相同（见 `testFrozenArmShowsSkeletonWhileLiveArmDoesNot` 的读数），没有新信息。

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

    /// 纯函数：从逐行众数里挑出「卡片自己的填充」，或者宣布**这一带根本没有卡片**。
    ///
    /// R96 之前这一格是写在 `cardRowKinds` 里的一行：
    /// `modals.first(where: { abs($0 - pageLuma) > 3 })` —— "第一行离页面底超过 3 就算卡片"。
    /// 「统计」那一屏（源码里没有 `GroupBox`，`SettingsView.statsSection` 直接放
    /// `DailyCopyStatsSection`）把这条定义的后果演了一遍：带子里第一个满足条件的
    /// **是一条 1pt 的 `Divider()`**（本机实测：从 y=271.0pt 起、2px 高、
    /// 那一行 94% 的像素都在 228 这一档，见 `.scratch/motion-audit-2/r97_stats_readings.log`）
    /// ⇒ "卡片填充"=那条横线的颜色，而下面那一格又把"众数==页面底"的行一律判成 `.outside`
    /// ⇒ 带子里所有**文字行**连参加墨计数的资格都没有 ⇒ 读数是
    /// 「卡片里没有一行被判成墨 ⇒ 尺没压住字」。**一把本该说"这一屏没有卡片"的尺，说了自己瞎。**
    ///
    /// 判据换成"这个档在整带里占多少行"。地板 20pt 是从上面那组读数里取的，不是最优阈值：
    /// 真卡片 176.5–217.0pt（带子总共 440pt）、那条线 1.0pt ⇒ 20 离两边都远，
    /// 并且给"只有一两行的卡片"（如「通用」那张）留了余量。
    ///
    /// 为什么**不能**用"连续带高"当判据：快捷键那张真卡片的连续带只有 34.5pt
    /// （卡片里字多的行会把众数顶到别的档上），拿它当尺，正对照当场就不绿了 ——
    /// 这一条是本机量出来的，不是推的。
    ///
    /// 并列时取**离页面底近**的那一档：卡片材质是"比页面差一点点"，
    /// 而分隔线/胶囊是"差很多"的那一档。比较器必须全序 —— Swift 的字典遍历顺序不保证，
    /// 只按行数比的话同一帧两遍可能挑到不同的档（R80b 那一族：读数通道自己不稳定，判据就白搭）。
    /// R151 / BACKLOG 191 · 除了"有多少行是这一层"，还要问**这一层在这一行里有多宽**。
    ///
    /// 为什么必须加这一维（runner 的读数，run 39114424945）：那一台机器上被告格整幅只有一层
    /// （`CARD_FILL_CANDIDATES … 前三=(页底:480)`），唯一被当成"第二层"的是 R145 录制态帧那颗**高亮 pill**
    /// （暗档 60 vs 页底 52，差 8 > 门限 3，行数 47px ≈ 23.5pt 刚好过 20pt 的高度门）⇒ `materialCells` 从 0 被抬到 2
    /// ⇒ R100 那条 `materialCells == 0 ⇒ skip` 不再响 ⇒ 29 格未判撞上 `≤4` 地板（U-506）。
    /// 一颗控件与一张卡片在"行数"这一维上可以同形，在"这一层横贯多宽"这一维上差一个数量级：
    /// 本机实测（`/tmp/r151_span_probe.py`，临时尺）pill 行的最长连续段是带宽的 **0.08–0.13**，
    /// 真卡片行是 **0.58–1.00**。切点取 0.4 —— 两侧余量都 ≥3 倍，且 28 张 settings 帧全量重扫后
    /// 每一帧仍有 80–419 行过关（本机材质计数不会掉到地板以下）。
    /// 注意**不要**改用"最左出现到最右出现"那种跨度：pill 行的众数在带子两端都出现，跨度实测 0.87–0.91，
    /// 与真卡片的 0.95 不分辨 —— 那样尺会看起来修好了而什么都没拦住。
    static func cardFill(modals: [Int], pageLuma: Int, scale: Double,
                         gate: Int = 3, minCardHeightPt: Double = 20,
                         runs: [Int] = [], rowWidth: Int = 0,
                         minRunFraction: Double = 0.4) -> Int? {
        var counts: [Int: Int] = [:]
        let useRunAxis = runs.count == modals.count && rowWidth > 0
        let minRun = useRunAxis ? max(1, Int(Double(rowWidth) * minRunFraction)) : 0
        for (index, modal) in modals.enumerated() where abs(modal - pageLuma) > gate {
            // 行数这一维照旧；加上 run 轴之后，"一行里只占一小段的层"（控件、胶囊、描边）不再算卡片的一行。
            if useRunAxis && runs[index] < minRun { continue }
            counts[modal, default: 0] += 1
        }
        guard let best = counts.max(by: { lhs, rhs in
            if lhs.value != rhs.value { return lhs.value < rhs.value }
            let dl = abs(lhs.key - pageLuma), dr = abs(rhs.key - pageLuma)
            if dl != dr { return dl > dr }
            return lhs.key > rhs.key
        }) else { return nil }
        guard Double(best.value) / max(scale, 1) >= minCardHeightPt else { return nil }
        return best.key
    }

    /// 纯函数：把**逐行众数**按"这个档占多少行"排出前三名，连同各自的行数一起交出去。
    ///
    /// 这一格是为 BACKLOG 147 专门开的**成因通道**，不是第二把尺：本机读不到 runner 的像素
    /// （workflow 里没有 `upload-artifact` 步骤，`.scratch/motion-audit-2/r100_ci_readings.md`
    /// §④ 逐字核过），所以"那一台机器上 `GroupBox` 到底画没画出一层材质"这件事
    /// **只能由判据自己打印**才能被回答。三种形状靠这一行压成一种：
    /// 前三名里有一项 ≠ 页底且行数够 ⇒ 材质在、只是差 ≤3 被 `cardFill` 的门限挡掉（门限问题）；
    /// 前三名全是页底 ⇒ 那台机器根本没画材质（通道问题）；
    /// 这一行压根没打出来 ⇒ 判据在那台机器上没走到这一步（先修"为什么没走到"）。
    ///
    /// **它吃的是 `cardFill` 吃的那同一个数组**（`cardRowKinds` 把第一遍的 `modals` 原样交回来），
    /// 不是自己重扫一遍带子。这不是省算力：BACKLOG 104 那一族教过 —— 证人一旦与判据不同颗尺子，
    /// 它作的证就只对新尺成立，而新尺没有自己的判据。
    ///
    /// 排序必须是**全序**（与 `cardFill` 同一族理由：Swift 的字典遍历顺序不保证，
    /// 只按行数比的话同一帧两遍可能给出不同的前三名 ⇒ 读数通道自己不稳定）。
    static func fillCandidates(modals: [Int], top: Int = 3) -> [(luma: Int, rows: Int)] {
        var counts: [Int: Int] = [:]
        for modal in modals { counts[modal, default: 0] += 1 }
        let ranked = counts.keys.sorted { lhs, rhs in
            let l = counts[lhs] ?? 0, r = counts[rhs] ?? 0
            if l != r { return l > r }
            return lhs < rhs
        }
        return ranked.prefix(max(0, top)).map { ($0, counts[$0] ?? 0) }
    }

    /// 纯函数：把上面那前三名渲染成**一行文本**（BACKLOG 147 诊断通道的正文）。
    ///
    /// 为什么要单独拆出来，而不是在两把尺里各写一遍 `map/joined`：纵向节奏与横向内缩这两把尺
    /// 都要打这一行，而它唯一的价值就是"两台机器打的是同一句话"—— 手写两份迟早漂开，
    /// 漂开之后我在 CI 上读到的 `(236:471)` 与本机读到的 `页底 236 占 471 行`
    /// 就成了两个不能对的东西（R68 那一族：证人与判据不同颗尺子）。
    static func fillCandidatesLine(pageLuma: Int, modals: [Int], top: Int = 3) -> String {
        let ranked = fillCandidates(modals: modals, top: top)
        let body = ranked.isEmpty ? "无"
            : ranked.map { "(\($0.luma):\($0.rows))" }.joined(separator: " ")
        return "页底=\(pageLuma) 前三=\(body) 门槛=abs(档-页底)>3且行数/倍率>=20pt"
    }

    /// 把内容列逐行分类。参照是**整块卡片那一个稳定的填充色**（由 `cardFill` 按"这个档占多少行"选，
    /// 不是抄来的色号，也不是"这一行自己的众数"—— 后者在分隔线上会翻车，见下面那段）。
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
        -> (kinds: [CardRowKind], fill: Int, modals: [Int]) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return ([], -1, []) }
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
        var runs: [Int] = []
        modals.reserveCapacity(y1 - y0)
        runs.reserveCapacity(y1 - y0)
        for y in y0..<y1 {
            var histogram: [Int: Int] = [:]
            var rowValues: [Int] = []
            rowValues.reserveCapacity(x1 - x0)
            for x in x0..<x1 {
                let bucket = lumaAt(x, y) / 8
                histogram[bucket, default: 0] += 1
                rowValues.append(bucket)
            }
            let modal = histogram.max { $0.value < $1.value }.map { $0.key } ?? 0
            modals.append(modal * 8 + 4)
            var run = 0, best = 0
            for bucket in rowValues {
                run = (bucket == modal) ? run + 1 : 0
                if run > best { best = run }
            }
            runs.append(best)
        }
        guard let fill = cardFill(modals: modals, pageLuma: pageLuma, scale: scale,
                                  runs: runs, rowWidth: x1 - x0) else {
            // 这一带**根本没有卡片**（而不是"有一张卡片但读不到字"）—— R97 之前这一格会往下走，
            // 于是「统计」那一屏被安上一张 1pt 的假卡片，报出来的是"尺没压住字"。
            // `modals` 照样交出去（BACKLOG 147）：调用方要拿**同一个数组**打前三名，
            // 自己重扫一遍就不是这颗尺子见过的东西了。
            return (Array(repeating: .outside, count: y1 - y0), -1, modals)
        }
        var kinds: [CardRowKind] = []
        for (row, _) in modals.enumerated() {
            let y = y0 + row
            var ink = 0, line = 0, run = 0, best = 0
            for x in x0..<x1 {
                let luma = lumaAt(x, y)
                let dev = abs(luma - fill)
                if dev >= inkGate { ink += 1 } else if dev >= lineGate && dev < lineGate * 8 { line += 1 }
                // "这一像素更像卡片还是更像页面" —— 逐像素问，而不是拿一行的众数去问；
                // 再取**最长连续一段**，因为"这一行还在卡片里吗"问的是卡片有没有横贯过去。
                if dev < abs(luma - pageLuma) { run += 1; best = max(best, run) } else { run = 0 }
            }
            // 「这一行在卡片外」= 这一行里没有一段**够宽**的卡片材质。判据与门槛的出处都写在
            // `cardRowKind` 的文档串里（三个本机量出来的后果：一个色档的偏移会把卡片里的行
            // 翻成"卡片外"；`TextField` 的内芯会把一张卡片切断；而一颗按钮会被当成一张卡片）。
            kinds.append(Self.cardRowKind(cardRun: best, ink: ink, line: line,
                                          width: x1 - x0))
        }
        return (kinds, fill, modals)
    }

    /// 纯函数：一条**逐行布尔**（"这一行在那条窄带里有没有墨"）里数出几段墨带。
    ///
    /// 先合并、后按高度筛 —— 顺序是这条判据的语义，真值表第 ④ 条钉的就是它：
    /// 一颗按钮的字有降部（本机：「移除」那一段在 2x 下被降部切开过），
    /// 反过来写会把同一颗按钮数成 0 段（两段都不够高），于是"两条种子行没画出来"
    /// 与"这台机器画不出字"在报表上长得一模一样 —— 那正是本轮要抓的事，不能给它一个安静的逃法。
    static func inkRunCount(column: [Bool], minRunHeight: Int, mergeGap: Int) -> Int {
        return inkRuns(column: column, minRunHeight: minRunHeight, mergeGap: mergeGap).count
    }

    /// `inkRunCount` 的同一颗尺，只是把**段的位置**也交出来（R99 / BACKLOG 142）。
    ///
    /// 为什么要位置：只有"几段"这一个数的时候，"上方墨带=0"和"上方墨带=1"都没有对象可以
    /// 核对 —— 我看不到那一段在哪、有多高，就没法判断它是分区标题、说明段，还是侧栏串进来的墨。
    /// 计数与位置必须由同一段代码给出，否则"数"和"位置"是两颗尺（BACKLOG 104 那一族）。
    static func inkRuns(column: [Bool], minRunHeight: Int, mergeGap: Int) -> [(top: Int, bottom: Int)] {
        var runs: [(top: Int, bottom: Int)] = []
        var start: Int? = nil
        for (i, inked) in column.enumerated() {
            if inked {
                if start == nil { start = i }
            } else if let head = start {
                runs.append((head, i - 1))
                start = nil
            }
        }
        if let head = start { runs.append((head, column.count - 1)) }
        var merged: [(top: Int, bottom: Int)] = []
        for run in runs {
            if let last = merged.last, run.top - last.bottom - 1 < mergeGap {
                merged[merged.count - 1] = (last.top, run.bottom)
            } else {
                merged.append(run)
            }
        }
        return merged.filter { $0.bottom - $0.top + 1 >= minRunHeight }
    }

    /// 坐标约定：把**带内相对行号**换成**位图绝对行号**。
    ///
    /// 为什么单独有一格（R99 / BACKLOG 142）：`cardRowKinds` 交回来的 `segments[].top`
    /// 是"距离扫描带上沿 `band.minY` 第几行"，而 `columnInk` 吃的是位图的绝对行。
    /// 我第一次把两者直接对接时忘了这个差别，于是量出来的窗口是"绝对行 0..<first.top"
    /// = **0..45.5pt**，而它自认为在量 60..106pt ⇒ 九屏全报"卡片顶之上没有墨"，
    /// 而分区标题明明就画在 78.5..90.5pt（那张被隔离的 python 尺这一格报对了）。
    /// 一个"两种坐标约定"的接口不能靠我脑子里记得 —— 真值表在 `testBandRowToAbsoluteRowIsATruthTable`。
    static func absoluteRows(bandMinY: Double, scale: Double, count: Int) -> Range<Int> {
        return absoluteRows(bandMinY: bandMinY, scale: scale, bandRange: 0..<count)
    }

    /// 同一颗换算的区间版：卡片**之下**那段窗口要从 `last.bottom + 1` 起算，
    /// 而它同样是"带内相对行号"（`rows` / `segments` 的坐标系）。
    static func absoluteRows(bandMinY: Double, scale: Double,
                             bandRange: Range<Int>) -> Range<Int> {
        let top = max(0, Int(bandMinY * scale))
        return (top + bandRange.lowerBound)..<(top + bandRange.upperBound)
    }

    /// 纯函数：一条**逐列布尔**里找"第一段连续够长的真"的起点（R100 / BACKLOG 138）。
    ///
    /// 这是纵向那把尺的**横过来**的版本，语义刻意不同：这里问的不是"有几段"，
    /// 而是"第一段从哪里开始"——卡片左沿就是"从这里往右一路都是卡片材质"的那一列。
    /// 为什么必须有真值表：`firstTrue` 与"够长"这两格在本轮之前各错过一次
    ///（一条 1pt 的分隔线、一颗按钮都曾当上"卡片"，见 `cardFill` 的文档串），
    /// 而"没找到"必须返回 nil 而不是 0 —— 0 会被读成"内缩 = 0pt"，
    /// 那是把"仪器读不到"报成一个具体的产品值（R99 的 python 手搓尺就报出过 −172pt）。
    static func firstSpanStart(columns: [Bool], minRun: Int) -> Int? {
        guard minRun > 0, !columns.isEmpty else { return nil }
        var run = 0
        for (x, on) in columns.enumerated() {
            if on {
                run += 1
                if run >= minRun { return x - run + 1 }
            } else {
                run = 0
            }
        }
        return nil
    }

    /// 纯函数：`from` 之后第一处墨在哪一列；找不到返回 nil（**不返回 0**）。
    static func firstInkColumn(columns: [Bool], from: Int) -> Int? {
        var x = max(0, from)
        while x < columns.count {
            if columns[x] { return x }
            x += 1
        }
        return nil
    }

    /// 进料：把一段**横向**扫描切成两条例向量："这一列还是卡片材质吗"与"这一列有没有碰到墨"。
    ///
    /// 两格的定义不对称是有意的：材质要**一整列基本都是**（≥80% 的采样点"更像卡片而不是页面"），
    /// 否则一条分隔线、一行文字的下沿都会冒充"卡片的左半";
    /// 而墨只要**有一个采样点**偏离填充色够多就算 —— 问"最左边那笔字在哪"的时候，
    /// 一个字形的左上角就该被算进来。
    ///
    /// **两条问的是两条不同的 y 带，这是 R100 修掉的那一格**：
    /// 原来两边共用同一条"卡片顶往下 26pt"的带子，于是
    /// ① 材质那一侧被**圆角**骗：探针那张卡片只有 26pt 高，带子里外都是角，
    ///    读出来的左沿比真左沿晚 7.5pt，正好落在字上 ⇒ "内缩 0.0pt"（一个凭空造出来的产品数值）；
    /// ② 墨那一侧被**带子**骗：`settings-general` 读成 26.0pt，因为带子只盖住第一行，
    ///    而那一行的墨是复选框**后面**的标签；其余四屏第一行是小标题，读成 5.5pt。
    ///    同一扇设置窗口里"卡片内缩"被量成了两个差 20 倍的数，而产品那一侧一行都没错。
    /// 现在：材质问**卡片纵向中点**那一行（那里是直边，圆角够不着），
    /// 墨问**整张卡片的内沿**（"最贴左边的墨"才是"内缩"这个词的意思，与它在第几行无关）。
    ///
    /// **"像卡片"必须是相对判据，不是"离填充色差多少"**（R100 第一次跑就栽在这里）：
    /// 本机卡片填充 244、页面底 252，只差一个色档 ⇒ 用绝对容差 12 会把**页面底**判成材质，
    /// 于是每一屏的"卡片左沿"都读成 0pt、"内缩"读成 40.5pt（那其实是侧栏文字的左边缘）。
    /// 纵向那把尺早就用 `abs(luma-fill) < abs(luma-pageLuma)` 说这句话（R97 / D-155），
    /// 横向这一把第一次写成了绝对容差 —— **同一族错法换了个轴又犯一次**，
    /// 而它没有让任何断言变红：报出来的数格式完全正确、看起来很像读数。
    static func columnFlags(bytes: UnsafePointer<UInt8>, bytesPerRow: Int,
                            xRange: Range<Int>, materialYRange: Range<Int>,
                            inkYRange: Range<Int>,
                            fill: Int, pageLuma: Int, inkGate: Int)
        -> (material: [Bool], ink: [Bool]) {
        var material: [Bool] = []
        var ink: [Bool] = []
        material.reserveCapacity(xRange.count)
        ink.reserveCapacity(xRange.count)
        for x in xRange {
            var cardish = 0, seen = 0
            for y in materialYRange {
                let p = y * bytesPerRow + x * 4
                let luma = Int((0.2126 * Double(bytes[p]) + 0.7152 * Double(bytes[p + 1])
                                + 0.0722 * Double(bytes[p + 2])).rounded())
                seen += 1
                if abs(luma - fill) < abs(luma - pageLuma) { cardish += 1 }
            }
            var inked = 0
            for y in inkYRange {
                let p = y * bytesPerRow + x * 4
                let luma = Int((0.2126 * Double(bytes[p]) + 0.7152 * Double(bytes[p + 1])
                                + 0.0722 * Double(bytes[p + 2])).rounded())
                if abs(luma - fill) >= inkGate { inked += 1 }
            }
            material.append(seen > 0 && cardish * 10 >= seen * 8)
            ink.append(inked >= 1)
        }
        return (material, ink)
    }

    /// 进料：从位图里抽一条**纵向窄带**的逐行墨向量（`inkRunCount` 的纯函数不吃位图）。
    static func columnInk(bytes: UnsafePointer<UInt8>, bytesPerRow: Int,
                          xRange: Range<Int>, yRange: Range<Int>,
                          fill: Int, gate: Int, minInk: Int) -> [Bool] {
        var out: [Bool] = []
        out.reserveCapacity(yRange.count)
        for y in yRange {
            var inked = 0
            let o = y * bytesPerRow
            for x in xRange {
                let p = o + x * 4
                let luma = Int((0.2126 * Double(bytes[p]) + 0.7152 * Double(bytes[p + 1])
                                + 0.0722 * Double(bytes[p + 2])).rounded())
                if abs(luma - fill) >= gate { inked += 1 }
            }
            out.append(inked >= minInk)
        }
        return out
    }

    /// 纯函数：把逐行分类切成**一段一段的卡片**（连续"有卡片材质"的行）。
    ///
    /// 为什么必须有这一格：一个扫描带里可以纵向放**好几张**卡片
    ///（实测 `settings-privacy-excluded` 亮档：「隐私」那张 106..750pt，下面还有「数据与保留」
    /// 那张 ~785..935pt，中间那一行卡片材质像素=0）。R96 的判据把整带当一张卡片，
    /// 于是"边距"量的是两张的外框；R97 之前那一版又把它们并成一段（假红 44.0pt 就是这么来的）。
    /// 所以：**先分段，再逐段判**，每张卡片各得各的读数。
    static func cardSegments(rows: [CardRowKind], scale: Double, minHeightPt: Double = 20)
        -> [(top: Int, bottom: Int)] {
        var out: [(Int, Int)] = []
        var start = -1
        for (i, kind) in rows.enumerated() {
            if kind != .outside {
                if start < 0 { start = i }
            } else if start >= 0 {
                out.append((start, i - 1))
                start = -1
            }
        }
        if start >= 0 { out.append((start, rows.count - 1)) }
        return out.filter { Double($1 - $0 + 1) / max(scale, 1) >= minHeightPt }
    }

    /// 纯函数：**一行**的三个计数 → 这一行的身份。
    ///
    /// 拆出来是为了能拿合成件把四种判定各自钉住（`cardRowKinds` 要读真帧的字节，
    /// 而"漏检"和"没有检出"在真帧读数上一模一样 —— R92 那一课）。
    ///
    /// `cardRun` = 这一行里**最长一段连续**"更像卡片、不像页面"的像素数。它是**唯一**决定
    /// "这一行还在卡片里吗"的量。为什么用"最长一段"而不是"总个数"：三个本机读数各自说明——
    ///   真卡片的普通行 1048/1120 = **94%**；
    ///   卡片里那行 `TextField`（内芯是页面白）左右两侧加起来 518 = **46%**（总数也是这个量级）；
    ///   「恢复默认」那颗 `.bordered` 按钮所在的行 152 = **14%**（按钮宽 76pt，横不过去）。
    /// 地板取 30% ⇒ 按钮被挡掉（它曾被当成一张 23.5pt 的"卡片"，量出 `边距 6.5/5.5、内侧 0.0/0.0`
    /// 这样一条**假红**），而输入框那行仍然算卡片里。
    /// 为什么不是"总个数 + 1%"（R97 中途我用过）：按钮那 152 个像素在 1% 门槛下照样过关，
    /// 而两张卡片之间是 0 个 —— 总个数分不开"一小块控件"与"一条缝"，最长连续段可以。
    static func cardRowKind(cardRun: Int, ink: Int, line: Int, width: Int,
                            outsideTenths: Int = 3, inkMin: Int = 8,
                            lineShareTenths: Int = 8) -> CardRowKind {
        if cardRun * 10 < width * outsideTenths { return .outside }
        if ink >= inkMin { return .ink }
        if line * 10 >= width * lineShareTenths { return .line }
        return .card
    }

    // MARK: - 存在性墨证人（R103 / BACKLOG 150 的那道证人重做）

    /// 纯函数：一个像素离**两个背景里更近的那一个**有多远（R103）。
    ///
    /// `fill < 0` 是 `cardFill` 宣布「这一带没有卡片」的那一档 ⇒ 那时只剩页面底一个参照。
    /// 这一格不是将就，它正是 R102 那四朵红的病根：上一版证人吃的是 `cardRowKinds` 的逐行身份，
    /// 而 `fill < 0` 时那个数组**整带都是 `.outside`**，`.ink` 一格也不可能出现
    /// ⇒ 证人在「判据说没有材质」的那一臂里**结构上必然**报 0。
    /// 反过来说：它只能给「有材质」那一侧作证，而那一侧本来就不需要作证；
    /// 真正需要作证的「`材质=无` 能不能当结论」那一侧，它永远回答「不能」。
    /// R102 的 CI 因此把亮档臂 2 与暗档三臂一起读成红 —— 红的含义是**证人的形状错了**，不是容器。
    static func inkDelta(luma: Int, fill: Int, pageLuma: Int) -> Int {
        let page = abs(luma - pageLuma)
        guard fill >= 0 else { return page }
        return min(page, abs(luma - fill))
    }

    /// 纯函数：一行里有多少个像素算「字的笔画」，门限沿用 `isTextInk`（R24 本机量的那一道：
    /// GroupBox 底 6 与平涂 26 不算字，说明档 109 与标题档 209 算字）。
    /// **本轮不新写一道没量过的色号门限**（账本里那条「不许给没量过的色号写阈值」）。
    static func textInkPixels(rowLumas: [Int], fill: Int, pageLuma: Int) -> Int {
        var count = 0
        for luma in rowLumas where isTextInk(delta: inkDelta(luma: luma, fill: fill,
                                                             pageLuma: pageLuma)) {
            count += 1
        }
        return count
    }

    /// 纯函数：**一行**的逐像素亮度 → 这一行画了字（存在性判据，方向无关）。
    ///
    /// 地板 6 的出处（本机实测，`.scratch/motion-audit-2/r103_floor_exact.log`）：
    /// 六臂 × 两档外观 × 两个尺度（2x 原帧、以及 2x2 抽成 1x 模拟 runner 那一台）里，
    /// 页面底那条参考带的每行墨像素数**恒为 0**，而扫描带里的字行普遍 ≥9（12 组读数里只有 3 组
    /// 出现过 <6 的非零行，值是 4、4、5 —— 那是字形上下沿那一行，只有几个像素过得了门限）。
    /// ⇒ 6 落在「参考带的 0」与「真字行的 9+」之间；被它挡掉的只有字形的最外一圈，
    /// 而证人问的是**这一臂有没有内容**（有一行就算），少算边缘那一行不影响这个问句。
    /// 之所以宁可离上沿近一点：1x 那一档是最坏情况，而真 1x 渲染（不是我这台抽样的近似）
    /// 的细笔画可能比抽样的还少几个像素。两个方向各有一格真值表钉着（第 ⑤⑥⑦ 条）。
    /// （**这一格被更正过一次**：第一版这里写的是「非零行最小 9（1x）/ 15（2x）」，
    /// 那是从一张**只打前 6 档的直方图**里读的 —— 低频的小计数被截掉了。
    /// 出处不能是直方图的头部，得是把最小非零值直接数出来的那一份，见 U-304。）
    ///
    /// **地板这一处比较是唯一定义**（两个重载共用它）：进料那一侧数出像素数之后调这一格，
    /// 免得「这一行算不算有字」在同文件里有两份写法（R68 那一族的同文件版本）。
    static func rowHasTextInk(inkPixels: Int, minPixels: Int = 6) -> Bool {
        // 地板非正 ⇒ 这条判据自己失效（任何一行都算有字），那就不叫证人。
        minPixels > 0 && inkPixels >= minPixels
    }

    static func rowHasTextInk(rowLumas: [Int], fill: Int, pageLuma: Int,
                              minPixels: Int = 6) -> Bool {
        rowHasTextInk(inkPixels: textInkPixels(rowLumas: rowLumas, fill: fill,
                                               pageLuma: pageLuma),
                      minPixels: minPixels)
    }

    /// 进料 + 计数：一块矩形里有**几行**画了字，连同两个成因读数一起交出去（R103 的证人）。
    ///
    /// 为什么证人必须自己扫字节，而不是复用 `cardRowKinds` 交回来的 `rows`：
    /// 证人要证的正是「材质那条通道坏没坏」。它若吃判据的中间量，判据的中间量一坏它就跟着坏，
    /// 而**跟着坏的证人只在判据对的时候亮** —— 那等于没有证人。
    /// 这一格与 BACKLOG 104（R68「证人必须与判据同一颗尺子」）是**同一条规矩的反方向**：
    /// 那次错在证人与判据不同颗尺子，作的证只对新尺成立；这次错在证人吃判据的中间量，
    /// 于是它对「判据说没有」的那一臂永远无能为力。**同一颗尺子只适用于两者问同一件事的时候**；
    /// 文字与材质本来就是两件事，所以这里要的是字节层面的独立。
    ///
    /// `maxDelta` 与 `pixels` 不是装饰：runner 上没有 PNG 可下载，下一次读到 `墨行=0` 时，
    /// 只有 `最大偏离` 能分清「那一台机器压根没画字」（最大偏离也小）与
    /// 「画了字而我的地板太高」（最大偏离大而行数 0）—— 两种收场要修的东西完全不同（D-167 那一族）。
    static func textInkWitness(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                               bytesPerRow: Int, rect: CGRect, scale: Double,
                               fill: Int, pageLuma: Int, minPixelsPerRow: Int = 6)
        -> (rows: Int, pixels: Int, maxDelta: Int) {
        let x0 = max(0, Int(rect.minX * scale)), x1 = min(width, Int(rect.maxX * scale))
        let y0 = max(0, Int(rect.minY * scale)), y1 = min(height, Int(rect.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (0, 0, 0) }
        var rows = 0, pixels = 0, maxDelta = 0
        for y in y0..<y1 {
            var row: [Int] = []
            row.reserveCapacity(x1 - x0)
            for x in x0..<x1 {
                let o = y * bytesPerRow + x * 4
                let luma = Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                                + 0.0722 * Double(bytes[o + 2])).rounded())
                maxDelta = max(maxDelta, inkDelta(luma: luma, fill: fill, pageLuma: pageLuma))
                row.append(luma)
            }
            // 走 `textInkPixels` 而不是就地写第二个判断式：行数与像素数必须出自同一颗尺，
            // 否则「这一行算不算有字」在两处会有两种答案（BACKLOG 104 那一族，这次是同文件版本）。
            let count = textInkPixels(rowLumas: row, fill: fill, pageLuma: pageLuma)
            pixels += count
            if rowHasTextInk(inkPixels: count, minPixels: minPixelsPerRow) { rows += 1 }
        }
        return (rows, pixels, maxDelta)
    }

    /// R107 / BACKLOG 157 的实验 (a)：把"这一臂的**视图树**里详情列到底占哪一块"打成读数。
    ///
    /// 为什么去问视图树而不是继续问像素：157 要分开的三种成因里，
    /// 「扫描带没盖住内容」与「那棵视图在这台机器上根本没画」在像素上是**同一个形状**
    /// （都读 0 行墨），而视图树自己知道答案 —— 分栏有几列、每列多宽、详情列有没有塌成 0。
    /// 打印的只有**类名与数字**，没有任何字符串内容（帧与日志里不许出现用户剪贴板内容）。
    ///
    /// y 换算成"顶向下"与带子同一套约定（`textInkWitness` 直接拿 `rect.minY * scale` 当缓冲区行号，
    /// 也就是 PNG 的顶向下），否则这两行读数没法对（R58 那一族：坐标约定要实测）。
    static func columnBoxes(in host: NSView) -> [String] {
        var out: [String] = []
        func name(_ v: NSView) -> String { String(describing: type(of: v)) }
        func walk(_ view: NSView) {
            let isSplit = view is NSSplitView || name(view).contains("Split")
            if isSplit {
                for (i, sub) in view.subviews.enumerated() {
                    // `NSView.frame(in:)` 在 Swift 里不是一个方法（`frame` 是属性），
                    // 所以走 `convert(_:to:)`：把子视图自己的 bounds 换到 host 的坐标系。
                    // R108 / U-40x：这里的"顶向下"以前**一律**用 `rootHeight - maxY`，
                    // 那是非 flipped 视图的换算 —— 而 SwiftUI 的 `NSHostingView` 是 flipped 的，
                    // 于是本轮实测到标题栏被打成 `顶向下y=248.0..300.0`（它其实在帧的最上面）。
                    // 现在按 `host.isFlipped` 走 `topDownRect`，纵向约定由被测的 host 自己说。
                    let f = Self.topDownRect(of: sub, in: host)?.rect
                        ?? sub.convert(sub.bounds, to: host)
                    out.append("列\(i):\(name(sub))"
                        + "[x=\(String(format: "%.1f", f.minX))..\(String(format: "%.1f", f.maxX))"
                        + " 顶向下y=\(String(format: "%.1f", f.minY))"
                        + "..\(String(format: "%.1f", f.maxY))"
                        + " 宽=\(String(format: "%.1f", f.width)) 高=\(String(format: "%.1f", f.height))]")
                }
            }
            view.subviews.forEach { walk($0) }
        }
        walk(host)
        out.append("host=\(name(host))[宽=\(String(format: "%.1f", host.bounds.width))"
                   + " 高=\(String(format: "%.1f", host.bounds.height))]")
        return out
    }

    /// R108：**包住侧栏那一列的最里层** `_NSSplitViewItemViewWrapper` 的矩形（pt，host 坐标系）。
    ///
    /// 为什么不是"第一个 wrapper"：本轮实测的 `CARD_PROBE_GEOMETRY` 里有两个 wrapper ——
    /// 一个 `x=0.0..720.0`（外层整块内容）、一个 `x=0.0..148.0`（侧栏那一列），
    /// 而外层**也**包含侧栏的子树 ⇒ "第一个含 ColumnView 的"会选到整窗那一块，
    /// 判据就变成"在整窗里找最彩的一行"（红绿灯那几行的众数虽然还是页底，但窗口装饰在两台机器上不一样）。
    /// 取**最窄**那一块才是侧栏。
    ///
    /// 为什么只交 x、不交 y：`columnBoxes` 那个"顶向下"在 `NSHostingView` 上是**镜像的**
    /// —— 本轮实测：同一张帧里 `NSTitlebarBackgroundView` 被打成 `顶向下y=248.0..300.0`，
    /// 而它在 PNG 里明明在最上面（host 是 flipped，`rootHeight - maxY` 那一步方向反了）。
    /// U-305 那一课：**关于中线对称的矩形永远不会暴露镜像错**，所以这里干脆不依赖纵向约定 ——
    /// 纵向扫整列，靠"众数占该行的比例"把小面积彩点筛掉，而不是靠"从第几行开始"。
    static func sidebarColumnRect(in host: NSView) -> (rect: CGRect, kind: String)? {
        func name(_ v: NSView) -> String { String(describing: type(of: v)) }
        func containsColumn(_ v: NSView) -> Bool {
            if name(v).contains("ColumnView") { return true }
            return v.subviews.contains { containsColumn($0) }
        }
        var best: (CGRect, String)?
        func walk(_ view: NSView) {
            let isSplit = view is NSSplitView || name(view).contains("SplitView")
            if isSplit {
                for sub in view.subviews where name(sub).contains("_NSSplitViewItemViewWrapper")
                                            && containsColumn(sub) {
                    let f = sub.convert(sub.bounds, to: host)
                    if best == nil || f.width < best!.0.width { best = (f, name(sub)) }
                }
            }
            view.subviews.forEach { walk($0) }
        }
        walk(host)
        guard let found = best, found.0.width > 1 else { return nil }
        return found
    }

    /// R108：**按"每一行的众数色"扫色度**，返回一行的分布签名。
    ///
    /// 为什么是色度而不是亮度（这是本轮判据的整个前提）：
    /// 暗档里"非 key 的灰选中底"是 `rgb(70,70,70)`，而"仍然是蓝的侧栏选中"是 `rgb(28,43,64)` ——
    /// 两者亮度分别约 70 与 43，**用亮度轴判会读成"都是深色、差不多"**，
    /// 而色度是 0 对 36，一眼分开。R38 那一课的形状：一台机器的档位不能当另一台的地板，
    /// 而"通道之间的差"在两档外观、两台机器、两种倍率下都是同一个定义。
    ///
    /// 为什么看**众数**而不是"这一行里有没有彩点"：红绿灯（红/黄/绿）只有几十像素宽，
    /// 它所在那一行的众数仍然是页底色 ⇒ 小面积彩点被自然压掉；
    /// 而侧栏选中那颗胶囊铺满整列（本机实测众数占该行的 77%）⇒ 大面积填充才进得了判据。
    /// R108 的扫描结果：一行的**最长同色段**签名。
    ///
    /// 为什么不是"这一行的众数色"（这是本轮第二版栽过之后换的 shape，两处实测都在下面）：
    ///   ① 众数把**页底也算进去** ⇒ 字段那一臂的选中底只有字那么宽（本机 52px）而整条带 800px，
    ///      每一行的众数永远是页底 ⇒ 两臂读数一模一样（假绿）；
    ///   ② 众数即使只取"离页底 ≥3"的像素，**字段自己的白底**会当选：
    ///      本机亮档实测 `众数=255,255,255×748（距页底 3.0） 次位=220,220,220×52` ——
    ///      真正的选中底排在第二名，众数那一格永远看不见它，于是亮档量到 `无彩度行=0`、
    ///      暗档量到 31，看起来像"亮档没画填充"，其实是尺读错了对象。
    /// **连续同色段**这两个问题都没有：它问的是"这里有没有一块面积"，
    /// 而白底是"整片背景"不是"一块填充"—— 它离页底只有 3 档，被 ≥8 的档差门限直接排除。
    /// 段长门限由调用方按**倍率**换算成 pt（R38：不许拿一台机器的像素数当另一台的地板）。
    struct SurfaceScan {
        var rows = 0
        var chromaticRows = 0
        var achromaticRows = 0
        var chromaticY = -1
        var chromaticRun = 0
        var chromaticSpread = 0
        var chromaticR = 0
        var chromaticG = 0
        var chromaticB = 0
        var achromaticY = -1
        var achromaticRun = 0
        var achromaticR = 0
        var achromaticG = 0
        var achromaticB = 0
        // 诊断那一格：非页底像素最多的一行的前三名色号。
        // 留它的理由见上面 ② —— "填充没画"与"画了但离页底太近"在计数格里长得一样，
        // 只有原始分布能把它们分开（R92 那一课：缺值与缺对象都要能被数出来）。
        var peakY = -1
        var peakOffPage = 0
        var peakDistance = 0.0
        var peakTop = ""
    }

    static func surfaceScan(bytes: UnsafePointer<UInt8>, bytesPerRow: Int, samplesPerPixel: Int,
                            xRange: Range<Int>, yRange: Range<Int>,
                            pageLuma: Double, minRunPx: Int) -> SurfaceScan {
        var s = SurfaceScan()
        for y in yRange {
            var counts: [Int: Int] = [:]
            var offPage = 0
            var runColor = -1
            var runLen = 0
            var topRun = 0
            var topColor = -1
            for x in xRange {
                let i = y * bytesPerRow + x * samplesPerPixel
                let a = bytes[Int(i) + 3]
                let r = Int(bytes[i]), g = Int(bytes[i + 1]), b = Int(bytes[i + 2])
                let luma = 0.299 * Double(r) + 0.587 * Double(g) + 0.114 * Double(b)
                let packed = (r << 16) | (g << 8) | b
                // 与页底差 ≥8 的才算"不是背景"（8 沿用 `cardFill` 判第二层的那一档常数）。
                if a > 250 && abs(luma - pageLuma) >= 8 {
                    counts[packed, default: 0] += 1
                    offPage += 1
                    if packed == runColor {
                        runLen += 1
                    } else {
                        runColor = packed
                        runLen = 1
                    }
                    if runLen > topRun {
                        topRun = runLen
                        topColor = packed
                    }
                } else {
                    runColor = -1
                    runLen = 0
                }
            }
            guard offPage > 0 else { continue }
            if offPage > s.peakOffPage, let peak = counts.max(by: { $0.value < $1.value }) {
                let pr = (peak.key >> 16) & 0xff, pg = (peak.key >> 8) & 0xff, pb = peak.key & 0xff
                let pluma = 0.299 * Double(pr) + 0.587 * Double(pg) + 0.114 * Double(pb)
                s.peakOffPage = offPage
                s.peakY = y
                s.peakDistance = pluma - pageLuma
                var others: [String] = []
                for extra in counts.sorted(by: { $0.value > $1.value }).dropFirst().prefix(2) {
                    let er = (extra.key >> 16) & 0xff, eg = (extra.key >> 8) & 0xff, eb = extra.key & 0xff
                    others.append("\(er),\(eg),\(eb)×\(extra.value)")
                }
                let tail = others.isEmpty ? "" : " 次位=\(others.joined(separator: " "))"
                s.peakTop = "\(pr),\(pg),\(pb)×\(peak.value)\(tail)"
            }
            guard topRun >= minRunPx else { continue }
            let r = (topColor >> 16) & 0xff, g = (topColor >> 8) & 0xff, b = topColor & 0xff
            let spread = max(r, max(g, b)) - min(r, min(g, b))
            s.rows += 1
            if spread >= 6 {
                s.chromaticRows += 1
                if spread > s.chromaticSpread {
                    s.chromaticSpread = spread
                    s.chromaticY = y
                    s.chromaticRun = topRun
                    s.chromaticR = r
                    s.chromaticG = g
                    s.chromaticB = b
                }
            } else if spread <= 4 {
                s.achromaticRows += 1
                if topRun > s.achromaticRun {
                    s.achromaticRun = topRun
                    s.achromaticY = y
                    s.achromaticR = r
                    s.achromaticG = g
                    s.achromaticB = b
                }
            }
        }
        return s
    }

    /// R107：分栏的**内容盒有没有溢出夹具**（pt）。0 = 完全在帧内。
    ///
    /// 为什么要有它：本轮把臂 2 从 140pt 高改成 300pt，理由就是包围盒读数报的
    /// `顶向下y=-85.0..173.0`（内容盒 258pt 塞进 140pt 的窗，于是帧看到的是"裁出来的一条窗口"，
    /// 而这条窗口摆在哪儿**取决于窗口装饰高度**，也就是取决于机器）。
    /// 那件事如果哪天回来（有人把夹具改矮、或某台机器的装饰更高），
    /// 157 的实验就会重新变成"读 0 行墨"这种和"容器吃掉材质"长得一模一样的形状。
    /// 所以这一格把那个混淆**钉成会红的**：溢出 > 1pt ⇒ 红，并且消息里说清这是实验对象坏了，不是产品。
    static func splitContentOverflow(in host: NSView) -> Double {
        var overflow = 0.0
        func walk(_ view: NSView) {
            let name = String(describing: type(of: view))
            if name.contains("_NSSplitViewItemViewWrapper") || (view is NSSplitView && name != "NSHostingView") {
                for sub in view.subviews where String(describing: type(of: sub)).contains("SplitViewItem") {
                    let f = sub.convert(sub.bounds, to: host)
                    overflow = max(overflow, -f.minY)
                    overflow = max(overflow, f.maxY - host.bounds.height)
                }
            }
            view.subviews.forEach { walk($0) }
        }
        walk(host)
        // 归一化 -0.0：`max(0.0, -0.0)` 在 Swift 里可能留下负零，而读数打出 `-0.0pt` 会让人以为
        // 有什么方向性（U-305 那一族：一个格式上的负号被读成一个物理事实）。
        let rounded = Double((overflow * 10).rounded()) / 10
        return rounded == 0 ? 0 : rounded
    }

    /// 纯函数：一张浮层帧里**选中药丸**的位置（左沿 / 顶 / 底，px）；读不到返回 nil，**不返回 0**
    /// （0 会被读成"药丸贴着边"，那是把"仪器读不到"报成一个具体的产品值 —— R100 那一族）。
    ///
    /// 判据是**结构**，不是色号：一行里有一段连续、宽度 ≥ 帧宽 55%、且与页底差 ≥ 12 灰阶的带子，
    /// 才算这一行落在药丸上；左沿取这些行的**中位数**（圆角让首末几行往里缩，取平均会被它们拉偏）。
    ///
    /// 为什么不能写一个绝对色号：本机亮档药丸是 (220,220,220) 对页底 (255,255,255) ⇒ 差 35，
    /// 暗档是 (70,70,70) 对 (30,30,30) ⇒ 差 40。R100 那把 python 尺用的是"与填充差 ≥40"，
    /// 于是它在**亮档整档读不到这一带**（门限落在一对悬崖上，BACKLOG 148 的 R102 追记 ①）。
    /// 12 这一档取在"两档都量到的最小差 35"与噪声之间；"宽度 ≥55%"把行内图标、文字这些短段全挡掉。
    static func overlayPill(bytes: UnsafePointer<UInt8>, width: Int, height: Int,
                            bytesPerRow: Int, pageLuma: Int,
                            minDelta: Int = 12, minWidthShare: Double = 0.55)
        -> (left: Int, top: Int, bottom: Int)? {
        guard width > 0, height > 0, minWidthShare > 0, minWidthShare <= 1 else { return nil }
        let minWidth = Int(Double(width) * minWidthShare)
        guard minWidth > 0 else { return nil }
        func lumaAt(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        var lefts: [Int] = []
        var top = -1, bottom = -1
        for y in 0..<height {
            var run = 0, best = 0, bestStart = 0, start = 0
            for x in 0..<width {
                if abs(lumaAt(x, y) - pageLuma) >= minDelta {
                    if run == 0 { start = x }
                    run += 1
                    if run > best { best = run; bestStart = start }
                } else {
                    run = 0
                }
            }
            guard best >= minWidth else { continue }
            lefts.append(bestStart)
            if top < 0 { top = y }
            bottom = y
        }
        guard !lefts.isEmpty else { return nil }
        lefts.sort()
        return (lefts[lefts.count / 2], top, bottom)
    }

    /// 纯函数：一条横向带子里**第一个有字的列**在哪一列（px）；一条都没有 ⇒ nil。
    ///
    /// "有字"沿用 `isTextInk`（R24 本机量的那道 60）与 `textInkPixels` 同一个参照式：
    /// 离背景足够远。这里背景就是整帧的页底档 —— 浮层没有"卡片"那一层，
    /// 所以不需要 R103 那个"离两个背景都远"的形状（那一格是为材质层准备的）。
    /// `minPixels` 取 2：单列一个像素过门限是抗锯齿，两个才算笔画。
    static func firstInkColumnInStrip(bytes: UnsafePointer<UInt8>, width: Int,
                                      bytesPerRow: Int, yRange: Range<Int>,
                                      background: Int, minPixels: Int = 2,
                                      deltaFloor: Int? = nil) -> Int? {
        guard width > 0, !yRange.isEmpty, minPixels > 0 else { return nil }
        func lumaAt(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        // `deltaFloor` 是给**跨机器**那一格开的口子（R106 / BACKLOG 158 的答案）：
        // 全局的 `isTextInk` 地板 60 是在本机量的（R24），而 runner 上同一枚占位语对面板底的
        // 最大偏离只有 **58（亮）/ 49（暗）** —— 不是没画，是那台机器的底色档不同（页底 236/52 对本机 252/28）。
        // 所以"这一条带里有没有字"这种**存在性**问题，地板必须由**这一条带自己有多强**推出来，
        // 不能从一台机器的调色盘里抄（R38：两台机器的读数不能当另一台机器的地板）。
        func isInk(_ delta: Int) -> Bool {
            guard let floor = deltaFloor else { return Self.isTextInk(delta: delta) }
            return delta >= floor
        }
        for x in 0..<width {
            var inked = 0
            for y in yRange where isInk(abs(lumaAt(x, y) - background)) {
                inked += 1
                if inked >= minPixels { return x }
            }
        }
        return nil
    }

    /// 纯函数：从**一张卡片**的逐行分类里读出「卡片四边的留白」与「分隔线两侧的留白」（pt）。
    ///
    /// 缺陷形状是这一族里最不容易靠眼睛抓到的：卡片**自己**没错，每一行也都没错，
    /// 错的是同一张卡片里存在两种留白（内侧 14.5pt、边缘 6.5pt）。
    /// 所以判据必须是"这几个数是不是同一个数"，而不是"这个数够不够大" ——
    /// 后者会被"整体都很挤"骗过去，前者不会。
    ///
    /// R97 把"哪一段算一张卡片"交给了 `cardSegments`：这一支从此只面对**一张**卡片，
    /// 输入的第一行就是卡片顶、最后一行就是卡片底。它不再需要"顶到带上沿"那两种拒绝，
    /// 因为那已经不是它能回答的问题（它没见过带子）。
    static func cardRhythm(rows: [CardRowKind], scale: Double)
        -> (edges: [Double], gaps: [Double], dividers: Int, declined: String, run: [Int]) {
        let unit = 1.0 / max(scale, 1)
        guard let firstInk = rows.firstIndex(of: .ink),
              let lastInk = rows.lastIndex(of: .ink) else {
            return ([], [], 0, "卡片里没有一行被判成墨 ⇒ 尺没压住字", [])
        }
        var gaps: [Double] = []
        var dividers = 0
        var i = 0
        while i < rows.count {
            guard rows[i] == .line else { i += 1; continue }
            var j = i
            while j + 1 < rows.count, rows[j + 1] == .line { j += 1 }
            dividers += 1
            var up = i - 1
            while up >= 0, rows[up] != .ink { up -= 1 }
            var down = j + 1
            while down < rows.count, rows[down] != .ink { down += 1 }
            // 留白数的是**空行**：从上一行墨到这一行线之间，中间那几条不带墨的行。
            if up >= 0 { gaps.append(Double(i - up - 1) * unit) }
            if down < rows.count { gaps.append(Double(down - j - 1) * unit) }
            i = j + 1
        }
        return ([Double(firstInk) * unit, Double(rows.count - 1 - lastInk) * unit],
                gaps, dividers, "", [0, rows.count - 1, lastInk])
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
        // R145：录制态那张新帧也在 vibrancy 子树里 ⇒ 同一处合成前极性盲区（闸门实测把它点名，
        // 不是"顺手补名单"：`TEXT_SIDE_ROSTER_EXTRA` 的 vibrant 前提里有它）。
        "settings-shortcuts-recording",
        // R39 新增的两张（禁用态 / 失败回执）也进名单 —— 这条不是"顺手补名单"：
        // 先看了那张帧（`/tmp/r39-crops/r39-settings-general-login-unsupported-dark-sidebar.png`）：
        // 暗档侧栏里"快捷键 / 隐私 / 推荐 / 数据 / 统计"五枚标签**黑字黑底看不见**，
        // 而选中的"通用"是白字蓝底（强调色走固定色，不受 vibrancy 极性影响），图标也看得见。
        // 与 R29d/R30 那张是同一个机制（D-090：合成前的极性），所以记为盲区而不是缺陷。
        // 名单由 `testDarkSettingsSidebarTextIsACountedBlindSpot` 的 vibrant 前提决定，手改不改得绿。
        "settings-general-login-unsupported", "settings-general-login-failed",
        // R98 新增的两张高夹具（BACKLOG 140 结案那一半）也进名单 —— 同样不是"顺手补名单"：
        // 先看了那张帧（`/tmp/r98_tall_dark_sidebar.png`，`settings-privacy-tall` 暗档侧栏那一列），
        // 「快捷键 / 通用 / 推荐 / 数据 / 统计」五枚标签黑字黑底几乎看不见，
        // 而选中的「隐私」是白字蓝底药丸（强调色走固定色，不受 vibrancy 极性影响）——
        // 与 R29d/R30 同一机制（D-090：合成前的极性），所以记为盲区而不是缺陷。
        // 名单由 `testDarkSettingsSidebarTextIsACountedBlindSpot` 的 vibrant 前提决定，手改不改得绿。
        "settings-privacy-tall", "settings-recommendations-tall",
    ]

    /// 盲区名单**按机器分键**（R124 / BACKLOG 171）。
    ///
    /// 为什么要分键：这份名单从 R29d 起被当"全局权威"用，而它量的其实是
    /// **vibrant 子树 + `cacheDisplay` 不走合成**这一台机器的行为。本机反侧、runner 不反侧
    /// （R120 的 CI：`TEXT_SIDE_CAPABILITY 侧栏偏离=19470 … 判了 13/13` 之后
    /// `gone` 那朵红落地），两台都是真的离屏捕获 —— 那么"名单"就必须说清是哪台的名单。
    /// 键只准用**量出来的**事实（架构 / 系统版本 / 帧倍率），不许手挑一个看起来像的名字：
    /// R118 已经证明绝对坐标是机器相关的，而倍率与系统版本正是那两类差异的来源。
    static func sidebarRosterMachineKey(scale: Double) -> String {
        #if arch(arm64)
        let arch = "arm64"
        #elseif arch(x86_64)
        let arch = "x86_64"
        #else
        let arch = "other"
        #endif
        let v = ProcessInfo.processInfo.operatingSystemVersion
        let scaleText = scale >= 1.75 ? "2x" : (scale <= 1.25 ? "1x" : "other")
        return "\(arch)/macOS \(v.majorVersion).\(v.minorVersion)/\(scaleText)"
    }

    /// 每台机器一行。**没登记的那台必须红**：如果"不在表里"能安静通过，
    /// 那么任何一台新机器跑这条判据都会白拿一个绿（这才是 171 真正要拦的事）。
    /// 值 = 那一台上实测反侧的夹具；空集也是一条**声明**（"这台机器不反侧"），
    /// 它同样要被 `gone`/`extra` 两格钉住 —— 所以加一行之前必须真的去看那张帧。
    static let darkSidebarTextBlindSpotsByMachine: [String: Set<String>] = [
        // 本机（Retina 2x）：R29d / R30 / R39 / R98 一路看帧登记的 13 张。
        "arm64/macOS 27.0/2x": darkSidebarTextBlindSpots,
        // CI runner（GitHub macos-15，arm64、非 Retina）：**空集是一条声明，不是一行占位**。
        // 键与空集都不是我猜的 —— 来自 R124 那一跑自己印出来的两行：
        //   `TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 个夹具`
        //   （run 39031123341，171 故意留的那朵 `UNKEYED` 红）。
        // ⇒ 这台机器上侧栏暗档文字**不反侧**（13/13 全部落在期望侧），所以它的盲区位就是空。
        // 空集仍然被 extra/gone 两格钉着：哪天它反侧了 ⇒ `新盲区` 红；哪天有人往这一行里
        // 抄进本机那 13 张 ⇒ 这一台的 `不再反侧` 立刻红。
        "arm64/macOS 15.7/1x": [],
    ]

    /// 键的形状也是判据：`arch/macOS 主次版本/倍率` 三段，倍率只准是 `1x` 或 `2x`。
    /// 为什么要钉形状：这一行的键必须由**被打印出来的**读数填（D-186③），
    /// 而"看起来像 runner 的键"（`runner`、`CI`、`macos-15`）都能通过 `count >= 2` 那种懒判据，
    /// 却永远不会被命中 —— 那是一条死行，比没有更坏。
    static func sidebarRosterKeyIsWellFormed(_ key: String) -> Bool {
        let parts = key.split(separator: "/", omittingEmptySubsequences: false)
        guard parts.count == 3 else { return false }
        let archOK = parts[0] == "arm64" || parts[0] == "x86_64"
        let os = parts[1]
        let version = os.hasPrefix("macOS ") && os.dropFirst(6).split(separator: ".").count == 2
            && os.dropFirst(6).split(separator: ".").allSatisfy { Int($0) != nil }
        return archOK && version && (parts[2] == "1x" || parts[2] == "2x")
    }

    /// 名单与本机实测的四种关系，各有不同的修法（D-183 的形状：不许共用一个词）。
    enum SidebarRosterVerdict: Equatable {
        case unkeyed                 // 这台机器的位没登记 ⇒ 红（去看一眼，再决定登记哪一行）
        case clean                   // 与本机那一行完全一致
        case extra(Set<String>)      // 新盲区 ⇒ 红
        case gone(Set<String>)       // 登记过的帧不再反侧 ⇒ 红（机制修好了，或者尺瞎了）
    }

    static func sidebarRosterVerdict(registered: Set<String>?, measured: Set<String>)
        -> SidebarRosterVerdict {
        guard let registered = registered else { return .unkeyed }
        let extra = measured.subtracting(registered)
        if !extra.isEmpty { return .extra(extra) }
        let gone = registered.subtracting(measured)
        if !gone.isEmpty { return .gone(gone) }
        return .clean
    }

    /// 四种结局各一个词，且结论行要打在闸门之前（U-391 那一族）。
    static func rosterVerdictText(_ verdict: SidebarRosterVerdict) -> String {
        switch verdict {
        case .unkeyed: return "红(这台机器的位没登记)"
        case .clean: return "一致"
        case .extra(let s): return "红(新盲区\(s.count)张)"
        case .gone(let s): return "红(登记过的\(s.count)张不再反侧)"
        }
    }

    /// 侧栏那一列"文字应当出现的位置"（pt）。
    /// 左边界从 40 起：图标列在 12–34，把图标框进来会让"符号的固定色"混进这条读数，
    /// 那是 BACKLOG 41 那半条要单独判的事。右边界 142 = 侧栏宽 148 留 6pt 内边距。
    /// **R116 把 y 带换成实测行带**（六行 `_FocusRingView` = y 60..252，每行 32pt）。
    /// 原来这里写的是 `y 96 h 154`（96..250）—— 那是**五行时代**的坐标，阶段一加「统计」之后
    /// 它只盖住 5/6 行，而它喂的 `TEXT_SIDE` 与暗档盲区名单一路全绿（BACKLOG 169 / U-383）。
    /// 现在这条矩形与树给的行带由 `testSettingsSidebarRosterRectCoversEveryRow` 钉在一起：
    /// 布局再变而这里没跟着改，红的是这条守卫。
    static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 192)

    /// **同一张帧的内容区**（x 160 起：侧栏宽 148 + 分栏线）。
    /// 这一块的用途不是判产品，是**分辨"这台机器拍不出这一页"和"我这把尺瞎了"** ——
    /// 前者 BACKLOG 43 已经实测过（runner 上 `SettingsView` 整页是一块平涂底色），
    /// 后者是 R29d 刚在 `.scratch` 那把尺上犯过的错（`modalColor` 把 pt 当 px，
    /// 于是框其实没压住字，却报出一个像结论的数）。两种情况修法完全相反。
    static let settingsContentPane = CGRect(x: 160, y: 70, width: 400, height: 200)
    /// 一列里**视图树自己有多少可画的东西**（R117 / BACKLOG 150 的证人）。
    ///
    /// 为什么像素那两把尺不够：`CARD_PROBE_WHOLE`（整窗 vs 带子）能分开"带子放错"与"整页没画"，
    /// `CARD_PROBE_COLUMNS`（逐列墨）能分开"侧栏有墨"与"详情没墨"，
    /// 但**"详情列在树里存在、里面却是空的"与"详情画了但被裁到帧外"**在像素上是同一个形状：0 墨。
    /// 150 要的正是这两者的区别 —— 前者是实例化（runner 上的 `NavigationSplitView` 详情没被建出来），
    /// 后者才是容器吃材质。所以直接数这一列里的文字/图像类子视图与它们的包围盒。
    static func columnSubviewInventory(in host: NSView, rect: CGRect)
        -> (texts: Int, images: Int, hosts: Int, inside: Int, sample: [String]) {
        var texts = 0, images = 0, hosts = 0, inside = 0
        var raw: [(area: CGFloat, line: String)] = []
        var sample: [String] = []
        func walk(_ view: NSView, depth: Int) {
            let cls = String(describing: type(of: view))
            // 只数"落在这一列里"的视图总数：SwiftUI 的文字不是 NSTextField（本机实测
            // `详情列文字视图=0` 而有 24 行墨），所以"有没有东西"只能看子视图数量与 hosting 层数。
            if let box = Self.topDownRect(of: view, in: host), box.rect.intersects(rect) { inside += 1 }
            let isText = view is NSTextField
            let isImage = view is NSImageView
            if cls.contains("Hosting") { hosts += 1 }
            if isText || isImage {
                if isText { texts += 1 } else { images += 1 }
            }
            // R121：样本不再只收文字/图像 —— R119 的 CI 证明"只数数量"不够。
            // 那一跑里详情列有 7 个视图、整带最大偏离 0，光知道"有 7 个"分不开
            // "它们画在帧外"与"它们在帧内但一个像素都没动"。所以现在把矩形、
            // 可见性与 layer 不透明度一起打出来，让下一跑自己说。
            //
            // R121 追改：样本按**面积升序**取前 8，而不是按遍历顺序。第一次本地跑出来
            // 走的是遍历序，8 条全是 `NSHostingView / AppKitPlatformViewHost / NSSplitView /
            // _NSSplitViewItemViewWrapper` 这类铺满整窗的容器（每条都是 720x600），
            // 也就是说我加的证人根本没说该说的话 —— 我要看的是叶子，容器在
            // `列内视图数` 那个数里已经记过账了（U-405：加了仪表不等于读到了仪表）。
            if let top = Self.topDownRect(of: view, in: host), top.rect.intersects(rect) {
                let r = top.rect
                raw.append((area: r.width * r.height,
                            line: "\(cls)[\(Int(r.minX)),\(Int(r.minY)) \(Int(r.width))x\(Int(r.height))]"
                                  + (view.isHidden ? " 隐藏" : "")
                                  + ((view.layer?.opacity ?? 1.0) < 0.999
                                     ? String(format: " 层不透明度=%.2f", view.layer!.opacity) : "")))
            }
            if depth < 18 { view.subviews.forEach { walk($0, depth: depth + 1) } }
        }
        walk(host, depth: 0)
        sample = raw.sorted { $0.area < $1.area }.prefix(8).map { $0.line }
        return (texts, images, hosts, inside, sample)
    }


    /// 侧栏**图标列**（pt）。这里只留两块**对账用**的列级矩形，判据一律走 `sidebarRowRects`：
    /// `settingsSidebarIconColumnWide` 就是 R114 撤 167 时手量的那块（x 8..40），
    /// `settingsSidebarIconColumn` 是把上面注释里「图标列在 12–34」这句话照抄成矩形。
    /// **两条注释的 y 都是 96..250，而本轮实测行带是 y 60..252** ⇒ 老的列级矩形少盖第一行
    /// （BACKLOG 169：`settingsSidebarTextColumn` 与它喂的 `TEXT_SIDE`／盲区名单都受影响）。
    static let settingsSidebarIconColumn = CGRect(x: 12, y: 60, width: 22, height: 192)
    static let settingsSidebarIconColumnWide = CGRect(x: 8, y: 60, width: 32, height: 192)

    /// 侧栏**每一行**的矩形（顶向下 pt），从已布局的视图树里拿，不是把列高除出行数。
    ///
    /// 为什么不许除：除出来的行带是我对布局的假设，而假设错了它照样报数。
    /// 本轮实测就是反例 —— 台账里那条 y 96..250 的"侧栏列"根本没盖住第一行。
    /// `_FocusRingView` 是侧栏每个可聚焦按钮行都带一份的焦点环容器：
    /// 它与 `SettingsCategory.allCases` 数量不符 ⇒ 红的是这条尺或产品的行数，两种都得去看。
    static func sidebarRowRects(in host: NSView, column: CGRect) -> [CGRect] {
        var found: [CGRect] = []
        func walk(_ view: NSView, depth: Int) {
            if String(describing: type(of: view)).contains("FocusRingView"),
               let top = Self.topDownRect(of: view, in: host) {
                let r = top.rect
                if r.minX < column.maxX, r.maxX > column.minX, r.height > 8, r.height < 60, r.width > 40 {
                    found.append(r)
                }
            }
            if depth < 18 { view.subviews.forEach { walk($0, depth: depth + 1) } }
        }
        walk(host, depth: 0)
        var kept: [CGRect] = []
        for r in found.sorted(by: { $0.minY < $1.minY }) {
            if kept.contains(where: { abs($0.minY - r.minY) < 2 && abs($0.height - r.height) < 2 }) { continue }
            kept.append(r)
        }
        return kept
    }

    /// 带子的**纵向范围换成详情列自己**（R119 / BACKLOG 150）。
    ///
    /// x 仍然来自台账（`cardprobeBands` 里那条 170..720），因为参照条要靠它定位；
    /// y 改成这一列的完整高度 —— 列在树里就是"内容能出现的地方"，
    /// 它在两台机器上各自是多少，由那台机器的树说，不由我记的常数说。
    /// 没有详情列（臂 0 / 臂 1）时原样返回。
    static func bandYFromColumn(_ band: CGRect,
                                _ columns: [(name: String, rect: CGRect)]) -> CGRect {
        guard let detail = columns.first(where: { $0.name.contains("详情") }) else { return band }
        return CGRect(x: band.minX, y: detail.rect.minY,
                      width: band.width, height: detail.rect.height)
    }

    /// R121 / BACKLOG 150：参照臂"带子里没有墨"这一件事的**四种**结局。
    ///
    /// 为什么非要从像素里抽出这个函数：R107 把这条规则写在注释里（"整窗最大偏离 ≥ 60 而
    /// 带子只有个位数 ⇒ 内容画在带子之外 ⇒ 改带子"），**但它从来没被当成判据跑过**，
    /// 于是 R119 我在没有它的情况下给 150 认了一个成因（"帧太矮把内容裁掉了"），
    /// 而 R119 自己的 CI 把它证伪了：帧已经 720×600、整窗墨行 70、带子仍然 0 墨。
    /// 那条注释规则在那一跑上也会给出错的答案 —— 它拿**整窗**当"内容在不在"的证人，
    /// 而整窗里那 70 行墨全在**侧栏**那一列（`CARD_PROBE_COLUMNS` 列0 墨行=70，列1/列2=0），
    /// 详情那一列从头到尾是平涂。按整窗判就会说"改带子"，可带子已经铺满了详情列，
    /// 没有任何带子能改到看得见一列不存在的东西。
    /// ⇒ 证人换成**被告那一列自己**，三种 0 墨因此分得开：带子放错 / 这一列没画 / 整页没拍出来。
    enum CardprobeArmVerdict: Equatable {
        case judged          // 带子看得见内容：`材质=有/无` 是有对象的读数
        case bandMisplaced   // 会红：这一列有墨而带子没有 ⇒ 是我框错了，不是容器没画
        case regionUnpainted // 不可判（有名字）：整帧有墨、被告那一列 0 墨 ⇒ 这台机器画不出这一列
        case pageUnrendered  // 不可判（有名字）：整帧 0 墨 ⇒ 这台机器拍不出这一页（BACKLOG 43）
    }

    static func cardprobeArmVerdict(pageInkRows: Int, regionInkRows: Int, bandInkRows: Int)
        -> CardprobeArmVerdict {
        if bandInkRows > 0 { return .judged }
        if pageInkRows == 0 { return .pageUnrendered }
        if regionInkRows == 0 { return .regionUnpainted }
        return .bandMisplaced
    }

    /// 结论要打成中文读数，而且**四种结局必须各有一个词**：
    /// 上一版只有"会红"与"没红"两格，于是"我框错了"与"这台机器画不出这一列"共用同一格，
    /// 150 才会被"帧太矮"这种成因名糊过去（U-405）。
    static func verdictText(_ verdict: CardprobeArmVerdict) -> String {
        switch verdict {
        case .judged: return "可判(带子里有内容)"
        case .bandMisplaced: return "红(列里有墨而带子没有=框错)"
        case .regionUnpainted: return "不可判(整帧有墨而详情列0墨=这台机器没画这一列)"
        case .pageUnrendered: return "不可判(整帧0墨=这台机器拍不出这一页)"
        }
    }

    /// 侧栏**文字列**的行带：x 用台账写的那条（40..142），y 用树给的每一行。
    ///
    /// 为什么不许整列写死一个绝对 y：R116 那条对账守卫在 runner 上第一次跑就红，
    /// 读数是 `台账=60..252 树给=342..534 上界差=282.0pt` —— **同一份代码、同一个 720×540 帧，
    /// 整列在 runner 上往下挪了 282pt**（行高仍是 6×32=192pt，一点没变）。
    /// 也就是说"这一列在哪"是机器相关的，而"这一列有多高、有几行"不是。
    /// ⇒ 判据一律吃这里的行带；台账那条绝对矩形只留作 x 带的来源与本机的对照物。
    static func sidebarTextBands(in host: NSView) -> [CGRect] {
        let x = settingsSidebarTextColumn.minX
        let w = settingsSidebarTextColumn.width
        return sidebarRowRects(in: host, column: settingsSidebarIconColumn)
            .map { CGRect(x: x, y: $0.minY, width: w, height: $0.height) }
    }

    /// 带内候选（尺瞎了的时候自报家门，不靠我再搭一遍 /tmp 的复刻体）。
    static func sidebarIconCandidates(in host: NSView, column: CGRect,
                                      sizeCap: CGFloat = 60) -> [(name: String, rect: CGRect)] {
        var out: [(String, CGRect)] = []
        func walk(_ view: NSView, depth: Int) {
            if let top = Self.topDownRect(of: view, in: host),
               top.rect.intersects(column), top.rect.width < sizeCap, top.rect.height < sizeCap {
                out.append((String(describing: type(of: view)), top.rect))
            }
            if depth < 18 { view.subviews.forEach { walk($0, depth: depth + 1) } }
        }
        walk(host, depth: 0)
        return out.sorted { $0.1.height * $0.1.width < $1.1.height * $1.1.width }
    }

    /// 一行里**图标那半边**（x 到文字列左界为止）的墨横向铺在哪几列、两侧各多少偏离像素。
    ///
    /// 横向范围不写死「12–34」：那条评论本身没被量过，再拿它当尺就是把形容词换成数字
    /// 而已。由帧自己报出墨的左右界，才能区分"图标画在别处"与"图标根本没墨"。
    static func iconInkSpan(bytes: UnsafePointer<UInt8>, width: Int, height: Int, bytesPerRow: Int,
                            row: CGRect, textLeft: CGFloat, scale: Double, gate: Int = 16)
        -> (lo: Int, hi: Int, brighter: Int, darker: Int) {
        let x0 = max(0, Int(row.minX * scale))
        // x 上界内缩 2pt：贴着文字列左界的那 1~2 列是**标签字的抗锯齿**，不是图标。
        // 实测过：不外缩时 `command` 那行在亮档读到 x=39..39 / 10 个偏离像素 ⇒ 判成"有墨"，
        // 而那 10 个像素根本不是图标。把边界当墨，就是把尺的接缝当产品。
        let x1 = min(width, Int(max(row.minX, min(row.maxX, textLeft - 2)) * scale))
        let y0 = max(0, Int(row.minY * scale)), y1 = min(height, Int(row.maxY * scale))
        guard x1 > x0, y1 > y0 else { return (-1, -1, 0, 0) }
        func luma(_ x: Int, _ y: Int) -> Int {
            let o = y * bytesPerRow + x * 4
            return Int((0.2126 * Double(bytes[o]) + 0.7152 * Double(bytes[o + 1])
                        + 0.0722 * Double(bytes[o + 2])).rounded())
        }
        var histogram: [Int: Int] = [:]
        for y in y0..<y1 { for x in x0..<x1 { histogram[luma(x, y) / 8, default: 0] += 1 } }
        let background = histogram.max { $0.value < $1.value }.map { $0.key * 8 + 4 } ?? 0
        var lo = -1, hi = -1, brighter = 0, darker = 0
        for x in x0..<x1 {
            var ink = 0
            for y in y0..<y1 {
                let signed = luma(x, y) - background
                if signed > gate { brighter += 1; ink += 1 }
                else if signed < -gate { darker += 1; ink += 1 }
            }
            if ink > 0 { if lo < 0 { lo = x }; hi = x }
        }
        // 报 pt 不报像素号：把"这把尺量在多少 pt 上"藏在像素里，下一个人就会再犯 R29d 的 pt/px 错。
        return (lo < 0 ? -1 : Int(Double(lo) / scale), hi < 0 ? -1 : Int(Double(hi) / scale),
                brighter, darker)
    }


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
    /// R102 / BACKLOG 150 的容器梯子：每一臂的扫描带（pt）。
    /// 臂 0 与臂 1 的卡片都从 `.padding(24)` 起。
    ///
    /// **臂 2 的带子左沿在 R103 从 150 挪到 170**（本机逐张看帧量出来的，见 Round 103 §4）：
    /// 侧栏那一列占 148pt，而列里的东西并不止到 148 —— 选中那颗蓝胶囊实测画到 141pt、
    /// 列的右缘在 145pt 附近 ⇒ 旧值 150 只留了 **2pt** 余量。
    /// 这一格坏起来很难看：证人问的是"这一臂的带子里有没有**卡片的内容**"，
    /// 而 2pt 的余量在另一台机器上（1x、不同抖动、不同字体栅格）可能整条被侧栏占掉
    /// ⇒ 侧栏的字会给"卡片没有材质"作证，那正是 D-167 装证人要防的那种假答案。
    /// 新值 170 的两侧都有量：离侧栏右缘 25pt（145→170），离卡片左沿 2.5pt（170→172.5，
    /// 卡片左沿与产品卡片的 172.0pt 同一档）⇒ 带子仍然盖住整张卡片，`firstSpanStart` 量到的
    /// 还是真的那一条直边（本机复测：臂 2 的 `内缩` 亮 5.0 / 暗 5.5 与挪之前逐字相同）。
    /// 这三条**必须与夹具声明同步维护**：带子没盖住卡片 = 报"读不到卡片"，而那不是容器的结论。
    static let cardprobeBands: [String: CGRect] = [
        "cardprobe-groupbox-default": CGRect(x: 24, y: 24, width: 672, height: 100),
        "cardprobe-scroll-groupbox": CGRect(x: 24, y: 24, width: 672, height: 100),
        // 臂 2 的带子跟着夹具一起放宽到 300pt 高（R107）：内容盒 258pt 不再被裁，
        // 带子覆盖"整列详情"而不是"某一条窗口位置"，于是它盖不盖得住卡片**不再取决于机器装饰高度**。
        "cardprobe-split-groupbox": CGRect(x: 170, y: 24, width: 550, height: 260),
    ]

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

    /// R98 / BACKLOG 143：把"扫某一个文件"换成"扫 Views 目录下的每一个文件"。
    ///
    /// 存在的理由：按文件划的守卫追不上按组件长的东西 —— 卡片可以长在任何一个文件里，
    /// 而名单要有人记得改。目录枚举没有这个洞：新增文件自动进名单。
    /// 返回 `(文件名, 源码)`，按文件名排序（报表要能在两次运行之间逐字对齐）。
    private func productViewSources() throws -> [(name: String, text: String)] {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let dir = candidate.appendingPathComponent("Sources/ClipboardHistoryApp/Views", isDirectory: true)
            let urls = (try? FileManager.default.contentsOfDirectory(at: dir,
                                                                    includingPropertiesForKeys: nil)) ?? []
            let swifts = urls.filter { $0.pathExtension == "swift" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
            if !swifts.isEmpty {
                return swifts.compactMap { url in
                    guard let text = try? String(contentsOf: url, encoding: .utf8) else { return nil }
                    return (url.lastPathComponent, text)
                }
            }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "UICaptureHarness", code: 3,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/Views 目录"])
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
        var sidebarInkTotal = 0
        var attempted = 0
        // 盲区名单的键要用**量出来**的倍率，不是 `mainScreen` 的：CI 那台没有主屏，
        // 而这一跑真正扫的就是这些帧（D-183①：证人必须与被判的东西同源）。
        var measuredScaleMax: Double = 0
        for fixture in fixtures(appearance: .darkAqua) where fixture.name.hasPrefix("settings-") {
            let file = scratch.appendingPathComponent("\(fixture.name).png")
            var vibrant: String?
            var rosterRowBands: [CGRect] = []
            // R30：拍之前先记下"这一列到底在哪个外观里解析颜色" —— 这是下面那条
            // **前提断言**的对象（伪影的解释，不是伪影本身）。
            _ = try render(fixture, appearance: .darkAqua, to: file) { host in
                vibrant = Self.vibrantAppearanceCovering(host, column: Self.settingsSidebarTextColumn)
                rosterRowBands = Self.sidebarTextBands(in: host)
            }
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                return XCTFail("\(fixture.name)：读不回刚拍的帧")
            }
            let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
            measuredScaleMax = max(measuredScaleMax, scale)
            // 先量内容区：它只回答"这台机器拍不拍得出这一页"，不回答产品好不好。
            let content = Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow,
                                             rect: Self.settingsContentPane, scale: scale)
            contentInkTotal += content.brighter + content.darker
            // 逐行求和（行带来自树），不再吃那条绝对 y：runner 上整列挪了 282pt，
            // 绝对矩形在那里根本盖不住字（R118 / 见 `sidebarTextBands` 的说明）。
            var brighter = 0, darker = 0
            for band in rosterRowBands {
                let one = Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow, rect: band, scale: scale)
                brighter += one.brighter
                darker += one.darker
            }
            let counts = (brighter: brighter, darker: darker)
            emit("TEXT_SIDE_BANDS \(fixture.name) dark 行带数=\(rosterRowBands.count)"
                 + " 首行y=\(rosterRowBands.isEmpty ? "-" : String(format: "%.0f", rosterRowBands[0].minY))")
            // runner 上这一页整块画不出来（BACKLOG 43）⇒ 逐条记 NOT-RUN，最后由
            // `contentInkTotal` 那条决定"是机器拍不出这一页"还是"我这把尺没压住字"。
            attempted += 1
            guard counts.brighter + counts.darker > 0 else {
                emit("TEXT_SIDE_NOT_RUN \(fixture.name) dark 侧栏列读到 0 个偏离像素"
                      + "（同帧内容区读到 \(content.brighter + content.darker) 个）")
                continue
            }
            judged += 1
            sidebarInkTotal += counts.brighter + counts.darker
            let inverted = Self.inkFailureIsInverted(brighter: counts.brighter, darker: counts.darker,
                                                     darkAppearance: true)
            if inverted { wrongSide.insert(fixture.name) }
            if vibrant != nil { vibrantColumns.insert(fixture.name) }
            emit("TEXT_SIDE \(fixture.name) dark 亮侧=\(counts.brighter) 暗侧=\(counts.darker)"
                  + " 侧栏子树外观=" + (vibrant ?? "非 vibrant")
                  + " ⇒ " + (inverted ? "侧栏文字落在背景错误一侧（不可见）" : "墨在期望侧"))
        }
        // 闸门吃**被量物体自己那一条带**（D-166）。runner 的实测把旧写法的后果演了一遍：
        // 侧栏那一列在那台机器上读到 `亮侧=1503 暗侧=0`（有墨、且在期望侧），
        // 而内容区读到 0 墨 ⇒ 旧的 `contentInkTotal == 0` 让整条守卫 skip，
        // 于是"暗档盲区名单在这台机器上不成立"这条真信息被 skip 掩盖（BACKLOG 171）。
        if sidebarInkTotal == 0 {
            emit("TEXT_SIDE_NOT_RUN all（侧栏列在 \(attempted) 个夹具上读到 0 个偏离像素；"
                 + "同批内容区偏离=\(contentInkTotal)）")
            throw XCTSkip("TEXT_SIDE_NOT_RUN：侧栏那一列本身没有墨 ⇒ 这条守卫记为未运行，"
                          + "不算通过也不算盲区（内容区那个数只用来分'这台机器拍不出这一页'与'尺没压住字'）")
        }
        // R124 / BACKLOG 171：名单**按机器分键**之后，"这台机器的位没登记"是一种独立的、
        // 必须红的结局 —— 如果不在表里能安静通过，任何一台新机器跑这条判据都会白拿一个绿，
        // 而 runner 那一台恰恰是这轮才发现"它的位从来没被登记过"（R120 那朵 `gone` 红的真身）。
        let rosterKey = Self.sidebarRosterMachineKey(scale: measuredScaleMax)
        let rosterVerdict = Self.sidebarRosterVerdict(
            registered: Self.darkSidebarTextBlindSpotsByMachine[rosterKey], measured: wrongSide)
        emit("TEXT_SIDE_ROSTER_KEY \(rosterKey) 本机登记=\(Self.darkSidebarTextBlindSpotsByMachine[rosterKey]?.count ?? -1)"
             + " 实测反侧=\(wrongSide.count) 判了 \(judged)/\(attempted) 个夹具"
             + " ⇒ \(Self.rosterVerdictText(rosterVerdict))")
        switch rosterVerdict {
        case .unkeyed:
            XCTFail("TEXT_SIDE_ROSTER_UNKEYED \(rosterKey)：这台机器的盲区位没登记"
                    + "（实测反侧 \(wrongSide.count) 张：\(wrongSide.sorted().prefix(4))…）"
                    + " ⇒ 不许为了让它绿就复制另一台那一行：先去看那张帧（这台机器上暗档侧栏到底看不看得见），"
                    + "再把这一台自己的集合写进 `darkSidebarTextBlindSpotsByMachine`（空集也是一条声明）。"
                    + "R124 / BACKLOG 171。")
        case .extra(let extra):
            XCTFail("TEXT_SIDE_ROSTER_EXTRA \(rosterKey)：这些帧的暗档侧栏文字**第一次**落在错误一侧："
                    + "\(extra.sorted()) ⇒ 又多了一处离屏帧里不可见的文字。"
                    + "先定位是谁、为什么，再决定加名单还是修那一层；不许为了绿把断言放宽")
        case .gone(let gone):
            XCTFail("TEXT_SIDE_ROSTER_GONE \(rosterKey)：这些帧的暗档侧栏文字现在落在期望侧了：\(gone.sorted())"
                    + " ⇒ 两种可能：①机制被修好了（BACKLOG 45 可以关，但必须先肉眼复审那张帧，别只缩名单）；"
                    + "②尺瞎了（框没压住字 / 背景取错位置 —— R29d 刚犯过后者）。两种都要真的去看那张帧")
        case .clean:
            break
        }
        XCTAssertGreaterThan(judged, 0,
                             "侧栏列总共读到 \(sidebarInkTotal) 个偏离像素 ⇒ 这台机器**拍得出**这一列，"
                             + "可一条都没判 ⇒ 是**尺没压住字**，不是环境问题。"
                             + "回去核对 `sidebarTextBands` 的 x 带与单位（R29d 的 pt/px 教训）")
        emit("TEXT_SIDE_CAPABILITY 侧栏偏离=\(sidebarInkTotal) 内容区偏离=\(contentInkTotal)"
             + " 判了 \(judged)/\(attempted) 个夹具 ⇒ 闸门与判据同源（D-166）")
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

    /// 列级矩形与视图树行带的**对账**（R116 / BACKLOG 169 的钉子）。
    ///
    /// 为什么单独一条：`TEXT_SIDE` 那条守卫钉的是 vibrant 前提，行带那条钉的是数量，
    /// 于是"矩形悄悄过期"这一族没有任何东西会红（U-383 的原价）。
    /// 这条把 `settingsSidebarTextColumn` 的 y 带钉在树给的行带上：
    /// 上下界各差 1pt 以内、行数 ≥ 2（否则它就是在拿一块空带子自证）。
    func testSettingsSidebarRosterRectCoversEveryRow() throws {
        guard let fixture = fixtures(appearance: .darkAqua).first(where: { $0.name == "settings-general" }) else {
            return XCTFail("找不到 settings-general ⇒ 这条对账没有对象")
        }
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r116-roster-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var rows: [CGRect] = []
        _ = try render(fixture, appearance: .darkAqua,
                       to: scratch.appendingPathComponent("settings-general.png")) { host in
            rows = Self.sidebarRowRects(in: host, column: Self.settingsSidebarIconColumn)
        }
        let rect = Self.settingsSidebarTextColumn
        XCTAssertGreaterThanOrEqual(rows.count, 2, "树只给出 \(rows.count) 个行带 ⇒ 对账没有意义，先看容器名")
        let top = rows.map { $0.minY }.min() ?? 0
        let bottom = rows.map { $0.maxY }.max() ?? 0
        emit("SIDEBAR_ROSTER_RECT 台账=\(Int(rect.minY))..\(Int(rect.maxY))"
             + " 树给=\(Int(top))..\(Int(bottom)) 行数=\(rows.count)"
             + " 上界差=\(String(format: "%.1f", abs(rect.minY - top)))pt"
             + " 下界差=\(String(format: "%.1f", abs(rect.maxY - bottom)))pt")
        // **绝对 y 不判**：runner 实测整列往下挪 282pt（行高与行数一点没变），
        // 拿本机的绝对坐标当契约，这条守卫在另一台机器上永远红 —— 那是尺的机器依赖，不是产品的错。
        // 判的是"这块尺盖住的**范围**对不对"：高度、行数、以及 x 带。偏移本身打出来给人看。
        XCTAssertLessThanOrEqual(abs(rect.height - (bottom - top)), 1.0,
                                 "台账矩形高 \(rect.height)pt，而树给的六行合起来是 \(String(format: "%.1f", bottom - top))pt ⇒ "
                                 + "尺盖不住整列（要么少一行，要么行高变了）。改矩形，别改这条断言。")
        emit("SIDEBAR_ROSTER_OFFSET 台账起点=\(Int(rect.minY)) 树起点=\(Int(top))"
             + " 偏移=\(String(format: "%.1f", top - rect.minY))pt（绝对 y 是机器相关的，只报不判）")
    }

    /// 侧栏图标**逐行**的墨落在哪一侧（R115：把 167 撤回用的那套量法搬进仓库这颗尺真身）。
    ///
    /// **本轮只报数、不判产品** —— 167 的第一步就是这么写的，而 D-181 规定
    /// 单次读数不配给产品定罪：地板要等这份读数在本机与 runner 各落一次再定。
    /// 会红的全是**尺自己**：
    /// ① 视图树数出来的行数与产品那个枚举不符（带子/尺寸闸门把行滤掉了，或侧栏行数真变了）；
    /// ② 两档判的夹具数不等（不对称不能冒充覆盖）；
    /// ③ 内容区拍得出来、可所有图标行加起来一行墨都没有（尺瞎了，环境问题走 skip 不走这里）。
    ///
    /// 为什么必须逐行：R114 只有列级聚合（暗侧 3966 / 亮侧 1391），而列级会把
    /// "只有选中行有墨、其余五行没墨"抹平成"整列都在期望侧"。`SettingsSidebarRow`
    /// 的注释里正写着未选中四行图标实测墨水 0.0000（离屏管线解析语义色），
    /// 所以逐行是那次撤回唯一能被真正检验的形状。
    func testSettingsSidebarIconsAreMeasuredRowByRow() throws {
        let expectedRows = SettingsCategory.allCases.count
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r115-icon-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        var contentInkTotal = 0
        var pairs: [String: Int] = [:]
        var inked: [String: Int] = [:]
        var blank: [String: Int] = [:]
        var inverted: [String: Int] = [:]
        var rowsAboveRosterMinY = 0
        var rowsTotal = 0
        // 每枚符号在各档各有几行判成什么：行号与符号的对应见下面 `categories[index]` 那段说明。
        var bySymbol: [String: [String: Int]] = [:]
        let categories = SettingsCategory.allCases

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .aqua ? "light" : "dark"
            let darkSide = tag == "dark"
            for fixture in fixtures(appearance: appearance) where fixture.name.hasPrefix("settings-") {
                let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
                var rows: [CGRect] = []
                var smalls: [(name: String, rect: CGRect)] = []
                _ = try render(fixture, appearance: appearance, to: file) { host in
                    rows = Self.sidebarRowRects(in: host, column: Self.settingsSidebarIconColumn)
                    smalls = Self.sidebarIconCandidates(in: host, column: Self.settingsSidebarIconColumn)
                }
                pairs[tag, default: 0] += 1
                XCTAssertEqual(rows.count, expectedRows,
                               "\(fixture.name) \(tag)：视图树在图标带 x \(Int(Self.settingsSidebarIconColumn.minX))..\(Int(Self.settingsSidebarIconColumn.maxX)) 里数到 \(rows.count) 个行容器，而产品侧栏有 \(expectedRows) 行（`SettingsCategory.allCases`）⇒ 要么焦点环容器不叫这个名字了、要么侧栏行数变了。先看下面那行候选名单再动这条尺。")
                if rows.count != expectedRows {
                    emit("SIDEBAR_ICON_CANDIDATES \(fixture.name) \(tag) 带内小视图共\(smalls.count) 个："
                         + smalls.prefix(10).map { "\($0.name) [\(Int($0.rect.minX)),\(Int($0.rect.minY)) "
                             + "\(Int($0.rect.width))x\(Int($0.rect.height))]" }.joined(separator: " ; "))

                }
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("\(fixture.name)：读不回刚拍的帧")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                func side(_ rect: CGRect) -> (brighter: Int, darker: Int) {
                    Self.inkSideCounts(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                       bytesPerRow: rep.bytesPerRow, rect: rect, scale: scale)
                }
                let content = side(Self.settingsContentPane)
                contentInkTotal += content.brighter + content.darker

                for (index, row) in rows.enumerated() {
                    rowsTotal += 1
                    if row.minY < Self.settingsSidebarTextColumn.minY { rowsAboveRosterMinY += 1 }
                    let span = Self.iconInkSpan(bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                                                bytesPerRow: rep.bytesPerRow, row: row,
                                                textLeft: Self.settingsSidebarTextColumn.minX, scale: scale)
                    let total = span.brighter + span.darker
                    let verdict: String
                    if total == 0 {
                        blank[tag, default: 0] += 1
                        verdict = "无墨"
                    } else {
                        inked[tag, default: 0] += 1
                        if Self.inkFailureIsInverted(brighter: span.brighter, darker: span.darker,
                                                     darkAppearance: darkSide) {
                            inverted[tag, default: 0] += 1
                            verdict = "反侧"
                        } else {
                            verdict = "期望侧"
                        }
                    }
                    // 行号→产品那条枚举的顺序。这不是假设，是被药丸签名核对过的实测：
                    // `settings-general` 的混合两侧那一行落在 row=1（=`general`）、
                    // `settings-privacy` 落在 row=2、`settings-data` 落在 row=4
                    // —— 选中行的药丸底色让它的图标带同时读出亮侧与暗侧偏离，所以签名可辨。
                    let category = categories[index]
                    bySymbol[category.icon, default: [:]][tag + " " + verdict, default: 0] += 1
                    emit("SIDEBAR_ICON_ROW \(fixture.name) \(tag) row=\(index)"
                         + " 标签=\(category.title) 符号=\(category.icon)"
                         + " 行带y=\(Int(row.minY))..\(Int(row.maxY))"
                         + " 图标墨x=\(span.lo)..\(span.hi) 亮侧=\(span.brighter) 暗侧=\(span.darker)"
                         + " ⇒ \(verdict)")
                }
                // 与两份列级老矩形对账：R114 撤 167 用的就是 wide 那块（x 8..40）。
                let narrow = side(Self.settingsSidebarIconColumn)
                let wide = side(Self.settingsSidebarIconColumnWide)
                let text = side(Self.settingsSidebarTextColumn)
                emit("SIDEBAR_ICON_BAND \(fixture.name) \(tag)"
                     + " 逐行合计 亮侧=\(inked[tag] ?? 0) 无墨=\(blank[tag] ?? 0)"
                     + " | 窄 12..34×96..250 亮侧=\(narrow.brighter) 暗侧=\(narrow.darker)"
                     + " | 宽 8..40×96..250 亮侧=\(wide.brighter) 暗侧=\(wide.darker)"
                     + " | 文字列 40..142×96..250 亮侧=\(text.brighter) 暗侧=\(text.darker)"
                     + " | 内容区偏离=\(content.brighter + content.darker)")
            }
        }

        // 能力位必须写进这两行本身：runner 上整页是平涂底色（BACKLOG 43），
        // 那时"每行都有墨、零反侧"是噪声对着称的产物，不是健康证明。
        // 只把 skip 打在后面一行 ⇒ 单 grep COVERAGE 的人会拿到一张假的好消息（U-391）。
        let capability = contentInkTotal == 0 ? "能力=不可判(内容区 0 墨)" : "能力=可判"
        emit("SIDEBAR_ICON_COVERAGE \(capability) 产品行数=\(expectedRows) 行带总数=\(rowsTotal)"
             + " | light 有墨行=\(inked["light"] ?? 0) 无墨行=\(blank["light"] ?? 0) 反侧行=\(inverted["light"] ?? 0)"
             + " | dark 有墨行=\(inked["dark"] ?? 0) 无墨行=\(blank["dark"] ?? 0) 反侧行=\(inverted["dark"] ?? 0)"
             + "（反侧那一格 R122 起会红，见 SIDEBAR_ICON_INVERTED；地板仍等两台机器各落一次再定）")
        // R122：`反侧行` 从"只报数"升成会红。来历不是审美判断，是本轮的一次产品改动把它量成了数：
        // `SettingsView` 侧栏那六枚符号里 `wand.and.stars`（推荐）与 `chart.bar`（统计）是仅有的两枚多色符号，
        // 在 `.hierarchical` 下它们带自己的调色板 ⇒ 暗档 22 行图标墨落在**背景那一边**（黑底黑图标）。
        // 换成 `.monochrome` 之后 dark 反侧 22→0、期望 56→78。这一格钉的就是"别悄悄换回去"。
        // 闸门与判据同源（D-166）：只有这一档读得到墨才判反侧 —— 那台机器整档 0 墨时
        // "反侧=0" 是噪声对称，不是健康证明（R115 的 COVERAGE 说的就是这件事）。
        if capability == "能力=可判" {
            for tag in ["light", "dark"] {
                XCTAssertEqual(inverted[tag] ?? 0, 0,
                    "SIDEBAR_ICON_INVERTED \(tag)：有 \(inverted[tag] ?? 0) 行侧栏图标的墨落在**背景那一边**"
                        + "（同档期望侧=\(inked[tag] ?? 0) 无墨=\(blank[tag] ?? 0)，行带来自视图树，"
                        + "逐行见 SIDEBAR_ICON_ROW，按符号见 SIDEBAR_ICON_BY_SYMBOL）"
                        + " ⇒ 那是「看不见」级别的深浅色缺陷，不是留白风格。"
                        + "先查 `SettingsSidebarRow` 的 `.symbolRenderingMode` / `.foregroundStyle`，"
                        + "不要改这条断言的 0，也不要用固定色去讨好它（那会在真机上把颜色写死）。")
            }
            // 另一侧的账也要有名字：亮档有 65/78 行图标**一个墨都没画**，而这不是本轮改出来的
            // （改之前是 43/78）。它是离屏通道对 `.primary` 的解析盲区（审计第二轮 1.9 的原始发现），
            // 与"反侧"是两种病 —— 反侧会红，无墨登记。写成会红就会诱使下一轮拿固定色去填它。
            emit("SIDEBAR_ICON_BLIND_SPOT light 无墨行=\(blank["light"] ?? 0)"
                 + " 有墨行=\(inked["light"] ?? 0) 反侧行=\(inverted["light"] ?? 0)"
                 + " | dark 无墨行=\(blank["dark"] ?? 0) 有墨行=\(inked["dark"] ?? 0)"
                 + "（亮档无墨=通道对语义色的解析盲区，R122 实测：`.hierarchical`→`.monochrome`"
                 + " 让 dark 反侧 22→0 同时让 light 期望 35→13 ⇒ 两档要的是相反的解析，"
                 + "这一格只登记不判产品；真机那一半见人工批次 86.1）")
        }
        for symbol in bySymbol.keys.sorted() {
            let cell = bySymbol[symbol]!
            emit("SIDEBAR_ICON_BY_SYMBOL \(capability) 符号=\(symbol)"
                 + " | light 期望=\(cell["light 期望侧"] ?? 0) 反侧=\(cell["light 反侧"] ?? 0) 无墨=\(cell["light 无墨"] ?? 0)"
                 + " | dark 期望=\(cell["dark 期望侧"] ?? 0) 反侧=\(cell["dark 反侧"] ?? 0) 无墨=\(cell["dark 无墨"] ?? 0)"
                 + "（每档最多 \(expectedRows) 行 × \(pairs["light"] ?? 0) 个夹具）")
        }
        emit("SIDEBAR_ICON_ROSTER_DRIFT \(capability) 行带起点比台账矩形（y \(Int(Self.settingsSidebarTextColumn.minY))）更早的行数=\(rowsAboveRosterMinY)/\(rowsTotal)"
             + " ⇒ 老的列级矩形（含 `settingsSidebarTextColumn` 与它喂的 TEXT_SIDE／盲区名单）盖不全这些行，BACKLOG 169")
        XCTAssertEqual(pairs["light"], pairs["dark"],
                       "亮档判了 \(pairs["light"] ?? 0) 个设置夹具、暗档判了 \(pairs["dark"] ?? 0) 个 ⇒ 同一份名单该两边等量，"
                       + "不等就是夹具集合在一档里被跳过了（别让这种不对称冒充成覆盖）")

        if contentInkTotal == 0 {
            emit("SIDEBAR_ICON_NOT_RUN all（这一档图标判据没跑：内容区读到 0 个偏离像素。"
                 + "R121 的 `CARD_PROBE_COLUMNS` 已经把这台的盲区**收窄到详情那一列** —— "
                 + "侧栏列本身有墨，不许再写成「整页拍不出」）")
            throw XCTSkip("SIDEBAR_ICON_NOT_RUN：BACKLOG 43 那一族 —— 这台机器上整页是平涂底色 ⇒ 这条记为未运行")
        }
        XCTAssertGreaterThan((inked["light"] ?? 0) + (inked["dark"] ?? 0), 0,
                             "内容区读到了墨（\(contentInkTotal) 个偏离像素）⇒ 这台机器**拍得出**这一页，"
                             + "可所有图标行加起来读不到一行有墨 ⇒ 是尺没压住字形（带子或尺寸闸门），不是产品没画。"
                             + "回去核对 `sidebarRowRects` 的容器名与 `iconInkSpan` 的 x 上界（R29d 的 pt/px 教训）")
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
        // 「看得见墨却一条都没判」与「这台机器拍不出这一页」必须分开（R96：把判据从一张卡片
        // 扩到每一张之后，`dividers >= 2 ⇒ continue` 那一格给了尺一个**安静的逃法** ——
        // 它看不见线的时候就不再判任何东西，而「不判」在报表上与环境受限长得一模一样。
        // 这一格把那条路堵掉：只要有任何一张卡片读到了墨，就必须至少判成一次。
        var sawInk = false
        // R97：还要区分"这台机器拍不出这一页"与"墨那一档读不到"。
        // 前者会连卡片段都读不出来（没有材质），后者会读出**满带的卡片段却零墨** ——
        // 这两种情况在 `judged == 0` 这一格上长得一模一样，而只有一种该 skip。
        // R97：还要区分"这台机器拍不出这一页"与"墨那一档读不到"。
        // 前者会连卡片段都读不出来（没有材质），后者会读出**满带的卡片段却零墨** ——
        // 这两种情况在 `judged == 0` 这一格上长得一模一样，而只有一种该 skip。
        var sawSegment = false
        // R99：卡片**之上** / 卡片**之下**各有几段墨（逐夹具，两档各一格，键带 tag）。
        // 只收"这一页真读到了墨"的夹具：读不到墨的页两格都会报 0，而那个 0 是仪器的读数
        // 不是产品的事实 —— 让它进名单就等于把"没跑"记成"通过"（BACKLOG 43 那一族）。
        var aboveRoster: [String: Int] = [:]
        var belowRoster: [String: Int] = [:]
        // R100 / BACKLOG 146：**"这台机器看得见卡片材质吗"必须是一个独立的量**。
        // CI 的 macos-15 runner 上 `CARD_BAND` 二十格全是 `填充=-1 卡片段=0 scale=1.0`
        //（页底 light=236 / dark=52）—— 那里的 `GroupBox` 填充落在页面底 ±3 以内，
        // `cardFill` 的第一关（`abs(modal - pageLuma) > 3`）就没有一行过关。
        // 于是 R99 新加的"名单不许为空"在 runner 上红了：那是**仪器没有对象**，不是产品有缺陷。
        // 名单地板必须从**上游那一关**（有没有读到材质）推导，不能从名单自己推导 ——
        // 用名单长度给名单设地板是恒真式，M553（抬段高地板把尺弄瞎）那种刀就咬不住了。
        // 本机：材质 20 格 / 墨 20 格 / 名单 20 格；runner：材质 0 格 ⇒ 地板 0，
        // 但"材质 0"这件事必须以 skip 的形式**响**，不许静默通过。
        var materialCells = 0
        var settingsCells = 0
        // R102 / 读 R101 的 CI（run 38945656003）：「统计有几张卡片」这条断言在 runner 上红了四朵，
        // 红因不是产品，是**那一台读不到被告的材质层**（147 那一族）。它必须先被记成「没有对象」，
        // 再决定响成 skip 还是红 —— 不能像 R101 那样直接断言。
        var statsCells = 0
        var statsDeclined: [String] = []
        // R96 把对象从"那一张卡片"扩到"每一张有分隔线的卡片"：R95 的修法一次动了五张卡片，
        // 而判据只压在 `settings-shortcuts` 上 ⇒ 另外四张改没改对，今天没人看着。
        // "有分隔线"是这条判据的**前提**（没有内侧那一档，就没有可比的数），
        // 所以名单由读数决定而不是我手抄：读到 ≥2 条分隔线的才进来，一条都没读到的记 NOT-RUN。
        for (appearance, tag) in [(NSAppearance.Name.aqua, "light"),
                                  (NSAppearance.Name.darkAqua, "dark")] {
            let candidates = fixtures(appearance: appearance)
                .filter { $0.name.hasPrefix("settings-") && $0.name != "settings-min" }
            guard !candidates.isEmpty else {
                return XCTFail("\(tag)：一张 settings 夹具都没有 ⇒ 这条判据没有对象")
            }
            for fixture in candidates {
            let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
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
            // 扫描带**跟着夹具尺寸走**（R97 / BACKLOG 140 的真病根）：R96 这一格写死 `height: 440`，
            // 而 `settings-privacy-excluded` 那一档窗口高 1040pt ⇒ 卡片"到不了底"是**我的带子**造成的，
            // 尺却把它报成"这一页比窗口高，被切断了"。带子下沿=窗口底之后，
            // "卡片底==带子底"这条读数才真的等价于"卡片被窗口切断"，并且由下面那条恒等式钉住。
            let bandTop: Double = 60
            let band = CGRect(x: 155, y: bandTop, width: 560,
                              height: fixture.size.height - bandTop)
            XCTAssertEqual(band.maxY, fixture.size.height, accuracy: 0.001,
                           "扫描带必须扫到窗口底（这一档窗口高 \(fixture.size.height)pt、带子下沿 "
                           + "\(band.maxY)pt）⇒ 否则『卡片底到带子下沿』那句话没有资格被读成『被窗口切断』")
            let (rows, fill, modals) = Self.cardRowKinds(bytes: base, width: rep.pixelsWide,
                                                 height: rep.pixelsHigh,
                                                 bytesPerRow: rep.bytesPerRow, rect: band,
                                                 scale: scale, pageLuma: pageLuma)
            let inkRows = rows.filter { $0 == .ink }.count
            // **先分段，再逐段判**（R97）：一个扫描带里可以纵向放好几张卡片。
            // 实测 `settings-privacy-excluded` 亮档：「隐私」那张与「数据与保留」那张都在带子里，
            // 中间那一行卡片材质像素=0。R96 把整带当一张卡片 ⇒ "边距"量的是两张的外框。
            let segments = Self.cardSegments(rows: rows, scale: scale)
            // 记在**这里**而不是记在 `inkRows > 0` 之后：这一格要区分的是
            // "有没有读到卡片材质"，与"有没有读到墨"必须各自独立，
            // 否则"满带材质、零墨"会在 `inkRows == 0 ⇒ continue` 那一步先把证人吃掉
            //（M542 第一次跑就是这样：它没红，而是安静地 skip 掉了）。
            if !segments.isEmpty { sawSegment = true }
            settingsCells += 1
            if fill >= 0 { materialCells += 1 }
            // BACKLOG 147 的**成因通道**（R100）：runner 的 PNG 拿不回来，所以"那一台上材质到底是多少"
            // 只能由判据自己打印。只在 `fill < 0` 那一格打 —— 有三种形状，而"填充=-1"只排除了零种：
            // 前三名里有 ≠ 页底且行数够的档 ⇒ 材质在、差 ≤3 被门限挡掉（门限问题）；
            // 前三名全是页底 ⇒ 那台机器没画出材质层（通道问题，这一族要登记成"只有本机能判"）；
            // 这一行压根没出现 ⇒ 判据没走到那一步（先修"为什么没走到"）。
            // 打在这而不是打在 `inkRows == 0 ⇒ continue` 之后：那条出口会把证人先吃掉（M542 那一族）。
            if fill < 0 {
                emit("CARD_FILL_CANDIDATES \(fixture.name) \(tag) "
                     + Self.fillCandidatesLine(pageLuma: pageLuma, modals: modals))
            }
            let fmt = { (values: [Double]) in
                values.map { String(format: "%.1f", $0) }.joined(separator: "/")
            }
            let toPt = { (index: Int) in String(format: "%.1f", band.minY + Double(index) / scale) }
            // R99 / BACKLOG 142：**"卡片顶之上有什么"要用同一颗尺问**。
            // R98 为这件事另写过一把 python 尺，三条自检全不过（卡片顶差 14pt、亮暗互差 7pt、
            // 把热图切成 11 段"卡片"）⇒ 那把尺被隔离成"默认拒绝出表"（U-251）。
            // 这一格不再另起炉灶：直接拿节奏判据已经算好的 `rows`（`.ink` 是它自己判的）
            // 与 `segments.first.top`，数卡片顶之上还有几段墨。
            // 本轮先**只报数**：新尺要先在真产物上跑一遍，看清分布再钉断言（U-166 那一族）。
            if let first = segments.first {
                // **参照点必须换**：`rows` 里那一档 `.ink` 的语义是"卡片材质上有墨"，
                // 而卡片**之上**的那些行本来就长在页面底上 ⇒ 它们永远判不成 `.ink`
                // （第一版就是这么量的，于是十屏全报"上方墨带=0" —— 一个恒为 0 的读数）。
                // 所以这一格用 `columnInk` 以**页面底**为参照重算，门槛与卡片那侧同数
                // （gate 60 / minInk 8），只是零点从 `fill` 换成 `pageLuma`。
                let cardX = Int(band.minX * scale)..<Int(band.maxX * scale)
                // `first.top` 是**带内相对行号**，而 `columnInk` 吃**位图绝对行** ⇒ 必须过
                // `absoluteRows`。这一步不是形式：我第一次把两者直接对接，量出来的窗口是
                // "绝对行 0..<first.top" = 0..45.5pt，而它自认为在量 60..106pt，
                // 于是九屏全报"卡片顶之上没有墨"，而分区标题明明画在 78.5..90.5pt
                // （那张 python 尺这一格反而报对了 —— 它一直在扫绝对行）。
                let aboveWindow = Self.absoluteRows(bandMinY: band.minY, scale: scale,
                                                    count: first.top)
                // **恒等式**（不是同义反复）：窗口下沿换算回 pt 必须等于尺自己报的卡片顶。
                // 两边由两条不同的式子算出来 —— `absoluteRows` 一旦丢掉 `band.minY` 那一档，
                // 左边少 60pt 而右边不变 ⇒ 这一格立刻红（变异臂 M552 就是丢它）。
                XCTAssertEqual(Double(aboveWindow.upperBound) / scale,
                               band.minY + Double(first.top) / scale, accuracy: 0.001,
                               "卡片顶之上的窗口下沿必须正好落在卡片顶（窗口=\(aboveWindow)"
                               + " 而卡片顶=\(toPt(first.top))pt）⇒ 两套坐标系又在打架")
                let aboveVec = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,
                                              xRange: cardX, yRange: aboveWindow,
                                              fill: pageLuma, gate: 60, minInk: 8)
                let above = Self.inkRuns(column: aboveVec, minRunHeight: 4,
                                         mergeGap: Int(8 * scale))
                // 侧栏那一列（卡片 x 范围以左）用**同一颗尺**再量一遍。
                // 为什么要这一格：R98 那把被隔离的 python 尺在"整幅宽度"上找墨，
                // 于是把侧栏的行读成了"每一屏卡片顶之上都有一段分区标题"（十屏读数一模一样
                // ⇒ 那是侧栏，不是标题）。这一格把"卡片范围外的那片墨在侧栏"这句话
                // 变成**读数**，不是我的解释。
                let sidebar = Self.inkRuns(column: Self.columnInk(
                                                bytes: base, bytesPerRow: rep.bytesPerRow,
                                                xRange: 0..<Int(band.minX * scale),
                                                yRange: aboveWindow,
                                                fill: pageLuma, gate: 60, minInk: 8),
                                           minRunHeight: 4, mergeGap: Int(8 * scale))
                // 段的位置必须**和计数出自同一颗尺**：只有"几段"这个数的时候，
                // 我看不到那一段在哪、多高，就没资格说它是标题还是说明段。
                // 段的位置要带**偏移**：`inkRuns` 交回来的是它吃的那条向量的下标，
                // 而卡片之下那条向量是从 `last.bottom + 1` 才起算的。
                // 不带偏移会打印出 91.0..101.0pt 这种"卡片底下 60pt 处有墨"的假位置
                //（本轮第一次跑就是这样，是读数错，不是产品错）。
                let spans = { (runs: [(top: Int, bottom: Int)], offset: Int) in
                    runs.isEmpty ? "无" : runs.map {
                        "\(toPt(offset + $0.top))..\(toPt(offset + $0.bottom + 1))"
                            + "/\($0.bottom - $0.top + 1)px"
                    }.joined(separator: ",")
                }
                emit("CARD_ABOVE \(fixture.name) \(tag) 卡片顶=\(toPt(first.top))"
                     + " 窗口=\(toPt(0))..\(toPt(first.top))"
                     + " 详情区墨带=\(above.count) 详情区段=\(spans(above, 0))"
                     + " 侧栏墨带=\(sidebar.count) 侧栏段=\(spans(sidebar, 0))"
                     + " 详情区墨行=\(aboveVec.filter { $0 }.count) 卡片段数=\(segments.count)")
                // **对称的那一半**：卡片之下到窗口底之间还有几段墨。
                // 只看上面会漏掉同一个缺陷的另一半 —— 推荐那一屏在卡片**下面**还压着
                // 一条裸分隔线 + 「推荐反馈数据」标题 + 一颗按钮（R92 在「数据」那一屏
                // 删掉的就是这个形状），而它只在 1040 那一档才进得了画面。
                let last = segments[segments.count - 1]
                let clippedByWindow = last.bottom >= rows.count - 1
                let belowWindow = Self.absoluteRows(bandMinY: band.minY, scale: scale,
                                                    bandRange: (last.bottom + 1)..<rows.count)
                let belowVec = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,
                                              xRange: cardX, yRange: belowWindow,
                                              fill: pageLuma, gate: 60, minInk: 8)
                let below = Self.inkRuns(column: belowVec, minRunHeight: 4,
                                         mergeGap: Int(8 * scale))
                emit("CARD_BELOW \(fixture.name) \(tag) 卡片底=\(toPt(last.bottom + 1))"
                     + " 窗口=\(toPt(last.bottom + 1))..\(toPt(rows.count))"
                     + " 墨带=\(below.count) 段=\(spans(below, last.bottom + 1))"
                     + (clippedByWindow ? " 卡片贴窗口底⇒这一格没有对象，不进名单" : ""))
                if inkRows > 0 {
                    aboveRoster["\(fixture.name) \(tag)"] = above.count
                    if !clippedByWindow {
                        belowRoster["\(fixture.name) \(tag)"] = below.count
                    }
                }
            }
            emit("CARD_BAND \(fixture.name) \(tag) 页底=\(pageLuma) 填充=\(fill)"
                 + " 墨行=\(inkRows) 卡片段=\(segments.count) 窗口高=\(Int(fixture.size.height))"
                 + " 带子=\(Int(band.minY))..\(Int(band.maxY))"
                 + " 位图=\(rep.pixelsWide)x\(rep.pixelsHigh)"
                 + " 行数=\(rows.count) scale=\(scale)")
            emit("CARD_LAYOUT \(fixture.name) \(tag) bytesPerRow=\(rep.bytesPerRow)"
                 + " bitsPerPixel=\(rep.bitsPerPixel) hasAlpha=\(rep.hasAlpha)"
                 + " planar=\(rep.isPlanar) samples=\(rep.samplesPerPixel)"
                 + " 色彩空间=\(rep.colorSpaceName.rawValue)")
            // R101 / BACKLOG 131 之前这一格钉的是**反面**：「统计」那一屏源码里没有 `GroupBox`，
            // 所以它的正确读数是"这一带一张卡片都没有"，而 R96 那两条读数把它说成
            // "有一张卡片但读不到字"（一条 1pt 的 `Divider()` 当上了填充）。
            // 现在这一屏有了卡片 ⇒ 那条"不许把分隔线认成卡片"的证人**搬去了纯函数那一格**
            //（`testCardFillNeedsAStableBandNotTheFirstDifferingRow` 第 ① 条：只有一条 1pt 线的
            // `modals` 必须返回 nil）—— 它比帧级证人更强：不依赖这台机器拍不拍得出材质。
            // 这一格因此换成产品事实：这一带**恰好一张**卡片。多出来的那一张只可能是
            // 卡片内部那条 `Divider()` 或热图底色块被认成卡片，仍然是同一个 bug 的形状。
            if fixture.name.hasPrefix("settings-stats") {
                statsCells += 1
                if fill < 0 {
                    // **这一格没有对象**：这台机器在这一带根本读不到第二层。
                    // 记下来，交给循环之后那道闸门统一处置（skip），不在这里红。
                    statsDeclined.append("\(fixture.name) \(tag)=填充=-1")
                    emit("CARD_STATS_DECLINED \(fixture.name) \(tag) 原因=读不到被告材质"
                         + " ⇒ 「这一屏恰好一张卡片」这一格不判（不是通过）")
                } else {
                    XCTAssertEqual(1, segments.count,
                                   "\(fixture.name) \(tag)：这一屏现在有一张 `GroupBox`（R101 / 131）⇒ "
                                   + "尺却认出 \(segments.count) 张（≥2 = 卡片内那条 1pt 分隔线或热图底色块"
                                   + "又当上了卡片；0 而填充>=0 则是分段那一关坏了，不是机器看不见）")
                }
            }
            if inkRows == 0 {
                emit("CARD_RHYTHM_NOT_RUN \(fixture.name) \(tag)（整带零墨 ⇒ 这台机器拍不出这一页）")
                continue
            }
            sawInk = true
            if segments.isEmpty {
                emit("CARD_RHYTHM_DECLINED \(fixture.name) \(tag) 原因=整带没有卡片（全是页面底）"
                     + " ⇒ 不判（不是通过）")
                continue
            }
            for (index, seg) in segments.enumerated() {
                let slice = Array(rows[seg.top...seg.bottom])
                let (edges, gaps, dividers, declined, _) = Self.cardRhythm(rows: slice, scale: scale)
                emit("CARD_RHYTHM \(fixture.name) \(tag) 段\(index + 1)/\(segments.count)"
                     + " y=\(toPt(seg.top))..\(toPt(seg.bottom))pt 分隔线=\(dividers)"
                     + " 边距=\(fmt(edges)) 内侧=\(fmt(gaps))"
                     + (declined.isEmpty ? "" : " 未判原因=\(declined)"))
                // 段贴住带子边 ⇒ 这张卡片没有整块落进带子里，"上/下留白"没有对象。
                // 带子下沿==窗口底由上面那条恒等式钉着，所以**这里**才有资格说"被窗口切断"
                //（R96 是纯函数在替调用处说这句话，而对 720x1040 那一档它是假话）。
                if seg.top == 0 {
                    emit("CARD_RHYTHM_DECLINED \(fixture.name) \(tag) 段\(index + 1)"
                         + " 原因=卡片顶到扫描带上沿 ⇒ 不判（不是通过）")
                    continue
                }
                if seg.bottom >= rows.count - 1 {
                    emit("CARD_RHYTHM_DECLINED \(fixture.name) \(tag) 段\(index + 1)"
                         + " 原因=卡片底到带子下沿 \(Int(band.maxY))pt（=窗口底）"
                         + " ⇒ 这一页比窗口高，被切断了 ⇒ 不判（不是通过）")
                    continue
                }
                guard declined.isEmpty else {
                    emit("CARD_RHYTHM_DECLINED \(fixture.name) \(tag) 段\(index + 1)"
                         + " 原因=\(declined) ⇒ 不判（不是通过）")
                    continue
                }
                // **上下留白不许掉回"没补共享留白"那一档**（R101 新加，出处是本轮我自己犯的那个错）。
                // 我第一版给「统计」补卡片时把 `.settingsCardInset()` 挂到了 `GroupBox` **外面**，
                // 材质里面只剩 GroupBox 默认那一档 ⇒ 尺当场量出 `settings-stats-populated 边距=7.0/7.0`，
                // 而其余卡片是 12.5~14.5。**那一版没有任何断言会红**（这一屏只有 1 条分隔线，
                // 下面那道 `dividers >= 2` 让它走 declined）⇒ 这个错可以静默上线。
                //
                // 为什么只钉下界、不钉上界（第一版我写了 12…16，被真产物当场驳回）：
                // "卡片边到第一处墨"跨卡片**不是同一个量** —— 首行是开关、是图标、还是两行说明，
                // 都会把它推高（实测合法值一路到 17.5 与 33.0：`recommendations-tall 段2 下=17.5`、
                // `general-login-unsupported 段1 上=33.0`）。给它写一个上界就是拿一把
                // 跨种类的尺去要一个数（R100 的 D-160 与"同种元素才互相抵消侧边距"同一课），
                // 所以那条上界今天删掉，理由留在这里，别下一次又补回来。
                //
                // 10.0pt 这个下界是量出来的，不是最优阈值：bug 那一档是 7.0（= 没补留白），
                // 全 suite 合法最小值是 12.5 ⇒ 10 离两边都有 2.5pt 以上。
                for (which, edge) in [("上", edges.first ?? 0.0), ("下", edges.last ?? 0.0)] {
                    XCTAssertGreaterThanOrEqual(edge, 10.0,
                        "\(fixture.name) \(tag) 段\(index + 1) 的\(which)留白 \(String(format: "%.1f", edge))pt"
                        + " 低于 10.0pt ⇒ 这张卡片的上下留白掉回「没补 `.settingsCardInset()`」那一档"
                        + "（实测：补了的是 12.5~14.5，挂到材质外面去的是 7.0）。"
                        + "最常见的原因就是那 7pt 被挂到了 `GroupBox` 外面，见 Round 101 §3。")
                }
                guard dividers >= 2 else {
                    emit("CARD_RHYTHM_NO_DIVIDER \(fixture.name) \(tag) 段\(index + 1)"
                         + " 分隔线=\(dividers) ⇒ 这张卡片确实没有『内侧那一档』——"
                         + "卡片边界读到了、墨也读到了，只是那两条横线一条都不算"
                         + "（与下面那条『带子越界』的断言是两种情形，措辞刻意不共用词，"
                         + "否则变异表按文本认红会认错） ⇒ 不判（不是通过）")
                    continue
                }
                XCTAssertFalse(edges.isEmpty || gaps.isEmpty,
                               "\(fixture.name) \(tag) 段\(index + 1)：这一带有 \(inkRows) 行墨，"
                               + "却读不出卡片边距或分隔线两侧留白 ⇒ "
                               + "是**尺没压住卡片**（带子越界 / 填充取错位置），不是产品没问题")
                if fixture.name == "settings-shortcuts" {
                    XCTAssertGreaterThanOrEqual(dividers, 2,
                                                "settings-shortcuts 这张卡片上有两条分隔线（三行），"
                                                + "实测 \(dividers) 条 ⇒ 要么夹具换了，"
                                                + "要么 `.line` 那一档的门槛把线读丢了")
                }
                let all = edges + gaps
                let spread = all.max()! - all.min()!
                // 容差 4.5 不是拍的：**3.5pt 是从这张帧自己量出来的** —— `settings-data` 里
                // 同一张卡片、同样 12pt 布局间距，接在文字行后面的是 14.0/14.5，
                // 接在 `.rounded` 按钮行后面的是 17.5 ⇒ 按钮的 bezel 底下有 3.5pt 不画墨的边，
                // 而这把尺量的是**墨到墨**，不是布局到布局。再加 1pt 余量（光栅 0.5 + 抗锯齿）。
                // 为什么不是"把按钮行排除掉"：那等于给尺加一层"什么算行"的判断，
                // 而这一层判断本身没人验（R92 那条"漏检和没有检出一模一样"）。
                // R95 那个缺陷的极差是 8.5pt，M528 撤修复之后是 7.5pt ⇒ 4.5 这条线仍然咬得住。
                XCTAssertLessThanOrEqual(spread, 4.5,
                                         "\(fixture.name) \(tag) 段\(index + 1)："
                                         + "同一张卡片里最大的留白 \(String(format: "%.1f", all.max()!))pt、"
                                         + "最小的 \(String(format: "%.1f", all.min()!))pt（边距 \(fmt(edges))、"
                                         + "内侧 \(fmt(gaps))）⇒ 卡片四边与分隔线两侧必须是同一档；"
                                         + "差这么多就是首末行没有内边距，最后一行贴着卡片底"
                                         + "（超过 3.5pt 的那一部分不能拿『按钮 bezel 不画墨』解释）")
                judged += 1
            }
            }
        }
        // R99：把"卡片顶之上"的分布原样打出来，好让下一格的断言有出处可查。
        emit("CARD_ABOVE_SUMMARY " + aboveRoster.keys.sorted().map {
            "\($0)=\(aboveRoster[$0]!)"
        }.joined(separator: " "))
        emit("CARD_BELOW_SUMMARY " + belowRoster.keys.sorted().map {
            "\($0)=\(belowRoster[$0]!)"
        }.joined(separator: " "))
        // R99 / BACKLOG 142：**每一屏在卡片之外只准剩一格墨 —— 分区标题**。
        // 名单不是手抄的，是上面两条 SUMMARY 的实测分布（改产品**之前**）：
        //   上方：九屏各 1 段（78.5..90.5pt，就是分区标题那一行），唯独推荐屏 3 段 ——
        //        多出来的 112.5..124.5pt 是「推荐权重客制化」+「恢复默认」那一行，
        //        146.0..155.0pt 是那句说明；
        //   下方：推荐屏 1040 那一档 2 段（裸分隔线之下的「推荐反馈数据」标题 + 按钮），
        //        其余各屏 0 段。
        // 这两段内容在另外四屏都长在**卡片内部**（`SettingsView` 数据那一屏的
        // `VStack(spacing: 8){标题; 说明}` + `Divider()`，R92 就是照这个形状把「数据」
        // 屏的两段裸内容收进卡片的）。所以这不是"另一种合法排版"，是同一扇窗口里
        // 用两种语言说同一句话 —— 而这一次它有读数，不再是我看代码看出来的印象。
        emit("CARD_ABOVE_CAPABILITY settings格=\(settingsCells) 有材质=\(materialCells)"
             + " 进名单=\(aboveRoster.count)（地板=min(8, 有材质) —— 从**上游那一关**推，不从名单推）")
        // R100 / BACKLOG 146：CI 的 runner 上二十格全是 `填充=-1`（那里的 `GroupBox` 填充
        // 落在页面底 ±3 以内 ⇒ `cardFill` 第一关就没有一行过关）。
        // R99 让这件事变成一条红 —— 那是**这条判据第一次在 runner 上说话**，
        // 而它说的是"我没有对象"。两种收场都不许：静默通过（把没跑记成通过），
        // 永久红（把机器前提记成产品缺陷，之后真缺陷会被这条淹掉）。
        // 所以：以 skip 的形式**响** —— 跳过会被执行数闸门数进 `skipped=`，看得见、有名字。
        if materialCells == 0 {
            throw XCTSkip("这台机器拍不出任何卡片材质：\(settingsCells) 格 settings 全报 填充=-1"
                              + " ⇒ 「卡片外几段墨」这条判据没有对象（不是通过，也不是产品缺陷）。"
                              + "本机同一批帧读到 \(aboveRoster.count) 格；差异在 runner 的半透明材质"
                              + "不合成（页底 light=236/dark=52，卡片填充在 ±3 内）。见 BACKLOG 147。")
        }
        // R157 / BACKLOG 196：**同一族错法在这一格里是"按档"的**。runner 打的是
        // `CARD_ABOVE_CAPABILITY settings格=26 有材质=2 进名单=1`，而那一格来自
        // `settings-shortcuts-recording light` —— **暗档一格都没有**。旧出口问的是"有没有材质"
        // （`materialCells == 0`），runner 有 2 格 ⇒ 没 skip，于是红了两句都不是产品的话
        // （`「统计」4 格没进卡片计数`、`名单只有 1 格而本机读到 2 格材质`）。
        // 现在问的是这条判据真正需要的对象：**两档各都得有一格进得了名单**。
        let rosterLight = aboveRoster.keys.filter { $0.hasSuffix(" light") }.count
        let rosterDark = aboveRoster.keys.filter { $0.hasSuffix(" dark") }.count
        emit("CARD_ABOVE_BANDS light=\(rosterLight) dark=\(rosterDark)"
             + "（settings格=\(settingsCells) 有材质=\(materialCells) 进名单=\(aboveRoster.count)）")
        if rosterLight == 0 || rosterDark == 0 {
            emit("CARD_RHYTHM_SHADE_NOT_RUN=1 某一档整档进不了名单（light=\(rosterLight) dark=\(rosterDark)，"
                 + "有材质=\(materialCells) 统计未判=\(statsDeclined.count)）"
                 + " ⇒ 那一档的卡片材质在这台机器上不合成：不是通过，也不是产品缺陷。见 BACKLOG 147 / 196。")
            throw XCTSkip("这台机器在某一档上拍不出**可判的卡片段**（light=\(rosterLight) dark=\(rosterDark)）"
                              + " ⇒ 竖向节奏与「统计」那两格在那一档没有对象。本机两档各有十几格，照判。"
                              + "（读数在上一行 `CARD_RHYTHM_SHADE_NOT_RUN=1`，见 BACKLOG 196）")
        }
        emit("CARD_STATS_CAPABILITY 统计格候选=\(statsCells) 有对象=\(statsCells - statsDeclined.count)"
             + " 未判=\(statsDeclined.count)（未判名单只在**这台机器读得到材质**时才要求为空）")
        // skip 在上面那道 `materialCells == 0` 里已经响过了；能走到这一行说明
        // **本机读得到材质** ⇒ 那时「统计」这一屏不许有任何未判。
        // 没有这一格，①那条降级就成了万能挡箭牌：任何读不到都能自称机器前提。
        XCTAssertTrue(statsDeclined.isEmpty,
                      "本机读到 \(materialCells) 格材质，「统计」却有 \(statsDeclined.count) 格没进卡片计数："
                      + statsDeclined.joined(separator: " ")
                      + " ⇒ 同一台机器别处看得见，那就不是「机器看不见」，去看分段与填充那一关")
        XCTAssertFalse(aboveRoster.isEmpty,
                       "本机看得见 \(materialCells) 格卡片材质，却没有一屏进得了「卡片外几段墨」的名单"
                       + " ⇒ 尺瞎了（两档 settings 帧读到了卡片却读不到墨），不许当成通过")
        XCTAssertGreaterThanOrEqual(aboveRoster.count, min(8, materialCells),
                                    "名单只有 \(aboveRoster.count) 格，而本机读到 \(materialCells) 格材质"
                                    + " ⇒ 有对象却没被量到（大半页面漏了），这一轮的「全绿」不作数")
        for key in aboveRoster.keys.sorted() {
            XCTAssertEqual(1, aboveRoster[key]!,
                           "\(key)：卡片顶之上读到 \(aboveRoster[key]!) 段墨，而这一扇窗口的规矩是"
                           + "只剩分区标题那 1 段。两个方向各有成因："
                           + "读到 0 段 ⇒ 这把尺瞎了（分区标题一定画在卡片之上，"
                           + "R99 第一版把带内相对行号当绝对行用就是这个读数）；"
                           + "读到 2 段以上 ⇒ 产品把本该在卡片里的内容挂在外面"
                           + "（推荐屏多出来那两段是二级标题+按钮、说明段）。"
                           + "两种都不许靠改这条的期望数收场（段的位置在 CARD_ABOVE 那几行）")
        }
        for key in belowRoster.keys.sorted() {
            XCTAssertEqual(0, belowRoster[key]!,
                           "\(key)：最后一张卡片之下、窗口底之上还读到 \(belowRoster[key]!) 段墨"
                           + " ⇒ 卡片外面还压着裸内容（推荐屏那条 `Divider()` + "
                           + "「推荐反馈数据」标题 + 按钮就是这个形状）。"
                           + "上面「卡片之上必须恰好 1 段」这一格同时是这条的**正对照**："
                           + "尺瞎了的时候上面那格会先红，不会让这里假绿")
        }
        XCTAssertFalse(sawSegment && !sawInk,
                       "两档 settings 帧读到了卡片段，却一条墨都没判 ⇒ **墨那一档瞎了**"
                       + "（`inkGate` / 填充取错位置），不是这台机器拍不出：拍不出是连材质都读不到，"
                       + "也就不会有卡片段。这一格不许落到下面那条 skip 里")
        XCTAssertFalse(sawInk && judged == 0,
                       "有卡片读到了墨，却一条都没判 ⇒ **尺瞎了**（分隔线那一档读不到、"
                       + "或 declined 被误报），不是这台机器拍不出。不许让它安静地 skip 掉")
        if judged == 0 {
            throw XCTSkip("CARD_RHYTHM_NOT_RUN：两档所有 settings 帧都读到零墨 ⇒ 竖向节奏记为未运行"
                          + "（BACKLOG 43 同族），不算通过")
        }
    }

    /// 判据自己重渲染的那张帧，**必须就是交付的那一页**（R98 / BACKLOG 141）。
    ///
    /// 缺陷是量出来的，不是想到的。R97 记下的那句"两条读图通道给出不同的卡片边界"被 R98
    /// 自己的对照**证伪**了：同一张帧走 TIFF 回路与直接解 PNG，settings 族 20 帧逐段一致
    ///（`CARD_CHANNEL_SUMMARY 不一致=0`）。真正的分歧是**两张不同的图** ——
    /// 判据 `render` 的那张与捕获卷交付的那张逐字节不同（319980 B vs 333059 B，
    /// 其余 9 对逐字节相同），而它是全仓**唯一**声明了 `seed:` 的夹具；
    /// 逐行指纹把分歧起点钉在 **566.0pt**，那里正是种子的两行「移除」该在的位置，
    /// 870.5..936.0pt 交付帧 54 行墨 / 判据帧 0 行（`.scratch/motion-audit-2/r98_seed_divergence.py`）。
    /// 根因：种子的"种 + 还原"只写在 `testCaptureKeyViews` 一处，其余二十多个 `render`
    /// 调用点把 `fixture.seed` 当不存在 ⇒ **判据量的不是它名字里那张帧**，
    /// 而帧基线钉的是有种的那一张，两边的读数从此永远对不上。
    ///
    /// 三条判据各挡一种假绿：
    /// ① 拍之前把那个键**故意种成别的条数** ⇒ 只有"`render` 用了夹具自己的种子"能给出期望条数。
    ///    忽略种子的那一版会画出我种的这一条（1 行 vs 期望 2 行）⇒ 红。M543 走的就是这条路。
    /// ② 整页一条墨都没有 ⇒ 这台机器拍不出这一页，记未运行（BACKLOG 43 同族），不许算通过。
    ///    这一条必须在①之前判，否则 runner 上"空白页"会把①红成一条**假的产品缺陷**。
    /// ③ 拍完之后那个键必须还是我种进去的那一条 ⇒ `render` 只借不占；
    ///    还原由这条钉住，而不是靠调用方记得做（上一版的写法正是"调用方忘了就没人管"）。
    func testSeededFixtureRendersTheSeededPage() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r98-seed-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var judged = 0
        for (appearance, tag) in [(NSAppearance.Name.aqua, "light"),
                                  (NSAppearance.Name.darkAqua, "dark")] {
            let seeded = fixtures(appearance: appearance).filter { $0.seed != nil }
            XCTAssertFalse(seeded.isEmpty,
                           "\(tag)：一条声明了 `seed:` 的夹具都没有 ⇒ 这条判据没有对象。"
                           + "删掉最后一条种子夹具是可以的，但必须连这条判据一起删 —— "
                           + "留着它全绿，等于替『种子通道又没人验了』做担保")
            for fixture in seeded {
                guard let seed = fixture.seed else { continue }
                guard seed.key == CapturePolicy.userExcludedKey else {
                    emit("SEED_GUARD_NA \(fixture.name) \(tag) 键=\(seed.key)"
                         + "（这个键没有『条数 → 右边缘墨带』的映射 ⇒ 这一条没判，不算通过）")
                    continue
                }
                let expected = CapturePolicy.decodeUserExcluded(seed.value).count
                // ① 的哨兵：条数必须与夹具自己声明的不同，否则"忽略种子"也能给出期望条数。
                let sentinel = CapturePolicy.encodeUserExcluded(
                    expected == 1 ? ["com.example.sentinel.a", "com.example.sentinel.b"]
                                  : ["com.example.sentinel.a"])
                XCTAssertNotEqual(CapturePolicy.decodeUserExcluded(sentinel).count, expected,
                                  "哨兵与夹具声明的条数相同 ⇒ 这一条判据恒真，先修它")
                let original = UserDefaults.standard.string(forKey: seed.key)
                UserDefaults.standard.set(sentinel, forKey: seed.key)
                defer {
                    if let back = original {
                        UserDefaults.standard.set(back, forKey: seed.key)
                    } else {
                        UserDefaults.standard.removeObject(forKey: seed.key)
                    }
                }
                let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
                _ = try render(fixture, appearance: appearance, to: file)
                XCTAssertEqual(UserDefaults.standard.string(forKey: seed.key), sentinel,
                               "\(fixture.name) \(tag)：`render` 拍完之后没有把 \(seed.key) 还原成"
                               + "它进来时看到的那一条 ⇒ 同一次运行里后面的帧会被这张夹具带脏"
                               + "（R98 把种子搬进 `render` 之后，这一条才是『搬进去的那一半有没有还原』）")
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("\(fixture.name) \(tag)：读不回刚拍的帧")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let full = Int(177 * scale)..<Int(706 * scale)
                let fill = Self.modalLuma(bytes: base, bytesPerRow: rep.bytesPerRow,
                                          xRange: Int(684 * scale)..<Int(706 * scale),
                                          yRange: Int(120 * scale)..<Int(960 * scale))
                // ② 先判"这一页到底画没画"：整幅卡片区一条墨带都没有 ⇒ 这台机器的通道问题，
                // 不是产品没画种子行。（与①用**同一颗尺**：同一个 fill、同一个 gate，
                // 否则就是证人用自己的尺给别人的判据作证 —— BACKLOG 104 那一族。）
                let wholePage = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,
                                               xRange: full, yRange: Int(120 * scale)..<Int(960 * scale),
                                               fill: fill, gate: 60, minInk: 4)
                let rightEdge = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,
                                               xRange: Int(684 * scale)..<Int(706 * scale),
                                               yRange: Int(120 * scale)..<Int(960 * scale),
                                               fill: fill, gate: 60, minInk: 2)
                let drawn = Self.inkRunCount(column: wholePage, minRunHeight: 2, mergeGap: 2)
                // `mergeGap` 用**行距的一档**而不是 1：本机逐行量过「移除」那两颗按钮 ——
                // 一颗按钮的字在竖直方向本来就不连续（行内空隙 8px = 4pt），
                // 而行与行之间空 43px = 21.5pt。取 8pt 落在这两个数中间（5.4 倍空档），
                // 于是"一颗按钮"数成一段、"两颗按钮"数成两段。
                // 为什么不能取 2px：那样每颗字被自己的降部切成两段，两行读出 4 段 ——
                // 尺会把"种子画出来了"报成"画多了"，而这条判据要的恰恰是能被信任的计数。
                let found = Self.inkRunCount(column: rightEdge, minRunHeight: 4,
                                             mergeGap: Int(8 * scale))
                emit("SEED_GUARD \(fixture.name) \(tag) 期望=\(expected) 右边缘墨带=\(found)"
                     + " 整页墨带=\(drawn) 填充=\(fill)")
                guard drawn > 0 else {
                    emit("SEED_GUARD_NOT_RUN \(fixture.name) \(tag)（整页零墨 ⇒ 这台机器拍不出这一页，"
                         + "不算通过也不算盲区）")
                    continue
                }
                judged += 1
                XCTAssertEqual(found, expected,
                               "\(fixture.name) \(tag)：右边缘那一列读到 \(found) 段墨，而夹具声明的种子有 "
                               + "\(expected) 条 ⇒ 判据量的**不是**交付的那一页。"
                               + "`render` 有没有应用 `fixture.seed` 是这里唯一的解释路径"
                               + "（R98：上一版它没有，于是这张帧比交付帧少 60pt 的两行，"
                               + "而两版帧的字节数差 13079 B）")
            }
        }
        if judged == 0 {
            throw XCTSkip("SEED_GUARD_NOT_RUN：两档所有种子夹具都画不出墨 ⇒ 种子通道记为未运行"
                          + "（BACKLOG 43 同族），不算通过")
        }
    }

    /// 种子**只准在 `render` 里种一次**（R98 / 调用点级守卫，与 R43/R44 那一族同一条规矩）。
    ///
    /// 为什么光有上一条判据不够：上一条量的是"这一张帧有没有种子"，而本轮那个缺陷的形状是
    /// "种子的应用散落在调用方" —— 那件事可以在**不改变任何一张帧**的情况下重新长出来
    ///（下一个加种子夹具的人在自己的测试里种一次，就又多了一份迟早会漂开的副本）。
    /// 所以这一条判的是**写法**：全文件里"把 `fixture.seed` 写进 UserDefaults"这句只能出现一次。
    ///
    /// 锚点用拼接构造，不写全串：这条守卫扫的是**它自己所在的那个文件**，
    /// 字面量一出现就是 2 次命中，守卫会红在自己的源码上（R53 的 `region()` 刚犯过这一条）。
    func testSeedIsAppliedOnlyInsideRender() throws {
        let text = try String(contentsOfFile: #filePath, encoding: .utf8)
        let code = Self.codeOnly(text)
        let setter = "UserDefaults.standard.set(seed.value" + ", forKey: seed.key)"
        let writes = code.components(separatedBy: setter).count - 1
        XCTAssertEqual(1, writes,
                       "把夹具种子写进 UserDefaults 这句出现了 \(writes) 次，期望 1 次（只准在 `render` 里）。"
                       + "多于一次 ⇒ 某条测试自己种了一份：`render` 已经会种，"
                       + "自己再种的那份要么被 `render` 覆盖、要么在拍完之后没还原 —— "
                       + "两种都会让判据量的不是交付的那一页（R98 / BACKLOG 141 就是这个形状）")
    }

    /// 数墨带那把尺的算术要有真值表（**不覆盖管线**：它判的是纯函数；
    /// 管线级判据是上面那条 `testSeededFixtureRendersTheSeededPage`）。
    ///
    /// 合成分布照抄本机量出来的那一组数（亮档 `settings-privacy-excluded`，2x）：
    /// 一颗「移除」的字在窄带里占 17 行，**自己中间空 8 行**（降部），
    /// 两颗之间空 43 行。`mergeGap=16` 落在这两个数中间。
    /// 四条各挡一种"看着对、其实答不了问题"：
    /// ① 空 / 全 false ⇒ 0 段（尺不许把"没有"读成"有一段"）；
    /// ② 两颗真按钮（间隔 43 行 ≥ mergeGap）⇒ 2 段；
    /// ③ 一颗被降部切开（行内空 8 行 < mergeGap）⇒ **必须还是 1 段** —— 这一条钉的是合并本身：
    ///    不合并就是 2 段，于是"种子只画了一条"与"画了两条"这把尺读出来一样；
    /// ④ 两段都不够高、合并后够高 ⇒ 1 段 —— 这一条钉的是**先合并、后筛高**的顺序：
    ///    反过来说先筛高会数成 0，而 0 与"两条种子行整条没画出来"在报表上长得一模一样，
    ///    那正是本轮要抓的事，不能给它一个安静的逃法。
    /// ⑤⑥ 边界：间隔正好等于 mergeGap ⇒ 不合并（`<` 不是 `<=`）。
    func testInkRunCountArithmeticIsATruthTable() {
        func rows(_ spec: [(Bool, Int)]) -> [Bool] {
            spec.flatMap { value, count in Array(repeating: value, count: count) }
        }
        XCTAssertEqual(0, Self.inkRunCount(column: [], minRunHeight: 4, mergeGap: 16), "空输入")
        XCTAssertEqual(0, Self.inkRunCount(column: rows([(false, 120)]), minRunHeight: 4, mergeGap: 16),
                       "整列都没有墨")
        XCTAssertEqual(2, Self.inkRunCount(
            column: rows([(false, 20), (true, 17), (false, 43), (true, 17), (false, 20)]),
            minRunHeight: 4, mergeGap: 16), "两颗按钮（本机 17 行高、间隔 43 行）")
        XCTAssertEqual(1, Self.inkRunCount(
            column: rows([(false, 20), (true, 9), (false, 8), (true, 8), (false, 20)]),
            minRunHeight: 4, mergeGap: 16), "一颗按钮被自己的降部切开 ⇒ 仍算一颗")
        XCTAssertEqual(1, Self.inkRunCount(
            column: rows([(true, 3), (false, 1), (true, 3)]), minRunHeight: 4, mergeGap: 2),
                       "两段都不够高、但合并后够 ⇒ 1 段（先合并后筛高；反序数成 0）")
        XCTAssertEqual(0, Self.inkRunCount(
            column: rows([(false, 5), (true, 3), (false, 5)]), minRunHeight: 4, mergeGap: 2),
                       "3 行的孤立墨点不算一颗按钮")
        // 边界：间隔**正好等于** mergeGap ⇒ 不合并（`<` 而不是 `<=`）。
        // 这一格必须有，否则"把两颗数成一颗"与"把一颗数成两颗"这条尺都答不了问题。
        XCTAssertEqual(2, Self.inkRunCount(
            column: rows([(true, 5), (false, 2), (true, 5)]), minRunHeight: 4, mergeGap: 2),
                       "空 2 行 = mergeGap ⇒ 不合并")
        XCTAssertEqual(1, Self.inkRunCount(
            column: rows([(true, 5), (false, 1), (true, 5)]), minRunHeight: 4, mergeGap: 2),
                       "空 1 行 < mergeGap ⇒ 合并")
        // R99：`inkRuns` 交出的是**位置**，`inkRunCount` 只是它的 `.count`。
        // 位置必须与计数同源，否则"几段"和"那一段在哪"是两颗尺（BACKLOG 104 那一族）。
        let positioned = Self.inkRuns(
            column: rows([(false, 20), (true, 17), (false, 43), (true, 17), (false, 20)]),
            minRunHeight: 4, mergeGap: 16)
        XCTAssertEqual(2, positioned.count)
        XCTAssertEqual("20..36,80..96",
                       positioned.map { "\($0.top)..\($0.bottom)" }.joined(separator: ","),
                       "段的位置必须就是那两段墨的首尾行（不是外框、不是中心）")
    }

    /// 带内相对行 → 位图绝对行的换算（R99 / BACKLOG 142）。
    ///
    /// **不覆盖管线**：这条判的是纯函数；它守的那个管线级读数在
    /// `testSettingsCardVerticalRhythmIsOneNumber` 里的 `CARD_ABOVE` 那一格。
    /// 真值表里第 ② 条就是本轮真犯过的错（把相对行号直接当绝对行喂进去）：
    /// 那样量出来的窗口是 0..45.5pt，而它自认为在量 60..106pt，
    /// 报出来的"卡片顶之上没有墨"是**仪器读数**，不是产品事实。
    func testBandRowToAbsoluteRowIsATruthTable() {
        // ① 本机实测的那一档：带子从 60pt 起、2x 屏、卡片顶在带内第 92 行（=106pt）。
        XCTAssertEqual(120..<212, Self.absoluteRows(bandMinY: 60, scale: 2, count: 92))
        // ② 忘了偏移会量到哪：这一格就是本轮那个 bug 的形状。
        XCTAssertNotEqual(0..<92, Self.absoluteRows(bandMinY: 60, scale: 2, count: 92),
                          "窗口从 0 起 ⇒ 量的其实是窗口最上面那 46pt（带子外面）")
        // ③ 带子贴顶（minY=0）⇒ 两种坐标重合，换算必须退化成恒等。
        XCTAssertEqual(0..<92, Self.absoluteRows(bandMinY: 0, scale: 2, count: 92))
        // ④ 1x 屏：行数=pt，偏移也跟着变（不是"永远乘 2"）。
        XCTAssertEqual(60..<152, Self.absoluteRows(bandMinY: 60, scale: 1, count: 92))
        // ⑤ 零行 ⇒ 空区间，不越界（`first.top == 0` 时卡片顶就是带上沿）。
        XCTAssertEqual(120..<120, Self.absoluteRows(bandMinY: 60, scale: 2, count: 0))
        // ⑥ 负数带沿（不可能出现，但 clamp 必须在那儿）⇒ 从 0 起，不给越界读。
        XCTAssertEqual(0..<10, Self.absoluteRows(bandMinY: -50, scale: 2, count: 10))
        // ⑦ 区间版（卡片**之下**那一格用）：起点不是带上沿时，偏移要一起进去。
        XCTAssertEqual(212..<960, Self.absoluteRows(bandMinY: 60, scale: 2, bandRange: 92..<840))
        // ⑧ 区间版与"从 0 起"的那一格必须给出同一个窗口（两条式子不许各说一套）。
        XCTAssertEqual(Self.absoluteRows(bandMinY: 60, scale: 2, count: 92),
                       Self.absoluteRows(bandMinY: 60, scale: 2, bandRange: 0..<92))
    }

    /// 横向那两格纯函数的真值表（R100 / BACKLOG 138）。
    ///
    /// **不覆盖管线**：管线级判据是下面那条 `testSettingsCardHorizontalInset...`。
    /// 这里钉的是两件事：① "够长"这一格（一条 1pt 的分隔线、一颗按钮都不许冒充卡片左沿，
    /// 那是 R97 那一族的横向版本）；② **读不到必须返回 nil，不许返回 0** ——
    /// 0 会被下游读成"内缩 = 0pt"，那是把仪器的失败报成一个产品数值
    ///（R99 手搓的那把 python 尺就是把它报成了 −172pt）。
    func testHorizontalEdgeRulerIsATruthTable() {
        func cols(_ spec: [(Bool, Int)]) -> [Bool] {
            spec.flatMap { v, n in Array(repeating: v, count: n) }
        }
        XCTAssertEqual(4, Self.firstSpanStart(columns: cols([(false, 4), (true, 6)]), minRun: 5))
        XCTAssertNil(Self.firstSpanStart(columns: cols([(false, 4), (true, 4)]), minRun: 5),
                     "只有 4 列连续材质 ⇒ 不够长，宁缺不假")
        XCTAssertNil(Self.firstSpanStart(columns: cols([(true, 3), (false, 1), (true, 3)]), minRun: 5),
                     "被断开的小段不许拼成一条左沿")
        XCTAssertNil(Self.firstSpanStart(columns: cols([(false, 6)]), minRun: 5), "全假 ⇒ nil")
        XCTAssertNil(Self.firstSpanStart(columns: [], minRun: 5), "空向量 ⇒ nil（不是 0）")
        XCTAssertEqual(0, Self.firstSpanStart(columns: cols([(true, 5)]), minRun: 5))
        // ⑨ 调用点这一轮把 `minRun` 从 40pt 降到 2pt（卡片左沿到第一个字形只有 5.5pt，
        // 40pt 会**跳过**真正的边）。降下来之后"单列真"必须不算数，否则一个抗锯齿亮点
        // 就能当上左沿，而 5.5pt 那个读数会变成 0.5pt —— 一个更像缺陷的假数。
        XCTAssertNil(Self.firstSpanStart(columns: cols([(false, 3), (true, 1), (false, 6)]), minRun: 2),
                     "单列真不算左沿（minRun=2 的那一格）")
        XCTAssertEqual(5, Self.firstSpanStart(
            columns: cols([(false, 3), (true, 1), (false, 1), (true, 4)]), minRun: 2),
                       "被单列假断开的后一段才是左沿")
        XCTAssertEqual(7, Self.firstInkColumn(columns: cols([(false, 7), (true, 2)]), from: 0))
        XCTAssertNil(Self.firstInkColumn(columns: cols([(false, 9)]), from: 0), "没有墨 ⇒ nil")
        XCTAssertEqual(9, Self.firstInkColumn(columns: cols([(true, 3), (false, 6), (true, 2)]),
                                              from: 4),
                       "from 之前那三列墨不许被算进来（卡片左沿以左是页面底）")
        XCTAssertNil(Self.firstInkColumn(columns: cols([(true, 2)]), from: 5), "from 越界 ⇒ nil")
    }

    /// 卡片里的字离卡片左沿有多远，**与系统 `GroupBox` 自己那一档对账**（R100 / BACKLOG 138）。
    ///
    /// 它要回答的是 138 那句"横向内边距只有 5.5pt，而 macOS 通常 16–20pt"里
    /// 唯一没有出处的那一半：**"macOS 通常"是多少**。
    /// 量法刻意不用那个数：同一台机器、同一档外观，先量一个什么都不加的 `GroupBox`
    ///（`cardprobe-groupbox-default`）拿到系统自己那一档，再量真实卡片，比差。
    ///
    /// **答案：138 不是缺陷，那条"16–20pt"是没有出处的印象。** 系统自己那一档 = 5.5pt
    ///（亮暗两档同一个数），产品六张卡片 = 5.0~5.5pt，差在一像素之内；
    /// 而 `.settingsCardInset()` 只加**纵向**留白（`SettingsView.swift:38`），
    /// 横向一个像素都没加 —— 这个 5.5 完全是系统给的。
    /// 右沿同法量得 5.0pt（`r100_right.py`），左右对称。
    /// 所以按"16pt"去改会让这扇窗口**更不**像系统，与目标里那条"优先系统 API / 原生材质"反着走。
    /// 判据因此钉成"与系统参照同档"而不是"≥某个数"：它拦的是**以后有人给卡片加横向内边距**
    /// 或改掉 `GroupBox` 默认样式，而不是拦一个凭印象定的地板。
    /// R121 / BACKLOG 150：参照臂"带子里没墨"的四种出口，先写真值表再接产品入口。
    /// 全部 2³ = 8 种组合都列出来，包括物理上不可能的那几种（`整帧=0 而详情列>0`）——
    /// 不可能的那几行是**顺序**的证据：函数先问整帧再问列，所以冲突输入只会走一个出口。
    /// 为什么必须有这么一张表：R119 我在没有它的情况下把"带子 0 墨"读成了"帧太矮"，
    /// 而这一跑 CI 的读数（`整窗墨行=70 带子墨行=0 详情列墨行=0`）说明当时有四种解释，
    /// 我只看见了一种（U-405）。
    func testCardprobeArmVerdictIsATruthTable() {
        let ink = 7, none = 0
        let table: [(page: Int, region: Int, band: Int, expect: CardprobeArmVerdict, why: String)] = [
            (ink, ink, ink, .judged, "带子里有内容：材质那条读数有对象"),
            (ink, ink, none, .bandMisplaced, "列里有墨而带子没有＝我框错了 ⇒ 会红"),
            (ink, none, none, .regionUnpainted, "整帧有墨而这一列 0 墨＝这台机器没画这一列"),
            (none, ink, ink, .judged, "物理上不可能，但顺序要求带子优先：仍然可判"),
            (none, ink, none, .pageUnrendered, "冲突输入：整帧优先，先说'这一页没拍出来'"),
            (none, none, ink, .judged, "带子有墨就不必问地板"),
            (none, none, none, .pageUnrendered, "整帧 0 墨＝BACKLOG 43 那台机器的形状"),
            (ink, none, ink, .judged, "带子是列的子集，这种组合不可能出现；顺序仍然给可判")
        ]
        for row in table {
            let got = Self.cardprobeArmVerdict(pageInkRows: row.page,
                                               regionInkRows: row.region,
                                               bandInkRows: row.band)
            XCTAssertEqual(got, row.expect,
                           "整帧=\(row.page) 详情列=\(row.region) 带子=\(row.band)"
                               + " 期望 \(Self.verdictText(row.expect))，实际 \(Self.verdictText(got))"
                               + " —— 这一格讲的就是：\(row.why)")
        }
        // 四种出口必须各有不同的词：两个结局共用一个词，读数就分不开它们（这轮的新病的形状）。
        let words = Set(table.map { Self.verdictText($0.expect) })
        XCTAssertEqual(words.count, 4, "四种结局只打出 \(words.count) 个不同的词：\(words.sorted())")
    }

    /// R124 / BACKLOG 171：盲区位名单按机器分键之后，四种关系先写真值表。
    /// 为什么必须在真值表里钉"未登记"那一格：如果 `registered == nil` 能和 `.clean` 走同一个出口，
    /// 那么任何一台新机器跑这条判据都会白拿一个绿 —— 而 runner 那一台正是这轮才被发现
    /// "它的位从来没被登记过"（R120 那朵 `gone` 红的真身）。
    func testSidebarRosterVerdictIsATruthTable() {
        let a = "settings-general", b = "settings-min"
        let table: [(registered: Set<String>?, measured: Set<String>,
                     expect: SidebarRosterVerdict, why: String)] = [
            ([a, b], [a, b], .clean, "登记与实测完全一致：这一台的盲区还是那几处"),
            ([a], [a, b], .extra([b]), "多出一处没登记的盲区 ⇒ 红（先定位是谁）"),
            ([a, b], [a], .gone([b]), "登记过的那处不再反侧 ⇒ 红（机制修好了或尺瞎了，两种都要看帧）"),
            ([a, b], [], .gone([a, b]), "一台完全不反侧的机器复用别人的行 ⇒ 红，不许读成「全绿」"),
            (nil, [], .unkeyed, "没登记的那台：空集也不许通过"),
            (nil, [a], .unkeyed, "没登记的那台：有盲区也不许顺手借用别台的行"),
            ([], [], .clean, "登记成空集是一条**声明**（这台不反侧），它同样被 gone/extra 钉住"),
            ([], [a], .extra([a]), "登记成空集之后又冒出反侧 ⇒ 红")
        ]
        for row in table {
            let got = Self.sidebarRosterVerdict(registered: row.registered, measured: row.measured)
            XCTAssertEqual(got, row.expect,
                           "登记=\(row.registered.map { $0.sorted().description } ?? "nil")"
                               + " 实测=\(row.measured.sorted()) 期望 \(Self.rosterVerdictText(row.expect))"
                               + " 实得 \(Self.rosterVerdictText(got)) —— 这一格讲的是：\(row.why)")
        }
        // 四种结局必须各有不同的词：两个结局共用一个词，读数就分不开它们（D-183）。
        let words = Set(table.map { Self.rosterVerdictText($0.expect) })
        XCTAssertEqual(words.count, 5,
                       "四种关系（外加 extra/gone 的计数形状）只打出 \(words.count) 个不同的词：\(words.sorted())")
        // 键本身必须由**量出来**的事实组成：倍率是其中一格，不许写死成"我记得本机是 2x"。
        for good in ["arm64/macOS 15.7/1x", "x86_64/macOS 26.0/2x", "arm64/macOS 27.0/2x"] {
            XCTAssertTrue(Self.sidebarRosterKeyIsWellFormed(good), "成形的键被判不成形：\(good)")
        }
        for bad in ["runner", "CI", "macos-15", "arm64/macOS 15.7", "arm64/15.7/1x",
                    "arm64/macOS 15/1x", "arm64/macOS 15.7/3x", "ppc64/macOS 15.7/1x"] {
            XCTAssertFalse(Self.sidebarRosterKeyIsWellFormed(bad), "不成形的键被判成形：\(bad)")
        }
        // R126 / 171：这张表本身要能被本机判 —— 两行都在、键都成形，才谈得上"按机器分键"。
        XCTAssertGreaterThanOrEqual(Self.darkSidebarTextBlindSpotsByMachine.count, 2,
            "盲区名单只有 \(Self.darkSidebarTextBlindSpotsByMachine.count) 行 ⇒ 「按机器分键」退化成了"
                + "一台机器的别名。第二行必须由另一台机器**自己印出来的键**填（D-186③），"
                + "不许拿本机那一行改名凑数。")
        let malformed = Self.darkSidebarTextBlindSpotsByMachine.keys
            .filter { !Self.sidebarRosterKeyIsWellFormed($0) }.sorted()
        XCTAssert(malformed.isEmpty,
                  "盲区名单里有 \(malformed.count) 个键不成形：\(malformed) ⇒ 形状是 "
                      + "`arch/macOS 主次版本/倍率`（倍率只准 1x 或 2x）。不成形的键永远不会被命中，"
                      + "那是一条看起来像声明的死行（比没有更坏）。")
        let k1 = Self.sidebarRosterMachineKey(scale: 2.0)
        let k2 = Self.sidebarRosterMachineKey(scale: 1.0)
        XCTAssertNotEqual(k1, k2, "键里没带倍率 ⇒ 一台 Retina 与一台非 Retina 会共用同一行盲区名单")
        XCTAssertTrue(k1.contains("macOS"), "键里没带系统版本：\(k1)")
    }

    /// R125 / U-417：数"某个动效档在产品里被不被用"的那颗尺。
    ///
    /// 来历：本轮我为了找"声明了却没供电"的档，在 shell 里 grep `for: .bannerOut`，
    /// 得到 **0 个调用点**，差点据此开一条"这条声明是死的"的账。真去数才发现它是 5 处 ——
    /// 产品里写的是 `asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，
    /// 我的模式只认得其中一种写法（U-417）。
    /// ⇒ 计数不能靠临时 grep，必须是一把**在仓库里、会红、有真值表**的尺。
    ///
    /// 三条形状：① 只数代码不数注释（复用 `codeOnly`，M407 / M411 那一族）；
    /// ② 词边界：`.bannerOut` 不许被 `.bannerOutX` 喂饱，也不许被 `selection:`（无点）喂饱；
    /// ③ 它数的是"提到过"，不是"接上了动画" —— 所以地板是 **≥1**（撤掉声明时它会红），
    ///    而不是某个精确数字；把它写成"等于 n"就是把今天的形状钉成契约（U-92 那一族）。
    static func motionKindCallSites(in rawText: String, kindName: String) -> Int {
        // 剥注释在**尺里面**做，不要求调用方先剥：调用方忘了就是一条会被注释喂饱的守卫
        //（M407 / M411 那一族的形状）。
        let text = Self.codeOnly(rawText)
        let pattern = "\\." + NSRegularExpression.escapedPattern(for: kindName) + "(?![A-Za-z0-9_])"
        guard let re = try? NSRegularExpression(pattern: pattern) else { return 0 }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        return re.numberOfMatches(in: text, range: range)
    }

    /// 从测试文件上溯找产品源码目录；找不到就报**未运行**，不许默默算通过。
    static func productSourcesRoot() -> URL? {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let dir = candidate.appendingPathComponent("Sources/ClipboardHistoryApp")
            if FileManager.default.fileExists(atPath: dir.path) { return dir }
            candidate = candidate.deletingLastPathComponent()
        }
        return nil
    }

    static func swiftFiles(under dir: URL) -> [URL] {
        let fm = FileManager.default
        guard let en = fm.enumerator(at: dir, includingPropertiesForKeys: nil) else { return [] }
        var out: [URL] = []
        for case let url as URL in en where url.pathExtension == "swift" { out.append(url) }
        return out.sorted { $0.path < $1.path }
    }

    func testMotionKindCallSitesRulerIsATruthTable() {
        let samples: [(text: String, kind: String, expect: Int, why: String)] = [
            ("withAnimation(MotionCatalog.animation(for: .bannerOut)) { hide() }",
             "bannerOut", 1, "一种写法：命名参数里的枚举"),
            ("MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)",
             "bannerOut", 1, "本轮差点漏掉的就是这一种（U-417 的本体）"),
            (".hover\n.hover", "hover", 2, "同一颗尺要能数次数，不是数出现过"),
            ("// 这里以前写的是 .bannerOut，现在撤了", "bannerOut", 0,
             "注释里的提及不算供电（M407 / M411 那一族）"),
            ("let x = .bannerOutExtra", "bannerOut", 0, "词边界：更长的名字不许喂饱它"),
            ("List(selection: $sel)", "selection", 0, "无点的冒号标签不许算"),
            ("", "contentFade", 0, "空文本给 0，不给 nil 也不给 1")
        ]
        for s in samples {
            let got = Self.motionKindCallSites(in: s.text, kindName: s.kind)
            XCTAssertEqual(got, s.expect,
                           "文本「\(s.text.prefix(46))」数 .\(s.kind) 期望 \(s.expect) 实得 \(got)"
                               + " —— 这一格讲的是：\(s.why)")
        }
    }

    func testEveryMotionKindIsWiredSomewhereInProduct() throws {
        guard let root = Self.productSourcesRoot() else {
            emit("MOTION_KIND_NOT_RUN all（找不到 Sources/ClipboardHistoryApp，从 \(#filePath) 上溯 6 层未果）")
            throw XCTSkip("MOTION_KIND_NOT_RUN：源码目录找不到 ⇒ 这条守卫记为未运行，不算通过")
        }
        var zero: [String] = []
        for kind in MotionCatalog.Role.allCases {
            // 这个枚举是 `String` rawValue 的：取 rawValue 而不是 `String(describing:)`，
            // 后者对带原始值的枚举今天恰好等于 case 名，但那是实现细节，不是契约。
            let name = kind.rawValue
            var total = 0
            var files: [String] = []
            for url in Self.swiftFiles(under: root) {
                // 目录自己不算调用点：`case bannerOut` 与 `case .bannerOut: return 0.12` 都在里面
                if url.lastPathComponent == "MotionCatalog.swift" { continue }
                guard let text = try? String(contentsOf: url, encoding: .utf8) else { continue }
                let n = Self.motionKindCallSites(in: text, kindName: name)
                if n > 0 { total += n; files.append("\(url.lastPathComponent):\(n)") }
            }
            emit("MOTION_KIND_COVERAGE kind=\(name) 产品调用点=\(total)"
                 + " 文件=\(files.isEmpty ? "无" : files.prefix(4).joined(separator: " "))")
            if total == 0 { zero.append(name) }
        }
        XCTAssert(zero.isEmpty,
                  "MOTION_KIND_UNWIRED \(zero.sorted())：这些动效档在 MotionCatalog 里声明了，"
                      + "产品里却一处都没提 ⇒ 要么供电、要么把声明撤掉（R42 立的规矩：不许留着空转的声明）。"
                      + "不许为了让它绿而在注释里写一遍 —— 那颗尺只数代码（真值表第 4 格）。")
    }

    func testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r100-inset-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var control: [String: Double] = [:]
        // 参照那一格**左沿**的绝对读数（pt）：夹具自己声明 `.padding(24)` ⇒ 左沿必须在 24pt。
        // 为什么等式之外还要这一格绝对锚点：M559 那一刀（把墨门限从 60 降到 4）证明
        // **相对判据对"整把尺一起偏"是免疫的** —— 参照与被告同偏，差还是 0，判据照样绿。
        // 而本轮修掉的圆角错法恰好就是"整把尺一起偏"（左沿读晚 7.5pt）。
        // 锚点压在**夹具自己声明的那个数**上，不是压在一个借来的常数上。
        var probeBezel: [String: Double] = [:]
        var measured: [String: Double] = [:]
        // 臂 1 / 臂 2 的内缩与左沿：只打印、不参与等式（等式的那一侧必须是臂 0）。
        var armInsets: [String: Double] = [:]
        var declined: [String] = []
        // 与纵向那一格同一个上游信号（BACKLOG 147）：runner 上 `GroupBox` 的填充落在
        // 页面底 ±3 以内 ⇒ `cardFill` 返回 nil ⇒ 这把尺**没有对象**。
        // 地板从"有没有读到材质"推，不从"量到了几格"推（后者是恒真式）。
        var cells = 0
        var materialCells = 0
        // R101：`materialCells` 拆成两半 —— 参照（`cardprobe-*`）与被告（`settings-*`）。
        // 两者的"有没有材质"在 runner 上是**两个不同的事实**（参照亮档有、被告全无），
        // 混成一个数就会让"没有对象"与"没有对照"共用一个闸门（见调用点那段注释）。
        var controlMaterial = 0
        var defendantMaterial = 0
        // R121：参照臂的"带子里没墨"从此有四个出口，其中两个是**有名字的不可判**。
        // 必须计数：一条只打读数不计数的旁路，下一轮就会被读成"这一臂过了"。
        var judgedProbeArms = 0
        var blockedProbeArms = 0
        var misplacedProbeArms = 0
        var probeArmEvaluations = 0
        for (appearance, tag) in [(NSAppearance.Name.aqua, "light"),
                                  (NSAppearance.Name.darkAqua, "dark")] {
            for fixture in fixtures(appearance: appearance) {
                // R102：参照不再是一臂而是**一梯子**（BACKLOG 150），所以角色按前缀认；
                // 但**等式的锚只有一格** —— 臂 0 自己声明 `.padding(24)`，
                // 另外两臂的左沿正是本轮要问的问题，拿它当锚就是拿结论当前提。
                let isProbe = fixture.name.hasPrefix("cardprobe-")
                let isAnchorProbe = fixture.name == "cardprobe-groupbox-default"
                let isSettings = fixture.name.hasPrefix("settings-") && fixture.name != "settings-min"
                guard isProbe || isSettings else { continue }
                let file = scratch.appendingPathComponent("\(fixture.name)-\(tag).png")
                // R107 / 157 的实验 (a)：拍之前把**这一臂自己的视图树**留下（`inspect:` 与帧同源）。
                var geometry: [String] = []
                var columns: [(name: String, rect: CGRect)] = []
                var splitOverflow = 0.0
                var detailInventory = (texts: 0, images: 0, hosts: 0, inside: 0, sample: [String]())
                _ = try render(fixture, appearance: appearance, to: file) { host in
                    geometry = Self.columnBoxes(in: host)
                    columns = Self.splitColumnRects(in: host)
                    splitOverflow = Self.splitContentOverflow(in: host)
                    if let detail = columns.first(where: { $0.name.contains("详情") }) {
                        detailInventory = Self.columnSubviewInventory(in: host, rect: detail.rect)
                    }
                }
                guard let image = NSImage(contentsOf: file),
                      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                      let base = rep.bitmapData else {
                    return XCTFail("\(tag)：读不回刚拍的帧")
                }
                let scale = Double(rep.pixelsWide) / Double(fixture.size.width)
                let pageLuma = Self.modalLuma(bytes: base, bytesPerRow: rep.bytesPerRow,
                                              xRange: Int(150 * scale)..<Int(710 * scale),
                                              yRange: Int(4 * scale)..<Int(12 * scale))
                // **两边同一条尺**：探针与卡片都走 `cardRowKinds` + `cardSegments` 找自己的
                // 材质顶与填充色。探针那一档如果改走"我知道它画在哪"的特殊路径，
                // 它就又不与被告同一颗尺子了（BACKLOG 104），而 R99 已经证明特殊路径会自己长出新 bug。
                // 每一臂的带子由**这一臂自己声明**：臂 2 的卡片长在详情列里（侧栏 148pt 之后），
                // 拿臂 0 的带子去扫它，"读不到卡片"就只是带子没盖住，而不是容器没画材质。
                let band = isProbe
                    ? Self.bandYFromColumn(Self.cardprobeBands[fixture.name]
                        ?? CGRect(x: 24, y: 24, width: 672, height: 100), columns)
                    : CGRect(x: 155, y: 60, width: 560, height: fixture.size.height - 60)
                let (rows, fill, modals) = Self.cardRowKinds(bytes: base, width: rep.pixelsWide,
                                                     height: rep.pixelsHigh,
                                                     bytesPerRow: rep.bytesPerRow,
                                                     rect: band, scale: scale,
                                                     pageLuma: pageLuma)
                cells += 1
                if isProbe {
                    // `CARD_PROBE_ARM`：150 这一整轮的答案由这几行交出 —— runner 上
                    // 没有 PNG 可下载（CI 不上传构件），所以**一臂一行的读数**必须自带
                    // "有没有第二层""找到几段""页底与前三名"，否则下一次还是要靠猜。
                    let segs = fill >= 0 ? Self.cardSegments(rows: rows, scale: scale).count : -1
                    // **墨行是这一臂的「带子盖住了内容」的证人**：文字与材质是两条独立的通道，
                    // 材质可以被容器吃掉（那正是 150 要问的），文字不会被。
                    // 所以 `墨行=0` 只有一种解释：**扫描带没盖住这一臂的卡片** ——
                    // 那时「材质=无」是仪器的形状，不是容器的答案。两种必须分得开，
                    // 否则这条实验会把「我框错了」读成「容器杀死了材质」（R68 / BACKLOG 104 那一族）。
                    //
                    // R103 换成 `textInkWitness`：上一版这里写的是 `rows.filter { $0 == .ink }`，
                    // 而 `rows` 是**材质那条通道**的中间量（`fill<0` 时整带都是 `.outside`，
                    // `.ink` 一个也不可能有）⇒ 证人在最需要它作证的那一臂（判据说没有材质）里必然报 0。
                    // R102 的 CI 上亮档臂 2 与暗档三臂就是被这个形状读成四朵红的（BACKLOG 150 追记）。
                    let witness = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                      height: rep.pixelsHigh,
                                                      bytesPerRow: rep.bytesPerRow, rect: band,
                                                      scale: scale, fill: fill, pageLuma: pageLuma)
                    // R121：**被告那一列自己**有多少墨。带子的矩形就是从这一列推出来的，
                    // 所以"列里有墨而带子没有"才是"我框错了"；"列里也没有、整帧却有"
                    // 才是"这一列在这台机器上没画"。两种的修法完全相反（150 卡的正是这个）。
                    let regionRect = columns.first(where: { $0.name.contains("详情") })?.rect ?? band
                    let regionWitness = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                            height: rep.pixelsHigh,
                                                            bytesPerRow: rep.bytesPerRow,
                                                            rect: regionRect, scale: scale,
                                                            fill: fill, pageLuma: pageLuma)
                    // 整窗那一遍提前到这里：它现在是这条判据的证人之一，不能再排在判据后面。
                    // 矩形**只声明一次**（R107）：witness 与 cardRowKinds 两遍必须扫同一块。
                    let wholeRect = CGRect(x: 0, y: 0, width: fixture.size.width,
                                           height: fixture.size.height)
                    let whole = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                    height: rep.pixelsHigh,
                                                    bytesPerRow: rep.bytesPerRow,
                                                    rect: wholeRect,
                                                    scale: scale, fill: fill, pageLuma: pageLuma)
                    let verdict = Self.cardprobeArmVerdict(pageInkRows: whole.rows,
                                                           regionInkRows: regionWitness.rows,
                                                           bandInkRows: witness.rows)
                    probeArmEvaluations += 1
                    // 结论行打在闸门之前（U-391 那一族）：只在会红的那一臂才说清原因，
                    // 等于让"没红"的那一臂没有读数可查。
                    emit("CARD_PROBE_ARM_VERDICT \(fixture.name) \(tag)"
                         + " 整帧墨行=\(whole.rows) 详情列墨行=\(regionWitness.rows)"
                         + " 带子墨行=\(witness.rows) ⇒ \(Self.verdictText(verdict))")
                    switch verdict {
                    case .judged:
                        judgedProbeArms += 1
                    case .bandMisplaced:
                        misplacedProbeArms += 1
                        XCTAssertGreaterThan(witness.rows, 0,
                                             "参照臂 \(fixture.name) \(tag) 在带子 \(Int(band.minX))..\(Int(band.maxX))pt × \(Int(band.minY))..\(Int(band.maxY))pt 里读到 0 行墨"
                                             + "，而同一趟里被告那一列（\(Int(regionRect.minX))..\(Int(regionRect.maxX))pt）读到 "
                                             + "\(regionWitness.rows) 行、整帧读到 \(whole.rows) 行"
                                             + "（证人自己扫字节，与材质那条通道无关；这一带里像素离两个背景的最大偏离是 "
                                             + "\(witness.maxDelta)，门限 60）"
                                             + " ⇒ 这一臂的扫描带没盖住它自己的内容，它的「材质=无」不能当结论。"
                                             + "改带子（`cardprobeBands`），不要改这条断言。")
                    case .regionUnpainted, .pageUnrendered:
                        // 不可判要有名字、要计数：把这一格静默算成"这一臂过去了"，
                        // 下一轮就会拿着 0 墨当答案（R119 正是这样把「帧太矮」写成成因的）。
                        blockedProbeArms += 1
                    }
                    // **反方向那一半的牙**（R103）：同一条尺在页面底那条参考带上必须一个像素都不认。
                    // 只配「带子里必须有字」这一头，另一头可以随便松 —— 证人松到恒真时它照样绿，
                    // 而恒真的证人比缺席的证人更坏（它会把「我框错了」洗成「这是答案」）。
                    // 参考带就是 `pageLuma` 的取数区（x150..710 × y4..12pt）：它要是被读出了字，
                    // 那坏的不是这一格，是整把尺的页底参照。
                    let strip = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                    height: rep.pixelsHigh,
                                                    bytesPerRow: rep.bytesPerRow,
                                                    rect: CGRect(x: 150, y: 4, width: 560, height: 8),
                                                    scale: scale, fill: fill, pageLuma: pageLuma)
                    XCTAssertEqual(strip.rows, 0,
                                   "页面底那条参考带被证人读出了 \(strip.rows) 行字"
                                   + "（它自己数出的最大偏离=\(strip.maxDelta)，门限 60）"
                                   + " ⇒ 要么证人太敏感（地板失效），要么 `pageLuma` 取的这一条本来就不干净；"
                                   + "两种都先修仪器，不要来改这条断言的 0。")
                    emit("CARD_PROBE_ARM \(fixture.name) \(tag) 材质=\(fill >= 0 ? "有" : "无")"
                         + " 卡片段=\(segs) 墨行=\(witness.rows) 墨像素=\(witness.pixels)"
                         + " 最大偏离=\(witness.maxDelta) 参考条墨行=\(strip.rows)"
                         + " 带子=\(Int(band.minX))..\(Int(band.maxX))pt"
                         + " " + Self.fillCandidatesLine(pageLuma: pageLuma, modals: modals))
                    // R107 / BACKLOG 157 的实验 (b)：**整窗**用同一颗尺再扫一遍。
                    // 为什么这一行能把成因分开：`最大偏离` 是**与地板无关**的量
                    //（它取这一带像素离两个背景的极值，不参与"够不够 60"的判断），于是
                    //   整窗最大偏离 ≥ 60 而带子只有个位数 ⇒ 内容画在带子之外 ⇒ 改带子；
                    //   整窗最大偏离也只有个位数 ⇒ 这棵视图在那台机器上根本没画东西；
                    // 再配上 (a) 那行分栏列包围盒，"详情列宽≈0"与"列在、但带子没盖住"也分得开。
                    // **R121 更正**：上面那条"整窗 ≥ 60 ⇒ 改带子"是不完整的 —— R119 的 CI 里
                    // 整窗 70 行墨全在侧栏那一列，详情列 0 行，带子已经铺满详情列，
                    // 按原句就会把"这一列没画"读成"我框错了"。现在这条规则被
                    // `cardprobeArmVerdict` 接管（证人从整窗换成被告那一列），整窗只留作
                    // 「这一页在这台机器上拍不拍得出」那一半的证人。
                    // 这一格**只打读数不判产品**（D-163），但它自带一条结构不变量当尺的自检 ——
                    // 整窗包含带子，所以整窗的极值与墨像素**不可能低于**带子的；反过来说明这一趟扫错了对象。
                    // `wholeRect` / `whole` 已上移到判据之前（R121：它现在同时是证人和读数）。
                    emit("CARD_PROBE_WHOLE \(fixture.name) \(tag) 整窗墨行=\(whole.rows)"
                         + " 整窗墨像素=\(whole.pixels) 整窗最大偏离=\(whole.maxDelta)"
                         + " 带子墨行=\(witness.rows) 带子最大偏离=\(witness.maxDelta)"
                         + " 帧=\(rep.pixelsWide)x\(rep.pixelsHigh)px 倍率=\(String(format: "%.1f", scale))x")
                    emit("CARD_PROBE_GEOMETRY \(fixture.name) \(tag) "
                         + (geometry.isEmpty ? "视图树没打出列" : geometry.joined(separator: " ")))
                    // R109 / 162：**每一列自己有多少墨**，按列各自的众数当背景量。
                    // 这一行就是为了让 runner 那一跑能一句话分开"详情没实例化"与"带子又放错"。
                    var columnLines: [String] = []
                    for (i, column) in columns.enumerated() {
                        let cBand = Self.clampBand(column.rect, scale: scale,
                                                   pixelsWide: rep.pixelsWide, pixelsHigh: rep.pixelsHigh)
                        let cPage = Self.modalLuma(bytes: base, bytesPerRow: rep.bytesPerRow,
                                                   xRange: cBand.x, yRange: cBand.y)
                        let cInk = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                       height: rep.pixelsHigh, bytesPerRow: rep.bytesPerRow,
                                                       rect: column.rect, scale: scale,
                                                       fill: cPage, pageLuma: cPage)
                        columnLines.append("列\(i):\(column.name)"
                            + "[x=\(String(format: "%.1f", column.rect.minX))..\(String(format: "%.1f", column.rect.maxX))"
                            + " 顶向下y=\(String(format: "%.1f", column.rect.minY))..\(String(format: "%.1f", column.rect.maxY))]"
                            + " 页底=\(cPage) 墨行=\(cInk.rows) 墨像素=\(cInk.pixels) 最大偏离=\(cInk.maxDelta)")
                    }
                    emit("CARD_PROBE_COLUMNS \(fixture.name) \(tag) "
                         + (columnLines.isEmpty ? "视图树没打出列" : columnLines.joined(separator: " ")))
                    // 详情列的**树侧**证人：列在不在是一回事，列里有没有可画的视图是另一回事。
                    // 这一行不判产品（D-163），它只把 150 的两种成因分开记账。
                    if isProbe {
                        emit("CARD_PROBE_DETAIL_TREE \(fixture.name) \(tag)"
                             + " 详情列文字视图=\(detailInventory.texts)"
                             + " 图像视图=\(detailInventory.images)"
                             + " 嵌套hosting=\(detailInventory.hosts)"
                             + " 列内视图数=\(detailInventory.inside)"
                             + (detailInventory.sample.isEmpty
                                ? " 样本=无" : " 样本=" + detailInventory.sample.joined(separator: " ; ")))
                        // R121 尺自检（D-174③ 的形状，但对象是我新加的这台仪表）。
                        // `列内视图数` 与 `样本` 走的是**同一条** `intersects` 判据的两个出口，
                        // 所以 `inside>0 而样本为空` 只能是仪器坏（前缀丢了 / append 被删），
                        // 不可能是产品的形状。本轮就差点把这条坏法当成产品结论用（U-405）：
                        // 第一版样本按遍历顺序取前 8，本机跑出来 8 条全是铺满整窗的容器，
                        // 数字照常报、证人一句话没说。红的时候要说"仪表坏了"，不要说"详情是空的"。
                        let witnessVerdict = (detailInventory.inside > 0 && detailInventory.sample.isEmpty)
                            ? "仪器坏" : "一致"
                        emit("CARD_PROBE_WITNESS \(fixture.name) \(tag)"
                             + " 列内视图数=\(detailInventory.inside) 样本数=\(detailInventory.sample.count)"
                             + " 上限=8 ⇒ \(witnessVerdict)")
                        if detailInventory.inside > 0 {
                            XCTAssertFalse(detailInventory.sample.isEmpty,
                                "CARD_PROBE_WITNESS_BROKEN \(fixture.name) \(tag)：详情列里数到 "
                                    + "\(detailInventory.inside) 个与列相交的视图，样本却是空的。"
                                    + "视图数与样本是同一条 `intersects` 的两个出口，两者对不上就是仪器坏了 "
                                    + "（R121 / U-405）—— 这一跑的 `样本=无` 不能被读成"
                                    + "「详情列里没有可画的视图」（150 要区分的正是这两件事）。"
                                    + "改 `columnSubviewInventory`，不要改这条断言。")
                        }
                    }
                    // 尺自检（D-174③ 的形状）：**带子必须与详情那一列有交集**。
                    // 它不判产品，只判"我扫的是不是我想扫的那一块" —— 红的时候说的是仪器坏了。
                    // 为什么不是"带子必须包含整列"：本轮实测带子是 x=170..720 而详情列是 148..720，
                    // 那 22pt 是分栏阴影（`_NSSplitViewShadowView` 148..160）+ 分隔线，
                    // 里面本来就没有内容；要求包含会把一条正确的带子判成红。
                    if let detail = columns.first(where: { $0.name.contains("详情") }) {
                        let overlap = min(band.maxX, detail.rect.maxX) - max(band.minX, detail.rect.minX)
                        XCTAssertGreaterThan(overlap, 0,
                            "\(fixture.name) \(tag)：带子 x=\(String(format: "%.1f", band.minX))"
                                + "..\(String(format: "%.1f", band.maxX))pt 与详情列"
                                + " x=\(String(format: "%.1f", detail.rect.minX)).."
                                + "\(String(format: "%.1f", detail.rect.maxX))pt 的交集是 "
                                + "\(String(format: "%.1f", overlap))pt ⇒ 带子整个放到了别的东西上，"
                                + "这一臂的「材质=无」不能当容器结论（157 / 162 的第三种坏法）。"
                                + "改 `cardprobeBands`，不要改这条断言。")
                    }
                    // 整窗那一遍**同时问材质**：(a) 行墨与 (b) 视图树包围盒只说明"有东西"，
                    // 而 150 问的是"那层填充还在不在"。所以整窗也要给出
                    // `材质=有/无` 与**填充行落在哪一段 y**（顶向下，pt）——
                    // 有了这两样，runner 上那一跑就能一句话定案：
                    //   整窗材质=有、填充行的 y 段与带子的 y 段不相交 ⇒ 带子放错了（改带子，不是容器的罪）；
                    //   整窗材质=有、且与带子相交 ⇒ 这一臂真的被容器吃掉了一部分，才轮到 150 说话；
                    //   整窗材质=无 ⇒ 那台机器上这棵树的第二层墨根本没落地（并回 147 那一族）。
                    let (wholeRows, wholeFill, _) = Self.cardRowKinds(bytes: base,
                                                                      width: rep.pixelsWide,
                                                                      height: rep.pixelsHigh,
                                                                      bytesPerRow: rep.bytesPerRow,
                                                                      rect: wholeRect,
                                                                      scale: scale, pageLuma: pageLuma)
                    var fillTop = -1.0, fillBottom = -1.0
                    if wholeFill >= 0 {
                        for (i, kind) in wholeRows.enumerated() {
                            if kind == CardRowKind.card {
                                if fillTop < 0 { fillTop = Double(i) / scale }
                                fillBottom = Double(i + 1) / scale
                            }
                        }
                    }
                    // U-343（本轮改措辞）：以前这行同时打 `整窗材质=有` 与 `整窗填充行y=-1.0..-1.0pt`，
                    // 看着自相矛盾。两个量其实来自同一次 `cardRowKinds` 的**两个不同返回**：
                    // `wholeFill` 是"候选填充档的个数"（≥0 就报"有"），而 y 段要真有被分类成卡片的**行**才有值。
                    // 于是"有个候选档但没有成行的卡片"这一格会打成 有 / -1 —— 不是矛盾，是措辞把两件事说成了一件。
                    // 现在把两个量分开命名并各带自己的数，读的人不会再要求它们互相蕴含。
                    let cardRowCount = wholeRows.filter { $0 == CardRowKind.card }.count
                    emit("CARD_PROBE_WHOLE_FILL \(fixture.name) \(tag) 整窗填充候选档=\(wholeFill)"
                         + " 整窗卡片行数=\(cardRowCount)"
                         + " 整窗卡片行y=\(String(format: "%.1f", fillTop))..\(String(format: "%.1f", fillBottom))pt"
                         + " 带子y=\(String(format: "%.1f", band.minY))..\(String(format: "%.1f", band.maxY))pt"
                         + " 带子材质=\(fill >= 0 ? "有" : "无")"
                         + " 分栏内容溢出=\(String(format: "%.1f", splitOverflow))pt")
                    // **实验对象自己必须在帧内**（R107 / 157 的堵点）：溢出 > 1pt 意味着
                    // 帧看到的是"从一块比夹具高的内容里裁出来的一条窗口"，而裁在哪儿**取决于窗口装饰高度**
                    // ——那正是 157 在 runner 上读到的形状（`墨行=0 最大偏离=2`）与"容器吃掉材质"混淆的来源。
                    // 这一条红说的是**实验坏了**，不是产品坏了；消息里必须这样写，否则下一轮会有人去改产品。
                    XCTAssertLessThanOrEqual(splitOverflow, 1.0,
                        "\(fixture.name) \(tag)：分栏的内容盒比夹具高出 \(String(format: "%.1f", splitOverflow))pt"
                            + " ⇒ 这张帧拍的是「从一块更高的内容里裁出来的一条窗口」，"
                            + "而裁在哪儿取决于窗口装饰高度（本机实测：夹具 140pt 时溢出 85pt，改成 300pt 后为 0）。"
                            + "这时候『带子里 0 行墨』不能读成『容器吃掉了材质』（BACKLOG 157），"
                            + "也不许反过来去改产品 —— 先把实验对象放回帧内。")
                    XCTAssertGreaterThanOrEqual(whole.maxDelta, witness.maxDelta,
                        "\(fixture.name) \(tag)：整窗的最大偏离 \(whole.maxDelta) 低于带子的 \(witness.maxDelta)"
                        + " ⇒ 整窗**包含**这条带子，极值不可能更小 —— 这一趟整窗扫的不是同一份字节"
                        + "（rect / bytesPerRow / 缓冲区身份其中一处错了）。这是给新读数装的尺自检，不是产品判据。")
                    XCTAssertGreaterThanOrEqual(whole.pixels, witness.pixels,
                        "\(fixture.name) \(tag)：整窗墨像素 \(whole.pixels) 少于带子的 \(witness.pixels)（同上）")
                }
                if fill >= 0 {
                    materialCells += 1
                    // R101 / 读 R100 的 CI（run 38927822527）：这一格把**被告**与**参照**分开数。
                    // 上一版只数一个 `materialCells`，而 runner 上它是 2 —— 那两格全是参照
                    //（`cardprobe-groupbox-default` 亮档量出了 6.0pt 内缩），被告 24 格全报
                    // "读不到卡片"。于是 `measured.count >= min(16, materialCells)` 变成
                    // "0 ≥ 2" ⇒ 红，而 skip 那一格（`materialCells == 0`）没响 ——
                    // **闸门与地板吃了不同的量，闸门就白装**（D-161 只修了一半：
                    // 它把地板从上游推，却没问"上游那一格里哪些是被告"）。
                    if isProbe { controlMaterial += 1 } else { defendantMaterial += 1 }
                }
                // 与纵向那一格**同一句打印**（`fillCandidatesLine` 是纯函数，两处共用）：
                // 横向这把尺是本轮新写的，它和纵向那把在 runner 上必须报同一种形状，
                // 否则"两把尺问同一件事而结论相反"就又得靠猜（R87 那一族的分配规则）。
                if fill < 0 {
                    emit("CARD_FILL_CANDIDATES \(fixture.name) \(tag) "
                         + Self.fillCandidatesLine(pageLuma: pageLuma, modals: modals))
                }
                // **两种成因必须分开报**（R102 / BACKLOG 150 的前置）：
                // ① `fill < 0` —— 这一带**根本没有第二层**（runner 上那 24 格被告就是这个形状）；
                // ② `fill >= 0` 但 `cardSegments` 找不到段 —— **有材质却没量到卡片**。
                // 上一版两种共用一句「这一带读不到卡片」，于是 runner 那一台报的
                // `有材质=2 而 未判=25` 里，那两格印出来的原因恰好是**假的那一句**（150 的诚实记账）。
                // 角色也带上：`参照` 那一格是仪器，`被告` 那一格才是产品 ——
                // 没有角色就分不清"147 的通道问题"与"150 要查的容器问题"各是谁。
                let role = isProbe ? "参照" : "被告"
                guard fill >= 0 else {
                    declined.append("\(fixture.name) \(tag)[\(role)]=这一带没有第二层（fill=-1）")
                    continue
                }
                guard let first = Self.cardSegments(rows: rows, scale: scale).first else {
                    declined.append("\(fixture.name) \(tag)[\(role)]=有材质但找不到卡片段（fill=\(fill)）")
                    continue
                }
                let cardTopPx = Int(band.minY * scale) + first.top
                let cardBottomPx = Int(band.minY * scale) + first.bottom + 1
                // 材质问中点那一行（直边），墨问整张卡片内沿（避开上下边框那 1px）。
                let mid = (cardTopPx + cardBottomPx) / 2
                let xStart = Int(band.minX * scale)
                let flags = Self.columnFlags(bytes: base, bytesPerRow: rep.bytesPerRow,
                                             xRange: xStart..<rep.pixelsWide,
                                             materialYRange: (mid - 1)..<(mid + 2),
                                             inkYRange: (cardTopPx + 3)..<(cardBottomPx - 3),
                                             fill: fill, pageLuma: pageLuma, inkGate: 60)
                // `minRun` 取 2pt：只要"连续两列是材质"就算左沿。为什么不是原来那 40pt：
                // 卡片左沿到第一个字形之间只有 5.5pt，任何比它大的 run 都会跳过真正的边，
                // 而圆角那一族假边已经被"中点那一行"排掉了，不需要用长度兜底。
                guard let leftRaw = Self.firstSpanStart(columns: flags.material,
                                                        minRun: Int(2 * scale)) else {
                    declined.append("\(fixture.name) \(tag)[\(role)]=读不到卡片左沿")
                    continue
                }
                let left = xStart + leftRaw
                guard let inkRaw = Self.firstInkColumn(columns: flags.ink, from: leftRaw) else {
                    declined.append("\(fixture.name) \(tag)[\(role)]=左沿以右读不到墨")
                    continue
                }
                let ink = xStart + inkRaw
                let inset = Double(ink - left) / scale
                if isAnchorProbe {
                    control[tag] = inset
                    probeBezel[tag] = Double(left) / scale
                } else if isProbe {
                    armInsets["\(fixture.name) \(tag)"] = inset
                } else {
                    measured["\(fixture.name) \(tag)"] = inset
                }
                let leftPt = String(format: "%.1f", Double(left) / scale)
                let inkPt = String(format: "%.1f", Double(ink) / scale)
                let insetPt = String(format: "%.1f", inset)
                let topPt = String(format: "%.1f", Double(cardTopPx) / scale)
                emit("CARD_INSET \(fixture.name) \(tag) 卡片顶=\(topPt)pt"
                     + " 卡片底=\(String(format: "%.1f", Double(cardBottomPx) / scale))pt"
                     + " 材质行=\(mid - 1)..\(mid + 2)px"
                     + " 卡片左沿=\(leftPt)pt 第一处墨=\(inkPt)pt 内缩=\(insetPt)pt")
            }
        }
        for key in armInsets.keys.sorted() {
            emit("CARD_PROBE_ARM_INSET \(key) 内缩=\(String(format: "%.1f", armInsets[key]!))pt")
        }
        do {
            var expected: Set<String> = ["cardprobe-groupbox-default", "cardprobe-scroll-groupbox"]
            if #available(macOS 13.0, *) { expected.insert("cardprobe-split-groupbox") }
            let declared = Set(fixtures(appearance: .aqua).map { $0.name }
                                 .filter { $0.hasPrefix("cardprobe-") })
            XCTAssertEqual(declared, expected,
                           "容器梯子的臂与名单不一致：只在夹具里的是 \(declared.subtracting(expected).sorted())，"
                           + "只在名单里的是 \(expected.subtracting(declared).sorted())"
                           + " ⇒ 加一臂必须同时给它带子与读数（150 的答案靠读数，不靠图）；"
                           + "撤一臂要把 150 的对应分支一起收掉")
        }
        let controlText = control.keys.sorted().map {
            "\($0)=\(String(format: "%.1f", control[$0]!))pt"
        }.joined(separator: " ")
        emit("CARD_INSET_SUMMARY 系统参照 \(controlText) 卡片数=\(measured.count) 未判=\(declined.count)")
        emit("CARD_INSET_ALL " + measured.keys.sorted().map {
            "\($0)=\(String(format: "%.1f", measured[$0]!))"
        }.joined(separator: " "))
        if !declined.isEmpty { emit("CARD_INSET_DECLINED " + declined.joined(separator: " ")) }
        emit("CARD_INSET_CAPABILITY 候选=\(cells) 有材质=\(materialCells)"
             + "（被告=\(defendantMaterial) 参照=\(controlMaterial)）"
             + " 量到=\(measured.count) 未判=\(declined.count)")
        // R121 / BACKLOG 150：参照臂的四种出口各自计数，并且**必须加得回来**。
        // 这条恒等式是这台新仪表自己的地板：如果哪天有人在 switch 里加了一个不计数就返回的
        // 分支，"不可判"就会变成静默通过 —— 而 150 这一整轮卡住我的正是这种静默
        // （R119 我把"这一臂读不到墨"直接写成成因"帧太矮"，没有第三个词可说）。
        emit("CARD_PROBE_CAPABILITY 参照臂=\(probeArmEvaluations)"
             + " 可判=\(judgedProbeArms) 框错红=\(misplacedProbeArms)"
             + " 不可判=\(blockedProbeArms)"
             + "（拆：详情列0墨/整帧0墨，逐臂见 CARD_PROBE_ARM_VERDICT）")
        XCTAssertEqual(probeArmEvaluations, judgedProbeArms + blockedProbeArms + misplacedProbeArms,
                       "参照臂数了 \(probeArmEvaluations) 次，三个出口只加回 "
                           + "\(judgedProbeArms + blockedProbeArms + misplacedProbeArms) 次"
                           + " ⇒ 有一臂掉在了 switch 外面（仪器坏，不是产品坏）。R121。")
        // **绝对锚点**（M559 那一刀教出来的）：参照那一格的左沿必须落在夹具自己声明的
        // `.padding(24)` 上。等式判据看不见"整把尺一起偏"，这一格看得见。
        // 它排在所有闸门**之前**：这一格要判的是"仪器有没有错位"，与"这台机器画不画得出材质"无关，
        // 也不该被后者的 skip 吃掉。容差 1pt = 两像素，给抗锯齿与 2x 量化留的。
        for tag in ["light", "dark"] {
            guard let bezel = probeBezel[tag] else { continue }
            XCTAssertEqual(24.0, bezel, accuracy: 1.0,
                           "参照夹具声明的是 `.padding(24)`，尺却把卡片左沿读在 "
                               + "\(String(format: "%.1f", bezel))pt ⇒ 仪器自己错位了"
                               + "（圆角那一族：材质带压在卡片顶时读的是弧线不是直边，"
                               + "本轮修之前实测读成 31.5pt）。等式那一格对这种错法免疫，这一格不免疫。")
        }
        // 两件事分开判（R101 / 读 R100 的 CI 学到的那一格）：
        // ① **对照缺席**：参照一格都没量出来，而被告却有材质 ⇒ 等式没有对面，不许报干净。
        //    M558（把 `isProbe` 关掉）红在这一格 —— 它撤的是对照，不是对象。
        if controlMaterial == 0 && defendantMaterial > 0 {
            XCTFail("系统参照一张都没量出来，而 \(defendantMaterial) 格被告卡片有材质"
                    + " ⇒ 这条判据没有对照，不许报干净（借来的常数没有这个性质）")
        }
        // ② **没有对象**：被告格里一格材质都读不到 ⇒ 这台机器看不见这扇窗口的卡片，等式无从判起。
        //    runner 就是这个形状（24 格全报"读不到卡片"，而参照亮档量得出 6.0pt）⇒ 响成 skip，
        //    不是永久红（R99 那条常量地板 8 的伤），也不是静默通过（BACKLOG 43 那一族）。
        if defendantMaterial == 0 {
            throw XCTSkip("这台机器拍不出**被告**的卡片材质：\(cells) 格候选里被告全报「读不到卡片」"
                              + "（参照有 \(controlMaterial) 格量到了 ⇒ 不是尺瞎，是这扇窗口的材质层"
                              + "在这台机器上不显）。横向内缩这条判据没有对象，见 BACKLOG 147。")
        }
        // ②b **按档切片的盲区**（R157 / BACKLOG 196）。runner 的形状不是"被告全读不到"：
        //    `CARD_INSET_CAPABILITY 候选=32 有材质=6（被告=2 参照=4） 量到=1 未判=29` ——
        //    那唯一量到的一格是 `settings-shortcuts-recording light`，**暗档一格都没有**。
        //    旧出口 ② 问的是"有没有材质"（`defendantMaterial == 0`），而 runner 有 2 格材质
        //    （两格是 `fill=60 有材质但找不到卡片段`）⇒ 谓词落在错的量上，于是它没 skip、
        //    红了 3 格（`参照只有 ["light"]`、`被告读到 2 格材质却只量到 1 格内缩`、`未判 29`）。
        //    现在问的是本条判据真正需要的那个对象：**每一档都得至少有一格被告量到卡片段**，
        //    否则那一档的等式在这台机器上无从判起。这是**读数**（两档各自的段数），不是覆盖率通道；
        //    前提由同一次运行量出来，放不掉的是"那一档的等式"，不是整条判据（D-170：能力行排在 skip 之前）。
        let insetBandsLight = measured.keys.filter { $0.hasSuffix(" light") }.count
        let insetBandsDark = measured.keys.filter { $0.hasSuffix(" dark") }.count
        emit("CARD_INSET_BANDS light=\(insetBandsLight) dark=\(insetBandsDark)"
             + "（被告里各档量到卡片段的格数；候选=\(cells) 有材质=\(materialCells)）")
        if insetBandsLight == 0 || insetBandsDark == 0 {
            emit("CARD_INSET_NOT_RUN=1 被告有一档整档量不到卡片段（light=\(insetBandsLight) dark=\(insetBandsDark)，"
                 + "被告有材质=\(defendantMaterial) 参照有材质=\(controlMaterial) 未判=\(declined.count)）"
                 + " ⇒ 那一档的半透明材质在这台机器上不合成，等式没有对象：不是通过，也不是产品缺陷。见 BACKLOG 147 / 196。")
            throw XCTSkip("这台机器在某一档上拍不出**可判的卡片段**（light=\(insetBandsLight) dark=\(insetBandsDark)）"
                              + " ⇒ 横向内缩那条等式在那一档没有对象。本机两档各有十几格，所以本机照判。"
                              + "（读数在上一行 `CARD_INSET_NOT_RUN=1`，见 BACKLOG 196）")
        }
        // ③ **参照必须亮暗两档各一条**（这一条 R100 的 CI 上红过，红在 `("2") is not equal to ("1")`；
        //    R101 重写角色分账时我把它**整条弄丢了** —— 不是决定撤掉，是编辑掉的，
        //    由收尾那次「HEAD 的每一行是否都还在」的多重集包含检查抓回来，见 U-289）。
        //    它现在排在 skip **之后**：runner 那一台被告没有材质 ⇒ 等式本来就不判，
        //    在那里红一条"参照只亮了一档"说的仍不是产品（R100 那三朵红的原样）。
        //    放在本机这一侧才有意义：本机两档都拍得出参照，缺哪一档都是夹具或渲染坏了。
        XCTAssertEqual(control.count, 2,
                       "系统参照必须亮暗两档各一条（借来的常数没有这个性质）"
                       + " ⇒ 现在只有 \(control.keys.sorted())：夹具少亮一档，等式就是拿一档去比两档")
        // 这一格先只钉"这把尺至少量到了东西"：地板从**被告那一关**推，不从名单推。
        XCTAssertGreaterThanOrEqual(measured.count, min(16, defendantMaterial),
                                    "被告读到 \(defendantMaterial) 格材质却只量到 \(measured.count) 格内缩"
                                    + " ⇒ 有对象没量到（地板从材质那一关推，不从名单推）")
        // 未判名单必须**小**：它原来装着 5 格，其中两格（`login-unsupported` 暗档、
        // `login-failed`）是"禁用态读不到墨"—— 那是上一段那条 26pt 带子的错，
        // 不是产品的错（换成整张卡片内沿后它们量出了 5.0pt）。
        // R101 起「统计」两档也有卡片了（BACKLOG 131 结案），所以这一格从 6 收紧到 4：
        // 剩下的应当只有"卡片贴到窗口底"那一族。
        XCTAssertLessThanOrEqual(declined.count, 4,
                                 "未判 \(declined.count) 格：\(declined.joined(separator: " "))")
        // **等式，不是阈值**：BACKLOG 138 那句"macOS 通常 16–20pt"从来没有出处，
        // 而本轮量出来的系统自己那一档是 5.5pt（亮暗两档同一个数，且 12..64 的墨门限都给出
        // 同一个数 —— 见 `.scratch/motion-audit-2/r100_gate_sweep.txt`）。
        // 所以判据写成"与系统参照同档"，而不是"≥16"：后者会把产品推得**更不原生**，
        // 而那正是这条目标（优先系统 API / 原生材质）的反方向。
        // 1.0pt 的容差是给抗锯齿留的：卡片左沿与第一个字形各自有 ±0.5pt 的量化误差。
        //
        // **首墨是图标的那一格不能套这条等式**（R101 新撞出来的，量出来的数在下面的串里）：
        // 这把尺问的是"卡片左沿到第一处墨"，而空态那一臂的第一处墨是 `StateLine` 的托盘符号。
        // 同一张 `GroupBox`、同一份前导留白，图标那一列的**字形侧边距**比文字多约 1pt
        //（实测：亮 6.5 对文字参照 5.0 = +1.5；暗 6.5 对 5.5 = +1.0），
        // 而它旁边那一臂（`settings-stats-populated`，首墨是文字）量到 5.5 = 与参照同档。
        // 处理方式**不是**放宽等式的容差（那会把其余 23 格一起放宽），也不是把它塞进未判名单
        //（那是把一条能判的格记成"没判"）—— 换成给这一格一条**有界的**替代判据：
        // 图标 bearing 必须落在 [+0.5, +2.0]。产品如果真改了前导留白，这一格照样会红；
        // 而如果这一屏哪天首墨变成文字，`>= +0.5` 也会红，逼下一次把名册改掉。
        let iconFirstCells: Set<String> = ["settings-stats light", "settings-stats dark"]
        for (key, inset) in measured.keys.sorted().map({ ($0, measured[$0]!) }) {
            let tag = key.hasSuffix("dark") ? "dark" : "light"
            guard let want = control[tag] else {
                XCTFail("\(key)：参照缺席（\(tag) 档没量到）⇒ 这一格没有资格报干净")
                continue
            }
            if iconFirstCells.contains(key) {
                let delta = inset - want
                XCTAssertGreaterThanOrEqual(delta, 0.5,
                                            "\(key) 的首墨是空态图标，量到 \(inset)pt 对文字参照 "
                                            + "\(want)pt = \(String(format: "%+.1f", delta))pt，"
                                            + "低于 +0.5 ⇒ 图标的侧边距没理由比文字还小：先怀疑这把尺"
                                            + "（或者这一屏的首墨已经变成文字了 —— 那就把这一格从名册里删掉）")
                XCTAssertLessThanOrEqual(delta, 2.0,
                                         "\(key) 的首墨是空态图标，量到 \(inset)pt 对文字参照 "
                                         + "\(want)pt = \(String(format: "%+.1f", delta))pt，高于 +2.0"
                                         + " ⇒ 这一屏的前导留白与其余卡片不是同一档（本轮 131 刚把它们对齐）")
                emit("CARD_INSET_ICON_FIRST \(key) 内缩=\(String(format: "%.1f", inset))"
                     + " 文字参照=\(String(format: "%.1f", want)) 侧边距=\(String(format: "%+.1f", delta))")
                continue
            }
            XCTAssertEqual(inset, want, accuracy: 1.0,
                           "\(key) 的卡片内缩 \(String(format: "%.1f", inset))pt"
                               + " 与系统 `GroupBox` 自己那一档 \(String(format: "%.1f", want))pt"
                               + " 差超过 1pt。要么产品改掉了系统默认内缩（这扇窗口里六张卡片"
                               + "必须同一档），要么这把尺又瞎了（R99/R100 连着两轮都是后者）——"
                               + "先读 CARD_INSET 那几行的『卡片左沿/第一处墨』再决定改哪一边。")
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
        // R97：`cardRhythm` 现在只面对**一张**卡片 —— 传进来的第一行就是卡片顶。
        // 所以这些合成件不再带首末的 `.outside`（那归 `cardSegments` 那一支管）。
        // ① 边 14 / 内侧 14 ⇒ 同一档
        let even = rows([(.card, 14), (.ink, 10), (.card, 14), (.line, 1),
                         (.card, 14), (.ink, 10), (.card, 14)])
        let a = Self.cardRhythm(rows: even, scale: 1)
        XCTAssertEqual(a.dividers, 1)
        same(a.edges, [14, 14], "均匀那张卡片：四边")
        same(a.gaps, [14, 14], "均匀那张卡片：分隔线两侧")
        // ② 边 2 / 内侧 14 ⇒ R95 那个缺陷的形状
        let tight = rows([(.card, 2), (.ink, 10), (.card, 14), (.line, 1),
                          (.card, 14), (.ink, 10), (.card, 2)])
        let b = Self.cardRhythm(rows: tight, scale: 1)
        same(b.edges, [2, 2], "边距没补那张：四边")
        same(b.gaps, [14, 14], "边距没补那张：分隔线两侧")
        XCTAssertGreaterThan((b.edges + b.gaps).max()! - (b.edges + b.gaps).min()!, 3.0,
                             "这条合成件必须**能被**管线判据判红，否则那条断言是恒真的")
        // ③ 卡片中间夹着一段页面底（`TextField` 的内芯）：边距仍按"墨到边"算，
        //    而且不许因为这段空白就少算一条分隔线。
        let withField = rows([(.card, 14), (.ink, 10), (.card, 6), (.outside, 24), (.card, 6),
                              (.line, 1), (.card, 14), (.ink, 10), (.card, 14)])
        let f = Self.cardRhythm(rows: withField, scale: 1)
        same(f.edges, [14, 14], "卡片里有一块白色输入框：四边仍按墨算")
        XCTAssertEqual(f.dividers, 1, "输入框那段空白不许把线吞掉")
        // ④ 一张卡片里全是线、没有墨 ⇒ 拒绝给数，并且说清是哪一种拒绝
        let noInk = rows([(.card, 5), (.line, 1), (.card, 5)])
        let g = Self.cardRhythm(rows: noInk, scale: 1)
        XCTAssertTrue(g.edges.isEmpty, "没有墨就没有『边距』这个对象")
        XCTAssertEqual("卡片里没有一行被判成墨 ⇒ 尺没压住字", g.declined,
                       "拒绝给数还不够，还得说清是哪一种拒绝")
    }

    /// 「一行算什么」的真值表（R97）：四种身份各钉一格，门槛的出处见 `cardRowKind`。
    ///
    /// 这一支存在的理由是一条**假红**：`settings-privacy-excluded` 亮档报
    /// "末条墨离卡片底 8.0pt"，而 python 独立复算是 14.0pt —— 差在旧规则拿
    /// "这一行的众数离页面底 ≤3"当"在卡片外"，而卡片填充与页面底只差一个色档（244 vs 252）。
    func testCardRowKindReadsMaterialNotModal() {
        let width = 1120   // 本机：带子 560pt × scale 2
        // ① 卡片里的普通行：绝大多数像素是卡片材质
        XCTAssertEqual(.card, Self.cardRowKind(cardRun: 1048, ink: 0, line: 0, width: width))
        // ② 输入框那一行：白色内芯占了中间，但右侧那一大片仍然是卡片（实测最长一段 518）
        //    ⇒ **不能**算卡片外，否则一张卡片被自己的控件切断
        XCTAssertEqual(.card, Self.cardRowKind(cardRun: 518, ink: 0, line: 74, width: width),
                       "518/1120 = 46% ⇒ 这一行当然还在卡片里")
        // ②b 一颗按钮所在的行（实测最长一段 152 = 14%）⇒ 卡片外。
        //     这一格是本轮那条**假红**的证人：按钮曾被当成一张 23.5pt 的卡片，
        //     量出 `边距 6.5/5.5、内侧 0.0/0.0`。
        XCTAssertEqual(.outside, Self.cardRowKind(cardRun: 152, ink: 24, line: 96, width: width),
                       "一颗 76pt 宽的按钮横不过带子 ⇒ 它不是卡片")
        // ③ 两张卡片之间：一段卡片材质都没有
        XCTAssertEqual(.outside, Self.cardRowKind(cardRun: 0, ink: 0, line: 1120, width: width),
                       "整行都是页面 ⇒ 卡片外（`line` 那一格故意填满，验的是它排在后面）")
        // ④ 墨行与分隔线行各自还是原来的档
        XCTAssertEqual(.ink, Self.cardRowKind(cardRun: 1048, ink: 298, line: 0, width: width))
        XCTAssertEqual(.line, Self.cardRowKind(cardRun: 1046, ink: 0, line: 1000, width: width))
        // ⑤ 地板两侧：30% 之下算卡片外，之上算卡片里。
        //    实测三个数是 14%（按钮）/ 46%（输入框行）/ 94%（普通行）⇒ 地板取在 14 与 46 之间，
        //    离两边都远；这里钉的是"跨不过地板就不算卡片"这一侧。
        XCTAssertEqual(.outside, Self.cardRowKind(cardRun: 335, ink: 0, line: 0, width: width),
                       "335/1120 = 29.9% ⇒ 差一点点也不算卡片里")
        XCTAssertEqual(.card, Self.cardRowKind(cardRun: 336, ink: 0, line: 0, width: width),
                       "336/1120 = 30.0% ⇒ 正好踩线要算卡片里（地板是闭区间，别让它两头都开放）")
    }

    /// 存在性墨证人的真值表（R103 / 把 R102 那四朵「暗档 墨行=0」的假红查到底之后的产物）。
    ///
    /// 每一格的数都来自本机量，不来自印象：
    /// 页底与卡片填充 亮 252/244、暗 28/36（`/tmp/r102_shots` 那六张参照臂帧）；
    /// 标题档与说明档 亮 39/139、暗 235/140（R24 的 `testTextInkGateTruthTable` 那一批）；
    /// 平涂控件 亮 222、暗 55（同一格）；分隔线 亮 220、暗 84（R102 的 `前三` 读数里那一档 2 行）。
    func testTextInkWitnessIsAnExistenceJudgeWithPairedFloors() {
        let lightPage = 252, lightFill = 244
        let darkPage = 28, darkFill = 36
        func flat(_ value: Int, _ n: Int = 40) -> [Int] { Array(repeating: value, count: n) }
        // ① 页底整行 / ② 卡片填充整行 ⇒ 证人都必须闭嘴（这是地板的下沿）
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(lightPage), fill: lightFill,
                                          pageLuma: lightPage), "页底整行不许算字")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(darkPage), fill: darkFill,
                                          pageLuma: darkPage), "暗档页底整行不许算字")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(lightFill), fill: lightFill,
                                          pageLuma: lightPage), "卡片填充不许算字")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(darkFill), fill: darkFill,
                                          pageLuma: darkPage), "暗档卡片填充不许算字")
        // ③ 平涂控件与分隔线：R102 那把旧尺最容易在这里翻（它们都在带子里、都不是页底）
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(222), fill: lightFill, pageLuma: lightPage),
                       "亮档录制框/药丸的平涂底（离两个背景各 22/30）不许算字")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(55), fill: darkFill, pageLuma: darkPage),
                       "暗档控件平涂底（离两个背景各 19/27）不许算字")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(220), fill: lightFill, pageLuma: lightPage),
                       "亮档分隔线那一档（24/32）不许算字 ⇒ 否则一条线就能给一臂作证")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(84), fill: darkFill, pageLuma: darkPage),
                       "暗档分隔线那一档（48/56）不许算字（这一档在 R102 的 `前三` 里就有 2 行）")
        // ④ 标题与说明两档，两档外观各自都要算字（方向无关这件事就是这一格）
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: flat(39), fill: lightFill, pageLuma: lightPage),
                      "亮档标题（离两个背景 205/213）必须算字")
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: flat(139), fill: lightFill, pageLuma: lightPage),
                      "亮档说明档（105/113）必须算字 —— 它是 `.secondary`，不是噪声")
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: flat(235), fill: darkFill, pageLuma: darkPage),
                      "暗档标题（199/207）必须算字")
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: flat(140), fill: darkFill, pageLuma: darkPage),
                      "暗档说明档（104/112）必须算字")
        // ⑤ 一行里只有几个这样的像素（抗锯齿亮点）⇒ 不算（地板的上沿那一侧由 ⑥⑦ 钉）
        var sparse = flat(darkFill, 40)
        for i in 0..<5 { sparse[i] = 235 }
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: sparse, fill: darkFill, pageLuma: darkPage),
                       "5 个墨像素不算一行有字")
        // ⑥/⑦ 地板成对：6 个就算，5 个就不算（同一条规则的两边各钉一格，见 R38「阈值要成对」）
        var six = flat(darkFill, 40)
        for i in 0..<6 { six[i] = 235 }
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: six, fill: darkFill, pageLuma: darkPage),
                      "6 个正好踩地板 ⇒ 算（地板是闭区间）")
        // ⑧ **本轮真正修掉的那一格**：`fill = -1`（判据宣布这一带没有卡片）时证人仍然要有牙。
        //    上一版吃 `cardRowKinds` 的逐行身份，而 fill<0 时整带都是 `.outside` ⇒ 永远读不到墨，
        //    于是它对「材质=无」那一臂永远只能报 0 —— 恰恰是那一臂最需要有人作证。
        XCTAssertTrue(Self.rowHasTextInk(rowLumas: six, fill: -1, pageLuma: darkPage),
                     "没有卡片填充可参照时，字仍然离页底足够远 ⇒ 证人必须照样亮")
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: flat(darkPage), fill: -1, pageLuma: darkPage),
                       "同一种缺参照的形状下，页底仍然不许算字（负对照不许跟着失效）")
        // ⑨ 地板非正 ⇒ 这条判据自己失效，不能当证人（M573 那一刀钉的就是这一格）
        XCTAssertFalse(Self.rowHasTextInk(rowLumas: sparse, fill: darkFill, pageLuma: darkPage,
                                          minPixels: 0),
                       "minPixels=0 时任何一行都算有字 ⇒ 恒真的证人不叫证人，判据自己拒收")
        // ⑩ 逐像素距离那一格单独钉：`fill` 缺席时只剩页底一个参照，而不是拿 -1 去比距离。
        //     （写反成 `abs(luma - fill)` 的话，页底像素会得到 |28-(-1)|=29 这种**假的高偏离**，
        //     于是整带每一行都成为墨 —— 一版看起来完全正常的恒真证人。）
        XCTAssertEqual(0, Self.inkDelta(luma: darkPage, fill: -1, pageLuma: darkPage),
                       "没有卡片时参照只能是页底：页底像素的偏离是 0，不是 |28-(-1)|=29")
        XCTAssertEqual(0, Self.inkDelta(luma: darkFill, fill: darkFill, pageLuma: darkPage),
                       "有卡片时取两个参照里更近的那个 ⇒ 卡片自身的偏离是 0")
    }

    /// 「一段 = 一张卡片」的真值表（R97）：一个扫描带里可以纵向放好几张卡片。
    func testCardSegmentsSplitsCardsAndKeepsTallOnes() {
        // ① 两张卡片，中间 20 行页面底 ⇒ 必须切成两段
        let two = Array(repeating: CardRowKind.card, count: 30)
            + Array(repeating: .outside, count: 20)
            + Array(repeating: .card, count: 30)
        let segs = Self.cardSegments(rows: two, scale: 1)
        XCTAssertEqual(segs.count, 2, "两张卡片不许并成一张：那会把边距量成两张的外框")
        XCTAssertEqual(segs.map { $0.bottom - $0.top + 1 }, [30, 30])
        // ② 太短的段不算卡片（那条 1pt 的 `Divider()` 就是这么被挡掉的）
        let line = Array(repeating: CardRowKind.outside, count: 100)
            + [.line, .line] + Array(repeating: .outside, count: 100)
        XCTAssertTrue(Self.cardSegments(rows: line, scale: 2).isEmpty,
                      "2px=1pt 的一段没到 20pt 的地板 ⇒ 不当卡片")
        // ③ 恰好 20pt 的一段算（地板之下宁可不判，地板之上不许漏）
        let edge = Array(repeating: CardRowKind.outside, count: 10)
            + Array(repeating: .card, count: 40) + Array(repeating: .outside, count: 10)
        XCTAssertEqual(Self.cardSegments(rows: edge, scale: 2).count, 1)
        // ④ 一整带都是页面 ⇒ 零段
        XCTAssertTrue(Self.cardSegments(rows: Array(repeating: .outside, count: 200), scale: 2).isEmpty)
    }

    /// 「什么算一张卡片」的真值表（R97）。
    ///
    /// 这一格存在的理由是一条**说反了的读数**：R96 里 `settings-stats-populated` 被报成
    /// "卡片里没有一行被判成墨 ⇒ 尺没压住字"，而那一屏源码里根本没有 `GroupBox`。
    /// 尺认出的那张"卡片"是一条 1pt 的 `Divider()`（本机实测：y=271.0 起、2px 高、
    /// 那一行 94% 的像素在 228 档 —— 见 `.scratch/motion-audit-2/r97_stats_readings.log`）。
    /// 地板 20pt 的出处写在 `cardFill` 的文档串里（真卡片 176.5–217.0pt vs 那条线 1.0pt）。
    func testCardFillNeedsAStableBandNotTheFirstDifferingRow() {
        let page = 252
        // ① 只有 1pt 的线（2 行 @228，其余是页面底）⇒ 这一带没有卡片
        var lineOnly = Array(repeating: page, count: 400)
        lineOnly[200] = 228
        lineOnly[201] = 228
        XCTAssertNil(Self.cardFill(modals: lineOnly, pageLuma: page, scale: 2),
                     "一条 1pt 的分隔线没有资格当卡片填充 ⇒ 否则「统计」那一屏的读数会是"
                     + "『尺没压住字』，而真相是『这一屏没有卡片』")
        // ② 真卡片：填充档被字打断（中间 30 行顶到别的档），总行数仍远超地板 ⇒ 必须认得出
        var broken = Array(repeating: page, count: 100)
        broken.append(contentsOf: Array(repeating: 244, count: 88))
        broken.append(contentsOf: Array(repeating: 236, count: 30))
        broken.append(contentsOf: Array(repeating: 244, count: 88))
        XCTAssertEqual(244, Self.cardFill(modals: broken, pageLuma: page, scale: 2),
                       "连续带只有 44pt 的真卡片必须仍然认得出 —— 这一条就是『不许拿连续带高当判据』的证人"
                       + "（快捷键那张真卡片的连续带实测 34.5pt）")
        // ③ 地板之下：20pt 是门槛，19pt 不认
        var small = Array(repeating: page, count: 200)
        small.replaceSubrange(50..<88, with: Array(repeating: 244, count: 38))
        XCTAssertNil(Self.cardFill(modals: small, pageLuma: page, scale: 2),
                     "19pt 的色块不算卡片：门槛之下宁可说『没有卡片』")
        // ④ 并列时取离页面底**近**的那一档（卡片材质是"差一点点"，线/胶囊是"差很多"）
        var tied = Array(repeating: page, count: 100)
        tied.replaceSubrange(0..<40, with: Array(repeating: 244, count: 40))
        tied.replaceSubrange(40..<80, with: Array(repeating: 212, count: 40))
        XCTAssertEqual(244, Self.cardFill(modals: tied, pageLuma: page, scale: 2),
                       "两档行数相同时必须取离页面底近的那个，而且这个选择必须是全序的"
                       + "（Swift 的字典遍历顺序不保证，比较器少一个键就是同一帧两遍两个答案）")
        // ⑤ 全是页面底 ⇒ 没有卡片
        XCTAssertNil(Self.cardFill(modals: Array(repeating: page, count: 300), pageLuma: page, scale: 2))
    }

    /// BACKLOG 147 那条诊断通道的真值表：`cardFill` 说「没有卡片」的那一格，
    /// `fillCandidates` 必须能把「为什么没有」分开说。
    ///
    /// 这一条整段是**为 CI 那一台机器写的**（本机两种形状都能直接从帧里看出来，不需要它）：
    /// workflow 没有 `upload-artifact`，runner 的 PNG 拿不回来，所以「那一台上材质是多少」
    /// 只能靠判据自己打印。而一条会被打印的读数如果没有真值表，它就能安静地恒为「无」
    /// 而不被发觉 —— D-162 那一格说的正是这件事。
    ///
    /// **正对照的写法**：①/② 两格都把同一个数组同时交给**判据**（`cardFill`）和**证人**
    ///（`fillCandidates`），要求判据恒为 nil、证人恒为前三名 —— 这才叫"这一行确实能分开三种形状"。
    /// 只测证人自己的话，证人说什么都有可能绿（R68 那一族）。
    func testFillCandidatesSeparatesNoMaterialFromMaterialTooCloseToPage() {
        let page = 236
        // ① **门限问题**的形状：材质在（差 3，被 `abs(modal-页底)>3` 挡掉），行数也够（120/2=60pt ≥ 20）。
        //   ⇒ 判据给 nil，而证人必须把 (239:120) 摆在第二名。这两句同时成立才是 147 的第一行。
        var nearMiss = Array(repeating: page, count: 471)
        nearMiss.append(contentsOf: Array(repeating: 239, count: 120))
        XCTAssertNil(Self.cardFill(modals: nearMiss, pageLuma: page, scale: 2),
                     "① 的前提：这一档差 3，正被判据的门限挡掉 ⇒ 判据必须给 nil")
        let seen = Self.fillCandidates(modals: nearMiss)
        XCTAssertEqual([236, 239], seen.map { $0.luma },
                       "① 前三名必须**含页底那一档**（不是只报「离页底够远」的那些）："
                       + "否则「前三名全是页底」和「材质在但太近」这两种形状在这行读数里长得一样")
        XCTAssertEqual([471, 120], seen.map { $0.rows },
                       "① 行数要跟着打：147 的第一行判据是「行数/倍率 ≥20pt」，只角色号就判不了")
        // ② **通道问题**的形状：整带只有页底 ⇒ 那台机器根本没画材质。
        let flat = Array(repeating: page, count: 300)
        XCTAssertNil(Self.cardFill(modals: flat, pageLuma: page, scale: 2))
        // R151 / BACKLOG 191 · 新那一维必须**自己就能改变结论**，否则它是装饰（同一份 modals，只换 runs）。
        let pillRows = Array(repeating: 60, count: 60)
        let narrowRuns = Array(repeating: 40, count: 60)          // 600px 带子里只占 40px（≈pill 的 0.07）
        XCTAssertNil(Self.cardFill(modals: pillRows, pageLuma: 52, scale: 2,
                                   runs: narrowRuns, rowWidth: 600),
                     "一行里只横贯 7% 带宽的层是控件不是卡片：加了 runs 还判出材质 ⇒ 那一维没接上")
        let wideRuns = Array(repeating: 560, count: 60)           // 同一批行，只是这一层横贯 93%
        XCTAssertEqual(60, Self.cardFill(modals: pillRows, pageLuma: 52, scale: 2,
                                         runs: wideRuns, rowWidth: 600),
                       "同一份 modals 只换 runs：宽层必须照旧判成卡片（否则新维把真卡片也挡掉了）")
        let flatRanked = Self.fillCandidates(modals: flat)
        XCTAssertEqual([page], flatRanked.map { $0.luma },
                       "② 与①的区别只能靠这一格读出：前三名全等于页底 ⇒ 不是门限，是那条通道本身没画")
        XCTAssertEqual([300], flatRanked.map { $0.rows }, "② 行数也要对上，否则这一行的两个数没有意义")
        // ③ 名次按**行数**，不是按色号（变异臂 M562 动的就是这一格）：
        //   色号最大的那一档（239）只有 4 行 ⇒ 只能排第三；按色号排的写法会给出 (239, 236, 12)。
        var ranked = Array(repeating: page, count: 471)
        ranked.append(contentsOf: Array(repeating: 239, count: 4))
        ranked.append(contentsOf: Array(repeating: 12, count: 6))
        XCTAssertEqual([236, 12, 239], Self.fillCandidates(modals: ranked).map { $0.luma },
                       "③ 前三名是「占多少行」的排名；按色号排会把一条 1pt 的分隔线顶到最前面"
                       + "（R96/R97 那条真病根就是「第一行离页底最远的档」被当成了卡片）")
        // ④ 行数并列 ⇒ 按色号升（比较器必须是全序，否则同一帧两遍两个前三名）。
        //   输入故意取**不是回文**的那个数组：第一次我用 [80,200,200,80]，它的 reverse 和自身逐元素相同
        //   ⇒ 那一条"输入顺序不影响这一行"是在拿同一个数组和自己比，恒真（R88 那一族：对照要真的有两态）。
        let tied = [200, 80, 200, 80]
        XCTAssertEqual([80, 200], Self.fillCandidates(modals: tied).map { $0.luma },
                       "④ 两档各 2 行时必须给唯一答案（按色号升）")
        XCTAssertEqual(Self.fillCandidatesLine(pageLuma: page, modals: tied, top: 2),
                       Self.fillCandidatesLine(pageLuma: page, modals: Array(tied.reversed()), top: 2),
                       "④ 输入顺序不影响这一行：CI 上读到的一行必须与那一遍的遍历顺序无关")
        // ⑤ 档数不足前三名 ⇒ 有几档报几档，不许凑数也不许报错
        XCTAssertEqual(2, Self.fillCandidates(modals: [10, 10, 20], top: 3).count,
                       "⑤ 只有两档时打两档；「前三」是个上限，不是必须凑满的格式")
        // ⑥ 空数组 ⇒ 「无」，**不是空串**：空串在日志里与"那一行压根没打出来"读起来一样，
        //   而那正是 147 的第三种形状（判据没走到这一步）。这一格是三种形状之间的分隔线本身。
        XCTAssertEqual("页底=\(page) 前三=无 门槛=abs(档-页底)>3且行数/倍率>=20pt",
                       Self.fillCandidatesLine(pageLuma: page, modals: []),
                       "⑥ 没有档的时候必须写出「无」，否则第三种形状（没走到）与第二种（全是页底）"
                       + "在 CI 上无法区分")
    }

    /// 每张卡片都得补那份留白：`GroupBox` 的个数必须等于 `settingsCardInset()` 的个数。
    ///
    /// 为什么源码层也要一条（这一句在 R96 之前是"帧判据只压在一张上"，R96 把帧判据扩到了
    /// 每一张之后，那条理由不再成立 —— 留下来的理由是**另一种**）：帧判据要能判一张卡片，
    /// 前提是那张卡片里读得到 ≥2 条分隔线，而「通用」「统计」这类屏天然不满足 ⇒ 它们永远走
    /// `CARD_RHYTHM_DECLINED`。新增一张卡片忘了补留白，帧上不会红 —— 这一条会。
    /// 它数的是**调用点**，不是常量出现次数，所以卡片内部那处
    /// `.padding(.vertical, 4)`（R96 已删，见那一轮的 D-154）不会被算进来。
    ///
    /// R98 / BACKLOG 143：**扫描范围从"一个文件"改成"Views 目录下的每一个文件"**。
    /// 上一版只扫 `Views/SettingsView.swift`，而「推荐」那张卡片长在
    /// `Views/RecommendationWeightsView.swift` 里 ⇒ R95 那次"五处一起补"根本没把它算进名单，
    /// 它带着一个孤儿 `.padding(.vertical, 4)` 一直活到今天（本轮高夹具才量出来：
    /// `边距=11.5/9.5` 对 `内侧=16.5/18.0`）。
    /// 教训不是"那个文件也要扫"，是**按文件划的守卫永远追不上按组件长的东西** ——
    /// 所以这里改成枚举目录：新增一个 Views 文件不需要有人记得把它加进名单。
    func testEverySettingsCardAppliesTheSharedEdgeInset() throws {
        let files = try productViewSources()
        XCTAssertFalse(files.isEmpty, "Views 目录下一个源文件都没有 ⇒ 这条守卫的对象没了")
        var cards = 0, insets = 0
        var offenders: [String] = []
        for (name, text) in files {
            let code = Self.codeOnly(text)
            let here = code.components(separatedBy: "GroupBox {").count - 1
            let there = code.components(separatedBy: ".settingsCardInset()").count - 1
            cards += here
            insets += there
            if here > there { offenders.append("\(name)：\(here) 张卡片 / \(there) 处留白") }
        }
        XCTAssertGreaterThan(cards, 0, "源码里一张 GroupBox 都没找到 ⇒ 这条守卫的对象没了")
        XCTAssertEqual(cards, insets,
                       "设置页有 \(cards) 张卡片，却只有 \(insets) 处补了上下留白 ⇒ "
                       + "至少一张卡片的首末行会贴到卡片边上（R95 那个缺陷的形状）。"
                       + "新卡片请写 `.settingsCardInset()`，别再手抄一个数"
                       + (offenders.isEmpty ? "" : "  ⇒  缺在：" + offenders.joined(separator: "；")))
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
                 // R101 / BACKLOG 131：整列**上移 20pt** —— 「每日复制」这行标题从组件里搬到了
                 // 卡片之上（`DailyCopyHeatmapView.header` 现在只剩汇总行）。
                 // 逐带对过（亮档，同一把带子：旧 34.5..47.5 是标题、54..64 汇总、78.5..88 月份、
                 // 199..209 图例；新 34..44 汇总、58.5..68 月份、179..189 图例 ⇒ 除标题那一带消失之外
                 // 每一带都 -20.0pt，位移是量出来的不是推的）。
                 rect: CGRect(x: 40, y: 52.5, width: 380, height: 16)),
        InkProbe(fixture: "heatmap-populated", what: "星期刻度 一/三/五/日",
                 rect: CGRect(x: 10, y: 70, width: 26, height: 90)),
        InkProbe(fixture: "heatmap-populated", what: "图例「少 / 多」（颜色深浅的唯一标尺）",
                 rect: CGRect(x: 12, y: 176, width: 25, height: 14)),
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
                 // R101 / BACKLOG 131：这一屏补了卡片 ⇒ 汇总行**下移 25pt**（旧带 98.0..108.0，
                 // 新带 123.0..133.0），而分区标题那一带**逐像素没动**（两版都是 78.5..91.5）——
                 // 这正好是这次改动的形状：标题留在卡片之上，卡片自己的上沿与内缩把其余内容顶下去 25pt。
                 rect: CGRect(x: 150, y: 122.5, width: 560, height: 12)),
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

    /// **行为证人：冻住的那一臂画条带，不冻的那一臂不画**（R217 / BACKLOG 240）。
    ///
    /// 为什么这条必须存在：`freezeLoadingForCapture` 是捕帧通道唯一"把异步按住"的开关。
    /// 只看 `detail-loading-composed` 那张帧并不能证明它起作用了 —— 骨架本来就是
    /// `.task` 尚未完成时 SwiftUI 自己画的初始态，**参数被传成死值时帧里也照旧有条带**。
    /// 于是 R211 那句"冻住了所以拍得到"是一句没有证人的话。
    /// 两臂同一份夹具、同一个产品入口（`DetailView`），只差那一个参数 ⇒ 帧里的差别只能来自它。
    ///
    /// **实验的答案是否定的**（本机 2026-10-19 实测：亮 50 == 50、暗 50 == 50）：
    /// 那个参数在离屏捕帧通道里**没有像素后果**，因为 `.task` 里那一跳不会在渲染期内落地。
    /// 所以 BACKLOG 240 想要的"第三把刀（传死值）才会 CAUGHT"在这个通道里做不到 ——
    /// 死值刀要能被像素抓住，前提是通道分得出两臂。这条判据因此留着当**绊线**（见下面断言的说明），
    /// 参数现在能证的只有源码形状那三条（`MediaLoadingPlanTests`）。
    func testFrozenAndLiveArmsReadTheSameSkeletonRows() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r217-behavior-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        func barRows(_ fixture: Fixture, _ appearance: NSAppearance.Name,
                     _ name: String, _ tag: String) throws -> Int {
            let file = scratch.appendingPathComponent("\(name)-\(tag).png")
            _ = try render(fixture, appearance: appearance, to: file)
            guard let image = NSImage(contentsOf: file),
                  let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
                  let base = rep.bitmapData else {
                XCTFail("读不回 \(file.lastPathComponent) ⇒ 这一臂没有读数"); return -1
            }
            return Self.skeletonAxisReadings(
                bytes: base, width: rep.pixelsWide, height: rep.pixelsHigh,
                bytesPerRow: rep.bytesPerRow,
                scale: Double(rep.pixelsWide) / Double(fixture.size.width)).barRows
        }

        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            let frozen = try XCTUnwrap(
                fixtures(appearance: appearance).first { $0.name == "detail-loading-composed" },
                "\(tag)：找不到冻结臂夹具 ⇒ 这条判据没有对象")
            // 不冻臂在这里现造，**不登记进夹具名单**：它只服务这一条对照。
            let liveStore = makePopulatedStore(selectingIndex: 2)
            let live = Fixture("detail-load-live-composed", NSSize(width: 720, height: 520)) {
                AnyView(
                    DetailView(historyStore: liveStore, freezeLoadingForCapture: false)
                        .frame(width: 720, height: 520)
                )
            }

            let frozenRows = try barRows(frozen, appearance, "detail-loading-composed", tag)
            let liveRows = try barRows(live, appearance, "detail-load-live-composed", tag)
            emit("SKELETON_BEHAVIOR_PROOF \(tag) 冻结臂条带行=\(frozenRows) 不冻臂条带行=\(liveRows)")

            XCTAssertGreaterThan(frozenRows, 20,
                "\(tag)：冻结臂只数出 \(frozenRows) 行条带 ⇒ 骨架不在了，"
                    + "或者 `freezeLoadingForCapture` 没有真的把加载按住（这一臂的意义就是它）")
            XCTAssertGreaterThanOrEqual(liveRows, 0,
                "\(tag)：不冻臂没有读数（\(liveRows)）⇒ 帧读不回来，等号那一条会退化成 -1 == -1 的空对账")
            // 两臂**实测相等**（本机 2026-10-19：亮/暗都是 50 == 50）。这不是一条把参数钉成契约的断言，
            // 而是一条**通道改变时会响的绊线**：它记录的是"离屏捕帧里 `.task` 那一跳不会在渲染期内完成"，
            // 于是 `detail-loading-composed` 那张骨架帧不是 R22 禁的那种时机赌 —— 换谁重捕都是这张。
            // 它红了**不是**"把期望改成新数字"，而是"捕帧通道现在能让加载落地了"，
            // 那时候 `freezeLoadingForCapture` 才第一次有像素后果，BACKLOG 240 的第三把刀才有对象。
            XCTAssertEqual(liveRows, frozenRows,
                "\(tag)：不冻臂 \(liveRows) 行 vs 冻结臂 \(frozenRows) 行 ⇒ 捕帧通道里加载真的能完成了，"
                    + "骨架帧从此变成时机赌（R22 禁的那件事）。要做的不是改这条的期望值，"
                    + "而是让冻结臂真的冻住并给参数补像素级证人（BACKLOG 240 的原文）")
        }
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

    /// R189 / BACKLOG 210 欠的那把尺：那颗药丸到底**跟着选中走**，还是固定在控件的某一侧。
    ///
    /// 为什么这一格值得单独建一把尺：R182–R187 五轮里，「白卡在哪一半」这件事被三次改判
    /// （材质合成 → 按钮选中底 → 药丸几何反号），而每一次都是拿**另一把尺**的结论给这一把尺开脱；
    /// R188（`8b90efe`）把那句「病根钉死」撤回了，撤的理由是两把尺对**同一批逐字节相同的像素**给出矛盾形状，
    /// 而且其中一把（`rel=(中心-轨左)/(轨宽/2)`）把正中 1.0 标成了右半。
    ///
    /// 所以这把尺的设计约束写死在这里：
    /// ① **不预设分界线**：控件的 x 范围由帧里"与侧栏背景不同的最长连续段"给出（底轨自己说），
    ///    选中段的位置由**两态相减**给出（换了 filter 之后控件里唯一该变的就是那一段）；
    /// ② **不用绝对亮度**：亮区相对**自己那一行的中位数**判，于是 R185 那句"亮档整幅都过线"不再是理由；
    /// ③ **两态都得真的存在**：`.all` 与 `.favorites` 都从产品入口 `perform(.updateFilter:)` 设，
    ///    夹具不许直接改视图状态（AGENTS.md 第 1 条）；两态若画出一模一样的控件 ⇒ 当场红，
    ///    因为"换了选中态而画面不动"本身就是这一族缺陷的一种。
    ///
    /// 隐私：只打坐标、长度、色号、档名 —— 一个字的用户内容都不打。
    func testFilterPillBrightBandFollowsTheSelectedSegment() throws {
        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r189-pill-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }

        var judgedAppearances = 0
        var uncapableTags: [(tag: String, contrast: Double)] = []
        let appearances: [(tag: String, appearance: NSAppearance.Name)] = [
            ("dark", NSAppearance.Name.darkAqua), ("light", NSAppearance.Name.aqua)]
        for item in appearances {
            let tag = item.tag, appearance = item.appearance
            let roster = self.fixtures(appearance: appearance)
            guard let proto = roster.first(where: { $0.name == "content-empty" }) else {
                return XCTFail("\(tag)：`content-empty` 不在夹具名册 ⇒ 这一族判据失去对象，先查名册别放宽判据")
            }
            // 两态都从产品入口走：建一个空 store，再 perform(.updateFilter(_:))。
            let allStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
            let favStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
            XCTAssertEqual(allStore.filter, .all, "\(tag)：新 store 的默认档不是 `.all` ⇒ 下面的对照失去基准")
            favStore.perform(.updateFilter(.favorites))
            XCTAssertEqual(favStore.filter, .favorites,
                           "\(tag)：`perform(.updateFilter(.favorites))` 没把 filter 装上 ⇒ 两态其实是一态")

            let allFix = Fixture("r189-pill-all", proto.size) { AnyView(ContentView(historyStore: allStore)) }
            let favFix = Fixture("r189-pill-fav", proto.size) { AnyView(ContentView(historyStore: favStore)) }
            var column: (rect: CGRect, kind: String)?
            let allFile = scratch.appendingPathComponent("r189-all-\(tag).png")
            let favFile = scratch.appendingPathComponent("r189-fav-\(tag).png")
            _ = try render(allFix, appearance: appearance, to: allFile) { host in
                column = Self.sidebarColumnRect(in: host)
            }
            _ = try render(favFix, appearance: appearance, to: favFile) { _ in }

            guard let found = column,
                  let imageA = NSImage(contentsOf: allFile), let repA = NSBitmapImageRep(data: imageA.tiffRepresentation ?? Data()),
                  let imageF = NSImage(contentsOf: favFile), let repF = NSBitmapImageRep(data: imageF.tiffRepresentation ?? Data()),
                  let bytesA = repA.bitmapData, let bytesF = repF.bitmapData,
                  repA.pixelsWide == repF.pixelsWide, repA.pixelsHigh == repF.pixelsHigh else {
                return XCTFail("\(tag)：两态帧读不回来或尺寸不一致 ⇒ 对照不成立（不是产品没画）")
            }
            let scale = Double(repA.pixelsWide) / Double(proto.size.width)
            let colBand = Self.clampBand(found.rect, scale: scale,
                                         pixelsWide: repA.pixelsWide, pixelsHigh: repA.pixelsHigh)
            // 候选带：与侧栏背景不同的最长连续段（= 底轨自己说的 x 范围）。
            // 侧栏背景取**该带左沿外两个像素** —— 取角点会被别的元素污染（R37 那一课）。
            let spp = repA.samplesPerPixel, bpr = repA.bytesPerRow
            func luma(_ bytes: UnsafeMutablePointer<UInt8>, _ x: Int, _ y: Int) -> Double {
                let o = y * bpr + x * spp
                return (Double(bytes[o]) + Double(bytes[o + 1]) + Double(bytes[o + 2])) / 3.0
            }
            func trackRun(_ bytes: UnsafeMutablePointer<UInt8>, _ y: Int) -> (Int, Int) {
                let xLo = colBand.x.lowerBound, xHi = colBand.x.upperBound
                let bg = (luma(bytes, max(0, xLo - 2), y) + luma(bytes, max(0, xLo - 1), y)) / 2.0
                var best = (0, 0), cur: Int? = nil
                for x in xLo..<xHi {
                    if abs(luma(bytes, x, y) - bg) > 4.0 {
                        if cur == nil { cur = x }
                    } else if let s = cur {
                        if x - s > best.1 - best.0 { best = (s, x) }
                        cur = nil
                    }
                }
                if let s = cur, xHi - s > best.1 - best.0 { best = (s, xHi) }
                return best
            }
            func diffRun(_ y: Int, threshold: Double = 8.0) -> (Int, Int) {
                let xLo = colBand.x.lowerBound, xHi = colBand.x.upperBound
                var best = (0, 0), cur: Int? = nil
                for x in xLo..<xHi {
                    if abs(luma(bytesA, x, y) - luma(bytesF, x, y)) > threshold {
                        if cur == nil { cur = x }
                    } else if let s = cur {
                        if x - s > best.1 - best.0 { best = (s, x) }
                        cur = nil
                    }
                }
                if let s = cur, xHi - s > best.1 - best.0 { best = (s, xHi) }
                return best
            }
            let minRunPx = max(1, Int((80.0 * scale).rounded()))
            // **能力闸门（本机与 runner 不一样，这件事必须由这一跑量出来）**
            // R189 推上去那一笔在 runner 上红在两句：`找不到 ≥80pt 的差异带`（dark）与
            // `两态对照一次都没有真正判过`（档数闸门）。两句都是真话，但说的不是产品：
            // runner 那条离屏通道**不合成这层材质**（R100 早就量过"runner 看不见卡片材质"，
            // 真机 16 / 离屏 7 那一族），于是底轨与侧栏底是同一个数，控件整条带在帧里根本不存在。
            // 判法不用任何别处的常数：底轨 = 这一列里"与侧栏底不同"的最长连续段，
            // 它要么存在且与底之差 ≥ 地板（能判），要么不存在/差太小（这一档今天无从判定，点名出去）。
            var bestTrack = (0, 0, -1)
            for y in colBand.y.lowerBound..<colBand.y.upperBound {
                let t = trackRun(bytesA, y)
                if t.1 - t.0 > bestTrack.1 - bestTrack.0 { bestTrack = (t.0, t.1, y) }
            }
            let colW = max(1, colBand.x.upperBound - colBand.x.lowerBound)
            var materialContrast = -1.0
            if bestTrack.2 >= 0 {
                let bg = luma(bytesA, max(0, bestTrack.0 - 2), bestTrack.2)
                var mx = 0.0
                for x in bestTrack.0..<bestTrack.1 { mx = max(mx, abs(luma(bytesA, x, bestTrack.2) - bg)) }
                materialContrast = mx
            }
            let canSeeMaterial = FilterPillGeometry.channelCanSeeMaterial(
                trackWidth: bestTrack.1 - bestTrack.0, columnWidth: colW, contrast: materialContrast)
            if !canSeeMaterial {
                // 拆成局部串再拼：整条 `emit(a + b + c …)` 一长串会让编译器超时（R180 那一课）。
                let head = "FILTER_PILL_UNCAPABLE \(tag) 帧=\(repA.pixelsWide)x\(repA.pixelsHigh)"
                    + " 缩放=\(String(format: "%.2f", scale))x"
                let trackPart = "底轨宽=\(bestTrack.1 - bestTrack.0)px/列宽 \(colW)px 轨在y=\(bestTrack.2)px"
                let floorPart = "占比地板=\(String(format: "%.2f", FilterPillGeometry.trackMustCoverColumnFraction))"
                    + " 对比地板=\(String(format: "%.0f", FilterPillGeometry.materialContrastFloor))luma"
                let contrastPart = "轨与侧栏底之差=\(String(format: "%.0f", materialContrast))luma"
                let why = "⇒ 这台机器的这条离屏通道不合成这层材质（R100 那一族），这一档今天无从判定；"
                    + "承重的是能判的那一档，不是把地板调低"
                emit(head + " " + trackPart + " " + floorPart + " " + contrastPart + " " + why)
                uncapableTags.append((tag, materialContrast))
                continue
            }   // 差区至少 80pt 宽：文字换粗不够这一格
            var bands: [(yLo: Int, yHi: Int, runLo: Int, runHi: Int)] = []
            var open: (Int, Int, Int, Int)? = nil
            for y in colBand.y.lowerBound..<colBand.y.upperBound {
                let d = diffRun(y)
                if d.1 - d.0 >= minRunPx {
                    if open == nil { open = (y, d.0, d.1, d.1) }
                    open = (open!.0, min(open!.1, d.0), max(open!.2, d.1), y)
                } else if let o = open {
                    bands.append((o.0, y, o.1, o.2))
                    open = nil
                }
            }
            if let o = open { bands.append((o.0, colBand.y.upperBound, o.1, o.2)) }
            // 带高要与控件对得上：`SegmentedFilterPicker` 的 `.frame(height: 26)`（源码里那个 26 是契约），
            // 但**这里不写死 26** —— 用带高/控件高之比筛，再把候选全打出来，红了能一眼看出是哪一格。
            let pick = bands.max(by: { ($0.yHi - $0.yLo) * ($0.runHi - $0.runLo) < ($1.yHi - $1.yLo) * ($1.runHi - $1.runLo) })
            var verdict = "无从判定"
            var track = (0, 0)
            var cAll = -1.0, cFav = -1.0, mid = -1.0
            var expectedAll = -1, expectedFav = -1, obsAll = -1, obsFav = -1
            var spread = -1.0
            var leftA = -1.0, rightA = -1.0, leftF = -1.0, rightF = -1.0
            var canJudge = false
            if let b = pick {
                let yMid = (b.yLo + b.yHi) / 2
                track = trackRun(bytesA, yMid)
                let trackW = max(1, track.1 - track.0)
                func vals(_ bytes: UnsafeMutablePointer<UInt8>) -> [Double] {
                    (track.0..<track.1).map { luma(bytes, $0, yMid) }
                }
                // 亮区基准取**底轨自己的最暗值 +60**，不取中位数：
                // 第一版取中位数，而药丸正好占轨宽一半 ⇒ 双峰分布的中位数本身就是药丸的白，
                // `med+12` 于是谁也超不过，读回来是 `all=-1 fav=-1`（本机实测，形状像"量不到"，其实是尺坏）。
                // 这也与"参照点要问自己"那一族同源（R37 / U-60）。
                func brightCenter(_ bytes: UnsafeMutablePointer<UInt8>) -> Double {
                    let v = vals(bytes)
                    guard let base = v.min() else { return -1 }
                    var best = (0, 0), cur: Int? = nil
                    for (i, value) in v.enumerated() {
                        if value > base + 60.0 {
                            if cur == nil { cur = i }
                        } else if let s = cur {
                            if i - s > best.1 - best.0 { best = (s, i) }
                            cur = nil
                        }
                    }
                    if let s = cur, v.count - s > best.1 - best.0 { best = (s, v.count) }
                    return best.1 > best.0 ? Double(track.0 + (best.0 + best.1) / 2) : -1
                }
                func buckets(_ bytes: UnsafeMutablePointer<UInt8>) -> String {
                    let v = vals(bytes)
                    guard !v.isEmpty else { return "空" }
                    var out: [String] = []
                    for k in 0..<24 {
                        let lo = v.count * k / 24
                        let hi = max(lo + 1, v.count * (k + 1) / 24)
                        out.append(String(format: "%.0f", v[lo..<hi].reduce(0.0, +) / Double(hi - lo)))
                    }
                    return out.joined(separator: ",")
                }
                func rowsAbove(_ threshold: Double) -> Int {
                    var n = 0
                    for y in colBand.y.lowerBound..<colBand.y.upperBound {
                        let r = diffRun(y, threshold: threshold)
                        if r.1 - r.0 >= minRunPx { n += 1 }
                    }
                    return n
                }
                cAll = brightCenter(bytesA)
                cFav = brightCenter(bytesF)
                mid = Double(track.0 + track.1) / 2.0
                let allCases = HistoryStore.Filter.allCases
                expectedAll = FilterPillGeometry.segmentIndex(HistoryStore.Filter.all, in: allCases)
                expectedFav = FilterPillGeometry.segmentIndex(HistoryStore.Filter.favorites, in: allCases)
                let trackRect = CGRect(x: CGFloat(track.0), y: 0, width: CGFloat(trackW), height: 1)
                obsAll = cAll < 0 ? -1 : FilterPillGeometry.segmentIndex(
                    containingX: CGFloat(cAll), in: trackRect, count: allCases.count)
                obsFav = cFav < 0 ? -1 : FilterPillGeometry.segmentIndex(
                    containingX: CGFloat(cFav), in: trackRect, count: allCases.count)
                let valsA = vals(bytesA)
                let valsF = vals(bytesF)
                func halfLevels(_ v: [Double]) -> (Double, Double) {
                    guard v.count >= 2 else { return (-1, -1) }
                    let cut = v.count / 2
                    let lo = Array(v[0..<cut]), hi = Array(v[cut..<v.count])
                    return (lo.reduce(0.0, +) / Double(lo.count), hi.reduce(0.0, +) / Double(hi.count))
                }
                (leftA, rightA) = halfLevels(valsA)
                (leftF, rightF) = halfLevels(valsF)
                // 这一档能不能判，由**这一跑的数**决定，不是拿"亮档一贯判不了"的旧结论顶上来：
                // 极差 = 轨道那一行里最亮桶减最暗桶。分不开 ⇒ 后面走"有名字的未判定"出口。
                spread = (valsA.max() ?? 0) - (valsA.min() ?? 0)
                canJudge = cAll >= 0 && cFav >= 0
                if !canJudge {
                    verdict = "量不到偏离轨道电平的连续区"
                } else if obsAll == expectedAll && obsFav == expectedFav {
                    verdict = "亮区两态都落在选中段 ⇒ 与「亮=轨道暴露面」相反，通道翻向了，先重看裁片再动代码"
                } else if obsAll == expectedFav && obsFav == expectedAll {
                    verdict = "亮区在两态各占**非**选中段 ⇒ 与「亮=轨道暴露面、暗=药丸」一致"
                } else if abs(cAll - cFav) < Double(trackW) / 8.0 {
                    verdict = "亮区没跟着选中换（固定）"
                } else {
                    verdict = "亮区形状不在预期三种之内 ⇒ 需要人判"
                }
                emit("FILTER_PILL_BAND \(tag) 列=\(found.kind) 列带x=\(colBand.x.lowerBound)..\(colBand.x.upperBound)px"
                     + " 缩放=\(String(format: "%.2f", scale))x 候选带数=\(bands.count)"
                     + " 选中的带: y=\(b.yLo)..\(b.yHi)px(高\(String(format: "%.1f", Double(b.yHi - b.yLo) / scale))pt)"
                     + " 差区x=\(b.runLo)..\(b.runHi)px"
                     + " 底轨x=\(track.0)..\(track.1)px(宽\(String(format: "%.1f", Double(trackW) / scale))pt) 轨中心=\(Int(mid))px"
                     + " 亮区中心 all=\(Int(cAll))px fav=\(Int(cFav))px"
                     + " 期望段 all=\(expectedAll) fav=\(expectedFav) 读到段 all=\(obsAll) fav=\(obsFav)"
                     + " 轨道内极差=\(String(format: "%.0f", spread))luma 判定=\(verdict)"
                     + " 24桶all=[\(buckets(bytesA))] 24桶fav=[\(buckets(bytesF))]"
                     + " 差区行数(阈8)=\(rowsAbove(8.0))")
            } else {
                emit("FILTER_PILL_BAND \(tag) 列=\(found.kind) 候选带数=0 差区行=0"
                     + " 判定=两态在侧栏里没有任何 ≥80pt 宽的差异")
            }
            XCTAssertNotNil(pick,
                            "\(tag)：两态帧在侧栏里找不到一条 ≥80pt 宽的差异带 ⇒ 换了 filter 而画面一个字都没动，"
                            + "这是选中态不可辨（不是判据坏）。候选带全打在那行 FILTER_PILL_BAND 里，先读它。")
            guard canJudge else {
                // **有名字的未判定**（三条一起满足，R133/174 那一族）：
                // ① 前提由这一跑量出来 —— 轨道那一行的最亮桶减最暗桶 <30luma，材质与底轨分不开；
                // ② 说清放不掉什么 —— 放掉的是"亮档那一条的亮区归位"，暗档那条照旧承重、不因此放宽；
                // ③ 它是读数不是覆盖率通道 —— 极差 ≥30 却仍量不到 ⇒ 下面那条断言当场红（尺坏，不是档不行）。
                emit("FILTER_PILL_UNJUDGED \(tag) 理由=轨道内极差只有\(String(format: "%.0f", spread))luma"
                     + "（底轨x=\(track.0)..\(track.1)px 亮区中心 all=\(Int(cAll)) fav=\(Int(cFav))）"
                     + " ⇒ 这一档的材质与底轨在这条离屏通道分不开；暗档判据照旧承重")
                XCTAssertLessThan(spread, 30.0,
                                  "\(tag)：量不到亮区，可轨道那一行的极差有 \(String(format: "%.0f", spread))luma（≥30）"
                                    + " ⇒ 那不能算「这一档分不开」，是这把尺自己坏了，必须红")
                continue
            }
            // 判据一（**与合成方向无关**）：换选中 ⇒ 控件两半的电平必须各自翻转。
            // 这条不需要知道"药丸是亮的那半还是暗的那半"，所以它骗不过：
            // 两态若画得一模一样（选中态没表达）或只动文字不动块，这里当场红。
            XCTAssertGreaterThan(abs(leftA - leftF), 60.0,
                                 "\(tag)：左半在两态之间的电平只差 \(String(format: "%.0f", abs(leftA - leftF)))luma（要 >60）"
                                 + " ⇒ 换 filter 之后控件左半没动，选中态在这一档没有表达。"
                                 + "左all=\(String(format: "%.0f", leftA)) 左fav=\(String(format: "%.0f", leftF))")
            XCTAssertGreaterThan(abs(rightA - rightF), 60.0,
                                 "\(tag)：右半在两态之间的电平只差 \(String(format: "%.0f", abs(rightA - rightF)))luma（要 >60）"
                                 + " ⇒ 换 filter 之后控件右半没动。"
                                 + "右all=\(String(format: "%.0f", rightA)) 右fav=\(String(format: "%.0f", rightF))")
            judgedAppearances += 1
            // 判据二（**通道标定**，出处写在下面）：这条离屏通道里药丸合成成**暗**的那一半
            // （R189 直接裁片看过：`.all` 档暗块压住左段「全部」、右段轨道是白 255 —— 与屏幕上"亮药丸"的直觉相反）。
            // 这一条是**可证伪的标定**，不是常识：哪天通道翻了向，它会红，而红的第一步是重看裁片，不是改阈值。
            let darkSideAll = leftA < rightA ? 0 : 1
            let darkSideFav = leftF < rightF ? 0 : 1
            emit("FILTER_PILL_SWAP \(tag) 左all=\(String(format: "%.0f", leftA)) 右all=\(String(format: "%.0f", rightA))"
                 + " 左fav=\(String(format: "%.0f", leftF)) 右fav=\(String(format: "%.0f", rightF))"
                 + " 暗半all=\(darkSideAll) 暗半fav=\(darkSideFav) 期望段 all=\(expectedAll) fav=\(expectedFav)"
                 + " 段号反解 all=\(obsAll) fav=\(obsFav) 判定=\(verdict)")
            XCTAssertEqual(darkSideAll, expectedAll,
                           "\(tag)：`.all` 档里药丸（暗的那半）在第 \(darkSideAll) 段，而产品自己的 allCases 说选中是第 \(expectedAll) 段"
                            + "（左all=\(String(format: "%.0f", leftA)) 右all=\(String(format: "%.0f", rightA))）。"
                            + "红了的顺序是：先把这一帧的控件裁出来用眼睛看（R189 就是这么定下合成方向的），再谈改代码 —— 不许直接改阈值。")
            XCTAssertEqual(darkSideFav, expectedFav,
                           "\(tag)：`.favorites` 档里药丸（暗的那半）在第 \(darkSideFav) 段，而选中的是第 \(expectedFav) 段"
                            + "（左fav=\(String(format: "%.0f", leftF)) 右fav=\(String(format: "%.0f", rightF))）。"
                            + "两半若互换，才是 BACKLOG 210 说的「镜像反号」。")
        }
        // **出口不许把判据吃掉**（R99 那一族"名单为空=红"，这里的主语是"档"）：
        // 每一档都可以因为通道分不开而走"有名字的未判定"，但**全部档都走出口**就等于这条判据不存在了 ——
        // 那正是变异臂 M701 要抓的形状（把 `canJudge` 恒置 false，两档都安静出口，一条断言都不会跑）。
        if judgedAppearances == 0 && uncapableTags.count == appearances.count {
            let premise = uncapableTags.map { "\($0.tag)=\(String(format: "%.0f", $0.contrast))luma" }
                .joined(separator: " ")
            throw XCTSkip("FILTER_PILL_UNCAPABLE 两档都判不了（\(premise)，地板 "
                + "\(String(format: "%.0f", FilterPillGeometry.materialContrastFloor))luma）"
                + " ⇒ 这台机器的这条离屏通道不合成这层材质（R100 那一族：runner 看不见卡片材质），不是产品没画。"
                + "承重的那一格在能判的机器上（本机暗档同一把尺读到 214luma），而这条出口自己有证人："
                + "`FilterPillGeometryTests.testChannelCapabilityRejectsTheTwoBlindShapes`")
        }
        XCTAssertGreaterThanOrEqual(judgedAppearances, 1,
                                    "两态对照一次都没有真正判过，而判不了的原因不是「通道看不见材质」"
                                    + "（能判的档=\(judgedAppearances)，无能力的档=\(uncapableTags.count)）"
                                    + " ⇒ 这条判据今天不存在，必须红")
        emit("FILTER_PILL_JUDGED 真判的档数=\(judgedAppearances)/\(appearances.count) 判不了的档=\(uncapableTags.count)")
    }

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
        // R98 / BACKLOG 141：**种子必须在 `render` 里种，不能在调用方种**。
        //
        // 上一版这件事只有 `testCaptureKeyViews` 一处做（拍之前 `set`、拍完立刻还原），而其余
        // 二十多个 `render` 调用点 —— 全是"判据自己重渲染一张帧再量像素"的那些 —— 直接把
        // `fixture.seed` 当不存在。后果不是"少了一行字"，是**判据量的不是它名字里那张帧**：
        // 本机逐字节对过 settings 族 10 对帧，只有 `settings-privacy-excluded` 两版不同
        //（判据卷 319980 B / 交付卷 333059 B），而它是全仓**唯一**声明了种子的夹具；
        // 分歧从 **566.0pt** 开始，正好是那两行「移除」该在的位置，
        // 870.5..936.0pt 交付帧有 54 行墨、判据帧 0 行（`r98_seed_divergence.py`）。
        // R97 把这件事记成"两条读图通道给出不同边界"，R98 的对照证明那个机制是错的
        //（同一张帧 TIFF 回路与直接解 PNG 逐段一致，`CARD_CHANNEL_SUMMARY 不一致=0`）——
        // 真相是两张**不同的图**，而"两条通道"这个假设从没被验过。
        //
        // 放在这里而不是放在调用方，是因为只有这一处是**所有**拍帧路的必经点：
        // 调用方各自种 = 25 份迟早会漂开的副本。还原仍然由调用方的那条"谁种了默认值谁必须还原"
        // 断言兜住（`originalSeeds`），这一格只是不再依赖调用方记得做。
        var seededKey: String? = nil
        var seededOriginal: String? = nil
        if let seed = fixture.seed {
            seededKey = seed.key
            seededOriginal = UserDefaults.standard.string(forKey: seed.key)
            UserDefaults.standard.set(seed.value, forKey: seed.key)
        }
        defer {
            if let key = seededKey {
                if let back = seededOriginal {
                    UserDefaults.standard.set(back, forKey: key)
                } else {
                    UserDefaults.standard.removeObject(forKey: key)
                }
            }
        }
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
        // R162 / BACKLOG 194：**只出读数，不放行、不 skip、不豁免**（这是 R161 那条被证伪的出口该有的样子）。
        // runner 上六张 `settings-*-tall-720x1040` 报"有 95% 像素未画"，而"这台机器屏幕装不下"
        // 已被本机否掉：`CAPTURE_SCREEN … visibleHeightPt=847` 而同一批高帧本机 `blank=0.0%`、画到第 2079 行
        // ⇒ 离屏窗口不被屏幕可视高夹住。剩下三种成因（窗口被收小 / 内容视图没铺满 / 画了但整层不合成）
        // 靠下面这一行分辨：三个尺寸全部来自**这一次**捕获，谁也不引用别处的常数。
        if size.height >= Self.tallFixtureHeightFloor {
            let geometryTag = appearance == .darkAqua ? "dark" : "light"
            let content = window.contentView?.frame.size ?? NSSize(width: -1, height: -1)
            emit("CAPTURE_GEOMETRY \(fixture.name) \(geometryTag)"
                 + " requested=\(Int(size.width))x\(Int(size.height))"
                 + " content=\(Int(content.width))x\(Int(content.height))"
                 + " host=\(Int(host.frame.width))x\(Int(host.frame.height))"
                 + " screenVisibleHeightPt=\(Int(NSScreen.main?.visibleFrame.height ?? -1))")
            capturedGeometry[file.lastPathComponent] =
                (size.height, content.height, host.frame.height,
                 NSScreen.main?.visibleFrame.height ?? -1)
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
        // R145：产品入口操作放在 caret 静默**之后**（见 `Fixture.interact` 的注释）。
        fixture.interact?(window)
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

        // R106 / BACKLOG 159：把**用户根本看不到的选中区间**从帧里抹掉（与 `silenceCarets` 同一族）。
        // 放在这里而不是放在产品里：这一格是"上屏那一下字段自动全选"造成的通道现象，
        // 产品路径 `show()` 赋的是空串、用户逐字敲，从来没有这一刻（读数见 `QUICKPICK_FIELD_STATE`）。
        Self.collapsePhantomSelections(in: host)

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
        // R168 / BACKLOG 194：包围盒读的是**同一份 raw rep 字节**（与 blackBand 同源）。
        // -1 是"没拿到字节"，不是"没画" —— 两者在 194 的三分规则里落进不同出口。
        var drawnBox = (topPt: -1.0, bottomPt: -1.0, heightPt: -1.0)
        if let base = rep.bitmapData {
            blackBand = Self.blackBandHeight(bytes: base,
                                             width: rep.pixelsWide,
                                             height: rep.pixelsHigh,
                                             bytesPerRow: rep.bytesPerRow,
                                             backingScale: CGFloat(rep.pixelsWide) / max(size.width, 1))
            drawnBox = Self.drawnBoundingBox(bytes: base,
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
                              bottomInkFraction: bottomInk,
                              drawnBoxPt: drawnBox.heightPt, drawnBottomPt: drawnBox.bottomPt)
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
    private static func silenceCarets(in view: NSView) {        if let textView = view as? NSTextView {
            textView.insertionPointColor = .clear
            textView.needsDisplay = true
        }
        if let textField = view as? NSTextField, let editor = textField.currentEditor() as? NSTextView {
            editor.insertionPointColor = .clear
            editor.needsDisplay = true
        }
        view.subviews.forEach { silenceCarets(in: $0) }
    }

    /// R106 / BACKLOG 159 的读数用：按**身份**在树里找浮层那一枚搜索字段。
    ///
    /// 为什么不就地写一个递归 `func find`（我第一版就是这么写的）：它落在 `inspect:` 那个
    /// `@MainActor` 闭包里，Swift 不会把局部函数也判成 MainActor ⇒
    /// `subviews` 直接告警（本机实测，"构建 0 告警"这一格当场红）。
    /// 静态函数与 `silenceCarets` 同一条隔离，就没有这一档。
    static func firstOverlayTextField(in view: NSView) -> NSTextField? {
        if let field = view as? NSTextField { return field }
        for sub in view.subviews {
            if let field = firstOverlayTextField(in: sub) { return field }
        }
        return nil
    }

    /// R106 / BACKLOG 159：把**真实使用里不成立的选中区间**从帧里抹掉。
    ///
    /// 成因（本机读出来的，不是猜的）：捕获入口为了把查询摆上去必须程序化赋值，
    /// 窗口上屏那一下又会给那枚字段装一个 field editor，而字段成为第一响应者时**默认全选**；
    /// 离屏窗口不是 key（130 记过）⇒ 选中底画成**灰**而不是强调色，
    /// 于是 `quickpick-typed` / `-empty` 两张帧上出现一块 32 行 / 1115 像素的色块，
    /// 并且从 R63 起被帧基线钉成"正确答案"。
    /// 真实用户是逐字敲进去的，从来没有这一刻 ⇒ 与 `silenceCarets` 同一条规矩：
    /// **闪烁的、瞬时的、产品路径上不成立的状态不许进基线**。
    static func collapsePhantomSelections(in view: NSView) {
        if let text = view as? NSText {
            let end = (text.string as NSString).length
            if text.selectedRange.length != 0 || text.selectedRange.location != end {
                text.selectedRange = NSRange(location: end, length: 0)
            }
        }
        // field editor 不一定挂在被遍历的那棵子树上（它是宿主视图的兄弟级子视图），
        // 所以除了走子树，再按**身份**问一次字段自己。
        if let field = view as? NSTextField, let editor = field.currentEditor() {
            let end = (editor.string as NSString).length
            if editor.selectedRange.length != 0 || editor.selectedRange.location != end {
                editor.selectedRange = NSRange(location: end, length: 0)
            }
        }
        view.subviews.forEach { collapsePhantomSelections(in: $0) }
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
