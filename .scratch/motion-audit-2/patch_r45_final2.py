#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R45 收尾：人工批次 47 + AGENT_FINAL_REPORT 的计数。

（`patch_r45_final.py` 被一次 sed 式修补弄坏了 —— 那一版里的 `\\"` 在 Python 里是
"反斜杠 + 字符串结束"，直接 SyntaxError。这一版全部改用「」，并且曲线**现算 + assert**，
不抄记忆：R44 就是凭记忆写曲线写错过一次。）
"""
import io
import os
import re

os.chdir("/Users/wangziyi/Codex_Project0")


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


t = io.open("AGENT_VISUAL_ITERATION.md", encoding="utf-8").read()
cur = None
scored = []
pat_score = re.compile(r"(?:^### 自评 |\*\*自评 )(\d+) ?/ ?100")
for line in t.split("\n"):
    m = re.match(r"^## (Round [0-9]+[a-z]?)(?:（[^）]*）)?", line)
    if m:
        cur = m.group(1)
        continue
    if cur:
        s = pat_score.search(line)
        if s:
            scored.append((cur, int(s.group(1))))
            cur = None
vals = [v for r, v in scored if int(re.match(r"Round (\d+)", r).group(1)) >= 9]
n = len(vals)
mean = sum(vals) / n
below = sum(1 for v in vals if v < 90)
assert n == 38, ("阶段二读数应为 38 轮（Round 9…45，含 29d）", n)
assert vals[-1] == 94, vals[-1]
print("曲线 n=%d mean=%.4f min=%d below90=%d" % (n, mean, min(vals), below))
curve = " · ".join(str(v) if v >= 90 else "**%d**" % v for v in vals) + "。"

OLD_CURVE = ("91 · 90 · 92 · 93 · 94 · 95 · 96 · 93 · 95 · 91 · **86** · **89** · 91 · **87** · 90 · 92 · "
             "91 · 92 · 91 · 92 · 90 · **89** · 90 · **89** · 94 · 90 · 90 · **89** · 90 · 91 · 90 · "
             "**89** · 90 · 91 · 92 · 92 · 93。")
assert OLD_CURVE in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read(), "旧曲线锚点没找到"

BATCH = '''

---

## 批次 47 · R45 热图悬停那一圈（U-71 / D-104）

机器侧的证据：判据 +7（可见性 20 读数、归因 10、倍率 10、带选择器真值表 7 格、令牌真值表、
源码路由守卫、夹具自检）；帧基线 112 → 116，**既有 112 张逐字节不变**（这次重构没改外观）；
变异 M210–M215 六支全 CAUGHT。
已换装到 `/Applications/时间剪史.app`（sha `8753ffa722a09701…`，存档 103 条一条没丢）。

| # | 怎么试 | 我的预测（先写下再去对） | 如果不对 |
|---|---|---|---|
| 47.1 | 设置 → 统计 → 把鼠标**慢慢划过**热图那些格子（不要点） | 被指的那一格外面出现**一圈描边**：亮色下深灰、暗色下浅灰；1pt 宽、贴着格子自己的圆角，不改变格子的深浅 | 一圈都没有 ⇒ 本轮量的只是「表达」，坏的是「触发」那一半（`.onHover` 没回调）—— 那是 R14 三条合成通道的老问题（BACKLOG 67），请告诉我，我按产品缺陷查而不是按文案查 |
| 47.2 | 同一处，划到**最深**的那一格（复制最多的那天） | 那一圈仍然看得见，且**不吞掉深浅**：你仍能判断这一格比邻居深 | 深浅被盖住了 ⇒ 0.55 太重，本轮那条倍率判据（≤ 数据全幅度，实测 0.46–0.75）就是假的。把截图给我，我按令牌改 |
| 47.3 | 划到**未来那几天**（最右列里今天之后的格子） | 什么都没有：没有格子、也就没有圈（画成灰格等于宣称「那天你一次都没复制」） | 出现了灰格 ⇒ U-30 缺陷 5 那一族回来了，优先级最高 |
| 47.4 | 顺手回答 R43 欠的一问（BACKLOG 65）：设置 → 隐私里那两行回执，右侧的 × **贴着第一行**，而横幅的「知道了」是垂直居中的 | 我认为两件事不该统一：× 是「收起这一条」，贴着首行更像「这个 × 管这条」 | 你觉得它只管第一行 = 读错了 ⇒ 那就统一成居中，我按你的读法改，不按我的辩护 |

**批次 43、44、45 共 12 条仍然有效**（其中 45.1「导出反馈数据不再弹模态」是我最想要回答的一条）。
'''
with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
    f.write(BATCH)

R = "AGENT_FINAL_REPORT.md"
patch(R, [
    ("阶段二 全面独立动效与视觉审计 R9–R44", "阶段二 全面独立动效与视觉审计 R9–R45"),
    ("| 阶段二 **37 轮**审计（R9–R44） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 | `AGENT_VISUAL_ITERATION.md` Round 9–44 |",
     "| 阶段二 **38 轮**审计（R9–R45） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 | `AGENT_VISUAL_ITERATION.md` Round 9–45 |"),
    ("| 视觉台账 | U-31 … U-70（40 条；", "| 视觉台账 | U-31 … U-71（41 条；"),
    ("（`noticeSignature` 把五条存在性压成 bitmask）供电，按名字匹配的守卫会把它们**全部误报成没电**。） | `AGENT_UI_AUDIT.md` 第 10–46 轮 |",
     "（`noticeSignature` 把五条存在性压成 bitmask）供电，按名字匹配的守卫会把它们**全部误报成没电**；\n"
     "U-71 是第三种：**一句注释替产品做了决定** —— `VisualHeat.hoverStroke` 写着「发丝线在深色格子上会消失，"
     "所以描边要重一档」，而那一圈从没被画出来量过（112 张帧里没有一张带悬停态） | `AGENT_UI_AUDIT.md` 第 10–47 轮 |"),
    ("| 决定台账 | D-069 … D-103 | `AGENT_DECISIONS.md` |", "| 决定台账 | D-069 … D-104 | `AGENT_DECISIONS.md` |"),
    ("| 判据 | 653 → **735** 例（29 skip / 0 failures；", "| 判据 | 653 → **742** 例（29 skip / 0 failures；"),
    ("**M100–M209**（阶段二 110 支）", "**M100–M215**（阶段二 116 支）"),
    ("自评曲线（37 轮，Round 9–44，均值 **91.1**，最低 86）：",
     "自评曲线（38 轮，Round 9–45，均值 **%.1f**，最低 86）：" % mean),
    (OLD_CURVE, curve),
    ("· R43 仍 112 张，但 `receipt-line` 从 430×56 换成 430×72（那张帧以前**在裁自己**，而且画的文案产品根本没说）",
     "· R43 仍 112 张，但 `receipt-line` 从 430×56 换成 430×72（那张帧以前**在裁自己**，而且画的文案产品根本没说）"
     "· R44 一张不加（零产品改动）· **R45 112 → 116**：第一次有悬停态的帧（`heatmap-cell-strip-still` / `-hover`），"
     "而既有 112 张 `CHANGED=0` —— 那次重构没动任何一个像素，这句话是可数的"),
    ("| **BACKLOG 64 做了一半**（R44） |",
     "| **BACKLOG 66 / 67 新开**（R45） | ① 动效覆盖地板在 runner 上从 `4/4` 掉到 `3/4`"
     "（`notice-banner-dismiss` 只采到 2 帧）而那一关**仍然绿** —— 地板判的是「这些判据跑没跑」，"
     "所以「掉了一臂」没人报，我是靠人肉对比 run 日志才发现的；② 悬停的**触发**那一半仍只能人眼验"
     "（R14 三条合成通道全断） | 采样会漂是事实，但把地板抬成 4/4 会让它恒红（R39/R42 那一族的反面） | "
     "地板需要一个会红的形状（同一臂连续两次 not-run ⇒ 红）；触发那一半挂在批次 22 与 47.1 |\n"
     "| **R45 的靶：一句注释替产品做了决定**（U-71 / D-104） | `VisualHeat.hoverStroke` 写着"
     "「发丝线在深色格子上会消失」，而那一圈从没被量过 | R44 收口时写下「下一轮优先做能产生像素证据的那类」 | "
     "把单格画法抽成 `DailyCopyHeatmapCell(isHovered:)` ⇒ 表达那一半可离线渲染：20 条可见性读数"
     "（36.10–75.50/255，地板 18）+ 10 条归因（带外 0.00）+ 新立一条「悬停不许比数据响」"
     "（0.46–0.75 倍；M213 把那一圈画两遍 ⇒ 1.16 会红）。**0.55 与 primary 都不改**：量完站在正确一侧 |\n"
     "| **BACKLOG 64 做了一半**（R44） |"),
])
print("R45 收尾台账已写入")
