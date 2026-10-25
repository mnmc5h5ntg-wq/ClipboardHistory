#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R326 的变异表：六把刀钉的是**色档 A/B 换了统计量这一件事**（M943…M948）。

本轮的起因是一组对不上的读数：同一笔 commit（R325 的 `929c084`），本机读
`敏感=0`，runner（RUN=40057803215）读 `敏感=2`，而两台的**帧数都是 30/30**；
`noticeBanner` 的峰值本机 0.2598、runner 0.7208。⇒ 那颗峰值量的是采样通道，
不是色档，却被拿去决定"要不要钉色档"这个**动作**。

修法是把分类器收的数换成三颗通道无关的量（首末面积 / 动过的并集 / 首末墨量差），
取较大者判；峰值降为**只印不判**（`MOTION_SCENARIO_AB_CHANNEL`）。

六把刀各拆一环，每条都指定"哪一条用例必须红"：

  M943 让首末面积变成峰值的别名                     ⇒ 采样粒度证人必须红
       （这一刀就是本轮要被推翻的那颗旧尺：证人要是放得过它，说明新尺没换掉东西）
  M944 分类器只读首末面积、丢掉并集（R358 重钉：墨量已只印不判）           ⇒ 词表与分界证人必须红
       （取较大者这一半没有牙的话，"换统计量"就等于挑一颗恰好看不见问题的尺）
  M945 墨量那颗退化成"变没变"的计数                 ⇒ 面积盲区证人必须红
       （深浅读不出来的尺只是面积尺的别名 —— 这条是防本轮自己把判据换窄）
  M946 两臂粒度容差改成"帧数必须相等"               ⇒ 容差证人必须红
       （这不是假设：第一版就是这么写的，`blank` 暗 27 / 亮 28 当场红在判据自己身上）
  M947 并集的分母从"采样像素数"改成"帧对数"          ⇒ 采样粒度证人必须红
       （分母一跟着帧数走，"通道无关"这句话立刻不成立）
  M948 比值样本不再收进 MAGNITUDE 那一格            ⇒ 探针的分母同一性必须红
       （"亮臂更大=11/11" 是本轮不拿 敏感=8 去钉 8 颗的**读数**，它必须会红）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r326.py [M943 … M948]
（M948 那一臂要跑真探针，`ENV` 里已经带 `CLIPBOARD_HISTORY_UI_MOTION=1`；
  没设就会得到 skip，而 skip 在这一支表里是 NOT_RUN，不是过关。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
FILM = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                    "MotionFilmstripTests.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = u"1"

PROBE = u"MotionFilmstripTests/testFilmScenarioAppearanceDependenceIsMeasuredPerScenario"
PURE = u"MotionPillRampTests"
PROBE_TEST = u"testFilmScenarioAppearanceDependenceIsMeasuredPerScenario"
CLASSIFY_TEST = u"testAppearanceDependenceVerdictWordsAndBoundaries"
SAMPLING_TEST = u"testAppearanceStatisticsSurviveASamplingChange"
INK_TEST = u"testEndpointAreaIsBlindToInkMagnitudeButTheVerdictIsNot"
TOLERANCE_TEST = u"testSamplingComparableToleranceAdmitsJitterButNotACollapsedArm"

# ① 首末面积变成峰值的别名 ⇒ 它又跟着采样粒度走了。
NEEDLE_943 = u"        return changedFraction(raster(first), raster(last), band: band)\n"
REPL_943 = u"        return peak(deltas(frames, band: band))\n"

# ② 只读首末面积：并集与墨量两颗被摘掉 ⇒ 取较大者这一半没牙。
NEEDLE_944 = (u"        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),\n"
              u"                            Self.relativeDifference(unionDark, unionLight))")
REPL_944 = u"        let rel = Self.relativeDifference(endpointDark, endpointLight)\n"

# ③ 墨量退化成"变没变"的计数 ⇒ 深浅读不出来，只剩面积。
NEEDLE_945 = u"                total += Double(Swift.max(rgb, alpha))\n"
REPL_945 = u"                total += Double((rgb > 8 || alpha > 8) ? 1 : 0)\n"

# ④ 粒度容差换成"必须相等" ⇒ 时钟抖动会被判成没有对照物。
NEEDLE_946 = u"        return gap <= 1 || Double(gap) / Double(denom) <= 0.25\n"
REPL_946 = u"        return gap == 0\n"

# ⑤ 并集的分母跟着帧对数走 ⇒ "通道无关"当场不成立。
NEEDLE_947 = (u"            while x < xEnd {\n"
              u"                sampled += 1\n"
              u"                for index in 1..<bitmaps.count {\n")
