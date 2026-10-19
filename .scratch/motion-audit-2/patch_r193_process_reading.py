#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 的一处批量改形：把 `processReading` 升级成"帧数 + 连续段 + 合读法"，六个调用点各带上自己那一臂的帧数。

为什么用脚本而不是手改：六处文本两两同形（insert 与 move 两站点的变量名一样），
Edit 一次只能改一处、`allow_multiple` 又会把两站点一起改 —— 而这两处**必须**同时改，
所以按"整行字面相等"计数替换，替换后立刻数一遍（R100：只印不拦的读数=没读数）。
"""
import io
import sys

P = '/Users/wangziyi/Codex_Project0/ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift'
text = io.open(P, encoding='utf-8').read()

OLD_HELPER = """    /// `armProcessInIntervals` 的打印形状 —— 读不到打「无」，不许打空串（R100 那一课：
    /// 形状形容词不许落在缺席读数上，而缺席要有缺席的样子）。
    static func processReading(_ value: (intervals: Double, run: ChangedRun)?) -> String {
        guard let v = value else { return "无连续段(整卷峰值低于绝对地板)" }
        return String(format: "%.1f个间隔 时长%.0fms 段内最粗%.0fms 帧对%d",
                      v.intervals, v.run.elapsedMilliseconds, v.run.worstIntervalMilliseconds,
                      v.run.endFrame - v.run.startFrame + 1)
    }"""

NEW_HELPER = """    /// `armProcessInIntervals` 的打印形状 —— 读不到打「无」，不许打空串（R100 那一课：
    /// 形状形容词不许落在缺席读数上，而缺席要有缺席的样子）。
    ///
    /// 帧数与连续段**并排打**，因为本轮的真卷读数就是这两个数对不上：
    /// `row-insert 开 帧数=9 … 过程=1.4个间隔 时长10ms 帧对1` —— 九帧是**散着抖**出来的，
    /// 不是一段一直在演的过程。合读法把这件事说成一句话，免得读日志的人只看见那个 9。
    static func processReading(_ value: (intervals: Double, run: ChangedRun)?, span: Int) -> String {
        guard let v = value else { return "无连续段(整卷峰值低于绝对地板) 帧数=\\(span)" }
        return String(format: "%.1f个间隔 时长%.0fms 段内最粗%.0fms 帧对%d 帧数=%d ⇒ %@",
                      v.intervals, v.run.elapsedMilliseconds, v.run.worstIntervalMilliseconds,
                      v.run.endFrame - v.run.startFrame + 1, span,
                      processReadingVerdict(span: span, intervals: v.intervals))
    }

    /// "这一臂到底演了一段，还是只是被数到几帧"（R193 / BACKLOG 217）—— 措辞由两个数生成。
    ///
    /// 2.0 个间隔这个界**不是新阈值**：它就是 `minimumTransitionFrames`(3) 在时间轴上的等价形状
    /// —— 三帧**连续**在演，段长必然是"首帧到第四帧"= 2 个间隔。所以这条只在"帧数够、连续段不够"
    /// 时说话，说的还是原来那条判据自己的要求。
    static func processReadingVerdict(span: Int, intervals: Double) -> String {
        if span < minimumTransitionFrames { return "帧数本来就不够 \\(minimumTransitionFrames) ⇒ 这一臂判'没在演'" }
        if intervals < 2.0 { return "散点撑绿：帧数 \\(span) 够，但含峰值那段只跨 \(String(format: "%.1f", intervals)) 个间隔 ⇒ 这几帧不是一段过程（217）" }
        return "有一段一直在演的过程（连续段 \(String(format: "%.1f", intervals)) 个间隔）"
    }"""

CALLS = [
    ('Self.processReading(animatedProcess)', 'Self.processReading(animatedProcess, span: animatedSpan)', 2),
    ('Self.processReading(instantProcess)', 'Self.processReading(instantProcess, span: instantSpan)', 2),
    ('Self.processReading(sameProcess)', 'Self.processReading(sameProcess, span: sameSpan)', 1),
    ('Self.processReading(movedProcess)', 'Self.processReading(movedProcess, span: movedSpan)', 1),
]

problems = []
if text.count(OLD_HELPER) == 1:
    text = text.replace(OLD_HELPER, NEW_HELPER)
elif text.count(NEW_HELPER) == 1:
    print('HELPER_ALREADY_PATCHED')
else:
    problems.append('helper 锚点既不是旧形也不是新形')
for needle, repl, want in CALLS:
    got = text.count(needle)
    if got != want:
        problems.append('%r 命中 %d 次（要 %d）' % (needle, got, want))
if problems:
    raise SystemExit('REFUSE_TO_PATCH ' + '；'.join(problems))
# 第一版在这里只**数了**次数、没有替换，于是它打印了 "calls=6" 却一个字没改
# —— 自报成功的生成器必须按**改完之后的状态**作证，不是按"我数过锚点"。
for needle, repl, want in CALLS:
    text = text.replace(needle, repl)
for needle, want, done in [
        ('XCTAssertEqual(g?.intervals ?? 0, 30.0, accuracy: 0.5,', 1,
         'XCTAssertEqual(g?.intervals ?? 0, 31.0, accuracy: 0.5,'),
        ('"中位间隔 10ms、段内一次 300ms 空档 ⇒ 折算 30 个间隔', 1,
         '"中位间隔 10ms、段内一次 299ms 空档 ⇒ 折算 31 个间隔（310ms ÷ 10ms）')]:
    if text.count(needle) == 0 and text.count(done) == 1:
        print('ALREADY_PATCHED %s' % done[:36])
    elif text.count(needle) != want:
        problems.append('真值表锚点 %r 命中 %d 次' % (needle[:24], text.count(needle)))
if problems:
    raise SystemExit('REFUSE_TO_PATCH ' + '；'.join(problems))
for needle, repl, want in CALLS:
    text = text.replace(needle, repl)
text = text.replace('XCTAssertEqual(g?.intervals ?? 0, 30.0, accuracy: 0.5,',
                    'XCTAssertEqual(g?.intervals ?? 0, 31.0, accuracy: 0.5,')
text = text.replace('"中位间隔 10ms、段内一次 300ms 空档 ⇒ 折算 30 个间隔',
                    '"中位间隔 10ms、段内一次 299ms 空档 ⇒ 折算 31 个间隔（310ms ÷ 10ms）')
# 真值表补一格：合读法三态（散点撑绿 / 一段过程 / 帧数本来就不够）。
anchor = """        XCTAssertNil(Self.armProcessInIntervals(stamps: stamps, fractions: [0, 0.001, 0.001, 0, 0, 0]),
                     "峰值低于绝对地板时不许返回一个数 —— 那会把'没量到'说成'瞬移'")"""
extra = anchor + """

        // (e) 合读法三态：本轮真卷落在**散点撑绿**那一格（`row-insert 开 帧数=9 / 连续段 1.4 个间隔`）。
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 1.4).contains("散点撑绿"),
                      "帧数够而连续段不够 ⇒ 必须说'散点撑绿'，不许只报那个 9")
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 2.0).contains("一直在演"))
        XCTAssertTrue(Self.processReadingVerdict(span: 2, intervals: 1.0).contains("帧数本来就不够"),
                      "帧数本来就不够那一臂 ⇒ 不许被读成'散点撑绿'（那是另一种病）")
        XCTAssertTrue(Self.processReading(nil, span: 0).contains("无连续段"),
                      "缺席要打「无连续段」并带上帧数，不许打空串（R100）")"""
if text.count(anchor) == 1 and '散点撑绿：帧数' not in extra.split(anchor, 1)[1]:
    text = text.replace(anchor, extra)
elif 'processReadingVerdict(span: 9, intervals: 1.4)' in text:
    print('TRUTH_TABLE_E_ALREADY_PATCHED')
else:
    raise SystemExit('REFUSE_TO_PATCH 真值表 (d) 锚点命中 %d 次且 (e) 不在盘上' % text.count(anchor))
# 事后作证：按**改完的文本**数，不按"我数过锚点"。
post = [('Self.processReading(animatedProcess, span: animatedSpan)', 2),
        ('Self.processReading(instantProcess, span: instantSpan)', 2),
        ('Self.processReading(sameProcess, span: sameSpan)', 1),
        ('Self.processReading(movedProcess, span: movedSpan)', 1),
        ('static func processReading(_ value: (intervals: Double, run: ChangedRun)?, span: Int)', 1)]
for needle, want in post:
    if text.count(needle) != want:
        raise SystemExit('POST_STATE_MISMATCH %r 命中 %d 次（要 %d）⇒ 不写盘' % (needle[:40], text.count(needle), want))
io.open(P, 'w', encoding='utf-8').write(text)
print('PATCHED_OK helper=1 calls=6 truth_table_e=1 post_state=%d_checks' % len(post))
