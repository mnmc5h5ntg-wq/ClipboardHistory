#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R325 的变异表：六把刀钉的是**色档依赖探针 + 出口谓词 + 退化采样**（M937…M942）。

本轮的产出是把 BACKLOG 383 从"缺席计数"变成"逐颗读数"：12 颗没钉色档的胶片场景，
每颗在暗档与亮档里各拍一卷，比它自己那把尺的读数，归成四格词表
（同 / 漂 / 敏感 / 换对象）。本机现读 `场景=12 同=9 漂=3 敏感=0 换对象=0`
⇒ "其余场景不钉色档"这句话第一次有数，而不是猜。

读数要能红才有意义。四把刀各拆一环：

  M937 让 `pinned(to:)` 变成 no-op（请求的档位没落进场景） ⇒ 两臂通道前提必须红
       （这条与机器当前档位无关：两臂变成同一件事，至多一臂能对上自己的期望）
  M938 把"敏感"那条线推到永远够不到（>1000）              ⇒ 分类器证人必须红
  M939 从对象表里删掉一颗场景                              ⇒ 对象表与点名器的对账必须红
       （漏掉的那颗正是"我们以为量过了"的那颗 —— 这一刀拦的是探针静默少覆盖）
  M940 把"换对象"的判据写成两臂都看得见变化                ⇒ 分类器证人必须红
  M941 出口谓词丢掉"峰值全等"那一半                        ⇒ 合成证人必须红
       （这一刀的形状就是 RUN=40053805112 上真实发生过的漏放行：三臂帧数全等而峰值不同也算有对照物）
  M942 中间样本把端点也算进去                              ⇒ 退化采样证人必须红
       （斜坡尺不许给一步跳变发"走得平稳"的证）
       （M938 与 M940 打在**同一个纯函数**的不同分支上：同一句"红"分得清是谁坏的）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r325.py [M937 … M942]
（M937/M939 那一臂要 `CLIPBOARD_HISTORY_UI_MOTION=1` —— 没设就得到 skip，
 而 skip 在这一支表里是 NOT_RUN，不是过关。）
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

# ① pinned 变 no-op：请求的档位没进场景 ⇒ 两臂拍成同一档。
NEEDLE_937 = u"                     appearance: appearance, root: root, storeFactory: storeFactory,\n"
REPL_937 = u"                     appearance: self.appearance, root: root, storeFactory: storeFactory,\n"

# ② "敏感"那条线推到永远够不到。
NEEDLE_938 = u'        if rel > 0.25 { return "敏感" }\n'
REPL_938 = u'        if rel > 1000 { return "敏感" }\n'

# ③ 对象表少一颗：探针会静默漏覆盖，而汇总行仍然打"场景=11"。
NEEDLE_939 = u'             ("emptyState", emptyState()),\n'
REPL_939 = u""

# ④ "换对象"写成两臂都看得见变化 ⇒ 这一格永远不响。
NEEDLE_940 = u'        if changedDark != changedLight { return "换对象" }\n'
REPL_940 = u'        if changedDark && changedLight { return "换对象" }\n'

# ⑤ 出口谓词丢掉"峰值全等"那一半 ⇒ 合成证人必须红（这就是 runner 那一跑漏放行朵红的形状）。
NEEDLE_941 = u"        spanA == spanB && spanB == spanOff && peakA == peakB && peakB == peakOff\n"
REPL_941 = u"        spanA == spanB && spanB == spanOff\n"

# ⑥ 中间样本数把端点也算进去 ⇒ 一步跳变会被数成"有斜坡"，证人必须红。
NEEDLE_942 = u"        return centers.filter { $0 > lo + tolerance && $0 < hi - tolerance }.count\n"
REPL_942 = u"        return centers.filter { $0 >= lo && $0 <= hi }.count\n"

ARMS = [
    ("M937", u"尺：pinned(to:) 变 no-op ⇒ 两臂通道前提必须红", FILM,
     NEEDLE_937, REPL_937, PROBE_TEST, PROBE),
    ("M938", u"尺：敏感那条线推到 >1000 ⇒ 分类器证人必须红", FILM,
     NEEDLE_938, REPL_938, CLASSIFY_TEST, PURE),
    ("M939", u"尺：对象表删一颗 ⇒ 与点名器的对账必须红", FILM,
     NEEDLE_939, REPL_939, PROBE_TEST, PROBE),
    ("M940", u"尺：换对象那一格永远不响 ⇒ 分类器证人必须红", FILM,
     NEEDLE_940, REPL_940, CLASSIFY_TEST, PURE),
    ("M941", u"尺：出口谓词丢掉峰值全等 ⇒ runner 那种形状会漏放行，证人必须红", FILM,
     NEEDLE_941, REPL_941, u"testArmsIndistinguishableUsesTheNumbersTheJudgeActuallyCompares", PURE),
    ("M942", u"尺：中间样本把端点算进去 ⇒ 一步跳变被发「有斜坡」的证，证人必须红", FILM,
     NEEDLE_942, REPL_942, u"testIntermediateCountRefusesToCertifyATeleport", PURE),
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
            print(u"%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:30], n, u", ".join(names)))
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
