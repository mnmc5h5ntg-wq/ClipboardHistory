// R414：设置侧栏选中胶囊的几何、接线与像素尺。
//
// 不覆盖整页设置：整页的选中行底色是否逐像素不变，由帧基线对 192 张既有帧作证；
// 这里判的是「胶囊只有一颗、几何可插值、接线在」。像素尺 `SettingsSidebarCapsuleRuler`
// 同时被 `UICaptureHarness.testCaptureKeyViews` 的三态帧判据使用。

import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class SettingsSidebarSelectionTests: XCTestCase {

    func testCapsulePlanTruthTable() {
        let row = CGRect(x: 0, y: 10, width: 300, height: 30)
        XCTAssertEqual(SettingsSidebarSelectionPlan.capsuleRect(rowFrame: row),
                       CGRect(x: 6, y: 10, width: 288, height: 30),
                       "胶囊必须与旧的行内选中底同矩形（左右各内缩 6）")
        let from = SettingsSidebarSelectionPlan.capsuleRect(rowFrame: row)
        let to = SettingsSidebarSelectionPlan.capsuleRect(
            rowFrame: CGRect(x: 0, y: 40, width: 300, height: 30))
        XCTAssertEqual(SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
            from: from, to: to, progress: 0), from)
        XCTAssertEqual(SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
            from: from, to: to, progress: 1), to)
        XCTAssertEqual(SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
            from: from, to: to, progress: 0.5),
                       CGRect(x: 6, y: 25, width: 288, height: 30),
                       "半程必须正好落在两行中点")
        XCTAssertEqual(SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
            from: from, to: to, progress: -3), from, "负进度夹到 0")
        XCTAssertEqual(SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
            from: from, to: to, progress: 9), to, "超进度夹到 1")
    }

    /// 接线守卫：胶囊是唯一选中底，行内不再画第二层；驱动是 `.selection`。
    func testSelectionCapsuleIsWiredIntoTheSidebar() throws {
        let source = codeOnly(try productSourceText(named: "Views/SettingsView.swift"))
        XCTAssertTrue(source.contains("SettingsSidebarSelectionPlan.capsuleRect(rowFrame:"),
                      "侧栏没有用几何计划放胶囊 ⇒ 上面的真值表测的是没人用的替身")
        XCTAssertTrue(source.contains("SettingsSidebarSelectionPlan.interpolatedCapsuleRect("),
                      "中间态没有走同一个几何计划 ⇒ 夹具与产品各算一套")
        XCTAssertTrue(source.contains("settingsSelectionPreview"),
                      "没有捕获中间态的键 ⇒ 中段帧不存在")
        XCTAssertTrue(source.contains("MotionCatalog.animation(for: .selection, reduceMotion: shouldReduce)"),
                      "选中胶囊没有驱动/没有减弱动态降级")
        XCTAssertTrue(source.contains("guard !isSelected else { return 0 }"),
                      "行内还画着选中底 ⇒ 与胶囊叠成两层，静置帧会变深")
        XCTAssertTrue(source.contains(".fill(Color.primary.opacity(backgroundOpacity))"),
                      "行内底色又出现 accent 分支 ⇒ 选中底有第二个作者")
    }

    /// 像素尺的跨倍率正对照：同一块蓝色在 1×/2× 都读到同样的**点坐标**中心；
    /// 没有蓝色的图必须读不到。它不证明产品，证明这把尺在两档像素密度下量的是同一个对象。
    func testCapsuleRulerSeesBothScales() throws {
        for scale in [1, 2] {
            let blue = try syntheticFrame(scale: scale, block: true)
            let empty = try syntheticFrame(scale: scale, block: false)
            let on = SettingsSidebarCapsuleRuler.center(recording: blue, frameWidthPoints: 100)
            let off = SettingsSidebarCapsuleRuler.center(recording: empty, frameWidthPoints: 100)
            XCTAssertEqual(on.centerY, 60, accuracy: 1.0,
                           "\(scale)x：蓝块中心没读到 60pt ⇒ 这把尺在这档是歪的")
            XCTAssertGreaterThan(on.count, 20, "\(scale)x：蓝块像素太少 ⇒ 正对照自己没对象")
            XCTAssertEqual(off.count, 0, "\(scale)x：没有蓝块的图也读到 \(off.count) 颗 ⇒ 地板失效")
        }
    }

    private func syntheticFrame(scale: Int, block: Bool) throws -> NSBitmapImageRep {
        let width = 100 * scale
        let height = 200 * scale
        let rep = try XCTUnwrap(NSBitmapImageRep(bitmapDataPlanes: nil,
                                                 pixelsWide: width, pixelsHigh: height,
                                                 bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                                 isPlanar: false, colorSpaceName: .deviceRGB,
                                                 bytesPerRow: 0, bitsPerPixel: 0))
        let background = NSColor(calibratedRed: 0.8, green: 0.8, blue: 0.8, alpha: 1)
        let accent = NSColor(calibratedRed: 0.2, green: 0.5, blue: 1, alpha: 1)
        for y in 0..<height {
            for x in 0..<width {
                let inBlock = block && y >= 50 * scale && y < 70 * scale
                rep.setColor(inBlock ? accent : background, atX: x, y: y)
            }
        }
        return rep
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "SettingsSidebarSelectionTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}

/// 三态帧的胶囊中心尺（R414）。x 带故意取胶囊左缘与文字/图标之间：
/// 那里只有胶囊的底色，选中文字/图标的 accent 不会把中心拉偏。
enum SettingsSidebarCapsuleRuler {
    struct Reading: Equatable {
        let centerY: Double
        let count: Int
    }

    static func center(recording: NSBitmapImageRep, frameWidthPoints: CGFloat,
                       bandX: ClosedRange<CGFloat> = 8...13) -> Reading {
        let scale = Double(recording.pixelsWide) / Double(frameWidthPoints)
        let x0 = max(0, Int((bandX.lowerBound * scale).rounded(.down)))
        let x1 = min(recording.pixelsWide, Int((bandX.upperBound * scale).rounded(.up)))
        var sum = 0.0
        var count = 0
        guard x1 > x0 else { return Reading(centerY: -1, count: 0) }
        for y in 0..<recording.pixelsHigh {
            for x in x0..<x1 {
                guard let color = recording.colorAt(x: x, y: y) else { continue }
                let r = color.redComponent, g = color.greenComponent, b = color.blueComponent
                if b > r + 0.04 && b > g + 0.02 {
                    sum += Double(y)
                    count += 1
                }
            }
        }
        guard count > 0 else { return Reading(centerY: -1, count: 0) }
        return Reading(centerY: sum / Double(count) / scale, count: count)
    }
}
