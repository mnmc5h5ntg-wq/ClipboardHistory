#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R126（第 128 轮）账本补丁。数字从本轮日志解析。"""
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


SWIFT = executed("/tmp/r126_full.log")
CAP = executed("/tmp/r126_capture.log")
gate = log("/tmp/r126_gate.log")
mut = log("/tmp/r126_mut.log")
MUTL = re.search(r"MUTATE_TABLE n=\d+ caught=\d+ mismatch=\d+ not_run=\d+", mut)
MUT = MUTL.group(0) if MUTL else "MUTATE_TABLE 没解析到（见任务输出）"

BACKLOG = rd("AGENT_BACKLOG.md").rstrip("\n") + """

**171 追记 3（R126：第二行按 runner 自己印的键登记，空集也是一条声明）**

R124 故意留的那朵红在 run 39031123341 里交出键来了：
`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 个夹具 ⇒ 红(这台机器的位没登记)`。
⇒ 表里加第二行 `"arm64/macOS 15.7/1x": []`。
**空集不是占位，是一条会被两格钉住的声明**："这台机器上侧栏暗档文字不反侧"。
哪天它反侧 ⇒ `新盲区` 红；哪天有人把本机那 13 张抄进这一行 ⇒ 这一台的 `不再反侧` 红。
另加两格**本机就能红**的结构判据（不依赖 runner）：表必须 ≥2 行；键必须成形
（`arch/macOS 主次版本/倍率`，倍率只准 `1x`/`2x`）。理由：`runner`、`CI` 这种"看起来像"的键
能通过任何按数量的懒判据，却永远不会被命中 —— 那是一条死行，比没有更坏（D-188）。
⇒ 下一跑 CI 的期望：这一台读到 `⇒ 一致`，**捕获卷不再有红**（171 全结案）。

**173 追记（R126：这笔账不能用"再造一个动效"来还）**

本轮按清单侦察了四个候选位点，三个的结论是**这里已经量过并写下了不做的理由**：
① 热图格子悬停 —— `withAnimation(.hover)` 挂在变更点上、`hoverRingOpacity` 是有名字的数（R45 有帧）；
② 菜单栏推荐 —— `MenuBarExtraStyle.menu` 编译成**真 NSMenu**（D-055 / M15 实测），
   SwiftUI 过渡在那一层根本不执行，挂 `.transition` 就是自欺（R5 删过一条）；
③ 骨架扫光 —— 时钟形状、亮带宽度 0.3、30Hz、峰值抬升 0.05→0.12 才读得到东西，
   全部有取证记录（R84/R85），而覆盖率 0.522 对地板 0.50 这一格登记表里已写明"不抬成 must_judge"的理由。
⇒ 173 的下一步**不是**"随便挑一处加个动画"（那正是本目标禁止的"为动效而动效"），
而是等一次**用户可见的**观察：批次 86.1（亮档图标）与批次 83.1（真机浮层输入时整条查询有没有底色）
都是能给出"这里少了什么"的通道。本条保持开着，但把判据改成：
**要么由一次真机/用户观察指出具体缺陷再动，要么按 ①②③ 的样子把"不加"的理由量出来**。
"""

DECISIONS = rd("AGENT_DECISIONS.md").rstrip("\n") + """

### D-188（R126）登记表里"没登记"与"登记为空"是两种状态；后者也要能被本机判

`darkSidebarTextBlindSpotsByMachine` 的第二行是**空集** —— 它说的是一件真事
（CI runner 那台机器不复现侧栏暗档反侧）。空集与"这台没在表里"如果走同一个出口，
要么缺席被读成"这台没问题"（假绿），要么空集被读成"还没登记"（永久红）。两条都要防，所以：

1. **未登记 = 红**（R124），**登记为空 = 一条声明**，被 `新盲区`/`不再反侧` 两格钉住；
2. **表自身的结构要能在本机红**：行数 `>=2`、键必须成形（`arch/macOS 主次版本/倍率`）。
   只判数量不判形状，`runner`、`CI` 这种永不命中的死键就能混过闸门 ——
   而死行比空表更坏：它让"按机器分键"这件事看起来已经完成。
3. **键必须由那一台自己印出来**（R124 故意留一朵红，换 run 39031123341 那一行读数）。
"""

