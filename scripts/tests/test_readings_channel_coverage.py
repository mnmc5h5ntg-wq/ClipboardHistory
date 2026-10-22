#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R302 / BACKLOG 358 + 360：判据读数通道的覆盖率，钉成一个**会红的数**。

为什么这一卷存在（不是"再补一条规矩"）：R64 量过 `swift test` 的 stdout **会成块丢**
（同一批代码本机两遍分别少 324 / 238 行，切点落在行中间，而五条判据自写的 marker 两遍全丢）。
R301 把热图那一卷搬进文件通道，并把"零裸 stdout"的守卫从只扫自己那个文件扩成**按名册扫**（D-282）。
本轮量到的是同一件事的两半：

1. 名册本身是**手挑**的 —— 手挑的名册可以悄悄变短，而守卫不会红（"没扫到"永远不等于"扫过了"）。
   ⇒ 名册必须等于**派生集**：在判据里用 `emit(` 且代码里没有裸 stdout 的那些文件。少一个名字就红。
2. 派生集之外的裸 stdout 读数是**有名字的未覆盖**，不是"大概还有一些"。
   ⇒ 本轮把它数出来并钉成一根**双向棘轮**：磁盘上的行数是 57，登记值也必须是 57。
     变多 ⇒ 新写了会死的通道（红）；变少 ⇒ 有人修好了却没重新登记（也红）。

