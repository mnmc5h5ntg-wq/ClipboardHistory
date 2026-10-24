#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R337 落盘之后的两朵**读数错**修账（一次跑完，逐条锚点命中一次）。

两处都是我自己写的尺/解析器的错，不是台账抄错：

① `RATIO_DARK_ROW` 取了 `比 X:1` 的**第一个**匹配 —— 而 `row_ink_probe.py` 那一行先打印
   亮侧（暗档左列的亮墨=0 ⇒ 比 0.00:1）、后打印暗侧（黑字 ⇒ 比 1.23:1）。
   于是"暗档黑字 1.23:1"这条 finding 在台账里被写成了 0.00:1 —— 那个数的意思是
   "亮侧没有墨"，恰好把要找的那一格洗掉了。修法：**尺把两侧分开命名**，台账取暗侧那一个。
② 落后轮数解析自 `review_full_history.py` 的现读行，而那份日志是 **§14 补写之后**重跑的 ⇒
   它现在报"落后 0 轮"（门已经绿了），可 U-1142 讲的是"补写之前停在 R298"这件事。
   修法：落后数改成从 §14 自己那句现读（那里写着 38），并把"补写后现读 0"一起写进同一句 ——
   两个数都要在，否则下一轮读者不知道门是从哪儿开始生效的。

