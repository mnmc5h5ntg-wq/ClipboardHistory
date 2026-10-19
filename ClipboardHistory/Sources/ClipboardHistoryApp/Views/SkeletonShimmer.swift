import Combine
import SwiftUI

/// 骨架扫光（动效审计 M9）。
///
/// 为什么值得做这一条：spinner 说的是"我在等"，骨架说的是"内容马上来"。
/// 同一个等待时间里，后一种把用户的注意力放到了**即将出现的东西**上，
/// 而不是放在"还要等多久"上 —— 这是感知等待时间的差别，不是装饰。
/// 而详情预览确实有一段读不出宽高的等待（图片/视频/QuickLook），正是它该出现的场合。
///
/// **时钟是"每拍把相位写回视图状态"（`@State` + `Timer.publish`），不是
/// `.animation(...repeatForever:)`。** 选它的理由只有一条：**这一条被量过**。
///
/// 取证过程本身走了一次弯路，记下来比结论有用。我先后三次测到"整窗峰值 0.0000"
/// —— `repeatForever` 版、`@StateObject` + `Timer.scheduledTimer` 版、以及现在这一版
/// 在**亮带只抬 5 个点**的时候 —— 并且每次都把结论写成"这条路没落地"。
/// 至少有一次是错的：把抬升从 0.05 提到 0.12，**同一份代码**就读到 19 对在变、峰值 0.015
/// （`MotionFilmstripTests.testSkeletonSweepActuallySweeps` 的开臂）。
/// 所以那几个 0.0000 里至少有一部分是"对比度低于像素门槛"，不是"动画没跑"。
/// 报告 §12.5 的首选案（`repeatForever`）**没有在高对比度下复测过**，
/// 这里因此不能断言它不工作 —— 只能说它没被证明工作。仓库的规矩是反过来的那条：
/// **没被证明工作的路不拿去交付**。代价写在这里：视图里多一个 `@State`，以及 30Hz 的一次小面积重绘。
///
/// 三条约束来自报告 §5 红线 2（"仓库现在一个 `repeatForever` 都没有，
/// 这是新增的第一条常驻动画风险"）：
/// 1. **只在确实处于加载态时存在**：`SkeletonPreviewView` 只出现在 `DetailFileView`
///    的 `.loading` 分支里，结果一到（或超时改判失败）整个视图就被换掉，时钟跟着宿主一起消失。
///    这条同时给了它一个**时长上界**：`PreviewLoadTimeoutPolicy.timeoutSeconds = 8`，最坏 8 秒。
///    （这里曾经还带一个 `isLoading` 参数，删掉是因为产品在 `.loading` 分支里只能传 `true`：
///    一个永远为真的输入不是判据，是装饰 —— 报告 MC-11 对 `guard …fades` 的原话同一族。）
/// 2. **只在看得见的那块区域里扫**（详情预览区），不整页；
/// 3. 全仓只准有**一个**动画时钟，且 `repeatForever` 一次都不许出现
///    —— 由 `MotionCatalogTests.testAmbientLoopIsSingleton` 钉住。
enum SkeletonMotion {
    /// 扫光到底跑不跑 —— 纯函数，两档都要能断言。
    ///
    /// 减弱动态时**留着骨架、停掉扫动**（不是把整块换成 spinner，也不是什么都不画）：
    /// 骨架承载的是"内容马上来"这条信息，扫动承载的才是"我在动"；
    /// 前者留下、后者去掉，正好是 HIG 与 Emil 那句 "fewer and gentler, not zero" 的分工。
    static func sweepIsRunning(reduceMotion: Bool) -> Bool { !reduceMotion }

    /// 亮带宽度。**R84 起这是"占整组宽度的比例"**，不是占单根条的：
    /// 亮带现在画在容器坐标系里（见 `SkeletonBarsShape` 的理由），所以同一个数在
    /// 420pt 的详情区上是 126pt 宽的一条光，而不是每根条各自 30%。
    /// 沿用 markiv/SwiftUI-Shimmer 的 `bandSize 0.3`：再宽就没有"扫"的方向感，再窄会看成频闪。
    static let bandSize: CGFloat = 0.3

