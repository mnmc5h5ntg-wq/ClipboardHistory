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
# 松匹配只用来**审计那个正则本身**（R80）：尾轮守卫原来拿 HEAD 数标题，而 HEAD 正是它要审的那把尺 —— 我自己把 R80 的标题写成"## 第 80 轮（…）：…"（不带 `Round N ·`），于是那一轮被静默跳过，而尾轮守卫两边都用 HEAD，报的是"标题=79、曲线=79 ⇒ 没问题"。**拿被审的尺审自己，永远审不出东西。**
LOOSE_HEAD = re.compile(r"^##+\s*(?:Round\s+\d+|第\s*\d+\s*轮)", re.MULTILINE)
HEAD = re.compile(r"^##+\s*Round\s+(\d+)([a-z]?)(?:（[^）]*）)?\s*·", re.MULTILINE)
# 第三种写法是 R61 起换的：结论行不再写"自评"两个字，只写 `**96 / 100**`。
# 第一版这里只认带"自评"的两种，于是 61/62/63/64 四轮**被静默跳过**
# —— 它不报错，只在 stderr 打一行 `ROUND_WITHOUT_SCORE=64`，
# 而正文那两行 `ROUNDS=58 last=60` 看着完全像是"账本就到这里"。
# ⇒ 这正是本文件顶部那段话讲的错，只不过这次坏的是**算曲线的尺**。
# 收紧成"必须是标题或加粗"，是为了不把正文里引用的旧分（"比 R61 的 96 低"）当成结论行。
SCORE = re.compile(r"(?:^###\s*自评\s*|[＊*]{2}(?:自评[：:]?\s*)?)(\d{2,3})(?:\.\d+)?\s*/\s*(100|105)|"
                   r"[＊*]{2}均分\s*(\d{2}\.\d{1,2})[＊*]", re.MULTILINE)
# R98 / U-249 加的第二种写法：R93 起结论行换成 `**均分 91.3**`（七维表下面那一行），不带 "/100"
# ⇒ 93…98 六轮原来全部被静默跳过，而它照样打印 `last=92`。
# 两个分支各有一个捕获组 ⇒ findall 会给出元组，取值时要挑**非空的那一个**。


DERIVED = set()

# R143 审查轮（#22）：R139 起的表写的是 `| 名称 | 14/15 | 依据 |`，而原来只认 `| 14 |` ——
# 于是"没有结论行时从七维表推导"这条路对现在的表**从来没通过**（129…142 全报 DERIVED_BAD）。
# 现在两种都认，取分子；分母只用来确认它是"七分制"那一族，不参与求和。
DIM_ROW = re.compile(r"^\|\s*[^|]+?\s*\|\s*(\d{1,3})(?:\s*/\s*(\d{2,3}))?\s*\|", re.MULTILINE)


def derive_from_dimensions(section, round_no):
    """从"七维度自评"那张表算均值。**不新增任何数**：表里没有七行就不给推导值。

    要求正好七行 —— 少一行说明那张表被改过或标题认错，那时宁可不给数。
    小数按 `int()` 向下取整：曲线要的是"这一轮打了几分"，向下取整不会把 <90 的轮抬进 ≥90，
    而"少一轮"是不可接受的。
    """
    head = section.find(u"七维度自评")
    if head < 0:
        return None
    # findall 给元组 ⇒ 取分子（第一组）。分母不是 15 的行不算七分制的一行。
    # R152 / BACKLOG 190 · **分母决定这张表用的是哪一种约定**，两种都要归一到百分制：
    # 台账里同时存在两种七维表 —— 早期轮次每格写百分制（`| 名称 | 92 | 依据 |`，没有 `/15`），
    # R139 起每格写七分制（`| 名称 | 14/15 | 依据 |`）。旧代码一律 `sum/7`，于是同一条曲线上
    # 145=91（百分制表的均值）与 146=13（七分制表的均值）并存，而 `PHASE2 mean` 照样把两种量纲相加
    # （实测 `mean=170.69` —— 那个数从来不是分数）。第一版修法（一律 ×100/105）更坏：
    # 它把百分制那批推成 612 / 609 / 605（`max=617`），当场被自己打印的曲线抓到。
    pairs = [(int(a), (b or "").strip()) for a, b in DIM_ROW.findall(section[head:])]
    seven = [(num, den) for num, den in pairs if den in ("14", "15") and 0 <= num <= 15]
    hundred = [num for num, den in pairs if den == "" and 0 <= num <= 100]
    if len(seven) == 7:
        # 七分制：按每格自己的分母归一，再取均值 ⇒ 百分制。
        return int(round(sum(float(num) / float(den) for num, den in seven) / 7.0 * 100.0))
    if len(hundred) == 7:
        # 百分制：均值本身就是百分制，不再乘任何系数。
        return int(round(sum(hundred) / 7.0))
    print("DERIVED_BAD=%s 七维表读到七分制 %d 行 / 百分制 %d 行（要其中一种恰好 7 行）⇒ 这一轮不给推导值"
          % (round_no, len(seven), len(hundred)), file=sys.stderr)
    return None