AUDIT = rd("AGENT_UI_AUDIT.md")
SECTION = """## 第 128 轮 · R126：runner 那一行按它自己印的键登记（空集=声明），并给登记表加了两格本机就能红的结构判据（171 全结案 / 173 改判 / U-420…U-422 / D-188 · 产品 0 改动）

### 1. 开场清单（本轮全部证据的位置与坐标）

| # | 位点 | 读数 | 说明的缺陷 / 结论 |
|---|---|---|---|
| 1 | R124 的 CI（run 39031123341） | `TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 ⇒ 红(这台机器的位没登记)` | 键由那一台自己印出来 ⇒ 本轮照它登记第二行 |
| 2 | 同一跑 | `SIDEBAR_ICON_COVERAGE 能力=不可判(内容区 0 墨)`、`MOTION_GATE_RESULT=ok 红=0` | 除 171 那朵之外没有别的红 ⇒ 171 结案后 CI 应全绿 |
| 3 | 本机 · 加行之后 | `TEXT_SIDE_ROSTER_KEY arm64/macOS 27.0/2x 本机登记=13 实测反侧=13 判了 13/13 ⇒ 一致` | 两行互不污染：改第二行不动第一行的判定 |
| 4 | 清单侦察四个位点 | 热图 hover 已挂在变更点 + `hoverRingOpacity` 有名字；菜单栏推荐是**真 NSMenu**（D-055/M15）；骨架扫光的形状与抬升都有取证（R84/R85） | **没有一处支持"再加一个动效"** ⇒ 173 改判为"等一次用户可见的观察，或把『不加』量出来" |

### 2. 本轮改了什么（产品 0 改动；只动 `UICaptureHarness.swift`）

1. `darkSidebarTextBlindSpotsByMachine` 加第二行 `"arm64/macOS 15.7/1x": []`，
   注释里写明键与空集两处都来自 run 39031123341 的读数（不是猜的）。
2. `sidebarRosterKeyIsWellFormed(_:)` + 两格结构判据：表 `>=2` 行、每个键必须成形
   （三段、`macOS 主次版本`、倍率只准 `1x`/`2x`）。这两格**在本机就能红**，不依赖 runner。
3. 真值表补 3 个成形键 + 8 个不成形键（`runner` / `CI` / `macos-15` / 缺段 / 段序错 / 倍率不是 1x2x / 架构不认识）。
4. 变异第 29 张 `mutate_r126.py`：M629 删掉第二行 / M630 键形状判据改恒真 ⇒ 两刀全部 CAUGHT。
   第一版这张表**两臂都报 PASSED**，因为 `sed` 复制时漏改了 `TRUTH` 常量（U-421），
   顺带暴露两格结构判据放错了测试（U-422）—— 搬回去 + 改对靶之后才是真的 CAUGHT。
5. 173 的判据改写法（见 BACKLOG 追记）：不再承诺"下一轮加一条动效"，
   改成"要么由真机/用户观察指出具体缺陷再动，要么像 ①②③ 那样把『不加』的理由量出来"。

### 3. 三条定义

- **未登记（红）**：这台机器不在表里 ⇒ 必须去看、必须自己印键。
- **登记为空（合法声明）**：这台机器不复现 ⇒ 由 extra/gone 两格继续钉住，不是免检。
- **死键（会红）**：形状不对的键永远不会被命中 ⇒ `sidebarRosterKeyIsWellFormed` 拦。

### 3b. 本轮的 U（自坏，逐条定义）

- **U-422：两格登记表的结构判据被我放错了家。**
  它们判的是**盲区名单**（行数、键形状），我却写进了 `testEveryMotionKindIsWiredSomewhereInProduct`
  —— 那条测试判的是动效接线，名字里也没有 roster。后果有两层：下一轮找这两格的人看不见它们；
  而变异表按"这条判据住在哪个用例"打点，M629 因此指错了靶。
  修法是搬回 `testSidebarRosterVerdictIsATruthTable`，同时把 M629 的期望重新验一遍（两刀现在都 CAUGHT）。
- **U-421：变异表是从上一张 `sed` 出来的，臂名与文档串都改了，唯独 `TRUTH` 常量没改。**
  于是 M629/M630 两臂都打在**上一轮的尺子**（动效真值表）上，双双报 `PASSED` ——
  而 `MUTATE_TABLE n=2 caught=0 mismatch=2` 是这张表自己喊出来的（它没被记成通过，`RESTORE_CLEAN=yes` 也真）。
  规矩：`sed` 复制上一张表之后，第一件事是把 `TEST`/`TRUTH` 常量与本轮判据对账 ——
  读一遍它到底 filter 了哪个用例名，而不是相信文档串里那句"本轮"。
- **U-420：为了"还动效的账"连查四个表面，其中三个的结论早就写在代码注释里。**
  侦察本身花了本轮约三分之一的时间，而产出是"这里没有可做的动效"。
  教训不是"别侦察"，而是**清单式选位点之前先读候选位点的既有结论**：
  ①②③ 三处都带着实测过的"为什么不做/为什么这样做"，那些注释本轮才第一次被读到。
  反向的收获同样重要：如果本轮为了交差硬加一条动画，就是目标里明令禁止的那件事。

### 4. 覆盖与边界

产品 0 改动；判据 +2 格结构判据 + 11 个键形状样本；变异第 29 张两刀全 CAUGHT
（刀数 105 → **107**，caught 104 → **106**）；全量 swift `%s 例 / %s skip / %s failures`；
捕获卷 `%s / %s / %s`；帧基线 `COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`。
**留给下一跑的验证**：runner 那一台应当读到 `⇒ 一致`，捕获卷不再有红 ⇒ 171 全结案；
这条预测写在这里，红了就是名单又翻脸（而它现在有能力红）。

""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED", gate), g("FRAME_BASELINE_CHANGED", gate),
       g("FRAME_BASELINE_MISSING", gate), g("FRAME_BASELINE_ADDED", gate))
AUDIT = once(AUDIT, "## 第 127 轮 · R125", SECTION + "## 第 127 轮 · R125")

ITER = rd("AGENT_VISUAL_ITERATION.md").rstrip("\n") + """

