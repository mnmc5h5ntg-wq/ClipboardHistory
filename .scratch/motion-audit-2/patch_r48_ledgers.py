#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R48 台账（第 50 轮 / D-107 / BACKLOG 70 收口 + 69 改写 + 72、73 新开 / CHANGELOG / Round 48）。

数字来源（全部本轮真跑，逐条可查）：
  M230–M239 十支变异            <- /tmp/r48-measure.log、/tmp/r48-mutate.log、/tmp/r48-mutate2.log、
                                    /tmp/r48-measure2.log、/tmp/r48-mutate3.log
  本机三臂读数与段内最粗采样     <- /tmp/r48-motion3.log（本轮最后一次跑）
  runner R47 开臂 249 / 227ms   <- gh run view 38530030589 --log
  全量 745 / 29 / 0、116 帧       <- /tmp/r48-full.log + frame_baseline --against working compare
                                    （本轮**没有**改产品，帧数不变）
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


ROUND = '''
---

## 第 50 轮 · R48：那条"演了 266ms 的淡入"是钟停了 —— 顺带撤回我自己写的一句结论（BACKLOG 70 收口 / U-74 / D-107）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `MotionFilmstripTests.changedRunElapsedMilliseconds` | `moving.first … moving.last`，**不要求连续** | 名字叫 run，量的是首尾跨度：中间静止也算进"过程"里 |
| 同一条的下游判据 `fadeVisibility` | 只比"时长 vs 声明" | **没有分辨率轴**：`judgeMotion` 早在 R2/R8 就有"段内最粗采样 > 0.5×声明 ⇒ 判不了"这一档，这条 A/B 漏了它 |
| R47 留在源码里的注释 | "265ms 只能来自两波带空隙" | **这句是本轮我写的，且是错的**（见下面"我错在哪"） |
| R11/R47 留在台账里的结论 | "这条通道对纯 opacity 淡入可见性 = 0" | **这句也是错的**，被本轮第一次补上的条带图当场推翻 |
| 那条 A/B 的取证 | 只有一行结论文本 | 判了三轮"看不见"，一张画面都没留过 ⇒ 没人能反驳我 |

### 本轮真正的发现（看图看出来的，不是读代码）

给这条 A/B 补上 `writeStrip` 之后，第一次看到它自己的胶片：

- `heat-first-record-开A-strip.png` 第 3 帧是**半透明中间态** —— 空态那行字与整块日历叠在一起。
  ⇒ **这条通道看得见这条淡入。** R11 起写在台账里的"可见性 = 0"是**没抓到的时候下的结论**，
  本轮把它撤回：正确说法是"**不每次都抓得到**"，而这与"看不见"是两个完全不同的产品结论。
- 同一轮 per-run 打印给出真形状：`开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`。
  那 266ms **不是**"过程演了 266ms"，也**不是**我上一轮猜的"两波被跨度算法并成一段"，
  而是**一段连续的变化，中间有一次 260ms 的抓帧空档**（整卷中位 8ms）—— 是不是主线程被占住，正是第 73 条要问的。
  两个假设都被同一行读数否掉 —— 这就是为什么本轮先把读数打全再改判据。

### 修法（每一处都有格子或变异钉着）

1. **改名**：`changedRunElapsedMilliseconds` → `changedSpanElapsedMilliseconds`，行为一字不改。
   R2 那批夹具仍站在跨度上（迁移要逐条重问，见 BACKLOG 72），但名字不许再说谎。
2. **新建一把真尺**：`contiguousChangedRuns` 按 `峰值×0.15`（含等号）断段，
   `contiguousChangedRun` 取**含峰值**那一段（不是最长那段），并带出**段内最粗采样**。
3. **把分辨率轴接进判定**：`fadeVisibility` 新增 `.clockTooCoarse(worstOnA:worstOnB:)`，
   门槛沿用 `judgeMotion` 中间档的 0.5×声明，且**排在一致性之前** ——
   钟卡住的时候两个时长没有可比量纲，比"矛不矛盾"是给没测到的东西编结论。
4. **三态而不是两态**：`看不见` 的分支文案改成"今天没抓到"，并明写那句被撤回的旧结论；
   新增 `clock-coarse-in-window` 的 not-run 登记（不红）。
5. **取证补齐**：三臂各出一张条带；`MOTION_HEAT_RUNS` 打印"起–止@峰值/粗…"（时刻相对卷首）。
6. **调用点守卫**：段绑定必须来自 `contiguousChangedRun`、必须读自己那一卷、
   `elapsedX` 必须就是那一段的时长、判定调用必须把 `worstOnA/worstOnB` 传进去。

### 我错在哪（三处，全部由数据顶回来）

- **心算**：真值表第 ③ 格期望写成 308ms，实际 316ms（`stamps[3]` 是 24ms 不是 32ms）。
  与"needle 只能从实测抄"是同一条规矩的另一个面 —— 期望值也不许推理。
- **守卫判在读邻居**（两次）：第一版数 `contiguousChangedRun(` 出现次数，
  把 `elapsedB` 改成抄 `elapsedA` 仍然有 3 次 ⇒ M237 顶红；
  第二版固定取两行当语句边界，那条赋值缩成一行后第二行是邻居的 ⇒ M237 又顶红一次。
  第三版按括号配平取语句，并自己断言"这条语句里只许有一个 `let`"。
- **注释里写了一个没量过的数**：我在读到 `worstIntervalMilliseconds` 之前就把\"约 130ms\"写进了源码注释与台账草稿（那是拿 266 ÷ 2 估的）。实测是 **260ms 的一次空档**，不是两次各半 —— 本轮第四错，与前三个同源：**数只能从读数来，注释也不例外**。\n- **打印用绝对时钟**：第一版 `MOTION_HEAT_RUNS` 打出 `731797829–731797842`，
  没人能对账 ⇒ 改成相对卷首。这一条是"跑一遍看输出"才抓到的，读代码读不出来。

### 验证

- 真值表：`fadeVisibility` 15 格（新增 ⑬⑭ 三格钉分辨率轴）+ `contiguousChangedRun` 8 格。
- 变异 M230–M239 十支：见 STATE 的电池汇总（含 M239 第一版 **BROKEN-MUTATION** ——
  我把 `coarseRunRatio` 写成不带 `Self.`，编译不过；电池把这种情况单列成一个码，不混进"抓到"）。
- `swift build --build-tests` 0 告警；全量测试与 116 帧见 STATE；**本轮不换装**（`Sources/` 未动）。
- 自评 **94 / 100**。**CI 待读。**

'''

