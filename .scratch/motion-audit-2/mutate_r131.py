#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R131 的变异表：「指针必须指得到」与「缺席断言必须真缺席」两条新判据的牙（M642-M644）。

本轮做的事：清账表从 26 格扩到 38 格（菜单栏/状态图标、提示条、热图、说明段、列表行、详情区），
而其中五格立论靠的是**缺席**（"那个文件里没有 onTapGesture"）。上一版的闸门只判指针的**形状**
（U-424），于是它当场被自己的新数据打脸：R128 那两行写的
`Sources/ClipboardHistoryApp/ContentView.swift` 少了 `Views/` 一段 —— 形状合法、文件不存在，
读的人点不开，而闸门一直是绿的。⇒ 两条新判据：路径必须解析得到、`缺席:路径=词` 必须真缺席。

三刀（都期望 CAUGHT）：
  M642 摘掉路径存在检查 => 指向不存在文件的指针又能当证据用
  M643 让缺席断言恒过   => "没量过的缺席"重新变成免检的开脱
  M644 解析时只认仓库根（去掉 `ClipboardHistory/` 那一层候选）=> 整张真表被判成假
       （这一刀留着是有原因的：它证明这条判据坏的时候会坏在最坏的一侧，而不是静默放行）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r131.py [M642 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GATE = os.path.join(ROOT, "scripts/motion_surface_gate.py")
TESTS = "test_motion_surface_gate.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M642", "摘掉「指针指向的文件必须存在」=> 形状合法但点不开的指针重新算证据",
     "        if resolve(path, root) is None:", "        if False:", "CAUGHT"),
    ("M643", "让缺席断言恒过 => 写着「文件里没有这个词」而词就在里面，也没人报了",
     "        if token in text:", "        if False:", "CAUGHT"),
    ("M644", "解析只认仓库根（去掉 ClipboardHistory/ 那一层候选）=> 整张真表被判成假",
     '    for base in (root, os.path.join(root, "ClipboardHistory")):',
     "    for base in (root,):", "CAUGHT"),
]


def read():
    return open(GATE, encoding="utf-8").read()


def save(text):
    open(GATE, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "scripts/tests",
                           "-p", TESTS],
                          cwd=ROOT, env=dict(ENV, PYTHONUTF8="1"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    ran = re.search(r"Ran (\d+) tests", out)
    if not ran or int(ran.group(1)) == 0:
        return "DID-NOT-RUN", out
    m = re.search(r"^(OK|FAILED)", out, re.M)
    if not m:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if m.group(1) == "FAILED" else "PASSED"), out


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally, mismatch, not_run = [], {}, 0, 0
    for name, note, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = original.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, ""))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run()
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        mismatch += 0 if verdict == expect else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        names = sorted({l.split()[1] for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
        print("%s: %s %s 红掉的测试=%s" % (name, verdict, note, ",".join(names) or "-"))
        results.append((name, expect, verdict, note, names[0] if names else ""))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R131 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
