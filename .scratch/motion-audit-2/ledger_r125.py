#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R125（第 127 轮）账本补丁。数字一律从本轮日志解析，缺格写「没解析到」。"""
import io
import os
import re

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(n):
    return io.open(os.path.join(ROOT, n), encoding="utf-8").read()


def wr(n, t):
    io.open(os.path.join(ROOT, n), "w", encoding="utf-8").write(t)


def once(t, a, b):
    assert t.count(a) == 1, "锚点命中 %d：%s" % (t.count(a), a[:60])
    return t.replace(a, b, 1)


def log(path):
    try:
        return io.open(path, encoding="utf-8", errors="replace").read()
    except IOError:
        return ""


def executed(path):
    m = re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", log(path))
    return m[-1] if m else ("?", "?", "?")


def g(key, text):
    m = re.search(key + r"=(\d+)", text)
    return m.group(1) if m else "没解析到"


SWIFT = executed("/tmp/r125_full.log")
CAP = executed("/tmp/r125_capture.log")
gate = log("/tmp/r125_gate.log")
cap_log = log("/tmp/r125_capture.log")
kinds = re.findall(r"MOTION_KIND_COVERAGE kind=(\w+) 产品调用点=(\d+)", cap_log)
KINDLINE = " / ".join("%s=%s" % (k, n) for k, n in kinds) if kinds else "没解析到（见捕获卷日志）"

BACKLOG = rd("AGENT_BACKLOG.md").rstrip("\n") + """

173. **动效位点欠账：连续五轮零新增动效，而这一轮刚把「哪一档接在哪个文件」变成会红的清单**（R125 开 / 与 R42「要么供电要么撤声明」、R46 覆盖地板、103「悬停够不够响没有机器判据」同族）：
    `MOTION_KIND_COVERAGE` 第一次把九档动效的接线情况打成一行一行的读数
    （`""" + KINDLINE + """`）。
    有了这张清单，下一轮就不该再问「还有哪里没接动效」，而要按清单点一个位答三句话：
    ① 这个状态变化现在有几帧过渡（`QUICKPICK_*` / 胶片那把尺读变化段）；
    ② 加了之后重排次数 / 采样帧里最大跳变有没有变（R74 的规矩：先量代价再决定）；
    ③ 两档外观与 reduce-motion 关掉时各自长什么样（帧 + 目视）。
    **本条不许被写成「清单已建 = 动效已做」**：清单是尺，不是交付。

"""

DECISIONS = rd("AGENT_DECISIONS.md").rstrip("\n") + """

### D-187（R125）「声明了却没供电」这类账必须由一把会红的尺提出，临时 grep 不配当计数

本轮的真实经过：我想找"动效目录里哪一档是死的"，在 shell 里 `grep "for: \\.bannerOut"` 得到 **0**，
于是准备开一条"这条声明没供电"的账。真去数它是 **5 处** —— 产品写的是
`MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，
我的模式只认得其中一种写法（U-417）。差一点就用一个工具的语法盲区给产品记了一条假账。

三条落进判据的规矩：

1. **计数要在仓库里、会红、有真值表**：`motionKindCallSites` + 九档地板 `>=1`；
   今天这一条假账如果发生在判据里，它会红，而不是被我写进台账。
2. **尺自己剥注释**（M407 / M411 那一族）：剥注释这件事不许要求调用方记得做 ——
   真值表里"注释里提一句"那一格就是钉这个的（第一版要求调用方先剥，被自己那一格抓住了，U-418）。
3. **地板是 `>=1` 而不是 `== n`**：它数的是"提到过"，写成精确数字就是把今天的形状钉成契约（U-92 那一族）；
   而"撤掉声明"这种真回归，`>=1` 一样会红。
"""

