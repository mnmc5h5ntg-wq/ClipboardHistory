#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成表（死针）：needle 在仓库里一个字符都找不到 ⇒ 必须被算成 rot（这就是 364 要能响的那种坏）。"""

ROOT = "ClipboardHistory"
NEEDLE = u"ZZZ_THIS_NEEDLE_DOES_NOT_EXIST_ON_DISK_zzz"
REPL = u"whatever_else_not_on_disk_zzz"

ARMS = [
    ("M901", "scripts/hidden_arms.py", NEEDLE, REPL, u"腐烂针必须被点名"),
]
