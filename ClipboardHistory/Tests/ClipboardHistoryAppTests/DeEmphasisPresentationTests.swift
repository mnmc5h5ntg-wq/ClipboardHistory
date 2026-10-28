import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R454：弱化正文（完成项/删除线）的对比度。
///
/// R450/R453 用了 `secondaryLabelColor`：亮档 3.95:1，低于 14pt 正文的 4.5:1
///（仓库里引用块早因同一原因拒绝过它）。这里钉动态弱化色在两档都 ≥4.5，
/// 且仍然比正文弱；像素那一半在 `UICaptureTests.testDeEmphasizedTextMeetsContrast`。
@MainActor
final class DeEmphasisPresentationTests: XCTestCase {
    private func resolved(_ color: NSColor, _ name: NSAppearance.Name) -> NSColor {
        var out = color
        NSAppearance(named: name)?.performAsCurrentDrawingAppearance {
            out = color.usingColorSpace(.sRGB) ?? color
        }
        return out
    }

    private func composite(_ fg: NSColor, over bg: NSColor) -> (Double, Double, Double) {
        let a = fg.alphaComponent
        return (fg.redComponent * a + bg.redComponent * (1 - a),
                fg.greenComponent * a + bg.greenComponent * (1 - a),
                fg.blueComponent * a + bg.blueComponent * (1 - a))
    }

    private func relativeLuminance(_ rgb: (Double, Double, Double)) -> Double {
        func channel(_ c: Double) -> Double {
            c <= 0.04045 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * channel(rgb.0) + 0.7152 * channel(rgb.1) + 0.0722 * channel(rgb.2)
    }

    private func contrast(_ a: (Double, Double, Double), _ b: (Double, Double, Double)) -> Double {
        let la = relativeLuminance(a)
        let lb = relativeLuminance(b)
        let hi = max(la, lb), lo = min(la, lb)
        return (hi + 0.05) / (lo + 0.05)
    }

    func testDeEmphasisColorMeetsBodyTextContrast() {
        for name in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = name == .darkAqua ? "dark" : "light"
            let bg = resolved(.windowBackgroundColor, name)
            let fg = resolved(DeEmphasisPresentation.textColor, name)
            let ratio = contrast(composite(fg, over: bg),
                                 (bg.redComponent, bg.greenComponent, bg.blueComponent))
            XCTAssertGreaterThanOrEqual(ratio, 4.5,
                                        "\(tag)：弱化正文对比 \(String(format: "%.2f", ratio)):1"
                                        + " 低于 14pt 正文 4.5:1（旧 secondary 亮档 3.95）")
            let label = resolved(.labelColor, name)
            let labelComposite = composite(label, over: bg)
            let dim = composite(fg, over: bg)
            let dimDiffers = abs(dim.0 - labelComposite.0) > 0.05
                || abs(dim.1 - labelComposite.1) > 0.05
                || abs(dim.2 - labelComposite.2) > 0.05
            XCTAssertTrue(dimDiffers, "\(tag)：弱化色与正文同色 ⇒ 没有弱化")
        }
    }

    func testTaskAndStrikeUseTheSameDeEmphasisColor() {
        for name in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = name == .darkAqua ? "dark" : "light"
            let base = resolved(DeEmphasisPresentation.textColor, name)
            let task = resolved(TaskItemPresentation.completedTextColor, name)
            let strike = resolved(MarkdownPresentation.struckTextColor, name)
            XCTAssertTrue(base.isEqual(task), "\(tag)：完成项没有用统一的弱化色")
            XCTAssertTrue(base.isEqual(strike), "\(tag)：删除线没有用统一的弱化色")
        }
    }
}