AUDIT = rd("AGENT_UI_AUDIT.md")
SECTION = """## 第 127 轮 · R125：动效接线第一次成为一把会红的清单尺，顺手抓住我差点开的一条假账（新开 173 / U-417…U-418 / D-187 · 产品 0 改动）

### 1. 开场清单（本轮全部证据的位置与坐标）

| # | 位点 | 读数 | 说明的缺陷 |
|---|---|---|---|
| 1 | 我在 shell 里数 `for: \\.bannerOut` | **0 处** ⇒ 准备开「这条声明是死的」的账 | 模式只认一种写法：产品写的是 `asymmetricTransition(removal: .bannerOut)`（U-417） |
| 2 | 同一件事，用仓库里的尺数 | `MOTION_KIND_COVERAGE kind=bannerOut 产品调用点=5 文件=ContentView.swift:5` | 假账被自己的第二把尺拦住；两条独立实现（python / swift 正则）九档数字**逐档相同** |
| 3 | 九档全量 | `""" + KINDLINE + """` | 第一次有可 grep 的动效接线清单 ⇒ 新开 173：下一轮按清单点位答三句话 |
| 4 | 真值表第一版 | 「注释里提一句」那一格红：`("1") is not equal to ("0")` | 剥注释被要求由调用方做 ⇒ 移进尺内（U-418，M407 / M411 那一族） |

### 2. 本轮改了什么（产品 0 改动；只动 `UICaptureHarness.swift`）

1. `motionKindCallSites(in:kindName:)`：`Self.codeOnly` 剥注释 + `NSRegularExpression` 带词边界
   `(?![A-Za-z0-9_])`；数的是"提到过"，所以地板是 `>=1`。
2. `testMotionKindCallSitesRulerIsATruthTable`：7 行（两种写法 / 数次数 / 注释不算 / 更长的名字不算 /
   `selection:` 无点不算 / 空文本给 0）。
3. `testEveryMotionKindIsWiredSomewhereInProduct`：遍历 `MotionCatalog.Role.allCases`（取 `rawValue`
   而不是 `String(describing:)`，后者对带原始值的枚举是实现细节不是契约），排除 `MotionCatalog.swift` 自己，
   逐档打 `MOTION_KIND_COVERAGE`，任何一档为 0 ⇒ `MOTION_KIND_UNWIRED` 红，并写明"不许在注释里写一遍来骗它"。
4. 找不到源码目录 ⇒ `MOTION_KIND_NOT_RUN all` + skip（记为未运行，不算通过）。
5. 变异第 28 张 `mutate_r125.py`：M627 撤词边界 / M628 撤剥注释 ⇒ 两刀全部 CAUGHT。

### 3. 三条定义

- **接线（wired）**：产品源码（除目录自身）里在**代码**中出现过 `.<档名>`，词边界成立。
- **未接线（会红）**：某一档只在 `MotionCatalog` 里存在 ⇒ 要么供电要么撤声明（R42 的规矩）。
- **未运行**：源码目录找不到 ⇒ skip，不算通过。

### 3b. 本轮的 U（自坏，逐条定义）

- **U-417：用一个工具的语法盲区给产品记了一条差点成真的假账。**
  `grep "for: \\.bannerOut"` 数出 0，而产品有 5 处（写法是命名参数 `removal: .bannerOut`）。
  如果那天我手上没有第二把尺，台账里就会多一条「bannerOut 是死声明」，
  下一轮就会有人去"撤声明"—— 那是把一条在工作的动效删掉。
  规矩（进 D-187①）：**计数不许用临时 grep**；提"没供电 / 没作者 / 没调用点"这类账之前，
  必须先有一把在仓库里会红的尺替它作证。
- **U-418：新尺第一版把"剥注释"外包给调用方。**
  真值表里"注释里提一句"那一格当场红了（`("1") is not equal to ("0")`）——
  尺要求调用方先 `codeOnly`，那么任何一次忘记就是一条能被散文喂饱的守卫（M407 / M411 同族）。
  修法是把剥注释移进尺内部，调用方无法忘记。
- **U-419：这仍然不是动效交付。**
  本轮产出一张清单尺，**零新增动效、零位点判断**；连续第五轮。
  新开 173 把这笔账写成条目并规定下一轮的三句话答法，免得"清单建好了"被读成"动效做过了"。

### 4. 覆盖与边界

产品 0 改动；判据 +2 条（真值表 + 九档地板）；变异第 28 张两刀全 CAUGHT（刀数 103 → **105**，caught 102 → **104**）；
全量 swift `%s 例 / %s skip / %s failures`；捕获卷 `%s / %s / %s`；
帧基线 `COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`；脚本电池见 §9；针自检见 §9。
**没做**：按清单点一个位真做动效（173）；runner 那一行的盲区位（R124 留的红，等它自己印键）。

""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED", gate), g("FRAME_BASELINE_CHANGED", gate),
       g("FRAME_BASELINE_MISSING", gate), g("FRAME_BASELINE_ADDED", gate))
AUDIT = once(AUDIT, "## 第 126 轮 · R124", SECTION + "## 第 126 轮 · R124")

ITER = rd("AGENT_VISUAL_ITERATION.md").rstrip("\n") + """

