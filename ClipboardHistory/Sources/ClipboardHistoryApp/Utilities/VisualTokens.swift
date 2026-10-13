import SwiftUI

/// 几何与材质令牌 —— "表面长什么样"的唯一作者（视觉迭代 R1）。
///
/// R0 审计数出来的是一堆各写各的：圆角 **6 种**（4 / 5 / 6 / 7 / 8 / 9，其中 4 的那四处还漏了
/// `.continuous`）、发丝线 **3 种**（0.5 / 0.7 / 1.0）、投影 **4 处三个数**（0.06 与 0.08 打同一种
/// 16pt 小方块；0.08 与 0.10 打同一种浮起玻璃，后者还漏了 `.compositingGroup()`）、
/// 悬停底色 **3 档**（0.045 / 0.06 / 0.07）。它们干的活是同一件事 —— 把"这是一颗可点的东西"
/// "这块玻璃浮在内容之上"说给眼睛听，而参数散在七个文件里时，"统一"只能靠共识。
/// 收在这一份里之后，统一有判据（`VisualTokenTests`），而且**每个数旁边必须写清为什么是这个数**。
///
/// 规矩与 `MotionCatalog` 一模一样：
/// - 视图里不许再出现 `RoundedRectangle(cornerRadius: 数字)`、`.shadow(color: .black…)`、
///   `lineWidth: 数字` —— 一律走本文件的出口；
/// - 要新值就加一个带理由的令牌，加完它必须真的被读到（没人读的令牌会打红：
///   装饰性常数等于没有常数，这是上一轮 MC-5 的教训）；
/// - 上限只准降不准升的是数量，不是数值 —— 数值该改就改，但改完这里就是唯一现场。
///
/// 刻意**不放**在这里的东西：文字语义色与图标透明度（那是排版的活，R2）、
/// 动效参数（在 `MotionCatalog`，两套混起来会让"改一个数会影响什么"说不清）、
/// 布局尺寸（padding/frame 属于各视图自己的语境，令牌化它们只会得到一份"什么都往里装"的表）。

// MARK: - 圆角

enum VisualRadius {
    /// 4pt：16pt 级的小方块（行内缩略图、类型占位符）与 8pt 高的骨架条带。
    /// 这个量级上 4 已经是"圆到接近极限"：骨架条高 8，4 正好是半高，再大就成药丸，
    /// 缩略图则会看起来像图标按钮而不是"一张图"。
    static let chip: CGFloat = 4

    /// 6pt：24pt 高的可点胶囊（筛选滑块）。
    /// 半径要到高度一半才读得出"胶囊感"，但滑块必须在轨道里留出可见的上下间隙，
    /// 所以取"明确是圆的、又还没假装自己是 `Capsule`"的那一档。
    static let control: CGFloat = 6

    /// 7pt = `control` + 1：容纳滑块的轨道。
    /// 差值必须是 1pt 而不是同值：两层角同心时曲率半径相同 ⇒ 内层的角会切进外层的描边里，
    /// 看着像滑块没对齐。写成 `control + 1` 而不是字面量 7，是为了让"轨道跟着滑块走"这件事
    /// 在将来改 `control` 时自动成立。
    static let track: CGFloat = control + 1

    /// 8pt：30pt 级、装内容的表面（搜索框、多文件行、详情里可展开的预览块）。
    /// 选它是因为系统给的那类圆角容器（Finder 侧栏行、Spotlight 条目）就在这个量级 ——
    /// 目标是"看起来像系统的皮"，不是"自己的风格"。
    static let card: CGFloat = 8

    /// 9pt：覆盖一整块区域的表面（列表的拖拽落点框、设置侧栏行）。
    /// 沿用现状、不抬到 10：这两处本来就一致，为了"凑整数"再改一次几何，
    /// 代价是全部帧基线重画，而换不到任何肉眼读得出的差别。
    static let panel: CGFloat = 9

