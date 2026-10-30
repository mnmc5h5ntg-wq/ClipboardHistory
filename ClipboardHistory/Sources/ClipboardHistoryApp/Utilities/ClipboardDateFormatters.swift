import Foundation

/// R469：跨年记录的时间必须带年份。
///
/// 参照取**当前列表里最新的一条**，不是挂钟：同一年的历史仍保持 `M月d日 HH:mm` 的紧凑，
/// 只有跨年边界上的那几条加 `yyyy年`。挂钟参照会让所有旧记录一起变宽（夹具的 2025 记录
/// 在 2026 年全带年份），而"同一份历史里最早那条是哪一年"才是扫读时真正会混的地方。
enum TimestampYearPolicy {
    static func showsYear(for date: Date, relativeTo reference: Date?,
                          calendar: Calendar = .current) -> Bool {
        guard let reference else { return false }
        return calendar.component(.year, from: date) != calendar.component(.year, from: reference)
    }
}

enum ClipboardDateFormatters {
    static let sidebarTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "M月d日 HH:mm"
        return formatter
    }()

    static let sidebarTimeWithYear: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy年M月d日 HH:mm"
        return formatter
    }()

    static func sidebarTime(for date: Date, reference: Date?) -> String {
        TimestampYearPolicy.showsYear(for: date, relativeTo: reference)
            ? sidebarTimeWithYear.string(from: date)
            : sidebarTime.string(from: date)
    }

    static let detailTimestamp: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy年M月d日 HH:mm:ss"
        return formatter
    }()
}
