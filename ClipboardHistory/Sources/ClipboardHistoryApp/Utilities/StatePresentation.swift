import SwiftUI

/// 状态呈现规范（第三轮审计 §4 U-5）。
///
/// 审计的问题是"三态分散"：`NoticeBanner`（两种 tone）、`EmptyStateView`、菜单栏的
/// "正在整理推荐…"、详情区的加载 —— 字号、对齐、图标风格各写各的，同一件"现在在加载"
/// 在四个地方长得像四件事。这个文件把它收成一份常数 + 一个纯函数映射，
/// 于是"统一"这件事有判据而不是有共识。
///
/// 刻意只放**判定**，不放视图：视图各有布局（横幅有分隔线、空态占满整块），
/// 但字号、图标色系、动作按钮文案、对齐规则必须同源。
enum StatePresentation {
    enum Kind {
        case loading
        case empty
        case warning
        case error
    }

    /// 落在什么表面上。对齐规则看这个，不看 kind。
    enum Surface {
        /// 占满一整块区域的空态（详情区没选中条目、列表没有记录）。
        case pane
        /// 一条横幅、菜单里的一行 —— 有明确的阅读起点，必须左对齐。
        case inline
    }

    /// 状态文案的字号。统一取 13：正文级最小可读值，也是 HIG 里 secondary 文案的常用值。
    /// （空态原来 13、横幅用 `.callout`≈11–13 随系统文字大小、菜单栏那行没设字号 ——
    /// 三者不一致就是这么来的。）
    static let messageFontSize: CGFloat = 13

    /// 图标比文字小一档：状态的主角是那一句人话，图标是配角，不该比正文更抢眼。
    static let symbolFontSize: CGFloat = 12

    static let dismissActionTitle = "知道了"

    /// 正文用哪一档墨（R24 / U-46）。
    ///
    /// 这条以前没有：**四个状态共用 `.secondary`**。量出来的后果是亮色模式下提示条正文
    /// 只有 **3.82–3.92:1**（`notice-banner` 两条 3.90/3.85，真窗口里 3.92/3.82），
    /// 而它自己那枚"知道了"是 **12.28:1** —— 同一条横幅里，"下一步"比"发生了什么"清楚三倍。
    /// WCAG 对 13pt 常规文字的要求是 4.5:1，也就是说这句"你的数据出问题了"**不达 AA**。
    ///
    /// 为什么按 kind 分而不是按 surface 分：真正决定该不该抢眼的不是它画在哪，而是
    /// **"这件事需不需要被读到"**。警告与错误的正文就是这件事本身 ⇒ `.prominent`；
    /// 加载与空态是背景信息（"还在算"、"没东西"）⇒ 留在 `.subdued`，
    /// 不给菜单栏那行"正在整理推荐…"和热图空态升档（那才是喧宾夺主）。
    /// 暗色模式下 secondary 本来就有 5.26–5.58:1，升档后一起到 10:1 以上 —— 这条不是"修暗色"，
    /// 是把"严重度"与"可读性"从同一个源头拿出来。
    ///
    /// 返回档位而不是返回 `AnyShapeStyle`：`AnyShapeStyle` 不可比较，真值表就没法写
    /// （这一族的规矩见 `alignment(for:)` 返回 `HorizontalAlignment`）。
    /// 接线那一层（谁真的把档位换成了墨）由像素判据守着：`testNoticeBodyTextStaysReadable`。
    enum MessageInk: Equatable {
        case prominent
        case subdued
    }

    static func messageInk(for kind: Kind) -> MessageInk {
        switch kind {
        case .warning, .error: return .prominent
        case .loading, .empty: return .subdued
        }
    }

    /// 档位到墨的映射。只有这一处认识 `.primary` / `.secondary`，判据也只需要盯这一处。
    static func messageInkStyle(for kind: Kind) -> AnyShapeStyle {
        switch messageInk(for: kind) {
        case .prominent: return AnyShapeStyle(.primary)
        case .subdued: return AnyShapeStyle(.secondary)
        }
    }

    /// 整块 pane 状态句的墨（R397/R398：空态与加载态）。
    ///
    /// `StateLine` 的 inline 状态（菜单栏"暂无推荐"、热图空态）留在 `.subdued` 是对的：
    /// 它旁边还有内容，句子只是背景。但整块面板只剩这句话时，同一档 `.secondary`
    /// 在亮档实测只有 **2.90:1**（空态）/ **2.86:1**（加载态），连 AA 正文线都不到 ——
    /// 这不是"安静"，是"唯一的信息读不清"。pane 这一档单独抬到 0.85（0.72 实测亮档
    /// 仍只有 3.71:1，差值不是文字边缘能补的），仍比正文轻，但必须过 4.5。
    static var paneMessageInkStyle: AnyShapeStyle {
        AnyShapeStyle(Color.primary.opacity(0.85))
    }

