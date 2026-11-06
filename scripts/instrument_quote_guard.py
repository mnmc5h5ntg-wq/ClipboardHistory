# -*- coding: utf-8 -*-
"""R594 靶 4②：把"从仪器输出抄一行到台账"这件事做成会红的守卫。

来历（R593 ⑤ 自己列的自伤）：主节 ④ 那句"新表进预检名册"我贴的是**同一份输出里相邻的另一行**
（`mutate_r245 —— 静态抽不出 needle ⇒ 不在覆盖里`），而不是本轮那张表的行
（`mutate_r593_paths  M1598 ok；…；M1610 ok`）。形状对、话是真话、对象错 ⇒ 门看不见。
所以这一支只判三件事，都是可数的：

① 引号里那张表名**必须在名册里**（名册 = `mutate_needle_precheck.TABLES`，复用同一个对象，不抄第二份）；
② 引号里出现的刀号必须是**那张表自己登记的刀**（现读表文件的 `ARMS`），出现别表的号就红；
③ 没有逐条列全时必须写省略号（`…`/`...`）—— 不写就等于宣称"这一行就是全部"，
   而 `mutate_r593_paths` 那种十三把的表一定列不全 ⇒ 静默把"节选"写成"全文"。

扫描面 0 行（本轮台账里根本没抄仪器行）⇒ 具名 `no-quote-lines` 并退 0：这是**没判这一维**，
不是"这一维没问题"，读数里会把扫描面印出来。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import ledger_preflight as pre  # noqa: E402  —— 复用"哪一节是本轮那一节"的同一把尺

HERE = os.path.join(REPO, ".scratch", "motion-audit-2")
QUOTE = re.compile(u"`(mutate_\\w+)([^`]*)`")
ARM = re.compile(u"M(\\d{3,4})")
ELLIPSIS = (u"…", u"...")


def load_tables():
    spec = importlib.util.spec_from_file_location(
        "mutate_needle_precheck", os.path.join(HERE, "mutate_needle_precheck.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.TABLES)


def load_arms(name):
    """一张表里登记的刀号（现读表文件，不抄名册）。读不到就返回 None ⇒ 上层按红处理。"""
    path = os.path.join(HERE, name + u".py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except BaseException:                              # noqa: BLE001 —— 载不进就是判不了
        return None
    arms = getattr(mod, "ARMS", None)
    if not isinstance(arms, (list, tuple)):
        return None
    out = []
    for row in arms:
        first = row[0] if isinstance(row, (list, tuple)) else row
        found = ARM.findall(str(first))
        out.extend(int(x) for x in found)
    return sorted(set(out)) or None


def judge_line(line, tables, arms_by_table):
    """一行里可能同时"点名某张表"与"抄某张表的那一行"⇒ 先把两者分开。

    R593 那朵错的形状就在这里：`新表 \`mutate_r593_paths\` 进预检名册（\`mutate_r245  -- 静态抽不出…\`）`
    —— 括号里被当成"现读那一行"抄出来的，是**另一张表**的行。两张表都在名册里，
    所以只查"在不在名册"抓不到它；要查的是**被抄那一行的表名 == 被声称的那张新表**。
    """
    # 两种"看着像抄行"的形状**不是**抄行：① 文件路径（`.scratch/…/mutate_needle_precheck.py`）——
    # 那是文件名，不是某张表的那一行；② 反引号里只有表名、没有内容（`mutate_x`）—— 那是**提到**这张表。
    # 把它们当抄行，尺就把台账里一句正常话判成"抄错对象"（R594 本机实测到这两形，正对照在判据卷里）。
    stripped = re.sub(u"[\\w./-]*mutate_\\w+\\.py", u"PATH-STRIPPED", line)
    rows = [(n, rest) for n, rest in QUOTE.findall(stripped) if rest.strip()]
    out = []
    named = [n for n, rest in rows if rest.strip()]              # 带内容 ⇒ 是"抄的那一行"
    claimed = re.findall(u"新表\\s*`(mutate_\\w+)`|`?本轮那张表`?\\s*(mutate_\\w+)", line)
    claimed = [a or b for a, b in claimed]
    for name, rest in rows:
        problems = []
        if name not in tables:
            problems.append(u"名册里没有这张表（现读名册=%d 张）⇒ 抄的是不存在的对象" % len(tables))
        else:
            own = arms_by_table.get(name) or []
            quoted = sorted(set(int(x) for x in ARM.findall(rest)))
            foreign = [n for n in quoted if own and n not in own]
            if foreign:
                problems.append(u"引用里的刀号不属于这张表：%s（这张表现读=%s）"
                                % (foreign, u",".join(str(n) for n in own[:3]) + u"…"))
            if own and quoted and quoted[0] != own[0]:
                problems.append(u"引用从 %s 开始，而这张表的第一把是 %s ⇒ 这行不是表自己的那一行"
                                % (quoted[0], own[0]))
            if own and quoted and len(quoted) < len(own) and not any(e in rest for e in ELLIPSIS):
                problems.append(u"列了 %d 把而这张表有 %d 把，却没写省略号 ⇒ 把节选写成全文"
                                % (len(quoted), len(own)))
        if named and claimed:
            for n in claimed:
                wrong = [m for m in named if m != n]
                if wrong:
                    problems.append(u"这行声称新表是 `%s`，而括号里被抄成"
                                    u"“那一行”的是 %s ⇒ 指向了相邻另一张表（R593 ④ 那一朵的形状）"
                                    % (n, u",".join(wrong)))
        out.append((name, rest.strip()[:60], problems))
    return out


def judge_lines(lines, tables, arms_by_table):
    return [row for line in lines for row in judge_line(line, tables, arms_by_table)]


def selfcheck():
    tables = [u"mutate_r900_paths", u"mutate_r245"]
    arms = {u"mutate_r900_paths": [1611, 1612, 1613], u"mutate_r245": []}
    cases = [
        (u"新表进预检名册（`mutate_r900_paths  M1611 ok；…；M1613 ok`）", 0),
        (u"新表进预检名册（`mutate_r245  静态抽不出 needle`）", 0),      # 名册里有这张表 ⇒ 允许抄它
        (u"新表进预检名册（`mutate_r999_nothere  M1611 ok`）", 1),
        (u"新表进预检名册（`mutate_r900_paths  M1582 ok`）", 1),          # 别表的刀号
        (u"新表进预检名册（`mutate_r900_paths  M1611 ok；M1612 ok`）", 1),  # 少了省略号
        # R593 ④ 那一朵的形状：两张表都在名册里，被抄成"那一行"的却是**另一张**。
        (u"新表 `mutate_r900_paths` 进预检名册（`mutate_r245  -- 静态抽不出 needle`）", 1),
    ]
    bad = 0
    for text, want in cases:
        got = sum(1 for _, _, p in judge_lines([text], tables, arms) if p)
        ok = (got == 0) if want == 0 else (got >= want)
        if not ok:
            bad += 1
        print(u"  对照 %s ⇒ 红行=%d 期望=%s" % (text[:34], got, u"0" if want == 0 else u"≥%d" % want))
    print(u"INSTRUMENT_QUOTE_SELFTEST=%s 对照=%d 不符=%d"
          % (u"seen" if not bad else u"blind", len(cases), bad))
    return not bad


def newest_section(text):
    """整节（不是 ⓪ 那一段）：抄仪器行的那一格在 ④/⑤ 里，不在 ⓪。
    认"哪一节是本轮"仍复用 ledger_preflight.locate 那条依据（位置与内容两种认法要一致）。"""
    heads = list(re.finditer(u"(?m)^## R(\\d+) 状态（", text))
    if not heads:
        return None
    head = max(heads, key=lambda m: int(m.group(1)))
    body = text[head.start():]
    nxt = re.search(u"(?m)^## R\\d+ (状态|补记)（", body[1:])
    return body[:nxt.start() + 1] if nxt else body


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--state", default=pre.STATE)
    args = ap.parse_args(argv)
    if not selfcheck():
        print(u"INSTRUMENT_QUOTE_RESULT=red 原因=尺瞎了（合成对照没响）")
        return 1
    text = io.open(args.state, encoding=u"utf-8", errors=u"replace").read()
    _, where = pre.locate(text)
    print(where)
    section = newest_section(text)
    if section is None:
        print(u"INSTRUMENT_QUOTE_RESULT=not-run 原因=切不到本轮那一节")
        return 2
    tables = load_tables()
    arms = dict((t, load_arms(t)) for t in tables)
    lines = [l for l in section.split(u"\n") if QUOTE.search(l)]
    if not lines:
        print(u"INSTRUMENT_QUOTE 扫描面=0 ⇒ no-quote-lines（本轮台账没抄仪器行；"
              u"这一维今天**没判**，不是"
              u"抄得都对）")
        print(u"INSTRUMENT_QUOTE_RESULT=ok 扫描面=0")
        return 0
    rows = judge_lines(lines, tables, arms)
    reds = sum(1 for _, _, p in rows if p)
    for name, quoted, problems in rows:
        print(u"  引用 %s ｜%s｜ ⇒ %s" % (name, quoted, u"；".join(problems) if problems else u"ok"))
    print(u"INSTRUMENT_QUOTE 扫描面=%d 引用=%d 红=%d 名册=%d 无刀号可查的表=%d"
          % (len(lines), len(rows), reds, len(tables),
             sum(1 for t in tables if not arms.get(t))))
    if reds:
        print(u"INSTRUMENT_QUOTE_RESULT=red ⇒ 抄错了行就是给台账贴了一张指向别的对象的证人")
        return 1
    print(u"INSTRUMENT_QUOTE_RESULT=ok")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
