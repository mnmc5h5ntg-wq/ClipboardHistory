#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R247 的**影子**变异表：只把臂号与 needle 交给预检名册；执行在 `mutate_r247.sh`（对象=CI 抓帧那一步的正文）。

与 R245 同一形状（D-231）：臂内容存成 `arms_r249/MNNN.old|.new` 文件，路径一律相对 ROOT，
所以这张表被 import 时只读文件、不跑测试 —— `mutate_needle_precheck.py` 是 import 每张表的。
"""
import io, os
ROOT = '/Users/wangziyi/Codex_Project0'
MANI = os.path.join(ROOT, ".scratch/motion-audit-2/arms_r249/manifest.tsv")


def load():
    rows = []
    for line in io.open(MANI, encoding="utf-8").read().splitlines():
        if not line.strip():
            continue
        mid, kind, rel, oldf, newf, want, why = line.split("\t")
        rows.append((mid, why, kind, rel, io.open(os.path.join(ROOT, oldf), encoding="utf-8").read(),
                     io.open(os.path.join(ROOT, newf), encoding="utf-8").read(), want))
    return rows

ARMS = load()
