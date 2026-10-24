#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""把 `AGENT_FINAL_REPORT.md` 里「最后一次动到 `Sources/` 的轮次」那一格改成**派生**的。

为什么要有这一支（R335 现读，红在 runner 上而不是红在本机上）：
R334 动了两个产品文件并落了盘，而我的台账生成器刷了报告的**三处**计数器
（刀号区间、决定台账 D 号、变异表数），**漏了这一张**。守卫
`test_final_report_headline.test_the_sources_cell_agrees_with_git` 在 runner 上抓到：
「那一格写 commit `84c5468`，而 git 说最近动源码的是 `5d1c246`（R334 代码半…）⇒ 动过源码却没刷这张格」。
本机当时是绿的 —— 因为我在 commit 之后没有再跑电池，而这一格**只有 commit 之后才会红**。
⇒ 一条流程教训（写进 Skill）：**报告里每一张手抄格都要有一个取数口**；
  没有取数口的手抄格，早晚由 runner 替你记得。

用法：
  python3 scripts/report_sources_cell.py            # 只印：现在写的是什么、git 说是什么
  python3 scripts/report_sources_cell.py --write    # 把那一格按 git 重写（幂等）
退出码：0=两边一致（或已重写）；1=不一致且没给 --write，或 git 读不到；2=用法/解析错。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
SOURCES = os.path.join("ClipboardHistory", "Sources")

# 那一格的形状（守卫认的是 `**R<NNN>**（commit `<sha>`）`，所以重写必须保持同一形状）。
CELL = re.compile(u"(?m)^\\| 最后一次动到 `Sources/` 的轮次 \\|(.*)\\|$")
BADGE = re.compile(u"^R(\\d{2,4})\\b")


def git_rows(limit=5):
    out = subprocess.run([u"git", u"log", u"-%d" % limit, u"--format=%h%x09%s", u"--", SOURCES],
                         cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        return None
    rows = []
    for line in out.stdout.decode(u"utf-8", u"replace").splitlines():
        parts = line.split(u"\t")
        if len(parts) != 2:
            continue
        sha, subject = parts
        m = BADGE.match(subject)
        rows.append((sha, int(m.group(1)) if m else None, subject))
    return rows


def current_cell(text):
    m = CELL.search(text)
    if not m:
        return None
    claimed = re.search(u"\\*\\*R(\\d+)\\*\\*（commit `([0-9a-f]{7,40})`）", m.group(1))
    return (int(claimed.group(1)), claimed.group(2)) if claimed else (None, None)


def build_row(rows):
    u"""按 git 派生那一格的正文。第二笔（"上一笔"）也来自同一次 `git log`，不手抄。"""
    sha, rnd, subject = rows[0]
    files = re.search(u"产品 (\\d+) 文件", subject)
    n = files.group(1) if files else u"?"
    kind = u"本轮是**产品轮**" if rnd is not None and (files and int(files.group(1)) > 0) else u"本轮没动源码"
    tail = u""
    if len(rows) > 1 and rows[1][0] != sha:
        tail = u"上一笔动 `Sources/` 的是 R%s（`%s`）。" % (
            (u"%d" % rows[1][1]) if rows[1][1] is not None else u"号未读", rows[1][0])
    return (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— %s（`Sources/` %s 个文件）；"
            u"这一格登记的是仓库里**最近一笔动过源码的提交**，由 `scripts/report_sources_cell.py --write` "
            u"从 `git log -- %s` 派生（不是手抄），改了什么以 `AGENT_UI_AUDIT.md` 里 R%d 那一节为准。%s|"
            % (rnd if rnd is not None else 0, sha, kind, n, SOURCES, rnd if rnd is not None else 0, tail))


def main(argv=None):
    ap = argparse.ArgumentParser(prog=u"report_sources_cell.py", add_help=True,
                                 description=u"报告里「最后一次动到 Sources/」那一格的唯一取数口")
    ap.add_argument(u"--write", action=u"store_true", help=u"按 git 重写那一格（幂等）")
    args = ap.parse_args(argv)

    rows = git_rows()
    if not rows:
        sys.stdout.write(u"SOURCES_CELL_REFUSED git log 读不到动过 Sources 的提交 ⇒ 这一格没有对象\n")
        return 1
    text = io.open(REPORT, encoding=u"utf-8").read()
    claimed = current_cell(text)
    if claimed is None:
        sys.stdout.write(u"SOURCES_CELL_REFUSED 报告里找不到那一格（形状变了？先回守卫里抄正则）\n")
        return 2
    want = build_row(rows)
    hits = CELL.findall(text)
    if len(hits) != 1:
        sys.stdout.write(u"SOURCES_CELL_REFUSED 那一格命中 %d 次，重写会改错地方\n" % len(hits))
        return 2
    same = (claimed[0] == rows[0][1] and (claimed[1] or u"").startswith(rows[0][0][:7]))
    sys.stdout.write(u"SOURCES_CELL 账上=R%s/`%s` git=R%s/`%s` 一致=%s\n"
                     % (claimed[0], claimed[1], rows[0][1], rows[0][0], u"是" if same else u"否"))
    if same:
        return 0
    if not args.write:
        sys.stdout.write(u"  要写：python3 scripts/report_sources_cell.py --write\n")
        return 1
    new_text = CELL.sub(lambda m: want, text, count=1)
    if new_text == text:
        sys.stdout.write(u"SOURCES_CELL_REFUSED --write 之后文本没变（替换没生效）\n")
        return 2
    io.open(REPORT, u"w", encoding=u"utf-8").write(new_text)
    after = current_cell(io.open(REPORT, encoding=u"utf-8").read())
    ok = after[0] == rows[0][1] and (after[1] or u"").startswith(rows[0][0][:7])
    sys.stdout.write(u"SOURCES_CELL_WRITTEN 复核=%s\n" % (u"一致" if ok else u"仍不一致"))
    return 0 if ok else 2


if __name__ == u"__main__":
    sys.exit(main())
