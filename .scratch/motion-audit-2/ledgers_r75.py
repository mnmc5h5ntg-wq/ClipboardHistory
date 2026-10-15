#!/usr/bin/env python3
"""R75 的台账落盘：七份文件，每处替换都必须命中恰好一次，否则整条跳过并报错。

本轮的账全部挂在三遍真实 CI 日志上（run 38726667469 / 38726991211 / 38730788527），
每一段里出现的毫秒数、帧数、run 号都是从 `/tmp/r75_r7{2,3,4}.log` 里 grep 出来的原文。
"""
import io
import os
import sys

REPO = "/Users/wangziyi/Codex_Project0"
EDITS = []
APPENDS = []
BEFORES = []


def edit(path, old, new):
    EDITS.append((path, old, new))


def append(path, text):
    APPENDS.append((path, text))


def before(path, anchor, text):
    BEFORES.append((path, anchor, text))


def read(path):
    with io.open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


# ---------------------------------------------------------------- 1. 看图台账
append("AGENT_VISUAL_ITERATION.md", '''

---

## Round 75 · 那条红既不是产品也不是环境：是判据拿两帧的采样间隔当了时长（结案 104 / U-129、U-130 / D-133）

**靶**：读 R72 / R73 / R74 三遍 CI。BACKLOG 104 的①/②在等这三遍 —— 证人换成 0.004 的节拍之后，
runner 上到底落到哪一档，以及 `notice-banner` 那条红了三次的事到底是产品还是环境。

### 开场读数（同一份判据代码，三遍 runner + 本机一遍）

| | 帧数 | 变化段时长 | 事件内最粗 | 证人采样 / 可分数段 / 合格 / 判定 | 结论 |
|---|---|---|---|---|---|
| run 38726667469（R72） | **2** | 32ms | 18ms | 32ms / 4 / 是 / 拍成跳变 | **红** |
| run 38726991211（R73） | **2** | ≥60ms | — | 32ms / 4 / 是 / 拍成跳变 | **绿** |
| run 38730788527（R74） | **2** | 36ms | 19ms | 32ms / 4 / 是 / 拍成跳变 | **红** |
| 本机（R75 这一遍） | 11–12 | 182ms | 20ms | 4ms / 37 / 是 / **能分辨** | 绿 |

⇒ **① 有答案**：那 80ms 里抓帧只占 0.4–0.5ms，其余全是节拍；改成 0.004 之后 runner 上采样 32ms、
可分数段 4 ⇒ 证人第一次**有资格**作证（`合格=是`）。
⇒ **② 的答案不是我预期的任何一种**：证人三遍都说"这台机器把一条已知 150ms 的淡入拍成跳变"
（`中间态帧数=0`），而 `testTransitionsAreActuallyRunning` 却在同样的两帧上判出一次绿两次红。
**两帧的变化段里，"时长"就是一次采样间隔** —— 那条判据一直在拿采样器的抖动作产品断言，
而它自己造的证人站在同一个循环里，却只被阳性对照那一支问话。

### 这一轮值什么

- **把证人接到 `.jump` 那一支**（`jumpAdjudication`，纯函数 + 八格真值表）：
  证人看得见淡入 ⇒ 这一臂读成跳变就是产品的事（红）；证人合格且自己也 snap ⇒ 报
  `MOTION_NOT_RUN=witness-snaps-here`，不判产品。**不对称是刻意的**：绿是正面证据不需要借口，
  缺席的证据才要先确认这台机器看得不见得见。
- **登记表跟着实测走**：`notice-banner` 的 `must_judge` true ⇒ false（地板 4 ⇒ **3**，带两个 run 号），
  另外三臂一条都不放。R57 那条 Swift 守卫从"两臂都必须 true"改成
  **"放宽必须带理由与 run 号"** —— 它现在读 `allowed_not_run_reasons` 那个数组，不读整块散文。
- **M395 当场抓到我自己新写的守卫**：第一版用 `bannerBlock.contains("witness-snaps-here")`，
  而那一臂的 note 里就写着 `MOTION_NOT_RUN=witness-snaps-here`（那是在**解释**这次放宽）
  ⇒ 删掉数组里那一项，守卫照旧绿。**放宽的守卫被放宽条目的说明文字喂饱**（U-130），
  与 R55 的 M276、R79 的"守卫命中自己写下的名字"同族。修成读字段之后 M395 CAUGHT。
- 顺手一条跨机验证：R74 那条 `OVERLAY_HOVER_REFLOW` 在 runner 上给出**与本机逐字相同**的读数
  （帧夹具 6/1/1、嵌套前缀 8/7/6）⇒ 重排这件事不吃机器，R74 的决定在两台上都成立。

### 牙（M392–M397，5/5 CAUGHT，抓到=5 逃掉=0 没跑成=0 未落地=0）

| 刀 | 动的是 | 期望红在 |
|---|---|---|
| M392 | `jumpAdjudication` 永远放行 | 真值表（一条只会赦免的表就是免检牌） |
| M393 | `jumpAdjudication` 永远不放行 | 真值表（赦免恰好只有一个形状） |
| M395 | 从理由数组里删掉 `witness-snaps-here` | Swift 那半条 + python 那格（**第一版逃掉**） |
| M396 | 抹掉 note 里的两个 run 号 | Swift 那半条（放宽必须留证据） |
| M397 | `must_judge` 改回 true | python 那格（清单变了期望就得跟着变） |

**一刀按实不收进计数**：把真判据里 `.jump` 那一支的问话删掉、退回无条件 `XCTFail` ——
本机证人 `判定=能分辨`，那条路径在本机走不到 ⇒ 本地无判别力，由 runner 判
（下一轮读 `MOTION_NOT_RUN=witness-snaps-here notice-banner` 在不在，就是它的验收）。
沿用 M168 / M385 的先例，不混进 CAUGHT。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 0 产品文件；横幅那条淡入今天在两台机器上有了不同的、各自说得清的身份 |
| 流畅度 | 17 / 20 | 淡入的可测性往前一格：判不到现在有名字，且**能分辨的那台仍然会红**（M393 钉着） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 三遍 CI 的读数第一次能拼成一句结论；真正的修法（77 路 b）仍欠 |
| 交互反馈 | 9 / 10 | 无改动 |
| 可访问性 | 8 / 10 | 老账未变（U-116 焦点环仍未量） |
| 性能 | 14 / 15 | 全量 **790 / 38 skip / 0 failures / 157.9s**、动效卷 47 例 judged=4/4、编译告警 0、脚本 **140** OK |

**94 / 100**。分数涨在"一条反复出现的红终于有了正确的名字"，不涨在画面。

### 看图

`/tmp/r75_motion5/notice-banner-strip.png`（本机 27 格胶片）：横幅那一行从第 2 格起逐格变实，
到第 11–12 格才到底 —— 这与 `MOTION_SUMMARY notice-banner=11~12` 一致，
也证明这条量法在能分辨的机器上**确实看得见过程**（本轮不是把红改成不判）。
runner 那一份同样 27 格里只有 2 格在变 —— 那一对差别就是本轮全部的论证。

### 仍未解决

- **BACKLOG 77 路 b**：让判据不吃帧数（今天证人正是它的验收工具）。
- **BACKLOG 101 的③**（R75 新开的一格）：闸门层不查矛盾 ——
  某臂报 `witness-snaps-here` 而同一份日志里证人 `判定=能分辨`，今天只有判据自己守着。
- 浮层搜索框焦点态（U-116）、BACKLOG 95 剩下的位点、BACKLOG 106（真实语料）。
''')