## Round 126 · runner 那一行盲区位按它自己印的键登记（空集=声明），登记表加上两格本机就能红的结构判据（171 全结案 / 173 改判 / U-420…U-422 / D-188 · 产品 0 改动）

### 0. 开场缺陷清单

| # | 位点 | 证据 |
|---|---|---|
| 1 | R124 故意留的红 | `TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 ⇒ 红(这台机器的位没登记)` |
| 2 | 同跑其余 | `MOTION_GATE_RESULT=ok 红=0`、图标判据在 runner 上没假红 ⇒ 171 是最后一朵 |
| 3 | 173 的四个候选位点 | 三处已有量过的"为什么不做"（热图 hover / 真 NSMenu / 骨架扫光） |

### 1. 做了什么

加第二行 `"arm64/macOS 15.7/1x": []`（键与空集都抄自那一跑的读数，不是猜的）；
`sidebarRosterKeyIsWellFormed` + 表 `>=2` 行 + 键必须三段成形 —— 这三格**在本机就能红**，
所以"按机器分键"这件事不再只能等 CI 验收。真值表补 11 个键样本。
变异第 29 张：M629 删第二行 / M630 键形状恒真 ⇒ 两刀 CAUGHT。

### 2. 真实视觉审查（看图腿）

本轮零产品改动、帧基线 `CHANGED=0`，看图沿用 R123 那张真机暗档设置窗口（六枚图标与标签同亮、
选中行蓝药丸、三张卡片排版正常）。新看的是**清单侦察读到的三处代码形状**：
菜单栏那一处是 `MenuBarExtraStyle.menu` 编译成真 `NSMenu`（SwiftUI 过渡根本不执行），
这条如果没读到、本轮就会在那里挂一条永远不生效的 `.transition` —— 那才是目标禁止的事。

