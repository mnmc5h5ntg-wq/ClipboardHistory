# -*- coding: utf-8 -*-
"""R557：两条新判据 —— 捕获通道不开受保护文件（UICaptureHarness）+ 估高度的取样复用（计数器卷）。"""
import io

# ── A) UICaptureHarness：捕获通道的受保护读取 = 0 ─────────────────────────
p = 'Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
s = io.open(p, encoding='utf-8').read()
anchor = u'    // MARK: - R478 · 文件兜底态的所在路径\n'
assert s.count(anchor) == 1, s.count(anchor)

test = r'''    /// R557 / BACKLOG 632：**捕获通道一次都不许打开受保护文件** —— 帧必须是代码的函数，不是磁盘的函数。
    ///
    /// 来历：R556 把行内缩略图的读取从"采集 + 启动全表"搬到"行真正显示"（`HistorySidebarView.historyRow`
    /// 的 `.task(id: entry.id)` ⇒ `HistoryStore.requestThumbnail`）。那一步留下一个口子写在注释里：
    /// **若夹具把真实存在的图片路径装进侧栏行，异步补图会让同一份代码拍出两张帧**（R478
    /// 「夹具用捕获临时路径 ⇒ 帧不可基线」同族）。注释里的规矩等于没有 ⇒ 本轮升级成会红的判据。
    ///
    /// 两臂各判一件事：
    /// ① **字面量臂**：夹具里每一条 `fileURLWithPath:` 必须指向**不存在**的路径 —— 存在就意味着
    ///    补图真的能读到东西；
    /// ② **运行时臂**：拍 `sidebar-history` 亮/暗两档，前后对比计数环的事件数，增量必须为 0 ——
    ///    这一臂管的是"由 helper 拼出来的 URL"那种字面量扫不到的形状。
    /// 计数器只存路径哈希、不落盘、也没有全局 reset（那会抹掉并行判据正在数的东西）。
    func testCaptureOpensNoProtectedFiles() throws {
        let harnessURL = URL(fileURLWithPath: #filePath)
        let text = try String(contentsOf: harnessURL, encoding: .utf8)
        let literal = /URL\(fileURLWithPath: "([^"]+)"\)/
        var paths: [String] = []
        for match in text.matches(of: literal) {
            paths.append(String(match.output.1))
        }
        XCTAssertFalse(paths.isEmpty, "夹具里一条 `fileURLWithPath` 都没扫到 ⇒ 这把尺没有对象")
        let existing = paths.filter { FileManager.default.fileExists(atPath: $0) }
        emit("CAPTURE_FIXTURE_PATHS 字面量=\(paths.count) 存在=\(existing.count)")
        XCTAssertEqual(existing, [],
                       "有夹具把真实存在的路径装进了帧里 ⇒ 侧栏行的 `.task` 补图会读到东西，"
                       + "帧不再是代码的函数：\(existing.map { $0.lastPathComponent })")

        let scratch = FileManager.default.temporaryDirectory
            .appendingPathComponent("r557-capture-opens-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: scratch) }
        var judged = 0
        for (tag, appearance) in [("light", NSAppearance.Name.aqua),
                                  ("dark", NSAppearance.Name.darkAqua)] {
            guard let fixture = fixtures(appearance: appearance)
                .first(where: { $0.name == "sidebar-history" }) else {
                return XCTFail("\(tag)：找不到 sidebar-history ⇒ 运行时那一臂没有对象")
            }
            let before = ProtectedFileAccessLedger.eventCount
            _ = try render(fixture, appearance: appearance,
                           to: scratch.appendingPathComponent("sidebar-\(tag).png"))
            let after = ProtectedFileAccessLedger.eventCount
            emit("CAPTURE_PROTECTED_OPENS \(tag) 拍前=\(before) 拍后=\(after) 增量=\(after - before)")
            XCTAssertEqual(after, before,
                           "\(tag)：拍这一屏的过程中多开了 \(after - before) 次受保护目录"
                           + " ⇒ 异步补图进了捕获通道，帧开始依赖磁盘")
            judged += 1
        }
        XCTAssertEqual(judged, 2, "两档里只判成 \(judged) 档")
    }

'''
s = s.replace(anchor, test + anchor, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('harness criterion added')

# ── B) ProtectedFileAccessTests：估高度的取样复用 ─────────────────────────
q = 'Tests/ClipboardHistoryAppTests/ProtectedFileAccessTests.swift'
t = io.open(q, encoding='utf-8').read()
anchor2 = u'    // MARK: - 4 隐私红线：读数里不许出现路径\n'
assert t.count(anchor2) == 1, t.count(anchor2)

memo = r'''    // MARK: - 5 R557：估高度的取样在同一次挂载里只取一次

    /// 旧值（一次性探针现读）：展开一条文本 + 拖窗三次 = 同一份文件被开 **4** 次
    /// （`recalculateTargetHeight()` 每来一次宽度变化就重新 `FileHandle` 一趟）。
    /// 新值：同一份取样复用 ⇒ **1** 次；而**高度必须逐次相同**（省读不许改算式）。
    func testHeightEstimateReusesOneSampleAcrossWidthChanges() throws {
        let body = (0..<6).map { "第 \($0) 行 短文本\n" }.joined()
        let url = try makeTextFixture(named: "memo.txt", content: body)
        var sample: MultiFilePreviewLayout.TextSample? = nil
        var heights: [CGFloat] = []
        for width in [320.0, 360.0, 400.0, 440.0] {
            heights.append(MultiFilePreviewLayout.preferredHeight(for: url,
                                                                  availableWidth: width,
                                                                  textSample: &sample))
        }
        let opens = ProtectedFileAccessLedger.count(.layoutTextSample, for: url)
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_LAYOUT_MEMO", for: url)
               + " 高度=" + heights.map { String(format: "%.1f", $0) }.joined(separator: "/"),
               named: "PROTECTED_READS_AT_LAYOUT_MEMO")
        XCTAssertEqual(opens, 1,
                       "四次估高度开了 \(opens) 次同一份文件 ⇒ 取样没被复用（旧形状是 4 次）")
        // 等价证人：同一份文件、同一批宽度，走"每次重开"的旧入口得到的必须逐个相同
        // —— 省读只许省次数，不许改算式（改了就是视觉改动，得走帧基线那一关）。
        let widths = [320.0, 360.0, 400.0, 440.0]
        let uncached = widths.map { MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: $0) }
        XCTAssertEqual(heights, uncached,
                       "复用取样算出的高度与每次重开的不一致：复用=\\(heights) 重开=\\(uncached)"
                       + " ⇒ 省读顺带改了算式，这是视觉改动不是隐私改动")
    }

    /// 负向臂：换一份文件（或同一行被别的 URL 顶替）时**不许**复用上一份取样 ——
    /// `ForEach(id: \.offset)` 会让视图的 `@State` 跨 URL 活下来，只对得上哈希才作数。
    func testHeightEstimateDoesNotLeakTheSampleToAnotherFile() throws {
        let first = try makeTextFixture(named: "row-a.txt", content: "甲\n乙\n丙\n")
        let second = try makeTextFixture(named: "row-b.txt",
                                         content: "一\n二\n三\n四\n五\n六\n七\n八\n九\n十\n")
        var sample: MultiFilePreviewLayout.TextSample? = nil
        _ = MultiFilePreviewLayout.preferredHeight(for: first, availableWidth: 420, textSample: &sample)
        XCTAssertNotNil(sample, "第一份取样没写回 ⇒ 下面那一臂根本没在测复用")
        _ = MultiFilePreviewLayout.preferredHeight(for: second, availableWidth: 420, textSample: &sample)
        let secondOpens = ProtectedFileAccessLedger.count(.layoutTextSample, for: second)
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_LAYOUT_SWITCH", for: second),
               named: "PROTECTED_READS_AT_LAYOUT_SWITCH")
        XCTAssertEqual(secondOpens, 1,
                       "换了文件却复用上一行的取样（开 \(secondOpens) 次）⇒ 行内预览会拿甲的高度画乙")
        XCTAssertEqual(sample?.fileDigest, second.path.hashValue,
                       "写回的取样对不上现在这个文件 ⇒ 缓存身份漂了")
    }

'''
t = t.replace(anchor2, memo + anchor2, 1)
io.open(q, 'w', encoding='utf-8').write(t)
print('memo criteria added')
