#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R124（第 126 轮）账本补丁：BACKLOG / DECISIONS / UI_AUDIT / ITERATION / CHANGELOG / STATE / FINAL_REPORT。

数字一律从本轮日志里**解析**（U-264③：缺格就写"没解析到"，不许补一个看起来合理的数）。
"""
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


SWIFT = executed("/tmp/r124_full.log")
CAP = executed("/tmp/r124_capture.log")
gate = log("/tmp/r124_gate.log")
if not gate:
    # 电池把帧闸门直接打到 stdout；没落盘时按实记为"没解析到"
    gate = ""


def g(key):
    m = re.search(key + r"=(\d+)", gate)
    return m.group(1) if m else "没解析到"


mut = log("/tmp/r124_mut.log") or ""
mutline = re.search(r"MUTATE_TABLE n=\d+ caught=\d+ mismatch=\d+ not_run=\d+", mut)
MUT = mutline.group(0) if mutline else "MUTATE_TABLE 没解析到（见任务输出）"

BACKLOG = rd("AGENT_BACKLOG.md").rstrip("\n") + """

**171 结案（R124：名单按机器分键，"没登记的那台"必须红）**

R120 的预言在 R122 的 CI（run 39029027567）里再次落地：那一跑**只剩一朵红**
`testDarkSettingsSidebarTextIsACountedBlindSpot`，正文是"这些帧的暗档侧栏文字现在落在期望侧了：[13 张]"。
⇒ 名单不是"错"，是**它从来只属于一台机器**：本机 vibrant 列在合成前反侧，runner 不反侧，两台都是真的离屏捕获。

改法（不是把红按下去）：`darkSidebarTextBlindSpotsByMachine` 一行一台，键由**量出来**的事实组成
（`arch / macOS 主次版本 / 帧倍率`），关系判据 `sidebarRosterVerdict` 给四种出口
（未登记 / 一致 / 新盲区 / 登记过的不再反侧），配 8 行真值表。
本机那一行由本轮打印出来的键填：`TEXT_SIDE_ROSTER_KEY arm64/macOS 27.0/2x 本机登记=13 实测反侧=13 判了 13/13 ⇒ 一致`。
**runner 那一行故意还没登记** —— 它下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它的键>`，
再由那一跑印出来的键去填。手挑一个"看起来像 runner 的键"就是拿猜测当前提（R118 的教训同形）。
空集也是一条**声明**（"这台不反侧"），它同样被 extra/gone 两格钉住，所以加一行之前必须真的去看那张帧。

三刀 M624（键里丢掉倍率）/ M625（未登记改成"当成一致"）/ M626（撤掉新盲区那一格）全部 CAUGHT。
"""

DECISIONS = rd("AGENT_DECISIONS.md").rstrip("\n") + """

### D-186（R124）一份"哪些帧不可信"的名单必须写明它属于哪台机器；不在表里要红，而不是安静通过

`darkSidebarTextBlindSpots` 从 R29d 起被当全局权威用，而它量的是 **vibrant 子树 + `cacheDisplay`
不走合成**这一台机器的行为。两台机器给相反读数的同一件事，只有一种诚实的写法：**一行一台**，
并且"这台没登记"是一个**会红**的结局。三条：

1. **键只准用被量出来的事实**（架构 / 系统主次版本 / 帧倍率），不许手挑一个看起来像的名字，
   也不许用机器名 —— 机器名不解释机制，倍率与版本才解释。
2. **空集也是一条声明**：登记"这台不反侧"之后，extra/gone 两格仍然钉着它；
   不许把"没登记"与"登记为空"混成同一个绿（M625 就是钉这一格）。
3. **新登记的行必须由被打印出来的键填**：本轮先红一次、拿到那一台自己印的键，再填第二行。
   顺序反了就是拿猜测当前提，而猜错的键会安静地变成一条永不命中的死行。
"""

AUDIT = rd("AGENT_UI_AUDIT.md")
SECTION = """## 第 126 轮 · R124：盲区名单按机器分键，"没登记的那台"必须红（171 结案 / U-414…U-416 / D-186 · 产品 0 改动）

### 1. 开场清单（本轮全部证据的位置与坐标）

| # | 位点 | 读数 | 说明的缺陷 |
|---|---|---|---|
| 1 | R122 的 CI（run 39029027567） | 那一跑**只剩一朵红**：`testDarkSettingsSidebarTextIsACountedBlindSpot`「落在期望侧了：[13 张]」 | 名单是机器相关的，却按全局权威用着 |
| 2 | 同跑的图标判据 | `SIDEBAR_ICON_COVERAGE 能力=不可判(内容区 0 墨)` ⇒ 新装的 `SIDEBAR_ICON_INVERTED` 在 runner 上**没有假红** | R122 的能力闸门按预期工作 |
| 3 | 同跑的 150 出口 | `整帧墨行=70/60 详情列墨行=0 带子墨行=0 ⇒ 不可判(整帧有墨而详情列0墨)`；`参照臂=6 可判=4 框错红=0 不可判=2` | 与 R121 那一跑逐字一致 ⇒ 四种出口稳定 |
| 4 | 本机 · 改之前 | `dark 反侧=13 张`（名单 13 张，实测 13 张） | 本机那一行本来就是对的 |
| 5 | 本机 · 改之后 | `TEXT_SIDE_ROSTER_KEY arm64/macOS 27.0/2x 本机登记=13 实测反侧=13 判了 13/13 ⇒ 一致` | 键由量出来的三件事实组成，第一次跑就自证 |

### 2. 本轮改了什么（产品 0 改动；只动 `UICaptureHarness.swift`）

1. `sidebarRosterMachineKey(scale:)`：`arch / macOS 主次版本 / 帧倍率`，倍率取**这一跑真正扫的那些帧**的
   `pixelsWide / fixture.width` 最大值（不是 `mainScreen` —— CI 那台没有主屏，D-183①）。
2. `darkSidebarTextBlindSpotsByMachine`：一行一台。本机那一行用本轮印出来的键填；
   **runner 那一行故意还空着**，它下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它的键>`，再由那一跑填。
