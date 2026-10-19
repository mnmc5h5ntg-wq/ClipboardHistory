#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按表面清账表的闸门：**每一格要么有结论，要么被数成未清账**（R127 / 阶段二收尾）。

为什么要有它（目标原文）：阶段二要求「每一个元素/文字段/可动部件都要重新判断加动效是否有积极作用，
有作用才加，无作用或有害就写明理由不加」。127 轮下来这些判断散在 `AGENT_UI_AUDIT.md` 的各轮正文里，
没有任何东西能回答「哪个表面、哪个状态还没判过」—— 而"散在正文里"与"没做"在复核时是同一个样子。
这张表把答案变成数据，并让这个区别可判：

  DUP_KEY        同一个 (表面, 状态) 出现两行 ⇒ 红。两行的理由迟早会互相矛盾，而读的人只看第一行。
  UNKNOWN_CELL   某行的表面或状态不在名册里 ⇒ 红（改名要两边一起改，否则那格静默消失）。
  BAD_VERDICT    verdict 不在词表里 ⇒ 红（"看着像结论的字符串"不算结论）。
  REASONLESS     理由为空或短于 20 字 ⇒ 红。**没理由的 not-added 就等于还没决定**。
  EVIDENCELESS   证据指针为空 ⇒ 红（理由要能被复查：哪一轮、哪个 BACKLOG、哪个文件）。
  BELOW_FLOOR    已清账格子数低于 `floor_cleared` ⇒ 红。地板只准升不准降（`testHistoryStoreStaysThin`
                 同一族：会红的必须是单调量；均值与区间都被证伪过）。**只数已清账的行**，
                 占位行（`not-measured`）不把地板抬起来。
  FLOOR_LIES     `floor_cleared` 大于实际行数 ⇒ 红（把地板写成愿望，就是给自己留一张免检牌）。
  FLOOR_WENT_BACK 本轮的 `floor_cleared` 小于 **HEAD 那一版** ⇒ 红（R143 / BACKLOG 184）。
                 `BELOW_FLOOR` 的两个量都在同一份可写文件里 ⇒「删五行 + 地板降五」它防不住；
                 单调性要压在表外的基准上。基准读不到 ⇒ 打 `head=无` 并**不判**（由电池断言本仓库读得到）。
  EVIDENCE_SHAPE 证据指针不含可复查对象（源码/测试/仓库内路径 / BACKLOG 号 / D-号 / 批次号）⇒ 红。
                 单独的轮次号只是"某个人在某轮写过"（U-424）。
  EVIDENCE_PATH_MISSING
                 指针里写的那个源码/测试文件在仓库里不存在 ⇒ 红（路径写错与根本没这回事，读的人分不出）。
  ABSENT_CLAIM_FALSE / ABSENT_CLAIM_UNVERIFIABLE
                 理由里写着「某文件里没有某个词」这种**缺席断言**，去查却发现那个词就在里面 ⇒ 红。
                 写法：`缺席:<路径>=<词>`（R131：清账表里一半的 not-applicable 靠的是缺席，
                 而"没量过的缺席"与"没做"在复核时是同一个样子）。
  SURFACE_UNCOVERED / STATE_UNCOVERED
                 名册里新增一个表面或状态却没有任何一行 ⇒ 红：分母扩张必须付账，
                 否则"未清账 136 格"会被稀释成看起来还在推进（U-425）。

未覆盖的格子**不红**，但必须被数出来（`MOTION_LEDGER 未清账=k`）：
清账是进度，不是及格线 —— 假装 162 格都判过，比承认只判了 18 格更坏。

每个代码只打印一次（R129 / U-430）：`FLOOR_LIES` 原来在名册解析和清账统计两处都查，
于是同一条规则有两份实现 —— 变异任何一处都被另一处掩盖，读数还会印两遍。
闸门自己的冗余也是判据的冗余。