    /// 三根条的相对宽度：短 — 长 — 中，读起来像"一行标题 + 两行正文"，
    /// 而不是三根一样的杠（一样的杠会被读成"这里有个进度条"）。
    static let barFractions: [CGFloat] = [0.42, 0.86, 0.64]

    /// 单根条带的高度与条间距。
    ///
    /// 这两个数从视图里的两个魔法数提成令牌，是 R84 那条判据的**前提**：判据现在要
    /// 在同一套几何下去像素里找那三根条（`MotionFilmstripTests.testSkeletonSweepIsOneBand`）。
    /// 留在视图里就等于让判据猜产品的布局 —— 猜对了也是空的。
    static let barHeight: CGFloat = 8
    static let barSpacing: CGFloat = 10

    /// 第 `index` 根条在 `rect`（整组被给出的矩形）里的位置。
    ///
    /// 顶部起算、左边贴 `rect.minX`：与 R26 钉住的那条"骨架条带与下面那句说明同一条左轴"
    /// 是同一件事 —— 换成一整个 `Shape` 之后左轴仍然只有一条。
    static func barRect(index: Int, fraction: CGFloat, in rect: CGRect) -> CGRect {
        CGRect(x: rect.minX,
               y: rect.minY + CGFloat(index) * (barHeight + barSpacing),
               width: max(1, rect.width * fraction), height: barHeight)
    }

    /// 定时器节奏。30Hz 而不是 60Hz：一圈 1.5 秒只要 45 步就看不出台阶，
    /// 而每拍都是一次小面积重绘 —— 省下来的那一半不是洁癖，是给 500 条列表留的余量。
    static let tickInterval: TimeInterval = 1.0 / 30.0

    /// 相位 ∈ 0…1：0 = 亮带整条在左外，1 = 整条在右外。
    /// 两端都留在画面外是必须的 —— 停在画面里的话，每圈头尾都切在边缘上，
    /// 看起来像"扫到一半卡住、再弹回去"。
    static func bandStart(forPhase phase: CGFloat) -> CGFloat { -bandSize + phase * (1 + bandSize) }

    /// 一圈里走一步。**必须绕回 0**：不绕的话相位跑到 1 之后就停住，
    /// 于是"常驻循环"实际只演一次，而界面看起来像"卡住的灰条"。
    static func advance(_ phase: CGFloat, by fraction: CGFloat) -> CGFloat {
        guard fraction > 0 else { return phase }
        let next = phase + fraction
        return next >= 1 ? next - 1 : next
    }

    /// 一拍的推进量 = 一拍 ÷ 一圈。**返回 nil 表示"这个节奏不成立"**：
    /// 一圈比一拍还短 ⇒ 每拍推进 ≥ 100%，那不叫扫光，叫随机闪烁。
    /// 做成可失败的纯函数，是为了让退化输入这一档有判据，而不是靠"看起来没崩"。
    static func fraction(secondsPerCycle: TimeInterval) -> CGFloat? {
        guard secondsPerCycle > tickInterval, tickInterval > 0 else { return nil }
        return CGFloat(tickInterval / secondsPerCycle)
    }

    /// 条带底色。报告 §3 给的就是这个数：`.primary.opacity(0.06)`。
    static let baseOpacity: Double = 0.06
    /// 亮带亮度。**这里不能只抬 5 个点** —— 见 `minimumHighlightLift` 的注释。
    static let highlightOpacity: Double = 0.18

    /// 亮带相对底色的**最小抬升**，单位就是 opacity。
    ///
    /// 这条不是审美，是测量结论：第一版照报告字面写成 0.06 / 0.11（抬 5 个点），
    /// 胶片读到的整窗峰值是 **0.0000** —— 当时我判成"这条路没落地"。
    /// 拿同一套画法、只把亮带抬到 0.45 的对照臂一测就有 0.022，于是定性清楚了：
    /// **动画在跑，是 5 个点的抬升在像素上等于没动**（0.05 × 255 ≈ 12 级，
    /// 刚好压在尺子 8 级的噪声门槛上，再摊到每对帧就没了）。
    /// "尺子看不见"和"人眼看不见"在这里是同一件事：一条扫过去看不见的骨架，
    /// 比 spinner 更没用。所以把下限写成数字，而不是写成一句"要克制"。
    static let minimumHighlightLift: Double = 0.08

