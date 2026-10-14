#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43 写进最终报告（计数、曲线、§5 教训、§6 账）。"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")
P = "AGENT_FINAL_REPORT.md"
s = io.open(P, encoding="utf-8").read()


def once(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


once("阶段二 全面独立动效与视觉审计 R9–R42）", "阶段二 全面独立动效与视觉审计 R9–R43）")
once("| 阶段二 **35 轮**审计（R9–R42） |", "| 阶段二 **36 轮**审计（R9–R43） |")
once("`AGENT_VISUAL_ITERATION.md` Round 9–42 |", "`AGENT_VISUAL_ITERATION.md` Round 9–43 |")
once("| 视觉台账 | U-31 … U-68（38 条；", "| 视觉台账 | U-31 … U-69（39 条；")
once("U-68 是「三处回执的 `.transition` 有两句从来没供电、一句缺半个键」，而它同时暴露了**旧守卫的粒度错**（文件级抓不到调用级）） | `AGENT_UI_AUDIT.md` 第 10–44 轮 |",
     "U-68 是「三处回执的 `.transition` 有两句从来没供电、一句缺半个键」，而它同时暴露了**旧守卫的粒度错**（文件级抓不到调用级）；\n"
     "U-69 是「R41 说收口的那一族英文原文，界面上其实还剩**三个**出口，而其中一个动作还把同一件事说两遍」） | `AGENT_UI_AUDIT.md` 第 10–45 轮 |")
once("| 决定台账 | D-069 … D-101 |", "| 决定台账 | D-069 … D-102 |")
once("| 判据 | 653 → **726** 例（29 skip / 0 failures；", "| 判据 | 653 → **733** 例（29 skip / 0 failures；")
once("· R42 **一张不加**：改的是中间态，112 帧逐字节不变 | `docs/frame_baseline.json` |",
     "· R42 一张不加（改的是中间态，112 帧逐字节不变）· R43 仍 112 张，但 `receipt-line` 从 430×56 换成 430×72"
     "（那张帧以前**在裁自己**，而且画的文案产品根本没说） | `docs/frame_baseline.json` |")
once("+ **M100–M198**（阶段二 99 支），全部 CAUGHT", "+ **M100–M205**（阶段二 106 支），全部 CAUGHT")
once("自评曲线（35 轮，Round 9–42，均值 **91.0**，最低 86）：",
     "自评曲线（36 轮，Round 9–43，均值 **91.0**，最低 86）：")
once("· 90 · **89** · 90 · 91 · 92。\n", "· 90 · **89** · 90 · 91 · 92 · 92。\n")

once("""沉淀下来的规矩（都已进仓库，不靠记忆）：""",
     """24. **R43：**"这条族收口了"这句话本身要有一条按族的账**。R41 把"写剪贴板失败"翻成人话时，
     我写的是"BACKLOG 58 收口"，而界面上还有**三个**出口在把 `error.localizedDescription` 拼进回执
     （导出反馈 / 导出存档 / 导入存档），其中一个还把同一件事**同时**弹模态 + 走行内。
     ⇒ 收口一条族的时候，账上必须写"这一族现在有几个出口、各在谁身上"，
     否则"收口"只是把**我找到的那一个**改了。
     同轮两条顺带：`receipt-line` 那张帧从 R14 起画的是**产品没说过的一句话**（全仓 grep 不到），
     换成真文案后 `contentMustFit` 当场红出第二件事 —— **那张帧一直在裁自己**（56 → 72pt）。
     一条按族判据（"夹具不许手写回执文案"）把第一件钉住，第二件由既有闸门自己喊出来。

沉淀下来的规矩（都已进仓库，不靠记忆）：""")

once("""| BACKLOG 61（R41 新开） |""",
     """| BACKLOG 62 **已收口**（R43） | 导出反馈既弹模态又发行内回执，而失败那句是 `localizedDescription` 直出 | R42 复核动效时看到、当时只记不修；本轮判完发现**不是一处是三处** | 措辞集中进 `Utilities/ReceiptWordings.swift`、模态删掉、原文进日志；判据 7 条 + 变异 M199–M205。剩一个开放问：**用户是否更喜欢模态**（人工批次 45.1） |
| BACKLOG 64 **被一条真问题挡住**（R43 复核） | 想把"调用点级"的动效守卫从 `ReceiptLine` 推广到 `NoticeBanner` | `ContentView` 那五条的驱动是**派生键** `noticeSignature`（把五条存在性压成 bitmask）⇒ 按名字匹配会**全部误报成没电** | 推广前先让判据会把派生键**展开**成它读的那几个状态；这五条本身确实有电（R22 量过像素） |
| BACKLOG 61（R41 新开） |""")

io.open(P, "w", encoding="utf-8").write(s)
print("最终报告已更新到 R43")
