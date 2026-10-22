#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACKLOG 353：产品面「连续零改动的轮数」只能由 git 派生，台账短语一律不作数。

为什么要有这一支（R298 现读，不是假想）：同一件事在台账里有**四种形状**，数出来四个不同的数 ——
「产品文件 N 个」9 节、「产品 N 文件」140 节、「N 个产品文件」10 节、其余 137 节根本没有这句话
（`AGENT_VISUAL_ITERATION.md` 共 296 节）。按其中一种形状数得 7，按另一种数得 8，而
`AGENT_STATE.md` 写着「第十一轮」；报告 §13 里那句「上一次落到 Sources 的改动是 R263 的收藏星字形墨」
**是假的** —— `git log -- ClipboardHistory/Sources/` 现读的最后一次是 2f8b1e0（R290 / 第 289 轮），
R263 之后还有 R275、R289、R290 三笔产品改动。短语数的是「我有没有在本轮正文里写下这句话」，
不是「产品有没有动」。

所以这一支把这一格改成**唯一的取数口**：
① `derive()` 从 git 现读：最后一次动 `ClipboardHistory/Sources/` 的那一笔、它 subject 里的轮次标签、
   `AGENT_UI_AUDIT.md` 里最大的「第 N 轮」节 ⇒ 连续零改动轮数 = 后者 − 前者；
② `check_ledger()` 要求台账那一格**等于**派生值，并且**同一格引用本命令**（`scripts/product_streak.py`）——
   手抄一个数、或者按短语数，都会红；
③ 派生不出来就红，不许给默认值：subject 里轮次标签缺失/多义、标签与 diff 打架
   （有更新的 Sources 改动却没被 `log -1` 选中）、Sources 之后仍有产品提交、节号解析不到 ——
   全部写成 problems 并 exit 1（「算不出来必须响」，R102 那一课）。

用法：`python3 scripts/product_streak.py`（只印读数）
      `python3 scripts/product_streak.py --check`（再对账台账的两格，不印 OK 就 exit 1）
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

# 台账里这一格的**唯一合法形状**（报告 §13 与 STATE 各一格；两种形状都要带引用）
CELL_REPORT = re.compile(u"产品面连续零改动轮数[ \\t]*=[ \\t]*\\*\\*(\\d+)\\*\\*")
CELL_STATE = re.compile(u"连续零改动[ \\t]*\\*\\*(\\d+)\\*\\*[ \\t]*轮")