用法：PYTHONUTF8=1 python3 scripts/motion_surface_gate.py [--path docs/motion_surface_ledger.json]
退出码：0 = 全部行合法；1 = 有任何一格不合法（逐条打印）；2 = 文件或 JSON 读不到。
"""
import argparse
import io
import json
import os
import re
import sys

MIN_REASON = 20

# U-424：证据指针必须有**可复查的具体对象**。轮次号（`R14`）只是"某个人在某轮写过"，
# 复查要翻台账；源码文件 / BACKLOG 号 / D-号 / 批次号 / 仓库内路径才是能直接点开的东西。
EVIDENCE_PATTERNS = [
    r"Sources/", r"Tests/", r"docs/", r"scripts/",
    r"BACKLOG\s*\d+", r"D-\d{3}", r"批次\s*[\d.]+",
]


def evidence_is_checkable(text):
    return any(re.search(pat, text or "") for pat in EVIDENCE_PATTERNS)

# R131 的两条新判据（U-424 的下一步）：指针「含一个可复查对象」还不够 ——
# 它必须**真的在那儿**，而理由里那些「grep 某个词 0 命中」的缺席断言必须**能被复查**。
# 缺席写法：`缺席:<路径>=<词>`，一条 evidence 里可以写多条（用 ｜ 或 ；分开）。
PATH_RE = re.compile(r"(?:Sources|Tests|scripts|docs|Managers)/[\w/\-.]*\.(?:swift|py|md|json)")
ABSENT_RE = re.compile(r"缺席:([\w/\-.]*\.(?:swift|py|md|json))=([^；|｜\s]+)")
# R203 补的第三种坏法（U-644…U-646 那批的读数）：PATH_RE 只认「以 Sources/Tests/… 开头」的形状，
# 于是 `Views/SearchField.swift`（少写前缀）和 `MenuBarController.swift`（只写文件名）这两类指针
# **从来没有被检查过** —— 闸门绿着，而读者点不开。 lax 那条把两类都收进来，
# 解析方式不同：能按整条路径解析 = 过；只能按文件名解析 = PARTIAL（要改写成可点击的整路径）；
# 文件名也找不到 = MISSING（假证人）。
PATH_RE_LAX = re.compile(r"[\w/\-.]*\.(?:swift|py|md|json)")
INDEX_DIRS = ("ClipboardHistory/Sources", "ClipboardHistory/Tests", "scripts", "docs")
_index_cache = {}


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def basename_index(root=None):
    """按 (root, 目录集) 建一次「文件名 -> 相对路径」的索引。

    为什么按文件名而不是整路径：松散指针（`Foo.swift`）本来就少了前缀，
    只有按文件名才判得出「这文件真有、但你写的路径点不开」与「根本没这文件」的区别。
    """
    root = root or repo_root()
    key = (root, tuple(INDEX_DIRS))
    if key not in _index_cache:
        idx = {}
        for rel_dir in INDEX_DIRS:
            top = os.path.join(root, rel_dir)
            for dirpath, dirnames, filenames in os.walk(top):
                dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
                for name in filenames:
                    if not name.endswith((".swift", ".py", ".md", ".json")):
                        continue
                    idx.setdefault(name, set()).add(os.path.relpath(os.path.join(dirpath, name), root))
        _index_cache[key] = idx
    return _index_cache[key]


def resolve(path, root=None):
    """把台账里写的相对路径落到真实文件上。

    指针一律写成 `Sources/...` 这种**从包根算起**的形状，而仓库根下面还有一层
    `ClipboardHistory/` —— 所以候选根是两个。少一个候选根，整张表的每一条指针都会
    被判成不存在（M644 就是这一格的证词：那条判据坏在最坏的一侧，比不判更糟）。
    """
    root = root or repo_root()
    for base in (root, os.path.join(root, "ClipboardHistory")):
        cand = os.path.join(base, path)
        if os.path.exists(cand):
            return cand
    return None


def path_problem(path, root=None):
    """一条路径指针的三种结局：过 / 松散（存在但点不开）/ 不存在。"""
    root = root or repo_root()
    if resolve(path, root) is not None:
        return None
    hits = sorted(basename_index(root).get(os.path.basename(path), ()))
    if not hits:
        return ("EVIDENCE_PATH_MISSING",
                "指针指向的文件不存在（%s）—— 路径写错、文件改名、或者根本没这回事" % path)
    if len(hits) > 1:
        return ("EVIDENCE_PATH_AMBIGUOUS",
                "%s 按文件名能对上 %d 个文件（%s）⇒ 指针必须写成整路径，别让读者猜"
                % (path, len(hits), u"、".join(hits)))
    return ("EVIDENCE_PATH_PARTIAL",
            "%s 这个文件在（%s），但指针写的形状点不开 ⇒ 改成从包根算起的整路径"
            % (path, hits[0]))


def evidence_problems(row, where, root=None):
    """返回这一格指针上的三类新问题：路径不存在、路径写得点不开、缺席断言其实不成立。"""
    out = []
    evidence = (row.get("evidence") or "")
    for path in sorted(set(PATH_RE_LAX.findall(evidence))):
        got = path_problem(path, root)
        if got is not None:
            out.append((got[0], "%s：%s" % (where, got[1])))
    for path, token in ABSENT_RE.findall(evidence):
        found = resolve(path, root)
        if found is None:
            out.append(("ABSENT_CLAIM_UNVERIFIABLE",
                        "%s：缺席断言指向不存在的文件（%s）⇒ 没量过的缺席不算缺席"
                        % (where, path)))
            continue
        text = io.open(found, encoding="utf-8", errors="replace").read()
        # 比**忽略大小写**：Swift 里 `disabled` 与 `Disabled` 讲的是同一件事，
        # 原来区分大小写的话，把断言写成 `缺席:X=Disabled` 就能在含 `disabled` 的文件上被"证实"。
        if token.lower() in text.lower():
            out.append(("ABSENT_CLAIM_FALSE",
                        "%s：写着「%s 里没有 %s」，但它就在里面 ⇒ 这条理由是在替一个没做的东西开脱"
                        % (where, path, token)))
    return out


def head_table(path="docs/motion_surface_ledger.json", root=None):
    """读 HEAD 那一版**整张表**；读不到返回 None（= 这一格没判，不是通过）。"""
    import subprocess
    root = root or repo_root()
    try:
        raw = subprocess.check_output(["git", "-C", root, "show", "HEAD:" + path],
                                      stderr=subprocess.DEVNULL)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _cleared_pairs(table):
    cleared = (table or {}).get("cleared_verdicts") or []
    return set((r.get("surface"), r.get("state")) for r in (table or {}).get("rows") or []
               if (r.get("verdict") or "") in cleared)


def retirement_allowance(data, head):
    """本轮**显式退役**的表面，在 HEAD 那一版里已清账几格 —— 地板的合法降幅。

    为什么地板需要一个降幅（R177 / BACKLOG 204）：`FLOOR_WENT_BACK` 要挡的是"清账退步"，
    而撤掉一个不存在的表面也会让已清账行数下降。两件事在纯计数上长得一模一样，
    所以要么禁止撤词表（等于逼着幽灵表面继续产生假进度），要么把"撤"变成**显式登记**的量。
    这里选后者：降幅只从登记过的表面来，没登记的照旧红。
    """
    retired = set((data or {}).get("retired_surfaces") or {})
    if not retired or not head:
        return 0
    head_surfaces = set(head.get("surfaces") or [])
    return len([1 for pair in _cleared_pairs(head) if pair[0] in retired and pair[0] in head_surfaces])


def retirement_problems(data, head):
    """撤词表项的四条判据（每条都能红，红名各不一样）。"""
    out = []
    retired = (data or {}).get("retired_surfaces") or {}
    surfaces = set((data or {}).get("surfaces") or [])
    for name, reason in sorted(retired.items()):
        if name in surfaces:
            out.append(("RETIRED_STILL_LISTED",
                        "%s：登记了退役，却还在 surfaces 名册里 ⇒ 撤项没撤干净" % name))
        if not isinstance(reason, str) or len(reason.strip()) < 20:
            out.append(("RETIRED_NO_REASON",
                        "%s：退役理由为空或太短（%r）⇒ 撤词表项要有产品面的理由，不是嫌格子多"
                        % (name, (reason or "")[:24])))
    if any(name in surfaces for name in retired):
        pass
    for row in (data or {}).get("rows") or []:
        if row.get("surface") in retired:
            out.append(("RETIRED_ROW_PRESENT",
                        "%s × %s：表面已退役却还留着这一行 ⇒ 表与名册自相矛盾"
                        % (row.get("surface"), row.get("state"))))
    if head:
        head_surfaces = set(head.get("surfaces") or [])
        lost = set(s for s, _ in _cleared_pairs(head) if s not in surfaces)
        undeclared = sorted(lost - set(retired))
        for name in undeclared[:3]:
            out.append(("RETIRED_UNDECLARED",
                        "%s：HEAD 里它有已清账的格子，本轮名册里没了，却没登记退役 ⇒ "
                        "『少了一行』与『清账退步』分不开（R143 那一族）" % name))
        if lost and not head_surfaces:
            out.append(("RETIRED_HEAD_UNREADABLE", "HEAD 那张表读得出行数却读不出名册 ⇒ 无从对账"))
    return out


def head_floor_cleared(root=None, path="docs/motion_surface_ledger.json"):
    """读 **HEAD 那一版**的 `floor_cleared`；读不到返回 None（= 这一格没判，不是通过）。

    为什么要外部基准（R143 / BACKLOG 184）：`BELOW_FLOOR` 拿"已清账格子数"与 JSON 里的地板比，
    而地板自己就在同一份可写的文件里 ⇒「删五行 + 地板降五」这一刀今天不会红。
    单调性必须压在**表外**的一个量上（同 AGENTS.md 里"守卫要读字段不能读散文"那一族）。
    基准读不到时不红：CI 的 shallow checkout 里 `HEAD` 仍然存在，所以读不到只可能是"不在 git 工作树里"；
    那一格由 `scripts/tests/test_motion_surface_gate.py` 断言"在本仓库里必须读得到"，
    于是"没判"与"判过"仍然分开记账。
    """
    import subprocess
    root = root or repo_root()
    try:
        raw = subprocess.check_output(["git", "-C", root, "show", "HEAD:" + path],
                                      stderr=subprocess.DEVNULL)
    except Exception:
        return None
    try:
        value = json.loads(raw.decode("utf-8")).get("floor_cleared")
    except Exception:
        return None
    return value if isinstance(value, int) else None


def check(data, root=None, head_floor=None):
    """返回 [(代码, 说明)]；空列表 = 全部合法。"""
    problems = []
    verdicts = data.get("verdicts") or []
    surfaces = data.get("surfaces") or []
    states = data.get("states") or []
    rows = data.get("rows") or []
    floor = data.get("floor_cleared")
    # 分母只能有一处定义。原来 check() 缺省时回落到 `verdicts`（全部），而 main() 回落到 `[]`
    # ⇒ 同一份表在"判红"与"报数"两件事上用了两套已清账集合（R143 #13）。
    cleared_verdicts = data.get("cleared_verdicts") or verdicts
    if not data.get("cleared_verdicts"):
        problems.append(("BAD_TABLE", "cleared_verdicts 缺失或为空 ⇒ 已清账的名册没有定义，"
                                      "地板与读数会各说一套"))
    if not verdicts or not surfaces or not states:
        problems.append(("BAD_TABLE", "verdicts / surfaces / states 三个名册都不许为空"))
    if not isinstance(floor, int):
        problems.append(("BAD_TABLE", "floor_rows 必须是整数"))
    elif floor > len(rows):
        problems.append(("FLOOR_LIES",
                         "floor_cleared=%d 大于实际行数 %d ⇒ 地板写成了愿望" % (floor, len(rows))))
    if isinstance(floor, int) and isinstance(head_floor, int) and floor < head_floor:
        problems.append(("FLOOR_WENT_BACK",
                         "floor_cleared 从 HEAD 的 %d 降到 %d ⇒ 清账只能往前不能往后。"
                         "这一格补的是 BELOW_FLOOR 唯一防不住的形状：删掉已清账的行**同时**把地板降下来"
                         "（R143 / BACKLOG 184）" % (head_floor, floor)))
    seen = set()
    root = root or repo_root()
    for i, row in enumerate(rows):
        surface = row.get("surface", "")
        state = row.get("state", "")
        where = "第 %d 行（%s × %s）" % (i + 1, surface or "?", state or "?")
        if surface not in surfaces:
            problems.append(("UNKNOWN_CELL", "%s：表面不在名册里" % where))
        if state not in states:
            problems.append(("UNKNOWN_CELL", "%s：状态不在名册里" % where))
        key = (surface, state)
        if key in seen:
            problems.append(("DUP_KEY", "%s：这个组合出现了不止一次" % where))
        seen.add(key)
        if row.get("verdict") not in verdicts:
            problems.append(("BAD_VERDICT", "%s：verdict=%r 不在词表 %s 里"
                             % (where, row.get("verdict"), verdicts)))
        reason = (row.get("reason") or "").strip()
        if len(reason) < MIN_REASON:
            problems.append(("REASONLESS", "%s：理由为空或短于 %d 字（没理由的 not-added 等于没决定）"
                             % (where, MIN_REASON)))
        evidence = (row.get("evidence") or "").strip()
        if not evidence:
            problems.append(("EVIDENCELESS", "%s：没有证据指针（哪个文件 / 哪个 BACKLOG / 哪个批次）" % where))
        elif not evidence_is_checkable(evidence):
            problems.append(("EVIDENCE_SHAPE",
                             "%s：指针不可复查（%r）—— 至少要含 Sources/ Tests/ docs/ scripts/ "
                             "BACKLOG 号 D-号 或批次号之一；轮次号只能附带（U-424）" % (where, evidence[:40])))
        problems.extend(evidence_problems(row, where, root))
    cleared = [r for r in rows if (r.get("verdict") or "") in cleared_verdicts]
    for surface in surfaces:
        if not any(r.get("surface") == surface for r in rows):
            problems.append(("SURFACE_UNCOVERED",
                             "表面「%s」一行都没有 ⇒ 往名册里加表面必须同时给它记账，"
                             "否则覆盖率会被分母稀释（U-425）" % surface))
    for state in states:
        if not any(r.get("state") == state for r in rows):
            problems.append(("STATE_UNCOVERED",
                             "状态「%s」一行都没有 ⇒ 同上，分母扩张要付账" % state))
    if isinstance(floor, int) and len(cleared) < floor:
        problems.append(("BELOW_FLOOR", "已清账格子数 %d 低于地板 %d ⇒ 清账只能往前不能往后"
                         % (len(cleared), floor)))
    return problems


def open_cells(data):
    """返回**还没被清账**的格子（表面, 状态），按字面顺序排。

    为什么要闸门自己列（R173）：`MOTION_LEDGER 未清账=59` 只给了一个数，
    而下一轮要挑格子判时必须知道"是哪 59 格"。以前这件事靠反推 JSON（读 `rows` 再手工求差），
    而反推出来的名单一旦与 `cleared_verdicts` 的词表不一致，就会把已判的格子当成没判 ——
    或者反过来把没判的当成判完了。列名单和数名单必须是**同一颗函数**。
    """
    cleared = set(data.get("cleared_verdicts") or [])
    judged = {(r.get("surface"), r.get("state"))
              for r in (data.get("rows") or []) if (r.get("verdict") or "") in cleared}
    return [(s, t) for s in (data.get("surfaces") or [])
            for t in (data.get("states") or []) if (s, t) not in judged]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="docs/motion_surface_ledger.json")
    ap.add_argument("--list-open", action="store_true",
                    help="逐格列出还没清账的格子（MOTION_LEDGER_OPEN k + 每格一行）")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        print("MOTION_LEDGER_NOT_RUN 文件不存在（%s）⇒ 记为没跑，不算通过" % args.path)
        return 2
    try:
        data = json.load(io.open(args.path, encoding="utf-8"))
    except ValueError as exc:
        print("MOTION_LEDGER_NOT_RUN JSON 读不出来：%s" % exc)
        return 2
    cells = len(data.get("surfaces") or []) * len(data.get("states") or [])
    rows = data.get("rows") or []
    counts = {}
    for row in rows:
        counts[row.get("verdict") or "?"] = counts.get(row.get("verdict") or "?", 0) + 1
    dist = " ".join("%s=%d" % (k, counts[k]) for k in sorted(counts))
    cleared_n = len([r for r in rows if (r.get("verdict") or "") in (data.get("cleared_verdicts") or [])])
    print("MOTION_LEDGER 表面=%d 状态=%d 格子=%d 行数=%d 已清账=%d 未清账=%d 地板=%s"
          % (len(data.get("surfaces") or []), len(data.get("states") or []), cells, len(rows),
             cleared_n, max(0, cells - cleared_n), data.get("floor_cleared")))
    print("MOTION_LEDGER_VERDICTS %s" % (dist or "无"))
    retired = data.get("retired_surfaces") or {}
    print("MOTION_LEDGER_RETIRED %d%s"
          % (len(retired), ("（" + "、".join(sorted(retired)) + "）") if retired else ""))
    if args.list_open:
        todo = open_cells(data)
        # 名单为空**不许**读成"活干完了"：也可能是词表漂了或 rows 被清空，
        # 所以这里打的是两种可能都写明的句子，而不是一句 OK（R99 那一族：空名单必须响）。
        print("MOTION_LEDGER_OPEN %d（= 格子 %d − 已清账 %d；0 只说明没有缺失格，不等于阶段二做完了）"
              % (len(todo), cells, cleared_n))
        if len(todo) != max(0, cells - cleared_n):
            print("MOTION_LEDGER_OPEN_MISMATCH 名单 %d 格、计数 %d 格 ⇒ 列名单与数名单分叉了"
                  % (len(todo), max(0, cells - cleared_n)))
        for surface, state in todo:
            print("OPEN %s × %s" % (surface, state))
    # 基准只对**仓库里那一份**有意义：`--path` 指到别处（沙箱夹具）时不比对，读成 None。
    in_repo = args.path == "docs/motion_surface_ledger.json"
    head = head_table() if in_repo else None
    head_floor = head_floor_cleared() if in_repo else None
    allowance = retirement_allowance(data, head)
    if head_floor is not None and allowance:
        head_floor -= allowance   # 只有**登记过**的退役才算降幅；没登记的少一行就是退步
    problems = check(data, head_floor=head_floor)
    problems += retirement_problems(data, head)
    print("MOTION_LEDGER_FLOOR_BASELINE head=%s now=%s"
          % ("无（不在 git 工作树里 ⇒ 这一格没判）" if head_floor is None else head_floor,
             data.get("floor_cleared")))
    for code, msg in problems:
        print("MOTION_LEDGER_%s %s" % (code, msg))
    print("MOTION_LEDGER_RESULT=%s 不合法格=%d（未清账不算不合法，它只是进度）"
          % ("ok" if not problems else "red", len(problems)))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
