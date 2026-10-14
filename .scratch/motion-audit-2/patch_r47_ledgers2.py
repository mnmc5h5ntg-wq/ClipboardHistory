#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R47 第二段台账：STATE / BACKLOG 70+71 / 批次 49 / 最终报告对账 / 看图补记。

所有数字都来自本轮**真跑过的**读数：
  743 tests / 29 skipped / 0 failures   <- /tmp/r47-full.log
  CAPTURE_GATE_RESULT=ok 红=0 NOT_RUN=0 <- 同日志跑闸门
  116 帧 CHANGED=0 MISSING=0 ADDED=0     <- scripts/frame_baseline.py --against working compare
  脚本 101 全绿 / WARN_COUNT=0            <- unittest discover / swift build
  曲线 40 轮 均值 91.3 最低 86            <- .scratch/motion-audit-2/curve_from_ledger.py
"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


STATE = '''

---

## R47 · 那条 A/B 判的是采样，不是淡入（第 49 轮 / U-73 / D-106）

- **靶是上一轮自己撞出来的**：R46 为拿像素证据跑了动效胶片套件，`testHeatmapFadeIsNotVisibleToThisRuler`
  在本机报红 —— 而它报红的理由是**它自己用的轴不可靠**（两臂峰值 0.226 / 0.226 完全相同，只有帧数不同，
  帧数正是这个文件写着「会随采样相位漂」的量）。
- **改法**：判据抽成纯函数 `fadeVisibility(elapsedOnA:elapsedOnB:elapsedOff:peakOn:declared:interval:)`，
  换成时长轴 + 四个门槛（下限 0.3×声明 / **上限 声明+2×间隔** / 归因看两遍里较短的那个 /
  A/A 不一致 ⇒ `.inconsistent` 只打印不红）。真值表 12 格。
- **上限是读数逼出来的，不是设计出来的**：本机反复抓到 `258 / 259 / 260 / 265 / 307ms` 的变化段，
  而这条过渡**声明只有 160ms** ⇒ 那不是淡入。没有上限，判据会把它读成「尺子终于看见了」，
  然后催我把场景放进 `Scenario.all()` —— **把探针的毛病当产品进步**。加上限后 3/3 稳定「看不见」。
- **`流畅度` 这一维今天写死了**：离屏 `cacheDisplay` 抓模型树，纯 opacity 交叉淡活在 presentation 层
  ⇒ 这条通道对淡入的可见性是 0。抬它要换通道（真屏抓帧 / presentation 采样），不是再改判据。
  连续三轮 94 不体面，但比在曲线上虚涨一分诚实。
- **本轮看图看出的两条新账**（不是读代码读出来的）：
  BACKLOG 70 = 读数函数名叫 `changedRun…` 但它的取法**不要求连续**，两段变化之间隔着静止帧也会被
  首尾相连算成一段 ⇒ 那正是 258–307ms 的一个候选解释（**假设，未证**）；
  BACKLOG 71 = 暗色帧里图例最低那一格几乎与背景同色，而**梯子相邻两档能不能被分开**这件事从来没有一条判据
  ——「1 次的那天」如果和「0 次的那天」看着一样，这张图就在骗读数的人。
- **顺手抓到自己写的解析器的错**：为了「曲线必须从台账生成」新写的 `curve_from_ledger.py`
  第一版正则不认 `Round 29d` 这种带字母后缀的轮次，于是**静默少一轮**、均值跟着错。
  是拿它算出来的 38 轮对上报里写的 39 轮才发现的 —— 判据是「两处独立数字对不上」，不是「看起来没事」。
- **验证**：743 tests / 29 skipped / 0 failures、闸门 `红=0 NOT_RUN=0`、脚本 101 全绿、
  `swift build` 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`（本轮 `Sources/` 未动）、
  变异 M223–M229 七支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。自评 **94 / 100**。**CI 待读。**
- **本轮不换装**：`Sources/` 一个字节没动，装了旧包和装新包界面上不会有任何差别。
- **下一步（R48）**：① BACKLOG 70 的连续性 —— 把 `changedRunElapsedMilliseconds` 改成真正的「run」，
  并用两波带空隙的形状钉住它（它同时给 BACKLOG 69 一个答案）；② BACKLOG 71 的梯子档间可分辨性；
  ③ 读 R46/R47 的 CI，特别是新地板闸门第一次在 runner 上的读数。
'''

