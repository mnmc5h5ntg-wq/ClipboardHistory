#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R54 台账（第 56 轮 / D-113 / U-80 / BACKLOG 71 结案 / CHANGELOG / Round 54 / 报告对账）。

数字来源：
  16 条 `HEAT_ADJACENT` 读数              <- 本机 `swift test --filter HeatmapHoverEvidenceTests` 的打印
  最小读数 30.00（dark empty→bucket1）    <- 同一批；地板 18 沿用 R45 那把
  M264–M268 五支全 CAUGHT                 <- /tmp/r54_mutations.log
  753 tests / 29 skip / 0 failures        <- /tmp/r54-full.log
  CI 已读：run 38547820163                <- `judged=4/4 / REDS=0 / success`
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 56 轮 · R54：相邻档第一次有判据，而它给出的结论是"梯子没错，我的轴错了"（BACKLOG 71 结案 / U-80 / D-113）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `HeatmapHoverEvidenceTests` | 三条判据：悬停那一圈响不响、悬停只改一圈、悬停不许比数据响 | **从来没有一条量"相邻两档分不分得开"**。而这张图上深浅是唯一的信息通道 —— 相邻档分不开等于那张日历少一档（BACKLOG 71 从 R47 挂到现在） |
| R51/R53 留在台账里的结论 | "暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开" | 那是 **Rec.709 亮度轴**。`VisualHeat.empty` 走 `primary`（灰）、四档走 `accent`（蓝），那一步差的是**色相** |
| `flatRep`（本轮新写的尺子夹具） | 第一版用 `NSBitmapImageRep.setColor(_:atX:y:)` 逐像素上色 | 两幅"不同色"的图量出来差是 **0.00** —— 那条 API 在整数格式位图上不落地，而且**不报错**。是尺子自己的真值表把它抓出来的 |

### 修法与读数