### 7. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 产品 0 改动；菜单栏那处按系统真实行为（NSMenu）判，不按愿望判 |
| 动效华丽度 | 86 | 第六轮零新增；本轮的结论是"没有证据支持的位点可加"，并把它写进 173 的判据 |
| 状态完备 | 92 | 171 全结案（两行、四种关系、空集也是声明）；下一跑有可证伪的预测 |
| 证据强度 | 93 | 两格本机可红的结构判据 + 11 个键样本 + 两刀 |
| 一致性 | 92 | 键来自被登记那台自己印的读数；两行互不污染（本机仍 `一致`） |
| 可维护 | 92 | 死键会被拦；表退化成一机别名会被拦 |
| 风险控制 | 92 | 没有为了交差硬加动画；预测写在账上，红了看得见 |
| **合计** | **91** | 加权取整；动效那一格按实际 86 记 |

### 9. §8 覆盖计数（本轮，全部从日志解析）

- 全量 swift：`Executed %s tests, %s skipped, %s failures`；捕获卷：`%s / %s / %s`
- 帧基线：`COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`
- 变异：第 29 张 `mutate_r126.py` `%s`（刀数 105 → 107，caught 104 → 106）
- 脚本电池与针自检：落盘后重跑，见下

""" % (SWIFT[0], SWIFT[1], SWIFT[2], CAP[0], CAP[1], CAP[2],
       g("FRAME_BASELINE_COMPARED", gate), g("FRAME_BASELINE_CHANGED", gate),
       g("FRAME_BASELINE_MISSING", gate), g("FRAME_BASELINE_ADDED", gate), MUT)

CHANGELOG = rd("CHANGELOG.md")
CHANGELOG = once(CHANGELOG, "## [Unreleased]\n", """## [Unreleased]
### runner 那一行盲区名单按它自己印的键登记；登记表加上两格本机就能红的结构判据（R126 / 171 全结案 / 173 改判 / U-420…U-422 / D-188 · 产品 0 改动）

- R124 故意留的那朵红交出键来（run 39031123341）：
  `TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 ⇒ 红(这台机器的位没登记)`
  ⇒ 表里加第二行 `"arm64/macOS 15.7/1x": []`。**空集是一条声明**（这台机器不复现侧栏暗档反侧），
  仍然被 `新盲区`/`不再反侧` 两格钉住；本机那一行不受影响（`登记=13 实测=13 ⇒ 一致`）。
- 新增两格**在本机就能红**的结构判据，不必等 CI：表必须 `>=2` 行；每个键必须成形
  （`arch/macOS 主次版本/倍率`，倍率只准 `1x`/`2x`）。真值表补 3 个成形键 + 8 个不成形键
  （`runner`、`CI`、`macos-15`、缺段、段序错、倍率不合法、架构不认识）。
  理由：形状不对的键永远不会被命中 —— 死行比空表更坏，它让"按机器分键"看起来已完成。
- 173 改判：本轮按动效清单侦察四个位点，三处已有量过的"为什么不做/为什么这样做"
  （热图 hover 挂在变更点 + `hoverRingOpacity` 有名字；`MenuBarExtraStyle.menu` 编译成**真 NSMenu**，
  SwiftUI 过渡根本不执行；骨架扫光的时钟形状与亮带抬升都有取证）。
  ⇒ 不再承诺"下一轮加一条动画"，改成"要么由真机/用户观察指出具体缺陷再动，要么把『不加』量出来"。
  **为了还账而硬加动画，正是目标禁止的那件事**（U-420）。
- 变异第 29 张 `mutate_r126.py`：M629 删掉第二行 / M630 键形状判据改恒真 ⇒ 两刀全部 CAUGHT
  （刀数 105 → 107，caught 104 → 106）。**第一版是两臂 PASSED**：`sed` 从上一张复制时只改了臂名与
  文档串、没改 `TRUTH` 常量，两臂打在上一轮的尺子上（U-421）；修的过程中又发现两格结构判据
  被放进了动效那条测试里（U-422）—— 搬回真值表、改对靶，才是现在这两个 CAUGHT。
