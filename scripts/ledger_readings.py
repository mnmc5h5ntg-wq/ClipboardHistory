#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R309 / BACKLOG 348 的「数字对不对」那一格：验证链日志的读数只能按**小节**取，并且必须过恒等式闸门。

为什么要有这一支（R308 实测换来的，不是假想）：台账生成器里那句
`re.findall("Executed (N) tests, …", chain)[-1]` 是在**整份**日志里取末，
而那份日志最后一行 `Executed` 属于 `### CAPTURE 结论行补记`（UICaptureTests 那一卷 = 92 格、0 失败）。
于是 ITER / CHANGELOG / STATE 三本一度一起写着「全量卷 Executed 92」，而真读数是 934 / 44 skip / 0。
当时 `FULL_FAIL != 0 就拒写` 那道门**完全不响** —— 抄来的那一行恰好是 0 失败。
也就是说：一道只在「红」时响的门，对「抄错但抄到一行绿的」是盲的。所以这里把三件事写成会红的纯函数：

① 取数按 `### 小节` 切片 —— 跳遍残留不许互相冒充；
② 恒等式闸门 —— 全量卷的格数不可能比同一份日志里任何一卷还小（抄到子集时这一格必响）；
③ 每一跑各自记账 —— 早先那一跑的红要原样报出来，不许被「最后一跑绿了」抹掉。

顺序也承重：`re.split` 只吃掉分隔符 ⇒ 小节标题与它的正文住在**同一个块**里，
正文要取本块去掉首行；取下一块拿到的是下一节的第一行（R309 写这一格时又踩了一次，
被 ② 当场抓住，七本一个字节都没落盘）。

用法：`python3 scripts/ledger_readings.py <验证链日志> [小节前缀]`（默认前缀 `FULL SUITE`）
结论行：`LEDGER_READINGS 小节=… 取用=… 其它最大=… 早先红=… 红=…`（「红」非 0 ⇒ exit 1）。
缺文件、读不到结论行、恒等式不符 —— 三种都算红，不算「没数据所以通过」。
"""
import io
import os
import re
import sys

EXEC_RX = re.compile(
    u"Executed (\\d+) tests?, with (?:(\\d+) tests? skipped and )?(\\d+) failures?")


def section_parts(text, prefix):
    """把日志按 `### <prefix>…` 切成 (小节标题, 小节正文)。"""
    chunks = re.split(u"(?m)^### ", text)
    out = []
    for blk in chunks[1:]:
        if blk.strip().startswith(prefix):
            bits = blk.split(u"\n", 1)
            out.append((bits[0].strip(), bits[1] if len(bits) > 1 else u""))
    return out


def suite_rows(text, prefix=u"FULL SUITE"):
    """每一小节一行结论；同一小节里出现两行**不一致**的结论 ⇒ 算红（哪一跑作数说不清）。"""
    rows, problems = [], []
    for title, body in section_parts(text, prefix):
        seen = []
        for m in EXEC_RX.finditer(body):
            if m.groups() not in seen:
                seen.append(m.groups())
        if not seen:
            continue
        if len(seen) > 1:
            problems.append((u"LEDGER_READINGS_SECTION_AMBIGUOUS",
                             u"小节「%s」里有 %d 行不一致的结论行：%s" % (title, len(seen), seen)))
            continue
        rows.append((title,) + seen[0])
    return rows, problems


def all_exec_counts(text):
    return [int(m.group(1)) for m in EXEC_RX.finditer(text)]


def pick_full_run(text, prefix=u"FULL SUITE"):
    """返回 (读数 dict, problems)。读数只描述「最后一跑」，早先那几跑的红另列，谁也不替谁作数。"""
    rows, problems = suite_rows(text, prefix)
    info = {u"rows": rows, u"pass_count": len(rows), u"title": None,
            u"run": None, u"skip": None, u"fail": None,
            u"other_max": max(all_exec_counts(text)) if all_exec_counts(text) else None,
            u"red_passes": []}
    if not rows:
        problems.append((u"LEDGER_READINGS_NO_SUITE_LINE",
                         u"日志里读不到任何「%s」小节的结论行 ⇒ 不许按「跑过了」写" % prefix))
        return info, problems
    title, run, skip, fail = rows[-1]
    info.update({u"title": title, u"run": run, u"skip": skip, u"fail": fail})
    if skip is None:
        problems.append((u"LEDGER_READINGS_SKIP_MISSING",
                         u"取用那一行（%s）读不到 skip 数 ⇒ 结论行的形状漂了" % title))
    if fail != u"0":
        problems.append((u"LEDGER_READINGS_LAST_PASS_RED",
                         u"最后一跑（%s）是 %s 朵红 ⇒ 台账不许把它写成 0" % (title, fail)))
    for t, r, s_, f_ in rows[:-1]:
        if f_ != u"0":
            info[u"red_passes"].append((t, f_))
    # 恒等式闸门：全量卷不可能比同一份日志里任何一卷小。
    if info[u"other_max"] is not None and int(run) < info[u"other_max"]:
        problems.append((u"LEDGER_READINGS_SUBSET_TAKEN_AS_FULL",
                         u"取用的全量卷是 %s 格，而日志里有一卷是 %s 格 ⇒ 全量卷不可能比单卷小，"
                         u"取数口拿到的是子集" % (run, info[u"other_max"])))
    return info, problems


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(u"USAGE ledger_readings.py <验证链日志> [小节前缀]\n")
        return 2
    path = argv[1]
    prefix = argv[2] if len(argv) > 2 else u"FULL SUITE"
    if not os.path.exists(path):
        sys.stderr.write(u"LEDGER_READINGS_REFUSED 日志不存在：%s ⇒ 缺产物算红，不算通过\n" % path)
        return 1
    with io.open(path, encoding="utf-8", errors="replace") as h:
        text = h.read()
    info, problems = pick_full_run(text, prefix)

    def dash(v):
        return u"-" if v is None else v

    sys.stdout.write(u"LEDGER_READINGS 小节前缀=%s 跑=%d 取用=%s 格数=%s skip=%s 失败=%s "
                     u"其它最大=%s 早先红=%d\n"
                     % (prefix, info[u"pass_count"], dash(info[u"title"]), dash(info[u"run"]),
                        dash(info[u"skip"]), dash(info[u"fail"]), dash(info[u"other_max"]),
                        len(info[u"red_passes"])))
    for t, f_ in info[u"red_passes"]:
        sys.stdout.write(u"LEDGER_READINGS_EARLIER_RED 小节=%s 失败=%s（原样留档，不抹）\n" % (t, f_))
    for code, msg in problems:
        sys.stdout.write(u"LEDGER_READINGS_RED %s %s\n" % (code, msg))
    return 1 if problems else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv))
