#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R48 第二段台账：STATE / 批次 50 / 最终报告对账（含 R47 的 CI 追认）。

数字来源：
  745 tests / 29 skipped / 0 failures        <- /tmp/r48-full.log
  CAPTURE_GATE_RESULT=ok 红=0 NOT_RUN=0       <- 同一份日志
  116 帧 CHANGED=0 MISSING=0 ADDED=0          <- frame_baseline --against working compare
  脚本 101 全绿 / swift build 0 告警            <- unittest discover / swift build
  变异 M230–M239 十支全 CAUGHT                  <- /tmp/r48-mutate4.log
  曲线 41 轮 均值 91.4                          <- curve_from_ledger.py（本脚本再对一次账）
  R47 CI（run 38530030589，success）            <- gh run view --log
"""
import io
import os
import re

os.chdir("/Users/wangziyi/Codex_Project0")

STATE = '''

---

## R48 · 那条"演了 266ms 的淡入"是钟停了，而"看不见"是我写错的（第 50 轮 / U-74 / D-107）

- **本轮最重要的一行是撤回**：R11 起台账里写着"离屏 `cacheDisplay` 对纯 opacity 淡入可见性 = 0"。
  本轮第一次给这条 A/B 补上条带图，第 3 帧是**半透明中间态**（空态那行字与整块日历叠在一起）
  ⇒ 这条通道**看得见**这条淡入，只是不每次都抓得到。"没抓到"被写成"看不见"，
  是把探针的占空比当成了产品的极限 —— 与"把没跑写成跑过"同一族，方向相反。
- **我上一轮的假设也错了**：R47 我在源码注释里写"265ms 只能来自两波被跨度算法并成一段"。
  补上 per-run 打印之后真形状是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`
  —— **一段连续的**变化，段内有一次 **260ms 的抓帧空档**。缺的不是连续性，是**分辨率轴**。
- **改了什么**：① 撒谎的名字改回 `changedSpanElapsedMilliseconds`（行为不变）；
  ② 新建 `contiguousChangedRun(s)`（含峰值那一段 + 段内最粗采样）；
  ③ `fadeVisibility` 从两态改三态，新增 `.clockTooCoarse`（0.5×声明那档，沿用 `judgeMotion` 口径，
  排在一致性门**之前**）；④ `看不见` 分支文案改成"今天没抓到"；⑤ 三臂各出一张条带；
  ⑥ 调用点守卫钉四件事（段来源 / 臂归属 / 时长轴 / 分辨率轴有没有传）。
  本机今天的判定因此从"看不见"变成 **`判定=钟太粗`**（`MOTION_NOT_RUN=clock-coarse-in-window`，不红）。
- **新开 BACKLOG 73（性质比 69 硬）**：那次 260ms 的抓帧空档发生在**用户刚按下 ⌘C 的那一刻**。
  候选是首次布局 182 个格子、`DailyCopyLedger.record` 主线程侧的工作、或去抖落盘回主线程。
  目标里明令"采集路径上不许有同步磁盘写"，所以这条要单独量，不许猜着修。
- **本轮自己错四处，全部由数据顶回来**：真值表期望心算错（308 vs 实测 316）；
  守卫前两版都在读邻居（数词频、固定取两行 —— 同一支变异 M237 顶红了两次）；
  打印用了绝对时钟（`731797829–731797842`，跑一遍才看见）；
  **注释里写了一个没量过的数**（"约 130ms"是拿 266 ÷ 2 估的，实测是 260ms 的一次空档）。
  外加电池自己的一处错：M239 第一版把 `// MUTANT` 加在条件行尾，**顺手注释掉了 `{`**
  ⇒ 编译失败 ⇒ 电池如实报 `BROKEN-MUTATION`（这个码存在的意义就在这一格）。
- **验证**：真值表 15 + 8 格、M230–M239 十支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）、
  745 tests / 29 skipped / 0 failures、闸门 `红=0 NOT_RUN=0`、脚本 101 全绿、
  `swift build` 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`。**本轮不换装**（`Sources/` 未动）。
  自评 **94 / 100**。
- **R47 的 CI 已读**（run 38530030589，success）：`motion suite exit: 0`（R46 那次是 1）、
  `executed: 25`、`MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss`、
  新地板闸门第一次在 runner 上给出 `MOTION_FLOOR_OK=3/4 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`；
  离屏闸门 `passed=25 skipped=9 failed=0 NOT_RUN=24`（BACKLOG 57 那个漂移今天仍是 24，未解释）。
  runner 上那条淡入 A/B 的读数是 **开臂 249 / 227ms**（声明 160ms）——
  与本机同一族形状，所以 R47 那道上限门在 runner 上真的挡下了一次误判。
  R46 那次红的正是这条 A/B 的旧写法（`testHeatmapFadeIsNotVisibleToThisRuler]' failed`），
  本轮的靶因此有 runner 证据，不是我推出来的。
- **下一步（R49）**：① BACKLOG 73（那次 260ms 空档是谁占的，用"设置窗口没打开"的对照臂去量）；
  ② BACKLOG 71（热图梯子相邻档可分辨性，暗档第 1 级 vs 空格子）；
  ③ BACKLOG 72（其余调用点还在跨度上，先数真胶片有没有"段内掉回地板以下"）；④ 读 R48 的 CI。
'''

BATCH = '''

---

## 批次 50 · R48：本轮没有产品改动，但有一句旧结论被撤回（U-74 / D-107）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。

本轮的看图推翻了我自己写在台账里两轮的结论。想请你用眼睛替我确认一次：

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 50.1 | 打开 设置 → 统计（热图那一页），然后在别处**复制一条文本** | 那张日历是**淡进来**的，还是"啪"一下整块出现的？ | 我的离屏抓帧器能拍到半透明中间态，但它的占空比不稳；"人眼看不看得见那一下过渡"只有你判得了 |
| 50.2 | 同一次操作里感受**卡顿**：复制那一下有没有约 0.1–0.3 秒的停顿/掉帧 | 有 / 没有 / 说不清 | 我的探针量到触发后有一次 260ms 的抓帧空档（BACKLOG 73）。如果你说"没有"，那更可能是抓帧器自己慢，不是产品慢 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49 共 18 条**。
最想要回答的两条还是 45.1（导出反馈数据不再弹模态）与 47.1（鼠标真的划过去时那一圈出现没有）。
'''

U74 = ("U-74 是**把「没抓到」写成「看不见」**：R11 起台账说这条离屏通道对纯 opacity 淡入可见性 = 0，"
       "而 R48 第一次给它补上条带图，里面就有半透明中间态 ⇒ 那句撤回；同轮还发现自己那条长读数是"
       "一段连续变化里有一次 260ms 的抓帧空档（BACKLOG 73）；\n"
       "U-73 是**判据用错了自己宣布过不可靠的轴**")


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve():
    """曲线那一行由解析器生成，并与报告里现有那一行做**前缀对账**。

    为什么不是"脚本里抄一行新的"：抄的那一行正是最容易编出来的东西
    （R44 凭记忆写过一条不存在的曲线；R47 的解析器第一版漏掉 `Round 29d`）。
    这里要求：报告里的旧行必须正好是解析器结果**去掉最后一个读数**，
    两处独立数字对不上就不落盘。
    """
    import subprocess
    out = subprocess.run(["python3", ".scratch/motion-audit-2/curve_from_ledger.py"],
                         capture_output=True, text=True).stdout
    raw = [l for l in out.splitlines() if l.startswith("PHASE2 CURVE:")][0]
    values = raw.split("PHASE2 CURVE: ", 1)[1].split(" · ")
    head = [l for l in out.splitlines() if l.startswith("PHASE2 n=")][0]
    mean = [l for l in out.splitlines() if l.startswith("PHASE2 n=")][0].split("mean=")[1].split()[0]
    assert "n=41" in head, head
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    found = re.findall(r"自评曲线（(\d+) 轮，Round 9–(\d+)，均值 \*\*([\d.]+)\*\*，最低 (\d+)）：\n(.+?)。\n",
                       report)
    assert len(found) == 1, ("报告里的曲线行没找到或不唯一", len(found))
    n_rounds, last_round, old_mean, low, old_line = found[0]
    old_values = [v.strip("*") for v in old_line.split(" · ")]
    assert int(n_rounds) + 1 == len(values), (n_rounds, len(values))
    assert old_values == values[:-1], ("旧行不是解析器结果的前缀", old_values[-3:], values[-4:])
    assert last_round == "47", last_round
    old_clause = "自评曲线（%s 轮，Round 9–%s，均值 **%s**，最低 %s）：\n%s。\n" % (
        n_rounds, last_round, old_mean, low, old_line)
    new_clause = "自评曲线（%d 轮，Round 9–48，均值 **%s**，最低 %s）：\n%s。\n" % (
        len(values), mean, low, bolded(values))
    return head, old_clause, new_clause


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


def main():
    head, curve_old_clause, curve_new_clause = check_curve()
    pairs = [
        ("| 阶段二 **40 轮**审计（R9–R47） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–47 |",
         "| 阶段二 **41 轮**审计（R9–R48） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–48 |"),
        ("| 决定台账 | D-069 … D-106 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-107 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **743** 例（29 skip / 0 failures",
         "| 判据 | 653 → **745** 例（29 skip / 0 failures"),
        ("+ **M100–M229**（阶段二 130 支）",
         "+ **M100–M239**（阶段二 140 支）"),
        ("R46 / R47 各一张不加（两轮都零产品改动，116 帧 `CHANGED=0 MISSING=0 ADDED=0`） |",
         "R46 / R47 / R48 各一张不加（三轮都零产品改动，116 帧 `CHANGED=0 MISSING=0 ADDED=0`） |"),
        (curve_old_clause, curve_new_clause),
        ("| 视觉台账 | U-31 … U-73（43 条；", "| 视觉台账 | U-31 … U-74（44 条；"),
        ("U-73 是**判据用错了自己宣布过不可靠的轴**", U74),
        ("| `AGENT_UI_AUDIT.md` 第 10–49 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–50 轮 |"),
    ]
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    for old, _ in pairs:
        assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])
    with io.open("AGENT_STATE.md", "a", encoding="utf-8") as f:
        f.write(STATE.lstrip("\n"))
    with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
        f.write(BATCH)
    patch("AGENT_FINAL_REPORT.md", pairs)
    print("R48 第二段台账已写入；曲线核对：", head)


main()
