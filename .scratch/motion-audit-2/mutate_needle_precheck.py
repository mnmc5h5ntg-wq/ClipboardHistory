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
REPO = "/Users/wangziyi/Codex_Project0"
TABLES = ["mutate_r95_rhythm", "mutate_r94_order", "mutate_r96_triage", "mutate_r97_card",
          "mutate_r98_seed", "mutate_r98_card", "mutate_r99", "mutate_r100", "mutate_r100b",
          "mutate_r101", "mutate_r102", "mutate_r103", "mutate_r104", "mutate_r105", "mutate_r106", "mutate_r107", "mutate_r108", "mutate_r109", "mutate_r110", "mutate_r111", "mutate_r115", "mutate_r116", "mutate_r118", "mutate_r120", "mutate_r121", "mutate_r122", "mutate_r124", "mutate_r125", "mutate_r126", "mutate_r127", "mutate_r128", "mutate_r129", "mutate_r130", "mutate_r131", "mutate_r132", "mutate_r133", "mutate_r135", "mutate_r137", "mutate_r139", "mutate_r140", "mutate_r141", "mutate_r142", "mutate_r168", "mutate_r169", "mutate_r172", "mutate_r178", "mutate_r189", "mutate_r190", "mutate_r191", "mutate_r192", "mutate_r193", "mutate_r195", "mutate_r196", "mutate_r198", "mutate_r205", "mutate_r208", "mutate_r210", "mutate_r213", "mutate_r214"]
MID = re.compile(r"^M\d{3}[a-z]?$")


ARM_LINE = re.compile(r'^\s*\("(M\d{3}[a-z]?)"\s*,')


def arm_ids(path):
    """从表的**源码形状**里抽臂号：ARMS 里每一行都以 `("M6NN", …` 开头。

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
            out.append(m.group(1))
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
    dupes = {k: sorted(set(v)) for k, v in ids.items() if len(set(v)) > 1}
    repeats = {k: v for k, v in ids.items() if len(v) != len(set(v))}
    return files, dupes, repeats, sum(len(v) for v in ids.values())


def is_source(path):
    """被注入的文件是什么：Swift 与 Python 都算。

    第一版只认 `.swift` ⇒ `mutate_r96_triage`（它注入的是 `scripts/ui_probe_report.py`）
    被当成"抽不出臂"，而那句解释写的是"needle 藏在 lambda 里"—— **一个错的解释盖住了一次漏覆盖**。
    """
    return path.endswith(".swift") or path.endswith(".py")



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
    third, fourth = arm[2], arm[3]
    if isinstance(third, str) and is_source(third):
        path = third
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
    print("ARM_TOTAL files=%d arms=%d dupes=%d repeats=%d" % (len(files), arm_total, len(dupes), len(repeats)))
    print("NEEDLE_PRECHECK tables=%d covered=%d arms=%d bad=%d"
          % (len(TABLES), covered, arms_total, bad))
    if covered != len(TABLES):
        print("  ↑ 覆盖不全：那几支的 needle 藏在 lambda 里，静态判不了（要判只能真跑）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
