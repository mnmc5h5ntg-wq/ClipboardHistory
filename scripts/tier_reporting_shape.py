# -*- coding: utf-8 -*-
"""R588 / 靶 3：档位循环必须**逐档各自点名**，缺席/未判的档数必须**可数**。

来历：R587 把 `heatmap_frame_levels.py` 的 `('dark','light')` 收成共用词表时，既有那格测试当场红 ——
根因不是合并错，而是那支脚本在**第一个 stop 处就 `return`**，所以"缺席那一档被点名"一直靠的是
**循环顺序**而不是契约。监工本轮要求现读全仓还剩几处这种形状：答案是 `scripts/*.py` 里还剩一处
（`frame_recording_proof.py` 的取帧循环，缺帧就 `return 1` ⇒ 第二档永远不会被点名），本轮一并修掉。

两条规则都写成 AST 判据（注释里的分类法等于没有）：
· **R1 不许在档位循环里 return**：循环体里出现 `Return` ⇒ 红并点名 `文件:行`。
  为什么钉这一条而不是钉"必须打印两行"：`return` 是"后面那些档我不看了"的**唯一静默形状**，
  而"打印几行"是可以被一句 `print` 凑数的。修法只有两种：累加之后统一收口，或 `continue` 跳过这一档。
· **R2 缺席的档数必须可数**：含档位循环的那个函数里必须出现字面量 `not-run=`（或 `未点名的档=`）⇒
  否则"各自点名"可以靠两句 print 满足，而**没人知道少了几档**。这一条是"点名"与"数得出来"的差别。

范围：判的是 `scripts/*.py`（活仪器）。`.scratch/` 里历轮的一次性脚本**只数不判**（它们不在产品仪器里，
同 R587 对 `sweep_r564_candidates.py` 的处置）；Swift 捕获侧那 11 处（BACKLOG 661）由红线管着，本轮不动。

用法：python3 scripts/tier_reporting_shape.py [--scripts DIR] [--scratch DIR]
退出码：0=判过且无红；1=有红；2=连一个档位循环都没找到（⇒ 扫描器读错了对象，绿灯不算数）。
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")
SCRATCH = os.path.join(REPO, ".scratch")
COUNT_TOKENS = (u"not-run=", u"未点名的档=", u"not_run=")


def tier_iter_names():
    """词表本身 ⇒ 循环可迭代对象认这几种形状（Name=TIERS / 由它现推的 list()/sorted() / 字面量元组）。"""
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from tier_vocabulary import TIERS
    return set(TIERS)


def is_tier_iter(node, tiers):
    if isinstance(node, ast.Name):
        return node.id == "TIERS"
    if isinstance(node, (ast.Tuple, ast.List)):
        vals = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        return bool(vals) and set(vals) == tiers
    if isinstance(node, ast.Call):
        return any(is_tier_iter(a, tiers) for a in node.args)
    return False


def func_of(tree, target):
    """沿 parent 链往上找最近的函数节点（R2 要在函数级找那格可数的字面量）。"""
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    cur = target
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent.get(cur)
    return None


def scan_file(path, tiers):
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=path)
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not is_tier_iter(node.iter, tiers):
            continue
        returns = [m.lineno for m in ast.walk(node) if isinstance(m, ast.Return)]
        fn = func_of(tree, node)
        tokens = []
        if fn is not None:
            for lit in ast.walk(fn):
                if isinstance(lit, ast.Constant) and isinstance(lit.value, str):
                    if any(tok in lit.value for tok in COUNT_TOKENS):
                        tokens.append(lit.lineno)
        rows.append({"file": os.path.relpath(path, REPO), "loop": node.lineno,
                     "returns": returns, "countable": bool(tokens),
                     "count_lines": tokens, "func": fn.name if fn else ""})
    return rows, src.count("\n") + 1


def list_py(root):
    out = []
    for dp, _d, fns in os.walk(root):
        if "tier_reporting_shape" in dp:
            continue
        for fn in sorted(fns):
            if fn.endswith(".py"):
                out.append(os.path.join(dp, fn))
    return out


def verdict(rows):
    reds = []
    for r in rows:
        if r["returns"]:
            reds.append(u"%s:%d 档位循环体里有 return（%s）⇒ 缺席那一档靠词表顺序才被点名"
                        % (r["file"], r["loop"], u",".join(str(x) for x in r["returns"])))
        if not r["countable"]:
            reds.append(u"%s:%d 函数 %s 有档位循环却读不到可数的缺席格（%s 一个字面量都没有）"
                        % (r["file"], r["loop"], r["func"], u"/".join(COUNT_TOKENS)))
    return reds


def main(argv=None):
    ap = argparse.ArgumentParser(description="档位循环的点名形状扫描")
    ap.add_argument("--scripts", default=SCRIPTS)
    ap.add_argument("--scratch", default=SCRATCH)
    args = ap.parse_args(argv)
    tiers = tier_iter_names()

    rows, files = [], 0
    for p in list_py(args.scripts):
        if os.path.basename(p) == "tier_vocabulary.py":
            continue
        if os.sep + "tests" + os.sep in p:
            continue          # 夹具里的合成形状不算活仪器（同 R587 的范围规矩）
        files += 1
        try:
            got, _n = scan_file(p, tiers)
        except SyntaxError as e:
            print(u"TIER_SHAPE_PARSE_FAIL %s :: %s" % (p, e))
            continue
        rows.extend(got)
    scratch_rows = 0
    for p in list_py(args.scratch):
        try:
            scratch_rows += len(scan_file(p, tiers)[0])
        except SyntaxError:
            pass

    print(u"TIER_SHAPE_SCAN 活仪器文件=%d 档位循环=%d 带return=%d 无可数格=%d 一次性脚本里的循环=%d（只数不判）"
          % (files, len(rows), sum(1 for r in rows if r["returns"]),
             sum(1 for r in rows if not r["countable"]), scratch_rows))
    for r in rows:
        print(u"  逐字 %s:%d 循环=%d return=%s 可数=%s"
              % (r["file"], r["loop"], r["loop"], r["returns"], u"有" if r["countable"] else u"无"))
    if not rows:
        # 一个档位循环都没找到 ⇒ 扫描器读错了对象（词表改名了？循环写法换了？），这一格不许当绿
        print(u"TIER_SHAPE_RESULT=not-run 档位循环=0 ⇒ 扫描器没有对象，不许读成「全仓都合规」")
        return 2
    reds = verdict(rows)
    for r in reds:
        print(u"TIER_SHAPE_RED " + r)
    if reds:
        print(u"TIER_SHAPE_RESULT=red 拦路=%d" % len(reds))
        return 1
    print(u"TIER_SHAPE_RESULT=ok 档位循环=%d 全部逐档点名且缺席可数" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