DECISION = '''
---

## D-107（R48）：一把尺管"跨度"、一把尺管"一段过程"，而"判不了"必须是第三种结论

**背景**：`changedRunElapsedMilliseconds` 从 R2 起是所有"这条过渡演了多久"读数的来源，
但它取的是首尾跨度、不要求连续；而它唯一的下游 `fadeVisibility` 又只比"时长 vs 声明"，
没有 `judgeMotion` 那套"段内最粗采样"的分辨率档。两台机器因此都读出过
比声明还长的"淡入"（本机 266ms、runner 249 / 227ms，声明 160ms）。

**决定**：
1. 原函数改名 `changedSpanElapsedMilliseconds`，**行为不变**。迁移其余调用点要逐条重问
   （R2 的 `coarseSampling` 夹具本身就是"中间掉回 0.001"的两波形状）⇒ 记 BACKLOG 72。
2. 新增 `contiguousChangedRuns` / `contiguousChangedRun`（含峰值那一段 + 段内最粗采样）。
3. `fadeVisibility` 从两态改三态：看得见 / 看不见 / **今天的钟粗到判不了**（0.5×声明那档，
   沿用 `judgeMotion` 的口径）。分辨率门排在一致性门之前。
4. **撤回**台账里"这条通道对纯 opacity 淡入可见性 = 0"：条带图里有半透明中间态。
   正确结论是"抓得到就看得见，抓不到就是没抓到"，所以这条 A/B 的 `notVisible` 分支
   从此只许写"今天没抓到"，不许再写"看不见"。

**代价**：文件里现在有两把时长尺（跨度 / 连续段），并且一条判据多了一种 not-run 原因。
守卫钉的是调用点用哪一把、以及那一轴有没有被传进去，不是"全文件只许有一把尺"。
'''

