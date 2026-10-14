#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R50 台账（第 52 轮 / D-109 / U-76 / BACKLOG 75 推进 / CHANGELOG / Round 50 / 报告对账）。

数字来源：
  M245–M248 四支全 CAUGHT        <- /tmp/r50-measure.log + 验证跑（本脚本运行前）
  runner 真读数                  <- gh run view 38536051202 --log（R48 那次）
  全量测试 / 闸门 / 116 帧        <- /tmp/r50-full.log、/tmp/r50-gate.log、/tmp/r50-base.log
  曲线                           <- curve_from_ledger.py（本脚本会做前缀对账）
"""
import io
import os
import re

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 52 轮 · R50：runner 第一次跑完行移动那条判据就报红 —— 先修探针，再让结论分三态（BACKLOG 75 / U-76 / D-109）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `MotionFilmstripTests.TableProbe.record(animation:)` 的 move 臂 | 宣布一次 `moveRow` 之前先 `texts = texts.map { "·已挪" }` | **改了六行的文案，却只宣布一次移动**：两臂的像素差里混进"文字变了"，而产品那条分支根本不 rename（`QuickPickController.rebuildRows` 的移动分支只有 `moveRow`，文案变化走 `plan.reloads`）⇒ 归因不成立 |
| `testNativeRowMoveIsVisibleToTheRuler` 的结论 | 只有一句"帧数 ≥2 否则红" | runner 的真读数是 `开 帧数=1 峰值=0.047 / 关 帧数=1 峰值=0.047` —— 那句话**没分清**"瞬移"与"采样错过"，而这两种结论的性质不同（产品少做一段动画 vs 这台机器今天量不了） |
| 这条判据的可达性 | 本机每次 `app-not-active` ⇒ skip | 它**只在 runner 上、偶尔**才出结论，而且一出就是红。这种判据的分界如果画错了，没有任何人在本机发现得了 |

### 修法

1. **探针与产品逐行可对照**：删掉那次 rename。位置本身变了 ⇒ 每个下标上的内容就变了，
   不需要改文案也有像素可读。这一条不改结论，改的是"这个结论能不能算在产品头上"。
2. **结论分三态**：新增纯函数 `nativeMoveVerdict(animatedSpan:animatedPeak:instantSpan:instantPeak:)`
   - `animated`：开臂帧数 ≥2（含等号）；
   - `notAnimated`：帧数都是 1 **且**两臂峰值差 ≤ 0.02 ⇒ 形状一致 ⇒ 瞬移（**仍然红**，
     因为同一卷里 `row-insert` 的开臂能看见多帧、而 `wasActive` 为真，
     两个"是尺的问题"的解释都不成立）；
   - `samplingMissed`：帧数都是 1 但峰值差得远 ⇒ 打印 `MOTION_NOT_RUN=native-move-sampling-missed`，
     **不判产品**。
   判"形状一致"用**绝对值**：开臂变得比对照臂还少，同样是"说不清"，不是"一致"。
3. **读数与结论一起打**：新增 `MOTION_NATIVE_MOVE 判定=… 峰值容差=…`，
   并把"同一卷 insert 的读数就在上一行"写进日志，下一个人不必再推。

### 为什么这条红**不**改成 NOT_RUN

R36 立的规矩是"红必须有名字"，不是"红要少"。这条判据今天有名字、有读数、
还有同一卷里的阳性对照（insert 看得见），所以它是一个**站得住的产品侧候选缺陷**。
把它洗成 not-run 就是为了让日志好看 —— 那是把红藏起来，不是把红讲清楚。
真需要登记的是第三种形状（采样错过），它现在有自己的名字，不再寄生在"瞬移"那一格里。

### 真实视觉审查

本轮没有新帧（零产品改动，116 帧逐字节不变）。看的是**上一轮那三张条带之外的东西**：
把 R48 的 runner 日志按臂对齐读了一遍 —— `row-insert 开 4 帧 / 关 1 帧` 与
`row-move 开 1 帧 / 关 1 帧` 出自同一次运行、同一卷、同一个进程。
这个对比是本轮全部结论的来源：**同一把尺在同一个地方看得见另一种动**，
所以"看不见移动"不能先赖给尺。

### 验证

- 真值表 7 格（含 runner 今天那组真读数当第 ② 格）；变异 M245–M248 四支全 CAUGHT
  （`未被抓到=0 红得不对=0 还原不干净=0`）。
- `swift build --build-tests` 0 告警；全量测试与 116 帧见 STATE；**本轮不换装**。
- 自评 **94 / 100**。**CI 待读** —— 本轮的修法要等 runner 再给一次样本才算落地，
  那是唯一能跑到这条判据的机器。

'''

DECISION = '''
---

## D-109（R50）：一条只在别的机器上偶尔跑得到的判据，分界必须由真值表与变异钉死

**背景**：`testNativeRowMoveIsVisibleToTheRuler` 在本机每次都是 `app-not-active` skip，
它诞生以来只在某一次 runner 运行里出过一次结论，而那次是红。

**决定**：
1. 先修**探针的越权**：move 臂在宣布一次移动之前把六行文案全改了，而产品不这么做。
   不修这一条，红也好绿也好都不能算产品的结论。
2. 结论从两态改三态：动了 / 瞬移 / **采样错过**。中间那一格今天被并进了"瞬移"，
   而它俩的区别不是"红与不红"，是"这个结论算在谁头上"。
3. **不把这条红改成 not-run**：它有名字、有读数、有同一卷里的阳性对照。
   R36 的规矩是"红必须有名字"，不是"红必须少"。
4. 这种"本机跑不到"的判据，其分界一律配真值表 + 变异（M245–M248），
   并且真值表里必须有一格是**真读数**（第 ② 格 = runner 那次 1/0.047 vs 1/0.047）。

**代价**：判据多一个枚举、多一条打印；`samplingMissed` 那一格不红，
所以它必须像现在这样把两个峰值打出来，否则就是一个没人能反驳的空档。
'''

BACKLOG_PATCH = '''
75. **（R50 推进，仍未结案）**runner 第一次跑完 `testNativeRowMoveIsVisibleToTheRuler` 就报红：
    `row-insert 开 4 帧/关 1 帧` 与 `row-move 开 1 帧/峰值 0.047 = 关 1 帧/峰值 0.047` 出自同一次运行。
    R50 做了两件事：① 删掉探针在 move 臂里对六行文案的 rename（那是产品没做的动作，
    留着就不能把结论算在产品头上）；② 结论分三态，"峰值都是 1 帧但形状不同"从此叫
    `native-move-sampling-missed`，不再冒充"瞬移"。
    **还欠的**：修完探针之后的 runner 第二次样本。三种可能各自怎么走 ——
    a) `判定=动了` ⇒ 上一轮那次红是探针 rename 造成的，BACKLOG 75 结案，不写进任何产品缺陷；
    b) `判定=瞬移` ⇒ 产品侧缺陷成立（`moveRow` 的隐式动画在 macOS 12 这条路上不产生可见中间帧），
       下一轮去查 `NSAnimationContext` 的 duration 与 `runAnimationGroup` 的同步语义，
       并考虑像侧栏那样退回"整表刷新 + 淡入"这种确定看得见的表达；
    c) `判定=采样错过` ⇒ 这台机器今天量不了，继续挂着，**不许改成常绿**。
    人工批次 52.1 同时问用户的眼睛（快速选择浮层里候选重排那一下有没有滑）。
'''

BATCH = '''

---

## 批次 52 · R50：本轮没有产品改动；有一条**只有你能判**的新问题（U-76 / BACKLOG 75）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮改的是探针与判据。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 52.1 | 打开**快速选择浮层**（默认快捷键），先输入一两个字让候选变少，再删掉一个字让候选变多 | 列表里某一条**换位置**的那一下，是**滑过去**的，还是**直接跳过去**的？ | runner 报"跳"，但那是唯一一次跑到这条判据的机器；本机量不到（进程无法激活） |
| 52.2 | 同一个浮层里，用**方向键**上下移动选中 | 选中条移动时有没有动画？（这一条我知道答案，只用来核对我的判据说的是不是同一件事） | 已知边界：九臂实验给出"选中变了会吃掉行动画"，这条是防我把两件事混起来 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51 共 22 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**51.1 / 52.1（移动到底动没动）**。
'''

CHANGELOG = '''### Fixed（R50：行移动那条判据先修探针，再让结论分三态）
- `TableProbe` 的 move 臂在宣布一次 `moveRow` 之前把**六行文案全改了**（`·已挪`），
  而产品那条分支不 rename（`QuickPickController.rebuildRows` 的文案变化走 `plan.reloads`）。
  ⇒ 两臂的像素差里混进了与动画无关的"文字变了"，那次红不能算在产品头上。删掉 rename。
- `testNativeRowMoveIsVisibleToTheRuler` 的结论从两态改三态：
  `动了 / 瞬移 / 采样错过`（新增纯函数 `nativeMoveVerdict`，真值表 7 格）。
  以前只有一句"帧数 ≥2 否则红"，把 runner 那组 `开 1 帧 0.047 / 关 1 帧 0.047`
  和"两帧数都是 1 但峰值差很远"混成同一种红 —— 而前者是产品侧候选缺陷，后者是今天量不了。
- 新增日志 `MOTION_NATIVE_MOVE 判定=… 峰值容差=…`，把结论与判据用的数一起打出来。
- **没有**把这条红改成 not-run：它有名字、有读数、有同一卷里 `row-insert` 的阳性对照。
- 产品代码零改动，116 张帧逐字节不变。变异 M245–M248 四支全 CAUGHT。

'''


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve(expected_count, new_last_round):
    import subprocess
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


VISUAL = """
---

