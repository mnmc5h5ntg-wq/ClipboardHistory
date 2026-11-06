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
from collections import Counter

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


def leaf_exprs(test):
    """把一条 `if` 的判断式摊平成**被读的量子表达式**集合（`and/or/not` 拆掉、比较的两边各自算一个量子）。

    为什么要摊平而不是整条比字面：`frame_baseline.py` 那两条分支写的是
    `bake["scale"] and current_scale and bake["scale"] != current_scale` 与 `not current_scale` ——
    整条字面永不相同，但**读的量**有交集（`current_scale`），而交集正是"同一对量"的证据。
    """
    out = []

    def dump(node):
        # 字面量不算"量子"：`== "tie"` 里那个 'tie' 被两条分支共读，说明的是同一个标签，
        # 不是同一种"读的是哪一个量"⇒ 标成 CONST: 让上层把它从共读集合里剔掉。
        return u"CONST:%s" % ast.dump(node) if isinstance(node, ast.Constant) else ast.dump(node)

    def unpick(node, neg=False):
        if isinstance(node, ast.BoolOp):
            for v in node.values:
                unpick(v, neg)
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            unpick(node.operand, not neg)
            return
        if isinstance(node, ast.Compare):
            out.append(dump(node.left))
            for c in node.comparators:
                out.append(dump(c))
            return
        if isinstance(node, ast.Call):
            # `cur_info.get("sizeless")` 这一类：量子是接收者，参数是键名 ⇒ 只记接收者
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                out.append(dump(node.func.value))
            else:
                for a in node.args:
                    unpick(a, neg)
            return
        if isinstance(node, (ast.Name, ast.Subscript, ast.Attribute)):
            out.append(dump(node))
            return
        if isinstance(node, ast.Constant):
            out.append(dump(node))

    unpick(test)
    return out


def printed_channel_literals(body):
    """这条分支体里**印出去**的通道名（`NAME=` 那种全大写串），用来认"这一组 if 在说同一个维度"。"""
    names = []
    for st in body:
        for n in ast.walk(st):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print":
                for lit in ast.walk(n):
                    if isinstance(lit, ast.Constant) and isinstance(lit.value, str):
                        m = re.match(r"^\s*([A-Z][A-Z0-9_]{5,}=?)", lit.value)
                        if m:
                            names.append(m.group(1).rstrip(u"="))
    return names


def common_prefix(names):
    if len(names) < 2:
        return u""
    p = os.path.commonprefix(sorted(names))
    cut = p.rfind(u"_")            # 只认到最后一个下划线为止：`FRAME_BASELINE_SCALE_` 而不是半截词
    return p[:cut + 1] if cut >= 6 else u""