BACKLOG = '''
70. **`changedRunElapsedMilliseconds` 量的不是「一段」，是「首尾」**（R47 看图 + 读码，未证）：
    它的取法是 `moving = fractions.indices.filter { $0 >= peak * stepFloorRatio }` 然后取
    `moving.first` 到 `moving.last` —— **不要求连续**。于是「触发后 7ms 内变完，静止 250ms，
    又有一帧因为别的原因变了」会被读成一段 258ms 的「画面还在变」。
    这正好是 BACKLOG 69 那串 258–307ms 读数的一个候选解释，而且解释的是**尺**不是产品。
    怎么证（不许猜着修）：先给这条通道打一行 per-frame 序列（帧号 + 相对时刻 + 变化量），
    抓到一次长读数时看它是不是**两波带空隙**；是 ⇒ 把函数改成「取包含峰值的那一段连续 run」，
    并补真值表（单波 / 两波带空隙 / 峰值在第二波）+ 变异。
    **注意代价**：这个函数不止那条 A/B 在用（R2 起多处判据用它当时间读数），
    语义一改，别的判据的读数会一起变 ⇒ 必须逐条复核，不许只改不核。
71. **热图梯子的相邻档从来没有一条判据**（R47 看图看出）：`VisualHeat.ladder = [0.18, 0.34, 0.56, 0.85]`
    加 `empty = 0.055` 一共五个台阶，R45 量的是「悬停那一圈相对于整条数据范围响不响」，
    **没有量过「第 1 档与空格子能不能分开」**。本轮看暗色帧：图例最左那一格几乎与背景同色。
    如果 1 次/天 与 0 次/天 在暗档下肉眼分不开，这张图就在把「没数据」和「有一点数据」抹成同一个意思 ——
    这是数据可读性缺陷，不是审美问题。
    怎么判：拿 R45 已有的渲染夹具（`renderCell(level:hovered:appearance:scale:)`）扩一条判据，
    要求**相邻两档**的均值差 ≥ 恰可察觉台阶（沿用 `perceptibleBand255 = 18` 那把尺，
    但地板要从实测推导，不许照抄），亮/暗两档、1×/2× 两尺度各跑一遍。
    如果暗档第 1 级过不了 ⇒ 改 `empty` 或改梯子（**改数值必须同时改这条判据的期望**，
    并且帧基线要 `update`，因为格子颜色会变）。
'''

BATCH = '''

---

## 批次 49 · R47 本轮**没有可人工验收的产品改动**（U-73 / D-106）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮改的是一条测试判据用的轴（帧数 → 时长）。

本轮看图时新冒出**两个只有你能一句话判掉**的问题，麻烦顺手回答：

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 49.1 | 系统设置切到**暗色**，打开 设置 → 统计，看热图最下面那行图例「少 ▢ ▢  ▢ 多」 | 第一格你**看得见**吗？看得见就答「看得见」，看不见就答「看不见」 | 我这边它和背景只差一点点，而「差一点点」到底算不算能读，是人的判读，不是我的阈值 |
| 49.2 | 同一天里找**只复制过 1 次**的格子（tooltip 会写「1 条」），和旁边**0 次**的灰格比 | 不看 tooltip 能不能分出哪个是 1 条 | 这决定 BACKLOG 71 是「审美小瑕疵」还是「图在骗人」，优先级差一级 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47 共 16 条**。
最想要回答的两条还是 45.1（导出反馈数据不再弹模态，你更喜欢哪一种）与
47.1（热图格子鼠标划过去**那一圈到底出现没有** —— 帧能证明它画得出来，证明不了真鼠标会触发它）。
'''

AUDIT_ADDEND = '''
### 本轮看图看出的两条新账（不是读代码读出来的）

看的是 `heatmap-cell-strip-hover-90x140-light`、`heatmap-populated-430x250-{light,dark}`
（都在 `/tmp/r47-frames/`，与基线逐字节相同）：

| 位点 | 看到什么 | 记成 |
|---|---|---|
| 暗色帧的图例「少 ▢ ▢  ▢ 多」 | 最左那一格与背景几乎同色；亮色帧里同一格是可读的 | **BACKLOG 71**：梯子相邻档（尤其第 1 档 vs 空格子）从来没有一条判据 —— R45 量的是悬停圈相对数据范围响不响，没量过档间 |
| 那条 A/B 的读数形状 | `changedRunElapsedMilliseconds` 取的是 `moving.first … moving.last`，**不要求连续** ⇒ 两波变化之间隔着静止帧也会被算成一段 | **BACKLOG 70**：这是 258–307ms 的候选解释（解释尺，不解释产品）；改法要先抓一次 per-frame 序列证实，**不许猜着修** |

另外：为「曲线必须从台账生成」新写的解析器第一版**漏掉了 `Round 29d`**（正则不认字母后缀），
算出 38 轮、报告写 39 轮 —— 两处独立数字对不上才被抓到。修完的解析器给出的曲线与台账逐格一致：
阶段二 40 轮（Round 9–47）、均值 91.3、最低 86、低于 90 的仍是那七轮（R19/R20/R22/R29d/R31/R35/R39）。
'''


