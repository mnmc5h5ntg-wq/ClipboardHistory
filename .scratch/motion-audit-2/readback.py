#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""刀的落刀回读：判的是"盘上恰好变成预期的那一份"，不是"替换串出现过几次"。

426 的现场：R350 想给 425 配刀，替换串 `.contentFade) * 1000) { store in` 在文件别处本来就有，
`read(path).count(repl) == 1` 不成立 ⇒ **刀根本没落下去**，跑器却只能说一句"回读不匹配"。
而"替换串唯一"既不必要也不充分：真正要证的是
    `after == before.replace(needle, repl)`  （且 before 里 needle 恰好一次）
—— 它同时排除"没落刀""落了两次""顺手改了别处"三种坏法，且不要求 repl 全局唯一。
"""


def single_substitution_lands(before, needle, repl, after):
    u"""True 只有当 after 恰好是 before 的单次 needle→repl 替换。"""
    if not needle or before.count(needle) != 1:
        return False
    expected = before.replace(needle, repl, 1)
    return after == expected and after != before
