import Foundation

/// 「按 App 排除」名单的增删与回执（视觉迭代 R8 / 审计 B-P2）。
///
/// 为什么要有这个纯函数：`CapturePolicy.encodeUserExcluded` 会 **去重 + 排序**，
/// 于是设置页那台"添加"按钮有三种结局（加进去了 / 本来就有 / 它属于系统默认排除项），
/// 而界面上**一种都看不出来** —— 输入框被清空、列表没变长，
/// 用户读到的是"我加的那条去哪了"。判定收在这里，视图侧只负责摆出来。
///
/// 与 `ClearHistoryReceiptPolicy`（R6）同一族：**做了什么都要说，没做成更要说**。
enum ExcludedAppListPolicy {
    enum Outcome: Equatable {
        /// 名单真的长了。
        case added(String)
        /// 用户名单里已经有这条 ⇒ 什么都不该变。
        case alreadyListed(String)
        /// 系统默认排除项已经覆盖它 ⇒ 加不加行为完全一样，必须说清楚，
        /// 否则用户会以为"加了没生效"，转而去做更危险的事（比如整个暂停采集）。
        case coveredByDefault(String)
        /// 输入是空的或纯空格。
        case emptyInput
        /// 从名单里移出去了。
        case removed(String)
        /// 要移除的 id 不在用户名单里（可能是默认项，被误点了"移除"）。
        case notListed(String)
    }

    struct Result: Equatable {
        /// 新的持久化值。没做成时也给出**原值**，调用点可以无脑赋值。
        let raw: String
        let outcome: Outcome
        /// 给用户看的那一句。永远非空 —— 沉默是这一族缺陷的本体。
        let receipt: String
    }

    /// 加一条。`raw` 是 `UserDefaults` 里那份未解码的字符串。
    static func add(_ input: String,
                    to raw: String,
                    defaults: Set<String> = CapturePolicy.defaultExcludedBundleIDs) -> Result {
        let id = input.trimmingCharacters(in: .whitespacesAndNewlines)
        if id.isEmpty {
            return Result(raw: raw, outcome: .emptyInput,
                          receipt: "先填一个 App 的标识（Bundle ID），例如 com.example.app。")
        }
        let current = CapturePolicy.decodeUserExcluded(raw)
        if current.contains(id) {
            return Result(raw: raw, outcome: .alreadyListed(id),
                          receipt: "「\(id)」已经在名单里，不用重复添加。")
        }
        if defaults.contains(id) {
            return Result(raw: raw, outcome: .coveredByDefault(id),
                          receipt: "「\(id)」属于系统默认排除项，本来就不入库，不用再加。")
        }
        let next = CapturePolicy.encodeUserExcluded(Array(current) + [id])
        return Result(raw: next, outcome: .added(id),
                      receipt: "已加入名单：「\(id)」不再自动入库；你主动拖进来的内容仍然会记录。")
    }

    /// 移一条。
    static func remove(_ id: String, from raw: String) -> Result {
        let current = CapturePolicy.decodeUserExcluded(raw)
        guard current.contains(id) else {
            return Result(raw: raw, outcome: .notListed(id),
                          receipt: "「\(id)」不在这份用户名单里。")
        }
        let next = CapturePolicy.encodeUserExcluded(Array(current).filter { $0 != id })
        return Result(raw: next, outcome: .removed(id),
                      receipt: "已移出名单：「\(id)」的复制会重新入库。")
    }
}
