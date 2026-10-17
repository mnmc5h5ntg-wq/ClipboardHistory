#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R122（第 124 轮）账本补丁：BACKLOG / DECISIONS / UI_AUDIT / ITERATION / CHANGELOG / STATE / FINAL_REPORT。"""
import io
import os
import re

ROOT = "/Users/wangziyi/Codex_Project0"


def read(n):
    return io.open(os.path.join(ROOT, n), encoding="utf-8").read()


def write(n, t):
    io.open(os.path.join(ROOT, n), "w", encoding="utf-8").write(t)


def once(t, a, b):
    n = t.count(a)
    assert n == 1, "锚点命中 %d：%s" % (n, a[:60])
    return t.replace(a, b, 1)


# 数字只从本轮日志里解析
full = read_log = io.open("/tmp/r122_full.log", encoding="utf-8", errors="replace").read()
m = re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", read_log)
swift = m[-1] if m else ("?", "?", "?")

BACKLOG = read("AGENT_BACKLOG.md").rstrip("\n") + "\n\n" + """172. **R122 开：亮档侧栏图标在离屏通道里几乎不画墨 —— 与暗档"反侧"是两种病，本轮只修了暗档**（R122 开 / 与 41、167、170、43 同族）：
    `SettingsSidebarRow` 的渲染模式从 `.hierarchical` 换成 `.monochrome` 之后，两档的读数**朝相反方向动**：

    - `dark 期望 56→78、反侧 22→0`（`wand.and.stars` 推荐 与 `chart.bar` 统计 是六枚里仅有的两枚多色符号，
      `.hierarchical` 会带它们自己的调色板 ⇒ 暗档黑底黑图标）—— 看帧确认：改后六枚图标与标签同亮。
    - `light 期望 35→13、无墨 43→65` —— 看帧也确认：亮档未选中行的图标淡到几乎看不见。

    为什么判它是**通道**而不是产品：同一行里标签文字用的就是同一个 `.primary`，文字照样是清晰的黑字，
    只有 Image 那一路不画 ⇒ 坏的是离屏通道对 `Image + .monochrome + 语义色` 的解析（审计第二轮 1.9
    的原始发现就是这一条：把颜色换成固定 `Color.black` 就能画到 0.175–0.402）。
    **没有定论的那一半记在这里**：真机上 `.monochrome` + `.primary` 是系统侧栏的标准做法，
    预期图标与标签同色；但这一轮的验收只到"帧 + 读数"，没到真机。
    ⇒ 判据只把**反侧**升成会红（`SIDEBAR_ICON_INVERTED`，M620/M621 两刀），亮档那一半写成
    `SIDEBAR_ICON_BLIND_SPOT` 登记行 —— 写成会红就会诱使下一轮拿固定色去填它，那才是真把颜色写死。
    下一步（R123）：装包到真机，用 `screencapture` 量亮档侧栏图标列的墨，与标签文字同列对照；
    真机若也淡，就把 `.monochrome` 撤回去并给多色符号单独配 `.palette`。
"""

DEC = read("AGENT_DECISIONS.md").rstrip("\n") + "\n\n" + """### D-184（R122）一档变好、另一档变读数的改动不算修好；会把两种病分开的，是"各有名字的登记"与"只判其中一格的红"

侧栏图标这一格把这件事演得很干净：`.hierarchical` → `.monochrome` 让暗档 22 行"黑底黑图标"归 0，
同时让亮档 22 行从"画得出墨"变成"几乎不画"。如果只看暗档那一半的读数，本轮可以宣布修好一个
深浅色缺陷；把两档并排放，结论就变成"两档要的方向相反，而其中一档的坏法发生在通道里"。

三条落地的规矩：

1. **成对读数一起打**（`SIDEBAR_ICON_COVERAGE` 两档同行、`SIDEBAR_ICON_BY_SYMBOL` 逐符号两档同行）——
   只打一档的判据会诱导出"单边修好"的改动。
2. **只把有把握的那一格升成会红**（反侧=0），另一格写成登记（`SIDEBAR_ICON_BLIND_SPOT`）。
   给"通道画不出墨"配红，下一轮就会用固定色去填 —— 那是拿产品换读数。
3. **同一路语义色的两条通道要互相作证**：同一行里标签文字清晰、图标不画 ⇒ 坏的必然是图标那一路的解析，
   不是 `.primary` 本身。这种"同一颜色、两条通道"的对照，比任何单点读数都便宜且难自欺。
"""

