# -*- coding: utf-8 -*-
"""R589 / 靶 B：把 638 的②那一问从散文做成会红的门 —— 逐字节副本必须登记，且不许当唯一像素证人。

三格口径（都是会红的判据，不是注释里的告诫）：

· **登记（R-a）**：现读语料里每一个「两张以上逐字节同一」的组，都必须在 `docs/frame_identical_pairs.json`
  里有自己的行。多了组没登记 ⇒ 红并点名。这是监工要求的那把刀的落点：`撞号组数 == 名册覆盖数`。
· **该不该相同（R-b）**：名册每行带 `should_be_identical=是/否`。
  「不该相同而相同」= 状态没画（R490 那一族）⇒ 红；「该相同而不同」= 有东西漂了 ⇒ 红。
  两个方向的成因相反，所以必须分开点名，不许合并成一句「名册与语料不符」。
· **唯一证人（R-c）**：判据若**只**引用某一组里的副本（引用 ≥2 张且全在同一组内）⇒ 它拿两张逐字节同一的帧
  互相作证 = 恒真门 ⇒ 红并点名 `文件:组`。引用了组外的第三张不算（所以这一条不会把"用了其中一张"误伤）。

范围与禁事：本脚本**不删帧、不改基线名单、不跑 `frame_baseline.py update`**（那些是 638①/655 归用户的处置）。
它只读 sha256 与 `scripts/*.py` 的字面量。Swift 捕获侧一字未动。

用法：python3 scripts/identical_frame_witness.py [--shots DIR] [--roster PATH] [--scripts DIR] [--fixture-dir DIR]
退出码：0=三格都判过且无红；1=有红；2=**没有读数**（帧目录不在 / 名册空 / 语料里没有 png ⇒ 扫描器没有对象，不许当绿）。
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from scripts.frame_baseline import machine_key          # noqa: E402  （键的实现全仓只此一份，见 test_python_machine_key_implementations_agree）
SCRIPTS = os.path.join(REPO, "scripts")
ROSTER = os.path.join(REPO, "docs", "frame_identical_pairs.json")
SWIFT_TESTS = os.path.join(REPO, "ClipboardHistory", "Tests")
REQUIRED = (u"members", u"should_be_identical", u"cause", u"cause_refs", u"ticket",
            u"observed", u"registered_by_round", u"machine")
SHA_PREFIX = 12


def frame_key(name):
    """`content-paused-idle-750x560-dark.png` ⇒ `content-paused-idle`（去掉尺寸段、色档与扩展名）。

    按行取证那一类（`detail-3-files-row0`）的键本身带 `-row0`，所以这里只抹**尾巴**上
    `-<宽>x<高>-<dark|light>` 那一段，不抹中间的连字符 —— 抹错了会把两张不同的夹具并成一把键。
    """
    stem = os.path.basename(name)
    if stem.endswith(u".png"):
        stem = stem[:-4]
    return re.sub(u"-\\d+x\\d+-(dark|light)$", u"", stem)


def load_roster(path):
    """形状坏了要**抛**，不许在调用方手里变成「0 行 ⇒ 没有副本」（`load_drift_registry` 同族，R99）。"""
    document = json.load(io.open(path, encoding=u"utf-8"))
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError(u"名册里没有 rows 列表：%s" % path)
    out = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(u"名册里有一行不是对象：%r" % (row,))
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            raise ValueError(u"名册里有一行缺字段 %s：%r" % (missing, row))
        members = row[u"members"]
        if not isinstance(members, list) or len(members) < 2:
            raise ValueError(u"名册里有一行的 members 不是两张以上的列表：%r" % (members,))
        if row[u"should_be_identical"] not in (u"是", u"否"):
            raise ValueError(u"should_be_identical 只允许「是/否」，读到 %r" % (row[u"should_be_identical"],))
        if not str(row[u"cause"]).strip():
            raise ValueError(u"名册里有一行的成因是空的：%r" % (members,))
        if not isinstance(row[u"cause_refs"], list) or not row[u"cause_refs"]:
            raise ValueError(u"名册里有一行没有 cause_refs（成因引用不许只靠散文）：%r" % (members,))
        if not str(row[u"ticket"]).strip():
            raise ValueError(u"名册里有一行的 ticket 是空的：%r" % (members,))
        observed = row[u"observed"]
        if not isinstance(observed, dict) or not str(observed.get(u"sha", u"")).strip():
            raise ValueError(u"名册里有一行没有 observed.sha（每行要带取数时刻的实测哈希）：%r" % (members,))
        if not str(row[u"registered_by_round"]).strip():
            raise ValueError(u"名册里有一行没有 registered_by_round：%r" % (members,))
        if not str(row[u"machine"]).strip():
            raise ValueError(u"名册里有一行没有 machine —— 副本是不是同一张是**一台机器**的事（658 那一族），"
                             u"没有机器归属的行不许参与判定：%r" % (members,))
        out.append(row)
    keys = [tuple(sorted(os.path.basename(m) for m in r[u"members"])) for r in out]
    dupe = [k for k, v in collections.Counter(keys).items() if v > 1]
    if dupe:
        raise ValueError(u"名册里有两行覆盖同一组（同组只准一行）：%s" % (dupe,))
    return out


def sha_groups(frames_dir):
    hashes = {}
    for name in sorted(os.listdir(frames_dir)):
        if not name.endswith(u".png"):
            continue
        hashes[name] = hashlib.sha256(io.open(os.path.join(frames_dir, name), u"rb").read()).hexdigest()
    groups = collections.defaultdict(list)
    for name, digest in hashes.items():
        groups[digest].append(name)
    return hashes, dict(groups)


def copy_groups(groups):
    """逐字节撞号的组（≥2 张同一份内容），按帧键归并 ⇒ 一组一条。"""
    out = []
    for digest, names in sorted(groups.items(), key=lambda kv: sorted(kv[1])):
        if len(names) < 2:
            continue
        out.append({"sha": digest, "names": sorted(names),
                    "keys": sorted(set(frame_key(n) for n in names))})
    return out


def judge(copies, rows, present_names):
    """三格口径的判法，返回 (counts, reds)。

    组的身份是**文件名**而不是夹具键：`-dark` 与 `-light` 是两组不同的实测（sha 也不同），
    名册里 8 行对应 8 组 —— 这一点是这一版自己抓出来的：第一版我按去掉色档的键归组，
    于是暗/亮两行塌成同一组，名册 loader 当场报「同组只准一行」。
    """
    reds = []
    registered = {}
    for row in rows:
        registered[tuple(sorted(os.path.basename(m) for m in row[u"members"]))] = row
    group_index = {tuple(g[u"names"]): g for g in copies}

    unregistered = [g for g in copies if tuple(g[u"names"]) not in registered]
    for g in unregistered:
        reds.append(u"新增副本没登记：%s（sha 前 %d 位=%s）⇒ 这一组现在不为任何断言单独作证，却也没进名册"
                    % (u" + ".join(g[u"names"]), SHA_PREFIX, g[u"sha"][:SHA_PREFIX]))

    drifted, vanished, should_differ = [], [], []
    for row in rows:
        names = sorted(os.path.basename(m) for m in row[u"members"])
        key = tuple(names)
        missing = [n for n in names if n not in present_names]
        if missing:
            vanished.append(key)
            reds.append(u"名册这一行的帧不在现读语料里：%s ⇒ 帧被删过或夹具改过名，名册要跟着走（不许留着当「已登记」）"
                        % (u" + ".join(missing),))
            continue
        g = group_index.get(key)
        if g is None:
            if row[u"should_be_identical"] == u"是":
                drifted.append(key)
                reds.append(u"该相同而不同：%s ⇒ 名册说这组是设计内同图，现读它们已经不是同一份字节了 = 有东西漂了"
                            % (u" + ".join(names),))
        elif row[u"should_be_identical"] == u"否":
            should_differ.append(key)
            reds.append(u"不该相同而相同：%s（sha=%s）⇒ 状态没画出来（R490 那一族），这不是登记问题，是缺陷"
                        % (u" + ".join(names), g[u"sha"][:SHA_PREFIX]))

    return {"夹具键数": len(set(frame_key(n) for n in present_names)), "同图组": len(copies),
            "名册行": len(rows), "未登记": len(unregistered), "漂了": len(drifted),
            "名册帧缺失": len(vanished), "不该相同": len(should_differ)}, reds


def referenced_keys(path):
    """一个判据在字面量里引用了哪些**夹具键**（只认带连字符的那种形状，避免把普通词当帧名）。"""
    src = io.open(path, encoding=u"utf-8").read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for token in re.findall(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+", node.value):
                out.add(token)
    return out


def strip_swift_comments(src):
    """剥 Swift 注释：**先块后行**，顺序不许换。

    R578 那一课的复发预防：先剥行注释时，块注释里那一句 `//` 会让正则从那里一路吃到文件尾，
    实测一次吞掉 86 万字符 ⇒ 整份文件"没有引用"，把 0 读成干净。所以块注释先整段删。
    """
    src = re.sub(r"/\*.*?\*/", u"", src, flags=re.S)
    src = re.sub(r"//[^\n]*", u"", src)
    return src


LITERAL_RX = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def swift_units(path):
    """按 `func` 切成单元（函数级而不是文件级 —— 整个 harness 是一个文件几百个测试，
    文件级判"只引用同组两张"永远不会命中，那种 0 是假干净）。"""
    src = strip_swift_comments(io.open(path, encoding="utf-8", errors="replace").read())
    units = []
    for m in re.finditer(r"(?m)^[ \t]*(?:@\w+[ \t]*)?(?:private |fileprivate |internal |public )?func\s+([A-Za-z_]\w*)",
                         src):
        name = m.group(1)
        line = src[:m.start()].count(u"\n") + 1
        depth = 0
        started = False
        end = len(src)
        for i in range(m.end(), len(src)):
            ch = src[i]
            if ch == u"{":
                depth += 1
                started = True
            elif ch == u"}":
                depth -= 1
                if started and depth == 0:
                    end = i + 1
                    break
        units.append((name, line, src[m.start():end]))
    return units


def swift_refs_and_shapes(text):
    """一个单元里引用的夹具键 + 两种"认不出"的形状计数（拼接 `+` 与插值 `\\(`）。"""
    refs = set()
    for lit in LITERAL_RX.findall(text):
        for token in re.findall(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+", lit):
            refs.add(token)
    concat = len(re.findall(r'"\s*\+|\+\s*"', text))
    interp = len(re.findall(r"\\\(", text))
    return refs, concat, interp


def witness_reds(rows, python_dir, swift_dir, self_path, corpus_keys=()):
    """R-c：判据只引用某一组里的副本（≥2 张且全在同一组内）⇒ 它拿同图互证，恒真。

    「组外第三张」的口径挂在**现读语料的键**上，不是挂在名册上：判据引用了一张真存在的、
    不在这组里的帧，它就还有别的证人，这一条就不许红。名册之外的那张帧同样算组外。

    R590 / 靶 1：扫描面是**读数**，不是默认值。python 侧与 Swift 侧分开数、分开出声，
    Swift 树不在就叫 `swift=absent`（那一维不判），不许让"python 侧 0 条"被读成"全仓 0 条"。
    """
    keyed = [(sorted(set(frame_key(m) for m in row[u"members"])), row) for row in rows]
    universe = set(corpus_keys)
    for keys, _ in keyed:
        universe |= set(keys)

    def refs_in(refs, keys):
        # 引用匹配要**整段相等**或以该键开头紧跟 `-`：`row-text` 不许把 `row-text-something-else` 也算进来，
        # 反过来 `row-text-300x74` 那种带尺寸的写法要能认（夹具键就是它的前缀）。
        return set(k for k in keys for r in refs if r == k or r.startswith(k + u"-"))

    reds, scope = [], {u"python_files": 0, u"swift_files": 0, u"swift_units": 0,
                       u"swift_concat": 0, u"swift_interp": 0, u"swift_present": False}

    def judge_unit(label, refs):
        hit_any = refs_in(refs, universe)
        if len(hit_any) < 2:
            return
        for keys, _row in keyed:
            hit = refs_in(refs, keys)
            if len(hit) >= 2 and hit == hit_any:
                reds.append(u"%s 的像素证人只落在名册那一组副本里的 %s（它们逐字节同一）⇒ 没有组外第三张帧，"
                            u"这条断言恒真" % (label, u"+".join(sorted(hit))))
                return

    if python_dir and os.path.isdir(python_dir):
        for name in sorted(os.listdir(python_dir)):
            if not name.endswith(u".py"):
                continue
            path = os.path.join(python_dir, name)
            if os.path.abspath(path) == os.path.abspath(self_path):
                continue
            scope[u"python_files"] += 1
            judge_unit(os.path.relpath(path, REPO), referenced_keys(path))
    if swift_dir and os.path.isdir(swift_dir):
        scope[u"swift_present"] = True
        for dp, _d, fns in os.walk(swift_dir):
            for fn in sorted(fns):
                if not fn.endswith(u".swift"):
                    continue
                scope[u"swift_files"] += 1
                for name, line, text in swift_units(os.path.join(dp, fn)):
                    scope[u"swift_units"] += 1
                    refs, concat, interp = swift_refs_and_shapes(text)
                    scope[u"swift_concat"] += concat
                    scope[u"swift_interp"] += interp
                    judge_unit(u"%s:%s func %s" % (os.path.relpath(os.path.join(dp, fn), REPO), line, name), refs)
    return reds, scope


def main(argv=None):
    ap = argparse.ArgumentParser(description=u"逐字节同图名册与唯一像素证人守卫")
    ap.add_argument(u"--shots", default=os.environ.get(u"CLIPBOARD_HISTORY_UI_SHOTS") or u"")
    ap.add_argument(u"--roster", default=ROSTER)
    ap.add_argument(u"--scripts", default=SCRIPTS)
    ap.add_argument(u"--swift", default=SWIFT_TESTS,
                    help=u"Swift 测试树根（R-c 的第二块扫描面）；目录不在就叫 swift=absent，那一维不判")
    ap.add_argument(u"--fixture-dir", default=None,
                    help=u"正对照：额外扫一份合成语料/合成判据目录，证明这把尺看得见违规（0 要分得开「没有」与「看不见」）")
    args = ap.parse_args(argv)

    if not args.roster or not os.path.exists(args.roster):
        print(u"IDENTICAL_PAIR_REFUSED=roster-missing ⇒ 名册不在，这一格不许读成「没有副本」")
        return 2
    try:
        rows = load_roster(args.roster)
    except ValueError as e:
        print(u"IDENTICAL_PAIR_REGISTRY=broken %s ⇒ 名册读不出来时不许当成「没有登记」" % e)
        return 1
    if not rows:
        print(u"IDENTICAL_PAIR_RESULT=not-run 名册行=0 ⇒ 名册是空的，不许读成「语料里没有副本」")
        return 2

    frames_dir = args.shots
    if not frames_dir or not os.path.isdir(frames_dir):
        print(u"IDENTICAL_PAIR_REFUSED=no-shots ⇒ 帧目录不可用（要 --shots 或 CLIPBOARD_HISTORY_UI_SHOTS）；"
              u"这一格是**没跑**，不是「没有副本」")
        return 2
    hashes, groups = sha_groups(frames_dir)
    if not hashes:
        print(u"IDENTICAL_PAIR_REFUSED=no-png 目录里没有 png：%s ⇒ 扫描器没有对象" % frames_dir)
        return 2

    # 名册是**一台机器的产物**（658 那一族在这里的对应物）：同一对夹具在 2x 与 1x 上不一定都逐字节同一，
    # 所以判之前先按机器分家。本机没有自己的行 ⇒ 具名不判（照报组数），不许读成「这台机器没有副本」，
    # 也不许拿别的机器那 8 行来判这一台。
    this_machine = machine_key()
    mine = [r for r in rows if str(r.get(u"machine") or u"") == this_machine]
    foreign = len(rows) - len(mine)
    print(u"IDENTICAL_PAIR_MACHINE 本机=%s 名册本机行=%d 他机行=%d" % (this_machine, len(mine), foreign))

    copies = copy_groups(groups)
    present_names = set(hashes)
    counts, reds = judge(copies, mine, present_names)

    # R-c 的证人只在**判据自己引用了帧**时才判得到，所以**扫描面本身要当读数印出来**（R590 靶 1）：
    # 这一维的 0 今天只能说"python 侧没有只拿同图互证的断言"，不能说"全仓干净"——
    # 这 8 组帧的像素证人主要住在 Swift 测试树里（`UICaptureHarness.swift` 那几百个 func）。
    wr, scope = witness_reds(rows, args.scripts, args.swift, os.path.abspath(__file__),
                             corpus_keys=set(frame_key(n) for n in hashes))
    reds.extend(wr)
    print(u"WITNESS_SCAN_SCOPE python文件=%d swift文件=%d swift函数=%d 拼接点=%d 插值点=%d"
          % (scope[u"python_files"], scope[u"swift_files"], scope[u"swift_units"],
             scope[u"swift_concat"], scope[u"swift_interp"]))
    if not scope[u"swift_present"]:
        print(u"WITNESS_SWIFT_NOT_RUN=%s ⇒ Swift 那一维今天不判，`唯一证人` 只覆盖 python 侧" % (args.swift or u"（没给）",))
    if scope[u"swift_concat"] or scope[u"swift_interp"]:
        print(u"WITNESS_SWIFT_PARTIAL=拼接 %d 处 / 插值 %d 处 ⇒ 这两种写法里的键**可能**没被认出来，"
              u"这一维的 0 是「下界」而不是「全仓没有」" % (scope[u"swift_concat"], scope[u"swift_interp"]))

    print(u"IDENTICAL_PAIRS png=%d 夹具键=%d 逐字节同图组=%d 本机名册行=%d 未登记=%d 漂了=%d 名册帧缺失=%d "
          u"不该相同=%d 唯一证人=%d"
          % (len(hashes), counts["夹具键数"], counts["同图组"], counts["名册行"], counts["未登记"],
             counts["漂了"], counts["名册帧缺失"], counts["不该相同"], len(wr)))
    for g in copies:
        print(u"  逐字组 %s sha=%s 成员=%d" % (u"+".join(g[u"names"]), g[u"sha"][:SHA_PREFIX], len(g[u"names"])))
    if args.fixture_dir:
        fx_hashes, fx_groups = sha_groups(args.fixture_dir)
        fx_copies = copy_groups(fx_groups)
        fx_counts, fx_reds = judge(fx_copies, rows, set(fx_hashes))
        print(u"IDENTICAL_CONTROL 合成语料组=%d 判成红=%d（正对照：这一趟必须>0，否则这把尺看不见违规）"
              % (len(fx_copies), len(fx_reds)))
        for r in fx_reds:
            print(u"IDENTICAL_CONTROL_RED " + r)
    if not mine:
        print(u"IDENTICAL_PAIR_RESULT=not-run 本机行=0 他机行=%d 本机组=%d ⇒ 这一台还没登记过自己的副本，"
              u"不许读成「这台机器没有副本」，也不许拿别台的行来判" % (foreign, len(copies)))
        return 2
    for r in reds:
        print(u"IDENTICAL_PAIR_RED " + r)
    if reds:
        print(u"IDENTICAL_PAIR_RESULT=red 拦路=%d" % len(reds))
        return 1
    print(u"IDENTICAL_PAIR_RESULT=ok 组=%d 全部登记、方向各自点名、无恒真证人" % counts["同图组"])
    return 0


if __name__ == u"__main__":
    sys.exit(main())
