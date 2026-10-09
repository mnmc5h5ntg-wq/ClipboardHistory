import AppKit
import SwiftUI
import UniformTypeIdentifiers

/// 把一条记录拖出去（审计第二轮 1.5 / 账本 R2-05：全仓 `onDrag`/`draggable`/`NSItemProvider`/`onDrop` 零命中，
/// 而"把某条记录拖到 Finder 或别的 App"正是剪贴板管理器最该有的 affordance 之一）。
///
/// 用 `onDrag`（macOS 10.15+）而**不是** `.draggable`：后者是 macOS 13 的 `Transferable`，
/// 本项目部署下限是 macOS 12。
///
/// 载荷规划是纯函数（`payload(for:)`），所以"哪种内容拖出去是什么"可以被单测；
/// 真正与系统交互的只有 `itemProvider(for:)` 那一层薄封装。
enum EntryDragPayload: Equatable {
    case text(String)
    case png(Data)
    case fileURL(URL)
}

enum EntryDragPlanner {
    /// 返回 `nil` = 这一条**不提供拖拽**。
    ///
    /// 刻意不给"拖起来什么也不会发生"的假 affordance，也不给"拖 3 个文件只落地 1 个"的半截动作：
    /// 多文件条目需要 `NSView` 级的 dragging session 才能一次拖出多个 item，本轮不做（账本 R2-05 记为部分完成）。
    static func payload(for content: ClipboardEntryContent) -> EntryDragPayload? {
        switch content {
        case .text(let string):
            guard !string.isEmpty else { return nil }
            return .text(string)
        case .image(let image):
            guard let data = image.pngData(), !data.isEmpty else { return nil }
            return .png(data)
        case .file(let url):
            // 只拖真实文件 URL：Web URL 拖进 Finder 没有意义，而且 P-15 那一类
            // "把 Web URL 当文件"的混淆就是从这里开始的。
            guard url.isFileURL else { return nil }
            return .fileURL(url)
        case .files:
            return nil
        }
    }

    static func itemProvider(for payload: EntryDragPayload) -> NSItemProvider {
        let provider = NSItemProvider()
        switch payload {
        case .text(let string):
            provider.registerObject(string as NSString, visibility: .all)
        case .png(let data):
            provider.registerDataRepresentation(
                forTypeIdentifier: UTType.png.identifier,
                visibility: .all
            ) { completion in
                completion(data, nil)
                return nil
            }
        case .fileURL(let url):
            // `NSURL` 自己实现 `NSItemProviderWriting`：文件 URL 会登记成 `public.file-url`。
            // 交出的是引用 —— 不复制、也绝不删除原文件。
            provider.registerObject(url as NSURL, visibility: .all)
        }
        return provider
    }

    /// 视图侧的便捷入口：没有可拖的载荷时返回 nil，调用方据此决定挂不挂 `onDrag`。
    /// 名字里带 `Content` 是必要的：`ClipboardEntryContent.text("x")` 与
    /// `EntryDragPayload.text("x")` 形状相同，同名重载会让调用点变成 "ambiguous use of 'text'"。
    static func itemProvider(forContent content: ClipboardEntryContent) -> NSItemProvider? {
        guard let payload = payload(for: content) else { return nil }
        return itemProvider(for: payload)
    }
}

/// 有载荷才挂 `onDrag`。SwiftUI 没有"条件性 modifier"，所以分两条路径：
/// 给没有载荷的条目挂一个返回空 provider 的 `onDrag`，会让用户拖起来毫无反应 —— 比不挂更糟。
struct EntryDragModifier: ViewModifier {
    let content: ClipboardEntryContent

    @ViewBuilder
    func body(content: Content) -> some View {
        if EntryDragPlanner.payload(for: self.content) != nil {
            content.onDrag {
                EntryDragPlanner.itemProvider(forContent: self.content) ?? NSItemProvider()
            }
        } else {
            content
        }
    }
}
