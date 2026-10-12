import AppKit
import SwiftUI

/// 全 App 的动效目录：时长、曲线、以及"减弱动态效果时退化成什么"，三张表只写在这一处。
///
/// 为什么要有这个文件（动效审计 §4 / M11）：动效参数一旦散在各视图里，
/// 结果就是同一个"状态被改变了"在四处分别是 0.11 / 0.14 / 0.15 / 0.18 秒 ——
/// 没人能说出哪个是对的，也没人改得动。仓库里已经有两处把参数抽成纯值的先例
/// （`FilterPillMotion.SlideMotion`、`MultiFilePreviewLayout.animation(reduceMotion:)`），
/// 这里沿用同一个形状：**参数是纯值、视图消费它、测试断言它**。
///
/// 四条硬规矩，都写成了可断言的形式：
/// 1. **上限 250ms**，而且上限管的是**真正交出去的那条曲线**。
///    第一版这里被打回来过（报告 MC-2）：`duration(for:)` 表里全是 0.12–0.18，
///    而 `animation(for:)` 在位移档里根本不用它，写死 `response: 0.32` ——
///    于是"没有任何一档超过 0.25s"这条守卫只检查了常数表，检查不到用户看到的那条曲线，
///    声明 150ms 的滑入实测跑 200ms。现在 `Animation` **只能**从 `curve(for:)` 推出来，
///    而 `curve(for:).seconds` 又只能来自 `duration(for:)`，两头都钉住了。
/// 2. **只动 `opacity` / `scaleEffect` / `offset`，不动 `frame` / `padding` / `height`**。
///    布局型动画每帧触发重排，500 条列表时必掉帧。唯一的既有例外是多文件预览的展开
///    （`CollapsibleFilePreview`，已被 reduce-motion 门控），不扩散。
/// 3. **减弱动态是"替换"而不是"关掉"**（MDN 对口径）：触发前庭的是大面积的缩放与平移，
///    所以滑入换成淡入、弹跳换成直接落位；时长**不归零** ——
///    把界面变成"无反馈"不是无障碍，是另一种缺陷（同类里 Pearcleaner 的
///    `duration: animationEnabled ? 0.35 : 0` 就是被反对的那种写法）。
/// 4. **进场用强 ease-out，不用 ease-in 段**（M17）：Emil 原文 "Never `ease-in` on UI"、
///    "`ease-out` at 200ms *feels* faster than `ease-in` at 200ms"；
///    Carbon 的 entrance productive 是 `(0, 0, 0.38, 0.9)`、exit productive 是 `(0.2, 0, 1, 0.9)`。
///    第一版所有纯淡入档给的是 `.easeInOut` —— 前半段就是 ease-in，方向反了。
enum MotionCatalog {
    /// 动效的**用途**。用用途而不是用秒数来选参数：
    /// 视图里写 `MotionCatalog.animation(for: .bannerIn)`，
    /// 而不是写一个没人知道为什么是 0.14 的数。
    ///
    /// 目录里**不留没人消费的档位** —— `testEveryRoleHasAConsumer` 钉着这条。
    /// 已经有三档被删掉过，都是量过之后砍的：
    /// - `detailSwap`：详情换页淡入只能从全透明开始 ⇒ 每次换选一帧空白（`DetailView`）；
    /// - `listReflow` / `rowInsertion` / `rowRemoval`：`List` 的行过渡在 macOS 上跑不出来，
    ///   四种写法全部一帧到位（`HistorySidebarView` 的注释 + 胶片分带实测）；
    /// - `panelIn` / `panelOut`：热键呼出路径按规范就不该有动画（报告 §12.1 更正 #7）。
    enum Role: String, CaseIterable, Sendable {
        case hover         // 悬停底色/描边：跟着鼠标，必须几乎无感
        case selection     // 选中态淡入
        case bannerIn      // 顶部提示条出现
        case bannerOut     // 顶部提示条消失
        case emphasis      // 状态被改变的确认（收藏 / 固定 / 已复制）
        case dropTarget    // 拖入落点框
        case contentFade   // 内容换页（详情换类型、设置分类、菜单栏结果落地、空态）
    }

    /// 全局上限。任何一档超过它都要在这里改常数，改完 `testEveryRoleStaysUnderTheCeiling` 会红
    /// —— 而且它现在断言的是 `curve(for:)` 的秒数，也就是真正交给系统的那条曲线。
    static let maximumDuration: TimeInterval = 0.25

