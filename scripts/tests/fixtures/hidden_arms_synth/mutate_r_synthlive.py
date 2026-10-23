#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成表（活针）：needle 走变量，必须在盘上恰好命中一次 ⇒ 这一臂算「可判且不腐烂」。"""

ROOT = "ClipboardHistory"
NEEDLE = u'def main(argv):'
REPL = u'def main(argv):  # MUTANT'

ARMS = [
    ("M900", "scripts/hidden_arms.py", NEEDLE, REPL, u"活针必须被算成可判"),
]
