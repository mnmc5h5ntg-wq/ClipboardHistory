#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R46 的台账写入。锚点全部 assert；写不进去就报错，不静默。

数字来源（不是记忆）：
  101 条脚本自测 OK              <- python3 -m unittest discover -s scripts/tests
  本机真日志 2 条红              <- python3 scripts/motion_floor_gate.py /tmp/motion-local.log
  R45 CI：742/36/0、MOTION_FLOOR_OK=3/4、闸门 NOT_RUN=24  <- gh run view 38519597818 --log
  R44 CI：judged=3/4 not-run=notice-banner-dismiss、NOT_RUN=8 <- gh run view 38514753036 --log
"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


ROUND = '''
---

## 第 48 轮 · R46：地板原来只问"判够 2 条没有"，现在问"掉了谁、为什么"（U-72 / D-105）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `ci.yml:207-227`（旧）| `if [ "$judged" -lt 2 ]; then exit 1` | 地板是一个**写死的常数**。R42 的 4/4 与 R44 的 3/4 都绿 |
| run 38514753036（R44）| `judged=3/4 not-run=notice-banner-dismiss` | **一臂掉了，这一步仍然绿** —— 我是把三次 run 的日志拉下来人肉对比才发现的 |
| `ci.yml:190`（旧）| `grep -E "MOTION_(…NOT_RUN)" /tmp/motion.log \\| head -24` | 理由行排在一大堆读数之后被 `head -24` 挤出控制台 ⇒ 那次 not-run 在日志上**查不到为什么** |

⇒ 这一轮没有产品改动，改的是"CI 能不能替我记住自己看不见什么"。

### 修法：判据搬进 `scripts/motion_floor_gate.py`，盲区搬进 `scripts/motion_floor_expectations.json`

规则：`NO_RESOLVE` / `MISSING_KEY` / `UNLISTED_SCENARIO` / `UNREGISTERED` / `REASONLESS` /
`BAD_REASON` / `UNDERCOVERED` / `STALE`，每一条都配一支"关掉它就有用例过不掉"的变异（M216–M222）。
两条是**方向**上的：

- **旧版那张免检牌收掉了**：跑完了（`Executed N>0`）却没有 `MOTION_RESOLVE_SUMMARY` ⇒ 现在红。
  旧版在这里 `exit 0`，理由是"旧版判据没有这一行" —— 那已经是历史，本仓库每条判据都打这一行，
  缺了就是坏了。
- **不许反向恒红**：会随采样漂的那一臂（`notice-banner-dismiss`：R42/R42b/R43 判到、
  R44/R45 没判到）登记成 `must_judge=false`，且**不**带 `stale_if_judged` ⇒ 判到不红、判不到也不红。
  给它 `stale_if_judged=true` 就变成"判不到红、判到也红"，恒红的守卫最后会被人删掉
  （R39 那一族演过三次）。这一格由 `testFlakyArmBeingJudgedIsNotRed` +
  `testStaleFlagIsWhatMakesJudgedRed` 钉住：**红不红取决于登记，不取决于读数**。

**明确不判帧数。** `MOTION_SUMMARY <arm>=<帧数>` 那个数由采样相位决定 ——
R2 实测同一份代码本机跑过 `2/3/2`（原始记录在 `changedRunElapsedMilliseconds` 开头）。
这道闸门只判**形状**：谁在、谁不在、不在的理由登记过没有。

### 登记表里的理由从哪来：自己产一份真日志

runner 上 R44 那次的理由我**查不到**（被 `head -24` 截了）。与其猜一条登记进去，
不如跑一遍真的：`CLIPBOARD_HISTORY_UI_MOTION=1 swift test --filter MotionFilmstripTests`
⇒ `/tmp/motion-local.log`，逐字读数：

```
MOTION_NOT_RUN=premise-not-visible notice-banner：首尾两帧逐像素相同 …
MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：事件那一段最粗 101ms 一帧、整段过渡只有 120ms
MOTION_RESOLVE_SUMMARY judged=2/4 not-run=notice-banner,notice-banner-dismiss
```

这份日志同时是**正对照夹具**（`scripts/tests/fixtures/r46_motion_local.log`）：
新闸门跑它必须红，而且红在该红的两处 —— 真日志的夹具比合成日志值钱，因为它不由我编。

```
MOTION_FLOOR_FACTS judged=2/4 executed=24 not-run=notice-banner,notice-banner-dismiss …
MOTION_FLOOR_BAD_REASON notice-banner 的理由是 premise-not-visible，而登记过的是 无 ⇒ …
MOTION_FLOOR_UNDERCOVERED judged=2/4 低于地板 3（= 清单里 must_judge 的臂数）⇒ …
MOTION_FLOOR_REDS=2   exit=1
```

本机 notice-banner 判不到（首尾相同），runner 判得到 ⇒ **登记表说的是 runner 的前提**，
这句话写在表里，不留在脑子里（"判据依赖的环境前提要写进判据本身"）。

### 顺手修掉的一处"报告看不见"

`Motion filmstrip` 那一步现在把 `MOTION_NOT_RUN=` 的行**单独打、不截断**，其余读数仍走 `head -24`。
闸门读的是文件，本来不受影响；这一步负责的是让人**看见**。

### 本轮查出、没在本轮修的

- **`NOT_RUN` 的数量在漂**：R44 的捕获闸门 `NOT_RUN=8`，R45 报 `NOT_RUN=24`，
  而两次的 skip 用例数都是 36。BACKLOG 57 那一族（未解释的漂移），本轮没动它 ——
  新闸门管的是动效那一族，不是捕获那一族。两个数已记进 BACKLOG 57。
- **热图淡入那条 A/B 用错了轴**：跑真日志时 `testHeatmapFadeIsNotVisibleToThisRuler` 本机报红，
  读数 `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— **两臂峰值完全相同**，只有帧数不同，
  而帧数正是 R2 已经宣布"会随采样相位漂"的那个量。
  ⇒ 这条判据在拿一个自己宣布过不可靠的量做判据，**红的是尺，不是产品**。
  已开 BACKLOG 68，下一轮（R47）单独做：A/B 换成时长轴。

### 验证

脚本自测 83 → **101** 全绿（新增 `test_motion_floor_gate` 18 条，含真日志正对照）；
变异 **M216–M222** 七支全 CAUGHT、`未被抓到=0 红得不对=0 还原不干净=0`；
Swift 侧**零改动**（`git status` 里没有 `.swift` 文件）⇒ R45 那一遍的 742/29/0 与 116 帧仍然有效；
本轮**不换装**，理由记账：没有任何"只有装上新包才看得见"的东西。
R45 的 CI 已逐步骤读过：15 步全 ✓、`Executed 742 / 36 skipped / 0 failures`、闸门 `红=0`、
`MOTION_FLOOR_OK=3/4`（旧闸门，正是要被换掉的那个）、`SMOKE_OK=1`。
**R46 的 CI 待读** —— 新闸门第一次在 runner 上跑：若 `notice-banner-dismiss` 的理由与本机不同，
它会红在 `BAD_REASON` 并把真理由打印出来（那是一次可诊断的红，改一行收口）。
'''

