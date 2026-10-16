#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 补的第二张变异表：能力闸门与诊断通道都要有牙（M560 / M561 / M562）。

为什么单独一张表、而且**每臂的期望不一样**：

M560 / M561（期望 = SKIP，不是红也不是绿）
  R100 把「这台机器看不见卡片材质」从永久红改成 `throw XCTSkip`。
  skip 是一种**看起来像通过**的收场 —— 报表上它只多一个 `skipped=` 计数。
  所以「没对象时要响」这句话本身必须能被证伪：
  **把能力信号强行归零，判据必须变成 skipped；如果它还是 passed，那 skip 那一格就是假的
  （等于把「没跑」重新记成「通过」，正是 BACKLOG 43 那一族）。**
    M560 横向判据：`materialCells` 强行归零 ⇒ 必须 skip
    M561 竖向判据：同样归零 ⇒ 必须 skip

M562（期望 = CAUGHT）
  本轮新加的 `CARD_FILL_CANDIDATES`（BACKLOG 147 的成因通道）是一条**会被打印**的读数，
  而一条只有打印、没有闸门的读数可以恒为「无」而不被发觉（D-162）。
  它的牙在真值表那一格：`fillCandidates` 的名次如果按**色号**而不是按**行数**排，
  ①/③ 两格立刻红 —— 而那正是 147 要区分的形状（按色号排 = R96 那条真病根「第一行离页底
  最远的档被当成卡片」在这把尺里复活）。
    M562 `fillCandidates` 的比较器换成按色号降序 ⇒ 真值表必须红

诚实记账（这一臂**没有**做，原因是量出来的，不是嫌麻烦）：
  换掉调用点的 `if fill < 0 {` 闸门（让它反过来打）不会被任何判据抓到 ——
  因为 `declined.count ≤ 6` 那条断言数的是"读不到卡片"的格数，与这一行打没打无关。
  所以 147 的这条通道在**本机**只有真值表这一层保护；它真正的验收发生在下一次 CI run
  读到这一行的那一刻（见 AGENT_BACKLOG.md 147 与 `.scratch/motion-audit-2/r100_ci_readings.md` §④）。

反向对照（证明 skip 不是无条件发生的）：预检不注入 ⇒ M560/M561 的目标必须 passed。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r100b.py [M560 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H_INSET = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
V_RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"
T_TABLE = "UICaptureTests/testFillCandidatesSeparatesNoMaterialFromMaterialTooCloseToPage"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
# **needle 不能靠缩进区分这两格**：12 空格那一串是 16 空格那一串的**子串**，
# 所以"浅缩进"那一支永远命中 2 次 ⇒ DID-NOT-RUN（本轮第一次跑就是这样，脚本拒绝注入是对的）。
# 区分要靠**上一行**（`cells += 1` 对 `settingsCells += 1`），这两格的上一行本来就不同。
ARMS = [
    ("M560", "横向判据：能力信号强行归零 ⇒ 必须 skip（不许 passed、不许红）", HARNESS,
     "                cells += 1\n                if fill >= 0 { materialCells += 1 }",
     "                cells += 1\n                if fill >= 0 { materialCells += 1 }\n                materialCells = 0",
     H_INSET, "SKIPPED"),
    ("M561", "竖向判据：能力信号强行归零 ⇒ 必须 skip（不许 passed、不许红）", HARNESS,
     "            settingsCells += 1\n            if fill >= 0 { materialCells += 1 }",
     "            settingsCells += 1\n            if fill >= 0 { materialCells += 1 }\n            materialCells = 0",
     V_RHYTHM, "SKIPPED"),
    ("M562", "诊断通道：前三名改成按色号排 ⇒ 真值表必须红", HARNESS,
     "            if l != r { return l > r }\n            return lhs < rhs",
     "            return lhs > rhs",
     T_TABLE, "CAUGHT"),
]

PREFLIGHT = [(H_INSET, "PASSED"), (V_RHYTHM, "PASSED"), (T_TABLE, "PASSED")]


def run(test_filter, timeout=2400):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True,
                          env=BASE_ENV, timeout=timeout)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        errs = [l.strip()[:160] for l in lines if "error:" in l][:4]
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
        why = [l.strip()[:220] for l in out.splitlines() if " failed " in l or "XCTAssert" in l]
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
    paths = [HARNESS]
    originals = {p: read(p) for p in paths}
    snapshots = {p: open(os.path.join(ROOT, p), "rb").read() for p in paths}

    print("=== 预检（不注入：三处都必须是 passed）===", flush=True)
    ok = True
    for test, want in PREFLIGHT:
        verdict, out, note = run(test)
        print("  %-76s %s" % (test.split("/")[-1], verdict), flush=True)
        if verdict != want:
            ok = False
            print("      期望 %s，拿到 %s｜%s" % (want, verdict, note[:200]), flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    for mid, title, path, needle, mutant, test, expect in ARMS:
        if only and mid not in only:
            continue
        text = originals[path]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, evidence = run(test)
        except subprocess.TimeoutExpired:
            verdict, evidence = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        # 结论行必须带**原文**：只有 verdict 的话，下一次没人能核对它抓的是哪一句。
        note = (u"对  期望 " + expect + (u"｜" + evidence[-150:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-220:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R100b 汇总（每臂按自己的期望判定）===")
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