    /// 对齐规则（纯函数，可断言）。
    ///
    /// 审计写的是"统一左对齐"，但**整块面板里的空态居中是 macOS 的既有语言**
    /// （Finder 的空文件夹、Xcode 的空结果都是居中）。一刀切左对齐会让它看起来像坏了。
    /// 所以这里把规则说清楚：**内联的状态（横幅、菜单行）左对齐；占满整块的空态居中，
    /// 但居中块内部的多行文字仍然左对齐**（避免居中的参差行）。
    static func alignment(for surface: Surface) -> HorizontalAlignment {
        switch surface {
        case .pane: return .center
        case .inline: return .leading
        }
    }

    /// 每个状态的图标。`empty` 的图标由调用方给（"没有历史记录"和"没有收藏"该画不同的东西），
    /// 所以这里只钉住三个**有确定含义**的状态。
    static func symbolName(for kind: Kind) -> String {
        switch kind {
        case .loading: return "arrow.triangle.2.circlepath"
        case .warning: return "exclamationmark.arrow.circlepath"
        case .error: return "exclamationmark.triangle.fill"
        case .empty: return "tray"
        }
    }

    /// 图标颜色。只有 error 允许抢一眼 —— 它意味着"你的数据出问题了"；
    /// 警告是橙色（要读但不必慌），加载与空态用 `.secondary`，不许用强调色
    /// （菜单栏那行"正在整理推荐…"以前跟着系统强调色走，看起来像选中了某条推荐）。
    static func iconStyle(for kind: Kind) -> AnyShapeStyle {
        switch kind {
        case .loading, .empty: return AnyShapeStyle(.secondary)
        case .warning: return AnyShapeStyle(Color.orange)
        case .error: return AnyShapeStyle(Color.red)
        }
    }

    /// 底色调（横幅用；空态/加载不着底）。
    static func backgroundStyle(for kind: Kind) -> AnyShapeStyle {
        switch kind {
        case .error: return AnyShapeStyle(Color.red.opacity(0.10))
        case .warning: return AnyShapeStyle(Color.orange.opacity(0.12))
        case .loading, .empty: return AnyShapeStyle(Color.clear)
        }
    }

    /// 一句话的人话规范：**说清发生了什么 + 说清下一步**，不许只报状态码。
    ///
    /// 动作位的规则（纯函数存在是为了让它可断言）：
    /// - 加载态**不放**按钮：那会儿按什么都没有意义，放一个只会让人以为点了能取消；
    /// - 空态放调用方给的那一个（"无匹配结果 → 清除搜索"是真下一步；没有就不放）；
    /// - 警告与错误默认就是"知道了"，调用方给了别的（"打开历史文件夹"）就用别的。
    static func actionTitle(for kind: Kind, provided: String?) -> String? {
        switch kind {
        case .loading: return nil
        case .empty: return provided
        case .warning, .error: return provided ?? dismissActionTitle
        }
    }
}

/// 一行的状态呈现：图标 + 一句人话（+ 可选一个动作）。
///
/// 审计要的是"三处对齐"，而只发一份常数表对不齐 —— 三处各自 `HStack { Image; Text }`
/// 迟早会漂（间距、baseline、谁带 Spacer 都不一样）。所以把这一行本身做成组件：
/// 横幅、菜单栏状态行、以及任何"内联状态"都从这里出，`EmptyStateView` 是它的整块面板版本。
struct StateLine: View {
    let kind: StatePresentation.Kind
    let message: String
    /// 空态之类的图标由场景决定，允许覆盖规范里的默认符号。
    var systemName: String? = nil
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        // **图标与文字按基线成一组，动作按钮相对整组垂直居中**（R25 / U-47 / D-084）。
        //
        // 以前整行是 `HStack(alignment: .firstTextBaseline)`，于是两三行的横幅里那颗"知道了"
        // 跟着**第一行**走。量出来的偏差（按钮字形那一行的中心 vs 色带中心）：
        // 单行 0pt（碰巧对）、两行 **7.5pt**、三行 **14.5pt** —— 读起来像"这个动作只管第一句"，
        // 而系统那类顶部提示条（邮件 / 备忘录 / 设置里的内联警告）动作位都是垂直居中的。
        //
        // 为什么不是整行改成 `.center`：那会把图标从文字的基线上摘下来，
        // 12pt 的符号压在 13pt 正文旁边会"浮"半格（R3 定的"图标比正文小一档"就白定了）。
        // 所以内层继续 baseline 对齐，只有动作位换一根对齐轴。
        // `action` 这条路径今天只有 `NoticeBanner` 在用（菜单栏那行与热图空态都没有按钮），
        // 所以这一改的影响面就是横幅本身。
        HStack(spacing: 10) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Image(systemName: systemName ?? StatePresentation.symbolName(for: kind))
                    .font(.system(size: StatePresentation.symbolFontSize))
                    .foregroundStyle(StatePresentation.iconStyle(for: kind))
                    .accessibilityHidden(true)

                Text(message)
                    .font(.system(size: StatePresentation.messageFontSize))
                    .foregroundStyle(StatePresentation.messageInkStyle(for: kind))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    // 只允许纵向折行：横向 `fixedSize` 会把整块面板撑宽，
                    // 而状态文案恰恰是最长的那种（"拖入的 N 项不是本机文件，未加入历史"）。
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            if let actionTitle, let action {
                Button(actionTitle, action: action)
                    .controlSize(.small)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
