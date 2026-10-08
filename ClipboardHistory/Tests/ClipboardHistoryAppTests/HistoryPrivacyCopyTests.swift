import XCTest
@testable import ClipboardHistoryApp

final class HistoryPrivacyCopyTests: XCTestCase {
    func testSettingsCopyExplainsPersistenceRetentionAndSensitiveContent() {
        let combinedCopy = ([HistoryPrivacyCopy.storageSummary] + HistoryPrivacyCopy.settingsBullets)
            .joined(separator: "\n")

        XCTAssertTrue(combinedCopy.contains("本机"))
        XCTAssertTrue(combinedCopy.contains("~/Library/Application Support/时间剪史/"))
        XCTAssertTrue(combinedCopy.contains("文本、图片、文件引用"))
        XCTAssertTrue(combinedCopy.contains("500 条 / 30 天"))
        XCTAssertTrue(combinedCopy.contains("收藏项会长期保留"))
        XCTAssertTrue(combinedCopy.contains("清空历史只会删除未收藏记录"))
        XCTAssertTrue(combinedCopy.contains("密码、验证码、截图或聊天内容"))
    }
}