## Round 50 · runner 报红之前，我先发现探针改了产品没改的东西（R50 / BACKLOG 75 / U-76 / D-109）

**这一轮问的问题**：R49 读 R48 的 CI 时撞见一条以前从没出过结论的判据报红了 ——
`testNativeRowMoveIsVisibleToTheRuler`。第一反应是"产品少做了一段动画"。
第二反应应该是：**这个探针做的事，产品做了吗？**

**答案是没有。** 探针在宣布一次 `moveRow` 之前，把六行文案全加了个后缀；
产品那条分支只移动、不改文案（文案变化走另一条 `plan.reloads`）。
于是两臂的像素差里混进了"文字变了"，那次红**不能算在产品头上**。删掉 rename，位置本身变了就有像素可读。

**第二个改动**：那条判据以前只有两态 —— 帧数 ≥2 算"看得见"，否则红。
runner 的读数是 `开 1 帧 峰值 0.047 / 关 1 帧 峰值 0.047`，
而"两臂都是 1 帧但峰值差很远"是另一种完全不同的事（今天量不了）。
现在分三态：`动了 / 瞬移 / 采样错过`，各自有自己的日志与后果。

**为什么没把红改成 not-run**：R36 的规矩是"红必须有名字"，不是"红必须少"。
这条红有名字、有读数，还有同一卷里 `row-insert 开 4 帧 / 关 1 帧` 当阳性对照
—— 同一把尺在同一个地方看得见另一种动。剩下能赖的只有采样，而那已经有自己的格子了。

