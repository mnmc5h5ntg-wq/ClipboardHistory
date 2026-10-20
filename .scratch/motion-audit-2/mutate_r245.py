#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R245 的**影子**变异表：只负责把臂号与 needle 交给预检名册，真跑在 mutate_r245.sh。

为什么要拆成两份（BACKLOG 283）：`swift test` / `python3 -m unittest` 经 python subprocess 起会撞上
`Invalid manifest`（今天验过：同一条命令在 shell 里 rc=0，经子进程稳定 rc=1 且日志字节数恒定），
而 needle 唯一性与臂号跨表查重是**静态**检查，不需要跑测试。所以登记表留在这里（名册照样能扫到），
执行交给 bash。两边共用同一份 arms_r245/manifest.tsv，形状只有一处定义。
"""
import io, os
ROOT = '/Users/wangziyi/Codex_Project0'
MANI = os.path.join(ROOT, ".scratch/motion-audit-2/arms_r245/manifest.tsv")


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