DECISION = '''

---

### D-105 · R46：一道守"别的判据有没有真跑到"的闸门，自己必须能被证伪

- **背景**：`Motion coverage floor` 从 R7 起就是 `judged<2 ⇒ 红`。R45 读 CI 时发现
  R44 那次 `judged` 从 4/4 退到 3/4（`notice-banner-dismiss` not-run），整步仍然绿。
  "CI 绿"与"读数没退"是两件事，而后者以前没有任何东西在守。
- **决定**：判据从 shell 搬进 `scripts/motion_floor_gate.py`，盲区搬进
  `scripts/motion_floor_expectations.json`。八条规则各配一支变异（M216–M222）。
- **决定 2（这条是本体）**：**红不红取决于登记，不取决于读数。**
  会随采样漂的臂登记成 `must_judge=false` 且不带 `stale_if_judged` ⇒ 判到/判不到都不红；
  登记成"永远判不了"的臂判到了 ⇒ 红（清单不许慢慢变成免检牌堆）。
  两种极端都有先例：把漂的臂要求成必须判到 ⇒ 恒红（R39 那一族，守卫最后被人删）；
  把清单写成"允许一切" ⇒ 免检牌（R44 之前那句 `no-resolve-line ⇒ exit 0` 就是这个形状）。
- **决定 3**：登记的**理由**必须来自真跑一遍产出的日志（本机 `/tmp/motion-local.log`），
  不许从"它大概是 clock 太粗吧"推出来。理由错了闸门会红在 `BAD_REASON` 并把真理由打出来 ——
  可诊断的红，一次改一行就收口。
- **决定 4**：登记表是 **runner 的前提表**，不是本机的。本机 notice-banner 判不到、runner 判得到，
  两边读数不同是事实；写在表里，是为了下一台机器来的时候不致于把它当普适真理。
- **代价**：CI 多一个 python 文件 + 一份 JSON；判据 18 条（含真日志正对照）；
  产品零改动、帧零变化、本轮**不换装**。
- **谁守着**：`scripts/tests/test_motion_floor_gate.py`（18 条）+
  `test_ci_report_selftest` 里 `motion_floor` 的六个形状（够 / 漂了但登记过 / 漂了没理由 /
  地板不够 / 没跑完 / 没有结论行）—— 最后两格把"旧版的两个 exit 0"分别钉成"一个仍 0、一个已 1"。
- **仍未收口的部分**：① 新闸门在 runner 上的第一次结果待读（可能红在 `BAD_REASON`）；
  ② 捕获那一族的 `NOT_RUN` 也在漂（R44=8 / R45=24），这道闸门管不到它（BACKLOG 57）；
  ③ 热图淡入那条 A/B 用帧数当轴（BACKLOG 68，R47 的靶）。
'''

