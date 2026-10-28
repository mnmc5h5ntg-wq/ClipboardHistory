import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R472：设置隐私卡里的存储路径要用等宽字体。
///
/// 路径是逐字符读的值；比例字体下 `i/l/1` 与斜杠的步进不齐。判据读字体自己的
/// `isFixedPitch`（结构量）与 "~/" 的拆分；像素帧 `settings-privacy-tall/-excluded` 看视觉。
final class SettingsPathPresentationTests: XCTestCase {
    func testSplitsAtTildeSlash() {
        let parts = SettingsPathPresentation.split("保存位置：~/Library/Application Support/时间剪史/")
        XCTAssertEqual(parts.prefix, "保存位置：")
        XCTAssertEqual(parts.path, "~/Library/Application Support/时间剪史/")
    }

    func testNoPathLeavesTextWhole() {
        let parts = SettingsPathPresentation.split("这是一段没有路径的说明")
        XCTAssertEqual(parts.prefix, "这是一段没有路径的说明")
        XCTAssertNil(parts.path)
    }

    func testPathFontIsFixedPitchAndBodyFontIsNot() {
        XCTAssertTrue(SettingsPathPresentation.pathFont.isFixedPitch,
                      "路径字体不是等宽 ⇒ 路径仍按比例步进")
        let body = NSFont.systemFont(ofSize: SettingsPathPresentation.pathFont.pointSize)
        XCTAssertFalse(body.isFixedPitch,
                       "同字号的系统正文字体本来就是比例字体 ⇒ 两臂分得开")
    }
}