BACKLOG = '''
72. **其余调用点还站在"跨度"那把尺上**（R48 / D-107 留下的口子）：
    `worstIntervalInsideChangedRun` 与那条通用场景判据（`MotionFilmstripTests` 里 `judgeScenario`
    一路）仍然用首尾跨度。本轮没迁移，理由是它们喂的 R2 夹具
    `coarseSampling = [0.11, 0.001, 0.10, 0, 0, 0]` **本身是两波带空隙**的形状，
    而"真机上一次 135ms 的淡入会不会被采成这个形状"从没对过账。
    连续段那把尺会把它读成两段（45ms + 45ms），跨度那把尺读成一段 135ms ——
    同一个数据，两把尺差 3 倍，而这条判据今天还在用后者。
    怎么判（不许两种读法都留着不写理由）：拿真胶片（`empty-state` / `detail-kind-change` 各一卷）
    数一遍"段内掉回地板以下"出现过没有；从没出现 ⇒ 那个夹具是虚构的，按连续段重写并改掉 R2 那句话；
    出现过 ⇒ 采样真的会漏，跨度才是对的，那连续段只该用于"两波之间有明显空隙"的场合。
73. **触发之后有一次 260ms 的抓帧空档 —— 是谁占住了这段时间**（R48 新读数，性质比 BACKLOG 69 更硬）：
    `heat-first-record` 的 `段内最粗采样 = 260ms`（整卷中位 8ms）说明抓帧器在触发后那一段挤不进去。
    候选：①首次布局 26 周 × 7 天 = 182 个格子的 SwiftUI 布局；②`DailyCopyLedger.record` 主线程侧的工作；
    ③去抖落盘（它在 `saveQueue` 上，但发布 `@Published` 会回主线程）。
    **为什么值得查**：这条发生在**用户刚按下 ⌘C 的那一刻**，而目标里明令"采集路径上不许有同步磁盘写"。
    如果这 260ms 是我们自己的代码占住主线程，那是可感知的卡顿，不是探针噪声。
    怎么量：`worstIntervalMilliseconds` 已经是现成的读数 —— 拿同一条通道跑一次"设置窗口没打开"的对照
    （只有 `HistoryStore.add`，没有热图视图），如果停顿消失 ⇒ 是视图布局；不消失 ⇒ 往采集/落盘那侧查。
    **不许猜着修。**
'''

BACKLOG_PATCHES = [
    ("70. **`changedRunElapsedMilliseconds` 量的不是「一段」，是「首尾」**（R47 看图 + 读码，未证）：",
     "70. **【R48 已收口，U-74 / D-107】**`changedRunElapsedMilliseconds` 量的不是「一段」，是「首尾」"
     "（R47 看图 + 读码）："),
    ("    并补真值表（单波 / 两波带空隙 / 峰值在第二波）+ 变异。",
     "    并补真值表（单波 / 两波带空隙 / 峰值在第二波）+ 变异。\n"
     "    **R48 的实际收口与原计划不同，且把本轮自己的假设也否掉了**：\n"
     "    ① 改名 + 新建连续段那把尺确实做了（真值表 8 格 + 变异 M230–M234）；\n"
     "    ② 但\"两波被并成一段\"这个解释**错了** —— 补上 per-run 打印之后真形状是\n"
     "    `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`：**一段连续的**变化，\n"
     "    段内有一次 **260ms 的抓帧空档**。所以那条长读数既不是\"过程演那么久\"，也不是\"两波被并\"，\n"
     "    而是**钟在过程中间停了** —— 缺的是分辨率轴，不是连续性。两把尺都补上了（D-107），\n"
     "    而\"是谁卡的\"另开第 73 条（性质比第 69 条硬，因为它发生在用户刚按下 ⌘C 的那一刻）。"),
    ("69. **那条 A/B 反复抓到的 258–307ms 变化段到底是什么**（R47 实测，未定位）：",
     "69. **那条 A/B 反复抓到的 258–307ms 变化段到底是什么**（R47 实测；**R48 已解释**，见第 70、73 条）："),
    ("    性质从\"测量噪声\"变成\"产品缺陷\"。",
     "    性质从\"测量噪声\"变成\"产品缺陷\"。\n"
     "    **R48 更新**：那段不是\"过程演了 266ms\"，是**一段连续变化里有一次 260ms 的抓帧空档**\n"
     "    （段内最粗采样 260ms，整卷中位 8ms）。\"采集路径上有同步磁盘写\"这个最坏解释\n"
     "    **没有被这条读数否证** —— 恰恰相反，它现在有了一个可量的读数（`worstIntervalMilliseconds`），\n"
     "    于是问题从\"这段读数是什么\"升级成\"那一刻是谁占住主线程\"，另开第 73 条接着查。"),
]