BACKLOG = '''68. **热图淡入那条 A/B 用错了轴：它判"看得见"用的是帧数，而帧数会随采样相位漂**（R46 跑真日志时撞出来的）：
    `MotionFilmstripTests.testHeatmapFadeIsNotVisibleToThisRuler` 的放行条件是
    `onSpan == offSpan && |peak(on) - peak(off)| < 0.02`。本机真跑一遍的读数是
    `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— **两臂峰值完全相同**，只有帧数不同，
    于是它走进 `XCTFail("两臂读数不同 ⇒ 这把尺现在看得见这条淡入")` 那一支。
    而"帧数会漂"正是 R2 已经证伪过的事（同一份代码本机跑过 2/3/2，
    原始记录写在 `changedRunElapsedMilliseconds` 开头）。
    ⇒ 这条判据在拿一个自己宣布过不可靠的量做判据，红的是尺，不是产品。
    下一轮（R47）：A/B 换成**时长轴**（两臂 `changedRunElapsedMilliseconds` 之差），
    峰值差作第二证据；并把"只漂帧数不许算看得见"写成一条真值表 + 一支变异。
'''

CHANGELOG = '''### Added（R46 · 动效覆盖地板会报"掉了谁、为什么"了）

- 新增 `scripts/motion_floor_gate.py` + `scripts/motion_floor_expectations.json`，
  `Motion coverage floor` 那一步从一段 shell（只问 `judged<2`）换成读登记表的脚本。
  来历：R44 那次 `judged=4/4` 退到 `3/4`（`notice-banner-dismiss` not-run）**整步仍然绿**，
  而我是人肉对比三次 run 的日志才发现的。
- 八条规则：没有结论行 / 少一臂的键 / 多一臂 / 清单外的盲区 / not-run 没理由 /
  理由没登记过 / 判不够地板 / 登记成"永远判不了"却判到了。
  每条一支变异（M216–M222 全 CAUGHT），因为这道闸门是**判据的判据**。
- 两条方向上的取舍写进 D-105：**红不红取决于登记，不取决于读数** ——
  会随采样漂的臂判到不红、判不到也不红（否则恒红，守卫最后被人删）；
  而"跑完了却没有结论行"从旧版的 `exit 0`（免检牌）改成红。
- **不判帧数**：`MOTION_SUMMARY <arm>=<帧数>` 由采样相位决定（R2 实测 2/3/2）。
- 登记表里的理由来自**本机真跑一遍**产出的日志，并把它原样收成正对照夹具
  （`scripts/tests/fixtures/r46_motion_local.log`）：闸门跑这份真日志必须红，
  且红的正是 `BAD_REASON` + `UNDERCOVERED` 两格。
- `Motion filmstrip` 那一步把 `MOTION_NOT_RUN=` 单独打、不截断
  （`head -24` 正是 R44 那次"not-run 查不到为什么"的成因）。
- 脚本自测 83 → **101** 全绿。Swift 侧零改动 ⇒ 742/29/0 与 116 帧不变；本轮**不换装**。
- 新开 BACKLOG 68：跑真日志时撞见热图淡入那条 A/B **用帧数当判据**，
  而两臂峰值完全相同（0.226 / 0.226）⇒ 红的是尺，不是产品。R47 的靶。

'''

