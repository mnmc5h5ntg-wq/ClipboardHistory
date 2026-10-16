#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R99 的变异对照：卡片"外面还剩几段墨"这把新尺，四刀，全部期望 CAUGHT。

本轮做的事：
  ① 修 R99 自己写的第一版 `CARD_ABOVE` —— 它把 `cardRowKinds` 交回来的**带内相对行号**
     直接当**位图绝对行**喂进 `columnInk`，于是量的窗口是 0..45.5pt 而不是 60..106pt，
     九屏全报"卡片顶之上没有墨"（那张被隔离的 python 尺这一格反而报对了）。
     现在换算有真值表（`testBandRowToAbsoluteRowIsATruthTable`）+ 调用处恒等式。
  ② 把"卡片之外只剩分区标题"钉成名单判据（上方恰好 1 段、下方 0 段）。
  ③ 产品照这个名字改：「推荐权重客制化」标题行 + 说明段搬进卡片，
     「推荐反馈数据」从"裸分隔线 + 卡片外内容"收成第二张卡片。

四刀各钉一角，M552 是**两条账**（名单 + 真值表）：
  M552 尺：`absoluteRows` 丢掉 `bandMinY` 那一档 ⇒ 名单红 **且** 真值表红
  M553 尺：把段高地板抬到 400px（= 让这把尺瞎掉）⇒ 名单必须红
           —— 这一刀是名单那条判据的**非恒真证明**：尺瞎了不许报"干净"
  M554 产品：两个产品文件还原成 HEAD 那一版（= 本轮改之前）⇒ 上方 3 段红、下方 2 段红
  M555 产品：第二张卡片丢掉 `.frame(maxWidth: .infinity)` ⇒ 卡片按内容缩成 250pt 宽，
             尺读不到它的材质 ⇒ 下方 2 段红（本轮是**看帧**抓到的，不是看代码）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r99.py [M552 ...]
退出码：0 = 全部 CAUGHT 且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
VIEW = "Sources/ClipboardHistoryApp/Views/RecommendationWeightsView.swift"
SETTINGS = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"
PRODUCT = (VIEW, SETTINGS)

BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"
TRUTH = "UICaptureTests/testBandRowToAbsoluteRowIsATruthTable"

# (编号, 标题, 文件, needle, mutant, 主判据, 期望红在哪句话, 第二支判据, 第二支期望)
NEEDLE_ARMS = [
    ("M552", "absoluteRows 丢掉扫描带上沿（回到本轮第一版那个错）", HARNESS,
     "        let top = max(0, Int(bandMinY * scale))",
     "        let top = 0",
     RHYTHM, "卡片顶之上读到 0 段墨", TRUTH, "XCTAssertEqual failed"),
    ("M553", "把段高地板抬到 400px（= 让这把尺瞎掉）", HARNESS,
     "                let above = Self.inkRuns(column: aboveVec, minRunHeight: 4,",
     "                let above = Self.inkRuns(column: aboveVec, minRunHeight: 400,",
     RHYTHM, "卡片顶之上读到 0 段墨", None, None),
]

# 第二张卡片缩回内容宽度（本轮看图抓到的那个形状）
M555 = ("M555", "第二张卡片丢掉 maxWidth ⇒ 缩成 250pt 宽、尺读不到材质", SETTINGS,
        """                    .animation(MotionCatalog.animation(for: .contentFade), value: exportMessage == nil)
                }
                .frame(maxWidth: .infinity, alignment: .leading)""",
        """                    .animation(MotionCatalog.animation(for: .contentFade), value: exportMessage == nil)
                }""",
        RHYTHM, "还读到 2 段墨", None, None)


