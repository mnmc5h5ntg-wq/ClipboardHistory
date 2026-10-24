#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R338 落盘之后量到的**取数口差一**：本轮明明动了产品，连读那一格却写着 2。

现读（本轮，第 337 轮 / R338 · 产品 1 文件）：

    $ python3 scripts/product_streak.py --streak-for 337
    PRODUCT_STREAK_FOR round=337 streak=2 last=fde8227 last_round=335      ← 把本轮那笔排除在外
    $ python3 scripts/product_streak.py --streak-for 338
    PRODUCT_STREAK_FOR round=338 streak=1 last=d8e6486 last_round=337      ← 认到了本轮这笔

而 `streak_for()` 的文档串自己写着"那一格写的是**落盘之后**的数" ⇒ 问第 337 轮就该把第 337 轮
那笔算进去。差一在这里第一次**看得见**：R337 那轮没有产品改动，两种口径都给 1，所以它藏了一轮。

这一支不修工具（修它要连带把历史上每一格的数重算，且 `test_product_streak_cell` 的窗口会整片红），
而是：① 把这条发现登记成 U-1154 与 BACKLOG 412；② 在两处连读格旁边**就地写明**它现在读作
"本轮之前"，不许被读成"本轮零改动"。工具修好之后这两处标注要一起撤掉（412 里写着）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
STA = os.path.join(ROOT, u"AGENT_STATE.md")
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
GEN = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledgers_r338.py")
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def once(t, old, new, tag):
    n = t.count(old)
    if n != 1:
        sys.stderr.write(u"R338_STREAK_DIED 锚点命中 %d 次：%s\n" % (n, tag))
        for p in WRITTEN:
            sys.stderr.write(u"  已写盘：" + p + u"\n")
        sys.exit(1)
    return t.replace(old, new)


def maybe(t, old, new, tag):
    if old not in t:
        if new in t:
            print(u"SKIP（已改过）" + tag)
            return t
        sys.stderr.write(u"R338_STREAK_DIED 既没有锚点也没有改过的痕迹：" + tag + u"\n")
        sys.exit(1)
    return once(t, old, new, tag)


# 现读两份口径
env = dict(os.environ)
env[u"PYTHONUTF8"] = u"1"