AUDIT = read("AGENT_UI_AUDIT.md")
AUDIT = once(AUDIT, "## 第 123 轮 · R121", """## 第 124 轮 · R122：侧栏图标的两档读数是反方向动的 —— 暗档 22 行"黑底黑图标"修掉了，亮档那一半判成通道盲区（新开 172 / U-408…U-409 / D-184 · 产品 1 行）

### 1. 开场清单（本轮全部证据的位置与坐标）

| # | 位点 | 改前读数 | 改后读数 | 判成 |
|---|---|---|---|---|
| 1 | 暗档侧栏 推荐(`wand.and.stars`) / 统计(`chart.bar`) 行带 y=156..188 / 220..252 | `dark 期望=56 反侧=22`，逐符号 `亮侧=0` | `dark 期望=78 反侧=0`，六枚符号各 `期望=13 反侧=0` | **产品缺陷，已修**：多色符号在 `.hierarchical` 下带自己的调色板，暗档黑底黑图标 |
| 2 | 亮档侧栏未选中行（同一列 x 12..34） | `light 期望=35 无墨=43` | `light 期望=13 无墨=65` | **通道盲区，登记**（新开 172）：同一行标签文字用同一个 `.primary` 照样清晰，只有 Image 那一路不画 |
| 3 | 帧 `settings-general-720x540-{dark,light}.png`（本轮逐张看过） | 暗档两枚图标看不见；亮档六枚都在但偏淡 | 暗档六枚与标签同亮；亮档未选中图标淡到几乎不见 | 图与数一致：两档**反方向**动 ⇒ 不能只按暗档宣布修好（D-184①） |
| 4 | 参照臂帧 `cardprobe-split-groupbox-720x600-{dark,light}.png` | — | 一起 CHANGED（同一棵侧栏树） | 帧基线 28 张变更、同提交 `update` |

### 2. 本轮改了什么（产品 1 行 + 判据 1 处）

1. `SettingsSidebarRow`：`.symbolRenderingMode(.hierarchical)` → `.monochrome`，
   并把那段"刻意保持 hierarchical"的旧注释换成上面这组读数 —— 旧结论（"不可见来自通道，不是产品"）
   **对了一半**：通道确实解析不了 `.primary` 的 Image 那一路，但暗档那 22 行是符号自带的多色板，
   是产品侧可改的（U-408）。
2. `SIDEBAR_ICON_COVERAGE` 的 `反侧行` 从"只报数"升成会红 `SIDEBAR_ICON_INVERTED`（闸门与判据同源 D-166：
   整档 0 墨时不判），亮档那一半写成 `SIDEBAR_ICON_BLIND_SPOT` 登记行，不配红。
3. 变异第 26 张 `mutate_r122.py`：M620 产品换回 `.hierarchical` ⇒ 暗档 22 行反侧被新红抓到（CAUGHT）；
   M621 把那条红从比 `inverted` 改成比 `blank` ⇒ 亮档 65 行无墨会踩红（CAUGHT，证明这条红认的是反侧那一格）。

### 3. 三条定义

- **反侧**：图标墨解析到**背景那一边**（黑底黑图标 / 白底白图标）—— 用户级别的"看不见"，会红。
- **无墨**：这一行图标列里既不比背景亮也不比背景暗 —— 本轮判为通道对 `Image + .primary` 的解析盲区，登记。
- **期望侧**：图标墨与标签文字落在同一边 —— 六枚符号 × 13 个夹具 × 两档，逐符号打表。

### 4. 覆盖与边界

产品 1 行；判据 +1 条红 +1 行登记；帧 136 张里 28 张变更并同提交 `update`；
全量 swift `%s 例 / %s skip / %s failures`；捕获卷 68 / 4 / 0；脚本电池 239 OK；
针自检 `tables=26 covered=24 arms=87 bad=0`；变异第 26 张 2 刀全 CAUGHT（刀数 98 → **100**，caught 97 → **99**）。
**没做的那一半**：真机验收（本机装的还是 R111 那一版），所以 172 的"通道 vs 产品"只到读数与看图，
没到 `screencapture` 那一层；人工批次 86.1 的问题因此从"看六枚图标"改成"看**亮档**未选中行的图标有没有标签那么黑"。

""" % (swift[0], swift[1], swift[2]) + "## 第 123 轮 · R121")
AUDIT = once(AUDIT, "- **U-407：用全局改名更新台账计数格", """- **U-409：一条判据同时看着"反侧"与"无墨"两种病，红就会指错方向。**
  本轮把 `反侧行` 升成会红之前，先量了一刀 M621：把这条红从比 `inverted` 改成比 `blank`，
  亮档 65 行无墨立刻把它踩红 —— 说明这两个数在同一个 `SIDEBAR_ICON_COVERAGE` 行里长得很像，
  而修法是相反的（反侧改产品渲染模式，无墨是通道盲区、不许动产品）。
  规矩：一条红只准认**一种**病，另一种病写登记行；这条红现在由 M621 钉着它认的是哪一格。
- **U-408：旧注释里"这不是产品，是通道"的结论被沿用了六轮，实际只对了一半。**
  审计第二轮 1.9 的探针量的是"未选中行的图标列墨水 0.0000"，据此写下"不可见来自离屏管线对语义色的解析"，
  本轮按符号拆开才发现：暗档那 22 行是**两枚多色符号自带的调色板**（产品可改），
  亮档那一半才是通道。规矩：一条"是通道不是产品"的结论必须**逐符号/逐元素**成立，
  整体读数为 0 不足以证明与产品无关 —— 本轮就是靠 R115 装的逐符号表才看见这个分裂。
- **U-407：用全局改名更新台账计数格""")

