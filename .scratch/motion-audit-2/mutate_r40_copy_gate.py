#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R40 变异对照：复制失败 → 不许自动粘贴 这道闸门，四种坏法各该红一次。

  M185 闸门整段拿掉（回到 R40 之前）        ⇒ 管线臂红在"仍然注入了 ⌘V"
  M186 闸门方向反了（成功挡掉、失败放行）  ⇒ 红在"正常路径被挡掉了"
  M187 只取消不说话（回执不报）            ⇒ 红在"复制失败必须浮到界面"
  M188 决策表本身方向反了                  ⇒ 真值表那一格必须红

M186 与 M188 看着像同一件事，其实不是：M188 改的是**纯函数**，
如果只测纯函数（没有 M186 那条调用点变异），"接错方向"仍可能悄悄溜过去 ——
调用点的 switch 与决策表是两处代码，两处都可能反。
"""
import os
import subprocess
import sys

from knife_guard import backup, clear_backup, restore_if_stale, run as guarded_run

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SHELL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/ApplicationShell.swift")
POLICY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/CopyThenPaste.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

FILTER = "PasteFailureVisibilityTests"

GATE = """        switch CopyThenPaste.decide(failure: historyStore?.clipboardWriteFailure) {
        case .pasteNow:
            break
        case .cancel(let reason):
            reportPasteOutcome(reason)
            return
        }"""
GATE_REMOVED = "        // MUTANT：闸门整段拿掉（回到 R40 之前：复制失败也照样切前台、照样按键）"
GATE_INVERTED = """        switch CopyThenPaste.decide(failure: historyStore?.clipboardWriteFailure) {
        case .pasteNow:
            return  // MUTANT：方向反了 ⇒ 成功的不许粘
        case .cancel(let reason):
            reportPasteOutcome(reason)  // MUTANT：失败的反而放行
        }"""
GATE_SILENT = """        switch CopyThenPaste.decide(failure: historyStore?.clipboardWriteFailure) {
        case .pasteNow:
            break
        case .cancel(let reason):
            _ = reason  // MUTANT：只取消，不说话
            return
        }"""
DECIDE = """        guard let failure else { return .pasteNow }"""
# R378：`guard failure == nil else` 编译不过（下面要用 `failure.message`，可选型没解开）。
# 改成「成功那一格也判取消」：同样的坏方向，且能编译 —— 真值表那格必须红在「必须放行」。
DECIDE_INVERTED = """        guard let failure else { return .cancel(reason: "MUTANT：成功反被挡") }"""

MUTATIONS = [
    ("M185", "闸门整段拿掉", SHELL, GATE, GATE_REMOVED, "仍然注入了"),
    ("M186", "闸门方向反了（成功挡掉、失败放行）", SHELL, GATE, GATE_INVERTED, "正常路径被闸门误挡"),
    ("M187", "只取消、不说话", SHELL, GATE, GATE_SILENT, "复制失败必须浮到界面"),
    ("M188", "决策表把成功也判成取消（方向反）", POLICY, DECIDE, DECIDE_INVERTED, "必须放行"),
]


def run():
    # R378 / BACKLOG 433：硬超时 + 进程组/子孙树 KILL，超时记 NOT_RUN_TIMEOUT。
    code, out, timed_out = guarded_run(["swift", "test", "--filter", FILTER],
                                       cwd=ROOT, env=BASE_ENV, timeout_seconds=600)
    if timed_out:
        return "NOT_RUN_TIMEOUT", out, []
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if code != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:120]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    # R378：上一次落刀若没被还原（进程被杀），先恢复再预检。
    for path, tag in ((SHELL, "SHELL"), (POLICY, "POLICY")):
        if restore_if_stale(path, tag):
            print("KNIFE_RESTORED_FROM_BACKUP " + tag)
    wanted = set(sys.argv[1:])
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1200:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needle in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        backup(path, mid)
        original = apply(path, old, new)
        try:
            code, out, failed = run()
        finally:
            ok = restore(path, original)
            if ok:
                clear_backup(path, mid)
        right = needle in out
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO",
                        ",".join(f.split(".")[-1] for f in failed)))
        print("%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, right, failed))
        if code != "CAUGHT" or not right:
            print(out[-1200:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] != "yes"]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


if __name__ == "__main__":
    main()
