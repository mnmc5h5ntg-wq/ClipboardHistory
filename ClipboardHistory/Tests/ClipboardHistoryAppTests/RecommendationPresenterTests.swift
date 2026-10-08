import XCTest
@testable import ClipboardHistoryApp

/// 推荐理由文案（从 `HistoryStore.refreshPredictions()` 搬出来后的可测性）。
final class RecommendationPresenterTests: XCTestCase {
    private func textEntry(_ text: String, source: String? = nil) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date(),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: [],
            sourceAppBundleID: source.map { _ in "com.example.app" },
            sourceAppName: source
        )
    }

    private func candidate(features: [RecommendationFeature: Double], value: Double = 0.42) -> RecommendationCandidate {
        RecommendationCandidate(entryID: UUID(), score: RecommendationScore(value: value, features: features), reason: "")
    }

    private func context(bundleID: String? = nil, events: [ContextEvent] = [], directory: String? = nil, extensions: [String] = []) -> ContextSnapshot {
        var snapshot = ContextSnapshot.minimal(recentEntries: [], capturedAt: Date())
        snapshot.frontmostApplication = bundleID.map {
            RunningApplicationContext(localizedName: "App", bundleIdentifier: $0, processIdentifier: nil)
        }
        snapshot.recentEvents = events
        snapshot.finderDirectory = directory.map { FinderDirectoryContext(path: $0, sensitivity: .personal) }
        snapshot.finderSelection = extensions.isEmpty ? nil : FinderSelectionContext(fileExtensions: extensions, count: extensions.count, sensitivity: .personal)
        return snapshot
    }

    func testKindLabels() throws {
        XCTAssertEqual(RecommendationPresenter.kindLabel(for: textEntry("https://a.b")), "链接")
        XCTAssertEqual(RecommendationPresenter.kindLabel(for: textEntry("第一行\n第二行")), "文本片段")
        XCTAssertEqual(RecommendationPresenter.kindLabel(for: textEntry(String(repeating: "长", count: 300))), "文本")
    }

    func testReuseCountComesFromCountNotFromWeightedFeature() {
        // 权重被调到 0.5 时，特征值只有真实次数的一半；文案必须仍显示真实次数（审计 R-17）。
        let entry = textEntry("hello")
        let weightedHalf = RecommendationFeature.reuseFrequency.rawValue   // 仅用于表达"这是同一个因子"
        let features: [RecommendationFeature: Double] = [
            .reuseFrequency: 3 * 0.08 * 0.5,   // 权重 0.5 后的特征值
        ]
        _ = weightedHalf
        let reason = RecommendationPresenter.reason(
            for: candidate(features: features),
            entry: entry,
            context: context(),
            currentAppName: nil,
            reuseCount: 3
        )
        XCTAssertTrue(reason.contains("复用3次"), reason)
        XCTAssertFalse(reason.contains("复用1次"), "不得从乘过权重的特征值反推次数：\(reason)")
    }

    func testContentTypeTagsPerFrontmostApp() {
        func tag(_ bundleID: String) -> String {
            RecommendationPresenter.reason(
                for: candidate(features: [.contentTypeAffinity: 0.1]),
                entry: textEntry("x"),
                context: context(bundleID: bundleID),
                currentAppName: nil,
                reuseCount: 0
            )
        }
        XCTAssertTrue(tag("com.apple.Safari").contains("偏好链接"))
        XCTAssertTrue(tag("com.google.Chrome").contains("偏好链接"))
        XCTAssertTrue(tag("com.apple.finder").contains("偏好文件"))
        XCTAssertTrue(tag("com.apple.dt.Xcode").contains("偏好命令/代码"))
        XCTAssertTrue(tag("com.tencent.xinWeChat").contains("偏好文本/图片"))
        XCTAssertTrue(tag("com.unknown.app").contains("内容匹配"))
    }

    func testAppAffinityLabels() {
        let same = RecommendationPresenter.reason(
            for: candidate(features: [.appAffinity: 0.1]),
            entry: textEntry("x", source: "Safari"),
            context: context(),
            currentAppName: "Safari",
            reuseCount: 0
        )
        XCTAssertTrue(same.contains("回到Safari"), same)

        let crossing = RecommendationPresenter.reason(
            for: candidate(features: [.appAffinity: 0.1]),
            entry: textEntry("x", source: "Safari"),
            context: context(),
            currentAppName: "Notes",
            reuseCount: 0
        )
        XCTAssertTrue(crossing.contains("Safari→Notes"), crossing)
    }

    func testBehavioralTags() {
        func copyEvents(_ n: Int) -> [ContextEvent] { (0..<n).map { _ in ContextEvent(kind: .copy) } }
        func switchEvents(_ n: Int) -> [ContextEvent] { (0..<n).map { _ in ContextEvent(kind: .switchToApp) } }

        func label(_ events: [ContextEvent]) -> String {
            RecommendationPresenter.reason(
                for: candidate(features: [.semanticSimilarity: 0.04]),
                entry: textEntry("x"),
                context: context(events: events),
                currentAppName: nil,
                reuseCount: 0
            )
        }
        XCTAssertTrue(label(copyEvents(3) + switchEvents(1)).contains("跨应用连续复制"))
        XCTAssertTrue(label(copyEvents(4)).contains("短时间内多次复制"))
        XCTAssertTrue(label(switchEvents(2)).contains("频繁切换应用中"))
        XCTAssertTrue(label([ContextEvent(kind: .copy)]).contains("你刚复制过同类内容"))
    }

    func testFinderAndNegativeFeedbackTags() {
        let directory = RecommendationPresenter.reason(
            for: candidate(features: [.finderDirectoryAffinity: 1.0]),
            entry: textEntry("x"),
            context: context(directory: "/Users/shared/Downloads"),
            currentAppName: nil,
            reuseCount: 0
        )
        XCTAssertTrue(directory.contains("来自「Downloads」"), directory)

        let twoExt = RecommendationPresenter.reason(
            for: candidate(features: [.finderSelectionAffinity: 1.0]),
            entry: textEntry("x"),
            context: context(extensions: ["png", "jpg"]),
            currentAppName: nil,
            reuseCount: 0
        )
        // 文案与重构前逐字一致（原实现就是 "选中 .png、jpg"，点号只出现在第一个扩展名前）。
        XCTAssertTrue(twoExt.contains("选中 .png、jpg"), twoExt)

        let manyExt = RecommendationPresenter.reason(
            for: candidate(features: [.finderSelectionAffinity: 1.0]),
            entry: textEntry("x"),
            context: context(extensions: ["png", "jpg", "pdf"]),
            currentAppName: nil,
            reuseCount: 0
        )
        XCTAssertTrue(manyExt.contains("选中 .png、jpg 等文件"), manyExt)

        let demoted = RecommendationPresenter.reason(
            for: candidate(features: [.negativeFeedback: -0.2]),
            entry: textEntry("x"),
            context: context(),
            currentAppName: nil,
            reuseCount: 0
        )
        XCTAssertTrue(demoted.contains("已降权"), demoted)
    }

    func testPercentSuffixAlwaysPresent() {
        let reason = RecommendationPresenter.reason(
            for: candidate(features: [:], value: 0.77),
            entry: textEntry("x"),
            context: context(),
            currentAppName: nil,
            reuseCount: 0
        )
        XCTAssertTrue(reason.hasSuffix("77%"), reason)
    }
}