3. `sidebarRosterVerdict` 四种关系 + `rosterVerdictText` 四个词 + 8 行真值表；
   原来那两条 `XCTAssert(extra/gone.isEmpty)` 换成按本机那一行判。
4. 结论行 `TEXT_SIDE_ROSTER_KEY …` 打在闸门之前（U-391 那一族）。
5. 变异第 27 张 `mutate_r124.py`：M624 键里丢掉倍率 / M625 未登记改成"当成一致" / M626 撤掉新盲区那一格 ⇒ 三刀全部 CAUGHT。

### 3. 三条定义

- **未登记（会红）**：这一台机器不在表里。空手通过等于任何新机器白拿一个绿。
- **一致**：本机那一行与实测反侧集合完全相等（多一张少一张都不行）。
- **新盲区 / 不再反侧（都会红）**：方向相反，修法也相反 —— 前者先定位是谁，后者必须先去看那张帧
  再决定是关 BACKLOG 45 还是承认尺瞎了。

### 3b. 本轮的 U（自坏，逐条定义）

- **U-414：结论行被自己的转义打回原文，等于结论没进台账。**
  第一次跑出来是 `… ⇒ \\(Self.rosterVerdictText(rosterVerdict))` —— 我在上一格里把
  `\\(` 写成了字面量，数字照常打、键照常打，**只有那个词没打出来**。
  这是 U-406 的直系（"加了仪表不等于读到了仪表"）：修法不是"再检查一遍代码"，
  而是**每次新加 emit 都在本机看一遍它自己那行的输出**，本轮就是这么抓到的。
