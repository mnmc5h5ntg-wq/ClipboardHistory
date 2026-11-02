# -*- coding: utf-8 -*-
"""R557 小补记：本轮成对号（含刚推的补记笔）与 R558 的 ⓪ 读单。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
⑥ **本轮成对号与 R558 读单**（取号时三跑均 in_progress ⇒ 全记 NOT-RUN，R558 必读）：
- `41464892684 ↔ ce4da8f` —— R557 B（刀表 M1443–M1445 + 预检名册），**同一跑覆盖产品笔 `2ca9501`**（一次 push 两笔，GitHub 只给 tip 建跑）⇒ 这一跑里 sources-cell 那一族**注定红**（台账还没写），不要把它的 STEP[9] 红读成产品回归。
- `41465486002 ↔ 5d05578` —— R557 台账笔。**这是本轮第一跑「账上那一格与 git 派生一致」的候选**：若它 STEP[9] 绿，就说明「推送顺序」这一格修对了；STEP[16]/[19] 也会带上 629 与 569 的读数（`QUICKPICK_STAR_FULLROWS` 的 1x 整行下界至今没有 runner 读数）。
- `41467173705 ↔ 61285b6` —— R557 补记笔（本轮 ⓪ 那四跑到手后的读数就在这里）。
- ⓪ 笔 `598b253` 自己的跑 `41455782587` 已 **cancelled**（15m01s、日志 404）⇒ 永远读不到，不重开。

R558 的 ⓪ 逐条抄**全部失败步骤**（`ci_read.py steps` 只列 failure/skipped，后面的 success 步骤要另用 `gh run view --json jobs` 逐条读，别把「不在列表里」当「没跑」）。② 的头一格已经不由我选：**629 按 (B) 落地**（三个 runner 真数已把 (A) 否掉，见 `AGENT_BACKLOG.md` 629 的「读数到手」那一行），第二格 = 634（把 `test_skip_roster` 的「没汇总行」与「汇总是 FAILED」拆成两格）。禁碰 9 面不变；刀号 **M1446** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板一律不动；633 仍等用户人工回执。

"""


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = u"stale-cell 窗口，标签要重审。\n"
    if not check:
        if t.count(anchor) != 1:
            sys.stderr.write("ANCHOR_BAD state ④ tail hits=%d\n" % t.count(anchor))
            return 1
        io.open(p, "w", encoding="utf-8").write(t.replace(anchor, anchor + BLOCK.strip(u"\n") + u"\n", 1))
    else:
        if t.count(anchor) != 1:
            sys.stderr.write("ANCHOR_BAD state ④ tail hits=%d\n" % t.count(anchor))
            return 1
    sys.stdout.write("ADDENDUM2_R557_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
