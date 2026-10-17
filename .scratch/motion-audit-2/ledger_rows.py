#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从验证电池的日志里**解析**出台账 §8 那十几行，而不是手抄。

为什么要有它（R99 / U-264 那一族的根治）：§8 那一格历史上错过三次 ——
① 手抄抄成了上一轮的数（R99 报告里停在"796 例 / 112 帧 / M509"）；
② 抄成了**本轮的中间态**（R101 §8 的"已量"来自被最后一次产品改动取代的那一版，U-287①）；
③ 某一格**根本没打值**，而"0 个缺陷"比红更坏（R92 立的"缺值算红"）。
这一版把三件事都交给机器：**值只能从指定那一份日志里解析出来；解析不到就非 0 退出，绝不补一个看起来合理的数**。

它同时是一格**对账**：`--expect-keywords` 之外的关键字（比如新加的一轮读数）不会被它静默丢掉，
因为第 12 行"本轮读数"是把日志里所有 `CARD_*` / `PROBE_*` 汇总行**原样搬运**，不重排版。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledger_rows.py <verify.log> [--pass 2] \
      [--must-include CARD_PROBE_WHOLE CARD_PROBE_WHOLE_FILL CARD_PROBE_GEOMETRY]
`--must-include` 是**本轮自己声明**的读数族：任何一族在 §8 的搬运结果里一行都没有 ⇒ 退出码 1。
它拦的是"我新装了读数，但台账里没有它的数字"（R107 / U-339），不拦产品。
退出码：0=每一格都有值且声明的族都在；1=有格子缺值或有声明的族被丢掉（打印缺哪几格/哪几族）；2=用法错。
"""
import re
import sys
from pathlib import Path

# 每一格 = (台账里的行名, 从日志里抓什么的正则)。正则必须**只**匹配电池自己打出的键，
# 不匹配任何我可能手写进日志的说明文字（所以全部锚定行首）。
ROWS = [
    ("构建", r"^BUILD_EXIT=\d+ BUILD_WARNING_LINES=\d+"),
    ("全量测试", r"^TEST_EXIT=\d+ .*"),
    ("在屏那一卷", r"^PROBE_EXIT=\d+ .*"),
    ("捕获卷", r"^CAPTURE_EXIT=\d+ .*"),
    ("帧基线", r"^FRAMES_EXIT=\d+ .*"),
    ("脚本电池", r"^PY_EXIT=\d+ .*"),
    ("变异表", r"^MUT_EXIT=\d+ .*"),
    ("台账编号守卫", r"^LEDGER_EXIT=\d+ .*"),
    ("曲线仪器", r"^VIS_EXIT=\d+ .*"),
    # R103：断言/读数包含对账进了电池（`CONTAIN_EXIT`）⇒ §8 也要能解析它，
    # 否则这一格的值只能靠我手抄，而"手抄"正是这个脚本存在的理由（U-264 那一族）。
    ("断言包含对账", r"^CONTAIN_EXIT=\d+ .*"),
    ("摘要缺值", r"^SUMMARY_MISSING=\d+"),
    ("总结论", r"^VERIFY_OK=\d+"),
]

# 本轮读数：把这些前缀的行原样搬进表格（不重排、不改数字）。
READINGS = re.compile(r"^(CARD_[A-Z_]+|HEATMAP_[A-Z_]+|PROBE_[A-Z_]+|LUMA_[A-Z_]+)="
                   r"|^CARD_PROBE_[A-Z_]+ |^QUICKPICK_")   # R103：证人那一行是空格分隔的读数，不是 key=
                   # R105：浮层左轴那三行（`QUICKPICK_SEARCH_AXIS` / `_AXIS_CAPABILITY` / `_AXIS_DECLINED`）
                   #   同样是空格分隔 ⇒ 走第二个分支。R104 的 §8 把它们漏在了搬运之外
                   #   （那一轮 §8 的"本轮读数"只有 `CARD_*`），本轮补上 —— 判据的结论行必须与它的
                   #   数字一起进台账，否则下一轮又要靠我记得去 grep（U-264 那一族）。
                   # R107 / U-339：第二个分支原来**只认 `CARD_PROBE_ARM`** 这一个名字，
                   #   于是本轮新装的三族（`CARD_PROBE_WHOLE` / `_WHOLE_FILL` / `_GEOMETRY`，
                   #   还有 R102 就在的 `CARD_PROBE_ARM_INSET`）在 §8 里**一行都没出现** ——
                   #   而这一轮的结论恰恰建立在它们上面。放宽到"整族前缀 + 空格"，
                   #   并加 `--must-include`：本轮声明哪几族是它的判据读数，缺任何一族就非 0 退出。
                   #   为什么不做成"所有大写行都搬"：`PROBE_ELIGIBILITY` 一类有几十行，
                   #   全搬会把 §8 冲成噪声；声明式让**每一轮自己**回答"我这轮的读数是哪几族"。


def grab(text, pattern):
    hits = [l for l in text.splitlines() if re.match(pattern, l)]
    return hits[-1].strip() if hits else None   # 同一格打多次 ⇒ 取最后一次（重跑覆盖前一次）


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0].startswith("--"):
        print(__doc__)
        return 2
    log = Path(args[0])
    if not log.exists():
        sys.stderr.write("日志不存在：%s\n" % log)
        return 2
    pass_label = ""
    if "--pass" in args:
        pass_label = "（**这一份是 pass-%s**）" % args[args.index("--pass") + 1]
    # 本轮声明"我的判据读数是哪几族"（U-339：不声明的话，新族会被白名单静默丢掉）。
    must = []
    if "--must-include" in args:
        i = args.index("--must-include") + 1
        while i < len(args) and not args[i].startswith("--"):
            must.append(args[i])
            i += 1
        if not must:
            sys.stderr.write("--must-include 后面一个前缀都没有 ⇒ 这等于没声明\n")
            return 2
    text = log.read_text(encoding="utf-8")
    missing, out = [], []
    for name, pat in ROWS:
        v = grab(text, pat)
        if v is None:
            missing.append(name)
            out.append("| %s | !! 日志里没有这一格 ==" % name)
        else:
            out.append("| %s | `%s` |" % (name, v))
    readings = [l for l in text.splitlines() if READINGS.match(l)]
    out.append("| 本轮读数（%d 行，原样搬运） | %s |"
               % (len(readings), "；".join("`%s`" % r for r in readings[:3]) if readings else "!! 没有"))
    print("### 8. 验证（%d 格，数字全部由 `ledger_rows.py` 从 `%s` 解析%s）"
          % (len(ROWS) + 1, log.name, pass_label))
    print()
    print("| 格子 | 读数 |")
    print("|---|---|")
    print("\n".join(out))
    print()
    print("ROWS_TOTAL=%d ROWS_MISSING=%d" % (len(ROWS) + 1, len(missing)))
    # 结论行打在闸门之前（R93 那一族：闸门一 return，它下面那行就永远不会出现在日志里）。
    families = {}
    for l in readings:
        head = l.split(" ", 1)[0].split("=", 1)[0]
        families[head] = families.get(head, 0) + 1
    print("READINGS_FAMILIES 搬运=%d 族=%s"
          % (len(readings), " ".join("%s:%d" % kv for kv in sorted(families.items()))))
    lacking = [p for p in must if not any(l.startswith(p) for l in readings)]
    print("READINGS_MUST_INCLUDE 声明=%d 缺=%d%s"
          % (len(must), len(lacking), (" 缺的族=" + ",".join(lacking)) if lacking else ""))
    if missing:
        print("缺值的格子：%s ⇒ 不许用任何'看起来合理'的数补上" % ", ".join(missing))
        return 1
    if lacking:
        print("!! 本轮自己声明的读数族有族一行都没搬进 §8 —— 台账里的结论将没有它的数字（U-339）")
        return 1
    if readings:
        print("=== 本轮读数全量（贴进 §8 下面那一节，别改数字） ===")
        print("\n".join(readings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