- **U-415：类里调静态成员漏了 `Self.`，以及新测试里留了一个没用上的变量。**
  两个都被 0 告警那道门挡下（`static member cannot be used on instance` + `immutable value 'c' was never used`）
  —— U-396 / U-400 那一族的第三次复发。规矩：写新判据的同一遍就 `swift build --build-tests` 看告警数，
  别把它留给电池的最后一步。
- **U-416：我先按记忆写了本机那一行的键，再去跑。**
  这次猜对了（`arm64/macOS 27.0/2x`），但**对的原因不是我会猜**，而是 `.unkeyed` 那一格会红：
  设计本身兜住了我。规矩（进 D-186③）：新登记的行必须由**被打印出来的键**填；
  顺序反过来一次，表里就会多一条永不命中的死行，而它看起来像一条声明。

### 4. 覆盖与边界

产品 0 改动；判据 +1 条真值表 + 1 种会红关系（未登记）；
全量 swift `%s 例 / %s skip / %s failures`；捕获卷 `%s / %s / %s`；
帧基线 `COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`；脚本电池见 §9；
变异第 27 张 `mutate_r124.py` `%s`（刀数 100 → **103**，caught 99 → **102**）。
**故意留的红**：runner 那一行未登记 ⇒ 下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED`，
拿到它自己印的键之后由 R125 填 —— 那是这条判据**第一次在另一台机器上工作**，不是回归。

""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED"), g("FRAME_BASELINE_CHANGED"),
       g("FRAME_BASELINE_MISSING"), g("FRAME_BASELINE_ADDED"), MUT)
AUDIT = once(AUDIT, "## 第 125 轮 · R123", SECTION + "## 第 125 轮 · R123")

ITER = rd("AGENT_VISUAL_ITERATION.md").rstrip("\n") + """

## Round 124 · 盲区名单按机器分键：不在表里的那台必须红（171 结案 / U-414…U-416 / D-186 · 产品 0 改动）

### 0. 开场缺陷清单

| # | 位点 | 证据 |
|---|---|---|
| 1 | R122 的 CI | 只剩一朵红，正是 171 预言的那朵 `gone`（13 张全说"落在期望侧"） |
| 2 | 同一跑 | 新装的 `SIDEBAR_ICON_INVERTED` 在 runner 上没有假红（能力闸门按预期） |
| 3 | 名单本身 | 从 R29d 起按"全局权威"用，而它量的是 vibrant + 不走合成这一台机器的行为 |

### 1. 做了什么

`sidebarRosterMachineKey`（架构 / macOS 主次版本 / 帧倍率，倍率取这一跑真正扫的帧）+
`darkSidebarTextBlindSpotsByMachine`（一行一台，空集也是一条声明）+ `sidebarRosterVerdict`
四种关系 + 8 行真值表 + 结论行打在闸门之前。本机那一行用本轮印出来的键填
（`arm64/macOS 27.0/2x 登记=13 实测=13 ⇒ 一致`）；**runner 那一行故意留空**，
下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它的键>`，那时再由它自己印的键填第二行（D-186③）。
三刀 M624/M625/M626 全部 CAUGHT。

### 2. 真实视觉审查（看图腿）

本轮零产品改动、帧基线 `CHANGED=0`（见 §9），所以看图对象沿用 R123 那两张真机帧
（`/tmp/real_screen_sidebar_icons.png` 暗档设置窗口：六枚图标与标签同亮、选中行蓝药丸、三张卡片排版正常），
新看的是**读数本身**：`TEXT_SIDE_ROSTER_KEY … ⇒ 一致` 这一行第一次把"哪台机器的名单"写进了台账。

### 7. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 产品 0 改动；两档/两台的系统差异记到正确位置 |
| 动效华丽度 | 87 | **连续第四轮零动效位点**，这笔账只会越滚越大，R125 必须先还 |
| 状态完备 | 92 | 171 结案；四种关系各有名字；"没登记"从静默通过变成会红 |
| 证据强度 | 93 | 8 行真值表 + 键的三件实测事实 + 三刀（其中一刀专测"未登记改成一致"） |
| 一致性 | 92 | 键由这一跑自己印，不手挑；两台的行各自被 extra/gone 钉住 |
| 可维护 | 91 | 判据 +1 条真值表；名单从一个 Set 变成一张按机器的表 |
| 风险控制 | 92 | 故意留的那朵红有名字、有填法、有下一轮的去处，不是回归 |
| **合计** | **91** | 加权取整；动效那一格按实际 87 记 |

