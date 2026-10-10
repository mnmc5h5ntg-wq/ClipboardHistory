import Foundation

/// "暂停记录"与"识别截图文字"这两个总开关的判据（第三轮审计 D-3，§5 的 F1/F4）。
///
/// 放在这里而不是写在 `HistoryStore` 里，是为了让**两个方向都可判**：
/// 暂停时"自动采集不入库、但用户明确要求的导入照旧入库"，这个区别用布尔函数写出来
/// 才能被一条真值表用例钉住；写在 if 里就只剩"看起来生效"。
enum RecordingGate {
    /// 这一笔要不要入库。
    /// - Parameter isUserInitiated: 用户明确发起的动作（拖入文件、手动添加）。
    ///   暂停的是**后台自动采集**，不是用户点名要存的东西 —— 把两者混在一起挡掉，
    ///   会出现"我明明拖进去了却没存"这种更难解释的失灵。
    static func accepts(isPaused: Bool, isUserInitiated: Bool) -> Bool {
        if isUserInitiated { return true }
        return !isPaused
    }

    /// OCR 任务要不要排。关掉开关后不再对图片排识别任务（也不写 ocrText）。
    static func schedulesOCR(isEnabled: Bool, hasImage: Bool) -> Bool {
        isEnabled && hasImage
    }
}
