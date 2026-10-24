#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACKLOG 353：产品面「连续零改动的轮数」只能由 git 派生，台账短语一律不作数。

为什么要有这一支（R298 现读，不是假想）：同一件事在台账里有**四种形状**，数出来四个不同的数 ——
「产品文件 N 个」9 节、「产品 N 文件」140 节、「N 个产品文件」10 节、无陈述 137 节
（`AGENT_VISUAL_ITERATION.md` 共 296 节）。按 A 数得 7、按 B 数得 8，而 `AGENT_STATE.md` 写「第十一轮」。
更要紧的是报告 §13 那句「上一次落到 Sources 的改动是 R263」**是假的** —— git 现读 R263 之后
还有 R275 / R289 / R290。短语统计量的是「我有没有在本轮正文里写下这句话」，不是「产品有没有动」。

R300 补的第二课（与 355 同一族）：**这一格是"时点量"，不是"当前量"。**
代码半先提交、台账半后提交，于是在写台账那一次之前，`git log -1 -- Sources` 已经指向本轮那一笔，
而台账最大节还停在上一轮 —— 拿"当前"去判历史格，会把上一轮写对的数判成假红。
所以取数口径是 **as-of**：某一轮 N 的格 = N − （标签 **< N** 的最后一笔产品提交的轮次标签）。
R334 把 `≤` 换成了 `<`，理由写在 `streak_at` 的 docstring 里（同一格不许在 commit 前后答两个数）。

三条硬规矩：
① 派生不出来就 exit 1、不给默认值（subject 里「第 N 轮」缺失且第二个来源（台账节标题里的
   同一段 U 区间）也没唯一命中、节号解析不到、最大节之前一笔产品提交都没有 —— 全部写成 problems）；
② 台账那一格必须**等于** as-of 派生值，且**同一行必须引用本命令**（数对但没引用也红）；
③ 数**缺席**算红，不算通过（R140 的空对账）。

用法：`python3 scripts/product_streak.py`（只印读数）
      `python3 scripts/product_streak.py --check`（再对账台账的两格，不 OK 就 exit 1）
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join("ClipboardHistory", "Sources")
UI_AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
CITE = u"scripts/product_streak.py"

CELL_REPORT = re.compile(u"产品面连续零改动轮数[ \\t]*=[ \\t]*\\*\\*(\\d+)\\*\\*")
CELL_STATE = re.compile(u"连续零改动[ \\t]*\\*\\*(\\d+)\\*\\*[ \\t]*轮")
LABEL = re.compile(u"第 (\\d+) 轮")