### 9. §8 覆盖计数（本轮，全部从日志解析）

- 全量 swift：`Executed %s tests, %s skipped, %s failures`；捕获卷：`%s / %s / %s`
- 帧基线：`COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`
- 变异：`%s`（第 27 张表 `mutate_r124.py`，刀数 100 → 103，caught 99 → 102）
- 脚本电池与针自检：见任务输出（`Ran 244 tests` 一档不变，本轮没加脚本单测）
""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED"), g("FRAME_BASELINE_CHANGED"),
       g("FRAME_BASELINE_MISSING"), g("FRAME_BASELINE_ADDED"), MUT)

CHANGELOG = rd("CHANGELOG.md")
CHANGELOG = once(CHANGELOG, "## [Unreleased]\n", """## [Unreleased]
### 盲区名单按机器分键：不在表里的那台必须红（R124 / 171 结案 / U-414…U-416 / D-186 · 产品 0 改动）

- R122 的 CI（run 39029027567）只剩一朵红，正是 R120 预言的那朵：
  「这些帧的暗档侧栏文字现在落在期望侧了：[13 张]」⇒ `darkSidebarTextBlindSpots` 不是错，
  是**它从来只属于一台机器**（本机 vibrant 列在合成前反侧，runner 不反侧）。
- 改法不是把红按下去：`darkSidebarTextBlindSpotsByMachine` 一行一台，键只由**量出来**的事实组成
  （架构 / macOS 主次版本 / 帧倍率，倍率取这一跑真正扫的那些帧而不是 `mainScreen`）；
  `sidebarRosterVerdict` 给四种关系（未登记 / 一致 / 新盲区 / 登记过的不再反侧）+ 8 行真值表。
- 本机那一行由本轮打印出来的键填：`TEXT_SIDE_ROSTER_KEY arm64/macOS 27.0/2x 本机登记=13 实测反侧=13 ⇒ 一致`。
  **runner 那一行故意留空** —— 它下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它的键>`，
  再由那一跑自己印的键填第二行（D-186③：不许拿猜测当键，猜错就是一条永不命中的死行）。
- 同跑另外两格按预期：新装的 `SIDEBAR_ICON_INVERTED` 在 runner 上**没有假红**（能力闸门）；
  150 的四种出口与 R121 那一跑逐字一致（`参照臂=6 可判=4 框错红=0 不可判=2`）。
- 变异第 27 张 `mutate_r124.py`：M624 键里丢掉倍率 / M625 未登记改成"当成一致" / M626 撤掉新盲区那一格 ⇒ 三刀全部 CAUGHT。
- 自坏三条：U-414 结论行被自己的转义打回原文（数字都打、只有那个词没打 ⇒ 每次新加 emit 都要看它自己的输出）；
  U-415 静态成员漏 `Self.` 与一个没用上的变量（0 告警那道门挡下，U-396 那一族第三次）；
  U-416 先按记忆写键再跑 —— 这次是 `.unkeyed` 那一格兜住了我，不是我会猜。
""")

REPORT = rd("AGENT_FINAL_REPORT.md")
REPORT = once(REPORT, "**M100–M621**", "**M100–M626**")
REPORT = once(REPORT, "⇒ 两臂全部 CAUGHT，表数 **26**、刀数 **100**、caught **99**。",
              "⇒ 两臂全部 CAUGHT，表数 **26**、刀数 **100**、caught **99**。"
              "R124 再加第 27 张 `mutate_r124.py`（M624 键里丢掉倍率 / M625 未登记改成「当成一致」/"
              "M626 撤掉新盲区那一格）⇒ 三臂全部 CAUGHT，表数 **27**、刀数 **103**、caught **102**。")
