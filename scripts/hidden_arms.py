#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R310 / BACKLOG 364：藏在 lambda 与变量里的「腐烂针」必须被数出来，而且要能被归因。

为什么要有这一支（现读，不是假想）：`.scratch/motion-audit-2/mutate_needle_precheck.py`
只能抽"元组里直接放字符串"的针；抽不出的那些表整批被报成「不在覆盖里」。
R308 我就是这么把 `mutate_r45_hover_ring.py` 的一根针**放烂了八轮**（它早就命中 0 次），
直到我改到同一行才撞见。名册那一行给的是规模：`registered=103 unregistered_with_arms=75 hidden_arms=423`。

判法（两条都是本轮量出来的，缺一条就不可信）：
① **先做常量传播再判**。臂里的 needle 常常写成变量（`ARMS = [(…, N_GATE, R_GATE, …)]`），
   只把"臂子树里的字符串常量"当候选 ⇒ 中文说明与守卫 id 会被当成针 ⇒ 假正例。
   第一版探针就是这样在 191 张表上报出 152 rot，其中包含当天刚全 CAUGHT 的 r308 / r309
   （与 R307「区间对账没分箱就数出 34 个假正例」同一课：**判法不成立时先怀疑分箱，不要先加门**）。
   分箱之后：可判臂 701、rot 30、抽不出候选的臂 5。
② **双向棘轮**：上界必须**恰好等于**现读值。只判"不许超过"会允许它悄悄涨回去；
   只判"不许低于"会把真修好的成果钉死。所以 `rot != ROT_CEILING` 就红，两个方向都有牙。

不许 import 那些表来数（这是本轮探到的另一条）：191 张表里至少 10 张没有
`if __name__ == "__main__"` 守卫 —— import 就会真的落刀跑 swift 测试。
所以判据必须是**静态**的（AST + 常量传播），这一点也写进上界：抽不出候选的臂同样被登记。

