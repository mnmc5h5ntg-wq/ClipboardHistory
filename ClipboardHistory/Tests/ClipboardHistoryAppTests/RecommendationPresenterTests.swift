import XCTest
@testable import ClipboardHistoryApp

/// 推荐理由文案（从 `HistoryStore.refreshPredictions()` 搬出来后的可测性）。
final class RecommendationPresenterTests: XCTestCase {
    private func textEntry(_ text: String, content: ClipboardEntryContent? = nil, source: String? = nil) -> ClipboardEntry {

        ClipboardEntry(
            content: content ?? .text(text),
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

    /// 第三轮审计 D-2：这条用例**原来钉的是缺陷本身** —— 它断言
    /// 「前台是 Safari ⇒ 理由里写偏好链接」「前台是 Finder ⇒ 偏好文件」……
    /// 于是每一条推荐（PDF、HEIC、纯文本）在 Safari 里都被说成"偏好链接"。
    /// 修法是把标签的来源换成条目自身，所以这里把断言**翻转**而不是删除：
    /// 同一份条目在前台 App 怎么变时，类型标签都不许变，而且不许出现按 App 猜出来的说法。
    func testContentTypeTagFollowsTheEntryAcrossFrontmostApps() {
        func reason(bundleID: String?, content: ClipboardEntryContent) -> String {
            RecommendationPresenter.reason(
                for: candidate(features: [.contentTypeAffinity: 0.1]),
                entry: textEntry("x", content: content),
                context: context(bundleID: bundleID),
                currentAppName: nil,
                reuseCount: 0
            )
        }
        let apps = ["com.apple.Safari", "com.google.Chrome", "com.apple.finder",
                    "com.apple.dt.Xcode", "com.tencent.xinWeChat", "com.unknown.app"]
        for content: ClipboardEntryContent in [.text("x"), .text("https://example.com")] {
            let tags = Set(apps.map { reason(bundleID: $0, content: content) })
            XCTAssertEqual(tags.count, 1,
                           "同一份条目的理由随前台 App 变了 \(tags)：内容类型标签不该跟着 App 走")
            for text in tags {
                XCTAssertFalse(text.contains("偏好链接"), "按 App 猜类型的旧说法又回来了：\(text)")
                XCTAssertFalse(text.contains("偏好文件"), "按 App 猜类型的旧说法又回来了：\(text)")
                XCTAssertFalse(text.contains("偏好命令/代码"), "按 App 猜类型的旧说法又回来了：\(text)")
                XCTAssertFalse(text.contains("偏好文本/图片"), "按 App 猜类型的旧说法又回来了：\(text)")
                XCTAssertFalse(text.contains("内容匹配"), "又回落到与条目无关的笼统说法：\(text)")
            }
        }
        XCTAssertTrue(reason(bundleID: "com.apple.Safari", content: .text("x")).contains("常用文本"))
        XCTAssertTrue(reason(bundleID: "com.apple.Safari", content: .text("https://example.com")).contains("常用链接"))
    }

    func testAppAffinityLabels() {
        func mentions(_ haystack: String, _ needle: String) -> Int {
            haystack.components(separatedBy: needle).count - 1
        }

        let same = RecommendationPresenter.reason(
            for: candidate(features: [.appAffinity: 0.1]),
            entry: textEntry("x", source: "Safari"),
            context: context(),
            currentAppName: "Safari",
            reuseCount: 0
        )
        XCTAssertTrue(same.contains("回到Safari"), same)
        // 菜单栏面板第一次拍出真像素时暴露的缺陷：来源 App 在同一行里被说了两遍
        // （"文本 · Safari · 偏好链接 · 回到Safari · 24%"）。「回到Safari」已经点明来源，
        // 再列一个裸名只是把 2 行的菜单位置吃掉。
        XCTAssertEqual(mentions(same, "Safari"), 1, "来源 App 不得重复出现：\(same)")

        let crossing = RecommendationPresenter.reason(
            for: candidate(features: [.appAffinity: 0.1]),
            entry: textEntry("x", source: "Safari"),
            context: context(),
            currentAppName: "Notes",
            reuseCount: 0
        )
        XCTAssertTrue(crossing.contains("Safari→Notes"), crossing)
        XCTAssertEqual(mentions(crossing, "Safari"), 1, "跨应用时也不该再多列一个裸来源名：\(crossing)")

        // 反向：没有亲和标签时，裸来源名是**唯一**的来源信息，不能被一起去掉。
        let noAffinity = RecommendationPresenter.reason(
            for: candidate(features: [:]),
            entry: textEntry("x", source: "Safari"),
            context: context(),
            currentAppName: "Safari",
            reuseCount: 0
        )
        XCTAssertTrue(noAffinity.contains("Safari"), "去掉重复时不能把来源信息一起删掉：\(noAffinity)")
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

    /// 第三轮审计 U-1：理由尾巴上那个 `24%` 是**内部指标**，不是概率，用户会按概率读，
    /// 而且权重滑杆一动它的含义就变。所以这里把原来那条
    /// `testPercentSuffixAlwaysPresent`（钉的就是"必须有百分号"）**翻转**成：
    /// 面向用户的文案里不许出现百分号，尾巴改成人话三档。
    func testReasonNeverExposesRawPercentage() throws {
        for value in [0.05, 0.12, 0.24, 0.5, 0.77, 0.99] {
            let reason = RecommendationPresenter.reason(
                for: candidate(features: [:], value: value),
                entry: textEntry("x"),
                context: context(),
                currentAppName: nil,
                reuseCount: 0
            )
            XCTAssertFalse(reason.contains("%"), "文案里仍有原始分数（\(value)）：\(reason)")
        }
        XCTAssertTrue(RecommendationPresenter.reason(
            for: candidate(features: [:], value: 0.77), entry: textEntry("x"),
            context: context(), currentAppName: nil, reuseCount: 0
        ).hasSuffix("把握较大"))
    }

    func testConfidenceWordThresholdsMatchTheObservedSpread() {
        // 帧里实测到的真实分布是 0.12 / 0.24 这一档，所以"低到不值得说"的下限必须盖住它。
        XCTAssertNil(RecommendationPresenter.confidenceWord(for: 0.0))
        XCTAssertNil(RecommendationPresenter.confidenceWord(for: 0.12),
                     "0.12 这种小分数说出来只会让用户以为系统在猜")
        XCTAssertEqual(RecommendationPresenter.confidenceWord(for: 0.24), "把握中等")
        XCTAssertEqual(RecommendationPresenter.confidenceWord(for: 0.5), "把握较大")
        XCTAssertEqual(RecommendationPresenter.confidenceWord(for: 0.9), "把握较大")
    }

    /// 菜单栏面板要回到原生菜单语言：左对齐、不自绘底、不居中（U-1 的验收）。
    func testMenuBarPanelUsesNativeMenuLanguage() throws {
        let source = codeOnly(try productSource(named: "Views/MenuBarRecommendationsView.swift"))
        XCTAssertFalse(source.contains("alignment: .center"),
                       "菜单栏面板里还有居中的行：系统菜单项一律左对齐")
        XCTAssertFalse(source.contains("RoundedRectangle"),
                       "菜单栏面板还在画自绘卡片底：那是 macOS 菜单里没有的语言")
        XCTAssertTrue(source.contains("alignment: .leading"), "标题/理由没有左对齐")
        XCTAssertTrue(source.contains("foregroundStyle(.secondary)"), "理由没有降成次要色")
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
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp/\(relativePath)")
    }
}
