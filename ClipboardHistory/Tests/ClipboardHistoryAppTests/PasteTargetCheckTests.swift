import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 B-6 / 03-04 / 账本 R2-12：注入 ⌘V 前不复核目标应用，
/// 250ms 里用户切走窗口就会把内容粘进别的应用。
final class PasteTargetCheckTests: XCTestCase {
    func testSameForegroundAppProceeds() {
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: "com.apple.Safari",
                actualBundleID: "com.apple.Safari",
                expectedTerminated: false
            ), .proceed)
    }

    func testDifferentForegroundAppCancelsThePaste() {
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: "com.apple.Safari",
                actualBundleID: "com.tencent.xinWeChat",
                expectedTerminated: false
            ), .targetChanged, "前台换了应用还注入 = 把内容粘进别的地方")
    }

    func testMissingForegroundAppCancelsThePaste() {
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: "com.apple.Safari",
                actualBundleID: nil,
                expectedTerminated: false
            ), .targetChanged, "读不到前台应用时不能假设它还是原来那个")
    }

    func testTerminatedTargetCancelsEvenWhenTheBundleIDMatches() {
        // 目标崩溃后被重新拉起：前台 bundle id 相同，但那已经不是原来的窗口上下文。
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: "com.apple.Safari",
                actualBundleID: "com.apple.Safari",
                expectedTerminated: true
            ), .targetGone)
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: "com.apple.Safari",
                actualBundleID: "com.apple.finder",
                expectedTerminated: true
            ), .targetGone, "退出优先于'前台是谁'")
    }

    func testUnknownExpectedTargetKeepsTheOldBehaviour() {
        // 当初就识别不出目标 ⇒ 无从复核。这里刻意放行：
        // 改成"识别不出就不粘"会把一条本来能用的功能变坏，而风险与改动前相同。
        XCTAssertEqual(
            PasteTargetCheck.evaluate(
                expectedBundleID: nil,
                actualBundleID: "com.apple.Safari",
                expectedTerminated: false
            ), .proceed)
        XCTAssertEqual(
            PasteTargetCheck.evaluate(expectedBundleID: nil, actualBundleID: nil, expectedTerminated: true),
            .proceed)
    }

    /// 接线守卫：粘贴流程必须真的先复核再注入，否则这张真值表只是装饰。
    func testPasteFlowVerifiesTheTargetBeforeInjecting() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Managers/ApplicationShell.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 ApplicationShell.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)

        XCTAssertTrue(source.contains("PasteTargetCheck.evaluate("), "粘贴流程没有调用复核")
        XCTAssertTrue(source.contains("sendPasteKeystrokeAfterVerifyingTarget(expected:"),
                      "延时结束后必须走带复核的那个入口")
        // 复核必须在注入之前：按出现顺序断言，位置比"关键字在场"更能说明问题。
        let verifyIndex = source.range(of: "PasteTargetCheck.evaluate(")?.lowerBound
        let injectIndex = source.range(of: "sendPasteKeystroke()\n")?.lowerBound
        if let verifyIndex, let injectIndex {
            XCTAssertLessThan(verifyIndex, injectIndex, "注入出现在复核之前，顺序反了")
        } else {
            XCTFail("找不到复核或注入的调用点，无法判断顺序")
        }
    }
}