# ---------------------------------------------------------------- 2. 决定台账
append("AGENT_DECISIONS.md", '''

## D-133（R75）：一条时长断言不许站在两帧上；而放宽登记必须**读字段、留 run 号**

**读数**（三遍 runner，同一份判据代码）：`notice-banner` 三遍都是 **2 帧**，
时长分别 32ms / ≥60ms / 36ms ⇒ 红、绿、红；证人三遍都是
`采样≈32ms 可分数段=4 合格=是 判定=拍成跳变（中间态帧数=0）`。
本机同一判据：`notice-banner=11~12 帧、时长 182ms、证人 采样≈4ms 可分数段=37 判定=能分辨`。

**结论**：BACKLOG 104 的①答完（80ms 里抓帧只占 0.4–0.5ms，其余是节拍），
②的答案是**第三种**：那条红既不是产品跳变，也不是含糊的"环境问题"，
而是**判据把一次采样间隔当成了过渡时长**，同时它自己造的证人在同一次运行里说"这台机器看不见淡入"。
两条判据（阳性对照 / 四臂）对同一台机器给相反处置 —— 缺的不是阈值，是**接线**。

**决定**：
1. `.jump` 那一支先问证人（`jumpAdjudication` 纯函数 + 八格真值表 + M392/M393 两刀）。
   赦免只有一个形状：证人**合格且自己 snap**；证人死了或不合格 ⇒ 仍然红。
2. 登记表按实测把 `notice-banner` 的 `must_judge` 从 true 改回 false（地板 4⇒3，带 run 38726667469
   与 38726991211 两个号），另外三臂一条不放。R57 那条 Swift 守卫同步换成
   "放宽必须带理由与 run 号"，并把理由**从数组里读**，不从整块散文里读。
3. 真正的修法仍记在 BACKLOG 77 路 b（让判据不吃帧数）；证人从今天起是它的验收工具。

**判别力**：M392–M397 五刀全 CAUGHT。其中 **M395 第一版逃掉** ——
`bannerBlock.contains("witness-snaps-here")` 被同一臂 note 里的解释文字喂饱（U-130）。
一刀按实"本地无判别力"（删掉真判据里的问话），由 runner 判，不计入。

**代价与边界**：产品 0 文件、帧 0 变化（`CHANGED=0`）、本机 `judged=4/4` 一格没少
⇒ 这次不是把红改成不判：能分辨的机器上仍然判，且 M393 钉着"不许永远放行"、M392 钉着"不许永远不放行"。
runner 上那一臂从此是一条**有名字的未覆盖**（`witness-snaps-here`），
而闸门层还缺一格矛盾检查（BACKLOG 101 的③）。
''')