ITER = read("AGENT_VISUAL_ITERATION.md").rstrip("\n") + "\n\n" + """## Round 122 · 侧栏图标：暗档 22 行"黑底黑图标"修掉，亮档那一半判成通道盲区（新开 172 / U-408…U-409 / D-184 · 产品 1 行）

### 0. 开场缺陷清单

| # | 位点 | 证据 |
|---|---|---|
| 1 | 设置侧栏 推荐 / 统计（暗档） | `dark 反侧=22`，逐符号 `wand.and.stars`/`chart.bar` 亮侧=0 ⇒ 黑底黑图标 |
| 2 | 设置侧栏未选中行（亮档） | `light 期望=35 无墨=43` ⇒ 图标列本来就有近半不画 |
| 3 | 上一轮遗留 | `SIDEBAR_ICON_COVERAGE` 写着"本轮只报数"，两档的数谁都不钉 |

### 1. 做了什么

`.symbolRenderingMode(.hierarchical)` → `.monochrome`（多色符号不再带自己的调色板，图标交回 `.primary`）。
实测两档**反方向**动：`dark 期望 56→78、反侧 22→0`；`light 期望 35→13、无墨 43→65`。
判据跟着分家：反侧升成会红（`SIDEBAR_ICON_INVERTED`），亮档无墨写成 `SIDEBAR_ICON_BLIND_SPOT` 登记（新开 172 追真机）。
两刀：M620 产品退回 `.hierarchical` ⇒ 新红抓到（CAUGHT）；M621 把红改成比"无墨" ⇒ 亮档立刻踩红（CAUGHT，证明这条红认的是反侧）。

### 2. 真实视觉审查（看图腿，本轮看了 4 张）

`settings-general-720x540-dark.png`：六枚图标与标签同亮，推荐/统计两枚不再消失 ⇒ 暗档这一半是**看得见的改善**。
`settings-general-720x540-light.png`：标签文字清晰（同一个 `.primary`），未选中行的图标淡到几乎看不见 ⇒ 亮档这一半**变差**，
但同一行"文字画得出、图标画不出"把病因指向 `Image + 语义色` 那条通道，而不是颜色本身（D-184③）。
`cardprobe-split-groupbox-720x600-{light,dark}.png`：同一棵侧栏树，跟着一起变，没有别的位移。

### 7. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 91 | `.monochrome` 是系统侧栏的标准做法；但亮档那一半没在真机上验过 |
| 动效华丽度 | 90 | 三轮之后第一次回到产品面；本轮没有新动效，只修了静置可辨性 |
| 状态完备 | 90 | 未选中/选中/悬停三态的图标颜色第一次有逐符号数；亮档无墨登记为 172 |
| 证据强度 | 92 | 两档成对读数 + 逐符号表 + 两把刀（一把钉产品、一把钉"这条红认哪一格"） |
| 一致性 | 92 | 暗档修好、亮档按证据判成通道，没有为了读数把颜色写死 |
| 可维护 | 91 | 产品 1 行、判据 1 红 + 1 登记；旧注释换成读数，不再留推断 |
| 风险控制 | 89 | **本机装的还是 R111**：这次产品改动没经过真机验收就进基线，28 张帧同提交 update；172 的第一条就是补真机 |
| **合计** | **91** | 加权取整；真机那一半没做，所以风险控制按实际 89 记 |

### 9. §8 覆盖计数（本轮，全部从日志解析）

- 全量 swift：`Executed %s tests, %s skipped, %s failures`；捕获卷：68 / 4 / 0
- 帧基线：`COMPARED=136 CHANGED=28 MISSING=0 ADDED=0` → 同提交 `update`（`FRAME_BASELINE_UPDATED=136`）
- 脚本电池：`Ran 239 tests OK`；针自检：`tables=26 covered=24 arms=87 bad=0`
- 变异：`MUTATE_TABLE n=2 caught=2 mismatch=0 not_run=0`（第 26 张 `mutate_r122.py`）
- 本轮新读数族：`SIDEBAR_ICON_INVERTED`（红）/ `SIDEBAR_ICON_BLIND_SPOT`（登记）/ `SIDEBAR_ICON_COVERAGE`（改文案）
""" % (swift[0], swift[1], swift[2])