    /// 2pt：热图那一格 11pt 的小方块。
    ///
    /// 为什么比 `chip`(4) 还小：格子只有 11pt，4 的圆角会把相邻两格的"角"接在一起
    ///（间距才 3pt），整行读成一串药丸而不是一张日历。2pt 是"角不再是尖的"与
    /// "还是一块方砖"之间唯一站得住的位置。
    static let heatCell: CGFloat = 2
}

// MARK: - 热图（每日复制统计）

/// 每日复制热图的几何与色阶。
///
/// 单独一个枚举而不是散进 `VisualFill` / `VisualTint`：这五档强度**只在同一张图里互相比较**，
/// 它们与"hover / pressed / selected"那条强度次序**不是同一个量**（那一条说的是"离你多近"，
/// 这一条说的是"那天你干了多少"）。把两套混成一个布尔或一个数组，
/// 下一次改 hover 就会顺手改掉统计图的刻度（同一个词在两个判据里含义不同那一族）。
enum VisualHeat {
    /// 11pt 见方：一列 7 格 = 77pt + 间距，`defaultWindowWeeks`（26 周）
    /// ≈ 26×11 + 25×3 = 361pt，加星期标签列约 375pt ——
    /// 设置页右栏在 720pt 窗口下放得下且不需要横向滚动。再小（9pt）格子会开始像噪点，
    /// 再大（13pt）整张图会顶到窗口边缘，逼着缩短窗口。
    /// （这条算式跟着窗口周数走：窗口从 18 周加宽到 26 周那次（视觉审查发现右栏半空）
    /// 只改了 `DailyCopyHeatPolicy.defaultWindowWeeks`，注释漏改 —— 见 D-068。）
    static let cell: CGFloat = 11

    /// 3pt：格间距。必须是**奇数**且明显小于格宽：
    /// 偶数 2pt 在 1x 屏上会被并成一条看不见的缝，格子会糊成一片实心矩形；
    /// 4pt 则开始把"行"读成三条独立的横线（日历的星期行就散了）。
    static let spacing: CGFloat = 3

    /// 0.055：没有记录的那一格。**不能是 0**（透明）——
    /// 那样"那天没复制"与"那天还没到来"就长得一样，而这两件事差得很远。
    static let empty: Double = 0.055

    /// 四档由浅到深。等比递增（×1.9 左右）而不是等差：
    /// 等差会让前两档几乎分不开（0.15/0.30 在 11pt 的方块上是同一个灰度），
    /// 而深浅在日历上是**唯一**的信息通道 —— 分不开就等于少两档。
    static let ladder: [Double] = [0.18, 0.34, 0.56, 0.85]

    /// 悬停那一圈的描边宽度。比 `VisualHairline.edge` 重一档：
    /// 它要在**已经有色块**的表面上把自己读出来，发丝线在深色格子上会消失。
    static let hoverStroke: CGFloat = 1

    /// 强度 `bucket`（0…4）→ 强调色不透明度。
    static func opacity(bucket: Int) -> Double {
        guard bucket > 0 else { return empty }
        return ladder[min(bucket, ladder.count) - 1]
    }
}

enum VisualShape {
    /// 唯一的圆角矩形出口。**永远 `.continuous`**：
    /// 默认的 `.circular` 在角上是"圆弧接直线"，曲率不连续，放大看角的两端有一处肉眼可见的折；
    /// `.continuous`（squircle）才是苹果控件的画法。R0 审计里 4pt 那四处（缩略图、骨架条带）漏了
    /// `style:`，而 6pt 以上的表面都带着 —— 于是同一屏里同时存在两种曲率语言：
    /// 小方块是"圆弧接直线"，卡片是 squircle，挨在一起时角上的接法一眼可辨。
    static func rounded(_ radius: CGFloat) -> RoundedRectangle {
        RoundedRectangle(cornerRadius: radius, style: .continuous)
    }
}

// MARK: - 线宽

enum VisualHairline {
    /// 0.5pt：贴在内容边缘的发丝描边（缩略图、搜索框）。
    /// Retina 上是半个物理像素、非 Retina 上会并成 1 个 —— 两个外观下都只"描一下"，不会画成一根线。
    static let edge: CGFloat = 0.5

