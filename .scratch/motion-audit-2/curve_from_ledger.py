#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 AGENT_VISUAL_ITERATION.md **解析**自评曲线，不许凭记忆抄。

为什么要脚本：R44 的台账初稿里我凭记忆写过一条"87 → 88 → …"的曲线，和账上任何读数都对不上。
曲线是最容易顺手编出来的一行，因为它看起来只是抄一遍已知数字。

两种写法都要认（历史遗留）：
  `### 自评 94 / 100`（正文里最常见）
  `**自评 94 / 100**`（Round 9 那种内联写法）
标题也要认两种：`## Round 47 · …` 与 `## Round 31（边界轮）· …` —— 带全角括号的漏一次就少一个读数。
"""
import io
import re
import sys

# 后缀那个组不是装饰：账本里真有 `## Round 29d · …`（R29 的第四段）。
# 第一版没写它，于是 `29d` 整条被漏掉 —— 它落在 Round 29 的区间里，
# 而那一区间的第一个"自评 N / 100"是 Round 29 自己的，29d 的分数被静默吞掉。
# 少一个读数不会报错，只会让均值跟着错（这正是文件顶部那段话讲的错）。
HEAD = re.compile(r"^##+\s*Round\s+(\d+)([a-z]?)(?:（[^）]*）)?\s*·", re.MULTILINE)
SCORE = re.compile(r"自评\s*(\d{2,3})\s*/\s*100")


def curve(path="AGENT_VISUAL_ITERATION.md"):
    text = io.open(path, encoding="utf-8").read()
    marks = [(m.start(), m.group(1) + m.group(2)) for m in HEAD.finditer(text)]
    readings = []
    for index, (start, round_no) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        found = SCORE.findall(text[start:end])
        if not found:
            print("ROUND_WITHOUT_SCORE=%s" % round_no, file=sys.stderr)
            continue
        # 一轮里可能有多处"自评 N / 100"（修订说明会引用旧分），取**这一轮标题下第一个**。
        readings.append((round_no, int(found[0])))
    readings.sort(key=lambda item: (int(re.match(r"\d+", item[0]).group(0)), item[0]))
    return readings


def main():
    readings = curve()
    scores = [s for _, s in readings]
    print("ROUNDS=%d  first=%s  last=%s" % (len(scores), readings[0][0], readings[-1][0]))
    print("MEAN=%.1f  MIN=%d" % (sum(scores) / float(len(scores)), min(scores)))
    print(" · ".join(str(s) for s in scores))
    # 断档检查按**数字**做（29d 不是 30 的替代品，它是 29 与 30 之间多出的一轮）。
    numbers = sorted({int(re.match(r"\d+", r).group(0)) for r, _ in readings})
    missing = [n for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
    print("GAPS=%s" % (missing or "none"))
    # 只报阶段二（Round 9 起）的曲线：前八轮属于上一阶段，口径不同，不许混进均值。
    phase2 = [(r, s) for r, s in readings if int(re.match(r"\d+", r).group(0)) >= 9]
    ps = [s for _, s in phase2]
    print("PHASE2 n=%d rounds=%s..%s mean=%.1f min=%d"
          % (len(ps), phase2[0][0], phase2[-1][0], sum(ps) / float(len(ps)), min(ps)))
    print("PHASE2 CURVE: " + " · ".join(str(s) for s in ps))
    for cut in (46, 47):
        sub = [s for r, s in phase2 if int(re.match(r"\d+", r).group(0)) <= cut]
        print("PHASE2_TO_%s n=%d mean=%.2f" % (cut, len(sub), sum(sub) / float(len(sub))))
    print("SCORES_BY_ROUND " + " ".join("%s=%d" % (r, s) for r, s in readings[-4:]))


main()