    /// 临界阻尼 = 不过冲。WWDC18「Designing Fluid Interfaces」：默认从 100% damping 开始调弹性，
    /// 只有**手势本身带惯性**时才给轻微过冲。这里的滑入都是程序触发的，不是手势跟手。
    /// （第一版写的是 0.86 并注释成"不过冲"—— `dampingFraction < 1` 在 SwiftUI 里就是欠阻尼、
    /// 必有过冲，仓库自己在 `FilterPillMotion` 里已经写了正确定义。报告 MC-1。）
    static let criticalDamping: Double = 1.0

    /// 一档时长。
    static func duration(for role: Role) -> TimeInterval {
        switch role {
        case .hover: return 0.12
        case .selection: return 0.12
        case .bannerIn: return 0.15
        case .bannerOut: return 0.12
        case .emphasis: return 0.16
        case .dropTarget: return 0.12
        case .contentFade: return 0.16
        }
    }

    /// 落点框的"吸住"缩放。量级参照 Carbon `contextual` 的退场 scale(0.96)：
    /// 这个体系里缩放是 4% 一档，不是 16%（第一版的 `emphasisScale = 1.16` 既没人消费、
    /// 又完全不在量级上，报告 MC-5 一并删掉；`slideOffset` 同批删除 —— 滑入用的是
    /// `.move(edge:)`，位移量由系统决定，那个 8 从来没人读）。
    static let dropTargetScale: CGFloat = 0.98

    /// 进场曲线：Emil 的强 ease-out。
    static let entranceControlPoints: [Double] = [0.23, 1, 0.32, 1]
    /// 退场曲线：Carbon exit productive。
    static let exitControlPoints: [Double] = [0.2, 0, 1, 0.9]

    // MARK: - 形状（纯值，可断言）

    /// 一个动效"到底动了什么"。`Animation` 与 `AnyTransition` 都不好比较，
    /// 所以视图从这份形状构造它们，测试直接断言这份形状 ——
    /// 否则"减弱动态时到底退化成什么"没有判据（仓库里那 15 处淡入就是这么漏掉门控的）。
    ///
    /// 这里**没有** `fades` 开关：所有档位都淡入，这是规矩 3 的底线，
    /// 而一个恒为真的布尔字段等于没有（报告 MC-5 对第一版的原话）。
    struct Shape: Equatable, Sendable {
        enum Slide: Equatable, Sendable { case none, top, bottom, leading, trailing }

        var slides: Slide = .none
        var scales = false
        /// 退场档：曲线换成 exit 那一组控制点，且不带位移（走的时候不该再占一次注意力）。
        var isExit = false
    }

    /// 减弱动态时的退化规则集中在这一个函数里：滑入 → 淡入；缩放 → 直接落位；时长一律不归零。
    static func shape(for role: Role, reduceMotion: Bool) -> Shape {
        var shape = Shape()
        switch role {
        case .hover, .selection, .contentFade, .emphasis:
            break
        case .bannerIn:
            shape.slides = reduceMotion ? .none : .top
        case .bannerOut:
            shape.isExit = true
        case .dropTarget:
            shape.scales = !reduceMotion
        }
        return shape
    }

    // MARK: - 曲线（纯值，`Animation` 只能从这里来）

    /// 真正交出去的那条曲线的**值**。上限、reduce-motion 退化、进场/退场选哪组控制点，
    /// 全在这里一次定完，`animation(for:)` 只剩机械映射。
    struct Curve: Equatable, Sendable {
        enum Kind: Equatable, Sendable {
            case timingCurve([Double])
            case spring(damping: Double)
        }

        var kind: Kind
        var seconds: TimeInterval
    }

    static func curve(for role: Role, reduceMotion: Bool) -> Curve {
        let shape = shape(for: role, reduceMotion: reduceMotion)
        let seconds = duration(for: role)
        if shape.slides != .none {
            // 位移档用弹簧：response 直接取这一档的时长（MC-2 的病灶就是这里曾经写死 0.32）。
            return Curve(kind: .spring(damping: criticalDamping), seconds: seconds)
        }
        return Curve(kind: .timingCurve(shape.isExit ? exitControlPoints : entranceControlPoints),
                     seconds: seconds)
    }

    // MARK: - 视图消费的那两份

    /// 由 `curve(for:reduceMotion:)` 机械映射出来的 `Animation`。**不要在这里加参数**：
    /// 参数只在上三张表里，否则形状断言与真实曲线会分叉。
    static func animation(for role: Role, reduceMotion: Bool = motionShouldBeReduced) -> Animation {
        // 胶片探针的 A/B 开关（见下面 `animationsEnabled`）。`Animation` 没有 `.none`，
        // 所以"没有动画"要由一条极短的曲线来表达。
        //
        // 为什么是 0.001 而不是 0：实测**精确为 0** 时，带 `.transition` 的插入根本不会落地 ——
        // 30 帧全等、峰值 0.000，A/B 于是从"一帧到位"退化成"什么都没发生"，
        // 那条对照就失去了意义（它要求"变化仍然看得见，只是不再分摊到几帧"）。
        guard animationsEnabled else { return .linear(duration: 0.001) }
        let curve = curve(for: role, reduceMotion: reduceMotion)
        switch curve.kind {
        case .timingCurve(let points):
            return .timingCurve(points[0], points[1], points[2], points[3], duration: curve.seconds)
        case .spring(let damping):
            return .spring(response: curve.seconds, dampingFraction: damping, blendDuration: 0)
        }
    }

