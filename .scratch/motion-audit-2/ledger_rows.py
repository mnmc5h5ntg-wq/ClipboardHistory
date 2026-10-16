#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从验证电池的日志里**解析**出台账 §8 那十二行，而不是手抄。

为什么要有它（R99 / U-264 那一族的根治）：§8 那一格历史上错过三次 ——
① 手抄抄成了上一轮的数（R99 报告里停在"796 例 / 112 帧 / M509"）；
② 抄成了**本轮的中间态**（R101 §8 的"已量"来自被最后一次产品改动取代的那一版，U-287①）；
③ 某一格**根本没打值**，而"0 个缺陷"比红更坏（R92 立的"缺值算红"）。
这一版把三件事都交给机器：**值只能从指定那一份日志里解析出来；解析不到就非 0 退出，绝不补一个看起来合理的数**。

它同时是一格**对账**：`--expect-keywords` 之外的关键字（比如新加的一轮读数）不会被它静默丢掉，
因为第 12 行"本轮读数"是把日志里所有 `CARD_*` / `PROBE_*` 汇总行**原样搬运**，不重排版。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledger_rows.py <verify.log> [--pass 2]
退出码：0=十二格全有值；1=有格子缺值（打印缺哪几格）；2=用法错。
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
    ("摘要缺值", r"^SUMMARY_MISSING=\d+"),
    ("总结论", r"^VERIFY_OK=\d+"),
]

# 本轮读数：把这些前缀的行原样搬进表格（不重排、不改数字）。
READINGS = re.compile(r"^(CARD_[A-Z_]+|HEATMAP_[A-Z_]+|PROBE_[A-Z_]+|LUMA_[A-Z_]+)=")


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
    print("### 8. 验证（十二格，数字全部由 `ledger_rows.py` 从 `%s` 解析%s）" % (log.name, pass_label))
    print()
    print("| 格子 | 读数 |")
    print("|---|---|")
    print("\n".join(out))
    print()
    print("ROWS_TOTAL=%d ROWS_MISSING=%d" % (len(ROWS) + 1, len(missing)))
    if missing:
        print("缺值的格子：%s ⇒ 不许用任何'看起来合理'的数补上" % ", ".join(missing))
        return 1
    if readings:
        print("=== 本轮读数全量（贴进 §8 下面那一节，别改数字） ===")
        print("\n".join(readings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
