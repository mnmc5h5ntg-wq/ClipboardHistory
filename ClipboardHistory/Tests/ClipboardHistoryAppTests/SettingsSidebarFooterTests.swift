// R426：设置侧栏底部「时间剪史 <版本>」脚注 —— 读不到版本时只写应用名，不编假号。
// 像素正/负/最小窗三臂在 UICaptureHarness 的 settings-general / settings-general-no-footer / settings-min。
import XCTest
@testable import ClipboardHistoryApp

final class SettingsSidebarFooterTests: XCTestCase {

    func testVersionTextCarriesANonBlankShortVersion() {
        XCTAssertEqual(SettingsSidebarFooterPolicy.versionText(shortVersion: "1.4.8"), "时间剪史 1.4.8")
        XCTAssertEqual(SettingsSidebarFooterPolicy.versionText(shortVersion: " 1.4.8 "), "时间剪史 1.4.8")
    }

    func testVersionTextFallsBackToTheAppNameOnly() {
        XCTAssertEqual(SettingsSidebarFooterPolicy.versionText(shortVersion: nil), "时间剪史")
        XCTAssertEqual(SettingsSidebarFooterPolicy.versionText(shortVersion: ""), "时间剪史")
        XCTAssertEqual(SettingsSidebarFooterPolicy.versionText(shortVersion: " \n\t "), "时间剪史")
    }

    func testResolvedTextPrefersTheCaptureOverride() {
        XCTAssertEqual(SettingsSidebarFooterPolicy.resolvedVersionText(override: "1.4.8"),
                       "时间剪史 1.4.8")
        XCTAssertTrue(SettingsSidebarFooterPolicy.resolvedVersionText(override: "  ")
                        .hasPrefix(SettingsSidebarFooterPolicy.appName),
                      "空白覆盖值必须退回真实 bundle，而不是写一个空版本")
    }

    func testSidebarWiresTheFooterAndTheCaptureNegativeArm() throws {
        let sidebar = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(sidebar.contains("SettingsSidebarFooterPolicy.resolvedVersionText(override: versionForCapture)"),
                      "设置窗口没有从 policy 取版本行文案")
        XCTAssertTrue(sidebar.contains("SettingsSidebarFooter(text: footerText)"),
                      "设置窗口没有挂版本脚注")
        XCTAssertTrue(sidebar.contains("if footerForCapture != false"),
                      "负臂开关不是「只有夹具写 false」的形状 ⇒ 产品可能被它关掉")
        XCTAssertTrue(sidebar.contains("                if footerForCapture != false {\n"
                                       + "                    SettingsSidebarFooter(text: footerText)\n"
                                       + "                }\n"
                                       + "                Spacer()"),
                      "版本行不在导航行之后（或又被挪到窗口下沿）⇒ 最小窗会把它裁在框外")

        let footer = codeOnly(try productSource(named: "Views/SettingsSidebarFooter.swift"))
        XCTAssertTrue(footer.contains("Color(nsColor: .secondaryLabelColor)"),
                      "侧栏在 vibrant 材质里：脚注没有用动态系统色 ⇒ 亮档可能看不见")
        XCTAssertTrue(footer.contains(".font(.system(size: VisualFont.meta))"),
                      "脚注没有走字号令牌")
        XCTAssertTrue(footer.contains(".padding(.leading, 16)"),
                      "脚注左沿不在侧栏内容轴 16pt 上")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "SettingsSidebarFooterTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
