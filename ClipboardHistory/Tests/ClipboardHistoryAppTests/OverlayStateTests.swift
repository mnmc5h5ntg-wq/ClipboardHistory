import XCTest
@testable import ClipboardHistoryApp

/// R7：浮层与临时状态（QuickPick 空结果、批量条、视频两颗图标）。
///
/// 本文件里前两条走真模型（管线级），后面几条是**源码级**判据：
/// 它们不覆盖"淡入到底演没演"——那件事的取证边界写在账本 D-055
/// （`cacheDisplay` 抓不到 AppKit 图层动画，也抓不到系统 symbol effect），
/// 产物级证据走人工批次 15。
@MainActor
final class OverlayStateTests: XCTestCase {

    // MARK: - QuickPick 空结果（管线级）

    /// 真值表：三种"空"必须说三句话，因为**下一步不一样**。
    func testQuickPickEmptyMessageTruthTable() {
        XCTAssertEqual(QuickPickModel.emptyMessage(query: "验证码", hasAnyHistory: true),
                       "没有匹配「验证码」的记录，换个词或按 Esc 清空。")
        XCTAssertEqual(QuickPickModel.emptyMessage(query: "   ", hasAnyHistory: true),
                       "没有可显示的记录。", "全是空格算没输入词：不许说成「没有匹配」")
        XCTAssertEqual(QuickPickModel.emptyMessage(query: "", hasAnyHistory: false),
                       "还没有历史记录，先复制点东西再按这个快捷键。")
        // 词是用户自己打的 ⇒ 必须原样带回去（他要知道是哪个词没中）。
        XCTAssertTrue(QuickPickModel.emptyMessage(query: "ABC", hasAnyHistory: false).contains("ABC"),
                      "空历史时把用户的词丢了，他会以为是搜索坏了而不是没东西")
    }

    /// 有候选 ⇒ 一句话都不许出现（否则空态文案会盖在列表上）。
    func testQuickPickEmptyMessageIsNilWheneverThereAreCandidates() throws {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        for text in ["验证码 1234", "会议纪要"] { store.add(intakeEntry(text: text)) }

        var model = QuickPickModel(all: store.entries)
        XCTAssertNil(model.emptyMessage, "有两条历史却报了空态")

        model.setQuery("验证码")
        XCTAssertEqual(model.visible.count, 1)
        XCTAssertNil(model.emptyMessage)

        model.setQuery("zzz 不存在")
        XCTAssertTrue(model.visible.isEmpty)
        let message = try XCTUnwrap(model.emptyMessage, "搜不出东西时仍然是一片空白（R7 要修的就是这个）")
        XCTAssertTrue(message.contains("zzz 不存在"), "文案里要带上用户输入的那个词：\(message)")
        XCTAssertTrue(message.contains("Esc"), "要给出下一步（§4 U-5）：\(message)")

        // 历史本来就是空的 ⇒ 没词时也要出声，而且说的是"先去复制"，不是"你搜错了"。
        let fresh = QuickPickModel(all: [])
        XCTAssertTrue(fresh.visible.isEmpty)
        let freshMessage = try XCTUnwrap(fresh.emptyMessage, "空历史 + 没词 ⇒ 面板仍然一片空白")
        XCTAssertTrue(freshMessage.contains("复制"), freshMessage)
        XCTAssertFalse(freshMessage.contains("没有匹配"), freshMessage)
    }

    /// 面板必须真的把那句话摆出来，并且淡入而不是"突然出现"。
    func testQuickPickPanelWiresTheEmptyLabel() throws {
        let controller = codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        XCTAssertTrue(controller.contains("emptyLabel.stringValue = message"),
                      "空态文案没有落到面板上（模型会说了，界面仍然空白）")
        XCTAssertTrue(controller.contains("model.emptyMessage"),
                      "面板不再问模型 ⇒ 两处各写一套空态语言")
        XCTAssertTrue(controller.contains("stack.detachesHiddenViews = true"),
                      "隐藏时不脱离布局 ⇒ 那句话会占着一行高度把表格挤短")
        // **调用点**，不是定义。第一版这里只写 `contains("applyEmptyState()")`，
        // 于是变异 M15（把调用整行删掉）**绿着通过** —— 因为定义那一行
        // （`private func applyEmptyState() {`）本身就含这个子串。
        // 与 R5 的 A7 同一课：needle 命中面比意图宽，判据就是假的。
        let selectBody = controller.components(separatedBy: "private func selectCurrentRow()")
            .dropFirst().first?
            .components(separatedBy: "\n    }").first ?? ""
        XCTAssertTrue(selectBody.contains("applyEmptyState()"),
                      "刷新入口没有被调用 ⇒ 那句话会停在上一条的状态（定义在、调用点没了）")
        XCTAssertFalse(controller.components(separatedBy: "\n")
            .filter { $0.contains("applyEmptyState()") && !$0.contains("func applyEmptyState") }
            .isEmpty,
                       "整个文件里只剩定义、没有调用点")
        // 动效参数只有一个作者：这里不许出现写死的秒数。
        XCTAssertTrue(controller.contains("MotionCatalog.duration(for: .contentFade)"),
                      "淡入时长没走目录")
        XCTAssertTrue(controller.contains("MotionCatalog.motionShouldBeReduced"),
                      "减弱动态时仍然淡 ⇒ 绕过了全源门")
    }