REPL_947 = (u"            while x < xEnd {\n"
            u"                for index in 1..<bitmaps.count {\n"
            u"                    sampled += 1\n")

# ⑥ MAGNITUDE 那一格的样本偷偷漏掉 ⇒ 分母同一性必须红。
NEEDLE_948 = u"                if inkLight > 0 { ratios.append(inkDark / inkLight) }\n"
REPL_948 = u""

ARMS = [
    ("M943", u"尺：首末面积变成峰值别名 ⇒ 粒度证人必须红", FILM,
     NEEDLE_943, REPL_943, SAMPLING_TEST, PURE),
    ("M944", u"尺：分类器只读面积 ⇒ 词表与分界证人必须红", FILM,
     NEEDLE_944, REPL_944, CLASSIFY_TEST, PURE),
    ("M945", u"尺：墨量退化成计数 ⇒ 面积盲区证人必须红", FILM,
     NEEDLE_945, REPL_945, INK_TEST, PURE),
    ("M946", u"尺：粒度容差写成帧数必须相等 ⇒ 容差证人必须红", FILM,
     NEEDLE_946, REPL_946, TOLERANCE_TEST, PURE),
    ("M947", u"尺：并集分母跟着帧对数走 ⇒ 粒度证人必须红", FILM,
     NEEDLE_947, REPL_947, SAMPLING_TEST, PURE),
    ("M948", u"尺：比值样本偷偷漏收 ⇒ 探针的分母同一性必须红", FILM,
     NEEDLE_948, REPL_948, PROBE_TEST, PROBE),
]
TARGETS = sorted({a[2] for a in ARMS})


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite(filt):
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", filt],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1) for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    skipped = len(re.findall(r"Test Case '[^']+' skipped", out))
    if failures < 0:
        return n, False, [u"NO_SUMMARY_LINE（读不到失败数）"], out, skipped
    return n, (n >= 1 and failures > 0), names, out, skipped


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print(u"ARG_ERROR 不认识这些臂号：%s（认识的是 %s）"
              % (u", ".join(unknown), u", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print(u"ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    originals = {path: read(path) for path in TARGETS}
    clock = [time.time() + 10.0]

    def restore():
        for path, base in originals.items():
            save(path, base, bump=clock[0])
        clock[0] += 10.0

    restore()
    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if skipped:
            restore()
            print(u"PRECHECK_FAILED 基线里 %s 被 skip（skipped=%d）⇒ 没设 CLIPBOARD_HISTORY_UI_MOTION=1"
                  % (filt, skipped))
            return 1
        if red or n == 0:
            restore()
            print(u"PRECHECK_FAILED 未落刀时 %s 基线不绿（Executed=%d 红=%s）"
                  % (filt, n, u", ".join(names)))
            return 1
        print(u"BASELINE_GREEN %s Executed=%d" % (filt, n))

    caught = 0
    mismatch = 0
    not_run = 0
    for arm_id, why, target, old, new, expected, filt in arms:
        text = read(target)
        if text.count(old) != 1:
            not_run += 1
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:52]))
            continue
        want_text = text.replace(old, new)
        save(target, want_text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != want_text:
            restore()
            not_run += 1
            print(u"%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out, skipped = run_suite(filt)
        restore()
        if names and names[0].startswith(u"NO_SUMMARY_LINE"):
            not_run += 1
            print(u"%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif skipped:
            not_run += 1
            print(u"%s NOT_RUN 落刀后被 skip（skipped=%d）⇒ 不许记成 CAUGHT" % (arm_id, skipped))
        elif "error: " in out and not red:
            not_run += 1
            print(u"%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and any(expected in name for name in names):
            caught += 1
            print(u"%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:32], n, u", ".join(names)))
        elif red:
            mismatch += 1
            print(u"%s MISMATCH 红了但不是它那条（Executed=%d）红在：%s" % (arm_id, n, u", ".join(names)))
        else:
            mismatch += 1
            print(u"%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 这一环没有证人" % (arm_id, n))

    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if red or n == 0 or skipped:
            print(u"RESTORE_FAILED %s Executed=%d 红=%s skip=%d" % (filt, n, u", ".join(names), skipped))
            print(u"CAUGHT=%d/%d, RESTORE_CLEAN=no" % (caught, len(arms)))
            return 1
    restored = "yes" if all(read(q) == base for q, base in originals.items()) else "no"
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print(u"RESTORE_FAILED 盘上内容与基线不一致")
    if not_run or mismatch:
        print(u"NOT_RUN=%d MISMATCH=%d ⇒ 这支表不算过关" % (not_run, mismatch))
    return 0 if caught == len(arms) and restored == "yes" and not not_run and not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