两处都同时改**生成器**（`ledgers_r337.py`）与**已落盘的台账**，让生成器与账对得上；
这一支就是那件"对得上"的证人。
"""
import io
import os
import re
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
GEN = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledgers_r337.py")
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def once(t, old, new, tag):
    n = t.count(old)
    if n != 1:
        sys.stderr.write(u"R337_FIX_DIED 锚点命中 %d 次（要 1）：%s ⇒ %s\n" % (n, tag, old[:60]))
        for p in WRITTEN:
            sys.stderr.write(u"  已写盘：" + p + u"\n")
        sys.exit(1)
    return t.replace(old, new)


# 现读：正确的两个数都不手填
ink = rd(u"/tmp/r337_ink.log")
dark_line = [ln for ln in ink.splitlines() if u"ROW_INK dark 行1文字" in ln][0]
ratios = re.findall(u"比 ([0-9.]+):1", dark_line)
if len(ratios) != 2:
    sys.stderr.write(u"R337_FIX_DIED 暗档那一行没打两个方向的比：%s\n" % dark_line)
    sys.exit(1)
DARK_RATIO = ratios[1]                      # 第二个 = 暗侧（黑字对底）
lag_src = rd(os.path.join(ROOT, u"AGENT_FINAL_REPORT.md"))
LAG = (re.findall(u"停在 R298，落后 \\*\\*(\\d+) 轮\\*\\*", lag_src) or [None])[0]
if LAG is None or DARK_RATIO == u"0.00":
    sys.stderr.write(u"R337_FIX_DIED 现读失败：LAG=%s DARK_RATIO=%s\n" % (LAG, DARK_RATIO))
    sys.exit(1)
print(u"R337_FIX_READ 暗侧比=%s:1 补写前落后=%s 轮" % (DARK_RATIO, LAG))

# ── 生成器本体：尺的取数口改成"暗侧那一个"，落后数改成从 §14 现读 ──────────
SKIPPED = []


def apply(t, old, new, tag, marker):
    u"""幂等版 once：已经改过（marker 在盘上）就跳过并记账，没改过才要求锚点恰好一次。

    这一支第一次跑在断言上 die 过，而它**已经写过生成器** ⇒ 没有幂等，第二次跑会把
    自己判成"锚点命中 0 次"，那正是本仓库反复记过的半批已写形状。
    """
    if marker in t:
        SKIPPED.append(tag)
        return t
    return once(t, old, new, tag)


g = rd(GEN)
g = apply(g, u"RATIO_DARK_ROW = (re.findall(u\"比 ([0-9.]+):1\", INK_DARK_ROW) or [None])[0]",
           u"# 暗档那一行**两个方向都打**：第一个比是亮侧（暗档左列亮墨=0 ⇒ 0.00:1，意思是"
           u"「没有亮墨」），\n# 第二个才是暗侧（黑字对底）。取错下标 = 把这条 finding 洗成它的反面。\n"
           u"RATIO_DARK_ROW = (re.findall(u\"比 ([0-9.]+):1\", INK_DARK_ROW) or [None, None])[1]",
           u"生成器：暗侧比的下标", u"INK_DARK_ROW) or [None, None])[1]")
g = apply(g, u"RATIO_LIGHT_ROW = (re.findall(u\"比 ([0-9.]+):1\", INK_LIGHT_ROW) or [None])[1]",
          u"RATIO_LIGHT_ROW = (re.findall(u\"比 ([0-9.]+):1\", INK_LIGHT_ROW) or [None, None])[1]",
          u"生成器：亮档比的下标", u"INK_LIGHT_ROW) or [None, None])[1]")
g = apply(g, u"RATIO_DETAIL = (re.findall(u\"比 ([0-9.]+):1\", INK_DETAIL) or [None])[0]",
          u"RATIO_DETAIL = (re.findall(u\"比 ([0-9.]+):1\", INK_DETAIL) or [None, None])[0]",
          u"生成器：详情头比的下标", u"INK_DETAIL) or [None, None])[0]")
g = apply(g, u"if not (RATIO_DARK_ROW and RATIO_LIGHT_ROW and RATIO_DETAIL):",
          u"if not (RATIO_DARK_ROW and RATIO_LIGHT_ROW and RATIO_DETAIL):\n"
          u"    die(u\"行墨尺的比没解析到\")\n"
          u"if RATIO_DARK_ROW == u\"0.00\":\n"
          u"    die(u\"暗侧比读成 0.00 ⇒ 十有八九又取了亮侧那一个（这一族本轮真栽过）\")",
          u"生成器：0.00 自检", u"if RATIO_DARK_ROW == u\"0.00\":")
g = g.replace(u"(re.findall(u\"落后 (\\\\d+) 轮\", REVIEW_REPORT) or [u\"?\"])[0]",
              u"LAG_BEFORE")
if u"REVIEW_REPORT) or [u\"?\"]" in g:
    sys.stderr.write(u"R337_FIX_DIED 生成器里还有没换掉的落后读数\n")
    sys.exit(1)
g = apply(g, u"INK_DETAIL = line_with(ink_log, u\"ROW_INK dark 详情头\", u\"行墨尺\")",
          u"INK_DETAIL = line_with(ink_log, u\"ROW_INK dark 详情头\", u\"行墨尺\")\n"
          u"# 「落后多少轮」必须取**补写之前**那一份：回顾尺在 §14 落盘之后重跑会报 0（门已经绿了），\n"
          u"# 而 U-1142 讲的是补写之前那件事。出处是 §14 自己那句现读（它由 report_section14.py 生成）。\n"
          u"LAG_BEFORE = (re.findall(u\"停在 R298，落后 \\\\*\\\\*(\\\\d+) 轮\\\\*\\\\*\",\n"
          u"                          rd(FRA)) or [None])[0]\n"
          u"if LAG_BEFORE is None:\n"
          u"    die(u\"报告 §14 里没有那句落后读数 ⇒ 落后轮数没出处，不许手填\")",
          u"生成器：落后数出处", u"LAG_BEFORE = (re.findall(")
if u"LAG_BEFORE = (re.findall(" not in g:
    sys.stderr.write(u"R337_FIX_DIED 生成器用了 LAG_BEFORE 却没定义它 ⇒ 会 NameError\n")
    sys.exit(1)
wr(GEN, g)
print(u"R337_FIX_GEN 生成器已改到现读口径，跳过（本来就对）的：%s" % (u"、".join(SKIPPED) or u"无"))

# ── 已落盘的三本账 + 报告 + 迭代账 ─────────────────────────────────────────
P = os.path.join


def fix(name, pairs):
    path = P(ROOT, name)
    t = rd(path)
    for old, new, tag in pairs:
        if old not in t and new[:24] in t:
            SKIPPED.append(name + u" " + tag)          # 已经改过 ⇒ 幂等跳过
            continue
        t = once(t, old, new, name + u" " + tag)
    wr(path, t)


fix(u"AGENT_UI_AUDIT.md", [
    (u"落后 0 轮（`review_full_history.py` 现读）",
     u"落后 " + LAG + u" 轮（这是 §14 **补写之前**的现读；补写之后同一把尺现读 0 轮 —— "
     u"两个数都要在，否则下一轮读者不知道那格门是从哪儿开始生效的）",
     u"U-1142 落后数"),
    (u"底 28 ⇒ **比 0.00:1**", u"底 28 ⇒ **比 " + DARK_RATIO + u":1**", u"U-1144 比"),
])
fix(u"AGENT_STATE.md", [
    (u"报告叙述节停在 R298（落后 0）",
     u"报告叙述节停在 R298（补写前落后 " + LAG + u"，补写后现读 0）", u"STATE 落后数"),
    (u"底 28 ⇒ 比 0.00:1，", u"底 28 ⇒ 比 " + DARK_RATIO + u":1，", u"STATE ④ 比"),
    (u"暗档左列那 0.00:1", u"暗档左列那 " + DARK_RATIO + u":1", u"STATE NOT-RUN 比"),
    (u"两份都现读、并在同一行里写清哪一份作数，下一次换口径的人就看得见差一从哪来。",
     u"两份都现读、并在同一行里写清哪一份作数，下一次换口径的人就看得见差一从哪来。\n"
     u"第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——\n"
     u"那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 "
     + DARK_RATIO + u":1）。\n"
     u"于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**"
     u"（下标 + 一格「读到 0.00 就 die」的自检），\n"
     u"并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。",
     u"STATE 第三处自伤"),
])
fix(u"AGENT_BACKLOG.md", [
    (u"底 28 ⇒ 0.00:1）", u"底 28 ⇒ " + DARK_RATIO + u":1）", u"409 标题比"),
])
fix(u"AGENT_FINAL_REPORT.md", [
    (u"底 28 ⇒ 比 0.00:1（亮档同一盒子", u"底 28 ⇒ 比 " + DARK_RATIO + u":1（亮档同一盒子",
     u"§13 产品面比"),
])
fix(u"AGENT_VISUAL_ITERATION.md", [
    (u"③ 报告的叙述节停在 R298、落后 0 轮",
     u"③ 报告的叙述节停在 R298、落后 " + LAG + u" 轮（补写之后同一把尺现读 0）", u"ITER 落后数"),
    (u"底 28 ⇒ 比 0.00:1（亮档同一块盒子", u"底 28 ⇒ 比 " + DARK_RATIO + u":1（亮档同一块盒子",
     u"ITER 正文比"),
    (u"两向像素尺（0.00:1 对 20.29:1）", u"两向像素尺（" + DARK_RATIO + u":1 对 20.29:1）",
     u"ITER 七维表比"),
])

# ── 第三处：STATE 里那三笔小坏（曲线取的是写盘**之前**那份、前缀重复、一个错字）──
import subprocess
env = dict(os.environ)
env[u"PYTHONUTF8"] = u"1"
p = subprocess.run([sys.executable, os.path.join(ROOT, u".scratch", u"motion-audit-2",
                                                    u"curve_from_ledger.py")],
                   cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
curve_after = p.stdout.decode(u"utf-8", u"replace")
PH_AFTER = (re.findall(u"(?m)^PHASE2 n=.*$", curve_after) or [None])[0]
if PH_AFTER is None or u"GAPS=none" not in curve_after:
    sys.stderr.write(u"R337_FIX_DIED 写盘之后的曲线尺没给数\n")
    sys.exit(1)
def maybe(t, old, new, tag):
    u"""已经改过就跳过并记账（这一支会被重跑，幂等是底线）。"""
    if old not in t:
        SKIPPED.append(tag)
        return t
    return once(t, old, new, tag)


st = rd(P(ROOT, u"AGENT_STATE.md"))
# 那一格在 STATE 里是**句中的一段**（`…；曲线 \`PHASE2 n=…\`。`），所以不许按行首找 ——
# 第一版按 `^PHASE2` 找，命中 0 次而那一格悄悄留在了写盘之前的数上（少一轮）。
PH_BEFORE = (re.findall(u"PHASE2 n=[^`。\n]*", st) or [None])[0]
# 比较只看仪器那一段：后缀是这一支自己加的说明，带上它会让"是否已改"永远判不成（跑一次改一次）。
PH_CORE = PH_BEFORE.split(u"（")[0] if PH_BEFORE else None
if PH_CORE and PH_CORE != PH_AFTER:
    st = once(st, PH_CORE, PH_AFTER + u"（**取的是本轮 ITERATION 落盘之后**那一份）",
              u"STATE 曲线格")
st = maybe(st, u"REVIEW_COMMIT_CLAIMS REVIEW_COMMIT_CLAIMS ", u"REVIEW_COMMIT_CLAIMS ",
           u"STATE 前缀重复")
st = maybe(st, u"窗口之外从来没没人看过", u"窗口之外从来没人看过", u"STATE 错字")
wr(P(ROOT, u"AGENT_STATE.md"), st)
print(u"R337_FIX_CURVE %s → %s" % (PH_BEFORE or u"没解析到", PH_AFTER))

# 幂等自检：不该再有"错的形状"残留（排除 row_ink_probe 原样搬运的那两行 raw 读数）
bad = []
for name in (u"AGENT_UI_AUDIT.md", u"AGENT_STATE.md", u"AGENT_BACKLOG.md",
             u"AGENT_FINAL_REPORT.md", u"AGENT_VISUAL_ITERATION.md"):
    for ln in rd(P(ROOT, name)).splitlines():
        if u"ROW_INK" in ln or u"亮侧" in ln:
            continue                                  # 原样搬运的读数行 / 解释"错在哪"的自伤行
        if u"0.00:1" in ln or u"落后 0 轮" in ln:
            bad.append(name + u": " + ln[:70])
if bad:
    sys.stderr.write(u"R337_FIX_DIED 还有残留：\n  " + u"\n  ".join(bad) + u"\n")
    sys.exit(1)
print(u"R337_FIX_OK 五本=%d 处=10 暗侧比=%s:1 落后=%s" % (len(WRITTEN), DARK_RATIO, LAG))
