import SwiftUI

/// R538（626）：行右键菜单的呈现与动作。旧值：`.contextMenu` 挂在行内容上时被
/// SwiftUI Text/cell 的系统文本菜单盖住（真机两次 117×165 撤销/剪切/复制/粘贴/全选）；
/// 改挂到 List 的 `contextMenu(forSelectionType:)`（macOS 13+），由列表层接管右键。
enum RowContextMenu {
    enum Action {
        case copy
        case favorite
    }

    static func title(for action: Action, isFavorite: Bool) -> String {
        switch action {
        case .copy: return "复制"
        case .favorite: return FavoriteTogglePresentation.helpText(isFavorite: isFavorite)
        }
    }

    static func systemImage(for action: Action, isFavorite: Bool) -> String {
        switch action {
        case .copy: return "doc.on.doc"
        case .favorite: return FavoriteTogglePresentation.symbolName(isFavorite: isFavorite)
        }
    }

    static func perform(_ action: Action, copy: () -> Void, favorite: () -> Void) {
        switch action {
        case .copy: copy()
        case .favorite: favorite()
        }
    }
}