    /// 0.7pt：玻璃表面上的描边（胶囊、视频控件）与 hover 时浮起的卡片描边。
    /// 比 `edge` 重一档是必要的：材质本身在抖动，0.5 的线压不住它。
    static let rule: CGFloat = 0.7

    /// 1pt：胶囊内部那种**实心**分隔线。它说的是"这里断开"，不是"这里有个边"，
    /// 发丝级的宽度在 `.ultraThinMaterial` 上会被材质吃掉，读不出分隔。
    static let divider: CGFloat = 1
}

enum VisualStroke {
    /// 1.5pt：拖拽落点的虚线框。它必须比任何发丝线都粗 —— 否则和描边分不出来，
    /// 而"能放"这个提示的价值全在于一眼看见。
    static let highlight: CGFloat = 1.5

    /// [4, 3]：虚线段与间隔几乎等长 ⇒ 读起来是"虚线"，而不是"点划线"或"长划"。
    /// 3 不是 4 是为了让整圈的分段数在常见窗口宽度下不出现"接缝"（段长不整除周长时最难看）。
    static let highlightDash: [CGFloat] = [4, 3]

    /// 3pt：光晕那一圈的线宽。模糊之后还剩多少取决于原始线宽，1pt 的圈过 `blur` 就没了。
    /// 与 `MotionCatalog.dropGlowRadius`（模糊半径）数值相同纯属巧合：一个是线宽、一个是半径，
    /// 改一个不会让另一个跟着动，所以不放同一个令牌。
    static let glow: CGFloat = 3
}

// MARK: - 投影

enum VisualShadow {
    struct Edge {
        let color: Color
        let radius: CGFloat
        let y: CGFloat
        /// 打阴影之前要不要先把子树合成一次。见 `flat` / `raised` 各自的理由。
        let groupsFirst: Bool
    }

    /// 贴平：16pt 级小方块只要一点边，让它从行底色上分出来。
    /// 0.08 是原"图片缩略图"那一档（另一处"类型占位符"写的是 0.06）：取强的那个数，
    /// 因为占位符本身只有一层 `.quaternary` 底，投影没了它就真的贴不住了。
    /// 刻意**不**分组合成：缩略图里只有一层裁剪后的位图，分组等于给**每一行**多一次离屏合成，
    /// 而列表滚动是这个 App 最贵的一条路径。
    static let flat = Edge(color: .black.opacity(0.08), radius: 1, y: 0.5, groupsFirst: false)

    /// 浮起：8pt 扩散 + 3pt 下沉。配合材质读出来的才是"这块玻璃在内容之上"。
    /// 必须分组合成：`.ultraThinMaterial` 是独立图层，不分组合成就给每一层各打一次阴影，
    /// 表现是控件边缘多一圈重影。R0 审计在视频控件那处抓到过"同一个数、漏了这一句"。
    static let raised = Edge(color: .black.opacity(0.10), radius: 8, y: 3, groupsFirst: true)
}

extension View {
    /// 投影的唯一出口（见 `VisualShadow`）。走这里而不是就地 `.shadow(...)`，
    /// 是因为"要不要分组合成"正是上一轮漏掉的那一半，而它会静默地不报错。
    @ViewBuilder
    func visualShadow(_ edge: VisualShadow.Edge) -> some View {
        if edge.groupsFirst {
            self.compositingGroup()
                .shadow(color: edge.color, radius: edge.radius, y: edge.y)
        } else {
            self.shadow(color: edge.color, radius: edge.radius, y: edge.y)
        }
    }
}

// MARK: - 底色强度

enum VisualFill {
    /// 0.06：行与卡片级的悬停底色（多文件行、Markdown 切换、设置侧栏行悬停）。
    /// R0 之前这里是三档：0.045 / 0.06 / 0.07 —— 同一件"鼠标在这里"说出三种音量。
    /// 取中间值而不是最大值：底色用来标出范围，不该盖过它里面的文字。
    static let hover: Double = 0.06