    // MARK: - 批量条（两臂都要演）

    /// 进批量软交接、出批量硬换 = 只修了一半。两臂各挂一条过渡，驱动仍是那个布尔。
    func testBulkBarTransitionsOnBothArms() throws {
        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        let region = try XCTUnwrap(
            sidebar.components(separatedBy: "if historyStore.selectedCount > 1 {").dropFirst().first?
                .components(separatedBy: ".animation(MotionCatalog.animation(for: .selection)").first,
            "找不到批量条那一段：锚点失效")
        XCTAssertEqual(region.components(separatedBy: "\n")
                       .filter { $0.contains(".transition(MotionCatalog.transition(for:") }.count, 2,
                       "批量条两臂不是两条过渡 ⇒ 有一边仍然是一帧硬换")
        XCTAssertTrue(sidebar.contains("value: historyStore.selectedCount > 1"),
                      "驱动那条布尔被换掉了（它才是这两臂的供电）")
    }

    // MARK: - 视频两颗图标

    /// 两颗图标走同一个 `symbolMotion` 入口，并且各自有事务供电。
    func testVideoControlsShareTheSymbolMotionEntry() throws {
        let video = codeOnly(try productSource(named: "Views/VideoPreview.swift"))
        XCTAssertEqual(video.components(separatedBy: "\n")
                       .filter { $0.contains(".symbolMotion(symbol:") }.count, 2,
                       "播放/静音两颗里有人没接唯一入口")
        XCTAssertEqual(video.components(separatedBy: "\n")
                       .filter { $0.contains("value: playback.isPlaying")
                           || $0.contains("value: playback.isMuted") }.count, 2,
                       "12/13 那一臂是「身份变了 + 淡入」，没有按值事务就什么都不会演（R5 的 A3 同一课）")
        XCTAssertFalse(video.contains("bounce"),
                       "播放/暂停是高频动作，频率闸门判它不该弹（报告红线 0/8）")
    }

    /// 一族判据：**符号替换这个动作只有一个作者**。
    /// 第二处写 `.contentTransition(.symbolEffect(.replace))` 就等于第二套"换符号"的语言，
    /// 而 reduce-motion 的退化规则也要跟着写两遍（漏一处就是"减弱动态时还在弹"）。
    func testSymbolReplacementHasOneAuthor() throws {
        var offenders: [String] = []
        for (file, source) in try productViewSources() {
            let code = Self.stripCommentLines(source)
            guard code.contains(".contentTransition(") else { continue }
            if file == "MotionModifiers.swift" { continue }   // 唯一作者
            offenders.append("\(file) 自己写了 .contentTransition")
        }
        XCTAssertTrue(offenders.isEmpty,
                      "符号替换必须走 `SymbolMotion`：\n" + offenders.joined(separator: "\n"))
    }

    // MARK: - 设置页 · 按 App 排除（R8 / 审计 B-P2、B-P4）