VISUAL = '''
---

## Round 46 · 地板学会报"掉了谁、为什么"；顺带撞出一条判据在用不可靠的轴（R46 / U-72 / D-105）

**这一轮问的问题**：R45 读 CI 时我发现 run 38514753036 的动效覆盖从 `4/4` 退到 `3/4`
而整步仍然绿 —— 那道从 R7 就在的闸门只问"判够 2 条没有"。
"CI 绿"与"读数没退"是两件事，后者以前没有任何东西在守。

**做了什么**：把判据搬进 `scripts/motion_floor_gate.py`，把盲区搬进一份登记表，
八条规则各配一支变异。设计上的主点是**红不红取决于登记，不取决于读数**：
会随采样漂的那一臂判到不红、判不到也不红（否则恒红 → 守卫被删，R39 那一族），
而"跑完却没有结论行"从 `exit 0` 改成红（那是旧版留下的免检牌）。
登记表里的理由不是猜的：本机真跑一遍 `MotionFilmstripTests` 产出 `/tmp/motion-local.log`，
把它原样收成正对照夹具 —— 真日志的夹具比合成日志值钱，因为它不由我编。

**真实视觉审查**：零产品改动 ⇒ 没有新画面，而且不该有（`git status` 里没有 `.swift` 文件）。
本轮明确**跳过换装**并写下理由：没有任何"只有装上新包才看得见"的东西。

**分数为什么持平**：这一轮抬的是"CI 说的话可不可信"，它不是这七维里的任何一维。
把它记成 `动效细节 +1` 就是给曲线注水 —— 连续两轮 94 比一轮虚高好看。

### 自评 94 / 100（与 R45 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 未动时序，也没新增像素证据。**本轮反而查出这条维度的尺有一处用错了轴**（BACKLOG 68） |
| 层次与材质 | 15 / 15 | 沿用 R45；116 帧不变 |
| 动效细节 | 14 / 15 | 沿用；本轮抬的是判据的判据，不是画面 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只有 CI 侧脚本；产品零成本 |

**验证**：脚本自测 83 → 101 全绿、变异 M216–M222 七支全 CAUGHT、
Swift 侧零改动（742/29/0 与 116 帧沿用 R45）。**CI 待读**。
'''