# ---------------------------------------------------------------- 3. 审计台账
append("AGENT_UI_AUDIT.md", '''

## 第 77 轮 · R75：那条反复出现的红，是判据拿两帧的采样间隔当了时长（结案 104 / U-129、U-130 / D-133）

- 读三遍 CI（38726667469 / 38726991211 / 38730788527）：`notice-banner` 三遍都是 **2 帧**，
  时长 32 / ≥60 / 36ms ⇒ 红、绿、红；证人三遍同一句 `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变`。
  ⇒ **104 的①**：80ms 里抓帧只占 0.4–0.5ms，其余全是节拍（证人现在第一次有资格作证）。
  ⇒ **104 的②**：既不是产品也不是含糊的"环境" —— 是**接线缺失**：
  阳性对照那支问证人，四臂那支不问，于是同一台机器上两条判据互相矛盾。
- 修：`jumpAdjudication`（纯函数 + 八格真值表）把证人接到 `.jump`；
  赦免只有一个形状（证人合格且自己 snap），证人死了/不合格仍然红。
  **不对称是刻意的**：绿是正面证据，不需要借口。
- 登记表按实测放宽一臂（`notice-banner` must_judge true⇒false，地板 4⇒3，带两个 run 号），
  另外三臂不放；R57 那条 Swift 守卫换成"放宽必须带理由与 run 号"。
- **M395 抓到本轮自己写的守卫**：`contains` 被同一臂 note 里的解释文字喂饱
  ⇒ 改成读 `allowed_not_run_reasons` 数组 + 一条"数组非空"的正对照（U-130）。
- 牙：M392–M397 五刀全 CAUGHT；另有一刀（删掉真判据里的问话）**本地无判别力**，由 runner 判，不计入。
- 跨机验证：R74 的 `OVERLAY_HOVER_REFLOW` 在 runner 上给出与本机**逐字相同**的读数（6/1/1、8/7/6）。
- 看图：`/tmp/r75_motion5/notice-banner-strip.png` 本机 27 格里横幅逐格变实（11–12 格到底）
  ⇒ 这条量法在能分辨的机器上确实看得见过程，本轮不是把红改成不判。
- 全量 **790 / 38 skip / 0 failures / 157.9s**、动效卷 **47 例 / 3 skip / 0 failures、judged=4/4**、
  `FRAME_BASELINE_COMPARED=124 CHANGED=0 MISSING=0 ADDED=0`、编译告警 0、脚本 **140** OK。
  **产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`。自评 94。
''')