新增 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis`：五档两两相邻（4 对）× 亮暗两种外观
× 1×/2× 两种尺度 = **16 条读数**，量的是**格子内部**（`fillBand`，与描边带严格互补），
距离取**逐像素三通道最大差**再对带内取均值（`meanMaxChannelDelta`）。
三条轴一起打进日志，让"用哪根轴"可审计：

| 相邻档（本机实测） | 最大通道差 | 均值通道差 | 亮度差 |
|---|---|---|---|
| dark `empty→bucket1` | **30.00** | 17.33 | **2.16** |
| dark `bucket1→bucket2` | 36.00 | 18.33 | 10.83 |
| dark `bucket2→bucket3` | 49.00 | 25.33 | 15.23 |
| dark `bucket3→bucket4` | 65.00 | 33.67 | 20.57 |
| light `empty→bucket1` | 34.00 | 19.33 | 15.84 |
| light `bucket1→bucket2` | 41.00 | 21.00 | 25.17 |
| light `bucket2→bucket3` | 56.00 | 28.33 | 33.77 |
| light `bucket3→bucket4` | 74.00 | 37.33 | 44.43 |

⇒ **16 条全部过地板 18，最小的一条是 30.00（1.7 倍余量）**。
⇒ BACKLOG 71 的答案是：**梯子的数值不用改，一帧像素都没变**；要改的是我那把尺的轴。
亮度轴上 `dark empty→bucket1` 只有 **2.16** —— 如果当初按它判，我会去抬 `empty` 或抬第 1 级，
把一张本来没病的图改响（而且违反"不喧宾夺主"）。**这就是"用错轴"的代价，本轮它有数了。**

顺带一条与 R45 相反的实测：**填充那一半对尺度完全不敏感**（1× 与 2× 读数逐条相同），
R45 那条"1× 比 2× 系统性低 20%–25%"只成立于**1pt 描边**，不成立于整格填充。
以后引用那句话要带范围。

### 真实视觉审查

本轮零产品改动 ⇒ 116 张帧逐字节不变（`CHANGED=0 MISSING=0 ADDED=0`，见验证），
所以"看图"看的是**同一批帧换一根轴重读**：
`heatmap-cell-strip-still-90x140-dark.png`（180×280 px，格子在 x=32–53 / x=88–109）
最下面那两行的"灰格 vs 浅蓝格"，眼睛看到的是**颜色不同**而不是深浅不同 ——
这与新读数（ΔB=30、Δ亮度=2.16）一致，也正是 R51 那两次归位/轴错误唯一能由人眼纠偏的地方。
人工批次 53.1 / 54.1 仍在等这一句回答；判据已经先站在"不改像素"这一边。

### 验证

- 尺子自己的真值表 8 格（`testAdjacentLevelRulersAreATruthTable`）：填充带非空、够大、
  与描边带严格互补、两者加起来几乎铺满整格、每个点都在格子框内且离边界超过一条描边、
  **只有 B 通道差 30 的一对必须读出"最大通道 30 / 均值通道 10"**、自比=0、空带=−1、
  1× 与退化几何。
- 变异 **M264–M268 五支全 CAUGHT**（`红得不对=0 还原不干净=0`，电池还原后自己复跑=全绿）：
  其中 **M265（把最大通道差换成均值通道差）会红** —— 这一支是本轮的核心：
  它证明"轴"不是口味，选错轴等于把判据删掉。
  M264 改的是**产品令牌**（梯子第 1 级 0.18→0.06），红了 ⇒ "两档并成一档"确实有人看着。
- `swift build --build-tests` 编译 0 告警；全量 **753 tests / 29 skipped / 0 failures**；
  离屏闸门 `红=0`；116 帧 `CHANGED=0 MISSING=0 ADDED=0` ⇒ **不需要 `frame_baseline update`**（没改像素）；
  脚本 105 全绿。**不换装**（产品零改动）。
- **CI 已读**：R52 那一次 run 38547820163 `success`，
  `MOTION_FLOOR_FACTS judged=4/4 … MOTION_FLOOR_REDS=0`。
  同一条 runner 上横幅两臂这六次是 `4/4 / 2/4 / 无读数 / 3/4 / 4/4 / 4/4` ⇒ BACKLOG 77 的"漂移"有账了。
- 自评 **94 / 100**。

'''

DECISION = '''
---

## D-113（R54）：判"两态分不分得开"之前，先证明差在哪一根轴上

**背景**：BACKLOG 71 从 R47 挂着，R51 我"量出"暗档 0 次与 1 次只差 4/255，
结论是"这张图把没数据和有一点数据抹成同一个意思"。按这个结论走，下一步就是抬 `empty` 或抬梯子第 1 级 ——
一次会改像素、还会让 126 个空格子一起变响（撞"不喧宾夺主"）的产品改动。

**决定**：
1. **轴先于数**。`empty` 是 `primary`（灰），四档是 `accent`（蓝），那一步差的是**色相**：
   亮度轴 2.16，B 通道 30。判据建在**逐像素最大通道差**上，并把三根轴一起打进日志。
2. **新尺子必须自带真值表**，而且真值表要能抓到**尺子的夹具坏了**：
   `flatRep` 第一版用 `setColor(_:atX:y:)` 上色，两幅图读出来差 0.00（那条 API 在整数位图上不落地且不报错）。
   没有第 ③ 格（"只有 B 差 30 的一对必须读出 30 与 10"），这条判据会全绿地量着一片空气。
3. **结论是"不改产品"也要有牙**：M264 改产品令牌（梯子第 1 级压到 0.06）必须红、
   M265 把轴换回均值必须红。否则"不用改"与"调松了宣布通过"在日志里长得一样。
4. **不发明新地板**：沿用 R45 从 20 条真读数推导的 `perceptibleBand255 = 18`，
   实测最小值 30.00 有 1.7 倍余量 —— 这条判据现在既不是恒真也没贴着数跑。

**代价**：多两个带选择器与一个距离函数；日志多 16 行；
以及台账里要留一条相反方向的更正（R51 那句"分不开"作废）。
'''

BACKLOG_71_CLOSE = '''
    **【R54 已结案，U-80 / D-113】答案是"梯子没错，尺的轴错了"**：
    判据 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis` 已立（4 对 × 2 外观 × 2 尺度 = 16 条读数），
    距离取**逐像素最大通道差**，地板沿用 `perceptibleBand255 = 18`。
    实测最小一条是 `dark empty→bucket1 = 30.00`（同一对在亮度轴上只有 2.16）⇒ **16 条全过，
    产品数值一个没改，帧基线不需要 update**。
    上面那条"抬 `empty` 还是抬第 1 级"的选择题因此不成立：那是按亮度轴做的决定，
    真按它改会把一张没病的图改响。变异 M264（把梯子第 1 级压到 0.06）与 M265（把轴换回均值）都会红。
'''

BATCH = '''

---