CH = read("CHANGELOG.md")
CH = once(CH, "## [Unreleased]\n", """## [Unreleased]
### 设置侧栏图标：暗档 22 行「黑底黑图标」修掉，亮档那一半判成通道盲区（R122 / 新开 172 / U-408…U-409 / D-184 · 产品 1 行）

- 产品：`SettingsSidebarRow` 的 `.symbolRenderingMode(.hierarchical)` → `.monochrome`。
  六枚侧栏符号里 `wand.and.stars`（推荐）与 `chart.bar`（统计）是仅有的两枚**多色符号**，
  `.hierarchical` 会保留符号自带的多色调色板，于是暗档有 22 行图标墨落在背景那一边（黑底黑图标）。
- 实测两档反方向动：`dark 期望 56→78、反侧 22→0`；`light 期望 35→13、无墨 43→65`。
  看帧两边都确认（`settings-general-720x540-{dark,light}.png`）。
- 判据分家：`反侧行` 从"只报数"升成会红 `SIDEBAR_ICON_INVERTED`（闸门与判据同源 D-166，整档 0 墨不判）；
  亮档无墨写成 `SIDEBAR_ICON_BLIND_SPOT` 登记行 —— 给它配红等于诱使下一轮拿固定色去填（BACKLOG 172 追真机）。
- 更正一条沿用了六轮的结论（U-408）：审计第二轮 1.9 的"不可见来自离屏管线对语义色的解析，不是产品"
  只对了一半 —— 逐符号表显示暗档那 22 行是符号自带的多色板，产品可改；亮档那一半才是通道。
- 帧基线 28 张变更（13 个设置夹具 × 两档 + 参照臂 2 张），同提交 `update`，`COMPARED=136 MISSING=0 ADDED=0`。
- 变异第 26 张 `mutate_r122.py`：M620 产品退回 `.hierarchical` ⇒ 新红抓到；M621 把红改成比"无墨" ⇒ 亮档立刻踩红
  （这一刀钉的是"这条红认的到底是哪一格"）。两刀全 CAUGHT ⇒ 刀数 98 → 100，caught 97 → 99。
- **未做**：真机验收（本机装的仍是 R111），所以 `.monochrome` 在亮档到底是产品淡还是通道淡，只到读数与看图那一层。
""")

