#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R44 的台账写入。锚点全部 assert：写不进去就报错，不静默。"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 46 轮 · R44：那条会找驱动的尺，先学会读"派生键"（U-70 / D-103）

### 开场缺陷清单（坐标）

本轮没有产品改动，改的是**尺**。R42 立的那条"调用点级"守卫要推广到第二个组件
（BACKLOG 64），而第一步就把这条推广**挡住了**：

| 位点 | 形状 | 直接推广会怎样 |
|---|---|---|
| `ContentView:32` | `.animation(bannerIn, value: noticeSignature)` | 键里出现的名字是 `noticeSignature` |
| `ContentView:36-44` | `noticeSignature` 把**五条**回执的存在性压成一个 bitmask | 五个门控状态名一个都不在键里 |
| `ContentView:49-78` | 五条 `if let x = historyStore.…Notice { NoticeBanner(…).transition(…) }` | ⇒ **五条全部误报成"没电"** |

而它们**确实有电**（R22 用像素量过插入位移，`notice-banner` 那张帧判过带间缝）。
⇒ 这不是漏网的缺陷，是**尺读不懂一种合法的写法**。带着假阳性推广，
第一轮的收获会是"五条新缺陷"，而那五条全是编的 —— 这正是 R34 的 U-56 那一族。

### 修法：给判据加一跳"展开派生键"，且规定它**只增不减**

`MotionDriverTests` 新增 `drivingStates(for:in:)`：键里出现的**裸名字**如果在同一个文件里有
computed property 定义，就把那个 body 里点到的标识符并进状态集合（点路径与它的最后一段都算，
所以键里写 `historyStore.transferNotice`、门控里写 `transferNotice` 也能对上）。
只展开一跳。

**关键的一条设计**：展开**只增不减**，读不懂就退回按名字匹配 ——
找不到定义 ⇒ 不放行、也不报错，只是那一跳不发生。
理由：一个"因为读不懂而放行"的守卫是免检牌（R39b 那一族的反面），
而一个"读不懂就红"的守卫会在每一次合法写法出现时逼人把它删掉。
两种坏法都躲开，代价是**假阴性仍可能发生**（派生键读到了名字但其实那个名字不推像素）——
这一条由 M207 那支变异钉住。

### 判据（3 条新，CI 每轮跑）

- `testNoticeBannerCallSitesArePoweredByTheirDerivedKey`：五个调用点 × 名单两边都会红 × 展开后必须全推到。
  读数：`BANNER_DRIVE 调用点 5 个、键 1 条、展开后状态 13 个、无驱动 0 个`。
- `testDerivedKeyExpansionIsATruthTable`：5 格。三格是本轮新学的：
  ① 展开后**认最后一段**（否则五条全红）；
  ② 签名**没点到**的那条状态仍算没电（展开不是万能通行证 —— 这一格就是 M207 的靶）；
  ③ 键指向本文件里不存在的属性 ⇒ 按名字匹配、**不放行**（"读不懂不许变绿"）。
- 扫描器本体（`identifiers` / `computedPropertyBody` / `drivingStates`）都是纯函数，能直接喂字符串测。

### 真实视觉审查（本轮：没有新画面，而且**不该有**）

零产品改动 ⇒ 能数的还是"没动到稳态"：`receipt-line` 等 112 张帧逐字节不变
（本轮不重拍基线，`git status` 里只有 `MotionDriverTests.swift` 一个非台账文件）。
⇒ 换装本机**跳过**，理由写在账上而不是默默省略：这一轮没有任何"只有装上新包才看得见"的东西。

### 本轮查出、**没**在本轮修的

- **BACKLOG 64 只剩后半**：热图那两处（`DailyCopyHeatmapView:44/50/78`）不是"组件调用点 + `if let` 门控"
  这个形状，而是 `if 布尔 { 一块视图 } else { 另一块 }` 的**分支**。
  本轮的扫描器认调用点，不认分支 ⇒ 要推广到它，得先给判据加"分支门控"这一族（另一条真值表）。
  已把这条写回 BACKLOG 64，别让它看起来像"已经全推广完了"。

### 验证

735 tests / 29 skipped / **0 failures**（+2 条判据）；`swift build` 0 告警；
闸门 `有名字的红=0 NOT_RUN=0 ⇒ ok`；帧基线 112 张 `CHANGED=0`（本轮不改基线）；脚本 83 全绿；
变异 **M206–M209** 四支全 CAUGHT、`未被抓到=0 红得不对=0 还原不干净=0`
（needle 全部从 `--measure` 的失败消息原文抄，且都落在**排过序的数组**上 ⇒ 顺序稳定）。
**CI 待读**。
'''

DECISION = '''

---

### D-103 · R44：判据读不懂一种合法写法时，**不许**把它判成缺陷，也不许把它放行

