#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R345 的变异表（第 344 轮 / Round 342）：亮档选中那颗的**发丝边**，两把刀各钉一条轴。

R345 落的是一条**换了轴的身份**：亮档选中那颗不再只靠亮度（空闲 230 与选中 220 只差 1.099，
放不下第三个能过 1.20 的档），而是补一根 1pt × 0.12 的发丝边（R344 现读 填充 220 / 最深 198 ⇒ 差 22）。
判据是**次序**不是绝对值：`页面(255) > 填充(220) > 最深(198)`，且"最深那一格不是页面"——R343/R344
三次读错对象（页面 / 轨道 / 边）之后，这一条才把对象钉住（D-341）。

· M1001 边的 alpha 0.12→0.0（边还在、但看不见）⇒ 亮档最深那一格塌回填充 ⇒ 像素判据必须红。
· M1002 暗档也画边（`width(dark:)` 从 nil 改成 1）⇒ 像素判据这一轮不断言暗档（D-341：
  像素级的"暗档没有边"要两臂帧才证得了），红必须落在令牌真值表那一格。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r345.py [M1001 M1002]
（结论只准由 XCTest 的汇总行说；编译不过 = NOT_RUN，不算过关 = D-243。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOB = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                    "Views", "PressableStyle.swift")
TOKENS = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "VisualTokens.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIXEL_CELL = u"UICaptureTests/testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces"
PURE_CELL = u"FilterPillMotionTests/testSegmentEdgeIsLightOnlyAndWithinTheHairlineRange"
CELL = PURE_CELL + u"|" + PIXEL_CELL
# `expect` 用**裸方法名**：失败行打的是 `-[Bundle.Class methodName] : XCTAssert…`，
# 带 `Class/` 前缀的写法在失败行里根本不存在 ⇒ 每一刀都会被判成打空。
PIXEL_RED = u"testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces"
PURE_RED = u"testSegmentEdgeIsLightOnlyAndWithinTheHairlineRange"

NEEDLE_EDGE_ALPHA = u"    static let selectedSegmentEdge: Double = 0.12"
REPL_1001 = u"    static let selectedSegmentEdge: Double = 0.0"

NEEDLE_EDGE_WIDTH = u"    static func width(dark: Bool) -> CGFloat? { dark ? nil : 1 }"
REPL_1002 = u"    static func width(dark: Bool) -> CGFloat? { 1 }"

ARMS = [
    ("M1001", u"产品：边的 alpha 0.12→0.0（还在、看不见）⇒ 亮档最深那一格塌回填充，像素判据必须红",
     TOKENS, NEEDLE_EDGE_ALPHA, REPL_1001, PIXEL_RED, PIXEL_CELL),
    ("M1002", u"契约：暗档也画边（width 从 nil 改成 1）⇒ 令牌真值表必须红",
     KNOB, NEEDLE_EDGE_WIDTH, REPL_1002, PURE_RED, PURE_CELL),
]

SNAPSHOT = {}
_MISSING = object()


def sh(cmd):
    p = subprocess.run(cmd, cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


def read(path):
    with open(path, encoding="utf-8") as h:
        return h.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as h:
        h.write(text)


def red_in(out, name):
    u"""『红在这一格』必须能在**同一行**里同时看到那一格的名字与失败字样。

    只判 `name in out` 会被"这一格跑过并且 passed"喂饱（swift test 两种都打名字），
    于是刀打空也报 CAUGHT —— 与 R262 那三根腐烂针同一族：结果通道本身会坏。
    """
    for line in out.splitlines():
        if name in line and (u"error:" in line or u"' failed" in line):
            return True
    return False


def run_cell(filter_name):
    u"""红不红只准由 XCTest 的汇总行说，不许由「日志里有没有 error: 字样」说：
    产品自己会往 stderr 倒系统噪声（`CoreData: error: …AddressBook…`，本机每次跑都有）。
    """
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", filter_name])
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", out)
    if not executed:
        return (True, u"?", out)   # 一行汇总都没有（单数 `1 test` 也要认） ⇒ 编译没过 / 根本没跑
    n, fails = executed[-1]
    red = int(fails) > 0 or "Test Suite 'Selected tests' failed" in out
    return (red, n, out)


def main(argv):
    picked = [a for a in ARMS if not argv or a[0] in argv]
    if not picked:
        print(u"ARG_ERROR 认不出臂号：" + u" ".join(argv))
        return 2
    print(u"===== 基线（未落刀）")
    baseline_ok = True
    for cell in sorted(set(a[6] for a in picked)):
        red, n, out = run_cell(cell)
        print(u"BASELINE %s %s Executed=%s" % (cell, u"RED" if red else u"green", n))
        if red:
            baseline_ok = False
            print(out[-1500:])
    if not baseline_ok:
        print(u"PRECHECK_FAILED 基线不绿，这一轮的 CAUGHT 一律不作数")
        return 1

    caught = 0
    last_mtime = 0
    for a in ARMS:
        SNAPSHOT.setdefault(a[2], read(a[2]))
    for arm, desc, path, needle, repl, expect, cell in picked:
        text = read(path)
        hits = text.count(needle)
        if hits != 1:
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm, hits, path))
            continue
        write(path, text.replace(needle, repl))
        if read(path).count(repl) != 1:
            print(u"%s NOT_RUN 落刀后回读不匹配" % arm)
            write(path, text)
            continue
        stamp = os.path.getmtime(path)
        if stamp <= last_mtime:
            os.utime(path, (time.time() + 2, time.time() + 2))
        last_mtime = os.path.getmtime(path)
        red, n, out = run_cell(cell)
        if n == u"?":
            print(u"%s NOT_RUN 变异之后编译不过：%s" % (arm, out.strip().splitlines()[-1][:160]))
            write(path, text)
            continue
        ok = red and red_in(out, expect)
        if ok:
            caught += 1
            print(u"%s CAUGHT %s（Executed=%s）红在：%s" % (arm, desc, n, expect))
        else:
            print(u"%s %s %s —— 期望红在 %s，实得 Executed=%s"
                  % (arm, u"MISMATCH" if red else u"PASSED", desc, expect, n))
            print(out[-1200:])
        write(path, text)
        if read(path) != text:
            print(u"%s RESTORE_DIRTY 还原没回到原文" % arm)
            return 1

    clean = all(read(a[2]) == SNAPSHOT.get(a[2], _MISSING) for a in ARMS)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(picked), u"yes" if clean else u"no"))
    if caught == len(picked) and clean:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
