# -*- coding: utf-8 -*-
"""R308 的 BACKLOG 348 追记：台账生成器把「补记的子卷」当成「全量卷」，被新写的恒等式闸门当场拦下。

为什么单独一支脚本而不是改生成器：七本已由 `ledgers_r308.py` 落盘并通过写盘前后电池，
这一格是**落盘之后量到的新自曝**，重跑生成器会把已经作数的读数再刷一遍。
形状规矩照旧：整行锚点、命中数断言、段内落点检查、幂等（已有追记就拒写第二遍）。
"""
import io
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
BL = ROOT + "/AGENT_BACKLOG.md"
TAG = u"追记（R308）"

NOTE = [
    u"  追记（R308）：这一族今天又长了一颗新的牙，而且是被**我自己刚写的那道闸门**当场拦下来的。",
    u"  生成器取「全量卷」的读数用的是 `re.findall(Executed …, chain)[-1]` —— 在**整份**验证链日志里取末，",
    u"  而那份日志最后一行 `Executed` 属于 `### CAPTURE 结论行补记`（UICaptureTests 那一卷 = 92 格、0 失败），",
    u"  于是第一版落盘的三本账（ITERATION / CHANGELOG / STATE）都写着「全量卷 Executed 92 tests, with 4 skipped",
    u"  and 0 failures」，而真读数是 **934 / 44 skip / 0**。`FULL_FAIL != 0 就拒写` 那道门**完全不响** ——",
    u"  抄来的那一行恰好是 0 失败。与 R223「取末把内层 suite 当全量总数」同族第二次复发，",
    u"  这次的形状是「取末把补记的子卷当成全卷」。",
    u"",
    u"  落地的修法两条（都在 `.scratch/motion-audit-2/ledgers_r308.py`）：",
    u"  ① 读数**按验证链的小节切片取**（`section_parts(chain, 「FULL SUITE」)`）。写这一格时又踩一次：",
    u"  `re.split` 只吃掉分隔符 ⇒ 小节标题与它的正文住在**同一个块**里，正文要取本块去掉首行；",
    u"  取下一块拿到的是下一节的第一行 ⇒ FULL SUITE 的正文被读成 INSTALL / CAPTURE 那节，92 顶替 934。",
    u"  这个错当场被 ② 抓到（第一次运行就 REFUSED，七本一个字节都没落盘）。",
    u"  ② 恒等式闸门：**全量卷不可能比日志里任何一卷小**（`FULL_RUN < max(日志里所有 Executed 数)` 就拒写），",
    u"  并且每一跑各自记账 —— 早先那跑的红原样抄进台账（台账里那句「共 2 跑：…」），",
    u"  不许把改动过程写成「只跑了一遍绿」。",
    u"",
    u"  仍欠的那一把刀（诚实记账）：这道闸门今天只在**真日志**上证过（第一跑就红、点名 92 与 934），",
    u"  还没有变异对照钉住「把它摘掉就会漏」。下一轮（R309）把它与 364 那条「表自数 needle」并成一刀：",
    u"  闸门本体已是纯函数（`section_parts` + 恒等式那两行），喂两行合成日志就能断言必须拒写。",
]


def die(msg):
    sys.stderr.write(u"R308_NOTE_REFUSED " + msg + u"\n")
    raise SystemExit(1)


def main():
    txt = io.open(BL, encoding="utf-8").read()
    if TAG in txt:
        die(u"348 的 R308 追记已经在盘上 ⇒ 不许插第二遍（幂等守卫）")
    lines = txt.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(u"**348. ")]
    if len(hits) != 1:
        die(u"348 的条目头命中 %d 行（要恰好 1）" % len(hits))
    h = hits[0]
    nxt = [i for i in range(h + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    k = nxt[0] if nxt else len(lines)
    while lines[k - 1].strip() == u"":
        k -= 1
    head = u"\n".join(lines[:k])
    if not head.endswith(u"\n"):
        head += u"\n"
    out = head + u"\n".join(NOTE) + u"\n" + u"\n".join(lines[k:]).lstrip(u"\n")
    i348 = out.find(u"**348. ")
    inote = out.find(TAG)
    if not (0 <= i348 < inote):
        die(u"追记落点不对（348=%d 追记=%d）" % (i348, inote))
    # 落点的正确判法：348 之后**第一个**条目头必须排在追记之后 —— 追记要在 348 的节里。
    # 第一版写成「追记之后的条目头必须 ≤1 个」，那是恒假：追记本来就住在所有后续条目之前，
    # 后面永远跟着整本账的条目头（这一格在写盘之前自己红了，没弄坏账）。
    later = re.search(u"(?m)^\\*\\*\\d{3}\\. ", out[i348 + 8:])
    if later is None or i348 + 8 + later.start() <= inote:
        die(u"追记没落在 348 的节内（348=%d 追记=%d 下一条目头=%s）"
            % (i348, inote, (i348 + 8 + later.start()) if later else u"没有"))
    io.open(BL, "w", encoding="utf-8").write(out)
    print(u"R308_NOTE_WRITTEN 348 追记 %d 行；条目头总数 %d（写前 %d，一个都不许多也不许少）"
          % (len(NOTE), len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", out)),
             len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", txt))))


if __name__ == "__main__":
    main()
