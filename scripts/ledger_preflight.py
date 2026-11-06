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


def newest_zero_section(text):
    """切出**最新一轮状态节**里 ⓪ 那一段（从 `⓪` 行到下一个单字符节标题）。

    只在这一段里判，不许扫全文 —— 历史节的 ⓪ 早就填好了，扫全文会让这一支永远绿。
    """
    heads = list(re.finditer(u"(?m)^## R\\d+ 状态（", text))
    if not heads:
        return None
    # 台账是**降序**（最新一节在文件最上面）⇒ 取 heads[0]。写成 heads[-1] 会切到最老那一节，
    # 而那一节的 ⓪ 早就填好了 ⇒ 这一支永远绿（尺读错了对象，R555/R580 那一族）。
    body = text[heads[0].start():]
    nxt = re.search(u"(?m)^## R\\d+ (状态|补记)（", body[1:])
    if nxt:
        body = body[:nxt.start() + 1]
    m = re.search(u"(?m)^⓪[ \\t]*", body)
    if not m:
        return None
    rest = body[m.start():]
    stop = re.search(u"(?m)^[①②③⑤⑥⑦⑨⑩]", rest[1:])
    return rest[:stop.start() + 1] if stop else rest


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
    bad = [c for c in checks if c[0] != c[1]]
    print(u"LEDGER_PREFLIGHT_READER_SELFTEST=%s 格子=%d 不符=%d"
          % (u"seen" if not bad else u"blind", len(checks), len(bad)))
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--state", default=STATE)
    ap.add_argument(u"--section-text", default=None)
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
        rc, why = judge(newest_zero_section(text))
    print(why)
    return rc


if __name__ == u"__main__":
    sys.exit(main())
