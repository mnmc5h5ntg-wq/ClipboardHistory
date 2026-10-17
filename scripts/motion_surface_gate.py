#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按表面清账表的闸门：**每一格要么有结论，要么被数成未清账**（R127 / 阶段二收尾）。

为什么要有它（目标原文）：阶段二要求「每一个元素/文字段/可动部件都要重新判断加动效是否有积极作用，
有作用才加，无作用或有害就写明理由不加」。127 轮下来这些判断散在 `AGENT_UI_AUDIT.md` 的各轮正文里，
没有任何东西能回答「哪个表面、哪个状态还没判过」—— 而"散在正文里"与"没做"在复核时是同一个样子。
这张表把答案变成数据，并让这个区别可判：

  DUP_KEY        同一个 (表面, 状态) 出现两行 ⇒ 红。两行的理由迟早会互相矛盾，而读的人只看第一行。
  UNKNOWN_CELL   某行的表面或状态不在名册里 ⇒ 红（改名要两边一起改，否则那格静默消失）。
  BAD_VERDICT    verdict 不在词表里 ⇒ 红（"看着像结论的字符串"不算结论）。
  REASONLESS     理由为空或短于 20 字 ⇒ 红。**没理由的 not-added 就等于还没决定**。
  EVIDENCELESS   证据指针为空 ⇒ 红（理由要能被复查：哪一轮、哪个 BACKLOG、哪个文件）。
  BELOW_FLOOR    行数低于 `floor_rows` ⇒ 红。地板只准升不准降（`testHistoryStoreStaysThin` 同一族：
                 会红的必须是单调量；均值与区间都被证伪过）。
  FLOOR_LIES     `floor_rows` 大于实际行数 ⇒ 红（把地板写成愿望，就是给自己留一张免检牌）。

未覆盖的格子**不红**，但必须被数出来（`MOTION_LEDGER 未清账=k`）：
清账是进度，不是及格线 —— 假装 162 格都判过，比承认只判了 18 格更坏。

用法：PYTHONUTF8=1 python3 scripts/motion_surface_gate.py [--path docs/motion_surface_ledger.json]
退出码：0 = 全部行合法；1 = 有任何一格不合法（逐条打印）；2 = 文件或 JSON 读不到。
"""
import argparse
import io
import json
import os
import sys

MIN_REASON = 20


def check(data):
    """返回 [(代码, 说明)]；空列表 = 全部合法。"""
    problems = []
    verdicts = data.get("verdicts") or []
    surfaces = data.get("surfaces") or []
    states = data.get("states") or []
    rows = data.get("rows") or []
    floor = data.get("floor_rows")
    if not verdicts or not surfaces or not states:
        problems.append(("BAD_TABLE", "verdicts / surfaces / states 三个名册都不许为空"))
    if not isinstance(floor, int):
        problems.append(("BAD_TABLE", "floor_rows 必须是整数"))
    elif floor > len(rows):
        problems.append(("FLOOR_LIES",
                         "floor_rows=%d 大于实际行数 %d ⇒ 地板写成了愿望" % (floor, len(rows))))
    seen = set()
    for i, row in enumerate(rows):
        surface = row.get("surface", "")
        state = row.get("state", "")
        where = "第 %d 行（%s × %s）" % (i + 1, surface or "?", state or "?")
        if surface not in surfaces:
            problems.append(("UNKNOWN_CELL", "%s：表面不在名册里" % where))
        if state not in states:
            problems.append(("UNKNOWN_CELL", "%s：状态不在名册里" % where))
        key = (surface, state)
        if key in seen:
            problems.append(("DUP_KEY", "%s：这个组合出现了不止一次" % where))
        seen.add(key)
        if row.get("verdict") not in verdicts:
            problems.append(("BAD_VERDICT", "%s：verdict=%r 不在词表 %s 里"
                             % (where, row.get("verdict"), verdicts)))
        reason = (row.get("reason") or "").strip()
        if len(reason) < MIN_REASON:
            problems.append(("REASONLESS", "%s：理由为空或短于 %d 字（没理由的 not-added 等于没决定）"
                             % (where, MIN_REASON)))
        if not (row.get("evidence") or "").strip():
            problems.append(("EVIDENCELESS", "%s：没有证据指针（哪一轮 / 哪个 BACKLOG / 哪个文件）" % where))
    if isinstance(floor, int) and len(rows) < floor:
        problems.append(("BELOW_FLOOR", "行数 %d 低于地板 %d ⇒ 清账只能往前不能往后"
                         % (len(rows), floor)))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="docs/motion_surface_ledger.json")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        print("MOTION_LEDGER_NOT_RUN 文件不存在（%s）⇒ 记为没跑，不算通过" % args.path)
        return 2
    try:
        data = json.load(io.open(args.path, encoding="utf-8"))
    except ValueError as exc:
        print("MOTION_LEDGER_NOT_RUN JSON 读不出来：%s" % exc)
        return 2
    cells = len(data.get("surfaces") or []) * len(data.get("states") or [])
    rows = data.get("rows") or []
    counts = {}
    for row in rows:
        counts[row.get("verdict") or "?"] = counts.get(row.get("verdict") or "?", 0) + 1
    dist = " ".join("%s=%d" % (k, counts[k]) for k in sorted(counts))
    print("MOTION_LEDGER 表面=%d 状态=%d 格子=%d 已清账=%d 未清账=%d 地板=%s"
          % (len(data.get("surfaces") or []), len(data.get("states") or []), cells, len(rows),
             max(0, cells - len(rows)), data.get("floor_rows")))
    print("MOTION_LEDGER_VERDICTS %s" % (dist or "无"))
    problems = check(data)
    for code, msg in problems:
        print("MOTION_LEDGER_%s %s" % (code, msg))
    print("MOTION_LEDGER_RESULT=%s 不合法格=%d（未清账不算不合法，它只是进度）"
          % ("ok" if not problems else "red", len(problems)))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
