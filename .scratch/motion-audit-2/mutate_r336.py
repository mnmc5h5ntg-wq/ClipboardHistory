#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 的变异表：三把刀钉「图被撤之后，说明文字必须留下」这一族（M984…M986）。

R336 做的事：BACKLOG 402 用一次现读关掉（Markdown 那条通道的耗时 = 固定 13ms + 边际 0.047ms/KB，
在存档自己允许的最大条目上是 36ms，远在 250ms 预算内 ⇒ **不需要**字节上限，
而"不需要"从今天起是有数的判断，不是没证据的默认）；BACKLOG 401 落地成产品修法 ——
`<img>` 被消毒撤掉之后，它自己的 `alt` 文字必须留在正文里，而**空 alt / 没有 alt 的必须静默消失**。
三条各配一把刀，因为三种坏法在屏幕上长得都不一样：

  M984 产品：不换成 alt（回到"整块删"）        ⇒ 有 alt 那一格必须红
  M985 产品：alt 里的尖括号不剥                ⇒ "属性爬回文档"那一格必须红
  M986 产品：空 alt 也写一句占位文字           ⇒ 装饰图/埋点像素那一半必须红
  M987 产品：永远包成 <p>                      ⇒ 句中那张图必须红（一句话被劈成三段）
  M988 产品：永远不包段（R336 上半场那一版）    ⇒ 独占一行那一半必须红

后两把是下半场（规则 ④：说明要**自成一段**）的两侧 —— 只钉一侧的话，另一侧的坏法
在屏幕上长得完全相反却没人拦（现读：不包段 ⇒ alt 与下一段挤成同一行节奏，20.0 对 31.5）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r336.py [M984 … M988]
（五把都打在 Sources 的消毒器上，一格判据卷。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
SANITIZER = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                         "Utilities", "HtmlPreview.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIPE_CELL = u"HtmlPreviewPolicyTests|HtmlSanitizerTests|HtmlPreviewPipelineTests"
ALT_CELL_NAME = u"testImageAltTextSurvivesWhileTheImageItselfDoesNot"

NEEDLE_984 = u"        s = imagesReplacedWithAlt(s)"
REPL_984 = u'''        // 变异：不换成 alt，回到 R335 那一版「整块删」'''

NEEDLE_985 = u'let cleaned = raw.unicodeScalars.filter { $0 != "<" && $0 != ">" }'
REPL_985 = u'let cleaned = raw.unicodeScalars.filter { _ in true }'

NEEDLE_986 = u"            guard !cleaned.isEmpty else { continue }   // 装饰图 / 埋点像素：整块删"
REPL_986 = u'''            guard !cleaned.isEmpty else { out += "图片"; continue }'''

# R336 下半场（规则 ④：那句说明要**自成一段**）。两把刀打在同一个判据上，
# 因为这一条的两半在屏幕上是相反的两种坏法 —— 只钉一半，另一半就会漂过去。
NEEDLE_987 = u'            out += isStandaloneBlock(ns, at: m.range) ? "<p>" + cleaned + "</p>" : cleaned'
REPL_987 = u'            out += "<p>" + cleaned + "</p>"'

NEEDLE_988 = u"        return tailSlice.allSatisfy(\\.isWhitespace)"
REPL_988 = u"        return false   // 变异：永远算句中 ⇒ 独占一行的图也不给段前距"

ALT_BLOCK_CELL = u"testStandaloneImageBecomesItsOwnParagraphWhileInlineImageStaysInline"

ARMS = [
    ("M984", u"产品：<img> 不换成 alt ⇒ 「有 alt 的那句必须留」必须红", SANITIZER,
     NEEDLE_984, REPL_984, ALT_CELL_NAME, PIPE_CELL),
    ("M985", u"产品：alt 里的尖括号不剥 ⇒ 「属性爬回文档」那一格必须红", SANITIZER,
     NEEDLE_985, REPL_985, ALT_CELL_NAME, PIPE_CELL),
    ("M986", u"产品：空 alt 也写占位文字 ⇒ 装饰图/埋点像素那一半必须红", SANITIZER,
     NEEDLE_986, REPL_986, ALT_CELL_NAME, PIPE_CELL),
    ("M987", u"产品：永远包成 <p> ⇒ 句中那张图必须红（一句话被劈成三段）", SANITIZER,
     NEEDLE_987, REPL_987, ALT_BLOCK_CELL, PIPE_CELL),
    ("M988", u"产品：永远不包段（回到 R336 上半场）⇒ 独占一行那一半必须红", SANITIZER,
     NEEDLE_988, REPL_988, ALT_BLOCK_CELL, PIPE_CELL),
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


def run_cell(filter_name):
    """红不红只准由 **XCTest 的汇总行**说，不许由"日志里有没有 error: 字样"说。

    第一版就是那么判的，于是基线被判成 RED 而 17 格全绿 —— 成因是产品自己会往
    stderr 倒系统噪声（`CoreData: error: …AddressBook…`，本机每次跑都有）。
    这一族有名字：**结果通道本身会坏**（读到的字符串不等于结论）。
    """
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", filter_name])
    executed = re.findall(r"Executed (\d+) tests, with (\d+) failures", out)
    if not executed:
        return (True, "?", out)                      # 一行汇总都没有 ⇒ 编译没过 / 根本没跑
    n, fails = executed[-1]
    red = int(fails) > 0 or "Test Suite 'Selected tests' failed" in out
    return (red, n, out)


def main(argv):
    picked = [a for a in ARMS if not argv or a[0] in argv]
    if not picked:
        print(u"ARG_ERROR 认不出臂号：" + u" ".join(argv))
        return 2
    # 基线不绿 ⇒ 后面每一朵 CAUGHT 都不说明任何事（先量地板，再落刀）。
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
        # 回读磁盘自证：落下去的就是这一刀（改了又被换回去 ⇒ NOT_RUN，不许记 CAUGHT）
        if read(path).count(repl) != 1:
            print(u"%s NOT_RUN 落刀后回读不匹配" % arm)
            write(path, text)
            continue
        # mtime 必须**严格递增**：同长度变异 + 同一秒还原，工具链会继续执行旧字节码。
        stamp = os.path.getmtime(path)
        if stamp <= last_mtime:
            os.utime(path, (time.time() + 2, time.time() + 2))
        last_mtime = os.path.getmtime(path)
        red, n, out = run_cell(cell)
        if n == u"?":
            # 编译不过 ⇒ 这一刀本身坏了（不是判据没牙）。记 NOT_RUN，绝不记 CAUGHT。
            print(u"%s NOT_RUN 变异之后编译不过：%s" % (arm, out.strip().splitlines()[-1][:160]))
            write(path, text)
            continue
        ok = red and (expect in out)
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

    # 还原干不干净 = **与落刀前那份快照逐字相等**。
    # 第一版判的是"needle 还在、repl 不在"，而 M974 的 repl 是 needle 的一部分
    # （删一行 ⇒ 剩下那行仍然含 repl）⇒ 它把一次干净的还原报成 RESTORE_CLEAN=no。
    clean = all(read(a[2]) == SNAPSHOT.get(a[2], _MISSING) for a in ARMS)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(picked), u"yes" if clean else u"no"))
    if caught == len(picked) and clean:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
