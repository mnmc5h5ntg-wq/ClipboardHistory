#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R109 的变异表：菜单栏表面的"身份"与 162 的逐列读数各要有牙（M594 / M595 / M596 / M597）。

本轮做的两件事：
  ① 把"菜单栏这里不可能有动画"那句理由的前提**写成代码**（`.menuBarExtraStyle(.menu)`），
     并加一条源码守卫 `testMenuBarSurfaceIdentityIsDeclaredNotInherited`。
     起因：本轮逐元素重判菜单栏时读到，那句理由引用的样式**从来没被显式设置过**，
     而旁边那条守卫数的是文件里有没有 `animation(` ⇒ 理由失效与守卫变绿可以同时成立（R74 那一族）。
  ② 给臂 2 装上**逐列**的墨读数 `CARD_PROBE_COLUMNS`（含推导出来的"详情(外列−侧栏)"），
     配一条尺自检：带子必须与详情列有交集（D-174③ 的形状：红的时候说的是仪器坏了）。
     这是 162 的仪器 —— runner 那一跑用它分开"详情没实例化"与"带子又放错"。

四刀的期望都来自**当轮实测**：
  M594 删掉显式样式 ⇒ CAUGHT（守卫"样式必须是声明的"红）。
  M595 换成 `.window` ⇒ CAUGHT（不是 .menu，且那句理由当场失效）。
  M596 把臂 2 的带子整个挪进侧栏（x=20 宽 60）⇒ CAUGHT（红在尺自检那条交集上）。
  M597 把 `CARD_PROBE_COLUMNS` 改成不存在的 TAG ⇒ 本机 **PASSED（按实登记）**：
       纯读数、本机没有断言读它的名字，牙在 runner 上（与 M570 / M583 / M586 / M588 同规则）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r109.py [M594 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
APP = "Sources/ClipboardHistoryApp/App.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

GUARD = "MotionFilmstripTests/testMenuBarSurfaceIdentityIsDeclaredNotInherited"
LADDER = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
TARGETS = (GUARD, LADDER)

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M594", "删掉显式的 .menuBarExtraStyle(.menu) ⇒ 理由回到默认值上，守卫必须红", APP,
     '            .menuBarExtraStyle(.menu)',
     '            // M594：故意不声明样式（回到依赖默认值）',
     GUARD, "CAUGHT"),
    ("M595", "换成 .menuBarExtraStyle(.window) ⇒ 那时过渡会执行，守卫必须红", APP,
     '            .menuBarExtraStyle(.menu)',
     '            .menuBarExtraStyle(.window)',
     GUARD, "CAUGHT"),
    ("M596", "臂 2 的带子整个挪进侧栏 ⇒ 尺自检（带子∩详情列>0）必须红", HARNESS,
     '        "cardprobe-split-groupbox": CGRect(x: 170, y: 24, width: 550, height: 260),',
     '        "cardprobe-split-groupbox": CGRect(x: 20, y: 24, width: 60, height: 260),',
     LADDER, "CAUGHT"),
    ("M597", "把逐列读数的 TAG 改成不存在的名字 ⇒ 本机按实登记为无判别力（牙在 runner 人读那几行）", HARNESS,
     '                    emit("CARD_PROBE_COLUMNS \\(fixture.name) \\(tag) "',
     '                    emit("CARD_PROBE_COLUMNZ \\(fixture.name) \\(tag) "',
     LADDER, "PASSED"),
]


def path_of(rel):
    return os.path.join(ROOT, rel)


def read(rel):
    return open(path_of(rel), encoding="utf-8").read()


def write(rel, text):
    open(path_of(rel), "w", encoding="utf-8").write(text)


def run(target):
    r = subprocess.run(["swift", "test", "--filter", target], cwd=ROOT, env=dict(BASE_ENV),
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "Executed 0 tests" in out:
        return "DID-NOT-RUN", out
    if "' failed" in out:
        return "CAUGHT", out
    if "with 0 failures" in out and "Executed 1 test" in out:
        return "PASSED", out
    if "skipped" in out:
        return "SKIPPED", out
    return "DID-NOT-RUN", out


def main():
    originals = {rel: read(rel) for rel in (APP, HARNESS)}
    print("=== 预检（不注入：两目标都必须是 PASSED）===")
    bad = 0
    for target in TARGETS:
        verdict, _ = run(target)
        print("  %-70s %s" % (target, verdict))
        if verdict != "PASSED":
            bad += 1
    if bad:
        print("PREFLIGHT_FAILED：干净树上目标不是绿的，变异表无从判起（先修判据/夹具）")
        return 1
    wanted = sys.argv[1:]
    results = []
    for name, note, rel, needle, replacement, target, expect in ARMS:
        if wanted and name not in wanted:
            continue
        text = originals[rel]
        hits = text.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, hits))
            results.append((name, expect, "DID-NOT-RUN", note,
                            "needle 命中 %d，每处期望 1 ⇒ 不注入" % hits))
            continue
        write(rel, text.replace(needle, replacement, 1))
        verdict, out = run(target)
        write(rel, originals[rel])
        snippet = ""
        for line in out.splitlines():
            if "error:" in line and "XCTAssert" in line:
                snippet = line.strip()[:150]
                break
        ok = verdict == expect
        results.append((name, expect, verdict, note,
                        ("对  期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s %s" % (name, verdict, note, results[-1][4]))
    restored = "yes"
    for rel in (APP, HARNESS):
        if read(rel) != originals[rel]:
            write(rel, originals[rel])
            restored = "二次还原仍不干净"
    mismatch = sum(1 for r in results if r[1] != r[2])
    not_run = sum(1 for r in results if r[2] == "DID-NOT-RUN")
    caught = sum(1 for r in results if r[2] == "CAUGHT")
    print("\n=== R109 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), caught, mismatch, not_run))
    return 0 if (results and mismatch == 0 and restored == "yes") else 1


if __name__ == "__main__":
    sys.exit(main())
