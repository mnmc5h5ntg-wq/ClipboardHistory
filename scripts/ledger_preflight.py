# -*- coding: utf-8 -*-
"""R593 / 靶 4：把"⓪ 必须在台账之前"从纪律做成仪器。

来历：R592 收口时我自己报了"本轮跳过了开场的 ⓪ CI 读"。纪律写在 ⑨ 里只能让下一轮**看见**，
不能让这一轮**不发生** —— 台账写手照样把六本写完了。所以这一支判的是文本本身：
本轮那一节的 ⓪ 里既没有成对号、也没有具名的"未到数"，就不许落盘。

两种合法形状（缺任意一种都算没读）：
  · 成对号行：`RUN=<数字> ↔ <sha>`（`ci_status_*.py` 那一趟印出来的形状）；
  · 具名未到数：`未到数` / `RUN_UNFETCHED` / `CI_UNREAD` 三者之一，且同一行带着原因字样
    （`in_progress` / `还没` / `未创建` / `同次 push`）—— 光写"未到数"三个字不算，
    它可能是"还没去取"被写成"取了没到"。

用法：python3 scripts/ledger_preflight.py [--state PATH] [--section-text TEXT]
退出码：0=⓪ 那一节有读数或有具名未到数；1=两样都没有（⇒ 写手必须停手）；2=连 ⓪ 那一节都切不出来。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "AGENT_STATE.md")

# 两种形状都要认：`ci_read.py` 印的是 `RUN=42179047067 ↔ 40cccd4`，而台账正文里习惯写成反引号的
# `42179047067 ↔ 40cccd4`（没有 `RUN=`）。只认前者会把填好的账读成"没读"—— 尺读错了写法，
# 与 R590 那一族同形。run id 至少 9 位，避开把"两笔 sha 之间"误当配对。
PAIR = re.compile(u"(?:RUN=)?\\d{9,}\\s*↔\\s*[0-9a-f]{7,40}")
UNREAD_TOKENS = (u"未到数", u"RUN_UNFETCHED", u"CI_UNREAD")
UNREAD_REASONS = (u"in_progress", u"还没", u"未创建", u"同次 push", u"conclusion 空")


def zero_section(text, head):
    """从给定标题位置切出那一节的 ⓪ 那一段（到下一个 `①②…` 或下一节标题）。"""
    body = text[head.start():]
    nxt = re.search(u"(?m)^## R\\d+ (状态|补记)（", body[1:])
    if nxt:
        body = body[:nxt.start() + 1]
    m = re.search(u"(?m)^⓪[ \\t]*", body)
    if not m:
        return None
    rest = body[m.start():]
    stop = re.search(u"(?m)^[①②③⑤⑥⑦⑨⑩]", rest[1:])
    return rest[:stop.start() + 1] if stop else rest


def locate(text, expect_round=None):
    """返回 (⓪ 那一段, 逐字依据) —— **认得出本笔的凭据是标题里那个轮次号，不是它在文件里的位置**。

    为什么要换成内容这一维（R593 留的下半截）：把 `heads[-1]` 改成 `heads[0]` 只是把"位置猜错"
    换成"位置猜对"，它仍然不说明**为什么**那一节是本轮 —— 台账一旦变成乱序（追加笔、补记插在最上面、
    或有人手改顺序），位置就与"本轮那一笔"不是同一件事，而这一支会安静地判到别的轮次上去。
    现在三条独立的路一起走：
    · `expect_round`（写手自己知道在写第几轮）⇒ 首选，按号取；
    · `max(号)`（内容上的最新）；
    · `heads[0]`（位置上的最新，即降序约定）。
    后两者**分歧**就直接红（`一致=0`），因为那说明台账的排序约定已经不成立，
    此时"判了哪一节"变成猜 ⇒ 不许绿。
    """
    heads = list(re.finditer(u"(?m)^## R(\\d+) 状态（", text))
    if not heads:
        return None, u"LEDGER_PREFLIGHT_LOCATE 依据=没有 原因=读不到任何 `## Rnnn 状态` 节"
    by_pos = heads[0]
    by_content = max(heads, key=lambda m: int(m.group(1)))
    agree = by_pos.start() == by_content.start()
    if expect_round is not None:
        picked = [h for h in heads if int(h.group(1)) == int(expect_round)]
        if not picked:
            return None, (u"LEDGER_PREFLIGHT_LOCATE 依据=按号 期望轮=%s 现读号=%s ⇒ 台账里没有本轮那一节"
                          % (expect_round, u",".join(h.group(1) for h in heads[:4])))
        head = picked[0]
        basis = u"按号(写手给的轮次 %s)" % head.group(1)
    else:
        head = by_content
        basis = u"按号(内容最大 %s)" % head.group(1)
    return zero_section(text, head), (
        u"LEDGER_PREFLIGHT_LOCATE %s 位置=R%s 内容=R%s 一致=%d 切到=R%s 依凭=%s"
        % (basis, by_pos.group(1), by_content.group(1), 1 if agree else 0, head.group(1),
           u"标题里的轮次号；位置只当交叉核对" if agree else u"位置与内容分歧 ⇒ 台账排序约定已坏，判谁都不可信"))


def newest_zero_section(text):
    """兼容旧调用（不带轮次参数）：取**内容上最新**那一节的 ⓪ 那一段。

    只在这一段里判，不许扫全文 —— 历史节的 ⓪ 早就填好了，扫全文会让这一支永远绿。
    """
    return locate(text)[0]


def judge(section):
    """返回 (rc, 逐字理由)。`section` 是 ⓪ 那一段的整段文本。"""
    if section is None:
        return 2, u"LEDGER_PREFLIGHT_RESULT=not-run 原因=切不到本轮 ⓪ 那一段 ⇒ 不判，也不许当成绿"
    if PAIR.search(section):
        return 0, u"LEDGER_PREFLIGHT_RESULT=ok 形状=成对号 逐字=%s" % PAIR.search(section).group(0)
    hits = [t for t in UNREAD_TOKENS if t in section]
    if hits:
        reasons = [r for r in UNREAD_REASONS if r in section]
        if reasons:
            return 0, (u"LEDGER_PREFLIGHT_RESULT=ok 形状=具名未到数 词=%s 原因=%s"
                       % (u",".join(hits), u",".join(reasons)))
        return 1, (u"LEDGER_PREFLIGHT 红：⓪ 写了 %s 却没带原因字样 ⇒ "
                   u"'还没去取'与'取了没到'是两种账，混着写就是假话" % u",".join(hits))
    return 1, u"LEDGER_PREFLIGHT 红：⓪ 那一节既没有 RUN=…↔… 成对号，也没有具名的未到数 ⇒ 这一轮的 CI 根本没读"


def selfcheck():
    """三把正对照：成对号必须绿、裸"未到数"必须红、什么都没有必须红。少一把就是尺瞎了。"""
    good = u"⓪ 现读\n   RUN=42210166309 ↔ 03b48b2 到数=是\n"
    good_bare = u"⓪ 现读两对：`42210166309 ↔ 03b48b2`（台账里那种反引号写法）\n"
    named = u"⓪ 现读\n   status=in_progress ⇒ 未到数（conclusion 空）\n"
    bare = u"⓪ 现读\n   这一格还没填\n"
    empty = u"⓪\n   （空）\n"
    checks = [(judge(good)[0], 0), (judge(good_bare)[0], 0), (judge(named)[0], 0),
              (judge(bare)[0], 1), (judge(empty)[0], 1), (judge(None)[0], 2)]
    # locate 那一维也要有对照：尺换了认法却没证过"认得对本笔"，就只是把一种猜换成另一种。
    ordered = (u"## R594 状态（x）\n⓪ 现读\n   RUN=42220000001 ↔ abc1234\n\n"
               u"## R593 状态（y）\n⓪ 现读\n   RUN=42220000002 ↔ def5678\n")
    scrambled = (u"## R593 状态（y）\n⓪ 现读\n   RUN=42220000002 ↔ def5678\n\n"
                 u"## R594 状态（x）\n⓪ 现读\n   RUN=42220000001 ↔ abc1234\n")
    checks += [
        (0 if u"一致=1" in locate(ordered)[1] else 1, 0),
        (0 if u"一致=0" in locate(scrambled)[1] else 1, 0),
        (0 if locate(ordered, 593)[1].startswith(u"LEDGER_PREFLIGHT_LOCATE 按号(写手给的轮次 593)") else 1, 0),
        (1 if locate(ordered, 999)[0] is None else 0, 1),
        (0 if judge(locate(ordered, 594)[0])[0] == 0 else 1, 0),
    ]
    bad = [c for c in checks if c[0] != c[1]]
    print(u"LEDGER_PREFLIGHT_READER_SELFTEST=%s 格子=%d 不符=%d"
          % (u"seen" if not bad else u"blind", len(checks), len(bad)))
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--state", default=STATE)
    ap.add_argument(u"--section-text", default=None)
    ap.add_argument(u"--round", default=None,
                    help=u"写手正在落盘的那一轮（Rnnn 的号）；不给就取内容上最大的那一节")
    args = ap.parse_args()
    if not selfcheck():
        print(u"LEDGER_PREFLIGHT_RESULT=red 原因=尺瞎了（正对照没响）⇒ 这一格今天没判")
        return 1
    if args.section_text is not None:
        rc, why = judge(args.section_text)
    else:
        if not os.path.exists(args.state):
            print(u"LEDGER_PREFLIGHT_RESULT=not-run 原因=读不到 %s" % args.state)
            return 2
        text = io.open(args.state, encoding=u"utf-8", errors=u"replace").read()
        section, where = locate(text, args.round)
        print(where)
        if args.round is not None and section is None:
            print(u"LEDGER_PREFLIGHT_RESULT=red 原因=按号切不到本轮那一节 ⇒ 台账顺序或轮次号有一处坏")
            return 1
        if u"一致=0" in where:
            print(u"LEDGER_PREFLIGHT_RESULT=red 原因=位置与内容两种认法分歧 ⇒ 判的是哪一节变成猜")
            return 1
        rc, why = judge(section)
    print(why)
    return rc


if __name__ == u"__main__":
    sys.exit(main())
