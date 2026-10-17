#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R121 的变异表：参照臂的四种出口 + 新仪表自己的自检（M616–M619）。

本轮做的事：读 R119 的 CI（run 39024922502）把上一轮的成因**证伪**了 ——
帧已经是 720x600、整窗墨行=70，带子墨行仍是 0，而 `CARD_PROBE_COLUMNS` 说那 70 行
全在侧栏那一列（列0 墨行=70 / 列1、列2 墨行=0 最大偏离=0..2）。
所以「帧太矮把内容裁掉」不成立，「带子放错」也不成立（带子已铺满详情列）。
于是把 R107 写在注释里、从没当判据跑过的那条规则取出来重做：
证人从「整窗」换成「被告那一列自己」，`cardprobeArmVerdict` 给出四种出口，
其中两个是**有名字的不可判**（BACKLOG 150 的答案就是这个分类本身）。
另加 `CARD_PROBE_WITNESS`：样本与列内视图数出自同一条 `intersects`，对不上就是仪器坏。

四刀（全部期望 CAUGHT —— 这一轮的病是"仪器悄悄不说"，所以每刀都必须让某条断言红）：
  M616 样本恒空（把 area 排序后的赋值改成空数组）⇒ `CARD_PROBE_WITNESS_BROKEN` 红
  M617 两个不可判分支顺序互换 ⇒ 真值表里 (整帧0, 列0, 带子0) 那行拿到错的词
  M618 带子那条 `> 0` 改成 `>= 0`（恒真）⇒ 真值表里所有 band=0 的行全被判成可判
  M619 拆掉 `probeArmEvaluations += 1` ⇒ 恒等式「参照臂 = 可判 + 框错红 + 不可判」红

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r121.py [M616 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

SWIFT_ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(SWIFT_ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TRUTH = "testCardprobeArmVerdictIsATruthTable"
CARDPROBE = "testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"

ARMS = [
    ("M616", "样本赋值恒空 ⇒ 列内视图数>0 而样本=0 必须被自检抓到", CARDPROBE,
     "sample = raw.sorted { $0.area < $1.area }.prefix(8).map { $0.line }",
     "sample = []",
     "CAUGHT"),
    ("M617", "两个不可判分支互换顺序 ⇒ 真值表里整帧0墨那行必须拿到错的词", TRUTH,
     "        if pageInkRows == 0 { return .pageUnrendered }\n"
     "        if regionInkRows == 0 { return .regionUnpainted }\n",
     "        if regionInkRows == 0 { return .regionUnpainted }\n"
     "        if pageInkRows == 0 { return .pageUnrendered }\n",
     "CAUGHT"),
    ("M618", "带子那条存在性判据改成恒真 ⇒ 0 墨的臂冒充可判", TRUTH,
     "        if bandInkRows > 0 { return .judged }",
     "        if bandInkRows >= 0 { return .judged }",
     "CAUGHT"),
    ("M619", "拆掉一臂计数 ⇒ 恒等式「参照臂 = 可判 + 框错红 + 不可判」红", CARDPROBE,
     "                    probeArmEvaluations += 1\n",
     "",
     "CAUGHT"),
]


def read():
    with open(HARNESS, encoding="utf-8") as handle:
        return handle.read()


def save(text):
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(text)


def run(test):
    proc = subprocess.run(["swift", "test", "--filter", "UICaptureTests/" + test],
                          cwd=SWIFT_ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    verdicts = re.findall(r"Test Case '-\[[^\]]*\b%s\]' (passed|failed|skipped)" % test, out)
    if not verdicts:
        if "error:" in out:
            return "COMPILE-ERROR", out
        return "DID-NOT-RUN", out
    verdict = "CAUGHT" if verdicts[-1] == "failed" else verdicts[-1].upper()
    return verdict, out


def snippet_for(out):
    for key in ("CARD_PROBE_WITNESS cardprobe-split-groupbox light",
                "CARD_PROBE_CAPABILITY",
                "XCTAssertEqual failed",
                "CARD_PROBE_ARM_VERDICT cardprobe-split-groupbox light"):
        for line in out.splitlines():
            if key in line:
                return line.strip()[:200]
    return ""


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally = [], {}
    mismatch = not_run = 0
    for name, note, test, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = original.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run(test)
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet_for(out))) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet_for(out)))))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R121 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
