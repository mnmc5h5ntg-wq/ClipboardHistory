import SwiftUI

/// 按压态（R4）：全 App 唯一的"你按到了"表达。
///
/// R0 审计里这件事是**零**：没有一处 `isPressed`、没有任何自定义 `ButtonStyle`，
/// 而所有图标按钮都写着 `.buttonStyle(.plain)` —— 那等于把系统给的那一下临时高亮也拿掉了。
/// 结果不是"手感差一点"，是**界面不说话**：点下去之后要等结果（图标换了、选中变了）才知道被收到；
/// 结果本身不来的场合（复制失败、文件读得慢），按下与没按长得一模一样。
///
/// 表达刻意很小：缩放 0.97（44pt 控件上收 1.3pt）+ 一层比 hover 重一档的底色。
/// 按下要的是"东西被压下去了"的证据，不是表演 —— 而且这两样里只有底色是**信息**：
/// 减弱动态时缩放归零，底色留着（与 `MotionCatalog` 的 reduce 退化表同一句话）。
///
/// 不做按压态的两处，都是刻意的（写清楚，免得下一个人"顺手补齐"）：
/// 菜单栏推荐项走的是系统菜单，它自己的选中高亮就是反馈，再叠一层自绘底会把
/// 第三轮审计 U-1 刚拆掉的"卡片感"装回来。
enum PressableAppearance {
    /// 纯函数：按下时缩多少。三档真值都要能被断言（`isPressed` 与 `reduceMotion` 各两个取值），
    /// 因为"减弱动态时还缩放"这种缺陷只有把判断做成函数才量得到。
    static func scale(isPressed: Bool, reduceMotion: Bool) -> CGFloat {
        isPressed && !reduceMotion ? MotionCatalog.pressScale : 1.0
    }

    /// 纯函数：按下时的底色强度。没按但悬停时沿用 hover 那一档，两者都没有就是透明。
    /// 按下比 hover 重一档是**次序**上的必然：`hover < press`，就像 `hover < selected`
    /// （见 `VisualFill` 里那条判据）—— "正在按"比"鼠标在这儿"更近一步。
    ///
    /// `hoverLevel` 有默认值，但**小控件要显式抬一档**（`VisualFill.controlHover`）：
    /// 6% 铺在一整行上读得出来，铺在 20pt 的图标上等于没有 —— 那是尺寸差，不是口味差
    /// （`VisualFill.controlHover` 自己那条注释说的就是同一件事）。
    static func fillOpacity(isPressed: Bool,
                            isHovered: Bool,
                            hoverLevel: Double = VisualFill.hover) -> Double {
        if isPressed { return VisualFill.pressed }
        return isHovered ? hoverLevel : 0
    }
}

/// 按钮样式：把 `configuration.isPressed` 翻成缩放 + 底色。
///
/// 形状由调用方给，因为这一家的按钮形状本来就不一样（圆图标、圆角矩形行、胶囊里的段）。
/// 传形状而不是传"圆不圆"的布尔：形状是这里唯一画得对的东西。
struct PressedStyle<S: Shape>: ButtonStyle {
    let fillShape: S
    /// 整行类的按钮关掉缩放：一行横向铺满时缩放会让它在视觉上"缩进"列表，
    /// 而行的选中/底色已经是它的主反馈。
    var scales = true
    /// 注入点：默认跟全源门。做成参数是因为**没有夹具的两种状态等于没有验收**
    /// （`DetailView` 的 `initialMarkdownMode` 是同一手法）。
    var reduceMotion: Bool = MotionCatalog.motionShouldBeReduced
    /// 悬停那一档的强度（见 `PressableAppearance.fillOpacity`）。
    var hoverLevel: Double = VisualFill.hover
    /// label 四周留多少给底色层（默认 0 = 药丸正好贴着内容）。
    ///
    /// R15 加的这一层。默认 0 是故意的：**这不是"更漂亮"，是命中区**——
    /// 底色铺在 label 的包围盒上，所以一颗 16pt 图标的悬停药丸就是一圈紧贴笔画的方块，
    /// 而系统工具栏那颗是"图标 + 每边约 5pt"，且**能点的地方和高亮一样大**。
    /// 只在图标类站点抬（侧栏五颗批量按钮、排除名单的「移除」、回执 ×），
    /// 其余站点（整行、文字按钮）本来就有自己的内边距，再抬就是改版式。
    var labelPadding: CGFloat = 0

