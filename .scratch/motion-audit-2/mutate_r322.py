#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R322 的变异表：三把刀钉的是**胶囊横移那台过程证人**（M922-M924）。

这一轮的主线产出是给一个真实位补上了过程证人：`filter-pill-slide` 第一次把
「全部 / 收藏」那颗胶囊的位移档放进真窗口逐帧取证，本机读数
`开A 帧数=3(旧口径7) 峰值≈0.09 / 关 帧数=1(旧口径1) 峰值=0.354` ⇒ 它看得见，
于是按仓库自己的规矩当场升成硬判据（不许留免责）。

证人写出来不等于有牙。三把刀各拆一环，被拆的那一环必须红在指名它的断言上：

  M922 把量完的带子挪到窗口最顶上（R323 重钉：原来是挪走写死的那条）⇒ 前提必须红
  M923 把 A/B 开关弄坏（关臂其实没关） ⇒ 「开臂中间态帧数必须大于关臂」那条红
  M924 把触发换成 no-op（再选一次当前档） ⇒ 前提红 —— 这一把与 M922 打在**不同代码**上：
       一个坏观察面，一个坏驱动面（同一句"红"必须能分得清是谁坏的）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r322.py [M922 M923 M924]
（这一卷要 `CLIPBOARD_HISTORY_UI_MOTION=1` 才不 skip —— 没设就会得到 PASSED，
  而 PASSED 在这一支表里是**不过关**，不是"没问题"。）
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
FILTER = u"MotionFilmstripTests/testFilterPillSlideIsAProcessNotATeleport"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = u"1"

# ① 带子挪走。**R323 重钉**：原来那根针指着写死的 `CGRect(x: 12/300, y: 66/520, …)`，
# 而 R323 把那条带子改成**从这一卷量**（组件帧上目测的 66…92pt 在真窗口里根本不在胶囊那一行，
# 峰值被低估近三倍：0.097 → 0.277），旧针于是命中 0 次 —— 那是腐烂针，不是坏刀（R245/R262 那一族）。
# 现在把针下在**量完之后交出去的那一步**：y 推到 0.0（窗口最顶上一条绝对静止的带子），
# 「带内一个像素都没变 ⇒ 触发没让胶囊移动」那朵前提必须红。
NEEDLE_922 = u"                      y: CGFloat(band.lowerBound) / CGFloat(a.height),\n"
REPL_922 = u"                      y: 0.0,\n"

# ② A/B 开关坏掉：关臂根本没关 ⇒ 两臂同物，"中间态比关臂多"必须红。
# 多带一行 `onFilmB` 当锚：`animationsEnabled = false` + `let offFilm = record(scenario)`
# 这两行在本文件里出现两次（详情区那条交叉淡同形），单带这两行会命中 2 ⇒ NOT_RUN。
NEEDLE_923 = (u"        let onFilmB = record(scenario)\n"
              u"        MotionCatalog.animationsEnabled = false\n"
              u"        let offFilm = record(scenario)\n")
REPL_923 = (u"        let onFilmB = record(scenario)\n"
            u"        let offFilm = record(scenario)\n")

# ③ 触发换成 no-op：再选一次当前那一档 ⇒ 画面从头到尾不变。
NEEDLE_924 = u"            }) { store in\n                store.perform(.updateFilter(.favorites))\n"
REPL_924 = u"            }) { store in\n                store.perform(.updateFilter(.all))\n"

ARMS = [
    ("M922", u"尺：把观察带挪出胶囊那一行 ⇒ 前提必须红", FILM, NEEDLE_922, REPL_922),
    ("M923", u"尺：关臂其实没关（A/B 开关坏） ⇒ 中间态帧数那条必须红", FILM, NEEDLE_923, REPL_923),
    ("M924", u"尺：触发换成 no-op ⇒ 前提必须红（坏的是驱动面，不是带子）", FILM, NEEDLE_924, REPL_924),
]
TARGETS = sorted({a[2] for a in ARMS})
EXPECTED = u"testFilterPillSlideIsAProcessNotATeleport"


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
        print("PRECHECK_FAILED 这一卷被 skip 了（skipped=%d）⇒ 没设 CLIPBOARD_HISTORY_UI_MOTION=1，"
              "后面的 CAUGHT 都不说明任何事" % skipped)
        return 1
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1
    print("BASELINE_GREEN Executed=%d（过程证人已签）" % n)

    caught = 0
    mismatch = 0
    not_run = 0
    for arm_id, why, target, old, new in arms:
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
        elif red and any(EXPECTED in name for name in names):
            caught += 1
            print("%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:26], n, ", ".join(names)))
        elif red:
            mismatch += 1
            print("%s MISMATCH 红了但不是它那条（Executed=%d）红在：%s" % (arm_id, n, ", ".join(names)))
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
