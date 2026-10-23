#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R312 / BACKLOG 366：把「按位置取针到底能覆盖多少臂」量成常驻读数，不是一次性 here-doc。

为什么要有它（现读，不是假想）：366 那条欠账写着"把 rot 从下界做成上界，办法是按位置取针"。
本轮真去量了一下，两条做法都不成立：
① 严格按文档形状 `(刀号, 靶, [(needle, mutant)], 期望)` 抽 ⇒ 位置可判臂只有个位数；
   放宽到"臂里任意一格是若干对字符串" ⇒ 也只多一点点。**可判面塌掉**，那是把尺做瞎而不是做严。
② 把"至少一根候选不命中"当成上界 ⇒ 多出来的那批"死候选"绝大多数是**变异文本身**
   （变异文本来就不该在盘上命中），于是上界是一个假数。

所以这一支只打印读数、不做判定（没有棘轮、没有红）：它的用途是让"这两条都不行"这句话
随时可以被复查 —— 台账里引它的时候引的是它打印的那一行，不是我在散文里写的数。

用法：`python3 .scratch/motion-audit-2/probe_needle_positions_r312.py [--dir 表目录]`
结论行：
  `NEEDLE_POS_STRICT 表=… 臂=… 位置可判臂=… 有位置可判臂的表=… needle 对=…`
  `NEEDLE_POS_LOOSE  表=… 臂=… 有对子的臂=… 有对子的表=… needle 对=…`
  `NEEDLE_RANGE 可判臂=… 下界=… 部分死=… 假上界=…`
"""
import argparse
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import hidden_arms as H  # noqa: E402  （仓库里的尺，不另造第二套）


def strict_pairs(elt):
    """文档形状：臂是 ≥3 元组，且第 3 格是「若干个二元字符串对」。"""
    if not isinstance(elt, ast.Tuple) or len(elt.elts) < 3:
        return []
    third = elt.elts[2]
    if not isinstance(third, (ast.List, ast.Tuple)) or not third.elts:
        return []
    out = []
    for e in third.elts:
        if (isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) == 2
                and all(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in e.elts)):
            out.append([x.value for x in e.elts])
        else:
            return []
    return out


def loose_pairs(elt, cmap):
    """臂里**任意一格**是「若干对字符串」就算（变量名查常量表）。"""
    out = []
    for sub in ast.walk(elt):
        if not isinstance(sub, (ast.List, ast.Tuple)) or not sub.elts:
            continue
        got = []
        ok = True
        for e in sub.elts:
            vals = None
            if isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) == 2:
                v = [x.value if isinstance(x, ast.Constant) else None for x in e.elts]
                if all(isinstance(x, str) for x in v):
                    vals = v
            elif isinstance(e, ast.Name) and e.id in cmap and len(cmap[e.id]) == 2:
                vals = cmap[e.id]
            if vals is None:
                ok = False
                break
            got.append(vals)
        if ok and got:
            out.extend(got)
    return out


def probe(directory):
    text = H.corpus()
    tables = sorted(f for f in os.listdir(directory)
                    if f.startswith("mutate_r") and f.endswith(".py"))
    s_arms = s_hit = s_tbl = s_pairs = 0
    l_arms = l_hit = l_tbl = l_pairs = 0
    judged = lower = partial = 0
    for name in tables:
        try:
            with io.open(os.path.join(directory, name), encoding="utf-8") as h:
                tree = ast.parse(h.read())
        except (SyntaxError, OSError):
            continue
        cmap = H.const_map(tree)
        sh = lh = 0
        for _var, elt in H.arms_of(tree):
            s_arms += 1
            sp = strict_pairs(elt)
            if sp:
                sh += 1
                s_pairs += len(sp)
            lp = loose_pairs(elt, cmap)
            if lp:
                lh += 1
                l_pairs += len(lp)
            cands = H.arm_candidates(elt, cmap)
            if cands:
                judged += 1
                dead = [c for c in cands if c not in text]
                if dead and len(dead) == len(cands):
                    lower += 1
                elif dead:
                    partial += 1
        s_hit += sh
        l_hit += lh
        if sh:
            s_tbl += 1
        if lh:
            l_tbl += 1
    return {
        u"tables": len(tables), u"s_arms": s_arms, u"s_hit": s_hit, u"s_tbl": s_tbl,
        u"s_pairs": s_pairs, u"l_hit": l_hit, u"l_tbl": l_tbl, u"l_pairs": l_pairs,
        u"judged": judged, u"lower": lower, u"partial": partial,
    }


def main(argv):
    ap = argparse.ArgumentParser(
        prog="probe_needle_positions_r312.py",
        description=u"量「按位置取针」的可判面与「部分死」当上界的污染，只打印不判定。")
    ap.add_argument("--dir", default=H.TABLE_DIR, help=u"变异表所在目录")
    ns = ap.parse_args(argv[1:])
    r = probe(ns.dir)
    print(u"NEEDLE_POS_STRICT 表=%d 臂=%d 位置可判臂=%d 有位置可判臂的表=%d needle 对=%d"
          % (r[u"tables"], r[u"s_arms"], r[u"s_hit"], r[u"s_tbl"], r[u"s_pairs"]))
    print(u"NEEDLE_POS_LOOSE 表=%d 臂=%d 有对子的臂=%d 有对子的表=%d needle 对=%d"
          % (r[u"tables"], r[u"s_arms"], r[u"l_hit"], r[u"l_tbl"], r[u"l_pairs"]))
    print(u"NEEDLE_RANGE 可判臂=%d 下界=%d 部分死=%d 假上界=%d"
          % (r[u"judged"], r[u"lower"], r[u"partial"], r[u"lower"] + r[u"partial"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