def git(*args):
    proc = subprocess.Popen([u"git"] + list(args), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = proc.communicate()
    return out.decode("utf-8", "replace"), proc.returncode


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def rounds_in_subject(subject):
    """subject 里出现的「第 N 轮」标签集合；一个干净的 subject 只该有一个值。"""
    return sorted(set(int(x) for x in LABEL.findall(subject)))


U_RANGE = re.compile(u"U-(\\d{3,4})…U-(\\d{3,4})")
SECTION_TITLE = re.compile(u"(?m)^## 第 (\\d+) 轮.*$")


def ledger_round_by_urange():
    """台账节标题里那一段 U 号 = 「第 N 轮」的**第二个来源**：{区间 → set(轮次)}。

    为什么要有它（R334 / BACKLOG 398 / D-329）：已 push 的提交不许 amend，而 R333 那一笔
    产品提交的 subject 恰好缺了「第 N 轮」⇒ as-of 口径没有分界，`--streak-for` 派生出 **15**，
    而真值是 **1**（R333 是产品轮）。这不只是"红"，是**一个看起来像结论的错数**：
    豁免如果只买"不红"，下一轮读到 15 的人会拿它当账。
    所以这里不写 sha→轮次的手抄表，而是**派生**：U 区间是那一笔提交自己写的，
    而台账每一节的标题都写着同一区间 ⇒ 两边对上就有轮次。对不上（区间多义 / 台账没有那一节 /
    subject 里出现两段以上区间）一律 `None` ⇒ 照旧红。**没有退场条件要管，因为它不是豁免。**
    """
    out = {}
    try:
        text = rd(UI_AUDIT)
    except (IOError, OSError):
        return out
    for m in SECTION_TITLE.finditer(text):
        n = int(m.group(1))
        for a, b in set(U_RANGE.findall(m.group(0))):
            out.setdefault((int(a), int(b)), set()).add(n)
    return out


def round_from_uranges(subject, table):
    """subject 里**恰好一段** U 区间、且它在台账里**恰好命中一节** ⇒ 那一节的轮次；否则 None。

    三种歧义各给 None（不许猜）：多段区间（读者不知道哪一段是本轮的）、
    区间在台账里出现 0 次（引用了不存在的节）、出现 >1 节（同号两节，R304 那一族的形状）。
    """
    ranges = sorted(set(U_RANGE.findall(subject)))
    if len(ranges) != 1:
        return None
    hits = table.get((int(ranges[0][0]), int(ranges[0][1])))
    if hits is None or len(hits) != 1:
        return None
    return list(hits)[0]


def label_came_from_ledger(subject, label):
    """这一行的标签是不是"从台账 U 区间派生来的"（用于把 recovered 数印出来，不参与判定）。"""
    return label is not None and len(rounds_in_subject(subject)) != 1


def product_commits(limit=400):
    """动过产品目录的提交，按时间从新到旧：[(sha, label 或 None, 短 sha, 日期, subject)]。

    标签的第一来源是 subject 里唯一的「第 N 轮」；缺它时**不放过、也不手补**，
    而是问第二个来源（台账节标题里的同一段 U 区间，见 `ledger_round_by_urange`）。
    两个来源都给不出 ⇒ label=None，由 `derive()` 那三条出口去红。
    """
    out, rc = git("log", "-%d" % limit, "--date=short",
                  u"--format=%H%x09%h%x09%ad%x09%s", u"--", SOURCES)
    if rc != 0:
        return None
    table = None
    rows = []
    for line in out.splitlines():
        parts = line.split(u"\t")
        if len(parts) != 4:
            continue
        sha, short, date, subject = parts
        labels = rounds_in_subject(subject)
        label = labels[0] if len(labels) == 1 else None
        if label is None:
            if table is None:
                table = ledger_round_by_urange()
            label = round_from_uranges(subject, table)
        rows.append((sha, label, short, date, subject))
    return rows


def streak_at(round_n, rows):
    """第 round_n 轮那一格的答案：round_n − （标签 **< round_n** 的最后一笔产品提交的标签）。

    返回 (streak, 说明) 或 (None, 成因)。标签多义/缺失的提交会被跳过并记进说明 ——
    它们不配当分界，但也不许被当成"没有产品改动"。

    为什么是**严格小于**（R334 现读，口径改过一次）：原来是 `≤`，于是"本轮自己那一笔"
    一旦落进 git 就成了分界 —— 同一格在 commit 之前答 14、之后答 0，
    而这一格没写错，错的是口径：它把"**这一笔提交在不在**"当成了"这一轮改没改产品"。
    仓库里两种提交形状并存（代码半 + 账半两笔；也有整轮一笔，如 `117f45d`），
    `≤` 让答案依赖提交形状 ⇒ 换成 `<`：第 N 轮的分界 = **上一笔**产品轮，与本轮的账/码何时落盘无关。
    """
    unlabeled = 0
    for sha, label, short, date, subject in rows:
        if label is None:
            unlabeled += 1
            continue
        if label < round_n:
            return round_n - label, u"last=%s last_round=%d" % (short, label)
    return None, (u"标签 < 第 %d 轮的产品提交一笔都没有（跳过 %d 笔标签多义/缺失的）"
                  % (round_n, unlabeled))


def derive():
    """返回 (读数 dict, problems)。problems 非空 ⇒ 这一格派生不出来，不许编一个数。"""
    problems = []
    info = {}
    try:
        sections = [int(x) for x in re.findall(u"(?m)^## 第 (\\d+) 轮", rd(UI_AUDIT))]
    except (IOError, OSError) as exc:
        return info, [u"读不到 %s：%s" % (UI_AUDIT, exc)]
    if not sections:
        return info, [u"%s 里解析不到任何「## 第 N 轮」节 ⇒ 分母是空的" % UI_AUDIT]
    ledger_round = max(sections)
    info.update(ledger_round=ledger_round, sections=len(sections))

    rows = product_commits()
    if rows is None:
        return info, [u"git log -- %s 取不到 ⇒ 无从派生" % SOURCES]
    if not rows:
        return info, [u"%s 之前没有任何提交 ⇒ 这一格没有对象" % SOURCES]

    newest = rows[0]
    recovered = [r[2] for r in rows if label_came_from_ledger(r[4], r[1])]
    info.update(newest_sha=newest[2], newest_date=newest[3], newest_subject=newest[4],
                recovered=len(recovered), recovered_list=u",".join(recovered) or u"-",
                newest_label=(newest[1] if newest[1] is not None else u"无标签"))
    if newest[1] is None:
        problems.append(u"最新一笔产品提交的 subject 里没有唯一的「第 N 轮」标签，"
                        u"而第二个来源（台账节标题里同一段 U 区间，见 `ledger_round_by_urange`）"
                        u"也没命中：%s ⇒ as-of 口径没有分界，先补标签" % newest[4][:80])

    streak, note = streak_at(ledger_round, rows)
    if streak is None:
        problems.append(note)
        return info, problems
    info.update(streak=streak, note=note)

    # 打架检测：标签必须单调（更老的提交标着更新的轮次 ⇒ 标签是手抄错的）
    seen = None
    for sha, label, short, date, subject in rows:
        if label is None:
            continue
        if seen is not None and label > seen:
            problems.append(u"更老的产品提交 %s 标到第 %d 轮，比它之后的 %s（第 %d 轮）还新 ⇒ "
                            u"标签与时间打架，先修标签再谈这一格" % (short, label, seen, seen))
        seen = label
    return info, problems


def _state_top_section(text):
    """STATE 是**新节在上**，所以当前轮 = 第一个 `## Rnnn 状态（` 那一节（取末会读到最老一节，R223）。"""
    starts = [m for m in re.finditer(u"(?m)^## R\\d+ 状态（", text)]
    if not starts:
        return None
    body = text[starts[0].start():]
    nxt = re.search(u"(?m)^## ", body[len(starts[0].group(0)):])
    return body[:len(starts[0].group(0)) + nxt.start()] if nxt else body


def _cells(label, text, rx):
    bad = []
    hits = list(rx.finditer(text))
    if not hits:
        return [u"%s：找不到「%s」这一格 —— 缺席与写对不同形，算红" % (label, rx.pattern)], None
    if len(hits) > 1:
        bad.append(u"%s：同一格里出现 %d 个候选数 %s ⇒ 两处必须同值，先对账"
                   % (label, len(hits), [h.group(1) for h in hits]))
    for hit in hits:
        para = text[max(0, text.rfind(u"\n", 0, hit.start()) + 1):text.find(u"\n", hit.end())]
        if CITE not in para:
            bad.append(u"%s：那一格没引用 %s ⇒ 说明这个数是手抄的（或按短语数的）"
                       % (label, CITE))
    return bad, hits


def check_ledger(report_text, state_text, streak):
    """台账两格与派生值对账；返回 problems（空表 = 对得上）。"""
    problems, cells = _cells(u"AGENT_FINAL_REPORT.md", report_text, CELL_REPORT)
    if cells and any(c.group(1) != str(streak) for c in cells):
        problems.append(u"报告那一格写的是 %s，git 派生是 %d ⇒ 现读现取，别手抄"
                        % (u"/".join(c.group(1) for c in cells), streak))
    section = _state_top_section(state_text)
    if section is None:
        problems.append(u"AGENT_STATE.md：解析不到「## Rnnn 状态（」节 ⇒ 当前轮无从判定")
        return problems
    bad, cells = _cells(u"AGENT_STATE.md 当前轮", section, CELL_STATE)
    problems.extend(bad)
    if cells and any(c.group(1) != str(streak) for c in cells):
        problems.append(u"STATE 当前轮那一格写的是 %s，git 派生是 %d"
                        % (u"/".join(c.group(1) for c in cells), streak))
    return problems


def streak_for(round_n):
    """给第 round_n 轮的台账格用：那一格写的是「落盘之后」的数，所以按 as-of 现算。

    这是本命令唯一的"预测"入口，而它不预测任何事 —— as-of 口径下第 N 轮的答案只取决于
    标签 ≤ N 的最后一笔产品提交，与"账有没有落"无关。
    """
    rows = product_commits()
    if rows is None:
        return None, u"git log 取不到"
    return streak_at(int(round_n), rows)


def main(argv):
    if u"--streak-for" in argv:
        try:
            n = int(argv[argv.index(u"--streak-for") + 1])
        except (IndexError, ValueError):
            sys.stderr.write(u"PRODUCT_STREAK_USAGE --streak-for <轮次>\n")
            return 2
        streak, note = streak_for(n)
        if streak is None:
            sys.stderr.write(u"PRODUCT_STREAK_REFUSED " + note + u"\n")
            return 1
        sys.stdout.write(u"PRODUCT_STREAK_FOR round=%d streak=%d %s\n" % (n, streak, note))
        return 0
    info, problems = derive()
    if problems:
        for p in problems:
            sys.stderr.write(u"PRODUCT_STREAK_REFUSED " + p + u"\n")
        return 1
    sys.stdout.write(u"PRODUCT_STREAK ledger_round=%(ledger_round)d streak=%(streak)d "
                     u"sections=%(sections)d as_of=%(note)s newest=%(newest_sha)s "
                     u"newest_round=%(newest_label)s date=%(newest_date)s "
                     u"标签补自台账=%(recovered)d(%(recovered_list)s)\n" % info)
    sys.stdout.write(u"PRODUCT_STREAK_LAST_SUBJECT " + info[u"newest_subject"] + u"\n")
    if u"--check" in argv:
        probs = check_ledger(rd(os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")),
                             rd(os.path.join(ROOT, u"AGENT_STATE.md")), info["streak"])
        if probs:
            for p in probs:
                sys.stderr.write(u"PRODUCT_STREAK_LEDGER_STALE " + p + u"\n")
            return 1
        sys.stdout.write(u"PRODUCT_STREAK_LEDGER_OK streak=%d 两格均由本命令派生并带引用\n"
                         % info["streak"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
