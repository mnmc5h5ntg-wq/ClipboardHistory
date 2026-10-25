#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R140 的变异表：八格新证据 + 「生成器产物 == 已提交表」这道守卫的牙（M657-M659）。

三把刀都对准本轮真实发生过的失效形状，不是凭空造的错法：

  M657 把 QuickPickController 那条**缺席断言**的 token 从 `disabled` 改成 `emptyLabel`
       ⇒ 那个词就在文件里（本轮实测 15 命中），闸门必须报 ABSENT_CLAIM_FALSE。
       这一把证明新行里的「缺席」是**可证伪的**，不是装饰。
  M658 把 SettingsView 那条指针改回 `% SV` 外部变量写法 —— 本轮真的栽过一次
       （生成器语法正确、`ast.parse` 通过，运行时 `NameError: name 'SV' is not defined`）
       ⇒ 生成器非零退出，「生成器产物 == 已提交表」必须红。
  M659 把「主窗口/侧栏 × 选中」的表面名改成名册外的词
       ⇒ 生成器产物与已提交表不再逐字节相同，且闸门 UNKNOWN_CELL 必须红。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r140.py [M657 ...]
退出码：0 = 该下的刀都下了；1 = 有刀等于没下（PASSED）或还原后仍红。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GEN = os.path.join(ROOT, ".scratch/motion-audit-2", "make_surface_ledger.py")
TABLE = os.path.join(ROOT, "docs", "motion_surface_ledger.json")
MODULES = ("test_ledger_generator_output.py", "test_motion_surface_gate.py")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

QP = "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
SV = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"

ARMS = [
    # R381：M657/M658 原来的针写成 `u"缺席:%s=disabled" % QP` / `… % SV`，静态尺只看得见
    # 左边的模板（`缺席:%s=disabled`），于是两根**活**针被报成 rot。改成字面整串，语义不变。
    ("M657", TABLE,
     u"缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=disabled",
     u"缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=emptyLabel", "CAUGHT"),
    ("M658", GEN,
     u'"Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `SettingsCategory`（allCases 常量）"',
     u'"Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `SettingsCategory`（allCases 常量）" % SV', "CAUGHT"),
    ("M659", GEN,
     u'("主窗口/侧栏", "选中", "kept",',
     u'("主窗口/侧栏列", "选中", "kept",', "CAUGHT"),
]


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text):
    open(path, "w", encoding="utf-8").write(text)


def run_module(name):
    """跑一个测试模块，返回 (跑了几个, 是否红)。

    红必须是 `Ran >= 1 且 FAILED` —— 收集期崩掉（Ran 0）不算红，那是探针坏了（U-442 那一族）。
    """
    proc = subprocess.run(["python3", "-m", "unittest", "discover",
                           "-s", "scripts/tests", "-p", name],
                          cwd=ROOT, env=dict(ENV, PYTHONUTF8="1"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    ran = re.search(r"Ran (\d+) tests?", out)
    n = int(ran.group(1)) if ran else 0
    return n, (n >= 1 and "FAILED" in out)


def baseline_ran():
    """两个模块都要真的跑到用例（Ran >= 1）。"""
    return all(run_module(name)[0] >= 1 for name in MODULES)


def reds():
    hit = []
    for name in MODULES:
        n, is_red = run_module(name)
        if is_red:
            hit.append("%s(Ran %d)" % (name, n))
    return hit


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        # 打错一个臂号就会得到 `CAUGHT=0/0, RESTORE_CLEAN=yes` 与退出码 0 ——
        # 一把刀都没下也算过关（R143 审查轮 #1）。未知名字必须是硬错。
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）" % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print("ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    originals = {p: read(p) for p in (GEN, TABLE)}
    # 预检必须也认"一条都没跑"：`Ran 0 tests / OK` 是这道门自己坏掉的形状（BACKLOG 121 那一族）。
    if reds() or not baseline_ran():
        for p, text in originals.items():
            save(p, text)
        print("PRECHECK_FAILED 未落刀时已经红 ⇒ 后面的 CAUGHT 不说明任何事")
        return 1

    caught = 0
    for arm_id, target, old, new, expect in arms:
        text = read(target)
        hits = text.count(old)
        if hits != 1:
            print("%s NOT_RUN 锚点命中 %d 次（要 1 次）—— 刀没下，不许记成 CAUGHT" % (arm_id, hits))
            continue
        save(target, text.replace(old, new))
        hit = reds()
        for p, base in originals.items():
            save(p, base)
        if hit and expect == "CAUGHT":
            caught += 1
            print("%s CAUGHT 红在：%s" % (arm_id, ", ".join(hit)))
        elif hit:
            print("%s OVERRED 不该红的也红了：%s" % (arm_id, ", ".join(hit)))
        else:
            print("%s PASSED 刀等于没下（两模块都绿）" % arm_id)

    clean = reds()
    restored = "yes" if not clean and read(TABLE) == originals[TABLE] and read(GEN) == originals[GEN] else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED 红在：%s" % ", ".join(clean))
    return 0 if caught == len(arms) and restored == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
