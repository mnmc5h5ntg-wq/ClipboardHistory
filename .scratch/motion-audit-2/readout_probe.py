#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R370 / BACKLOG 432 第一刀：空刀探测（只对声明了 READOUT 的表生效）。

现场（R368 的 M906）：落刀之后 `HIDDEN_ARMS rot=33 抽不出=6 已声明=6` **一个数都没动**，
判据也没红（ESCAPED）。旧判法只会说"这刀没咬住"，分不清是「针找错对象」还是「这行代码对今天的语料没有作用」。
这一支把后者变成有名字的第四态：

  EMPTY_KNIFE   落刀前后读数一字不差，且判据没红  ⇒ 刀是空的（黑名单：命中一次也不等于有对象）
  READOUT_BLIND 落刀前后读数一字不差，但判据红了  ⇒ 红不是这条读数引起的（只印，不判死）

读数拿不到时返回 None，`four_state` 原样返回旧判词 —— 「没读到」不许冒充「没变化」。
"""
import subprocess


def capture(cmd, key, cwd=None, env=None):
    """跑一次读数命令，返回第一条包含 key 的行（strip）；一行都没有返回 None。"""
    proc = subprocess.run(cmd, cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    for line in text.splitlines():
        if key in line:
            return line.strip()
    return None


def four_state(verdict, before, after):
    u"""EMPTY_KNIFE 只在「两臂读数都可读且全等」时成立；CAUGHT 那半只降级成 READOUT_BLIND。"""
    if before is None or after is None or before != after:
        return verdict
    if verdict in ("ESCAPED", "WRONG_CELL"):
        return "EMPTY_KNIFE"
    if verdict == "CAUGHT":
        return "READOUT_BLIND"
    return verdict


def summarize(kinds):
    return {
        "caught": kinds.count("CAUGHT"),
        "empty": kinds.count("EMPTY_KNIFE"),
        "blind": kinds.count("READOUT_BLIND"),
        "escaped": sum(1 for k in kinds if k in ("ESCAPED", "WRONG_CELL")),
        "not_run": sum(1 for k in kinds if k in ("NOT_RUN", "RESTORE_FAILED")),
    }