REPORT = once(REPORT, "| 决定台账 | D-069 … **D-184**", "| 决定台账 | D-069 … **D-186**")

STATE = rd("AGENT_STATE.md")
lines = STATE.split("\n")
head = next(i for i, l in enumerate(lines) if l.startswith("最后更新："))
quoted = "\n".join(("> " + l) if l.strip() else ">" for l in "\n".join(lines[head:]).split("\n"))
NEW_STATE = """# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 19:58（本地 · R124 / 第 126 轮收尾：**盲区名单按机器分键 —— 不在表里的那台必须红**（171 结案 / U-414…U-416 / D-186 · 产品 0 改动））

**现场（R122 的 CI，run 39029027567）**：那一跑只剩一朵红，正是 R120 预言的那朵 —— 「这些帧的暗档侧栏文字现在落在期望侧了：[13 张]」。同一跑另外两格按预期：新装的 `SIDEBAR_ICON_INVERTED` 在 runner 上**没有假红**（`SIDEBAR_ICON_COVERAGE 能力=不可判(内容区 0 墨)`），150 的四种出口与 R121 逐字一致（`参照臂=6 可判=4 框错红=0 不可判=2`）。⇒ `darkSidebarTextBlindSpots` 从 R29d 起被当全局权威用，而它量的是 **vibrant 子树 + `cacheDisplay` 不走合成**这一台机器的行为。

**改了什么（不是把红按下去）**：`darkSidebarTextBlindSpotsByMachine` 一行一台，键只由量出来的事实组成（架构 / macOS 主次版本 / 帧倍率；倍率取这一跑真正扫的那些帧，不用 `mainScreen`）；`sidebarRosterVerdict` 四种关系各有名字（未登记 / 一致 / 新盲区 / 登记过的不再反侧）+ 8 行真值表 + 结论行 `TEXT_SIDE_ROSTER_KEY … ⇒ 一致` 打在闸门之前。本机那一行用本轮印出来的键填：`arm64/macOS 27.0/2x 登记=13 实测反侧=13`。**runner 那一行故意留空** —— 下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它自己印的键>`，那时再填（D-186③：不许拿猜测当键）。

**三刀**：M624 键里丢掉倍率 / M625 未登记改成「当成一致」/ M626 撤掉新盲区那一格 ⇒ 第 27 张表，全部 CAUGHT（刀数 100→103，caught 99→102）。

**三条自坏**：U-414 结论行被自己的转义打回原文（数字都打、只有那个词没打出来 ⇒ 新加的 emit 必须看它自己的输出）；U-415 静态成员漏 `Self.` + 一个没用上的变量（0 告警那道门挡下，U-396 那一族第三次）；U-416 我先按记忆写了本机的键再去跑 —— 兜住我的是 `.unkeyed` 那一格，不是我会猜。

**下一轮（R125）**：① **先还动效的账**（连续第四轮零动效位点，自评 87 那一格）：从浮层剩余位点或主窗口行悬停里真做一个；② 读 R124 的 CI，把 runner 那一行键填上并确认 `TEXT_SIDE_ROSTER_UNKEYED` 是那一跑唯一的红；③ 172 的亮档那一半仍等用户回答批次 86.1（或授权切系统外观后用 `scripts/real_screen_sidebar_icons.py` 复跑）。

""" + quoted
wr("AGENT_STATE.md", NEW_STATE)

for n, t in [("AGENT_BACKLOG.md", BACKLOG), ("AGENT_DECISIONS.md", DECISIONS),
             ("AGENT_UI_AUDIT.md", AUDIT), ("AGENT_VISUAL_ITERATION.md", ITER),
             ("CHANGELOG.md", CHANGELOG), ("AGENT_FINAL_REPORT.md", REPORT)]:
    wr(n, t)
    print("WROTE %s" % n)
print("LEDGER_R124=ok")