两条估计量要同一颗尺：这里的 `code_only` 与 Swift 侧 `UICaptureTests.codeOnly` 同形状
（剥行注释与块注释，不剥字符串字面量），`test_positive_and_negative_controls_on_the_estimator`
就是拿它自己开刀 —— 正对照（真调用算 1）与负对照（注释里算 0）两向都要灵，
只有一向灵不代表它能量（R100 那一族）。
"""
import io
import os
import re
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = os.path.join(REPO, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests")
HARNESS = os.path.join(TESTS_DIR, "UICaptureHarness.swift")

# ── 登记值（R302 现读 `python3 scripts/tests/test_readings_channel_coverage.py` 之外
#    的唯一来源是下面的 `measure_corpus()`，不许手抄别处的数）────────────────
BARE_PRINT_LINE_CEILING = 15

# 未覆盖的账，按**文件**登记（本轮量到的裸 stdout 行数 > 0 且确实发了读数的卷）。
# 这张表的作用是"下一轮该搬谁"，不是豁免名单：名册那一格不看它，棘轮那一格也不放过它。
NAMED_UNCOVERED = {
    "ControlHoverLadderTests.swift": 1,
    "DocumentationAnchorTests.swift": 1,
    "FileThumbnailTests.swift": 1,
    "HoverAnimationChannelTests.swift": 1,
    "MarkdownFuzzTests.swift": 1,
    "MarkdownParsingTests.swift": 2,
    "OCRDecodingTests.swift": 1,
    "PasteFailureVisibilityTests.swift": 1,
    "PressInteractionProbeTests.swift": 2,
    "SystemSymbolValidityTests.swift": 1,
    "WindowChromeLayoutTests.swift": 3,
# R306：第三批 OffscreenSymbolInkProbeTests 4 + Round4MarkdownTests 4 + CapturePathWriteBudgetTests 3 + PerfBudgetTests 3 = 14 行搬进 emit，这张表从 15 份 29 行退到 11 份 15 行（WindowChromeLayoutTests 那 3 行本轮没搬，留在表里）。
# R304：MotionDriver / PressFeedback / SettingsFailureReceipt（3 + 5 + 5 行）同族搬进 emit，
#   于是三行从这张表退场、Swift 那张名册的 emitChannel 多三个名字。
# R303：UIInteractionProbeTests 那 15 行已搬进 CaptureReadings（FOCUS-CHAIN / TAB-KEY-CHAIN / AX-VISITED /
# KEYCHAIN* / FILTER_FOCUS / FOCUSCHAIN-RING / RINGVIEWS），于是它从这张表里退场并进了名册（派生集 11 个）。
# 它文件级那颗 emit 仍然走 stderr —— 那是看门狗与 @Sendable 回调的通道（R88：主线程模态循环里
# 只能靠无缓冲的 stderr 留下最后一句话），不是读数的第二条腿，故不算重复实现。
}


def code_only_lines(source):
    """剥掉 `//` 行注释与 `/* … */` 块注释，只留代码；**不**剥字符串字面量。

    与 Swift 侧 `UICaptureTests.codeOnly` 同一形状的理由：守卫要判的是"有没有游离的调用"，
    而这一卷的注释里满是"以前这里是 print(...)"这种句子 —— 不剥注释的话守卫会把
    **解释自己**判成违规，于是下一次有人为了变绿去删注释（R55 的 M276 那一族）。
    不剥字符串则是刻意的：正对照与夹具里的 `print(` 形状在 Swift 侧同样会被扫到，
    两边必须数同一件事，否则"派生集"就成了第二个真值。
    """
    out, in_block = [], False
    for raw in source.split("\n"):
        line = raw
        if in_block:
            if u"*/" in line:
                line = line.split(u"*/", 1)[1]
                in_block = False
            else:
                continue
        while u"/*" in line and u"*/" in line.split(u"/*", 1)[1]:
            head = line.split(u"/*", 1)[0]
            tail = line.split(u"/*", 1)[1].split(u"*/", 1)[1]
            line = head + tail
        if u"/*" in line and u"*/" not in line:
            line = line.split(u"/*", 1)[0]
            in_block = True
        if u"//" in line:
            line = line.split(u"//", 1)[0]
        out.append(line)
    return out


def swift_readings_files():
    """盘上所有判据 Swift 文件（文件名 → 代码行）。"""
    out = {}
    for name in sorted(os.listdir(TESTS_DIR)):
        if not name.endswith(u".swift"):
            continue
        path = os.path.join(TESTS_DIR, name)
        if not os.path.isfile(path):      # 子目录（别的 target）不进这一卷
            continue
        out[name] = code_only_lines(io.open(path, encoding=u"utf-8").read())
    return out


def bare_print_count(lines):
    return sum(1 for l in lines if u"print(" in l)


def emit_usage_count(lines):
    # `emit(` 的调用形状：前面不能是标识符字符或点（`CaptureReadings.emit(` 是转发目标，
    # 不是又一处定义；`Self.emit(` 是调用）。这里两种都算"这卷在用文件通道"。
    return sum(1 for l in lines if re.search(u"(?:^|[^\\w.])emit\\(|\\.[ \\t]*emit\\(", l))


def derived_roster(files):
    """派生集 = 用了 `emit(` 且代码里零裸 stdout 的文件 —— 名册唯一合法的取值。"""
    return sorted(name for name, lines in files.items()
                  if emit_usage_count(lines) > 0 and bare_print_count(lines) == 0)


def declared_roster():
    """从 Swift 源里读名册数组，不重抄一份名单（重抄的那份会先腐烂）。"""
    text = io.open(HARNESS, encoding=u"utf-8").read()
    m = re.search(u"(?m)^\\s*let roster = \\[(.*?)\\]", text, re.S)
    if not m:
        raise AssertionError(u"读不到 UICaptureHarness.swift 里的 `let roster = [` ⇒ 名册形状漂了，"
                             u"这一格不许当成「名册为空所以没事」")
    names = re.findall(u'"([\\w.]+\\.swift)"', m.group(1))
    if not names:
        raise AssertionError(u"名册数组是空的 ⇒ 按名册扫的守卫（R301/D-282）已经没有对象了")
    return sorted(names)


def measure_corpus():
    files = swift_readings_files()
    total_prints = sum(bare_print_count(l) for l in files.values())
    emitters = sorted(n for n, l in files.items() if emit_usage_count(l) > 0)
    out = {
        "files_scanned": len(files),
        "bare_print_lines": total_prints,
        "emitters": len(emitters),
        "clean_emitters": derived_roster(files),
        "roster": declared_roster(),
        "uncovered_named": sum(v for v in NAMED_UNCOVERED.values()),
    }
    out.update(swift_roster_numbers())
    return out


def swift_roster_numbers():
    """Swift 那张按文件的读数名册 —— 数字只从同一份解析里取，不手抄（scripts/readings_roster_source.py）。

    R303 的理由：那张名册原来是按 `print("` 找读数的，搬动之后它对搬走的读数瞎了（刀 M731
    先 ESCAPED 后 CAUGHT，D-284）。台账要引用的合计/文件数/标记数从此必须"读得到或者响亮失败"。
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from readings_roster_source import swift_roster_readings
    return swift_roster_readings()