def run(test_filter, timeout=2400):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True,
                          env=BASE_ENV, timeout=timeout)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", out, "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not concluded:
        return "DID-NOT-RUN", out, "整条被 skip：" + (lines[-1][:200] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, ""


# **还原臂的基准必须是钉死的 commit，不能是 `HEAD`**（R100 的电池抓出来的，U-277）：
# 这一支的本意是"把两个产品文件换回**本轮改之前**那一版"，而"改之前"在写它的那天恰好等于 `HEAD`。
# R99 一提交，`HEAD` 就前进到**已经修好**的那一版 ⇒ 还原臂还原了个空，
# 于是它在 R100 的电池里以 `M554: ESCAPED` 的形式露出来 —— 不是判据没牙，是**参照点会自己走**。
# 3a05933 = R98 那一版（本轮改动之前），从此这一支与 `HEAD` 无关，永远还原到同一个状态。
PRE_FIX_COMMIT = "3a05933"


def git_show(path):
    proc = subprocess.run(["git", "show", PRE_FIX_COMMIT + ":ClipboardHistory/" + path],
                          cwd="/Users/wangziyi/Codex_Project0", capture_output=True,
                          text=True)
    if proc.returncode != 0:
        raise RuntimeError("git show 失败：%s" % proc.stderr[:200])
    return proc.stdout


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def arm_revert(results):
    """M554：把两个产品文件**整体**还原成 HEAD 那一版（= 本轮改之前的产品）。

    为什么不用手搓 needle：本轮产品改动是"把两段内容搬进容器"，
    任何一行局部替换都造不出"内容在卡片外"这个形状；而 `git show HEAD:` 给的就是
    那一个状态本身 —— 还原臂比仿制臂少一层"我猜的变异长得像不像真缺陷"。
    """
    snapshots = {p: read(p) for p in PRODUCT}
    try:
        for p in PRODUCT:
            write(p, git_show(p))
    except RuntimeError as err:
        results.append(("M554", "DID-NOT-RUN", "还原成 HEAD 那一版", str(err)[:150]))
        for p, text in snapshots.items():
            write(p, text)
        return
    verdict, out, note = run(RHYTHM)
    for p, text in snapshots.items():
        write(p, text)
    above = "卡片顶之上读到 3 段墨" in out
    below = "还读到 2 段墨" in out
    reason = ("对  上方 3 段=%s 下方 2 段=%s" % (above, below)) if verdict == "CAUGHT" else note
    if verdict == "CAUGHT" and not (above and below):
        reason = "!! 红得不全（上方 %s / 下方 %s）" % (above, below)
    results.append(("M554", verdict, "两个产品文件还原成改之前", reason))
    print("M554: %s %s" % (verdict, reason), flush=True)


def main():
    only = set(sys.argv[1:])
    results = []
    paths = sorted({HARNESS} | set(PRODUCT))
    originals = {p: read(p) for p in paths}
    snapshots = {p: open(os.path.join(ROOT, p), "rb").read() for p in paths}

    print("=== 预检（不注入任何变异，两支判据都必须绿）===", flush=True)
    ok = True
    for test in (RHYTHM, TRUTH):
        verdict, out, note = run(test)
        print("  %-62s %s" % (test, verdict), flush=True)
        if verdict != "ESCAPED":
            ok = False
            print("  " + note[:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    arms = list(NEEDLE_ARMS) + [M555]
    if not only or "M554" in only:
        arm_revert(results)
    for mid, title, path, needle, mutant, test, expect, second, expect2 in arms:
        if only and mid not in only:
            continue
        text = originals[path]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, note = run(test)
            extra = ""
            if verdict == "CAUGHT" and expect not in out:
                note = "!! 红得不对（找不到期望文本「%s」）" % expect
                verdict = "MISMATCH"
            if second:
                note = "对  「%s」" % expect
                v2, o2, n2 = run(second)
                extra = " | 真值表=%s" % v2
                if v2 != "CAUGHT":
                    note = "!! 同一刀没让真值表红（那条守卫没牙）" + n2[:120]
                elif expect2 and expect2 not in o2:
                    note = "!! 真值表红了但不是这一句" + n2[:120]
            else:
                note = "对  「" + ([l for l in out.splitlines() if expect in l][:1]
                                  or [""])[0].strip()[-140:] + "」" if verdict == "CAUGHT" else note
        except subprocess.TimeoutExpired:
            verdict, note, extra = "DID-NOT-RUN", "timeout", ""
        finally:
            write(path, originals[path])
        results.append((mid, verdict, title, note + extra))
        print("%s: %s %s %s%s" % (mid, verdict, title, note, extra), flush=True)

    print("\n=== R99 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, line, reason))
    dirty = [p for p in paths
             if open(os.path.join(ROOT, p), "rb").read() != snapshots[p]]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v in ("ESCAPED", "MISMATCH")
                 or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    return 0 if not dirty and caught == len(results) == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