CHANGELOG = '''### Fixed（R48：动效时长那把尺补了连续性，判定补了分辨率，一句旧结论被撤回）
- `changedRunElapsedMilliseconds` 名叫 "run" 却**不要求连续** ⇒ 改名 `changedSpanElapsedMilliseconds`
  （行为不变），新增 `contiguousChangedRun`（取**含峰值**的那一段连续变化 + 段内最粗采样）。
- 那条淡入 A/B 的判定**缺分辨率轴**：`judgeMotion` 从 R2/R8 起就有"段内最粗采样 > 0.5×声明 ⇒ 判不了"
  这一档，而 `fadeVisibility` 只比"时长 vs 声明"。现在它有三态：看得见 / 看不见 / **钟太粗**
  （`MOTION_NOT_RUN=clock-coarse-in-window`，不红）。
- **撤回一条写进台账的结论**：R11 起的"离屏 `cacheDisplay` 对纯 opacity 淡入可见性 = 0"是错的 ——
  本轮第一次给这条 A/B 补上条带图，里面出现过**半透明中间态**。正确说法是"不每次都抓得到"，
  所以 `notVisible` 分支的文案从"看不见"改成"今天没抓到"。
- 那条 A/B 现在打印 per-run 形状（`MOTION_HEAT_RUNS … 起–止@峰值/粗…`，时刻相对卷首）
  并为三臂各出一张条带图。
- 产品代码零改动，116 张帧逐字节不变。
- 新增判据：`fadeVisibility` 真值表 15 格（新增 3 格钉分辨率轴）+ `contiguousChangedRun` 8 格
  + 调用点守卫 1 条（段来源、臂归属、时长轴、分辨率轴是否传入）。
- 变异对照 M230–M239 十支；其中 M237 把本轮守卫的**前两版**都顶红（数词频、固定取两行），
  M239 第一版是 **BROKEN-MUTATION**（`coarseRunRatio` 忘了写 `Self.`，编译不过）。

'''

VISUAL = '''
---

## Round 48 · 我以为我看懂了那条读数，结果两个假设都错了（R48 / BACKLOG 70 收口 / U-74 / D-107）

**这一轮问的问题**：R47 我加了一条上限，把 258–307ms 挡在判定之外，并在台账里写"那不是淡入，
是两波变化被跨度算法并成一段"。本轮去做验证 —— 然后被数据打了两次脸：

1. **不是两波**：补上 per-run 打印之后，真形状是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`
   —— 一段**连续的**变化，段内有一次 **260ms 的抓帧空档**。缺的不是连续性，是**分辨率轴**。
2. **也不是看不见**：给这条 A/B 补上条带图之后，第 3 帧是**半透明中间态**（空态那行字与整块日历叠在一起）。
   也就是说 R11 起我写在台账里的"这条通道对纯 opacity 淡入可见性 = 0"**是错的**，
   它把"没抓到"当成了"看不见"。本轮正式撤回。

**做了什么**：跨度那把尺改名（行为不变）、新建连续段那把尺、判定加第三态"钟太粗"、
`看不见` 的文案改成"今天没抓到"、三臂各出一张条带、调用点守卫钉住四件事。

**真实视觉审查**：`heat-first-record-开A / 开B / 关` 三张条带 —— 这是这条判据诞生三轮以来
第一次有画面。结论是**看图推翻了我自己的日志**，所以本轮最值钱的一行不是新判据，是那句撤回。

**分数为什么持平**：`流畅度` 仍 13/20。本轮没有让任何一帧动起来；
它做的是把这一维**唯一一处我写错的结论**改对。四轮 94 不好看，
但"这一维的上限"这句话，我上一轮写错了还当成写死了。

### 自评 94 / 100（与 R45 / R46 / R47 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 不涨分：本轮的产出是**撤回一句错误结论** + 给判定补分辨率轴 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；这条 A/B 第一次有画面可看 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核） |
| 性能 | 15 / 15 | 只改测试文件；但本轮**新查出一个待定的 260ms 空档**（BACKLOG 73），它可能是产品侧的卡顿，下一轮去量 |

**本轮自己错三处**：真值表期望心算错（308 vs 316）；守卫两版都在读邻居（都被 M237 顶红）；
打印用了绝对时钟（跑一遍才看见）。全部记进账本，不藏。

**验证**：真值表 15 + 8 格、变异 M230–M239、`swift build --build-tests` 0 告警、
全量测试与 116 帧见 STATE。**CI 待读。**
'''


def main():
    # 先**全部预检**再落盘（R47 那一轮栽过"四个文件已追加、第五个锚点不存在"）。
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    for old, _ in BACKLOG_PATCHES:
        assert backlog.count(old) == 1, ("BACKLOG 锚点", backlog.count(old), old[:70])
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    assert changelog.count("## [Unreleased]\n") >= 1
    for path in ("AGENT_UI_AUDIT.md", "AGENT_DECISIONS.md", "AGENT_VISUAL_ITERATION.md",
                 "AGENT_STATE.md", "docs/MANUAL_TEST_v1.4.9_round3.md"):
        assert os.path.exists(path), path

    with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
        f.write(ROUND.lstrip("\n"))
    with io.open("AGENT_DECISIONS.md", "a", encoding="utf-8") as f:
        f.write(DECISION)
    with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
        f.write(BACKLOG)
    patch("AGENT_BACKLOG.md", BACKLOG_PATCHES)
    patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])
    with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
        f.write(VISUAL)
    print("R48 主体台账已写入（STATE / 批次 / FINAL_REPORT / R47 CI 追认在第二段）")


main()