- **背景**：R42 把"声明了过渡却没有驱动"从文件级降到调用点级，只覆盖了 `ReceiptLine`。
  要推广到 `NoticeBanner`（BACKLOG 64）时撞上：那五条的驱动是一条**派生键** ——
  `.animation(bannerIn, value: noticeSignature)`，`noticeSignature` 把五条的存在性压成 bitmask
  （`ContentView:32 / :36-44`）。按名字匹配 ⇒ 五条全红，而它们确实有电（R22 量过像素）。
- **决定**：判据加一跳"展开派生键"（键里的裸名字若在本文件有 computed property 定义，
  把 body 点到的标识符并进状态集合；点路径与最后一段都算）。
- **决定 2（这条是本体）**：展开**只增不减**；读不懂 ⇒ 退回按名字匹配，
  **既不放行也不报错**。两种极端都有先例：
  "读不懂就红" ⇒ 假阳性逼人删守卫（R34 的 U-56、R21b 的等高判据都是这一族）；
  "读不懂就放行" ⇒ 免检牌（R39b 的 `settingsDrawability` 那一族）。
  取中之后剩下的风险是**假阴性**（派生键读到了名字但那个名字不推像素），
  所以必须有 M207 那一支：从签名 body 里删掉一条 ⇒ **只有那一条红**。
- **决定 3（只展开一跳）**：两跳以上要处理环与顺序，收益不明确；
  如果哪天真的出现"派生键依赖另一个派生键"，判据会红在"这条没被推到"，
  那是**可诊断的红**，不是静默的绿。
- **代价**：只有测试代码（+3 条判据、+4 个纯函数）；产品零改动、帧零变化、本轮**不换装**。
- **谁守着**：`testDerivedKeyExpansionIsATruthTable` 五格 + `testNoticeBannerCallSitesArePoweredByTheirDerivedKey`；
  变异 M206–M209 四支全 CAUGHT。
- **仍未收口的部分**：热图那两处是**分支**门控（`if 布尔 { 一块视图 } else { … }`），
  本轮的扫描器只认"组件调用点 + `if let`" ⇒ BACKLOG 64 剩后半，已写明别当成做完了。
'''


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
    f.write(ROUND.lstrip("\n"))
with io.open("AGENT_DECISIONS.md", "a", encoding="utf-8") as f:
    f.write(DECISION.lstrip("\n"))

patch("AGENT_BACKLOG.md", [
    ("    推广之前要先让判据会把派生键**展开**成它读的那几个状态。这五条本身确实有电（R22 量过像素）。",
     "    推广之前要先让判据会把派生键**展开**成它读的那几个状态。这五条本身确实有电（R22 量过像素）。\n"
     "    **R44 做掉了一半**：派生键展开已进判据（`drivingStates`，只增不减、读不懂不放行），\n"
     "    `NoticeBanner` 那五个调用点已进名单（`testNoticeBannerCallSitesArePoweredByTheirDerivedKey`，\n"
     "    读数 `BANNER_DRIVE 调用点 5 个、展开后状态 13 个、无驱动 0 个`）。\n"
     "    **剩下一半**：热图那两处（`DailyCopyHeatmapView:44/50/78`）不是\"组件调用点 + `if let` 门控\"，\n"
     "    而是 `if 布尔 { 一块视图 } else { 另一块 }` 的**分支**形状 ⇒ 扫描器要先会认分支。\n"
     "    所以这条**仍然开着**，别因为\"NoticeBanner 做完了\"就划掉。"),
])

CHANGELOG = '''### Added（R44 · 判据会读"派生键"了 —— 调用点级的动效守卫推广到 NoticeBanner）

- 本轮**零产品改动**，改的是尺。R42 那条"调用点级"守卫要推广到 `NoticeBanner` 时被发现读不懂一种合法写法：
  `ContentView:32` 的驱动键是 `noticeSignature`，而它（`:36-44`）把五条回执的存在性压成一个 bitmask
  ⇒ 按名字匹配会把**五条全误报成没电**，而那五条确实有电（R22 量过像素）。
- 新增 `drivingStates(for:in:)`：键里的裸名字若在本文件有 computed property 定义，
  就把 body 点到的标识符并进状态集合（点路径与最后一段都算）。**只展开一跳、只增不减**：
  读不懂 ⇒ 退回按名字匹配，既不放行也不报错 ——
  "读不懂就红"会逼人删守卫（R34 / R21b 那一族），"读不懂就放行"是免检牌（R39b 那一族）。
- 剩下的假阴性风险由变异钉住：**M207** 从签名 body 里删掉一条 ⇒ 只有那一条红。
- 判据 +3（`testNoticeBannerCallSitesArePoweredByTheirDerivedKey` + 派生键展开的 5 格真值表 + 纯函数本体），
  变异 M206–M209 四支全 CAUGHT（needle 全实测抄来，且落在排过序的数组上 ⇒ 顺序稳定）。
- **BACKLOG 64 只做了一半**：热图那两处是 `if 布尔 { … } else { … }` 的**分支**形状，
  现在的扫描器只认"组件调用点 + `if let`" ⇒ 这条继续开着，别当成推广完了。
- 本轮**不换装**（没有任何"只有装上新包才看得见"的东西）；112 张帧逐字节不变。
- 验证：735 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿。

