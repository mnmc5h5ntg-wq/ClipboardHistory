import Foundation

/// 快捷键冲突：同一组键被两个动作同时占用时，系统只会把热键递给其中一个 ——
/// 另一个动作在界面上看起来"设好了"，按下去却没有反应。设置页必须把这句话说出来。
///
/// 纯函数（C-5 同一条规矩）：三个页面共用同一份判定，视图只负责画。
enum ShortcutConflictPolicy {
    struct Conflict: Equatable {
        let firstName: String
        let secondName: String
        let shortcut: String
    }

    /// 按行顺序两两比较；同一组快捷键只报一对，不重复报 (A,B) 与 (B,A)。
    static func conflicts(_ rows: [(name: String, shortcut: HotKeyShortcut)]) -> [Conflict] {
        var result: [Conflict] = []
        guard rows.count > 1 else { return result }
        for first in 0..<(rows.count - 1) {
            for second in (first + 1)..<rows.count
            where rows[first].shortcut == rows[second].shortcut {
                result.append(Conflict(firstName: rows[first].name,
                                       secondName: rows[second].name,
                                       shortcut: rows[first].shortcut.displayString))
            }
        }
        return result
    }
}