## 批次 55 · R54：零产品改动；上一轮那道"只有你能判"的题，我的尺已经站到"不用改"这一边了（BACKLOG 71 结案）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮新增的是热图**相邻档**的判据（换了度量轴）。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 55.1 | 设置 → 统计：图例里最左那两格（"最少"与它右边那一格） | 你看到的是**深浅不同**，还是**一个发灰、一个发蓝**？ | 我的新读数说这一步在 B 通道上差 30、在亮度上只差 2.16 ⇒ 它是**色相**步。如果你说"深浅不同"，那说明色相那条通道在你的屏幕上没起作用，我就得回头改数值 |
| 55.2 | 同一次操作里，看日历里**有 1 次复制**的那些格子 | 与"0 次"的格子比，需不需要眯眼才能分？ | 我的尺在 11pt 的方格上量出 30/255，但屏幕尺寸、距离、你的显示器我都不知道 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51、52、53、54 共 28 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**52.1（快速选择浮层里移动到底动没动）**。
'''

CHANGELOG = '''### Added（R54：热图相邻档第一次有判据 —— 结论是"梯子没错，我的轴错了"）
- 新增 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis`：五档两两相邻（4 对）× 亮暗 × 1×/2×
  = 16 条读数，量**格子内部**，距离取**逐像素三通道最大差**（`meanMaxChannelDelta`），
  地板沿用 R45 的 `perceptibleBand255 = 18`。实测最小一条 `dark empty→bucket1 = 30.00` ⇒ **全部通过，
  产品数值一个没改**（BACKLOG 71 结案）。
- 撤回 R51 写进台账的"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"：那是**亮度**轴；
  `empty` 是灰（`primary`）、四档是蓝（`accent`），同一对在 B 通道上差 30、亮度上只差 2.16。
  按旧结论去抬 `empty` 会把一张没病的图改响（撞"不喧宾夺主"）。
- 新增 `fillBand`（与 `ringBand` 严格互补的格子内部）与其真值表 8 格；
  其中一格把**坏掉的尺子夹具**抓了出来：`NSBitmapImageRep.setColor(_:atX:y:)` 在整数格式位图上
  不落地且不报错，两幅"不同色"的图读出来差 0.00 ⇒ 改成直接写 `bitmapData`。
- 实测补一条与 R45 相反的边界：**整格填充对尺度不敏感**（1× 与 2× 逐条相同），
  R45 那句"1× 比 2× 低 20%–25%"只成立于 1pt 描边。
- 变异 M264–M268 五支全 CAUGHT（M264 改产品令牌、M265 把轴换回均值 ⇒ 都会红）。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

'''

VISUAL = """
---

## Round 54 · 相邻档第一次有判据，而它判的是我自己（R54 / BACKLOG 71 结案 / U-80 / D-113）

**这一轮问的问题**：BACKLOG 71 从 R47 挂到现在，中间我已经"量出"过答案 ——
暗档 0 次与 1 次只差 4/255。按那个数，下一步就是抬 `empty` 或抬梯子第 1 级，
也就是**改产品像素**。开工前该问的是：**那 4 是从哪根轴上读出来的？**

**答：Rec.709 亮度。而那张图的那一步差的是色相。**
`VisualHeat.empty` 走 `primary`（灰），四档数据走 `accent`（蓝）——
同一对像素在 B 通道上差 30，在亮度上只差 2.16。
换成"逐像素最大通道差"之后，16 条读数（4 对 × 2 外观 × 2 尺度）**全部过地板 18，
最小的一条是 30.00**。⇒ 梯子一个数没改，帧基线不用 update，
而 R51 那句"分不开"进了台账的更正列表。

**如果当初按亮度轴改了什么会怎样**：抬 `empty` 会让 126 个空格子一起变响（明确违反"不喧宾夺主"），
抬第 1 级会把 `bucket1→bucket2` 压回去 —— 两条都是把一张没病的图改坏。
**用错轴的代价不是"数不准"，是"去做一件不该做的事"。**

**尺子的夹具也坏过一次，被真值表抓住**：`flatRep` 第一版用 `setColor(_:atX:y:)` 逐像素上色，
两幅"不同色"的图量出来差 **0.00**（那条 API 在整数格式位图上不落地、也不报错）。
没有那一格"只有 B 差 30 的一对必须读出 30 与 10"，这条判据会全绿地量着一片空气。

**真实视觉审查**：零产品改动、116 帧逐字节不变。看的是**同一批帧换一根轴重读**
（`heatmap-cell-strip-still-90x140-dark.png`，格子在 x=32–53 / x=88–109）：
最下两行的"灰格 vs 浅蓝格"，眼睛看到的是颜色不同而不是深浅不同 —— 与新读数一致。
这一眼仍然挂在人工批次 53.1 / 54.1 / 55.1，因为**显示器与观看距离不在我的量程里**。

**分数为什么持平，以及一件该说的事**：`流畅度` 13/20、`动效细节` 14/15 的失分点从 R42 起没动过。
R45–R54 **连续十轮 94** 不是稳定，是**同一件事没做完**：每轮都被尺子的问题截走。
R55 起回到动效本体（BACKLOG 77 那三条候选路里选一条真的做出来）。

### 自评 94 / 100（与 R45–R53 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；连续十轮的失分点，R55 回到动效本体 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变；相邻档第一次有自己的轴与地板 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：16 条读数全过、真值表 8 格、M264–M268 五支全 CAUGHT、
753 例 / 29 skip / 0 failures、编译 0 告警、116 帧不变、脚本 105 全绿。
"""

STATE = """

---

## R54 · 相邻档第一次有判据，而它判的是我用的轴（第 56 轮 / BACKLOG 71 结案 / U-80 / D-113）

- **靶**：BACKLOG 71（R47 挂到现在）。R51 我"量出"暗档 0 次 vs 1 次只差 4/255，
  下一步本应是抬 `empty` 或抬梯子第 1 级 —— 一次会改像素、还会让 126 个空格子一起变响的产品改动。
- **答案：梯子没错，我的轴错了。** `empty` 走 `primary`（灰）、四档走 `accent`（蓝），
  那一步差的是**色相**：亮度轴 2.16，B 通道 30。
  新判据取**逐像素最大通道差**，16 条读数（4 对 × 2 外观 × 1×/2×）**全部过地板 18，最小 30.00**
  ⇒ **产品数值一个没改，帧基线不需要 update**。
- **用错轴的代价不是"数不准"，是"去做一件不该做的事"**：按亮度轴改，我会把一张没病的图改响。
- **尺子的夹具坏过一次，被真值表抓住**：`flatRep` 第一版用 `setColor(_:atX:y:)` 上色，
  两幅"不同色"的图读出 **0.00**（整数格式位图上那条 API 不落地也不报错）⇒ 改成直接写 `bitmapData`。
  没有"只有 B 差 30 必须读出 30 与 10"那一格，这条判据会全绿地量着一片空气。
- **一条与 R45 相反的实测**：整格填充**对尺度不敏感**（1× 与 2× 逐条相同）；
  R45 那句"1× 比 2× 低 20%–25%"只成立于 1pt 描边。以后引用要带范围。
- **验证**：真值表 8 格、变异 **M264–M268 五支全 CAUGHT**
  （M264 改产品令牌 0.18→0.06 会红；M265 把轴换回均值会红 ⇒ "不用改产品"这个结论有牙）；
  全量 **753 tests / 29 skipped / 0 failures**、编译 0 告警、离屏闸门 `红=0`、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本 105 全绿。**不换装**。自评 **94 / 100**。
- **CI 已读**：R52 的 run 38547820163 `success`，`MOTION_FLOOR_FACTS judged=4/4 … REDS=0`；
  同一条 runner 上横幅两臂六次是 `4/4 / 2/4 / 无读数 / 3/4 / 4/4 / 4/4` ⇒ BACKLOG 77 的"漂移"有账。
  R53 那一次 run 38549020323 待读（要看 `MOTION_NATIVE_MOVE 判定=` 是否终于出现）。
- **一条自我记账**：R45–R54 **连续十轮 94** 不是稳定，是同一件事没做完 ——
  `流畅度` 13/20 与 `动效细节` 14/15 的失分点从 R42 起没动过，每轮都被尺子的问题截走。
  **R55 回到动效本体**：BACKLOG 77 三条候选路里选一条真的做出来（首选"把抓帧每帧成本降下来"，
  因为它同时解 74/75/77 三条）。
- **下一步（R55）**：① BACKLOG 77 落地一条（降 `Grabber` 每帧成本：按 1× 拍还是降采样，先 spike）；
  ② 读 R53/R54 的 CI；③ BACKLOG 72 的迁移（本机 3 卷 + runner 卷都答"从没出现"）。
"""


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve(expected_count, new_last_round):
    out = subprocess.run(["python3", ".scratch/motion-audit-2/curve_from_ledger.py"],
                         capture_output=True, text=True).stdout
    raw = [l for l in out.splitlines() if l.startswith("PHASE2 CURVE:")][0]
    values = raw.split("PHASE2 CURVE: ", 1)[1].split(" · ")
    head = [l for l in out.splitlines() if l.startswith("PHASE2 n=")][0]
    mean = head.split("mean=")[1].split()[0]
    assert "n=%d" % expected_count in head, head
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    found = re.findall(r"自评曲线（(\d+) 轮，Round 9–(\d+)，均值 \*\*([\d.]+)\*\*，最低 (\d+)）：\n(.+?)。\n",
                       report)
    assert len(found) == 1, ("报告里的曲线行没找到或不唯一", len(found))
    n_rounds, last_round, old_mean, low, old_line = found[0]
    old_values = [v.strip("*") for v in old_line.split(" · ")]
    assert int(n_rounds) + 1 == len(values), (n_rounds, len(values))
    assert old_values == values[:-1], ("旧行不是解析器结果的前缀", old_values[-3:], values[-4:])
    assert int(last_round) + 1 == new_last_round, (last_round, new_last_round)
    old_clause = "自评曲线（%s 轮，Round 9–%s，均值 **%s**，最低 %s）：\n%s。\n" % (
        n_rounds, last_round, old_mean, low, old_line)
    new_clause = "自评曲线（%d 轮，Round 9–%d，均值 **%s**，最低 %s）：\n%s。\n" % (
        len(values), new_last_round, mean, low, bolded(values))
    return head, old_clause, new_clause


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


def append_once(path, marker, text):
    current = io.open(path, encoding="utf-8").read()
    if marker in current:
        print("跳过（已写过）：%s  ← %s" % (path, marker))
        return
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(text)


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_71_tail = ("    R52 该做的：把这条变成 `renderCell` 上的判据（相邻档 Δ ≥ 从实测推导的地板），")
    anchor_77_tail = ("    判\"该走哪条\"的证据：本机与 runner 各一卷 `MOTION notice-banner*` 的 `时刻ms=[…]` 全列。")
    assert backlog.count(anchor_71_tail) == 1, ("BACKLOG 71 锚点", backlog.count(anchor_71_tail))
    assert backlog.count(anchor_77_tail) == 1, ("BACKLOG 77 锚点", backlog.count(anchor_77_tail))

    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **46 轮**审计（R9–R53） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–53 |",
         "| 阶段二 **47 轮**审计（R9–R54） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–54 |"),
        ("| 决定台账 | D-069 … D-112 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-113 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **751** 例（29 skip / 0 failures",
         "| 判据 | 653 → **753** 例（29 skip / 0 failures"),
        ("+ **M100–M263**（阶段二 164 支）", "+ **M100–M268**（阶段二 169 支）"),
        ("| 视觉台账 | U-31 … U-79（49 条；", "| 视觉台账 | U-31 … U-80（50 条；"),
        ("U-79 是**修含糊的动作自己造了新的含糊**",
         "U-80 是**用错轴险险地去改一张没病的图**：热图 `empty` 是灰（`primary`）、四档是蓝（`accent`），"
         "相邻档那一步在亮度轴上只有 2.16、在 B 通道上有 30 ⇒ 按亮度判会得到\"0 次与 1 次分不开\"，"
         "并据此去抬 `empty`（那会让 126 个空格子一起变响）。判据换到最大通道差之后 16 条全过，"
         "**产品一个数没改**（R54 结案 BACKLOG 71）；\\n"
         "U-79 是**修含糊的动作自己造了新的含糊**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–55 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–56 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Fixed（R53"
    if "### Added（R54" not in changelog:
        assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    if "U-80 是" not in report:
        for old, _ in pairs:
            assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    append_once("AGENT_UI_AUDIT.md", "## 第 56 轮 · R54", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-113（R54）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 54 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R54 · 相邻档第一次有判据", STATE.lstrip("\n"))
    append_once("docs/MANUAL_TEST_v1.4.9_round3.md", "## 批次 55 · R54", BATCH)
    if "【R54 已结案，U-80 / D-113】" not in backlog:
        patch("AGENT_BACKLOG.md", [
            (anchor_71_tail, anchor_71_tail.replace("R52 该做的：", "R52 当时该做的（R54 已做，见下面那条结案）：")),
        ])
        # 结案段挂在 71 的最后（也就是那段"一个先验约束"之后），并把 77 的证据补一行。
        tail_71 = ("    这两条互相牵着，R52 要把它们一起判，不许只调一个数就宣布修好。")
        patch("AGENT_BACKLOG.md", [
            (tail_71, tail_71 + "\n" + BACKLOG_71_CLOSE.strip("\n")),
            (anchor_77_tail, anchor_77_tail + "\n    **R54 补的账**：同一条 runner 六次运行"
             " `4/4（R48）/ 2/4（R49）/ 无读数（R51a）/ 3/4（R51b）/ 4/4（R51 更正）/ 4/4（R52）`"
             " ⇒ 这是**漂移**而不是坏了；登记放宽与 `MOTION_FLOOR_THIN` 都据此站得住。"),
        ])
    if "### Added（R54" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Fixed（R53")])
    head, curve_old, curve_new = check_curve(47, 54)
    if "U-80 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R54 台账已写入；曲线核对：", head)


main()