def ask(n):
    out = subprocess.run([sys.executable, os.path.join(ROOT, u"scripts", u"product_streak.py"),
                          u"--streak-for", str(n)], cwd=ROOT, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
    m = re.search(u"round=(\\d+) streak=(\\d+) last=(\\w+) last_round=(\\d+)", out)
    if not m:
        sys.stderr.write(u"R338_STREAK_DIED --streak-for 没给可解析的行：" + out[-200:] + u"\n")
        sys.exit(1)
    return m.groups()


A337, A338 = ask(337), ask(338)
if A338[3] != u"337":
    die_last = u"最后一笔产品提交没被认到第 337 轮"
    sys.stderr.write(u"R338_STREAK_DIED " + die_last + u"：" + str((A337, A338)) + u"\n")
    sys.exit(1)
NOTE = (u"—— 注意这一格的**口径差一**（U-%d / BACKLOG 412）：本轮明明动了产品，"
        u"`--streak-for 337` 仍给 %s，因为它把第 337 轮自己那笔排除在外"
        u"（`--streak-for 338` 才认到：streak=%s last_round=%s）。在工具修掉之前，"
        u"这一格只能读成「本轮**之前**的连读轮数」，不许读成「本轮零改动」。"
        % (1154, A337[1], A338[1], A338[3]))

# ── UI_AUDIT：加 U-1154，并把标题区间抬到 U-1147…U-1154 ─────────────────────
aud = rd(AUD)
aud = maybe(aud, u"## 第 337 轮（R338 · 2026-10-25 · U-1147…U-1153）",
            u"## 第 337 轮（R338 · 2026-10-25 · U-1147…U-1154）", u"UI 标题区间")
aud = maybe(aud, u"（U-1147…U-1153 · 产品 1 文件，HTML 通道）",
            u"（U-1147…U-1154 · 产品 1 文件，HTML 通道）", u"UI 标题尾部区间")
U_1154 = u"""- **U-1154：本轮明明动了产品，连读那一格却写着 %s —— 取数口的 as-of 边界差一，第一次看得见** ——
  现读 `--streak-for 337` → `streak=%s last=%s last_round=%s`（把第 337 轮自己那笔排除在外），
  而 `--streak-for 338` → `streak=%s last=%s last_round=%s`（认到了）。
  `streak_for()` 的文档串自己写着"那一格写的是**落盘之后**的数" ⇒ 问第 337 轮就该含第 337 轮。
  它藏了一轮的原因很典型：R337 没有产品改动，两种口径都给 %s，**没有反例能把它逼出来**；
  本轮第一次出现"这一轮的 commit 恰好就是要判的那一笔"，差一才现形。
  本轮不修工具（修它要把历史上每一格的数重算，`test_product_streak_cell` 的窗口会整片红），
  而是把两处连读格就地标注成「本轮**之前**的连读轮数」并开 BACKLOG 412 ——
  工具修好之后那两处标注要一起撤掉。**这一族的名字：口径差一在两边同数时是查不出来的，
  它只在两边分叉的那一轮才露头。**
""" % (A337[1], A337[1], A337[2], A337[3], A338[1], A338[2], A338[3], A337[1])
if u"- **U-1154" not in aud:
    # 追加在本节最后一条 U 之后（也就是下一节标题之前）—— 节内是降序，新号在尾
    i = aud.index(u"## 第 336 轮")
    aud = aud[:i] + U_1154.rstrip(u"\n") + u"\n\n" + aud[i:]
    wr(AUD, aud)
else:
    print(u"SKIP（已改过）U-1154 定义行")

# ── BACKLOG 412 ─────────────────────────────────────────────────────────────
blg = rd(BLG)
BL_412 = u"""**412. `product_streak.py --streak-for N` 的 as-of 边界差一：它不含第 N 轮自己的产品提交，\
而函数文档串写着"落盘之后的数"**（R338 现读）
现读两份：`--streak-for 337` → streak=2 last_round=335（不含本轮那笔产品提交）；
`--streak-for 338` → streak=1 last_round=337（含）。台账那一格按前者写，于是**动了产品的一轮**
在连读格里显示成"连读 2 轮"。R337 之前查不出来，因为那一轮没有产品改动 ⇒ 两种口径同数；
差一这种病只在两边分叉的那一轮露头（U-1154）。
修法两步，缺一不可：① 把 `streak_for` 的边界改成含 N 自己（`<=`），
② **同一笔**里把窗口内每一格的数按新口径重算 —— 否则 `test_product_streak_cell` 会整片红，
而那片红是正确的，不许为了绿而回滚①。做完要撤掉 STATE 与报告 §13 两处连读格旁边的临时标注
（那两句"本轮之前的连读轮数"是给这一轮读的，不是契约）。
"""
if u"**412. " not in blg:
    wr(BLG, blg.rstrip(u"\n") + u"\n\n" + BL_412.rstrip(u"\n") + u"\n")
else:
    print(u"SKIP（已改过）BACKLOG 412")

# ── 两处连读格就地标注 ───────────────────────────────────────────────────────
sta = rd(STA)
sta = maybe(sta, u"产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak" % A337[1],
            u"产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak" % A337[1] + NOTE,
            u"STATE 连读格标注")
wr(STA, sta)
fr = rd(FRA)
fr = maybe(fr, u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）。" % A337[1],
           u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）%s" % (A337[1], NOTE),
           u"报告连读格标注")
wr(FRA, fr)

# ── 幂等自检 + 电池 ─────────────────────────────────────────────────────────
out = subprocess.run([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"],
                     cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
tail = out.stdout.decode(u"utf-8", u"replace").strip().splitlines()[-3:]
if out.returncode != 0:
    sys.stderr.write(u"R338_STREAK_DIED 落盘之后电池红了：\n" + u"\n".join(tail) + u"\n")
    sys.exit(1)
print(u"R338_STREAK_OK 标注=2 处 U=1154 BL=412 现读=%s/%s 电池=%s"
      % (A337[1], A338[1], [t for t in tail if t.startswith(u"Ran")][0]))