    func makeBody(configuration: Configuration) -> some View {
        PressedLabel(configuration: configuration,
                     fillShape: fillShape,
                     scales: scales,
                     reduceMotion: reduceMotion,
                     hoverLevel: hoverLevel,
                     labelPadding: labelPadding)
    }
}

/// 悬停这一半**必须**由一个能持有状态的东西来记。
///
/// 以前这里直接在 `makeBody` 里写 `isHovered: false` —— 因为 `ButtonStyle.makeBody`
/// 里不能有 `@State`。后果不是"少一点效果"：`VisualFill.hover` 那一档
/// 在**全 App 每一个按钮**上都不可达（R13 抓到的一条），
/// 而 `PressableAppearance.fillOpacity` 的真值表一直是绿的 ——
/// 纯函数两个分支都测过，调用点只喂一个分支，这一族叫"载荷绿、消费侧坏"。
/// 所以把这半层做成一个真的视图，状态归它自己。
private struct PressedLabel<S: Shape>: View {
    let configuration: PressedStyle<S>.Configuration
    let fillShape: S
    let scales: Bool
    let reduceMotion: Bool
    let hoverLevel: Double
    let labelPadding: CGFloat
    @State private var isHovered = false

    var body: some View {
        configuration.label
            // 先加边再缩放：缩放是几何效果、不改布局，所以底色那一层（挂在后面）
            // 始终是"未缩放的那一圈"，而它覆盖的是**内容 + 边**——
            // 也就是高亮比字形大一圈，且这一圈同样点得动（padding 在 label 里，命中区跟着长）。
            .padding(labelPadding)
            .scaleEffect(scales ? PressableAppearance.scale(isPressed: configuration.isPressed,
                                                           reduceMotion: reduceMotion)
                                : 1.0)
            .overlay(
                fillShape.fill(Color.primary.opacity(
                    PressableAppearance.fillOpacity(isPressed: configuration.isPressed,
                                                   isHovered: isHovered,
                                                   hoverLevel: hoverLevel)))
            )
            // 时长用 `.hover` 那一档（0.12s）：按下跟鼠标事件同频，比内容切换更快才不觉得黏。
            .animation(MotionCatalog.animation(for: .hover), value: configuration.isPressed)
            .animation(MotionCatalog.animation(for: .hover), value: isHovered)
            .onHover { inside in isHovered = inside }
    }
}

extension View {
    /// 按压反馈的唯一入口。
    func pressedStyle<S: Shape>(in shape: S,
                                scales: Bool = true,
                                hoverLevel: Double = VisualFill.hover,
                                labelPadding: CGFloat = 0) -> some View {
        buttonStyle(PressedStyle(fillShape: shape, scales: scales,
                                 hoverLevel: hoverLevel, labelPadding: labelPadding))
    }
}

/// 焦点态这一半本轮**故意没做**（读码读出来的，不是没顾上）：
/// `ChineseEditableTextField` 早就把 `focusRingType = .default` 恢复了（审计第二轮 1.10 / R2-02），
/// 搜索框的键盘焦点已经有系统环 —— 再叠一条自绘边只会画两圈。
/// 剩下的真实缺口是"筛选段按钮与设置行拿不到任何焦点提示"，那需要先把
/// `List` 的行代理结构量清楚（已知红 `testSidebarListFocusRingAfterClick` 就在这一带），
/// 所以它单独成一轮，而不是在这里装一个没人用的环。