    /// 0.12：按下那一瞬间的底色。次序是语义：**hover < pressed < selected** ——
    /// "正在按"比"鼠标在这儿"更近一步，但仍轻于一个会留下来的选择。
    /// 减弱动态时缩放归零，这一档留着：底色是信息，缩放才是物理隐喻。
    static let pressed: Double = 0.12

    /// 0.08：44pt 圆形符号按钮的悬停底色。面积只有行的一小条，同强度下读不出"按这里"，
    /// 所以整档抬高 —— 这是尺寸差造成的，不是口味差。
    ///
    /// **为什么不是 0.10**（R14 实测改的，R13 一度把它定在 0.10）：
    /// 抬到 0.10 之后，"从悬停按下去"这一跳只剩 0.02 的余量 —— 在 22pt 的控件上量出来是
    /// `3.7/255` 的均值通道差，低于"一块平面上看得出来"的地板（4/255，见
    /// `PressFeedbackTests.perceptibleStep255`）。也就是说 **R13 为了让悬停看得出来而抬的那一档，
    /// 恰好把按压缩成和悬停同一档** —— 修好了一个反馈、弄没了另一个，而且两套判据都是绿的。
    /// 0.08 是两边都过的那一侧（同一把尺、同一尺寸、两种外观实测）：
    /// `idle→hover 15.9 / 14.0`、`hover→pressed 8.4 / 7.5`（亮 / 暗，0–255 均值通道差）。
    static let controlHover: Double = 0.08

    /// 0.035：输入框静止态。侧栏里的搜索框是背景信息，太实会跟列表抢层级。
    static let fieldIdle: Double = 0.035

    /// 0.06：输入框激活态（悬停或有内容）。与 `hover` 同档但**不共用**：
    /// "鼠标在这儿"和"这个框正在被用"是两件事，R7 要给焦点单独抬一档时不该牵连行悬停。
    static let fieldActive: Double = 0.06

    /// 0.16：选中行 / 选中分类的底色（由强调色派生）。选中是持久状态，必须比 hover 这种瞬时态重，
    /// 否则"哪一条是我选中的"要读第二眼。
    static let selected: Double = 0.16
}

// MARK: - 描边强度

enum VisualTint {
    /// 0.15：小方块（缩略图）的描边。原来图片 0.16、符号 0.14 —— 两种缩略图并排在同一行时
    /// 边界深浅不一样。取中间值。
    static let chipStroke: Double = 0.15

    /// 0.05 / 0.10：输入框静止与激活的描边（原为 0.05 与 0.095）。
    /// 收齐成"底色抬一档、描边也抬一档，两档间隔都是 0.05"，
    /// 于是激活这件事有节奏，而不是每个属性各加一点点。
    static let fieldIdleStroke: Double = 0.05
    static let fieldActiveStroke: Double = 0.10

    /// 0.07：hover 时浮起的卡片描边（多文件行）。它和 `VisualFill.hover` 的底色是一对：
    /// 底色说"范围"，描边说"边界"，所以描边比底色重半档。
    static let hoverStroke: Double = 0.07

    /// 玻璃描边渐变的两个端点：顶部受光 0.20 → 底部背光 0.07。
    /// 一条从左上到右下的淡出是"光从上面来"的唯一线索；两端都同值就退化成均匀描边，
    /// 而均匀描边在深色模式下会把胶囊画成灰圈。
    static let glassBorderTop: Double = 0.20
    static let glassBorderBottom: Double = 0.07

    /// 0.60：拖拽落点的强调色强度。落点是"临时接管注意力"的状态，比选中(0.16 底)更外显，
    /// 但不满值：满值的实色框会让人以为已经放下了。
    static let dropTargetStroke: Double = 0.60
}

// MARK: - 字号（R3）

enum VisualFont {
    /// 11pt：一切"次要到只用来定位"的字 —— 行内时间戳、详情 meta、菜单栏推荐理由的说明行。
    /// 它已经是这个 App 的下限：再小就跌破 HIG 的正文可读范围，暗色下 `.secondary` 会糊成一片。
    static let meta: CGFloat = 11

    /// 12pt：列表条目的标题（侧栏那一行、筛选段、多文件行的次行）。
    /// 密集列表里 12 是"能一行看两条信息"的最大值。
    static let row: CGFloat = 12

