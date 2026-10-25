#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R338 的变异表（第 337 轮 / Round 335）：取 alt 那一步的三条规矩，各钉一把。

R338 修的是 R337 复盘时从源码读出来、今天用产品入口量到的那条形状：
`altAttr` 用 `\\balt\\s*=` 在整段标签里搜，而 ICU 的词边界把 `data-alt` 里那个 `alt`
也算起点 ⇒ `<img data-alt="埋点属性写的假说明" alt="季度趋势图（图片未加载）">`
在屏幕上留下的是**埋点属性**那句话。现读（改前）：
`HTML_ALT_SOURCE 前缀属性没抢=false …`，改后 5 颗全 true；
真帧现读 改前/改后 渲染态 alt 那一行（y 460..488px）变了 1173（暗）/1112（亮）个采样点。

三把刀打在**同一格的三条不同轴**上（只钉一条，另外两条就会漂）：

· M993 名字整段相等 ⇒ 改成 `hasSuffix("alt")`：`data-alt` 又能冒充 ⇒ 「前缀属性没抢」必须红。
· M994 重复属性取第一个 ⇒ 改成倒序扫：HTML 里"第一个作数"被反判 ⇒ 「重复取第一个」必须红。
· M995 双引号/单引号两支都要认 ⇒ 只看双引号那一支：单引号 alt 被当成没有值 ⇒ 「单引号认」必须红。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r338.py [M993 … M995]
（结论只准由 XCTest 的汇总行说；编译不过 = NOT_RUN，不算过关 = D-243。）
"""
import io
import os
import re
import subprocess
import sys
import time

from readback import single_substitution_lands

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SANITIZER = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                         "Utilities", "HtmlPreview.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIPE_CELL = u"HtmlPreviewPolicyTests|HtmlSanitizerTests|HtmlPreviewPipelineTests"
ALT_SOURCE_CELL = u"testAltIsTakenFromTheTagsOwnAttributeNotFromAPrefixedNameOrAnotherValue"

NEEDLE_993 = u'                  ns.substring(with: nameRange).lowercased() == "alt" else { continue }'
REPL_993 = u'                  ns.substring(with: nameRange).lowercased().hasSuffix("alt") else { continue }'

NEEDLE_994 = u"        for m in attrs.matches(in: tag, range: NSRange(location: 0, length: ns.length)) {"
REPL_994 = u"        for m in attrs.matches(in: tag, range: NSRange(location: 0, length: ns.length)).reversed() {"

NEEDLE_995 = u"            let valueRange = m.range(at: 2).location != NSNotFound ? m.range(at: 2) : m.range(at: 3)"
REPL_995 = u"            let valueRange = m.range(at: 2)"

ARMS = [
    ("M993", u"产品：属性名允许后缀匹配 ⇒ data-alt 又能冒充 alt，那一格必须红", SANITIZER,
     NEEDLE_993, REPL_993, ALT_SOURCE_CELL, PIPE_CELL),
    ("M994", u"产品：重复 alt 改成最后一个作数 ⇒ 与规范相反，那一格必须红", SANITIZER,
     NEEDLE_994, REPL_994, ALT_SOURCE_CELL, PIPE_CELL),
    ("M995", u"产品：只认双引号那支 ⇒ 单引号 alt 被当成没有值，那一格必须红", SANITIZER,
     NEEDLE_995, REPL_995, ALT_SOURCE_CELL, PIPE_CELL),
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
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", out)
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
        if not single_substitution_lands(text, needle, repl, read(path)):  # R364 / 426：diff 判法
            print(u"%s NOT_RUN 落刀后回读与预期 diff 不一致" % arm)
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
