#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43 台账的第二半（STATE / CHANGELOG / 迭代日志 / BACKLOG / 人工清单）。
   第一半（第 45 轮正文 + D-102）已由 patch_r43_ledgers.py 写入，这里不重复。"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")

first = io.open(".scratch/motion-audit-2/patch_r43_ledgers.py", encoding="utf-8").read()
STATE = first.split("STATE = '''", 1)[1].split("'''", 1)[0]
CHANGELOG = first.split("CHANGELOG = '''", 1)[1].split("'''", 1)[0]
VISUAL = first.split("VISUAL = '''", 1)[1].split("'''", 1)[0]
BACKLOG_CLOSE = ("62. **「导出反馈数据」同一件事有两条通道，而失败那条又是系统英文原文（R42 复核 BACKLOG 53 时看到，未修）**：",
                 "62. **「导出反馈数据」同一件事有两条通道，而失败那条又是系统英文原文（R42 复核 BACKLOG 53 时看到）· 已收口（R43 / D-102）**：")
BACKLOG_NOTE = ("    注意 BACKLOG 60 里\"导出失败与'导出 N 条'两条横幅互相矛盾\"是**同一片代码**，一并判。",
                "    注意 BACKLOG 60 里\"导出失败与'导出 N 条'两条横幅互相矛盾\"是**同一片代码**，一并判。\n"
                "    **R43 收口记录**：判完发现不是一处而是**三处**（导出反馈 / 导出存档 / 导入存档都在拼\n"
                "    `localizedDescription`），措辞集中进 `Utilities/ReceiptWordings.swift`，模态那条删掉，\n"
                "    原文一律进日志；同时补了一条**夹具不许手写回执文案**的按族判据 ——\n"
                "    `receipt-line` 那张帧从 R14 起画的产品根本没说过（全仓 grep 无此文案），\n"
                "    换成真文案后 `contentMustFit` 又当场红出第二件事：那张帧一直在裁自己（56 → 72pt）。\n"
                "    与 BACKLOG 60 那条\"两条横幅互相矛盾\"是同一片代码，那条仍开放（它问的是横幅之间，不是模态）。")
BACKLOG_65 = first.split("BACKLOG_65 = '''", 1)[1].split("'''", 1)[0]
MANUAL = first.split("MANUAL = '''", 1)[1].split("'''", 1)[0]


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


with io.open("AGENT_STATE.md", "a", encoding="utf-8") as f:
    f.write(STATE.rstrip("\n") + "\n")

patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])

with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
    f.write("\n" + VISUAL)

patch("AGENT_BACKLOG.md", [BACKLOG_CLOSE, BACKLOG_NOTE])
with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
    f.write(BACKLOG_65)

with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
    f.write("\n" + MANUAL)

print("R43 剩余台账已写入")