# ---------------------------------------------------------------- 4. BACKLOG：结案 104、扩 101
before("AGENT_BACKLOG.md", "105. **1× 的捕获通道量不出参照物的圆角",
'''    → **R75 结案（①②都有答案，而②的答案是我没预期到的第三种）**：

    ① 那 80ms 里抓帧只占 **0.4–0.5ms**（`MOTION_FADE_CLOCK_COST 帧数=75 采样≈32ms 抓帧中位=0.5ms`），
    其余全是睡眠节拍 ⇒ R68 那句"面积决定证人采得粗"彻底作废，R72 的 0.004 把采样买到 **32ms**、
    `可分数段=4` ⇒ 证人第一次 `合格=是`。
    ② 红不是产品，也不是含糊的"环境"：**是判据把一次采样间隔当成了过渡时长**。
    三遍 runner 同一份判据代码：`notice-banner` 都是 2 帧，时长 32 / ≥60 / 36ms ⇒ 红、绿、红
    （run 38726667469 / 38726991211 / 38730788527）；
    而证人三遍同一句 `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变（中间态帧数=0）`。
    同一次运行里两条判据对同一台机器给相反处置 —— 阳性对照那支问证人，四臂那支不问。
    修在 R75：`jumpAdjudication` 把证人接到 `.jump`（M392/M393 两刀钉它有牙），
    登记表按实测把这一臂放宽成**有名字的未覆盖** `witness-snaps-here`（带 run 号）。
    剩下的那一半（让判据不吃帧数）仍在 **BACKLOG 77 路 b**，而证人从今天起是它的验收工具。

''')

edit("AGENT_BACKLOG.md",
     '''    要做的：给闸门加一层 `suite_not_run`（理由白名单 + 每次运行都打计数），
    并把 `MOTION_FADE_CLOCK` 的判定并进结论行（例如 `MOTION_RESOLUTION=能分辨/拍成跳变/探针坏了`），
    让人一眼能看出"这一卷的淡入判据今天有没有牙"。''',
     '''    要做的：给闸门加一层 `suite_not_run`（理由白名单 + 每次运行都打计数），
    并把 `MOTION_FADE_CLOCK` 的判定并进结论行（例如 `MOTION_RESOLUTION=能分辨/拍成跳变/探针坏了`），
    让人一眼能看出"这一卷的淡入判据今天有没有牙"。

    → **R75 推进一半**：`notice-banner` 那条缺席从今天起是**臂级**登记的
    （`MOTION_NOT_RUN=witness-snaps-here notice-banner` 进 `MOTION_RESOLVE_SUMMARY` 的 not-run 名单，
    闸门按 REASONLESS / UNREGISTERED / BAD_REASON 三格数它），证人判定也进了每条臂的
    `MOTION_JUMP_WITNESS` 行。剩下两格仍然欠着，其中③是 R75 新认下来的：
    ② `suite_not_run` 那一层（整卷一条的缺席仍然只活在 skip 行里）；
    ③ **闸门不查矛盾** —— 某臂报 `witness-snaps-here`，而同一份日志里证人 `判定=能分辨`，
    今天只有判据自己守着（`jumpAdjudication` 只在证人 snap 时才赦免），闸门层没有这道冗余。
    这一条记在这里而不是新开条目，是因为它和 101 原话是同一件事：**缺席要数得出来，
    而且数的时候得顺手看一眼给它签字的那台机器当天有没有牙**。''')

