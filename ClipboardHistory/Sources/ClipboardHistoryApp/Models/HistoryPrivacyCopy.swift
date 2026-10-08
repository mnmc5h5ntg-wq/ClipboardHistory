import Foundation

enum HistoryPrivacyCopy {
    static let storageTitle = "历史与隐私"

    static let storageSummary = "时间剪史会把剪贴板历史保存在本机，仅用于重启后恢复记录。"

    static let storageLocation = "保存位置：~/Library/Application Support/时间剪史/"

    static let capturedContent = "保存内容：文本、图片、文件引用和预览缩略图。文件记录保存原文件路径，用于再次复制。"

    static let retentionPolicy = "普通历史默认保留 500 条 / 30 天；收藏项会长期保留，不受自动清理影响。"

    static let clearBehavior = "清空历史只会删除未收藏记录；需要移除收藏内容时，请先取消收藏或删除对应条目。"

    static let sensitiveContentReminder = "剪贴板可能包含密码、验证码、截图或聊天内容。复制敏感内容后，建议及时删除对应历史。"

    static let settingsBullets = [
        storageLocation,
        capturedContent,
        retentionPolicy,
        clearBehavior,
        sensitiveContentReminder
    ]
}