    // MARK: - 按档给的墨（R219 / BACKLOG 242）

    /// 亮档的底色墨。**为什么亮档要单独一个数**：`Color.primary.opacity(α)` 是乘法，
    /// 同一个 α 在两个底上给的**绝对**差值差一个量级 —— 实测（R215，`/tmp/shots_r215` 的组合帧）：
    /// 暗档 底 28 ↔ 条带 41 = Δ13、对比度 **1.17**；亮档 底 248 ↔ 条带 242 = Δ6、对比度 **1.05**。
    /// 也就是同一份代码在亮档几乎画不出可见的条带 —— 骨架承诺的是"这块内容马上来"，
    /// 看不见就等于没承诺。0.14 是按"要跨过那条 8 级的噪声门槛"给的：
    /// Δ6 → Δ14（≈ 2.3 倍），仍远低于同帧那一句说明文字的 3.72。
    static let lightBaseOpacity: Double = 0.14
    /// 亮档的亮带墨。**抬 base 必须同时抬这一档**，否则抬升预算 `highlight - base` 被吃掉，
    /// 扫光会从"能测到"退回 R214 注释里那个 0.0000（242 的原话条件）。0.26 - 0.14 = 0.12，
    /// 与暗档同一个抬升量，也仍在 `testHighlightIsFarEnoughAboveTheBaseToBeSeen` 的 0.35 天花板之下。
    static let lightHighlightOpacity: Double = 0.26

    /// 这一档该用多少墨。**唯一一处**读"是亮档还是暗档"的地方 —— 视图里只调它，
    /// 于是"两档各一套"这件事有一个可以问"是不是恒真"的谓词（`SkeletonMotionTests` 的真值表）。
    static func inkOpacities(dark: Bool) -> (base: Double, highlight: Double) {
        dark ? (baseOpacity, highlightOpacity)
             : (lightBaseOpacity, lightHighlightOpacity)
    }

    /// 亮带的两个端点。`phase` 只影响**位置**，不影响形状 ——
    /// 形状（三个 stop）是固定的，这也是为什么 Timer 每拍只需要改一个数。
    ///
    /// 这两个端点落在**谁**的坐标系里是会被画出来的：填在整组的形状上就是整组一条带，
    /// 填在单根条上就是每根条各一条（R84 之前是后者，见 `SkeletonBarsShape`）。
    /// 这一句不是注释：`MotionFilmstripTests.testSkeletonSweepIsOneBand` 用像素判它。
    static func unitPoints(phase: CGFloat) -> (start: UnitPoint, end: UnitPoint) {
        let x = bandStart(forPhase: phase)
        return (UnitPoint(x: x, y: 0.5), UnitPoint(x: x + bandSize, y: 0.5))
    }
}

/// 详情预览的加载骨架：三根条带 + 一条匀速扫过去的亮带。
///
/// 它**只在加载态被画出来**（调用点在 `DetailFileView` 的 `.loading` 分支），
/// 所以"离开加载态就停"这件事有结构保证；减弱动态那一档走的是 `else` 分支 ——
/// 连时钟都不订阅，而不是"起了再停"。
struct SkeletonPreviewView: View {
    /// 注入点：默认跟随全源门（系统开关 + VoiceOver）。
    var reduceMotion: Bool = MotionCatalog.motionShouldBeReduced

    /// 这一档是亮还是暗。**为什么由视图问系统而不是由调用方传进来**：
    /// 骨架的宿主有三处（详情预览、组合帧夹具、以及以后可能有的占位），
    /// 让每个宿主各传一个 `isDark` 就会有一处传错，而"传错"在画面上只是"亮档那条带看不见"——
    /// 正是 R215 量出来、已经存在过一次的那个缺陷。系统这一路只有一个真相源。
    @Environment(\.colorScheme) private var colorScheme

    @State private var phase: CGFloat = 0

    var body: some View {
        if SkeletonMotion.sweepIsRunning(reduceMotion: reduceMotion),
           let step = SkeletonMotion.fraction(secondsPerCycle: MotionCatalog.duration(for: .skeletonSweep)) {
            bars.onReceive(Timer.publish(every: SkeletonMotion.tickInterval, on: .main, in: .common)
                .autoconnect()) { _ in
                phase = SkeletonMotion.advance(phase, by: step)
            }
        } else {
            bars
        }
    }

