#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成表（静态抽不出候选）：臂是推导出来的，needle 藏在 lambda 里 ⇒ 必须被算成「抽不出」而不是"没问题"。"""

ROOT = "ClipboardHistory"


def _mk(i):
    return ("M9%02d" % i, "scripts/hidden_arms.py", (lambda: u"a" * 40), u"b", u"抽不出候选")


ARMS = [_mk(i) for i in range(1)]
