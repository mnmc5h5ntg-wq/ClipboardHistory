# -*- coding: utf-8 -*-
"""R593 / 靶 4：读数行必须坐在会崩的门**之前** —— 把这条纪律做成扫描器。

来历（本轮自己撞的）：`test_skip_roster` 的 `SKIP_ROSTER 键=…` 那行印在 `inner-red` 那一支的
`self.fail()` 之后 ⇒ 在 runner 上内层一红，这一格连一行都不印（`42210166309` 实测该行出现 **0 次**），
于是"这一维今天有没有人判"只剩猜。R589 已经记过一次同族（守卫只在测试里被调用 ⇒ CI 没有读数行），
那次写在 ⑨ 里，这次做成仪器：**谁把读数印在门后面，扫描就点谁**。

判法：对名册里登记的每一处（文件、函数、通道 token），取函数体，找**第一条**印出该 token 的
`print(` / `emit(` 行的行号，与函数体里第一条会崩的门（`self.fail(` / `self.skipTest(` /
`raise SystemExit(` / `return` 之前的 fail 支）比行号。三种结论：
  · `ok`        —— 读数行在所有门之前；
  · `red`       —— 有门在读数行之前（那一格在红的时候不会出声）；
  · `not-found` —— 名册里的 token 在该函数里根本找不到 ⇒ 这本身就是红（不许把"我没找到"读成"没问题"）。

名册（`ROSTER`）只登记**已经知道必须出声**的那几处，新增一处就要加一行；加行的成本远低于
"runner 上那一格今天到底有没有印"只能靠猜。

用法：python3 scripts/reading_order_scan.py [--repo-root PATH]
退出码：0=全部 ok；1=有 red/not-found；2=名册为空或扫不到文件（没对象不算判过）。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GATES = (u"self.fail(", u"self.skipTest(", u"raise SystemExit(", u"sys.exit(1)")

# (相对路径, 函数名, 读数 token)。函数名按 `def <name>(` 找，token 按**同一行**里出现算。
# 每行是 (相对路径, 函数名, 读数 token, 允许在读数之前的门)。
# `allow` 里每一条都必须**在这一行之前真的找得到**，找不到就是陈旧豁免 ⇒ 红（R565：
# 豁免理由里写了退场不等于退场会发生）。今天只有一处合法的前置门：`test_skip_roster` 最开头
# 那道防递归 skip —— 它跳的是"别再往下跑一层"，不是"这一维没读数"，所以它可以在印之前。
ROSTER = (
    (os.path.join("scripts", "tests", "test_skip_roster.py"),
     u"test_the_roster_matches_what_this_machine_actually_skips", u"SKIP_ROSTER 键=",
     ((u"self.skipTest(", u"嵌套防递归：这一格是被观察的那一卷的一部分"),)),
    (os.path.join("scripts", "frame_geometry_blind.py"), u"selfcheck", u"READER_SELFTEST=", ()),
    (os.path.join("scripts", "ledger_preflight.py"), u"selfcheck",
     u"LEDGER_PREFLIGHT_READER_SELFTEST=", ()),
    (os.path.join("scripts", "repo_root_bundle.py"), u"main", u"READER_SELFTEST=", ()),
)


def read(path):
    with io.open(path, encoding=u"utf-8", errors=u"replace") as handle:
        return handle.read()


def function_body(text, name):
    """按 `def name(` 取到下一个同缩进的 `def ` / 文件尾。缩进按那一行的实际缩进算，不猜。"""
    m = re.search(r"^([ \t]*)def %s\(" % re.escape(name), text, re.M)
    if not m:
        return None, None
    indent = m.group(1)
    start = m.end()
    nxt = re.search(r"^%s(def |class |@)" % re.escape(indent), text[start:], re.M)
    body = text[start:start + nxt.start()] if nxt else text[start:]
    return text[:m.start()].count("\n") + 1, body


def judge_one(path, name, token, allow=()):
    text = read(path)
    line, body = function_body(text, name)
    if body is None:
        return u"not-found", u"%s::%s 这个函数根本找不到 ⇒ token %r 无从谈起" % (path, name, token)
    body_lines = body.split(u"\n")
    emit_at = None
    for i, l in enumerate(body_lines):
        if (u"print(" in l or u"emit(" in l or u".fail(" in l) and token in l:
            emit_at = i
            break
    if emit_at is None:
        # 允许跨行：`print(` 在上一行、token 在参数行 —— 那就找 token 行，再看它之前有没有 print(。
        for i, l in enumerate(body_lines):
            if token in l:
                emit_at = i
                break
    if emit_at is None:
        return u"not-found", u"%s::%s 里没有印 %r 的那一行 ⇒ 名册过期或函数被改名" % (path, name, token)
    def allowed(line):
        return any(head in line and reason in line for head, reason in allow)
    gate_at = None
    for i in range(emit_at):
        if any(g in body_lines[i] for g in GATES) and not allowed(body_lines[i]):
            gate_at = i
            break
    # 陈旧豁免要响：登记了"这条门允许在读数之前"，而函数里那条门实际不在之前（被删了或被挪走了）
    # ⇒ 这一格红。否则豁免会像 R565 那条说的那样，慢慢变成一张永久通行证。
    for head, reason in allow:
        where = [i for i in range(len(body_lines)) if head in body_lines[i] and reason in body_lines[i]]
        if not where:
            return u"red", (u"%s::%s 登记的允许门（%s / %s）在函数里找不到 ⇒ 陈旧豁免"
                            % (os.path.basename(path), name, head, reason))
        if min(where) > emit_at:
            return u"red", (u"%s::%s 登记的允许门现在坐在读数行**之后** ⇒ 那条豁免的前提没了，"
                            u"要么删登记要么把读数挪到它前面" % (os.path.basename(path), name))
    if gate_at is not None:
        return u"red", (u"%s::%s 第 %d 行有门（%s）在读数行之前 ⇒ 那一格红的时候不会出声"
                        % (os.path.basename(path), name, line + gate_at + 1,
                           body_lines[gate_at].strip()[:60]))
    return u"ok", u"%s::%s 读数行在门之前（偏移 %d）" % (os.path.basename(path), name, emit_at)


def selfcheck(root):
    """合成一份"门在读数之前"的函数，必须被读成 red；再合成一份正确的，必须 ok。

    少了这一步，`red=0` 就只是"我的正则没找到任何东西"的另一种说法（R590 那一族：扫描面 0 不算数）。
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix=u"reading-order-")
    bad = os.path.join(tmp, u"bad.py")
    io.open(bad, u"w", encoding=u"utf-8").write(
        u"class T:\n"
        u"    def one(self):\n"
        u"        self.fail('boom')\n"
        u"        print('TOKEN_X=1 后面才印')\n")
    good = os.path.join(tmp, u"good.py")
    io.open(good, u"w", encoding=u"utf-8").write(
        u"class T:\n"
        u"    def one(self):\n"
        u"        print('TOKEN_X=1 先印')\n"
        u"        self.fail('boom')\n")
    rc_bad, _ = judge_one(bad, u"one", u"TOKEN_X=")
    rc_good, _ = judge_one(good, u"one", u"TOKEN_X=")
    missing, _ = judge_one(good, u"nope", u"TOKEN_X=")
    # 第四把：豁免过期（登记了一条允许的门，而那条门在函数里不存在）也必须红。
    # 登记的门在函数里**根本不存在** ⇒ 红（陈旧豁免的第一种）
    stale, _ = judge_one(good, u"one", u"TOKEN_X=", ((u"self.skipTest(", u"防递归"),))
    # 第二种：那条门存在，却坐在读数行**之后** ⇒ 也要红。少了这一把合成样本，M1609 那把刀落下来
    # 撞的是前一支（`not where`），第二支被摘掉也没人响 —— 本轮第一次就是这么发现空刀的。
    after = os.path.join(os.path.dirname(bad), u"after.py")
    io.open(after, u"w", encoding=u"utf-8").write(
        u"class T:\n"
        u"    def one(self):\n"
        u"        print('TOKEN_X=1 先印')\n"
        u"        self.skipTest('嵌套防递归：这一格是被观察的那一卷的一部分')\n")
    stale_after, _ = judge_one(after, u"one", u"TOKEN_X=",
                               ((u"self.skipTest(", u"嵌套防递归"),))
    ok = (rc_bad == u"red" and rc_good == u"ok" and missing == u"not-found"
          and stale == u"red" and stale_after == u"red")
    print(u"READING_ORDER_SELFTEST=%s 坏形状=%s 好形状=%s 找不到函数=%s 陈旧豁免=%s 豁免在读数之后=%s"
          % (u"seen" if ok else u"blind", rc_bad, rc_good, missing, stale, stale_after))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--repo-root", default=REPO)
    args = ap.parse_args()
    if not ROSTER:
        print(u"READING_ORDER_RESULT=not-run 原因=名册是空的 ⇒ 这一维没人登记，等于没人判")
        return 2
    if not selfcheck(args.repo_root):
        print(u"READING_ORDER_RESULT=red 原因=尺瞎了（合成坏形状没被读成 red）")
        return 1
    bad, rows = 0, []
    for rel, name, token, allow in ROSTER:
        path = os.path.join(args.repo_root, rel)
        if not os.path.exists(path):
            rows.append((u"not-found", u"%s 不在盘上" % rel))
            bad += 1
            continue
        rc, why = judge_one(path, name, token, allow)
        rows.append((rc, why))
        if rc != u"ok":
            bad += 1
    for rc, why in rows:
        print(u"  %s %s" % (rc, why))
    print(u"READING_ORDER 登记=%d ok=%d red=%d not-found=%d"
          % (len(ROSTER), sum(1 for r, _ in rows if r == u"ok"),
             sum(1 for r, _ in rows if r == u"red"), sum(1 for r, _ in rows if r == u"not-found")))
    print(u"READING_ORDER_RESULT=%s" % (u"ok" if bad == 0 else u"red"))
    return 0 if bad == 0 else 1


if __name__ == u"__main__":
    sys.exit(main())
