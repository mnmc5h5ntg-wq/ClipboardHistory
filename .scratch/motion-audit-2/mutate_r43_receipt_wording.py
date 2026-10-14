#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43 变异对照：导出/导入那三条回执，七种坏法各该红一次。

  M199 导出反馈退回 `localizedDescription` 直出      ⇒ 红在"动作里又出现 localizedDescription"
  M200 模态那条通道被加回来（名字回来了）            ⇒ 红在"第二条通道被加回来了"
  M201 导入失败那句不再说"记录没有任何变化"          ⇒ 红在真值表那一格
  M202 writingFailed 的 payload 被拼进界面            ⇒ 红在"payload 是诊断材料，归日志"
  M203 「暂无数据」被说成失败                        ⇒ 红在"空数据被说成失败"
  M204 存档导出的 catch 不再走映射器（手写一句）      ⇒ 红在"不再走映射器 ⇒ 真值表与界面会分家"
  M205 夹具把产品文案换成手写字面量（R14 那张帧的原样）⇒ 红在"帧里的回执文案是手写的"

needle 一律**从 --measure 那一遍打印的失败消息原文里抄**（R41/R42 的账：同一族错犯了三次）。
判"红得对"只看失败消息那一层，不看整份日志。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SETTINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
CONTROLLER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/SettingsWindowController.swift")
WORDINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/ReceiptWordings.swift")
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "SettingsFailureReceiptTests"

FEEDBACK_FAILURE_CALL = "            exportMessage = FeedbackExportReceipt.failure(error)"
STATE_EXPORT = "    @State private var exportMessage: String?"
IMPORT_SENTENCE = ('        "导入失败：这个文件没能读进历史，记录没有任何变化。"')
WRITING_SENTENCE = ('            return "导出失败：这些反馈数据没能写进磁盘，文件没有生成。"')
NODATA_ARM = "            return noData"
ARCHIVE_EXPORT_CALL = "                    return ArchiveTransferReceipt.exportFailed(error)"
FIXTURE_CALL = """                ReceiptLine(text: FeedbackExportReceipt.failure(
                                RecommendationFeedbackStore.ExportError.writingFailed("disk full")),
                            dismiss: {})"""

MUTATIONS = [
    ("M199", "导出反馈退回系统原文直出", SETTINGS, FEEDBACK_FAILURE_CALL,
     '            exportMessage = "导出失败：\\(error.localizedDescription)"  // MUTANT',
     ["动作里又出现 `localizedDescription`"]),
    ("M200", "模态那条通道的名字回来了", SETTINGS, STATE_EXPORT,
     STATE_EXPORT + "\n    @State private var showExportAlertWasRemoved = false  // MUTANT",
     ["第二条通道被加回来了"]),
    ("M201", "导入失败不再说“记录没有任何变化”", WORDINGS, IMPORT_SENTENCE,
     '        "导入失败：这个文件没能读进历史。"  // MUTANT',
     ["没能读进历史。请确认"]),
    ("M202", "写盘失败的 payload 被拼进界面", WORDINGS, WRITING_SENTENCE,
     '            return "导出失败：\\(String(describing: error))"  // MUTANT',
     ["payload 是诊断材料"]),
    ("M203", "「暂无数据」被说成失败", WORDINGS, NODATA_ARM,
     '            return "导出失败：暂无数据"  // MUTANT',
     ["空数据被说成失败"]),
    ("M204", "存档导出的 catch 不再走映射器", CONTROLLER, ARCHIVE_EXPORT_CALL,
     '                    return "导出失败，请重试"  // MUTANT',
     ["导出存档那条回执不再走映射器"]),
    ("M205", "夹具把文案换回手写字面量", HARNESS, FIXTURE_CALL,
     '                ReceiptLine(text: "已导出 94 条记录到 ~/Desktop/时间剪史-导出.json", dismiss: {})  // MUTANT',
     ["这些 ReceiptLine 夹具的文案是手写的字面量"]),
]


def failure_messages(out):
    """只看失败消息那一层（XCTAssert 两种格式都认：`failed:` 与 `failed -`）。"""
    return [line for line in out.splitlines()
            if ("error: -[" in line and " failed" in line) or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1500:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        messages = failure_messages(out)
        hit = [n for n in needles if any(n in m for m in messages)]
        right = bool(needles) and len(hit) == len(needles) and "待 --measure" not in needles
        ok = restore(path, original)
        results.append((mid, code, "MEASURE" if measure else ("yes" if right else "NO"),
                        "yes" if ok else "NO", ",".join(f.split(".")[-1] for f in failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure or not right or code != "CAUGHT":
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:420])
        if measure or not right or code != "CAUGHT":
            print(out[-500:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] not in ("yes", "MEASURE")]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


if __name__ == "__main__":
    main()