def git(*args):
    proc = subprocess.Popen([u"git"] + list(args), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return out.decode("utf-8", "replace"), proc.returncode


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def rounds_in_subject(subject):
    """subject 里出现的「第 N 轮」标签集合；一个干净的 subject 只该有一个值。"""
    return sorted(set(int(x) for x in re.findall(u"第 (\\d+) 轮", subject)))


def derive():
    """返回 (读数 dict, problems 列表)。problems 非空 ⇒ 这一格派生不出来，不许编一个数。"""
    problems = []
    info = {}

    sha, rc = git("log", "-1", "--format=%H", u"--", SOURCES)
    sha = sha.strip()
    if rc != 0 or not sha:
        return info, [u"git log -1 -- %s 取不到（rc=%s）⇒ 无从派生" % (SOURCES, rc)]
    one, _ = git("log", "-1", "--date=short", "--format=%h|%ad|%s", sha, u"--", SOURCES)
    parts = one.strip().split(u"|", 2)
    if len(parts) != 3:
        return info, [u"最后一笔产品提交的正文形状不符：%r" % (one.strip()[:120],)]
    short, date, subject = parts
    info.update(last_sha=short, last_date=date, last_subject=subject)

    labels = rounds_in_subject(subject)
    if len(labels) != 1:
        problems.append(u"最后一笔产品提交 subject 里的轮次标签不是唯一值：%s ⇒ "
                        u"这一格不许按猜的数写" % (labels or u"没有「第 N 轮」",))
        return info, problems
    last_round = labels[0]
    info.update(last_round=last_round)

    # 打架检测：`log -1` 是按 diff 选的，若**更早**的产品提交里出现更大的轮次标签，
    # 说明标签与 diff 说的是两件事（标签手抄错了），此时派生值不可信。
    hist, _ = git("log", "-40", "--format=%h %s", u"--", SOURCES)
    for line in hist.splitlines()[1:]:
        earlier = rounds_in_subject(line)
        if earlier and earlier[-1] > last_round:
            problems.append(u"更早的产品提交 %s 的标签（第 %d 轮）比 diff 选中的最后一笔"
                            u"（第 %d 轮）还新 ⇒ 标签与 diff 打架，先修标签再谈这一格"
                            % (line.split()[0], earlier[-1], last_round))

    try:
        sections = [int(x) for x in re.findall(u"(?m)^## 第 (\\d+) 轮", rd(UI_AUDIT))]
    except (IOError, OSError) as exc:
        return info, problems + [u"读不到 %s：%s" % (UI_AUDIT, exc)]
    if not sections:
        return info, problems + [u"%s 里解析不到任何「## 第 N 轮」节 ⇒ 分母是空的" % UI_AUDIT]
    max_round = max(sections)
    info.update(max_round=max_round, sections=len(sections))
    if last_round > max_round:
        problems.append(u"最后一笔产品提交标到第 %d 轮，而 %s 最大节只有第 %d 轮 ⇒ 节号滞后，"
                        u"先补台账再谈这一格" % (last_round, UI_AUDIT, max_round))

    after, _ = git("rev-list", "--count", u"%s..HEAD" % sha)
    sources_after, _ = git("rev-list", "--count", u"%s..HEAD" % sha, u"--", SOURCES)
    info.update(commits_after=after.strip(), sources_after=sources_after.strip())
    if sources_after.strip() != u"0":
        problems.append(u"%s..HEAD 之间仍有 %s 笔动过 %s ⇒ 选中的「最后一笔」不对，尺坏了"
                        % (short, sources_after.strip(), SOURCES))

    info.update(streak=max_round - last_round)
    return info, problems


def _state_top_section(text):
    """STATE 是**新节在上**，所以当前轮 = 第一个 `## Rnnn 状态（` 那一节（取末会读到最老一节，R223 那一课）。"""
    starts = [m for m in re.finditer(u"(?m)^## R\\d+ 状态（", text)]
    if not starts:
        return None
    body = text[starts[0].start():]
    nxt = re.search(u"(?m)^## ", body[len(starts[0].group(0)):])
    return body[:len(starts[0].group(0)) + nxt.start()] if nxt else body


def _cells(label, text, rx):
    """在一篇文本里找那一格：形状要在、数要唯一、同一段落要引用本命令。"""
    bad = []
    hits = list(rx.finditer(text))
    if not hits:
        return [u"%s：找不到「%s」这一格 —— 缺席与写对不同形，算红" % (label, rx.pattern)], None
    if len(hits) > 1:
        bad.append(u"%s：同一格里出现 %d 个候选数 %s ⇒ 两处必须同值，先对账"
                   % (label, len(hits), [h.group(1) for h in hits]))
    for hit in hits:
        para = text[max(0, text.rfind(u"\n", 0, hit.start()) + 1):
                    text.find(u"\n", hit.end())]
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


def main(argv):
    info, problems = derive()
    if problems:
        for p in problems:
            sys.stderr.write(u"PRODUCT_STREAK_REFUSED " + p + u"\n")
        return 1
    sys.stdout.write(u"PRODUCT_STREAK last=%s date=%s last_round=%d ui_audit_max_round=%d "
                     u"sections=%d commits_after=%s sources_after=%s streak=%d\n"
                     % (info["last_sha"], info["last_date"], info["last_round"],
                        info["max_round"], info["sections"], info["commits_after"],
                        info["sources_after"], info["streak"]))
    sys.stdout.write(u"PRODUCT_STREAK_LAST_SUBJECT " + info["last_subject"] + u"\n")
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
