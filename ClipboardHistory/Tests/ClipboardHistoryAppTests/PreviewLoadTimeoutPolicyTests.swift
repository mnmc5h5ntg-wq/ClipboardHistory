import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-09 / 1.8：详情预览的 spinner 以前没有超时兜底，`MediaLoader` 不返回就永远转。
/// 策略本体是纯函数（`PreviewLoadTimeoutPolicy`），这里钉住它的真值表；
/// 最后一条钉"界面确实在用它"（接线），因为纯函数正确但没人调用等于没修。
final class PreviewLoadTimeoutPolicyTests: XCTestCase {
    func testGiveUpTruthTable() {
        // 只有"仍在等"且"还是同一次加载"才允许放弃。
        XCTAssertTrue(PreviewLoadTimeoutPolicy.shouldGiveUp(stillWaiting: true, isCurrentLoad: true))
        XCTAssertFalse(PreviewLoadTimeoutPolicy.shouldGiveUp(stillWaiting: false, isCurrentLoad: true),
                       "已经出结果了就不许再改成失败态")
        XCTAssertFalse(PreviewLoadTimeoutPolicy.shouldGiveUp(stillWaiting: true, isCurrentLoad: false),
                       "陈旧超时不许覆盖用户已经切到的下一条预览")
        XCTAssertFalse(PreviewLoadTimeoutPolicy.shouldGiveUp(stillWaiting: false, isCurrentLoad: false))
    }

    func testTimeoutConstantsAgree() {
        XCTAssertEqual(
            PreviewLoadTimeoutPolicy.timeoutNanoseconds,
            PreviewLoadTimeoutPolicy.timeoutSeconds * 1_000_000_000,
            "两个常量必须同源，否则改一个忘一个"
        )
        XCTAssertGreaterThan(PreviewLoadTimeoutPolicy.timeoutSeconds, 0)
        XCTAssertLessThanOrEqual(PreviewLoadTimeoutPolicy.timeoutSeconds, 30,
                                "兜底时间长得用户会以为界面卡死")
    }

    func testFailureMessageStatesTheBound() {
        let message = PreviewLoadTimeoutPolicy.failureMessage()
        XCTAssertTrue(message.contains("\(PreviewLoadTimeoutPolicy.timeoutSeconds)"),
                      "文案要说出等了多少秒，否则用户不知道这是超时还是坏了")
        XCTAssertEqual(PreviewLoadTimeoutPolicy.failureMessage(timeoutSeconds: 3), "预览加载超过 3 秒仍未返回，已停止等待。")
    }

    /// 接线守卫：`DetailFileView.loadPreview()` 必须真的调用这个策略并睡那么久。
    /// 钉的是"调用点存在且只有一处"，不是具体表达式写法。
    func testLoadingPathActuallyConsultsThePolicy() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 DetailPreviewViews.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)

        let giveUpCalls = source.components(separatedBy: "PreviewLoadTimeoutPolicy.shouldGiveUp(").count - 1
        XCTAssertEqual(giveUpCalls, 1, "放弃判定应当恰好被加载路径调用一次，实际 \(giveUpCalls) 次")
        XCTAssertTrue(source.contains("PreviewLoadTimeoutPolicy.timeoutNanoseconds"),
                      "超时时值必须来自策略，而不是在视图里另写一个字面量")
        XCTAssertTrue(source.contains("previewState = .failure(PreviewLoadTimeoutPolicy.failureMessage())"),
                      "超时后必须落到失败态（带出口文案），而不是继续转圈")
    }
}