REPORT_PAIRS = [
    ("| 阶段二 **39 轮**审计（R9–R46） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
     "| `AGENT_VISUAL_ITERATION.md` Round 9–46 |",
     "| 阶段二 **40 轮**审计（R9–R47） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
     "| `AGENT_VISUAL_ITERATION.md` Round 9–47 |"),
    ("| 决定台账 | D-069 … D-105 | `AGENT_DECISIONS.md` |",
     "| 决定台账 | D-069 … D-106 | `AGENT_DECISIONS.md` |"),
    ("自评曲线（39 轮，Round 9–46，均值 **91.2**，最低 86）：\n"
     "91 · 90 · 92 · 93 · 94 · 95 · 96 · 93 · 95 · 91 · **86** · **89** · 91 · **87** · 90 · 92 · 91 · 92 · 91 · 92 · 90 · **89** · 90 · **89** · 94 · 90 · 90 · **89** · 90 · 91 · 90 · **89** · 90 · 91 · 92 · 92 · 93 · 94 · 94。\n",
     "自评曲线（40 轮，Round 9–47，均值 **91.3**，最低 86）：\n"
     "91 · 90 · 92 · 93 · 94 · 95 · 96 · 93 · 95 · 91 · **86** · **89** · 91 · **87** · 90 · 92 · 91 · 92 · 91 · 92 · 90 · **89** · 90 · **89** · 94 · 90 · 90 · **89** · 90 · 91 · 90 · **89** · 90 · 91 · 92 · 92 · 93 · 94 · 94 · 94。\n"),
    ("（这一行**每次都是从 `AGENT_VISUAL_ITERATION.md` 的轮次标题配着分数重算出来的**，不是抄记忆：",
     "（这一行**每次都是从 `AGENT_VISUAL_ITERATION.md` 的轮次标题配着分数重算出来的**，不是抄记忆 —— "
     "R47 起这句话有了兑现物：`.scratch/motion-audit-2/curve_from_ledger.py`。"
     "它顺带抓到自己的第一版**漏掉 `Round 29d`**（正则不认字母后缀 ⇒ 少一轮、均值跟着错，"
     "是拿它算出的 38 与报告里写的 39 对不上才暴露的）。解析器的教训记在 U-73：\n"
     "一条「必须从台账生成」的规矩，如果生成器本身没被对过账，它就只是把抄记忆换成了抄脚本。"),
    ("**R45 112 → 116**：第一次有悬停态的帧（`heatmap-cell-strip-still` / `-hover`），而既有 112 张 `CHANGED=0` —— 那次重构没动任何一个像素，这句话是可数的 |",
     "**R45 112 → 116**：第一次有悬停态的帧（`heatmap-cell-strip-still` / `-hover`），而既有 112 张 `CHANGED=0` —— 那次重构没动任何一个像素，这句话是可数的 · "
     "R46 / R47 各一张不加（两轮都零产品改动，116 帧 `CHANGED=0 MISSING=0 ADDED=0`） |"),
    ("+ **M100–M222**（阶段二 123 支）",
     "+ **M100–M229**（阶段二 130 支）"),
]


def main():
    # 先**全部预检**再落盘：上一轮栽过——四个文件已追加、第五个锚点不存在，
    # 于是脚本半路抛错，重跑会把前四个再写一遍。预检把失败挪到还没动任何文件的时候。
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    for old, _ in REPORT_PAIRS:
        assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])
    for path in ("AGENT_STATE.md", "AGENT_BACKLOG.md", "AGENT_UI_AUDIT.md",
                 "docs/MANUAL_TEST_v1.4.9_round3.md", "AGENT_FINAL_REPORT.md"):
        assert os.path.exists(path), path

    with io.open("AGENT_STATE.md", "a", encoding="utf-8") as f:
        f.write(STATE.lstrip("\n"))
    with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
        f.write(BACKLOG)
    with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
        f.write(AUDIT_ADDEND)
    with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
        f.write(BATCH)

    patch("AGENT_FINAL_REPORT.md", REPORT_PAIRS)
    print("R47 第二段台账已写入")


main()
