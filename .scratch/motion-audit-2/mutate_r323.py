#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R323 的变异表：六把刀钉的是**斜坡尺**与它那条出口（M925-M930）。

这一轮的主线产出：全仓唯一那条位移档（`.slider`）第一次有**品质**证人 ——
`MOTION_PILL_RAMP filter-pill-slide A 判定=单调 首=81.0pt 末=219.0pt 位移=138.0pt 最大倒退=0.0pt`。
同一轮里两处自曝都由这里的刀钉住：
① R322 那条观察带是在**另一张帧**上目测的（组件帧 66…92pt，真窗口里胶囊在 49…75pt）；
② 第一版按"哪些行在变"定位行带，本机直接量到 126…520pt（列表整片在变）。
还有一条是 runner 交账逼出来的出口：三臂逐帧差数组**完全相同** ⇒ 那台机器的胶片里开关不可分。

证人写出来不等于有牙。六把刀各拆一环，被拆的那一环必须红在**指名它的用例**上：

  M925 拆掉"洞必须会走"这道闸      ⇒ 停在原处的一行会被当成位移证人
  M926 把药丸档与轨道档翻过来      ⇒ 尺会去量轨道而不是药丸（R333 重钉：本机 轨道 52 / 药丸 70）
  M927 列中位数换成均值            ⇒ 字墨把洞抬起来，中心一路读到字上
  M928 三臂相同少比一遍开臂        ⇒ 出口会把真有差异的一跑洗成绿（最坏的一种自伤）
  M929 回头的容差乘十              ⇒ MC-1 禁止的过冲读不出来
  M930 轨道范围少一根边界列        ⇒ 范围与"首尾两根都算"这件事脱钩

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r323.py [M925 …]
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
FILTER = u"MotionPillRampTests"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

# ① 会走的洞：去掉走量要求 ⇒ 静止的一行也算行带证人。
NEEDLE_925 = u"guard move >= minMoveFraction * width else { return nil }"
REPL_925 = u"guard move >= 0 else { return nil }"
EXPECT_925 = u"testMovingHoleReadingRejectsAHoleThatStaysPut"

# ② 洞的极性：把"与页底同档"换成"与页底不同档" ⇒ 量的是轨道两段的外包，不是胶囊。
# R333 重钉：这一针原来锚的是旧定义那行（`hole` 与页底比），重基之后那颗尺读的是
# `pillLevel`（由两臂镜像量出来），所以针与期望用例名一起换 —— 刀的意思没变：
# 把"哪一档是药丸"翻成"另一档"，证人必须红。
# R356 重钉：`pillRun` 多了 `mergeInk` 分支，旧针已不在盘上；极性翻面这一刀的语义不变。
NEEDLE_926 = u"let isPill = extent.map { abs(profile[$0] - pillLevel) < delta || isInk(profile[$0]) }"
REPL_926 = u"let isPill = extent.map { abs(profile[$0] - pillLevel) >= delta || isInk(profile[$0]) }"
EXPECT_926 = u"testPillRunFollowsTheLevelGivenByTheMirrorNotThePage"

# ③ 列剖面：中位数换成均值 ⇒ 少数行的字墨抬进中心。
NEEDLE_927 = u"out.append(Self.median(col))"
REPL_927 = u"out.append(col.reduce(0.0, +) / Double(max(col.count, 1)))"
EXPECT_927 = u"testColumnMedianProfileIgnoresMinorityGlyphInk"

# ④ 出口：只比一遍开臂 ⇒ 第二遍开臂差异被吞，真红洗成绿。
NEEDLE_928 = u"onA == off && onB == off"
REPL_928 = u"onA == off"
EXPECT_928 = u"testArmsAreIdenticalRequiresEveryArmToMatch"

# ⑤ 回头的容差乘十 ⇒ 过冲看不见。
NEEDLE_929 = u'if worstBack > tolerance { return ("回头", detail) }'
REPL_929 = u'if worstBack > tolerance * 10 { return ("回头", detail) }'
EXPECT_929 = u"testRampVerdictWordsAreFourAndDistinct"

# ⑥ 轨道范围丢掉最后一根边界列（off-by-one）。
NEEDLE_930 = u"return first..<(last + 1)"
REPL_930 = u"return first..<last"
EXPECT_930 = u"testTrackExtentSpansFirstToLastDifferentColumn"

ARMS = [
    ("M925", u"尺：拆掉『洞必须会走』这道闸", FILM, NEEDLE_925, REPL_925, EXPECT_925),
    ("M926", u"尺：把洞的极性翻过来", FILM, NEEDLE_926, REPL_926, EXPECT_926),
    ("M927", u"尺：列中位数换成均值", FILM, NEEDLE_927, REPL_927, EXPECT_927),
    ("M928", u"闸：三臂相同少比一遍开臂（出口洗红）", FILM, NEEDLE_928, REPL_928, EXPECT_928),
    ("M929", u"尺：回头的容差乘十", FILM, NEEDLE_929, REPL_929, EXPECT_929),
    ("M930", u"尺：轨道范围少一根边界列", FILM, NEEDLE_930, REPL_930, EXPECT_930),
]
TARGETS = sorted({a[2] for a in ARMS})


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1) for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    skipped = len(re.findall(r"Test Case '[^']+' skipped", out))
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数）"], out, skipped
    return n, (n >= 1 and failures > 0), names, out, skipped


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）"
              % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print("ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    originals = {path: read(path) for path in TARGETS}
    clock = [time.time() + 10.0]

    def restore():
        for path, base in originals.items():
            save(path, base, bump=clock[0])
        clock[0] += 10.0

    restore()
    n, red, names, out, skipped = run_suite()
    if skipped:
        restore()
        print("PRECHECK_FAILED 这一卷被 skip 了（skipped=%d）⇒ 后面的 CAUGHT 都不说明任何事" % skipped)
        return 1
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1
    print("BASELINE_GREEN Executed=%d（斜坡尺证人全绿）" % n)

    caught = 0
    mismatch = 0
    not_run = 0
    for arm_id, why, target, old, new, expected in arms:
        text = read(target)
        if text.count(old) != 1:
            not_run += 1
            print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:48]))
            continue
        want_text = text.replace(old, new)
        save(target, want_text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != want_text:
            restore()
            not_run += 1
            print("%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out, skipped = run_suite()
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            not_run += 1
            print("%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif skipped:
            not_run += 1
            print("%s NOT_RUN 落刀后这一卷被 skip（skipped=%d）⇒ 不许记成 CAUGHT" % (arm_id, skipped))
        elif "error: " in out and not red:
            not_run += 1
            print("%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and any(expected in name for name in names):
            caught += 1
            print("%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:26], n, ", ".join(names)))
        elif red:
            mismatch += 1
            print("%s MISMATCH 红了但不是它那条（Executed=%d）期望=%s 红在：%s"
                  % (arm_id, n, expected, ", ".join(names)))
        else:
            mismatch += 1
            print("%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 这一环没有证人" % (arm_id, n))

    n, red, names, out, skipped = run_suite()
    restored = "yes" if (not red and n >= 1 and not skipped
                         and all(read(q) == base for q, base in originals.items())) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s skip=%d" % (n, ", ".join(names), skipped))
    if not_run or mismatch:
        print("NOT_RUN=%d MISMATCH=%d ⇒ 这支表不算过关" % (not_run, mismatch))
    return 0 if caught == len(arms) and restored == "yes" and not not_run and not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
