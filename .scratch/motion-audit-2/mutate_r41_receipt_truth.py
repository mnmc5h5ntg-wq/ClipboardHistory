#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R41 变异对照：那条"报告失败"的回执，五种坏法各该红一次。

  M189 三种写入失败被标成"没清空"        ⇒ 真值表红在"必须承认旧内容没了"
  M190 未分类错误退回 localizedDescription ⇒ 真值表红在"系统英文原文不许进界面"
  M191 decide 无视 clearedPasteboard      ⇒ 真值表红在"同一句里不许既说…又说…"
  M192 Store 绕过 classify 直存原文        ⇒ 管线臂红在"未分类错误下不许承诺旧内容还在"
  M193 唯一"没清空"那一型被标成清空       ⇒ 真值表红在"这句才是真话"

M189 与 M193 是同一个布尔的两侧（这两支的「预期红」第一版又写错了：
我按 decide 的措辞写 needle，实际红在 classify 的那两格 —— 同一族第二次犯，
规矩照旧：needle 只能从实测日志里抄，不许从代码里推）：只测一侧的话，把默认值写反（`clearedPasteboard: true`
到处填）也能全绿。R40 那句谎话正是这么来的。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FAILURE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/ClipboardWriteFailure.swift")
PASTE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/CopyThenPaste.swift")
STORE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

FILTER = "PasteFailureVisibilityTests"

TEXT_CASE = '''            return ClipboardWriteFailure(
                message: "文本没能写进系统剪贴板（常被其他应用短暂占用）。",
                clearedPasteboard: true)'''
UNKNOWN_MSG = '''                message: "系统剪贴板拒绝写入（未分类错误）。这条记录本身没有变化，请重新复制一次。",'''
DECIDE_BRANCH = "        if failure.clearedPasteboard {"
STORE_CLASSIFY = "            clipboardWriteFailure = ClipboardWriteFailure.classify(error)"
MISSING_FLAG = "                clearedPasteboard: false)"

MUTATIONS = [
    ("M189", "三种写入失败被标成「没清空」（R40 那句谎话的形状）", FAILURE, TEXT_CASE,
     '''            return ClipboardWriteFailure(
                message: "文本没能写进系统剪贴板（常被其他应用短暂占用）。",
                clearedPasteboard: false)  // MUTANT''',
     "发生在 clearContents 之后"),
    ("M190", "未分类错误退回系统原文", FAILURE, UNKNOWN_MSG,
     '''                message: "系统剪贴板拒绝写入（\\(error.localizedDescription)）。",  // MUTANT''',
     "系统英文原文不许进界面"),
    ("M191", "decide 无视 clearedPasteboard", PASTE, DECIDE_BRANCH,
     "        if false {  // MUTANT：两种后果被并成一句",
     "同一句里不许既说"),
    ("M192", "Store 绕过 classify，直存 localizedDescription + 承诺没清空", STORE, STORE_CLASSIFY,
     "            clipboardWriteFailure = ClipboardWriteFailure("
     + "message: error.localizedDescription, clearedPasteboard: false)  // MUTANT",
     "未分类错误下不许承诺旧内容还在"),
    ("M193", "唯一「没清空」那一型被标成清空", FAILURE, MISSING_FLAG,
     "                clearedPasteboard: true)  // MUTANT",
     "抛在 clearContents 之前"),
]


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
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:120]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    wanted = set(sys.argv[1:])
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1200:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needle in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        right = needle in out
        ok = restore(path, original)
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