    /// 六种结局各有话说；**没做成的那三种尤其不能说"做好了"**。
    func testExcludedListPolicyTruthTable() {
        let empty = ""
        let added = ExcludedAppListPolicy.add("com.example.app", to: empty)
        XCTAssertEqual(added.outcome, .added("com.example.app"))
        XCTAssertEqual(CapturePolicy.decodeUserExcluded(added.raw), ["com.example.app"])
        XCTAssertTrue(added.receipt.contains("不再自动入库"), added.receipt)

        // 已经在用户名单里 ⇒ 持久化值不许变，且要说"不用重复添加"。
        let twice = ExcludedAppListPolicy.add("com.example.app", to: added.raw)
        XCTAssertEqual(twice.outcome, .alreadyListed("com.example.app"))
        XCTAssertEqual(twice.raw, added.raw, "重复添加不该改坏存档")
        XCTAssertTrue(twice.receipt.contains("已经在名单里"), twice.receipt)

        // 系统默认已经覆盖它 ⇒ 这句必须说"本来就不入库"，
        // 否则用户以为"加了没生效"，转去做更危险的事（整个暂停采集）。
        let def = ExcludedAppListPolicy.add("com.apple.keychainaccess", to: empty,
                                            defaults: ["com.apple.keychainaccess"])
        XCTAssertEqual(def.outcome, .coveredByDefault("com.apple.keychainaccess"))
        XCTAssertEqual(def.raw, empty, "默认项不该被写进用户名单（那会让它看起来能移除）")
        XCTAssertTrue(def.receipt.contains("默认"), def.receipt)

        let blank = ExcludedAppListPolicy.add("   ", to: empty)
        XCTAssertEqual(blank.outcome, .emptyInput)
        XCTAssertTrue(blank.receipt.contains("Bundle ID"), blank.receipt)

        let gone = ExcludedAppListPolicy.remove("com.example.app", from: added.raw)
        XCTAssertEqual(gone.outcome, .removed("com.example.app"))
        XCTAssertEqual(CapturePolicy.decodeUserExcluded(gone.raw), [])
        XCTAssertTrue(gone.receipt.contains("重新入库"), gone.receipt)

        let ghost = ExcludedAppListPolicy.remove("com.never.added", from: added.raw)
        XCTAssertEqual(ghost.outcome, .notListed("com.never.added"))
        XCTAssertEqual(ghost.raw, added.raw)

        // 沉默是这一族缺陷的本体：任何结局都必须给一句话。
        for result in [added, twice, def, blank, gone, ghost] {
            XCTAssertFalse(result.receipt.isEmpty, "有一条路径没有回执")
        }
    }

    /// 管线级：走**真的** encode/decode，而不是只测策略自己。
    /// 「加进去 ⇒ 解码得到它 ⇒ 再点是幂等 ⇒ 移除 ⇒ 又空」这一整圈必须在真实编码格式上成立。
    func testExcludedListRoundTripsThroughTheRealEncoding() {
        var raw = ""
        for id in ["com.b.app", "com.a.app"] {
            let result = ExcludedAppListPolicy.add(id, to: raw)
            XCTAssertTrue(result.receipt.contains(id), result.receipt)
            raw = result.raw
        }
        XCTAssertEqual(CapturePolicy.decodeUserExcluded(raw).count, 2)
        // encode 会排序去重 ⇒ 幂等性必须成立（否则"再点一次添加"会写坏存档）
        let again = ExcludedAppListPolicy.add("com.a.app", to: raw)
        XCTAssertEqual(again.raw, raw)

        let removed = ExcludedAppListPolicy.remove("com.a.app", from: raw)
        XCTAssertEqual(CapturePolicy.decodeUserExcluded(removed.raw), ["com.b.app"])
    }

    /// 三处结果文案要能**自己关掉**，并且淡入；而"自动消失"是刻意不做的（信息不是装饰）。
    func testSettingsReceiptLinesAreDismissibleAndDoNotVanish() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertEqual(settings.components(separatedBy: "\n")
                       .filter { $0.contains("ReceiptLine(text:") }.count, 3,
                       "三处结果文案（导出导入 / 反馈导出 / 排除名单）里有人退回裸 Text ⇒ 又变成永不清空")
        XCTAssertTrue(settings.contains("value: excludedBundleIDsRaw"),
                      "排除名单的增删没有驱动 ⇒ 行会瞬间塌位")
        // **钉到那一段里面**，不是"整个文件含 transition"：`ReceiptLine` 自己也有一条，
        // 只写 contains 的话行的过渡被删掉也照样绿（M21 第一次就是这么放过去的）。
        let listRegion = settings.components(separatedBy: "decodeUserExcluded(excludedBundleIDsRaw)).sorted()")
            .dropFirst().first?
            .components(separatedBy: "TextField(").first ?? ""
        XCTAssertTrue(listRegion.contains(".transition(MotionCatalog.transition(for:"),
                      "排除名单的行没有过渡 ⇒ 添加/移除是整块瞬间塌位")
        XCTAssertTrue(settings.contains(".animation(MotionCatalog.animation(for: .contentFade)"),
                      "名单过渡没走目录")
        XCTAssertTrue(settings.contains("xmark.circle"), "没有收起按钮")
        XCTAssertFalse(settings.contains("asyncAfter"),
                       "结果文案被改成自动消失：这三条是「你刚做那件事的结果」，不是瞬时回执")
    }

    // MARK: - 工具

    static func stripCommentLines(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func codeOnly(_ source: String) -> String { Self.stripCommentLines(source) }

    private func productViewSources() throws -> [(file: String, source: String)] {
        try productSources(in: "Views")
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        let found = try productSources(in: directory).first { $0.file == name }
        return try XCTUnwrap(found?.source, "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红")
    }

    private func productSources(in directory: String) throws -> [(file: String, source: String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory, isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            return names.filter { $0.hasSuffix(".swift") }.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "OverlayStateTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到目录 \(directory)"])
    }

    private func intakeEntry(text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
    }
}
