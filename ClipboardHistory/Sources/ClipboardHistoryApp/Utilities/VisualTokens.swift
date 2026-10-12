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

    /// 0.10：44pt 圆形符号按钮的悬停底色。面积只有行的一小条，同强度下读不出"按这里"，
    /// 所以整档抬高 —— 这是尺寸差造成的，不是口味差。
    static let controlHover: Double = 0.10

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
