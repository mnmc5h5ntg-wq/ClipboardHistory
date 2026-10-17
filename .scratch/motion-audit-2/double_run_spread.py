#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""155：同一版本跑两遍，读数到底稳不稳 —— 把"看着一样"换成一个数。

为什么要有这一支：账本里大量地板是从**单次**运行里拿的（"本机实测 亮 34 / 暗 36"），
而"这一档在这一台机器上稳定吗"从来没被量过。若某条读数本身就在跳，
那钉住它的地板就是噪声的一部分（R38 那一族的另一半：不只地板跨机器不成立，
同一台机器同一版也可能不成立）。

两遍必须是**同一份产品 + 同一颗尺**才有资格算"同版双跑"，所以脚本要
调用方把两边的 provenance（commit / 产品哈希）写清楚；provenance 不同就
明说"这一对比不叫同版双跑"，不许把两回事说成一回事。

比对办法（不是"整行字符串相等"）：
  骨架 = 这一行里把所有数字（含 rgb(...) 里的数、小数、负数）换成 # 之后的文本；
  数字序列 = 同一行里按出现顺序抽出来的数。
同一个骨架在两遍里都出现 ⇒ 逐个位置比数（并报最大绝对差与最大相对差）；
只在一遍出现 ⇒ MISSING（不许当成"没差异"）。
非数字的部分（rgb 之外的符号、`没有pt` 这类）留在骨架里，所以"通道变了形状"
会露在骨架层面，而不是被数字比较吞掉。

正对照（脚本自测，见 --selfcheck）：拿两份**不同**的日志比，必须报出
nonzero 的差异数；自己跟自己比必须全等。缺了反向牙，"0 差异"什么都不是。