    /// 三根条带，**一个形状、一条亮带**。抽出来是因为两个分支要画**同一张图** ——
    /// 差别只在于有没有那条时钟，而不是"减弱动态时画个别的"。
    ///
    /// 这里以前是 `GeometryReader + VStack { ForEach }`，每根条自己 `.fill(渐变)`
    /// 再 `.frame(width: 条宽)`：渐变的 `UnitPoint` 相对的是**那一根条**的矩形，
    /// 于是三根条各有一条亮带，同时扫过各自的条。R84 换成整组一个形状，
    /// 渐变因此落在容器坐标系里 —— 判据与量出来的数字见 `SkeletonBarsShape`。
    private var bars: some View {
        SkeletonBarsShape()
            .fill(bandGradient)
    }

    /// 底色 → 亮色 → 底色。三个 stop 固定不动，动的只有整条渐变的位置。
    ///
    /// 亮带在整组之外时两端都 clamp 回底色 ⇒ 减弱动态那一档、以及每圈头尾那一段，
    /// 画面上就是三根静止的灰条（这也是为什么静态帧基线预期不变）。
    private var bandGradient: LinearGradient {
        let points = SkeletonMotion.unitPoints(phase: phase)
        return LinearGradient(
            stops: [
                .init(color: base, location: 0),
                .init(color: highlight, location: 0.5),
                .init(color: base, location: 1),
            ],
            startPoint: points.start, endPoint: points.end)
    }

    /// 两档各一套墨（R219 / BACKLOG 242）。为什么不能共用一个 opacity：见 `inkOpacities(dark:)` 的注释 ——
    /// 同一支 6/100 的墨在 248 的底上只给 Δ6（对比度 1.05），在 28 的底上给 Δ13（1.17），
    /// 于是"亮档几乎看不见条带"是**乘法**的必然，不是谁没画。
    private var ink: (base: Double, highlight: Double) {
        SkeletonMotion.inkOpacities(dark: colorScheme == .dark)
    }

    private var base: Color { Color.primary.opacity(ink.base) }
    private var highlight: Color { Color.primary.opacity(ink.highlight) }
}

/// 三根条带的**轮廓**：一个 `Shape`，里面三个 `VisualShape.rounded(.chip)`。
///
/// 为什么值得单独一个类型（R84 / BACKLOG 117）：`LinearGradient` 的 `UnitPoint`
/// 是相对"这个形状被给出的那个矩形"的。原来每根条是一个独立的 `RoundedRectangle`
/// 加 `.frame(width: proxy.size.width * fraction)` ⇒ 三根条就是三套单位空间，
/// 同一个 `phase` 在三根条上是三个**绝对**位置（176 / 361 / 269pt 宽 ⇒ 中心在 88 / 181 / 134pt）。
/// `MotionFilmstripTests` 用像素把这件事量了出来（`.scratch/motion-audit-2/r83_band_fanout.py`
/// 是同一道题的第一版手量）：同一帧里三根条的亮斑绝对中心最大差 **170pt**，
/// 归一化中心最大只差 **0.003** ⇒ 画面上是"三条各扫各的亮带"，不是"一条光穿过一组条"。
///
/// 为什么这是缺陷而不是风格偏好：骨架扫光的全部表达力在于**给整组一个共同的方向和节奏**，
/// 读起来是"这一块内容正在加载"；三条各自闪动读起来是三个独立的东西在闪，
/// 信息量更低而注意力开销更大（报告 §5 红线 1：不抢用户的注意力）。
///
/// 修法只有一件事：让形状与填充都覆盖整组，轮廓自己描述三根条。
/// 代价写清楚：三根条不再由 `VStack` 排，纵向布局变成这个 `path(in:)` 的算术
/// ⇒ 由 `SkeletonMotion.barRect(index:fraction:in:)` 那两个令牌与像素判据一起钉住。
struct SkeletonBarsShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        for (index, fraction) in SkeletonMotion.barFractions.enumerated() {
            path.addPath(VisualShape.rounded(VisualRadius.chip)
                .path(in: SkeletonMotion.barRect(index: index, fraction: fraction, in: rect)))
        }
        return path
    }
}