    /// 进出场过渡。同样只从形状推出来；淡入是所有档位的底座（规矩 3）。
    static func transition(for role: Role, reduceMotion: Bool = motionShouldBeReduced) -> AnyTransition {
        let shape = shape(for: role, reduceMotion: reduceMotion)
        var transition: AnyTransition = .opacity
        switch shape.slides {
        case .none: break
        case .top: transition = transition.combined(with: .move(edge: .top))
        case .bottom: transition = transition.combined(with: .move(edge: .bottom))
        case .leading: transition = transition.combined(with: .move(edge: .leading))
        case .trailing: transition = transition.combined(with: .move(edge: .trailing))
        }
        if shape.scales {
            transition = transition.combined(with: .scale(scale: dropTargetScale))
        }
        return transition
    }

    /// 非对称进出场（插入用一档、移除用另一档）。
    ///
    /// 两个方向各自带上自己的 `animation`：`AnyTransition` 只描述"怎么变"，
    /// 时长来自事务，而这里两个方向的**时长本来就不同**（进 150ms、出 120ms）。
    /// 不显式绑上去的话，移除会借用插入那一档的时长，那张时长表就只有一半生效。
    static func asymmetricTransition(insertion: Role, removal: Role,
                                     reduceMotion: Bool = motionShouldBeReduced) -> AnyTransition {
        .asymmetric(
            insertion: transition(for: insertion, reduceMotion: reduceMotion)
                .animation(animation(for: insertion, reduceMotion: reduceMotion)),
            removal: transition(for: removal, reduceMotion: reduceMotion)
                .animation(animation(for: removal, reduceMotion: reduceMotion))
        )
    }

    // MARK: - 降级开关（全源门）

    /// 「这一档要不要降级成纯淡入」——**全源门**（M16，先例 Rectangle 的 `WindowAnimator`）：
    /// 系统「减弱动态效果」 **或** VoiceOver 正在运行。
    ///
    /// 为什么把 VoiceOver 也算进来：WCAG 2.2 SC 2.3.3 的字面要求是"由交互触发的动效
    /// 必须能被关闭"，而读屏用户同样是"看见动效会丢上下文"的人；只看 reduce-motion
    /// 会漏掉一整类人。
    ///
    /// 三重门里还差一条：开关控制（Switch Control）**没有公开 API**，
    /// 同类是去读 `com.apple.universalaccess` 的私有键 —— 那是拿兼容性赌一个观感，本轮不做，
    /// 记在账本里当未覆盖项。
    ///
    /// 做成 `static var`（而不是常量）是为了测试能改它 ——
    /// 一个读不到也写不了的开关，等于两个分支里只有一个被测过。
    static var motionShouldBeReduced: Bool {
        overrideReduceMotion ?? isMotionReduced(
            reduceMotionSetting: NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
            voiceOverRunning: NSWorkspace.shared.isVoiceOverEnabled
        )
    }

    /// 上面那条的**合成规则**，抽成纯函数是为了能断言：读系统状态只能测到一个真值，
    /// 而"任一来源说要降就降"这句话有四个格子，不拆出来就永远只有两格被测过。
    static func isMotionReduced(reduceMotionSetting: Bool, voiceOverRunning: Bool) -> Bool {
        reduceMotionSetting || voiceOverRunning
    }

    /// 测试注入点。`nil` = 跟随系统（reduce-motion 与 VoiceOver 取或）。
    nonisolated(unsafe) static var overrideReduceMotion: Bool?

    /// 胶片探针的 A/B 开关：关掉之后目录给出的所有曲线变成**零时长** ——
    /// 事务还在、`.transition` 声明还在，只是不再"分摊到几帧"。
    ///
    /// 它存在的唯一理由：证明判据量到的确实是**我们这条动画**，而不是恰好发生的重排、
    /// 图片解码或滚动条淡出。没有这条 A/B，"过渡帧数 ≥3" 这句话的归因是空的。
    /// 生产路径永远不写它；默认值由 `MotionCatalogTests` 钉住。
    nonisolated(unsafe) static var animationsEnabled = true
}