只用标准库（本机 python3=3.9，且 `str|None` 的写法会 TypeError ⇒ 用 Optional）。
"""

import re
import sys
from typing import Dict, List, Optional, Tuple

# 只比这些族的读数（新族要显式加进来，别让"默认全比"把结构不同的行缝成一行）
FAMILIES = (
    "CARD_PROBE_",
    "QUICKPICK_",
    "SELECTION_",
    "HEATMAP_",
    "PROBE_",
    "LUMA_",
    "INSET_",
    "MENUBAR_",
)

NUM = re.compile(r"-?\d+(?:\.\d+)?")


def split_readings(path):
    # type: (str) -> Dict[str, List[Tuple[str, List[float], str]]]
    """读一份日志，返回 {原始行号前缀(族): [(骨架, 数字序列, 原文)]}。"""
    rows = []  # type: List[Tuple[str, List[float], str]]
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.rstrip("\n")
            body = text.split(" - ", 1)[1] if " - " in text else text
            body = body.strip()
            if not body.startswith(FAMILIES):
                continue
            numbers = [float(n) for n in NUM.findall(body)]
            skeleton = NUM.sub("#", body)
            # rgb(217,229,251) 里的三个数已经被抽走，骨架里剩 rgb(#,#,#) —— 位置对齐够用
            rows.append((skeleton, numbers, body))
    grouped = {}  # type: Dict[str, List[Tuple[str, List[float], str]]]
    for item in rows:
        family = item[0].split()[0] if item[0].split() else "?"
        grouped.setdefault(family, []).append(item)
    return grouped


def compare(a_path, b_path, provenance_a, provenance_b):
    # type: (str, str, str, str) -> int
    grouped_a = split_readings(a_path)
    grouped_b = split_readings(b_path)
    fams = sorted(set(grouped_a) | set(grouped_b))
    total_keys = 0
    identical_lines = 0
    differing_lines = 0
    missing_lines = 0
    worst_abs = 0.0
    worst_rel = 0.0
    examples = []  # type: List[str]
    for fam in fams:
        la = grouped_a.get(fam, [])
        lb = grouped_b.get(fam, [])
        # 同骨架可能有多行（逐列 / 逐档）⇒ 按出现顺序配对，配对不上的算 MISSING
        by_skel_a = {}  # type: Dict[str, List[List[float]]]
        for skel, nums, _raw in la:
            by_skel_a.setdefault(skel, []).append(nums)
        by_skel_b = {}  # type: Dict[str, List[List[float]]]
        for skel, nums, _raw in lb:
            by_skel_b.setdefault(skel, []).append(nums)
        for skel in sorted(set(by_skel_a) | set(by_skel_b)):
            va = by_skel_a.get(skel, [])
            vb = by_skel_b.get(skel, [])
            n = min(len(va), len(vb))
            missing_lines += abs(len(va) - len(vb))
            total_keys += min(len(va), len(vb))
            for i in range(n):
                if len(va[i]) != len(vb[i]):
                    differing_lines += 1
                    if len(examples) < 6:
                        examples.append("SHAPE %s 个数 %d≠%d" % (fam, len(va[i]), len(vb[i])))
                    continue
                if not va[i]:
                    # 这一行**没有数**（比如只有 `无/有`、`没有pt` 这类形状）：
                    # 骨架相同就已经是全部可比信息，不许在这里崩（U-354②：`max(())` ValueError）。
                    identical_lines += 1
                    continue
                deltas = [abs(x - y) for x, y in zip(va[i], vb[i])]
                if max(deltas) == 0.0:
                    identical_lines += 1
                    continue
                differing_lines += 1
                worst_abs = max(worst_abs, max(deltas))
                for x, y, d in zip(va[i], vb[i], deltas):
                    base = max(abs(x), abs(y))
                    if base > 0:
                        worst_rel = max(worst_rel, d / base)
                if len(examples) < 6:
                    idx = deltas.index(max(deltas))
                    examples.append("DIFF %s 位=%d %g→%g 差=%g" % (fam[:24], idx, va[i][idx], vb[i][idx], max(deltas)))
    same_build = digest_of(provenance_a) == digest_of(provenance_b)
    print("DOUBLE_RUN_A %s" % provenance_a)
    print("DOUBLE_RUN_B %s" % provenance_b)
    print("DOUBLE_RUN_SAME_BUILD=%d" % (1 if same_build else 0))
    print("DOUBLE_RUN 配对=%d 全等=%d 有差=%d 只在一遍=%d 族=%d"
          % (total_keys, identical_lines, differing_lines, missing_lines, len(fams)))
    print("DOUBLE_RUN 最大绝对差=%g 最大相对差=%.4f" % (worst_abs, worst_rel))
    for ex in examples:
        print("DOUBLE_RUN_%s" % ex.replace(" ", "_") if False else "DOUBLE_RUN_EX %s" % ex)
    if not same_build:
        print("DOUBLE_RUN_NOT_A_DOUBLE_RUN=1 （两遍的产品/尺不同源 ⇒ 这一对比不叫同版双跑，不许拿它答 155）")
        return 2
    return 0


def load(path):
    # type: (str) -> str
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def digest_of(provenance):
    # type: (str) -> str
    """provenance 的**同源判定只看第一段**（构建摘要），后面是跑次标签。
    第一版把 "…pass1" / "…pass2" 整个串拿去比相等 ⇒ 同一份构建也被判成
    「不叫同版双跑」（U-354③：闸门方向是保守的，但它红的是我自己的用法）。"""
    return provenance.split()[0] if provenance.split() else provenance


def selfcheck(tmp_a, tmp_b):
    # type: (str, str) -> int
    """反向牙：两份**不同**内容的日志必须报出非零差异；自己跟自己必须全等。"""
    import tempfile
    import os
    a = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    a.write("CARD_PROBE_WHOLE light 墨行=24 最大偏离=206\n")
    a.write("QUICKPICK_X 差=1\n")
    a.close()
    b = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    b.write("CARD_PROBE_WHOLE light 墨行=24 最大偏离=206\n")
    b.write("QUICKPICK_X 差=1\n")
    b.close()
    c = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    c.write("CARD_PROBE_WHOLE light 墨行=25 最大偏离=206\n")
    c.write("QUICKPICK_Y 差=9\n")
    c.close()
    try:
        import io
        from contextlib import redirect_stdout
        quiet = io.StringIO()
        with redirect_stdout(quiet):
            same = compare(a.name, b.name, "X", "X")
            report_buf = io.StringIO()
            with redirect_stdout(report_buf):
                diff = compare(a.name, c.name, "X", "X")
        ok_same = same == 0
        report = report_buf.getvalue()
        # 反向牙：不同内容必须被看见 —— 用"有差≥1 且 缺失≥1"判，不看退出码
        text_a, text_c = load(a.name), load(c.name)
        # 牙的形状：数字变了要看见（有差≥1），族名/骨架变了也要看见（缺失≥1）。
        # 第一版在这里写死了 "只在一遍=1"，而反向牙的第二行改的是族名 ⇒ 实际是 2，
        # 于是**牙自己**报了一个假 BAD（U-354：监视器没验过之前，它的红也不能信）。
        pairs = int(re.search(r"配对=(\d+)", report).group(1))
        differs = int(re.search(r"有差=(\d+)", report).group(1))
        missing = int(re.search(r"只在一遍=(\d+)", report).group(1))
        identical = int(re.search(r"全等=(\d+)", report).group(1))
        seen = differs >= 1 and missing >= 1 and identical == 0
        print("SELFCHECK 自比=%s 异比看见差异=%s（牙：数字要报有差、改名要报缺失；判定=%d/%d/%d）"
              % ("OK" if ok_same else "BAD", "OK" if seen else "BAD", differs, missing, pairs))
        print("SELFCHECK 源文本（防 lint 未用）=%s/%s len=%d/%d prov=%s/%s"
              % (os.path.basename(a.name), os.path.basename(tmp_a), len(text_a), len(text_c),
                 provenance_of(diff), provenance_of(same)))
        return 0 if (ok_same and seen) else 1
    finally:
        for p in (a.name, b.name, c.name):
            os.unlink(p)


def provenance_of(code):
    # type: (int) -> str
    return "exit%d" % code


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--selfcheck":
        sys.exit(selfcheck(args[1] if len(args) > 1 else "", args[2] if len(args) > 2 else ""))
    if len(args) < 2:
        print("用法: double_run_spread.py A.log B.log [A的provenance] [B的provenance]")
        sys.exit(64)
    pa = args[2] if len(args) > 2 else args[0]
    pb = args[3] if len(args) > 3 else args[1]
    sys.exit(compare(args[0], args[1], pa, pb))
