#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异表跑之前先自检 needle：每一支 mutate_*.py 的原文 needle 现在还在不在、命中几次。

为什么要有它（R103 / U-301 那一族的正向版本）：
"接班者改了一行源码，前任的表里那根 needle 就空转"这件事已经撞过两次（M560 退役、M558 空转一整轮）。
电池能抓到它，但要等整卷跑到第 6 步、而且抓到之后是 **DID-NOT-RUN**（红），
而"红"和"这一轮白跑三小时"是同一件事。这一支把它挪到**跑之前**，只读、不建、不跑 swift。

它**不**做的事，写在这里免得被当成全能守卫：
- 不判变异文是否还合理、不判期望 verdict、不判目标测试是否还存在 —— 那些只有真跑一遍才知道；
- **分不清"needle 没了"与"此刻正有一支表把它注入了"**：命中=0 有两种成因。
  本轮实测到后者（电池第 6 步正在跑 r100 时读到 `M557 命中=0`，表跑完再读就 ok 了）。
  ⇒ 这一支要在电池**跑之前或跑完之后**读，别在中间读；读到 0 先怀疑时序，再怀疑死针（U-306 同族）。
- 覆盖不到的表会被**点名**，不会被算成"0 刀 ⇒ 干净"。
  第一版就是漏了这一格：它只认 `ARMS`，于是 12 张表里只有 5 张被读，`bad=0` 看着像全绿
  —— 与 U-294（新守卫的覆盖面必须自己量给自己看）同一族。现在结尾打 `covered=N/12`。
  第二版漏的是另一头：它只认 `.swift`，于是注入 `scripts/ui_probe_report.py` 的那支被报成
  "needle 藏在 lambda 里" —— **一个错的解释盖住了一次漏覆盖**，现在 `.py` 也算被注入的源。