class ReadingsChannelCoverageTests(unittest.TestCase):

    def test_the_swift_side_roster_is_readable_and_counts_both_channels(self):
        """Swift 名册必须读得到，且合计与探针那份都不许是零（读不到就响亮失败，不是"没有了"）。"""
        n = swift_roster_numbers()
        self.assertGreater(n["files"], 1, u"Swift 名册只覆盖 1 份文件以下 ⇒ 它已经不是名册")
        self.assertGreater(n["total"], 0, u"Swift 名册合计 0 行 ⇒ 形状漂了（读不到不等于没有了）")
        self.assertGreater(n["probe_lines"], 0, u"探针那份按名册读不到行数 ⇒ 通道键或表名漂了")
        self.assertGreater(n["probe_markers"], 5, u"探针的标记清单短到不像清单 ⇒ 改名不会再被抓到")

    def test_positive_and_negative_controls_on_the_estimator(self):
        """先锤尺子：正负对照各一格，缺一个方向都不算它会量。"""
        self.assertEqual(1, bare_print_count(code_only_lines(
            u'    emit("X 1)")\n  print("X 2)\n')))
        self.assertEqual(0, bare_print_count(code_only_lines(
            u'    // 以前这里是 print("X")，现在走 emit\n    emit("X 1)\n')))
        self.assertEqual(0, bare_print_count(code_only_lines(
            u'    /* print("X 2)\n    print("X 3) */\n    emit("X 4)\n')))
        # 块注释之后的一行必须还能被数到：块注释解析坏了的典型形状是"吃掉整段文件"，
        # 那会让覆盖率假装很干净（恒绿），所以这一格是正对照而不是细节。
        self.assertEqual(1, bare_print_count(code_only_lines(
            u'    /* 说明 */\n    print("X 5)\n')))
        # emit 的两种调用形状都算"在用通道"，而**定义**那一行不算（否则守卫自己进名册）
        self.assertGreaterEqual(emit_usage_count(code_only_lines(
            u'    static func emit(_ line: String) {\n        CaptureReadings.emit(line, to: u)\n')), 1)

    def test_bare_stdout_reading_lines_equal_the_registered_ceiling(self):
        """双向棘轮：盘上的裸 stdout 读数行数必须**等于**登记值。"""
        m = measure_corpus()
        print(u"READINGS_COVERAGE files_scanned=%d emitters=%d clean_emitters=%d "
              u"roster=%d bare_print_lines=%d ceiling=%d named_uncovered=%d "
              u"swift_total=%d swift_files=%d probe_lines=%d probe_markers=%d"
              % (m["files_scanned"], m["emitters"], len(m["clean_emitters"]),
                 len(m["roster"]), m["bare_print_lines"], BARE_PRINT_LINE_CEILING,
                 m["uncovered_named"], m["total"], m["files"], m["probe_lines"], m["probe_markers"]))
        self.assertEqual(BARE_PRINT_LINE_CEILING, m["bare_print_lines"],
            u"盘上有 %d 行裸 stdout 读数，登记值是 %d ⇒ 两种情况都坏："
            u"①变多 = 新写了只走会死的通道（R64 量过 stdout 会成块丢）；"
            u"②变少 = 有人把某些卷搬进文件通道却没把登记值改下来，"
            u"于是这根棘轮从此抓不到新的那一行（过期账比没账更坏）。"
            u"要么把读数改走 emit，要么在**这一格里**重新数一遍并写明成因。"
            % (m["bare_print_lines"], BARE_PRINT_LINE_CEILING))

    def test_roster_equals_the_derived_clean_emitters(self):
        """名册不许手挑：它必须等于派生集（在用 emit 且代码里零裸 stdout 的文件）。"""
        files = swift_readings_files()
        derived = derived_roster(files)
        declared = declared_roster()
        missing = sorted(set(derived) - set(declared))
        stale = sorted(set(declared) - set(derived))
        print(u"READINGS_ROSTER derived=%d declared=%d 未纳管=%s 已过期=%s"
              % (len(derived), len(declared),
                 u",".join(missing) if missing else u"无",
                 u",".join(stale) if stale else u"无"))
        self.assertEqual([], missing,
            u"这 %d 份文件已经在用文件通道且代码里没有裸 stdout，却没进名册 ⇒ "
            u"按名册扫的守卫不扫它们，而下一个人往里面加裸 print 不会有人红。"
            u"把它们加进 UICaptureHarness.swift 的 roster。" % len(missing))
        self.assertEqual([], stale,
            u"名册里有这 %d 个名字，但它们已经不满足「在用 emit 且零裸 stdout」⇒ "
            u"要么里面又长出了裸 stdout（那就是违规，改回 emit），"
            u"要么它不再发读数（那这个该退场，别留死名字 —— 名册里一个不存在的名字"
            u"会让守卫悄悄少扫一处）。已过期=%s" % (len(stale), u",".join(stale)))
        for name in declared:
            self.assertTrue(os.path.isfile(os.path.join(TESTS_DIR, name)),
                            u"名册里的 %s 在盘上不存在 ⇒ 守卫在扫一个不存在的文件" % name)

    def test_named_uncovered_is_not_a_dumping_ground(self):
        """未覆盖名单要能自查：登记的行数必须与现读一致，且不许把名册里的文件记进来。"""
        files = swift_readings_files()
        wrong = {n: v for n, v in NAMED_UNCOVERED.items()
                 if n in files and bare_print_count(files[n]) != v}
        self.assertEqual({}, wrong,
            u"未覆盖名单里这几行的数与现读不同源（改过没重登 / 文件已改名）：%s" % wrong)
        in_roster = sorted(set(NAMED_UNCOVERED) & set(declared_roster()))
        self.assertEqual([], in_roster,
            u"未覆盖名单与名册相交 ⇒ 有文件既「已被守卫扫」又「被记成没覆盖」：%s" % in_roster)

    def test_ceiling_is_not_read_back_from_the_disk_measurement_it_defends(self):
        """反自证：登记值不许是从同一次测量里抄回来的常数。

        这一格锤的是"棘轮有牙"：往一份**已在名册里**的文件文本上贴一行裸 stdout，
        估计量必须数到它（并因此把总数推到 ceiling 之上）。做不到就说明这把尺
        只在数它自己想数的东西。
        """
        name = declared_roster()[0]
        base = swift_readings_files()[name]
        self.assertEqual(0, bare_print_count(base),
            u"名册里的 %s 现读已经有裸 stdout ⇒ 名册本身过期了，这一格的对照不成立" % name)
        spiked = base + [u'    print("MOTION_X 1)']
        self.assertEqual(1, bare_print_count(spiked))
        self.assertGreater(bare_print_count(spiked) + measure_corpus()["bare_print_lines"],
                           BARE_PRINT_LINE_CEILING,
                           u"贴一行进去仍然不超过 ceiling ⇒ 这把尺的长度是抄来的")


if __name__ == u"__main__":
    unittest.main(verbosity=2)