# ---------------------------------------------------------------- 5. CHANGELOG
before("CHANGELOG.md", '### Tests（R74：浮层淡入那一格判完了',
'''### Tests（R75：那条反复出现的红，是判据拿两帧的采样间隔当了时长 —— 结案 BACKLOG 104 / U-129、U-130 / D-133）
- 读三遍 runner 日志（38726667469 / 38726991211 / 38730788527）：`notice-banner` 三遍都是 **2 帧**，
  时长 32 / ≥60 / 36ms ⇒ 红、绿、红；而淡入时钟证人三遍同一句
  `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变（中间态帧数=0）`
  ⇒ **104 的①**：那 80ms 里抓帧只占 0.4–0.5ms，其余是节拍（R68 那句"面积决定分辨率"作废）；
  **104 的②**：红既不是产品也不是含糊的"环境"，是判据把一次采样间隔当成了过渡时长。
- 修：新增纯函数 `jumpAdjudication` 把证人接到四臂判据的 `.jump` 那一支
  （赦免只有一个形状：证人**合格且自己 snap**；证人死了或不合格仍然红），
  八格真值表 `testTheJumpAdjudicationIsATruthTable`。
  **不对称是刻意的**：绿是正面证据不需要借口，缺席的证据才要先确认这台机器看得看得见。
- 登记表按实测走：`notice-banner` 的 `must_judge` true⇒false（地板 4⇒**3**，带两个 run 号），
  另外三臂一条不放；`notice-banner-dismiss` 的带捕获要求照旧。
- R57 那条 Swift 守卫从"两臂都必须 true"改成**"放宽必须带理由与 run 号"**，
  并且理由从 `allowed_not_run_reasons` **数组里**读 —— M395 实测：整块 `contains`
  会被同一臂 note 里的解释文字喂饱（放宽的守卫被放宽条目自己养活，U-130）。
- 牙：M392–M397 五刀全 CAUGHT（抓到=5 逃掉=0）；另有一刀（删掉真判据里的证人问话）
  **本地无判别力**，由 runner 判，不计入计数。
- 跨机验证：R74 的 `OVERLAY_HOVER_REFLOW` 在 runner 上给出与本机**逐字相同**的读数（6/1/1、8/7/6）
  ⇒ 重排频率不吃机器，R74 那条决定在两台上都成立。
- 看图：本机 27 格胶片里横幅逐格变实（11–12 格到底）⇒ 本轮不是把红改成不判。
- 全量 **790 / 38 skip / 0 failures**、动效卷 **47 例 / 3 skip / judged=4/4**、
  `FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本测试 **140** OK。
  **产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`。

''')

# ---------------------------------------------------------------- 6. STATE
append("AGENT_STATE.md", '''

## R75（第 77 轮账本 / D-133 / 结案 104、推进 101 / U-129、U-130）

- 三遍 runner 日志读完：**104 的①** = 那 80ms 里抓帧只占 0.4–0.5ms，其余是节拍；
  证人现在 `采样≈32ms 可分数段=4 合格=是`。
  **104 的②** = 那条红既不是产品也不是含糊的"环境"，而是 `notice-banner` 三遍都只有 2 帧，
  "变化段时长"就是一次采样间隔 ⇒ 判据在判采样。三遍 32/≥60/36ms ⇒ 红、绿、红。
- 修：`jumpAdjudication` 把证人接到 `.jump` 那一支（原来只有阳性对照问证人），
  八格真值表 + M392/M393 两刀钉住"赦免恰好一个形状"。
- 登记表按实测放宽一臂（地板 4⇒3，带 run 号），R57 那条 Swift 守卫改成
  "放宽必须带理由与 run 号"，且**读数组不读散文** —— M395 第一版逃掉就是被 note 喂饱（U-130）。
- **数字**：全量 **790 / 38 skip / 0 failures / 157.9s**、动效卷 47 例 / 3 skip / `judged=4/4`、
  `FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本 **140** OK、电池 **5/5 CAUGHT**。
  产品 0 文件 ⇒ 不重装（`git log -1 -- Sources` = `dd77480`，本机那颗是 R71 装的）。
- **自评 94 / 100**（曲线见下）。
- **下一步（R76）**：回到产品面 —— 浮层搜索框焦点态（U-116）→ BACKLOG 95 剩下的位点 →
  BACKLOG 106（真实存档上的重排频率）。动效那边欠的是 **77 路 b**（让判据不吃帧数），
  证人已经是它的验收工具。R75 的 CI 要读：`witness-snaps-here` 有没有如约出现在 runner 那一遍。
''')

# ---------------------------------------------------------------- 7. 最终报告
edit("AGENT_FINAL_REPORT.md", "| 视觉台账 | U-31 … U-128（98 条；", "| 视觉台账 | U-31 … U-130（100 条；")
edit("AGENT_FINAL_REPORT.md", "| 决定台账 | D-069 … D-132 |", "| 决定台账 | D-069 … D-133 |")
edit("AGENT_FINAL_REPORT.md", "653 → 757 → 783 → 787 → 788 → **789** 例",
     "653 → 757 → 783 → 787 → 788 → 789 → **790** 例")
