import XCTest
@testable import ClipboardHistoryApp

/// R519：关于页的 GitHub 入口。URL 只能有一个来源；界面必须走 `Link`，不能画成普通文字。
final class AboutPageGitHubLinkTests: XCTestCase {
    private func source(_ relative: String) throws -> String {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/\(relative)")
        return try String(contentsOf: url, encoding: .utf8)
    }

    func testGitHubURLHasOneSourceAndTheAboutPageUsesALink() throws {
        XCTAssertEqual(AboutPresentation.githubURLString,
                       "https://github.com/mnmc5h5ntg-wq/ClipboardHistory")
        let presentation = try source("Utilities/AboutPresentation.swift")
        XCTAssertEqual(presentation.components(separatedBy: "github.com/mnmc5h5ntg-wq").count - 1, 1,
                       "GitHub URL 只许在 AboutPresentation 里出现一次")
        let settings = try source("Views/SettingsView.swift")
        XCTAssertTrue(settings.contains("Link(\"GitHub 项目主页 ↗\", destination: githubURL)"),
                      "关于页没有把 GitHub 入口画成 Link")
        XCTAssertTrue(settings.contains("AboutPresentation.githubURLString"),
                      "关于页没有引用唯一的 URL 常量")
        XCTAssertFalse(settings.contains("github.com/mnmc5h5ntg-wq"),
                       "关于页不许复制 URL 字面量")
        let appDelegate = try source("Managers/AppDelegate.swift")
        XCTAssertTrue(appDelegate.contains("AboutPresentation.githubURLString"),
                      "帮助菜单/关于面板没有引用唯一的 URL 常量")
        XCTAssertFalse(appDelegate.contains("github.com/mnmc5h5ntg-wq"),
                       "帮助菜单/关于面板不许复制 URL 字面量")
    }
}