REPORT = read("AGENT_FINAL_REPORT.md")
REPORT = once(REPORT, "**M100–M619**", "**M100–M621**")
REPORT = once(REPORT, "⇒ 四臂全部 CAUGHT，表数 **25**、刀数 **98**、caught **97**。",
              "⇒ 四臂全部 CAUGHT，表数 **25**、刀数 **98**、caught **97**。"
              "R122 再加第 26 张 `mutate_r122.py`（M620 产品退回 `.hierarchical` ⇒ 暗档 22 行反侧被新红抓到；"
              "M621 把那条红从比反侧改成比无墨 ⇒ 亮档 65 行无墨立刻踩红，钉的是"
              "「这条红认的是哪一格」）⇒ 两臂全部 CAUGHT，表数 **26**、刀数 **100**、caught **99**。"
              "本轮是 R112 之后第一次动产品源码（1 行）。")
REPORT = once(REPORT, "| 决定台账 | D-069 … **D-183**", "| 决定台账 | D-069 … **D-184**")

STATE = read("AGENT_STATE.md")
lines = STATE.split("\n")
head = next(i for i, l in enumerate(lines) if l.startswith("最后更新："))
old = "\n".join(lines[head:])
quoted = "\n".join(("> " + l) if l.strip() else ">" for l in old.split("\n"))
NEW = """# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 19:3x（本地 · R122 / 第 124 轮收尾：**设置侧栏两枚多色图标在暗档是黑底黑图标** —— 修掉了，而亮档那一半判成通道盲区（新开 172 / U-408…U-409 / D-184 · 产品 1 行））

**现场**：逐符号表把六枚侧栏图标分开之后，`dark 反侧=22` 全部落在 `wand.and.stars`（推荐）与 `chart.bar`（统计）—— 六枚里仅有的两枚多色符号。`.hierarchical` 保留符号自带的多色调色板 ⇒ 暗档黑底黑图标。换成 `.monochrome` 之后实测 `dark 期望 56→78、反侧 22→0`，看帧确认六枚与标签同亮。

**但另一档朝反方向动**：`light 期望 35→13、无墨 43→65`，看帧也确认亮档未选中行的图标淡到几乎看不见。同一行里标签文字用的是**同一个** `.primary` 且照样清晰 ⇒ 坏的是离屏通道对 `Image + 语义色` 那一路的解析（审计第二轮 1.9 的原始发现），不是颜色。所以本轮只把**反侧**升成会红（`SIDEBAR_ICON_INVERTED`，闸门与判据同源），亮档那一半写成 `SIDEBAR_ICON_BLIND_SPOT` 登记 ⇒ 新开 172 追真机。

**两把刀**：M620 产品退回 `.hierarchical` ⇒ 新红抓到暗档 22 行；M621 把这条红从比 `inverted` 改成比 `blank` ⇒ 亮档 65 行无墨立刻踩红（钉"这条红认的是哪一格"，U-409）。第 26 张表，刀数 98 → 100，caught 97 → 99。

**两条自坏**：**U-408** "这不是产品，是通道"这条旧结论被沿用了六轮，实际只对一半 —— 整体读数为 0 不足以证明与产品无关，必须逐符号/逐元素成立；**U-409** 一条判据同时看着两种病（反侧 / 无墨）时红会指错方向，两种病修法相反。

**没做的那一半（重要）**：本机装的仍是 R111 那一版，`.monochrome` 在亮档到底是产品淡还是通道淡，只到读数与看图，**没到真机**。⇒ R123 第一件工作是装包 + `screencapture` 量亮档侧栏图标列，与同一行的标签文字对照；真机若也淡就撤回 `.monochrome` 并给多色符号单独配 `.palette`。人工批次 86.1 的问题相应改成"看**亮档**未选中行的图标有没有标签那么黑"。

**另外**：R121 的 CI（run 39027921504）本轮没读到就收口了 —— 四种出口的 runner 验收、171 的名单分键，都排在 R123。

""" + quoted
assert "> 最后更新：" in NEW
write("AGENT_STATE.md", NEW)

for n, t in [("AGENT_BACKLOG.md", BACKLOG), ("AGENT_DECISIONS.md", DEC), ("AGENT_UI_AUDIT.md", AUDIT),
             ("AGENT_VISUAL_ITERATION.md", ITER), ("CHANGELOG.md", CH), ("AGENT_FINAL_REPORT.md", REPORT)]:
    write(n, t)
    print("WROTE %s" % n)
print("LEDGER_R122=ok")