edit("AGENT_FINAL_REPORT.md",
     "+ **M100–M391**（阶段二 291 支；**R74 的 M386–M391 六刀全 CAUGHT**，",
     "+ **M100–M397**（阶段二 296 支；**R75 的 M392–M397 五刀全 CAUGHT，其中 M395 第一版逃掉**"
     "—— 它抓到本轮自己刚写的守卫：`contains` 被同一臂 note 里的解释文字喂饱（U-130）；"
     "**R74 的 M386–M391 六刀全 CAUGHT**，")
edit("AGENT_FINAL_REPORT.md",
     "→ **139** passed（R66 新增 `MotionSuiteRedTests` 12 格",
     "→ 139 passed → **140** passed（R75 新增一格 `testWitnessSnapsHereOnTheBannerArmIsRegisteredUncoverage`："
     "登记过的 `witness-snaps-here` 必须**不挡发布但要点名**，少了那行理由就红在 REASONLESS；"
     "同时 `testRegistryIsStrictAgain` 从\"四臂全 true\"改成\"地板=3、别的臂没被连带放宽、"
     "被放宽那一臂的 note 里必须有 run 号\"）（R66 新增 `MotionSuiteRedTests` 12 格")
edit("AGENT_FINAL_REPORT.md",
     "· **R74 一张不加**（零产品改动，124 张 `CHANGED=0 MISSING=0 ADDED=0`；本轮新增的是判据不是画面。",
     "· **R74 / R75 一张不加**（两轮都零产品改动，124 张 `CHANGED=0 MISSING=0 ADDED=0`；"
     "R75 改的是判据与登记表。")
before("AGENT_FINAL_REPORT.md", "U-94 是**一条只报「没跑完」的解释句",
'''U-129 是**一条红了三次、绿了一次的判据，判的是采样器而不是产品**：`notice-banner` 那一臂三遍 runner
  都只拍到 **2 帧**，而"变化段时长"在两帧上就是一次采样间隔 —— 32ms ⇒ 红、≥60ms ⇒ 绿、36ms ⇒ 红
  （run 38726667469 / 38726991211 / 38730788527）。同一次运行里我自己造的淡入时钟说的是
  `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变` —— 它早就在说"这台机器带不动一条 150ms 的淡入"，
  可只有阳性对照那一支问它，四臂那一支没问。⇒ 修的是**接线**，不是阈值（R75 / D-133 / 结案 104）；
U-130 是**放宽的守卫被放宽条目自己的说明文字喂饱**：R75 新写的那半条用
  `bannerBlock.contains("witness-snaps-here")` 检查"放行必须登记理由"，
  而那一臂的 note 里正写着 `MOTION_NOT_RUN=witness-snaps-here`（那是在**解释**这次放宽）
  ⇒ M395 把数组里那一项删掉，守卫照旧绿。与 R55 的 M276、R79 的"守卫命中自己写下的名字"同族：
  **守卫要读字段，不能读散文**（修成读 `allowed_not_run_reasons` 数组 + 一条数组非空的正对照，M395 才 CAUGHT）（R75 / D-133）；
''')

edit("AGENT_FINAL_REPORT.md",
     "自评曲线（**67 轮**，Round 9–74，含 29d 那一轮边界轮；均值 **92.34**，最低 86，最高 96）：",
     "自评曲线（**68 轮**，Round 9–75，含 29d 那一轮边界轮；均值见本轮读数，最低 86，最高 96）：")


def main():
    problems = []
    for path, old, new in EDITS:
        text = read(path)
        found = text.count(old)
        if found != 1:
            problems.append("EDIT 命中 %d：%s :: %s" % (found, path, old[:60]))
            continue
        write(path, text.replace(old, new))
        print("EDIT   %-30s %s" % (path, old[:52].replace("\n", " ")))
    for path, anchor, text in BEFORES:
        source = read(path)
        if source.count(anchor) != 1:
            problems.append("BEFORE 命中 %d：%s :: %s" % (source.count(anchor), path, anchor[:60]))
            continue
        write(path, source.replace(anchor, text + anchor, 1))
        print("BEFORE %-30s %s" % (path, anchor[:52].replace("\n", " ")))
    for path, text in APPENDS:
        write(path, read(path).rstrip("\n") + "\n" + text)
        print("APPEND %-30s +%d 行" % (path, text.count("\n")))
    if problems:
        print("\n=== 跳过（命中数不对）===")
        for line in problems:
            print("  " + line)
        return 1
    print("\n全部命中恰好一次。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