def curve(path="AGENT_VISUAL_ITERATION.md"):
    text = io.open(path, encoding="utf-8").read()
    marks = [(m.start(), m.group(1) + m.group(2)) for m in HEAD.finditer(text)]
    readings = []
    for index, (start, round_no) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        found = [g for g in (m.groups() for m in SCORE.finditer(text[start:end])) if any(g)]
        if not found:
            derived = derive_from_dimensions(text[start:end], round_no)
            if derived is None:
                print("ROUND_WITHOUT_SCORE=%s" % round_no, file=sys.stderr)
                continue
            readings.append((round_no, derived))
            DERIVED.add(round_no)
            continue
        # 一轮里可能有多处"自评 N / 100"（修订说明会引用旧分），取**这一轮标题下第一个**。
        readings.append((round_no, int(float([g for g in found[0] if g][0]))))
    readings.sort(key=lambda item: (int(re.match(r"\d+", item[0]).group(0)), item[0]))
    return readings


def main():
    readings = curve()
    # **尾轮守卫**：漏掉最后几轮不会让任何一行报错，只会让 `last=` 悄悄停在旧轮次上
    # （本轮就是靠这条才发现 61–64 四轮被跳过：`ROUNDS=58 last=60`，而账本里已经写到 Round 64）。
    text = io.open("AGENT_VISUAL_ITERATION.md", encoding="utf-8").read()
    heads = [m.group(1) + m.group(2) for m in HEAD.finditer(text)]
    loose_heads = LOOSE_HEAD.findall(text)
    if len(loose_heads) != len(heads):
        print("CURVE_UNPARSED_HEADINGS 松匹配看到 %d 个轮次标题，HEAD 只认 %d 个 ⇒ "
              "有轮的标题写法漂移，那一轮的分数不会进曲线（尺审不了自己，只能换一把尺对表）"
              % (len(loose_heads), len(heads)))
        return 1
    if not readings or heads[-1] != readings[-1][0]:
        print("CURVE_DROPS_TAIL 文件最后一个轮次标题是 %s，曲线里最后一条是 %s ⇒ 尺漏了尾轮"
              % (heads[-1], readings[-1][0] if readings else "（空）"))
        return 1
    scores = [s for _, s in readings]
    print("ROUNDS=%d  first=%s  last=%s" % (len(scores), readings[0][0], readings[-1][0]))
    print("MEAN=%.1f  MIN=%d" % (sum(scores) / float(len(scores)), min(scores)))
    # R98：把**来源**打出来。`derived` 的数是从那一轮的七维表算的，不是作者写下的结论行；
    # 两种来源混在一条曲线里而看不出来，下一次就没人知道哪些轮次当时根本没写自评
    # （R98 就是这样发现 R93 / R94 两轮的 —— 曲线照打 `last=92`，而账本已经写到 97）。
    print("CURVE_DERIVED=%s" % (",".join(sorted(DERIVED)) or "none"))
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
    # **中间断档也要挡**（R100 / U-278 补的这一格）：上面那行 `GAPS=[99]` 原来只是**印出来**。
    # 本轮我往台账里插新章节时，编辑工具的 old_string 只填了上一节的标题行，
    # 于是"插入"变成"替换"，`## Round 99 · …` 整行被吃掉 —— 曲线照样打 `last=100`、
    # 均值照样算得出（少一轮而已），而 `exit` 是 0。
    # 尾轮守卫挡不住它（尾轮确实在），只有断档检查看得见，可它当时没有牙。
    # 这正是本文件顶部那段话讲的错，只不过这次坏在**报出来了却不负责**。
    # 结论行仍然全部打在闸门**之前**（R53 那条规矩）：先让这一遍的读数全部落地，再决定红不红。
    if missing:
        print("CURVE_GAP 曲线中间断了 %s ⇒ 少一轮不报错、只会让均值跟着错"
              "（出处：R100 的台账编辑吃掉了 Round 99 的标题行）" % missing)
        return 1
    return 0


sys.exit(main())
