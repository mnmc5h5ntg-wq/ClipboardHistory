#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 AGENT_VISUAL_ITERATION.md **解析**自评曲线，不许凭记忆抄。

为什么要脚本：R44 的台账初稿里我凭记忆写过一条"87 → 88 → …"的曲线，和账上任何读数都对不上。
曲线是最容易顺手编出来的一行，因为它看起来只是抄一遍已知数字。

两种写法都要认（历史遗留）：
  `### 自评 94 / 100`（正文里最常见）
  `**自评 94 / 100**`（Round 9 那种内联写法）
  `**94 / 100**`（R61 起的第三种：结论行不再写"自评"两个字）
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
# 第三种写法是 R61 起换的：结论行不再写"自评"两个字，只写 `**96 / 100**`。
# 第一版这里只认带"自评"的两种，于是 61/62/63/64 四轮**被静默跳过**
# —— 它不报错，只在 stderr 打一行 `ROUND_WITHOUT_SCORE=64`，
# 而正文那两行 `ROUNDS=58 last=60` 看着完全像是"账本就到这里"。
# ⇒ 这正是本文件顶部那段话讲的错，只不过这次坏的是**算曲线的尺**。
# 收紧成"必须是标题或加粗"，是为了不把正文里引用的旧分（"比 R61 的 96 低"）当成结论行。
SCORE = re.compile(r"(?:^###\s*自评\s*|[＊*]{2}(?:自评[：:]?\s*)?)(\d{2})\s*/\s*100", re.MULTILINE)


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
    # **尾轮守卫**：漏掉最后几轮不会让任何一行报错，只会让 `last=` 悄悄停在旧轮次上
    # （本轮就是靠这条才发现 61–64 四轮被跳过：`ROUNDS=58 last=60`，而账本里已经写到 Round 64）。
    text = io.open("AGENT_VISUAL_ITERATION.md", encoding="utf-8").read()
    heads = [m.group(1) + m.group(2) for m in HEAD.finditer(text)]
    if not readings or heads[-1] != readings[-1][0]:
        print("CURVE_DROPS_TAIL 文件最后一个轮次标题是 %s，曲线里最后一条是 %s ⇒ 尺漏了尾轮"
              % (heads[-1], readings[-1][0] if readings else "（空）"))
        return 1
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
    print("PHASE2 n=%d rounds=%s..%s mean=%.2f min=%d max=%d"
          % (len(ps), phase2[0][0], phase2[-1][0], sum(ps) / float(len(ps)), min(ps), max(ps)))
    print("PHASE2 CURVE: " + " · ".join(str(s) for s in ps))
    for cut in (46, 47):
        sub = [s for r, s in phase2 if int(re.match(r"\d+", r).group(0)) <= cut]
        print("PHASE2_TO_%s n=%d mean=%.2f" % (cut, len(sub), sum(sub) / float(len(sub))))
    print("SCORES_BY_ROUND " + " ".join("%s=%d" % (r, s) for r, s in readings[-4:]))


sys.exit(main())