用法：`python3 scripts/hidden_arms.py [--dir 表目录] [--rot N]`
结论行：`HIDDEN_ARMS 表=… 可判=… rot=… 抽不出=… 上界 rot=… 抽不出=… 处置=ok|red`
"""
import argparse
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TABLE_DIR = os.path.join(ROOT, ".scratch", "motion-audit-2")
MIN_LEN = 12
LIST_NAMES = ("ARMS", "MUTATIONS", "CASES", "TABLE")
SCAN_ROOTS = ("ClipboardHistory/Sources", "ClipboardHistory/Tests", "scripts", "docs", ".github")

# 双向棘轮：这三个数**必须**等于现读值（R313 现读）。
# 注：过滤掉「路径型候选」之前测得 30 / 5 —— 那 3 把是被路径命中洗活的死刀（见 arm_candidates 的注释）。
# R313 起 rot 这一箱**只数未声明的臂**：表里写了 `NEEDLES = {刀号: [针, …]}` 的那些臂改走
# 「逐根判」那一箱（declared_dead），因为对已声明的针，"第几根死了"是可加总的真数；
# 未声明的仍然只配当下界（`any(候选命中)` 的漏报形状见 BACKLOG 366）。
ROT_CEILING = 33
OPAQUE_CEILING = 6
DECLARED_DEAD_CEILING = 0
DECLARED_TABLES_CEILING = 6  # R313 现读 2（r308/r312）→ R361 现读 6：r355/r356/r358/r360 也声明了 NEEDLES。
# R361 的一条读数：把四张表从"启发式判活"改成"自己声明"之后，rot 与抽不出**一个数都没动**（33 / 6）——
# 因为那四把针本来就是活的；声明的收益是"已判"从下界变成确数（declared_dead 可加总），不是让 rot 变小。
# 注：这里**必须**单反斜杠。R310 交付时它写的是 `r"M\\d{3,4}"` —— 在 raw 字符串里那是
# 「反斜杠 + d」，正则永远不命中，于是刀号归因静默退化成「臂#N」整整三轮，
# 直到 R313 的声明对账格（NEEDLES 的键要靠刀号匹配）把它撞出来。
# 同一族坏法在 R311 的台账补丁器里也出现过（三处 `\\d`），那条记在 BACKLOG 364 的追记里。
ARM_ID = re.compile(r"M\d{3,4}")
# 刀号那一格通常就是 `'M908'` —— 4~5 个字符，**过不了** `arm_candidates` 的 MIN_LEN=12，
# 所以不能靠候选集去找它。R313 第一次跑就是这么让 declared_arms 静默变成 0 的
# （而 declared_tables 仍然报 2 ⇒ 那一格是假绿，见下面的修正）。
ARM_LABEL = re.compile(r"^M\d{3,4}[a-z]?$")


def arm_label_of(elt):
    """臂里**恰好**是刀号的那一格（`'M908'` / `'M213b'`），不是"描述里含 M9xx"。"""
    for sub in ast.walk(elt):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and ARM_LABEL.match(sub.value):
            return sub.value
    return u""
PATHISH = re.compile(u"^[\\w./\\\\-]+$")


def _is_pathish(c):
    """像文件路径的候选不算针：含斜杠，或以已知扩展名结尾，且整串只有路径字符。"""
    if not PATHISH.match(c):
        return False
    return u"/" in c or c.endswith((".swift", ".py", ".json", ".md", ".yml", ".sh", ".txt"))


def corpus(roots=SCAN_ROOTS, repo=ROOT):
    """可能被落刀的文本文件，一次读进内存（本仓库源码体量小，够用）。"""
    blob = []
    for rel in roots:
        base = os.path.join(repo, rel)
        for dirpath, dirnames, filenames in os.walk(base):
            # 合成夹具**不许进语料**：死针的字符串就住在夹具自己里，进了语料就"哪都在"，
            # 于是 rot 永远数不出来（正对照当场失效）。
            dirnames[:] = [d for d in dirnames
                           if d not in (".build", "__pycache__", ".git", "fixtures")]
            for fn in filenames:
                if not fn.endswith((".swift", ".py", ".json", ".yml", ".md", ".sh")):
                    continue
                try:
                    with io.open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace") as h:
                        blob.append(h.read())
                except OSError:
                    pass
    return u"\n\x00\n".join(blob)


def const_map(tree):
    """模块级 `NAME = 字符串字面量`（`literal_eval` 能吃下的都算）⇒ 供臂里的变量名解析。"""
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if not isinstance(t, ast.Name):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if isinstance(val, str):
                out[t.id] = [val]
            elif isinstance(val, (list, tuple)):
                out[t.id] = [v for v in val if isinstance(v, str)]
    return out


def arms_of(tree):
    """顶层那些"看起来是一批臂"的列表赋值 ⇒ (变量名, 每一臂的 AST 节点)。"""
    res = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if not isinstance(t, ast.Name) or t.id not in LIST_NAMES:
                continue
            val = node.value
            if isinstance(val, (ast.List, ast.Tuple)):
                res.extend((t.id, elt) for elt in val.elts)
            elif isinstance(val, (ast.Call, ast.ListComp, ast.GeneratorExp)):
                # 推导式 / 函数造臂：整块当一臂（它的针要么静态可解，要么就是"抽不出"）
                res.append((t.id, val))
    return res


def arm_candidates(elt, cmap):
    """一臂里**能解析成字面量**的字符串：常量直接取，变量名查常量表；f-string / lambda 不猜。"""
    out = []
    for sub in ast.walk(elt):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value)
        elif isinstance(sub, ast.Name) and sub.id in cmap:
            out.extend(cmap[sub.id])
    # 目标路径那一格**不是针**（它当然在盘上）：不滤掉它，死针会被"路径命中"洗成活的
    # —— 本轮合成对照第一次跑就是这么假绿的（rot=0 而期望 1）。
    return [c for c in out if len(c) >= MIN_LEN and not _is_pathish(c)]


def needle_map(tree, cmap):
    """表里声明的 `NEEDLES = {"M890": GAP_LINE, "M891": [PAD_A, PAD_B]}` ⇒ 刀号 → 针的原文列表。

    为什么要有这个通道（BACKLOG 367）：把 rot 做成上界**没有**静态可推断的办法 ——
    R312 现读：按位置取针只能覆盖 16/715 臂（可判面塌掉），而"至少一根候选不命中"当上界
    会把**变异文**算成死针（它本来就不在盘上）。所以只能由表自己说哪根是针。
    值可以是字符串字面量、也可以是模块级常量名（走 `const_map` 解析，与臂本身同一套）。
    """
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "NEEDLES" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for k, v in zip(node.value.keys, node.value.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            items = []
            for e in (v.elts if isinstance(v, (ast.List, ast.Tuple, ast.Set)) else [v]):
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    items.append(e.value)
                elif isinstance(e, ast.Name) and e.id in cmap:
                    items.extend(cmap[e.id])
            if items:
                out[k.value] = items
    return out


def scan(directory=TABLE_DIR, text=None):
    """返回 (读数, 未声明那一箱的 rot 明细, 抽不出的明细)。

    读数里另有一箱：`declared_dead`（已声明针里死掉的**根数**，可加总）与
    `declared_arms` / `declared_tables`（覆盖面，用来钉"不许悄悄取消声明"）。
    明细放在 `info["declared_rows"]`，不改三元组的形状（调用方与判据卷都吃三元组）。
    """
    if text is None:
        text = corpus()
    tables = sorted(f for f in os.listdir(directory) if f.startswith("mutate_r") and f.endswith(".py"))
    judged = rot = opaque = 0
    declared_arms = declared_dead = declared_tables = 0
    rot_rows, opaque_rows, declared_rows = [], [], []
    for name in tables:
        try:
            with io.open(os.path.join(directory, name), encoding="utf-8") as h:
                tree = ast.parse(h.read())
        except (SyntaxError, OSError) as exc:
            opaque_rows.append((name, "-", u"解析失败 " + str(exc)[:40]))
            opaque += 1
            continue
        cmap = const_map(tree)
        nmap = needle_map(tree, cmap)
        hit_in_table = 0
        for idx, (_var, elt) in enumerate(arms_of(tree)):
            arm_id = arm_label_of(elt)
            cands = arm_candidates(elt, cmap)
            if not arm_id:
                for c in cands:
                    m = ARM_ID.search(c)
                    if m:
                        arm_id = m.group(0)
                        break
            if arm_id and arm_id in nmap:
                judged += 1
                declared_arms += 1
                hit_in_table += 1
                for n in nmap[arm_id]:
                    if n not in text:
                        declared_dead += 1
                        declared_rows.append((name, arm_id, n[:48]))
                continue
            if not cands:
                opaque += 1
                opaque_rows.append((name, u"臂#" + str(idx), u"抽不出候选"))
                continue
            judged += 1
            if not any(c in text for c in cands):
                rot += 1
                rot_rows.append((name, arm_id or (u"臂#" + str(idx)), len(cands)))
        # 「声明了几张表」必须按**真的匹配上了臂**来数，不能按"文件里有个 NEEDLES 字典"来数 ——
        # 后者会让一张键名对不上任何臂的表也被算成已覆盖（R313 第一次跑就是这个形状）。
        if hit_in_table:
            declared_tables += 1
    return ({u"tables": len(tables), u"judged": judged, u"rot": rot, u"opaque": opaque,
             u"declared_arms": declared_arms, u"declared_dead": declared_dead,
             u"declared_tables": declared_tables, u"declared_rows": declared_rows},
            rot_rows, opaque_rows)


def verdict(info, rot_ceiling=ROT_CEILING, opaque_ceiling=OPAQUE_CEILING,
            declared_dead_ceiling=DECLARED_DEAD_CEILING,
            declared_tables_ceiling=DECLARED_TABLES_CEILING):
    """双向棘轮：四个数都必须**恰好**等于现读值（只判一个方向 = 另一半没有牙）。"""
    problems = []
    if info[u"rot"] != rot_ceiling:
        problems.append(u"HIDDEN_ROT_DRIFT 现读 rot=%s 而上界写着 %s ⇒ "
                        u"变多=有新腐烂，变少=名单修掉了却没降上界（两个方向都不许留）"
                        % (info[u"rot"], rot_ceiling))
    if info[u"opaque"] != opaque_ceiling:
        problems.append(u"HIDDEN_OPAQUE_DRIFT 现读 抽不出=%s 而上界写着 %s ⇒ "
                        u"抽不出候选的臂变多=静态判据又瞎了一块"
                        % (info[u"opaque"], opaque_ceiling))
    if info[u"declared_dead"] != declared_dead_ceiling:
        problems.append(u"HIDDEN_DECLARED_DEAD_DRIFT 现读 已声明死针=%s 而上界写着 %s ⇒ "
                        u"这一箱是**逐根**数的可加总真数：变多=有声明过的针腐烂（必须重钉），"
                        u"变少=重钉了却没降上界"
                        % (info[u"declared_dead"], declared_dead_ceiling))
    if info[u"declared_tables"] != declared_tables_ceiling:
        problems.append(u"HIDDEN_DECLARED_TABLES_DRIFT 现读 已声明表=%s 而上界写着 %s ⇒ "
                        u"变少=有人悄悄删掉 NEEDLES 把已判的臂退回下界箱（那是洗白，不是修好）"
                        % (info[u"declared_tables"], declared_tables_ceiling))
    return problems


def main(argv):
    ap = argparse.ArgumentParser(
        prog="hidden_arms.py",
        description=u"静态数出变异表里「腐烂的针」与「静态抽不出候选的臂」，并过双向棘轮。")
    ap.add_argument("--dir", default=TABLE_DIR, help=u"变异表所在目录（默认 .scratch/motion-audit-2）")
    ap.add_argument("--synthetic", action="store_true",
                    help=u"用内置合成样本自证有牙（不碰真仓库，也不判上界）")
    ns = ap.parse_args(argv[1:])
    if ns.synthetic:
        info, rot_rows, opaque_rows = scan(os.path.join(HERE, "tests", "fixtures", "hidden_arms_synth"))
        # 三个期望各钉一件事：
        #   rot=1        —— 未声明那一箱仍然只报"整臂全死"（下界形状，别把它当上界）；
        #   抽不出=1     —— 静态抽不出候选的臂要显式露出来，不许悄悄算活的；
        #   已声明死针=1 —— **正对照**：夹具里 M997 那一臂有两根针、一根活一根死。
        #                  旧估计量看这一臂会报"活的"（`any` 命中），新那一箱必须报"死了 1 根"。
        #                  这一格就是 BACKLOG 366 说的那个漏报的证人。
        want = (info[u"rot"] == 1 and info[u"opaque"] == 1 and info[u"declared_dead"] == 1)
        print(u"HIDDEN_ARMS_SYNTH 表=%d 可判=%d rot=%d 抽不出=%d 已声明臂=%d 已声明死针=%d "
              u"期望 rot=1 抽不出=1 已声明死针=1"
              % (info[u"tables"], info[u"judged"], info[u"rot"], info[u"opaque"],
                 info[u"declared_arms"], info[u"declared_dead"]))
        for name, arm, needle in info[u"declared_rows"]:
            print(u"  HIDDEN_DECLARED_ROT %s %s 针=%r" % (name, arm, needle))
        return 0 if want else 1
    info, rot_rows, opaque_rows = scan(ns.dir)
    problems = verdict(info)
    print(u"HIDDEN_ARMS 表=%d 可判=%d rot=%d 抽不出=%d 已声明表=%d 已声明死针=%d "
          u"上界 rot=%d 抽不出=%d 已声明死针=%d 已声明表=%d 处置=%s"
          % (info[u"tables"], info[u"judged"], info[u"rot"], info[u"opaque"],
             info[u"declared_tables"], info[u"declared_dead"],
             ROT_CEILING, OPAQUE_CEILING, DECLARED_DEAD_CEILING, DECLARED_TABLES_CEILING,
             u"red" if problems else u"ok"))
    for name, arm, n in rot_rows:
        print(u"  HIDDEN_ROT %s %s（候选 %d 个，盘上一个都不命中 ⇒ 这一臂的针已腐烂）" % (name, arm, n))
    for name, arm, needle in info[u"declared_rows"]:
        print(u"  HIDDEN_DECLARED_ROT %s %s 针=%r（已声明的针在盘上找不到 ⇒ 必须重钉）"
              % (name, arm, needle))
    for name, arm, why in opaque_rows:
        print(u"  HIDDEN_OPAQUE %s %s %s" % (name, arm, why))
    for p in problems:
        print(u"  HIDDEN_ARMS_RED " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