    /// 13pt：正文级最小可读值。**刻意引用规范本体而不是重抄一个 13** ——
    /// 状态文案的字号早就由 `StatePresentation` 定过一次，两处各写一个数就是"三处对齐"散掉的老路。
    static let body: CGFloat = StatePresentation.messageFontSize

    /// 14pt：区块标题（侧栏头部"时间剪史"、文件预览的文件名）。
    /// 它是这一族里唯一带 `.semibold` 也仍然安静的尺寸：标题要比内容响，但只响一档。
    static let title: CGFloat = 14
}

enum VisualGlyph {
    /// 10pt：行内小符号 —— "固定"徽标、多文件行的展开箭头。
    /// 徽标以前写 9：9pt 的 `pin.fill` 在 2× 下笔画会并在一起，而它表达的是"这条被钉住了"，
    /// 看不清等于没有状态。9 与 10 收成同一档，同时把下限抬到 10。
    static let badge: CGFloat = 10

    /// 11pt：16pt 小方块里的类型符号。它要比 12pt 的正文弱一档（缩略图才是主角），
    /// 又得还认得出图形 —— 9/10 的 `doc.fill` 在 2× 下会糊成一团墨。
    static let chipSymbol: CGFloat = 11

    /// 14pt：行首的类型图标（与 `row` 12pt 的标题并排时，图标要比字略大才同样显眼）。
    static let rowIcon: CGFloat = 14

    /// 16pt：播放控件条上的符号。以前同一排里播放键 16、静音键 15 ——
    /// 两个尺寸在同一根 22pt 高的条上，读起来像"这两个按钮不是一组"。
    static let control: CGFloat = 16

    /// 28 / 40：整块面板空出来的那个图标，两档按**可用面积**分：
    /// 详情区是一整列（40），侧栏与菜单只有窄窄一块（28）。
    /// 刻意不按"哪个页面"分：按页面分就会每页各调一次，又回到六个数字的状态。
    static let emptyCompact: CGFloat = 28
    static let emptyPane: CGFloat = 40

    /// 36pt：加载失败 / 读不到信息那类状态的大图标（以前 36 与 32 并存，
    /// 同一个"这里出问题了"在详情区里画出两种音量）。
    static let state: CGFloat = 36

    /// 48pt：文件预览里"没有缩略图"时顶上的占位符号。它比状态图标更大，
    /// 因为它不是提示，而是**内容本身**的替身。
    static let placeholder: CGFloat = 48
}

// MARK: - 材质

enum VisualMaterial {
    /// 窗口底：`.thickMaterial`。它是"桌面/别的应用透过来的那一层"，
    /// 所以必须是全 App 最实的一档 —— 正文要能在上面读到 13pt 的字。
    static let window: Material = .thickMaterial

    /// 透明玻璃底：`.ultraThinMaterial`，用在"浮在内容之上"的表面上（详情区整块底、
    /// 详情胶囊、视频控件）。刻意用最薄的一档：这三层都压在正文/缩略图上，
    /// 材质每厚一档，底下那点像素就更糊，而层级关系反而更看不出来。
    ///
    /// 类型写 `Material` 而不是 `UltraThinMaterial`：后者是 iOS 那边的具名结构体，
    /// macOS SDK 里不存在（写上去编不过，实测），几种厚薄都是同一个 `Material` 的静态成员。
    static let glass: Material = .ultraThinMaterial

    /// 筛选滑块的底：`.ultraThickMaterial` —— 它要在一块 `.quaternary` 轨道上"凸起来"，
    /// 材质比玻璃控件更实，才读得出前后关系。
    static let sliderPill: Material = .ultraThickMaterial

    /// 轨道与小方块的底：`.quaternary`，四级弱化色。它是"这里有个控件"，不是"这里有个面板"。
    /// 缩略图的类型占位符也用它：两颗 16pt 方块并排时，占位符必须比旁边的真图更退一步。
    static let track: HierarchicalShapeStyle = .quaternary
}