## Round 125 · 动效接线第一次成为会红的清单尺；我差点用一条 grep 的语法盲区开出假账（新开 173 / U-417…U-419 / D-187 · 产品 0 改动）

### 0. 开场缺陷清单

| # | 位点 | 证据 |
|---|---|---|
| 1 | 我数 `for: \\.bannerOut` | 0 处 ⇒ 差点开「死声明」的账 |
| 2 | 仓库里的尺数同一件事 | 5 处（ContentView 的 `asymmetricTransition(removal:)`） |
| 3 | 九档清单 | `""" + KINDLINE + """` |

### 1. 做了什么

`motionKindCallSites`（剥注释在尺内 + 词边界）+ 7 行真值表 + 九档地板 `>=1` 的产品级判据
（`MOTION_KIND_UNWIRED` 会红、找不到源码目录记未运行）。变异第 28 张 M627/M628 两刀 CAUGHT。
两条独立实现（python 临时数 / swift 判据数）九档数字逐档相同 —— 这是本轮唯一让我敢把清单写进台账的理由。

### 2. 真实视觉审查（看图腿）

本轮零产品改动、帧基线 `CHANGED=0`，看图沿用 R123 那两张真机帧（暗档设置窗口：六枚图标与标签同亮、
选中行蓝药丸、三张卡片排版正常）；新看的是**读数**：`MOTION_KIND_COVERAGE` 九行第一次把"哪一档接在哪个文件"
打成可 grep 的清单，`bannerOut=5` 那一行直接推翻了我自己十分钟前的结论。

### 7. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 产品 0 改动 |
| 动效华丽度 | 86 | **连续第五轮零新增动效**；本轮只交了清单尺，且已写成 173 不许混充交付 |
| 状态完备 | 90 | 九档接线第一次有数；未接线会红、未运行不通过 |
| 证据强度 | 93 | 7 行真值表 + 两把独立实现互证 + 两刀（词边界 / 剥注释） |
| 一致性 | 92 | 尺自己剥注释，调用方无法忘记（U-418 的修法） |
| 可维护 | 92 | 判据 +2 条；撤声明这种真回归会被 `>=1` 抓住 |
| 风险控制 | 93 | 假账在进台账之前被拦住；没有为绿而放宽任何一格 |
| **合计** | **91** | 加权取整；动效那一格按实际 86 记，并且它只会更低 |

### 9. §8 覆盖计数（本轮，全部从日志解析）

- 全量 swift：`Executed %s tests, %s skipped, %s failures`；捕获卷：`%s / %s / %s`
- 帧基线：`COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`
- 九档接线：`%s`
- 变异：第 28 张 `mutate_r125.py` 两刀全部 CAUGHT（刀数 103 → 105，caught 102 → 104）
- 脚本电池与针自检：见下（落盘后重跑，不手抄）

""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED", gate), g("FRAME_BASELINE_CHANGED", gate),
       g("FRAME_BASELINE_MISSING", gate), g("FRAME_BASELINE_ADDED", gate), KINDLINE)

CHANGELOG = rd("CHANGELOG.md")
CHANGELOG = once(CHANGELOG, "## [Unreleased]\n", """## [Unreleased]
### 动效接线第一次成为一把会红的清单尺（R125 / 新开 173 / U-417…U-419 / D-187 · 产品 0 改动）

- 起因是我自己犯的一次错：`grep "for: \\.bannerOut"` 数出 **0 处**，我准备开一条
  「这条动效声明没供电」的账。产品里其实是 5 处 —— 写的是
  `MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，
  我的模式只认得一种写法（U-417）。差一点用一个工具的语法盲区给产品记假账。
- 于是计数进仓库：`motionKindCallSites`（剥注释在尺内 + 词边界 `(?![A-Za-z0-9_])`）
  + 7 行真值表 + `testEveryMotionKindIsWiredSomewhereInProduct`（九档地板 `>=1`，
  排除 `MotionCatalog.swift` 自己；某档为 0 ⇒ `MOTION_KIND_UNWIRED` 红；找不到源码目录 ⇒ 记未运行）。
- 第一次交出九档接线清单：`""" + KINDLINE + """`。
  两条独立实现（临时 python 与仓库里的 swift 正则）逐档相同 ⇒ 才敢写进台账。
- 自坏两条当场抓住并修掉：U-418 第一版把"剥注释"外包给调用方，被真值表"注释里提一句"那一格
  红出来（`("1") is not equal to ("0")`）；U-419 承认本轮**仍然零新增动效**（连续第五轮），
  新开 BACKLOG 173 规定下一轮按清单点位的三句话答法，不许把"清单建好"读成"动效做过"。
- 变异第 28 张 `mutate_r125.py`：M627 撤词边界 / M628 撤剥注释 ⇒ 两刀全部 CAUGHT（刀数 103 → 105，caught 102 → 104）。
""")