**真实视觉审查**：本轮没有新帧（零产品改动、116 帧逐字节不变）。
看的是 runner 日志里两行读数的**并排关系**，本轮全部结论来自那一次对照。

**分数为什么持平**：`流畅度` 仍 13/20。本轮没有加任何动画；
它做的是**在把缺陷记到产品头上之前，先证明探针没有替产品做主**。

### 自评 94 / 100（与 R45–R49 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；行移动到底动没动，等修完探针之后的 runner 第二次样本 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；这条判据的结论从两态分成了三态 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：真值表 7 格（第 ② 格就是 runner 的真读数）、M245–M248 四支全 CAUGHT、0 告警、
全量测试与 116 帧见 STATE。**CI 待读：本轮的修法只有 runner 能验收。**
"""

STATE = """

---

## R50 · 报红之前先问：探针做的事，产品做了吗（第 52 轮 / U-76 / D-109）

- **靶**：R49 读 CI 时撞见 `testNativeRowMoveIsVisibleToTheRuler` 在 runner 上第一次出结论就是红
  （`row-move 开 1 帧 峰值 0.047 / 关 1 帧 峰值 0.047`），而**同一卷里** `row-insert 开 4 帧 / 关 1 帧`。
- **先抓到的是探针**：move 臂在宣布一次 `moveRow` 之前把六行文案全改了（`·已挪`），
  而产品的移动分支只 `moveRow`、不改文案（文案变化走 `plan.reloads`）
  ⇒ 两臂像素差里混进与动画无关的"文字变了"，那次红**不能算产品的结论**（U-76）。删掉 rename。