用法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_needle_precheck.py
退出码：0=被覆盖的每一根 needle 都命中恰好 1 次；1=有 needle 命中 0 或 >1（打印是哪一支哪一刀）。
"""
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 仓库根**由自己所在位置推**，不写死。写死的那一版（R261）在 runner 上把
# `check_manifests` 打成 FileNotFoundError：它去开 `/Users/wangziyi/...`，而作业树在
# `/Users/runner/work/ClipboardHistory/ClipboardHistory` ⇒ 一格"本机绿 / 另一台机器只能报错"的判据
# 不是判据（run 39512069087 / STEP[9]，R262 现读；同一族先例见 R100 的夹具绝对路径）。
REPO = os.path.dirname(os.path.dirname(HERE))
TABLES = [
    "mutate_r245", "mutate_r247", "mutate_r249",
    "mutate_r242","mutate_r241", "mutate_r95_rhythm", "mutate_r94_order", "mutate_r96_triage", "mutate_r97_card", "mutate_r98_seed", "mutate_r98_card", "mutate_r99", "mutate_r100", "mutate_r100b", "mutate_r101", "mutate_r102", "mutate_r103", "mutate_r104", "mutate_r105", "mutate_r106", "mutate_r107", "mutate_r108", "mutate_r109", "mutate_r110", "mutate_r111", "mutate_r115", "mutate_r116", "mutate_r118", "mutate_r120", "mutate_r121", "mutate_r122", "mutate_r124", "mutate_r125", "mutate_r126", "mutate_r127", "mutate_r128", "mutate_r129", "mutate_r130", "mutate_r131", "mutate_r132", "mutate_r133", "mutate_r135", "mutate_r137", "mutate_r139", "mutate_r140", "mutate_r141", "mutate_r142", "mutate_r168", "mutate_r169", "mutate_r172", "mutate_r178", "mutate_r189", "mutate_r190", "mutate_r191", "mutate_r192", "mutate_r193", "mutate_r195", "mutate_r196", "mutate_r198", "mutate_r205", "mutate_r208", "mutate_r210", "mutate_r213", "mutate_r214", "mutate_r217", "mutate_r219", "mutate_r220", "mutate_r221", "mutate_r222", "mutate_r224", "mutate_r225", "mutate_r229", "mutate_r230", "mutate_r262", "mutate_r263", "mutate_r267", "mutate_r268", "mutate_r269", "mutate_r270", "mutate_r271", "mutate_r275", "mutate_r279", "mutate_r280", "mutate_r285", "mutate_r288", "mutate_r289", "mutate_r290", "mutate_r291", "mutate_r292", "mutate_r294", "mutate_r295", "mutate_r296", "mutate_r297", "mutate_r300", "mutate_r301", "mutate_r302", "mutate_r303", "mutate_r304", "mutate_r305", "mutate_r306", "mutate_r307", "mutate_r308", "mutate_r309", "mutate_r310", "mutate_r312", "mutate_r313", "mutate_r319", "mutate_r320", "mutate_r321", "mutate_r322", "mutate_r323", "mutate_r324", "mutate_r325", "mutate_r326", "mutate_r327", "mutate_r328", "mutate_r329", "mutate_r330", "mutate_r331", "mutate_r332", "mutate_r333", "mutate_r334", "mutate_r335", "mutate_r336",
            "mutate_r337",
            "mutate_r338",
            "mutate_r339",
            "mutate_r345",
            "mutate_r348",
            "mutate_r355",
            "mutate_r356",
            "mutate_r358",
            "mutate_r360",
            "mutate_r365",
            "mutate_r56_readings_channel",
            "mutate_r381_sidebar_icon",
            "mutate_r382_reset_disabled",
            "mutate_r383_shortcut_reset",
            "mutate_r384_login_receipt",
            "mutate_r385_reset_fade"]
# R355 / BACKLOG 430：这一格以前只认 **三位** 刀号（`M\d{3}`），而仓库从 R345 起已经在用四位
# （M1001…）：`arm_sites` 认不出 id ⇒ 整张表被读成「静态抽不出 needle」⇒ 那几把刀**从来没被针预检查过**
# （R355 自己那把 M1005 就是这么发现隐形的；同一次把 r348 的旧针重钉了）。四位只许往后长，不再加第二位边界。
MID = re.compile(r"^M\d{3,4}[a-z]?$")


# R262 放宽：引号两种都要认。旧版只认 `("M6NN",` 双引号形状 ⇒ 现读 **123 把刀 / 34 张表**
# 用 `('M6NN', …` 写 ARMS（r94/r96、r208…r230、r22–r28 那几批），它们对跨表查重**完全隐形** ——
# 与 306 结掉的那半个洞同源，只是这次坏在引号上而不是坏在语言上。
# 用反向引用锁"两边引号必须同种"，免得 `("M123',` 这种不合法写法也被抽成一个号。
# R381 / BACKLOG 430 的同一个洞在**跨表查重**这一侧还开着：`MID` 早已放宽到四位，
# 而下面这把 `ARM_LINE` 仍是 `M\d{3}` ⇒ M1001… 那批刀（含 r56 的 M1010）从来没进过跨表名册，
# 撞号在写的时候没人看得见。这里与 `MID` 对齐；正对照见
# `test_four_digit_arm_ids_are_not_invisible_to_the_cross_table_dedup`。
ARM_LINE = re.compile(r'^\s*\(?\s*(["\'])(M\d{3,4}[a-z]?)\1\s*,')


def arm_ids(path):
    """从表的**源码形状**里抽臂号：ARMS 里每一行都以 `("M6NN", …` 或 `('M6NN', …` 开头。

    为什么不用 `needles()` 抽出来的号：那个抽取只覆盖 27/42 张表（needle 藏在 lambda 里的抽不出），
    而 R141 与 R142 撞号那两张表恰好都在"抽不出"那一半里 ⇒ 照它们做的查重会**恒静默**。
    行首形状是两种形状共有的，所以这一格与 needle 抽取互相独立。
    `append` 那类运行期回填的行要跳过 —— mutate_r99 里 `results.append(("M554", …))` 出现过两次，
    那是同一把刀的两条路径，不是两个刀号（实测过：不跳过就报出一个假重复）。
    """
    with io.open(path, encoding="utf-8") as handle:
        lines = handle.readlines()
    out = []
    for line in lines:
        if "append" in line or "in only" in line:
            continue
        m = ARM_LINE.match(line)
        if m:
            # 放宽引号之后编号住在**第二**组（第一组是引号本身）。这一行若还取 group(1)，
            # 抽出来的是 `"` 或 `'` ⇒ 全部臂号塌成两个"号"，查重会报出一墙假撞号。
            # 这条不是猜的：现读放宽前 arms=572、放宽后 arms=695（+123 把单引号表里的刀），
            # 且 dupes=0 —— 如果组号取错，这里不可能还是 0。
            out.append(m.group(2))
    return out


def cross_table_ids(directory=HERE):
    """扫全部 `mutate_r*.py`，返回 (表文件, 跨表重复, 同表重复, 臂号总数)。

    目录可以是临时目录 ⇒ 电池能拿"人造的两张撞号表"当正对照，
    而不必赌仓库里恰好有一对重复号（R100 那一族：只印不拦的读数=没读数）。"""
    import glob
    ids, files = {}, sorted(glob.glob(os.path.join(directory, "mutate_r*.py")))
    for path in files:
        for mid in arm_ids(path):
            ids.setdefault(mid, []).append(os.path.basename(path)[:-3])
    # 重捕型刀住在 bash + `arms_r*/manifest.tsv`，旧版看不见它们 ⇒ 跨表撞号只在 python 表之间查得出来
    bash_tables = set()
    for table, mid, _k, _r, _o, _n, _w, _y in manifest_rows(directory):
        ids.setdefault(mid, []).append(table)
        bash_tables.add(table)
    files = files + sorted(glob.glob(os.path.join(directory, "arms_*", "manifest.tsv")))
    dupes = {k: sorted(set(v)) for k, v in ids.items() if len(set(v)) > 1}
    repeats = {k: v for k, v in ids.items() if len(v) != len(set(v))}
    return files, dupes, repeats, sum(len(v) for v in ids.values())


def is_source(path):
    """被注入的文件是什么：Swift 与 Python 都算。

    第一版只认 `.swift` ⇒ `mutate_r96_triage`（它注入的是 `scripts/ui_probe_report.py`）
    被当成"抽不出臂"，而那句解释写的是"needle 藏在 lambda 里"—— **一个错的解释盖住了一次漏覆盖**。
    """
    # R296：门本体的刀住在 bash 里（mutate_r296 的 M863 改的是 scripts/warning_gate.sh），
    # 白名单漏 .sh ⇒ 那把针恒报「命中 0」，预检 exit 1 —— 尺看不见不等于针不存在。
    # R377：r56 有四把刀打在 `ci.yml` 的并集整段上。`.yml` 不算源文件时，那四根针
    # 连"抽不出来"都不算，直接从覆盖面里消失（printed 行里只出现 6 把，而不是 10 把）。
    return path.endswith((".swift", ".py", ".sh", ".yml", ".yaml"))



def arm_sites(arm, default_path):
    """从一条臂里抽 (编号, 文件, [needle…])；抽不出来返回 None（调用方负责点名不覆盖谁）。

    历史上三种形状：
      `(编号, 说明, 文件, needle, 变异文, …)`            —— r95 / r97 / r99 / r100…r103
      `(编号, 说明, 文件, [(needle, 变异文), …], …)`      —— r102 的 M572（要同时造两个条件）
      `(编号, 说明, needle, 变异文, 期望…)`               —— r94 / r96 / r98 两支（文件在模块常量里）
    r94 那一支的 needle 藏在 `lambda t: sub_once(t, "…")` 里 ⇒ 静态抽不出，只能点名不覆盖。
    """
    if not isinstance(arm, (list, tuple)) or len(arm) < 4:
        return None
    mid = arm[0]
    if not (isinstance(mid, str) and MID.match(mid)):
        return None
    # 第四种形状（R169 那两张表）：`(编号, 文件, needle, 变异文, 期望)` —— 没有"说明"这一格。
    # 旧版不认识它，就把 needle 当"文件"、再退回 default_path（HARNESS）去数 ⇒ 数到 0，
    # 于是 R261 的预检把两把好刀报成"腐烂"（假指控，D-247 的反方向）。
    if isinstance(arm[1], str) and is_source(arm[1]) and isinstance(arm[2], str) and len(arm[2]) > 4:
        return (mid, arm[1], [arm[2]])
    third, fourth = arm[2], arm[3]
    if isinstance(third, str) and is_source(third):
        path = third
        # 第五种形状（R377 现读 r56）：`(编号, 说明, 文件, kind, 原文, 变异文, filter, heads)`。
        # 旧版把 kind 那一格当 needle（"swift"），于是它命中 0 次 —— 而 r56 从来没登记进 TABLES，
        # 这条错从来没有被打印出来（R377 补登记时才发现）。
        if isinstance(fourth, str) and fourth in ("swift", "python", "ci", "recapture", "bash") \
                and len(arm) > 4 and isinstance(arm[4], str):
            return (mid, path, [arm[4]])
        if isinstance(fourth, str):
            return (mid, path, [fourth])
        if isinstance(fourth, (list, tuple)):
            needles = [s[0] for s in fourth if isinstance(s, (list, tuple)) and s
                       and isinstance(s[0], str)]
            return (mid, path, needles) if needles else None
        return None
    if default_path and isinstance(third, str) and len(third) > 10:
        return (mid, default_path, [third])
    return None


def needles(module):
    """扫模块里所有列表，按**位置**认臂（三种命名：ARMS / MUTATIONS / NEEDLE_ARMS）。"""
    default_path = None
    for key in ("HARNESS", "FILE", "TARGET", "PATH", "VIEW"):
        value = getattr(module, key, None)
        if isinstance(value, str) and is_source(value):
            default_path = value
            break
    found = {}
    for value in vars(module).values():
        if not isinstance(value, (list, tuple)):
            continue
        for arm in value:
            site = arm_sites(arm, default_path)
            if site:
                found.setdefault(site[0], site)
    return [found[k] for k in sorted(found)]


KINDS = ("swift", "python", "recapture")


def manifest_rows(directory=HERE):
    """读 `arms_r*/manifest.tsv` —— 重捕型刀（M814…M818）住在 bash 脚本里，python 的 `ARMS` 形状抽不到。

    列形状沿用 R245 起就存在的那七列（`mutate_r245/247/249.py` 写的、`ledgers_r*.py` 读的），
    **不另造一份契约**（D-245：第二份定义处就是第二个可以各自算错的地方）：
        刀号  kind  被注入文件  .old 路径  .new 路径  期望红名  说明
    `.old` 的内容就是锚点：它在目标文件里必须**恰好命中一次**（0=针死了，>1=针不唯一）。
    格式不对直接抛，不许静默跳过。
    """
    import glob
    rows = []
    for path in sorted(glob.glob(os.path.join(directory, "arms_*", "manifest.tsv"))):
        table = os.path.basename(os.path.dirname(path))
        with io.open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) != 7:
                    raise ValueError("%s:%d 列数=%d（要 7 列：刀号 kind 文件 old new 期望 说明）"
                                     % (table, lineno, len(cols)))
                mid, kind, rel, oldf, newf, want, why = cols
                if not MID.match(mid):
                    raise ValueError("%s:%d 刀号形状不对：%r" % (table, lineno, mid))
                if kind not in KINDS:
                    raise ValueError("%s:%d kind=%r 不在 %s" % (table, lineno, kind, KINDS))
                rows.append((table, mid, kind, rel, oldf, newf, want, why))
    return rows


def anchor_hits(abs_path, anchor):
    """锚点命中次数 = **原文里这个块出现几次**（子串计数）。

    为什么不是整行相等：`.old` 存的是变异表真正拿去 `text.count(old)` 的那段文本，
    而它常常没有行首缩进（`arms_r245/M802.old`、`arms_r249/M811.old` 都是）。
    第一版按整行比 ⇒ 7 把老刀全被报成"针死了"，那是**尺的假话**：
    证人必须与它作证的那把尺同一颗（R68），变异怎么找针，预检就怎么找针。
    """
    if not os.path.exists(abs_path):
        return -1
    with io.open(abs_path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    needle = anchor.rstrip("\n")
    if not needle:
        return 0
    return text.count(needle)


def check_manifests(repo=REPO, directory=HERE):
    """返回 (行数, 坏行说明)。`.old` 必须命中恰好一次，且 `.new` 必须与 `.old` 不同（否则是空刀）。"""
    problems = []
    rows = manifest_rows(directory)
    for table, mid, kind, rel, oldf, newf, want, why in rows:
        with io.open(os.path.join(repo, oldf), encoding="utf-8") as handle:
            old_txt = handle.read().strip("\n")
        with io.open(os.path.join(repo, newf), encoding="utf-8") as handle:
            new_txt = handle.read().strip("\n")
        if old_txt == new_txt:
            problems.append("%s %s 的 .old 与 .new 一模一样 ⇒ 空刀" % (table, mid))
            continue
        hits = anchor_hits(os.path.join(repo, rel), old_txt)
        if hits != 1:
            problems.append("%s %s 锚点在 %s 命中 %d 次（要恰好 1 次）⇒ %s"
                            % (table, mid, rel, hits, want[:40]))
    return len(rows), problems


def bash_arm_ids(directory=HERE):
    """给 `cross_table_ids` 用：把 manifest 里的刀号也拉进跨表查重（旧版只看 python 表 ⇒ bash 刀可以撞号没人看见）。"""
    out = {}
    for table, mid, _k, _r, _o, _n, _w, _y in manifest_rows(directory):
        out.setdefault(table, []).append(mid)
    return out


def roster_gap(directory=HERE, tables=None):
    """现读缺口：**声明了臂却没登记进 `TABLES`** 的表（BACKLOG 310）。

    `cross_table_ids` 按 glob 扫全部表（所以撞号查重看得见它们），而 `main()` 的 needle 预检
    只走手写的 `TABLES` ⇒ 新写一张表忘了登记，就是**静默不覆盖**：锚点腐烂、R262 那两种坏法
    都会重新出现，而且报表上是一片绿。
    只数"静态抽得出臂"的那些：抽不出臂的表登记了也不进覆盖（那是 285 那族的"薄"），
    把两种相反的成因混成一个数，下一次就会有人去"修"错的那一半。
    """
    import glob
    registered = set(TABLES if tables is None else tables)
    gaps = []
    for path in sorted(glob.glob(os.path.join(directory, "mutate_r*.py"))):
        name = os.path.basename(path)[:-3]
        if name in registered:
            continue
        ids = arm_ids(path)
        if ids:
            gaps.append((name, len(ids)))
    return gaps


def main():
    bad = 0
    covered = 0
    arms_total = 0
    # R143 / U-483：臂号是**跨表唯一**的。R141 的 M666-M668 与 R142 的 M666-M669 撞了个正着，
    # 于是台账里一句「M668 CAUGHT」从此指的是两张表里的两把不同的刀。
    # 撞号在写的时候没人看见，因为每张表只数自己的 n=。这一格把它变成预检就响。
    cache = {}
    for name in TABLES:
        spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:            # 导入失败本身就是"这一支跑不了"
            print("%-18s !! 导入失败：%s" % (name, exc))
            bad += 1
            continue
        root = getattr(mod, "ROOT", REPO + "/ClipboardHistory")
        arms = needles(mod)
        if not arms:
            print("%-18s -- 静态抽不出 needle（替换是 lambda，或那一格根本不是文件路径）⇒ **不在覆盖里**" % name)
            continue
        covered += 1
        rows = []
        for mid, relpath, needles_list in arms:
            arms_total += len(needles_list)
            key = os.path.join(root, relpath)
            if key not in cache:
                try:
                    cache[key] = io.open(key, encoding="utf-8").read()
                except OSError as exc:
                    cache[key] = None
                    rows.append("%s/读文件失败(%s)" % (mid, exc.strerror))
                    bad += 1
            text = cache[key]
            if text is None:
                continue
            for needle in needles_list:
                n = text.count(needle)
                if n != 1:
                    rows.append("%s 命中=%d" % (mid, n))
                    bad += 1
                else:
                    rows.append("%s ok" % mid)
        print("%-18s %s" % (name, "；".join(rows)))
    files, dupes, repeats, arm_total = cross_table_ids()
    for mid, tables in sorted(dupes.items()):
        print("  DUPLICATE_ARM %s 出现在 %s" % (mid, " + ".join(tables)))
    for mid, tables in sorted(repeats.items()):
        print("  SAME_TABLE_REPEAT %s：%s" % (mid, " + ".join(tables)))
    bad += len(dupes) + len(repeats)
    # 台账里那句「刀数 131 → 133」从来没有仪器产过这个数（R143 复审查出来的）。
    # 这一行给的是**它自己口径**的数：全部 mutate_r*.py 里按行首形状声明的臂号数与表数，
    # 它不等于任何历史累计值，别拿它去对旧账（旧账那句先记 BACKLOG 184）。
    # R261 / BACKLOG 306：bash + manifest 里的重捕型刀也要被看见 —— 锚点（.old 的内容）
    # 必须在目标文件里恰好命中一次，`.new` 必须与 `.old` 不同（否则是空刀）。
    try:
        mani_rows_all = manifest_rows()
        mani_n, mani_bad = check_manifests()
    except ValueError as exc:
        print("BASH_ARM_MANIFEST_REFUSED %s ⇒ 名册格式坏了，这一支不许给绿" % exc)
        return 2
    for p in mani_bad:
        print("  BASH_ARM_ANCHOR %s" % p)
    bad += len(mani_bad)
    print("BASH_ARMS tables=%d arms=%d kinds=%s bad=%d"
          % (len({r[0] for r in mani_rows_all}), mani_n,
             ",".join(sorted({r[2] for r in mani_rows_all})), len(mani_bad)))
    print("ARM_TOTAL files=%d arms=%d dupes=%d repeats=%d" % (len(files), arm_total, len(dupes), len(repeats)))
    print("NEEDLE_PRECHECK tables=%d covered=%d arms=%d bad=%d"
          % (len(TABLES), covered, arms_total, bad))
    # 310：登记面要有仪器产数，不许靠"我以为通配到了"。这一行只测不判（判定在电池那格，
    # 它把这个数钉成地板 —— 新表忘了登记就会红）。
    gaps = roster_gap()
    print("TABLE_ROSTER registered=%d unregistered_with_arms=%d hidden_arms=%d named=%s"
          % (len(TABLES), len(gaps), sum(n for _, n in gaps),
             ",".join("%s(%d)" % (n, k) for n, k in gaps) or "无"))
    if covered != len(TABLES):
        print("  ↑ 覆盖不全：那几支的 needle 藏在 lambda 里，静态判不了（要判只能真跑）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
