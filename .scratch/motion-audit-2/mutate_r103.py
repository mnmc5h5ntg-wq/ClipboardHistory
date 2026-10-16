#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R103 的变异表：新墨证人自己要有牙（M573 / M574 / M575 / M576）。

本轮只改一样东西：**`CARD_PROBE_ARM` 的那道证人**。R102 的 CI（run 38958447236）里
暗档三臂与亮档臂 2 一起报 `墨行=0`，四朵红把 BACKLOG 150 拦在门口 —— 而查下去发现
红的不是容器，是证人自己：上一版写的是 `rows.filter { $0 == .ink }.count`，
而 `rows` 是**材质那条通道**的中间量，`fill < 0` 时 `cardRowKinds` 整带交回 `.outside`
⇒ 证人在「判据说没有材质」的那一臂里**结构上必然**报 0。
它只能给不需要作证的那一侧作证。

四刀各钉哪一句：
  M573 把地板规则放宽成恒真（`inkPixels >= 0`）⇒ 真值表必须红
       —— 这一刀是整个形状的关键：**恒真的证人比缺席的证人更坏**，它会把「我框错了」洗成「这是答案」。
  M574 把「没有卡片填充时只剩页底一个参照」写回「拿 -1 当参照」⇒ 真值表第 ⑩ 条必须红
       （|28-(-1)|=29：页底像素会拿到假的高偏离，整带每行都成为墨 —— 又一版恒真证人）。
  M575 把反方向那条参考带从页底挪到卡片内容上 ⇒ `参考条墨行 == 0` 必须红
       （这一刀证明那条断言不是恒真：它真的在看一条空带子）。
  M576 把调用点退回 R102 那一版（吃 `rows`）⇒ **本机期望 ESCAPED，按实登记**：
       本机六臂都有材质，两版读数一样 ⇒ 这一刀的牙在 runner 上（那一台暗档 `rows` 全 `.outside`
       而字节里明明有墨）。不为了让它看起来有牙去编一条断言（与 M570 同规则）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r103.py [M573 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H_INSET = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
T_TRUTH = "UICaptureTests/testTextInkWitnessIsAnExistenceJudgeWithPairedFloors"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M573", "证人的地板放宽成恒真 ⇒ 真值表必须红（恒证的证人不能作证）", HARNESS,
     "        minPixels > 0 && inkPixels >= minPixels\n",
     "        inkPixels >= 0\n",
     T_TRUTH, "CAUGHT"),
    ("M574", "缺卡片参照时拿 -1 去比距离 ⇒ 真值表第 ⑩ 条必须红（页底会得到 29 的假偏离）", HARNESS,
     "        guard fill >= 0 else { return page }",
     "        guard fill >= 0 else { return abs(luma - fill) }",
     T_TRUTH, "CAUGHT"),
    ("M575", "反方向的参考带挪到卡片内容上 ⇒ 「参考条墨行=0」必须红（证明它不是恒真）", HARNESS,
     "                                                    rect: CGRect(x: 150, y: 4, width: 560, height: 8),",
     "                                                    rect: CGRect(x: 24, y: 80, width: 672, height: 8),",
     H_INSET, "CAUGHT"),
    ("M576", "调用点退回 R102 那一版（证人吃材质的中间量）⇒ 本机无判别力，牙在 runner 上", HARNESS,
     """                    let witness = Self.textInkWitness(bytes: base, width: rep.pixelsWide,
                                                      height: rep.pixelsHigh,
                                                      bytesPerRow: rep.bytesPerRow, rect: band,
                                                      scale: scale, fill: fill, pageLuma: pageLuma)""",
     "                    let witness = (rows: rows.filter { $0 == .ink }.count, pixels: 0, maxDelta: 0)",
     H_INSET, "PASSED"),
]

PREFLIGHT = [(T_TRUTH, "PASSED"), (H_INSET, "PASSED")]


def run(test_filter, timeout=2400):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True,
                          env=BASE_ENV, timeout=timeout)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        errs = [l.strip()[:200] for l in lines if "error:" in l][:4]
        return "DID-NOT-RUN", out, " || ".join(errs) or "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and
                 ("passed" in l or " failed" in l or "skipped" in l)]
    if not concluded:
        return "DID-NOT-RUN", out, "整条被跳过到没有结论行：" + (lines[-1][:200] if lines else "")
    skipped = any("skipped" in l for l in concluded)
    failed = any(" failed" in l for l in concluded)
    passed = any("passed" in l for l in concluded)
    if skipped and not failed and not passed:
        why = [l.strip()[:220] for l in out.splitlines() if "XCTSkip" in l]
        return "SKIPPED", out, (why[0] if why else "")
    if failed:
        why = [l.strip()[:300] for l in out.splitlines() if "error:" in l]
        return "CAUGHT", out, (why[0] if why else "")
    return "PASSED", out, ""


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    only = set(sys.argv[1:])
    results = []
    paths = sorted({a[2] for a in ARMS})
    originals = {p: read(p) for p in paths}
    snapshots = {p: open(os.path.join(ROOT, p), "rb").read() for p in paths}

    print("=== 预检（不注入：目标必须是 PASSED）===", flush=True)
    ok = True
    for test, want in PREFLIGHT:
        verdict, out, note = run(test)
        print("  %-72s %s" % (test, verdict), flush=True)
        if verdict != want:
            ok = False
            print("      期望 %s，拿到 %s｜%s" % (want, verdict, note[:220]), flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    for mid, title, path, needle, mutant, test, expect in ARMS:
        if only and mid not in only:
            continue
        text = originals[path]
        count = text.count(needle)
        if count != 1:
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中 %d 次，期望 1 ⇒ 不注入" % count))
            print("%s: DID-NOT-RUN needle 命中 %d" % (mid, count), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, evidence = run(test)
        except subprocess.TimeoutExpired:
            verdict, evidence = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        if verdict != "DID-NOT-RUN" and read(path).find(needle) < 0:
            evidence = "回读失败：原文不在了（还原步骤坏了？）" + evidence
        note = (u"对  期望 " + expect + (u"｜" + evidence[-200:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-300:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R103 汇总（每臂按自己的期望判定）===")
    for mid, verdict, line, expect, reason in results:
        mark = "OK " if verdict == expect else "!! "
        print("  %-5s exp=%-8s got=%-12s %s%s  %s"
              % (mid, expect, verdict, mark, line, reason))
    dirty = [p for p in paths
             if open(os.path.join(ROOT, p), "rb").read() != snapshots[p]]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    good = sum(1 for _, v, _, e, _ in results if v == e)
    bad = sum(1 for _, v, _, e, r in results if v != e and r.startswith(u"!!"))
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), good, bad,
             sum(1 for _, v, _, _, _ in results if v == "DID-NOT-RUN")))
    want = len(ARMS) if not only else len(only)
    return 0 if not dirty and good == want and len(results) == want else 1


if __name__ == "__main__":
    sys.exit(main())