STATE = '''

---

## R46 · 地板会报"掉了谁、为什么"了（第 48 轮 / U-72 / D-105）

- **本轮改的是 CI，产品零改动**：`Motion coverage floor` 从"只问 `judged<2`"换成
  `scripts/motion_floor_gate.py` + 一份登记表。来历是 R45 读 CI 时发现 R44 那次
  `4/4 → 3/4`（`notice-banner-dismiss` not-run）**整步仍然绿**，而理由行被 `head -24` 挤出了日志。
- **设计主点**：**红不红取决于登记，不取决于读数**。
  会随采样漂的臂判到不红、判不到也不红（否则恒红 → 守卫被删）；
  "跑完却没有结论行"从 `exit 0` 改成红（旧版那张免检牌）。
- **理由不是猜的**：本机真跑一遍 `MotionFilmstripTests` 产出 `/tmp/motion-local.log`，
  逐字收成正对照夹具 ⇒ 新闸门跑真日志必须红，且红在 `BAD_REASON` + `UNDERCOVERED` 两格。
- **不判帧数**：`MOTION_SUMMARY <arm>=<帧数>` 由采样相位决定（R2 实测 2/3/2）。
- **撞出一条新的（BACKLOG 68，R47 的靶）**：`testHeatmapFadeIsNotVisibleToThisRuler`
  本机报红，读数 `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— 两臂峰值完全相同，
  只有帧数不同 ⇒ 它在拿自己宣布过不可靠的量做判据。**红的是尺，不是产品。**
- **验证**：脚本自测 83 → **101** 全绿、变异 M216–M222 七支全 CAUGHT、
  Swift 侧零改动（742/29/0 与 116 帧沿用 R45）、**本轮不换装**（理由记账）。
  R45 的 CI 已逐步骤读过：15 步全 ✓、`Executed 742 / 36 skipped / 0 failures`、`SMOKE_OK=1`。
  自评 **94 / 100**（与 R45 持平；曲线不涨是因为这轮抬的不是画面）。**R46 的 CI 待读。**
- **下一步（R47）**：① BACKLOG 68（热图淡入那条 A/B 换成时长轴）—— 它是 `流畅度` 那一维
  唯一一条"看起来能判、其实判的是采样"的判据；② 若新闸门在 runner 上红在 `BAD_REASON`，
  先把真理由抄进登记表再往下走；③ BACKLOG 64 的后半（分支门控）仍在。
'''


def main():
    with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
        f.write(ROUND.lstrip("\n"))
    with io.open("AGENT_DECISIONS.md", "a", encoding="utf-8") as f:
        f.write(DECISION.lstrip("\n"))
    with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
        f.write(BACKLOG)
    patch("AGENT_BACKLOG.md", [
        ("66. **动效覆盖地板在 runner 上从 4/4 掉到 3/4，而那一关还是绿的**（R45 读 CI 时看到）：",
         "66. **动效覆盖地板在 runner 上从 4/4 掉到 3/4，而那一关还是绿的**（R45 读 CI 时看到）"
         "**—— R46 已收口**：判据搬进 `scripts/motion_floor_gate.py` + 登记表 "
         "`scripts/motion_floor_expectations.json`，八条规则各配一支变异（M216–M222）。"
         "剩下的是**下一台机器**的问题：这张表说的是 runner 的前提，不是本机的。"),
    ])
    patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])
    with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
        f.write(VISUAL)
    patch("AGENT_STATE.md", [
        ("  下一轮优先做**能产生像素证据**的那类（分带抓帧 / 能进设置窗口的胶片通道），\n"
         "  否则就承认这一维的上限并把话写死。",
         "  下一轮优先做**能产生像素证据**的那类（分带抓帧 / 能进设置窗口的胶片通道），\n"
         "  否则就承认这一维的上限并把话写死。" + STATE),
    ])
    print("R46 主体台账已写入")


main()