def branch_groups(tree, relpath):
    """找**同一块里连续的 if 链**：≥2 条、印同一个通道前缀、且读了同一个量子 ⇒ 它就是在判一对互斥的情况。

    最后一道 `else` 有没有，是这一族与"档位循环 return"完全同形的洞：不穷尽 ⇒ 至少一种组合**一行都不印**，
    而静默与"量了没问题"在输出里逐字相同。返回的每格带 `closed`（有兜底）与 `shared`（共读的量）。
    同一串分支会因为 `orelse` 既被父块扫到、又被子块扫到而重复 ⇒ 按分支行号集合去重，
    否则 `分支链=5` 这种数会替我把"两个独立洞"说成"五个"。
    """
    rows = []
    seen = set()
    for node in ast.walk(tree):
        for field in ("body", "orelse"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            run = []
            for st in block:
                if isinstance(st, ast.If):
                    run.append(st)
                    continue
                if run:
                    rows.extend(_judge_run(run, relpath))
                    run = []
            if run:
                rows.extend(_judge_run(run, relpath))
    out = []
    for r in rows:
        key = (r["file"], tuple(r["lines"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def flatten_chain(node):
    """把 `if / elif / elif / else` 摊成一条链：返回 (分支节点列表, 有没有兜底 else)。

    为什么必须摊：`elif` 在 AST 里是 `orelse=[If(...)]`，不摊就只看得见链的第一朵 if，
    于是 `frame_baseline.py` 那条 `if … elif … elif … else` 会被读成「没有共读量子」而整条滑出对象
    —— 本轮第一版就是这么把唯一那个真对象漏掉的（现读 `分支链=1`，而它本该是 2）。
    """
    branches = [node]
    cur = node
    while cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
        cur = cur.orelse[0]
        branches.append(cur)
    closed = bool(cur.orelse)
    return branches, closed


def _judge_run(run, relpath):
    """一串连续的 if（含各自的 elif/else）⇒ 一条候选链。

    `closed` 取**最后一朵**的兜底：静默恰好发生在"后面没人接"，而中间某朵独立报告（`if TIE: print …`）
    本来就不需要 else —— 要求每一朵都有兜底会把无关的报告行也算成违规，规矩就从"防静默"退化成"逼废话"。
    """
    branches = []
    closed = False
    for it in run:
        bs, has_else = flatten_chain(it)
        branches.extend(bs)
        closed = has_else
    if len(branches) < 2:
        return []
    names = [printed_channel_literals(it.body) for it in branches]
    if any(not x for x in names):
        return []                     # 有一条分支不印通道 ⇒ 这不是"读数维度"的互斥链，不算对象
    prefix = common_prefix([n[0] for n in names])
    if not prefix:
        return []
    exprs = [set(leaf_exprs(it.test)) for it in branches]
    # 共读量子 = 出现在 ≥2 条分支里的表达式
    cnt = Counter()
    for e in exprs:
        cnt.update(e)
    shared = set(k for k, v in cnt.items() if v >= 2 and not k.startswith(u"CONST:"))
    if not shared:
        return []                     # 各判各的量 ⇒ 不是一组互斥分支（不许把无关的 if 挨在一起就当对象）
    return [{"file": relpath, "start": run[0].lineno, "lines": [it.lineno for it in branches],
             "prefix": prefix, "shared": sorted(shared), "closed": closed,
             "n": len(branches)}]


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


def verdict_branch(chains):
    """R3：读了同一对量、印同一个通道前缀、却没有『其余情况』分支 ⇒ 红。"""
    reds = []
    for c in chains:
        if not c["closed"]:
            reds.append(u"%s:%d 连续 %d 条 if 都在印 `%s*` 且共读同一个量（%s），却没有兜底 `else` ⇒ "
                        u"至少一种组合一行都不印，而静默与「量了没问题」逐字相同"
                        % (c["file"], c["start"], c["n"], c["prefix"],
                           u"; ".join(x[:40] for x in c["shared"][:3])))
    return reds


def main(argv=None):
    ap = argparse.ArgumentParser(description="档位循环的点名形状扫描 + 互斥分支链的穷尽性")
    ap.add_argument("--scripts", default=SCRIPTS)
    ap.add_argument("--scratch", default=SCRATCH)
    ap.add_argument("--extra", default=None,
                    help="额外扫一个目录（正对照用：把合成违规放进去，证明这把尺看得见违规）")
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

    # R589 / 靶 A②：互斥分支链。`--extra` 那一支是**正对照的来源**，它单独计数、单独判，
    # 因为"扫到 0 条链"有两种相反成因（全仓真的没有这种形状 / 这把尺认不出这种形状）——
    # 门的 0 必须分得开这两种（R578 ⑥ / M1519 那一族）。
    chains, extra_chains = [], []
    for p in list_py(args.scripts):
        if os.sep + "tests" + os.sep in p:
            continue
        try:
            tree = ast.parse(io.open(p, encoding="utf-8").read(), filename=p)
        except (SyntaxError, ValueError):
            continue
        chains.extend(branch_groups(tree, os.path.relpath(p, REPO)))
    if args.extra:
        for p in list_py(args.extra):
            try:
                tree = ast.parse(io.open(p, encoding="utf-8").read(), filename=p)
            except (SyntaxError, ValueError):
                continue
            extra_chains.extend(branch_groups(tree, os.path.relpath(p, REPO)))

    print(u"TIER_SHAPE_SCAN 活仪器文件=%d 档位循环=%d 带return=%d 无可数格=%d 一次性脚本里的循环=%d（只数不判）"
          % (files, len(rows), sum(1 for r in rows if r["returns"]),
             sum(1 for r in rows if not r["countable"]), scratch_rows))
    for r in rows:
        print(u"  逐字 %s:%d 循环=%d return=%s 可数=%s"
              % (r["file"], r["loop"], r["loop"], r["returns"], u"有" if r["countable"] else u"无"))
    unclosed = sum(1 for c in chains if not c["closed"])
    print(u"TIER_BRANCH_SCAN 分支链=%d（口径：按分支行号集合去重后的**候选链**条数，同一条长链的嵌套子串各算一次）"
          u" 共读同量=%d 无兜底=%d 正对照链=%d（--extra 给了才有）"
          % (len(chains), len(chains), unclosed, len(extra_chains)))
    for c in chains:
        print(u"  逐字链 %s:%d 条数=%d 前缀=%s 兜底=%s 共读=%s"
              % (c["file"], c["start"], c["n"], c["prefix"], u"有" if c["closed"] else u"无",
                 u"; ".join(x[:28] for x in c["shared"][:2])))
    reds = verdict(rows) + verdict_branch(chains)
    for r in reds:
        print(u"TIER_SHAPE_RED " + r)
    if extra_chains:
        print(u"TIER_BRANCH_CONTROL 正对照链=%d 其中应红=%d 其中判成红=%d"
              % (len(extra_chains), sum(1 for c in extra_chains if not c["closed"]),
                 len(verdict_branch(extra_chains))))
    if reds:
        print(u"TIER_SHAPE_RESULT=red 拦路=%d（其中分支链 %d）" % (len(reds), unclosed))
        return 1
    if not rows:
        # 一个档位循环都没找到 ⇒ 扫描器读错了对象（词表改名了？循环写法换了？），这一格不许当绿
        print(u"TIER_SHAPE_RESULT=not-run 档位循环=0 ⇒ 扫描器没有对象，不许读成「全仓都合规」")
        return 2
    if not chains:
        # 这一维的 0 必须**具名**：0 条候选有两种相反成因（全仓真的没有这种形状 / 这把尺认不出这种写法），
        # 输出里不许把它们写成同一句"没问题"。退出码这里**不动**（否则"一次性脚本只数不判"那格的负半会被带歪），
        # 由消费它的那道门负责把 `分支链=0` 拦下来 —— CI 的 `Release script tests` 步骤里那行
        # `TIER_BRANCH_BLIND=1` 就是这个拦截的落点，本机则由
        # `test_real_repo_chains_are_present_and_all_closed` 做成会红的断言。
        print(u"TIER_BRANCH_NOT_JUDGED=分支链这一维没有对象 ⇒ 这一维今天不判，不许读成「全仓的互斥分支都穷尽了」")
    print(u"TIER_SHAPE_RESULT=ok 档位循环=%d 全部逐档点名且缺席可数；分支链=%d %s"
          % (len(rows), len(chains),
             u"全部有兜底" if chains else u"这一维不判（见上面那行 NOT_JUDGED）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
