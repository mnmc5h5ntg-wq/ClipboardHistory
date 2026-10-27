// R417：暂停采集状态的主窗口横幅 —— 纯映射、源接线、以及"同一把钥匙"的产品入口。
// 像素读数在 UICaptureHarness（content-paused* 组件/整窗帧与 defaults 管线那一条）；
// 出现/消失的过程在 MotionFilmstripTests 的 pause-banner-appear/dismiss 场景里判。
import XCTest
@testable import ClipboardHistoryApp

final class PauseBannerTests: XCTestCase {

    func testPausedStateHasItsOwnPresentation() {
        XCTAssertEqual(StatePresentation.symbolName(for: .paused), "pause.circle.fill",
                       "暂停状态借用了别的图标 ⇒ 用户读到的是警告而不是「我把采集关了」")
        XCTAssertEqual(StatePresentation.messageInk(for: .paused), .prominent,
                       "暂停那句是唯一的信息，不能落在 subdued 档")
        // 动作不是「知道了」：知道没有用，把采集打开才有用。
        XCTAssertEqual(StatePresentation.actionTitle(for: .paused, provided: nil), "继续记录")
        XCTAssertEqual(StatePresentation.actionTitle(for: .paused, provided: "打开设置"), "打开设置",
                       "调用方给了下一步就该用它")
        XCTAssertEqual(NoticeTone.paused.stateKind, .paused,
                       "横幅 tone 与状态规范不是同一个 kind ⇒ 图标/底色/墨会各走各的")
    }

    @MainActor
    func testPausedStateReadsTheSameDefaultsKeyAsCapture() throws {
        let key = "recordingPaused"
        let saved = UserDefaults.standard.object(forKey: key)
        defer {
            if let saved { UserDefaults.standard.set(saved, forKey: key) }
            else { UserDefaults.standard.removeObject(forKey: key) }
        }
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        UserDefaults.standard.set(true, forKey: key)
        XCTAssertTrue(store.isRecordingPaused,
                      "视图写的那把钥匙与采集侧读的不是同一把 ⇒ 横幅亮了但复制照样进历史")
        UserDefaults.standard.set(false, forKey: key)
        XCTAssertFalse(store.isRecordingPaused)
    }

    func testPausedBannerIsWiredIntoTheContentView() throws {
        let content = codeOnly(try productSourceText(named: "Views/ContentView.swift"))
        XCTAssertTrue(content.contains("@AppStorage(\"recordingPaused\")"),
                      "ContentView 没有读设置页那把钥匙 ⇒ 开关拨了主窗口不会动")
        XCTAssertTrue(content.contains("pausedForCapture"),
                      "没有取证键 ⇒ 横幅拍不出来")
        XCTAssertTrue(content.contains("bits |= 32"),
                      "签名没有暂停这一位 ⇒ 横幅进出不会有过渡")
        // 只认**暂停分支那一段**：整文件里 `.bannerIn/.bannerOut` 还有五条别的横幅、
        // `recordingPaused = false` 还有 `@AppStorage` 的初值 —— 拿整文件 contains 当守卫，
        // 删掉暂停分支的过渡/动作它照样绿（R417 的 M1089/M1090 第一次就是这么 ESCAPED 的）。
        guard let start = content.range(of: "if isPausedForDrawing {"),
              let end = content.range(of: "if let recovery = historyStore.historyRecoveryNotice",
                                      range: start.upperBound..<content.endIndex) else {
            return XCTFail("读不到暂停分支（if isPausedForDrawing … if let recovery）⇒ 这条接线判据没有对象")
        }
        let branch = String(content[start.lowerBound..<end.lowerBound])
        XCTAssertTrue(branch.contains("tone: .paused"),
                      "暂停状态没有接到 .paused 那一档呈现")
        XCTAssertTrue(branch.contains("recordingPaused = false"),
                      "「继续记录」没有把开关关回去 ⇒ 点了也没用")
        XCTAssertTrue(branch.contains("asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)"),
                      "暂停横幅没有进出过渡")

        let settings = codeOnly(try productSourceText(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("@AppStorage(\"recordingPaused\")"),
                      "设置页那颗开关不是同一把钥匙 ⇒ 两边会各说各话")
        let store = codeOnly(try productSourceText(named: "Managers/HistoryStore.swift"))
        XCTAssertTrue(store.contains("recordingPausedKey = \"recordingPaused\""),
                      "采集侧那把钥匙改了名 ⇒ 视图与采集会分叉")
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
        throw NSError(domain: "PauseBannerTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
