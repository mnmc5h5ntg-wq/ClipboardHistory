import XCTest
@testable import ClipboardHistoryApp

/// R442：关于页的版本行与文案。
///
/// 版本号只做展示：读不到就写"版本信息未读到"，不编占位；build 单独一档。
/// 像素那一半在 `UICaptureTests`：侧栏第 7 行在 1x 可画（`SETTINGS_ABOUT_ROW`），
/// 关于页的说明段进 `captionInkProbes`（2x 本地判，1x 具名 `CAPTION_NOT_RUN`）。
final class AboutPresentationTests: XCTestCase {
    func testVersionLineCombinesVersionAndBuild() {
        XCTAssertEqual(AboutPresentation.versionLine(shortVersion: "1.4.8", build: "1"),
                       "版本 1.4.8（build 1）")
        XCTAssertEqual(AboutPresentation.versionLine(shortVersion: "1.4.8", build: nil),
                       "版本 1.4.8")
        XCTAssertEqual(AboutPresentation.versionLine(shortVersion: "1.4.8", build: "  "),
                       "版本 1.4.8", "空白 build 被当成有 build")
        XCTAssertEqual(AboutPresentation.versionLine(shortVersion: nil, build: "1"),
                       "版本信息未读到", "版本读不到时编了占位")
        XCTAssertEqual(AboutPresentation.versionLine(shortVersion: "  ", build: nil),
                       "版本信息未读到")
    }

    func testResolvedVersionLinePrefersOverrides() {
        XCTAssertEqual(AboutPresentation.resolvedVersionLine(shortVersionOverride: "9.9.9",
                                                             buildOverride: "42"),
                       "版本 9.9.9（build 42）")
    }

    func testAboutCategoryIsInTheSidebarList() {
        XCTAssertTrue(SettingsCategory.allCases.contains(.about), "关于没进侧栏分区")
        XCTAssertEqual(SettingsCategory.about.title, "关于")
        XCTAssertEqual(SettingsCategory.about.icon, "info.circle")
    }

    func testCopyrightAndTaglineArePinned() {
        XCTAssertEqual(AboutPresentation.appName, "时间剪史")
        XCTAssertTrue(AboutPresentation.tagline.contains("离线"),
                      "定位句没提离线 —— 这是这个应用最重要的一条")
        XCTAssertTrue(AboutPresentation.copyright.contains("2026"),
                      "版权年份不是常量 ⇒ 帧会随年份漂移")
    }
}