- **结论分三态**：`nativeMoveVerdict` ⇒ `动了 / 瞬移 / 采样错过`。
  以前只有"帧数 ≥2 否则红"，把"两臂形状一致"（产品瞬移）与"两臂都 1 帧但峰值不同"（今天量不了）
  混成同一种红。形状判据用**绝对值**：开臂变得比对照还少也是"说不清"。
- **没有把红改成 not-run**：它有名字、有读数、有同一卷的阳性对照。
  R36 的规矩是"红必须有名字"，不是"红必须少"。登记的是第三种形状（`native-move-sampling-missed`）。
- **真实视觉审查**：零产品改动、116 帧逐字节不变；本轮看图看的是 runner 两行读数的并排关系。
- **验证**：真值表 7 格（第 ② 格就是 runner 的真读数）、M245–M248 四支全 CAUGHT
  （`未被抓到=0 红得不对=0 还原不干净=0`）。
  **全量/闸门/帧基线没有独立跑过一遍**：R50 之后紧接着是 R51，验证跑在合并后的树上
  （750 例 / 29 skip / 0 failures / 0 告警 / 116 帧不变，原文见 R51 那一节与 `/tmp/r51-full.log`）。
  这一句是**记账不是结论** —— R50 单独那个提交从没被全量判据扫过，CI 跑的是 tip。
  自评 **94 / 100**。**CI 待读：本轮的修法只有 runner 能验收**（本机进程无法激活 ⇒ 每次 skip）。
- **下一步（R51）**：① 读 R50 的 CI，看 `MOTION_NATIVE_MOVE 判定=` 落在哪一格（三种可能各自怎么走，
  已写在 BACKLOG 75 里）；② BACKLOG 71（热图梯子相邻档可分辨性）；③ BACKLOG 72（其余调用点还在跨度上）。
"""


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    tail_anchor = ("    **这一步的判别力关键**：`row-insert` 在同一卷里是好的，"
                   "所以\"探针不行\"这个解释已经被否掉一半。")
    assert backlog.count(tail_anchor) == 1, backlog.count(tail_anchor)
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **42 轮**审计（R9–R49） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–49 |",
         "| 阶段二 **43 轮**审计（R9–R50） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–50 |"),
        ("| 决定台账 | D-069 … D-108 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-109 | `AGENT_DECISIONS.md` |"),
        ("+ **M100–M244**（阶段二 145 支）",
         "+ **M100–M248**（阶段二 149 支）"),
        ("| 视觉台账 | U-31 … U-75（45 条；", "| 视觉台账 | U-31 … U-76（46 条；"),
        ("U-75 是**一条硬要求写了 40 轮、没有一条判据在管**",
         "U-76 是**探针改了产品没改的东西，再把结论算在产品头上**：move 臂宣布一次移动之前把六行文案都改了"
         "（产品那条分支不 rename）⇒ R48 那次 runner 红不能算产品的结论（R50 修，并把结论分成三态）；\n"
         "U-75 是**一条硬要求写了 40 轮、没有一条判据在管**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–51 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–52 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    assert changelog.count("## [Unreleased]\n") >= 1
    # 先验锚点再动手：上一版这条脚本写到一半崩过，台账留下半截 R48 的格式（记在 U-73 那一族）。
    for old, _ in pairs:
        assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
        f.write(ROUND.lstrip("\n"))
    with io.open("AGENT_DECISIONS.md", "a", encoding="utf-8") as f:
        f.write(DECISION)
    with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
        f.write(VISUAL)
    with io.open("AGENT_STATE.md", "a", encoding="utf-8") as f:
        f.write(STATE.lstrip("\n"))
    with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
        f.write(BATCH)
    patch("AGENT_BACKLOG.md", [(tail_anchor, tail_anchor + "\n" + BACKLOG_PATCH.strip("\n"))])
    patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])
    # 曲线必须在 Round 50 落进台账之后再解析：先写后读，否则 `n=43` 这条断言拿到的是 42。
    head, curve_old, curve_new = check_curve(43, 50)
    patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    print("R50 台账已写入；曲线核对：", head)


main()