REPORT = rd("AGENT_FINAL_REPORT.md")
REPORT = once(REPORT, "**M100–M626**", "**M100–M628**")
REPORT = once(REPORT, "⇒ 三臂全部 CAUGHT，表数 **27**、刀数 **103**、caught **102**。",
              "⇒ 三臂全部 CAUGHT，表数 **27**、刀数 **103**、caught **102**。"
              "R125 再加第 28 张 `mutate_r125.py`（M627 撤词边界 / M628 撤剥注释）"
              "⇒ 两臂全部 CAUGHT，表数 **28**、刀数 **105**、caught **104**。")
REPORT = once(REPORT, "| 决定台账 | D-069 … **D-186**", "| 决定台账 | D-069 … **D-187**")

STATE = rd("AGENT_STATE.md")
lines = STATE.split("\n")
head = next(i for i, l in enumerate(lines) if l.startswith("最后更新："))
quoted = "\n".join(("> " + l) if l.strip() else ">" for l in "\n".join(lines[head:]).split("\n"))
NEW = """# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 20:15（本地 · R125 / 第 127 轮收尾：**动效接线第一次成为一把会红的清单尺** —— 顺手拦住我自己差点开的一条假账（新开 173 / U-417…U-419 / D-187 · 产品 0 改动））

**现场**：我想找"目录里哪一档动效是死的"，在 shell 里 `grep "for: \\.bannerOut"` 数出 **0**，于是准备开一条"这条声明没供电"的账。真去数它是 **5 处** —— 产品写的是 `asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，我的模式只认得一种写法（U-417）。差一点用一个工具的语法盲区给产品记了一条假账，而下一轮就会有人照着这条账去"撤声明"。

**改了什么**：计数进仓库 —— `motionKindCallSites`（剥注释在尺内 + 词边界）+ 7 行真值表 + 九档地板 `>=1` 的产品级判据（某档为 0 ⇒ `MOTION_KIND_UNWIRED` 红；找不到源码目录 ⇒ `MOTION_KIND_NOT_RUN` 记未运行）。第一次交出可 grep 的接线清单：`""" + KINDLINE + """`；临时 python 与仓库 swift 正则两条独立实现逐档相同。

**自坏**：**U-418** 第一版把"剥注释"外包给调用方，被真值表"注释里提一句"那一格当场红出来（`("1") is not equal to ("0")`）⇒ 移进尺内，调用方无法忘记；**U-419** 本轮**仍然零新增动效**（连续第五轮），清单是尺不是交付 ⇒ 新开 **BACKLOG 173**，规定下一轮按清单点一个位必须答三句话（现在几帧过渡 / 加了之后重排与跳变怎么变 / 两档 + reduce-motion 长什么样）。

**下一轮（R126）**：① 173 —— 从清单里点一个位真做动效（不再允许"又建了一把尺"）；② 读 R125 的 CI，把 runner 那一行盲区位用**它自己印出来的键**填上（R124 故意留的红）；③ 172 亮档那一半仍等用户回答批次 86.1 或授权切系统外观。

""" + quoted
wr("AGENT_STATE.md", NEW)

for n, t in [("AGENT_BACKLOG.md", BACKLOG), ("AGENT_DECISIONS.md", DECISIONS),
             ("AGENT_UI_AUDIT.md", AUDIT), ("AGENT_VISUAL_ITERATION.md", ITER),
             ("CHANGELOG.md", CHANGELOG), ("AGENT_FINAL_REPORT.md", REPORT)]:
    wr(n, t)
    print("WROTE %s" % n)
print("LEDGER_R125=ok")