- 下一跑的可证伪预测：runner 那台应读到 `⇒ 一致`，捕获卷不再有红 ⇒ 171 全结案。
""")

REPORT = rd("AGENT_FINAL_REPORT.md")
REPORT = once(REPORT, "**M100–M628**", "**M100–M630**")
REPORT = once(REPORT, "⇒ 两臂全部 CAUGHT，表数 **28**、刀数 **105**、caught **104**。",
              "⇒ 两臂全部 CAUGHT，表数 **28**、刀数 **105**、caught **104**。"
              "R126 再加第 29 张 `mutate_r126.py`（M629 删掉 runner 那一行 / M630 键形状判据改恒真）"
              "⇒ 两臂全部 CAUGHT，表数 **29**、刀数 **107**、caught **106**。")
REPORT = once(REPORT, "| 决定台账 | D-069 … **D-187**", "| 决定台账 | D-069 … **D-188**")

STATE = rd("AGENT_STATE.md")
lines = STATE.split("\n")
head = next(i for i, l in enumerate(lines) if l.startswith("最后更新："))
quoted = "\n".join(("> " + l) if l.strip() else ">" for l in "\n".join(lines[head:]).split("\n"))
NEW = """# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 20:32（本地 · R126 / 第 128 轮收尾：**runner 那一行盲区名单按它自己印的键登记（空集=声明）**，登记表加上两格本机就能红的结构判据（171 全结案 / 173 改判 / U-420…U-422 / D-188 · 产品 0 改动））

**现场（R124 的 CI，run 39031123341）**：`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 ⇒ 红(这台机器的位没登记)`，而同一跑 `MOTION_GATE_RESULT=ok 红=0`、图标判据在 runner 上没假红 ⇒ 171 是最后一朵红。上一轮故意留它，就是为了拿到这个键。

**做了什么**：表里加第二行 `"arm64/macOS 15.7/1x": []` —— **空集是一条声明**（这台机器不复现侧栏暗档反侧），仍被 `新盲区`/`不再反侧` 两格钉住；本机那一行不受影响（`登记=13 实测=13 ⇒ 一致`）。另加两格**在本机就能红**的结构判据：表必须 ≥2 行、每个键必须成形（`arch/macOS 主次版本/倍率`，倍率只准 1x/2x），真值表补 3 个成形键 + 8 个不成形键。理由：`runner`、`CI` 这种"看起来像"的死键能通过任何按数量的懒判据却永远不被命中，而死行比空表更坏（D-188）。变异第 29 张 M629/M630 两刀 CAUGHT。

**173 改判（重要）**：本轮按动效清单侦察四个位点，三处的结论早就写在代码里 —— 热图格子悬停已把事务挂在变更点上（`hoverRingOpacity` 是有名字的数）；`MenuBarExtraStyle.menu` 编译成**真 NSMenu**（D-055 / M15 实测），SwiftUI 过渡在那一层根本不执行；骨架扫光的时钟形状、亮带宽度、0.05→0.12 的抬升全有取证。**没有一处支持"再加一个动效"**，而为了还账硬加正是目标明令禁止的事。⇒ 173 改成"要么由真机/用户观察指出具体缺陷再动，要么像这三处一样把『不加』量出来"。这笔账诚实记：**连续第六轮零新增动效**（自评 86 那一格）。

**U-420**：清单式选位点之前应先读候选位点的既有结论 —— 本轮约三分之一的时间花在侦察上，产出是"这里没有可做的动效"，而那些"为什么不做"的注释是第一次被读到。

**下一轮（R127）**：① 读 R126 的 CI，确认 runner 读到 `⇒ 一致` 且**捕获卷全绿**（这是 171 结案的第二半，也是本轮写在账上的可证伪预测）；② 172 亮档那一半：等用户回答批次 86.1，或授权切系统外观后用 `scripts/real_screen_sidebar_icons.py` 复跑；③ 动效不再空转：若 ①② 都没有新观察，就把 173 转成"按表面清账"的收尾判据，而不是再造动画。

""" + quoted
wr("AGENT_STATE.md", NEW)

for n, t in [("AGENT_BACKLOG.md", BACKLOG), ("AGENT_DECISIONS.md", DECISIONS),
             ("AGENT_UI_AUDIT.md", AUDIT), ("AGENT_VISUAL_ITERATION.md", ITER),
             ("CHANGELOG.md", CHANGELOG), ("AGENT_FINAL_REPORT.md", REPORT)]:
    wr(n, t)
    print("WROTE %s" % n)
print("LEDGER_R126=ok")
