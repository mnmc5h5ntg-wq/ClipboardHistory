import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R-54：图标按钮的可访问名字。
///
/// 为什么用静态扫描而不是运行时断言：离屏窗口的无障碍树根本不会被 SwiftUI 建立
/// （实测从 NSHostingView 做 BFS 只能走到根节点，`已遍历 1 个节点，标签样本=[]`），
/// 所以"VoiceOver 到底读到什么"在这个环境里无法验证 —— 与其留一条永远测不到的断言，
/// 不如把**可静态证明的那一半**钉住：所有悬浮提示都必须同时给出无障碍标签。
final class AccessibilityLabelHygieneTests: XCTestCase {
    private func sourcesRoot() throws -> URL {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            if FileManager.default.fileExists(atPath: candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true).path) {
                return candidate.appendingPathComponent("Sources", isDirectory: true)
            }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到包根目录的 Sources")
    }

    private func codeLines(of url: URL) throws -> [String] {
        let text = try String(contentsOf: url, encoding: .utf8)
        return text.split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.hasPrefix("//") && !$0.hasPrefix("///") && !$0.hasPrefix("*") }
    }

    /// 界面层不得再出现裸 `.help(`：一律走 `helpLabel(_:)`，它同时上 help 与 accessibilityLabel。
    func testViewsNeverUseBareHelpWithoutAccessibilityLabel() throws {
        let root = try sourcesRoot()
        let views = root.appendingPathComponent("ClipboardHistoryApp/Views", isDirectory: true)
        let helper = "ViewExtensions.swift"   // 定义 helpLabel 的地方，允许出现 .help(
        var offenders: [String] = []

        let enumerator = FileManager.default.enumerator(at: views, includingPropertiesForKeys: nil)
        while let file = enumerator?.nextObject() as? URL {
            guard file.pathExtension == "swift", file.lastPathComponent != helper else { continue }
            let hits = try codeLines(of: file).filter { $0.contains(".help(") }
            if !hits.isEmpty {
                offenders.append("\(file.lastPathComponent): \(hits.count) 处裸 .help(")
            }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "这些视图只给了悬浮提示、没给无障碍标签（VoiceOver 读不到）：\(offenders)")
    }

    /// 定义处必须两件事都做，否则上面的扫描等于放了空炮。
    func testHelpLabelActuallySetsBothAttributes() throws {
        let root = try sourcesRoot()
        let url = root.appendingPathComponent("ClipboardHistoryApp/Views/ViewExtensions.swift")
        let body = try codeLines(of: url).joined(separator: "\n")
        XCTAssertTrue(body.contains("func helpLabel"), "helpLabel 定义不见了")
        XCTAssertTrue(body.contains(".help(text)") && body.contains(".accessibilityLabel(text)"),
                      "helpLabel 必须同时上 help 与 accessibilityLabel，否则守卫是假的")
    }

    /// 图片视图必须要么给自己一个名字、要么显式声明"我是装饰"（审计第二轮 1.11）。
    /// 标签一律是固定文案：缩略图里可能是截图带出来的密码或聊天记录，
    /// 所以这里钉的是"有名字"，绝不是"名字里带内容"。
    func testImageViewsEitherNameThemselvesOrDeclareThemselvesDecorative() throws {
        let root = try sourcesRoot()
        let cases: [(file: String, needles: [String])] = [
            ("ClipboardHistoryApp/Views/ThumbnailView.swift", ["图片缩略图", "accessibilityHidden(true)"]),
            ("ClipboardHistoryApp/Views/ImagePreviewView.swift", ["图片内容"])
        ]
        for entry in cases {
            let url = root.appendingPathComponent(entry.file)
            let text = try String(contentsOf: url, encoding: .utf8)
            for needle in entry.needles {
                XCTAssertTrue(text.contains(needle),
                              "\(entry.file) 里找不到 \(needle)：真图片要有标签，占位符号要显式标为装饰")
            }
        }
    }
}