'''
patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])

VISUAL = '''
---

## Round 44 · 判据先学会读"派生键"，调用点级的动效守卫才推得动（R44 / U-70 / D-103）

**这一轮问的问题**：R42 那把新尺只量了 `ReceiptLine`。要推广到 `NoticeBanner`（BACKLOG 64），
先要回答"它读得懂 `ContentView` 的写法吗" —— 答案是**不懂**：
那五条横幅的驱动是一条派生键（`noticeSignature` 把五条存在性压成 bitmask），
按名字匹配会把五条**全部误报成没电**，而它们确实有电。

**做了什么**：给判据加一跳展开（键里的裸名字若在本文件有 computed property 定义，
把 body 点到的标识符并进来；点路径与最后一段都算）。设计上的主点是
**读不懂时既不放行也不报错** —— 只增不减，退回按名字匹配。
剩下的假阴性由变异 M207 钉：从签名 body 里删掉一条，只有那一条红。

**真实视觉审查**：零产品改动 ⇒ 没有新画面，而且不该有；本轮明确**跳过换装**并写下理由
（没有任何只有新包才看得见的东西），112 张帧逐字节不变。

**分数为什么只 +1**：尺变强不等于画面变好。`动效细节` 那一格从 13 抬到 14，
抬的是"这一族以后再加调用点会被判到"，不是"用户多看见了一件动效"。
`流畅度` 仍然 13 —— 淡入量不到那件事本轮没解决（它需要的是能进设置窗口的胶片通道）。

### 自评 93 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动；守卫守住的是"提示条进出要有过渡"这套原生语言不被悄悄写坏 |
| 流畅度 | 13 / 20 | 未动时序，也没新增像素证据（淡入仍活在 presentation 层） |
| 层次与材质 | 14 / 15 | 112 帧逐字节不变（本轮的"没退化"是可数的） |
| 动效细节 | 14 / 15 | +1：调用点级守卫覆盖到第二个组件，且会读派生键 —— 这一族再想"挂个过渡不供电"要多骗过一层 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只有测试代码；产品零成本 |

**验证**：735 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门 `红=0 NOT_RUN=0`、
脚本 83 全绿、变异 M206–M209 四支全 CAUGHT。**CI 待读**。
'''
with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
    f.write("\n" + VISUAL)

STATE = '''
---

## R44 · 判据先学会读派生键（第 46 轮 / U-70 / D-103）

- **本轮改的是尺，产品零改动**：`ContentView:32` 用一条**派生键** `noticeSignature`
  推五条 `NoticeBanner`，R42 那把按名字匹配的尺读不懂 ⇒ 直接推广会把五条**全部误报成没电**
  （而它们确实有电，R22 量过）。⇒ 先给判据加一跳展开（`drivingStates`），
  设计主点是**读不懂时既不放行也不报错**：只增不减，退回按名字匹配。
- **新增**：`testNoticeBannerCallSitesArePoweredByTheirDerivedKey`（读数
  `BANNER_DRIVE 调用点 5 个、键 1 条、展开后状态 13 个、无驱动 0 个`）
  + 派生键展开的 5 格真值表 + 三个纯函数。
- **假阴性的靶**：变异 M207 —— 从签名 body 里删掉一条 ⇒ **只有那一条红**。
  这一支在，"展开"才不是万能通行证。
- **BACKLOG 64 只做了一半**（写清楚，别当成推广完了）：热图那两处是
  `if 布尔 { … } else { … }` 的**分支**形状，扫描器现在只认"组件调用点 + `if let`"。
- **本轮不换装**，理由记账：没有任何"只有装上新包才看得见"的东西；112 帧逐字节不变。
- **验证**：735 tests / 29 skipped / 0 failures、0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿、
  变异 M206–M209 四支全 CAUGHT。自评 **93 / 100**。**CI 待读**。
- **下一步（R45）**：① BACKLOG 64 的后半（分支门控）或 ② BACKLOG 59 的存盘失败通道形状；
  ③ R42/R43/R44 三轮都在加固尺与措辞，`流畅度` 已经五轮没涨 ——
  下一轮优先做**能产生像素证据**的那类（分带抓帧 / 能进设置窗口的胶片通道），
  否则就承认这一维的上限并把话写死。
'''
patch("AGENT_STATE.md", [
    ("- **下一步（R44）**：① BACKLOG 64 的派生键展开（做成了才能把调用点级守卫推广到 NoticeBanner / 热图）；\n"
     "  ② BACKLOG 59 的存盘失败通道形状（一次性横幅 vs 常驻只读标记）；③ BACKLOG 61 等人工批次 43.4 的回答。",
     "- **下一步（R44）**：① BACKLOG 64 的派生键展开（做成了才能把调用点级守卫推广到 NoticeBanner / 热图）；\n"
     "  ② BACKLOG 59 的存盘失败通道形状（一次性横幅 vs 常驻只读标记）；③ BACKLOG 61 等人工批次 43.4 的回答。\n"
     + STATE),
])
print("R44 主体台账已写入")
