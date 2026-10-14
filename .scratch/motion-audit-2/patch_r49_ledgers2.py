#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R49 第二段台账：STATE / BACKLOG 75（R48 的 CI 里新长出来的一条）/ 批次 51 / 最终报告对账。

数字来源：
  748 tests / 29 skipped / 0 failures       <- /tmp/r49-full.log
  CAPTURE_GATE_RESULT=ok 红=0                <- /tmp/r49-gate.log
  116 帧 CHANGED=0 MISSING=0 ADDED=0         <- /tmp/r49-base.log
  脚本 101 全绿 / swift build 0 告警           <- /tmp/r49-scripts.log
  M240–M244 五支全 CAUGHT                     <- /tmp/r49-mutate.log
  R48 CI（run 38536051202，success）          <- gh run view --log
"""
import io
import os
import re

os.chdir("/Users/wangziyi/Codex_Project0")

STATE = '''

---

## R49 · 目标里那句"采集路径不许同步写盘"，40 轮以来没有一条判据在管（第 51 轮 / U-75 / D-108）

- **本轮最难看的一条事实**：阶段一的目标里明写着"采集路径上不许有同步磁盘写"，
  而 `Tests/` 里**没有任何一条判据在管它**。实现是对的（`recordCopy` 只排去抖），
  但"对"不可证 —— 把同步写盘塞回去，748 条用例一条都不会红。
  新增 `CapturePathWriteBudgetTests`（3 条）之后，M240 真的把它塞回去试了一次：红了。
- **两条判据各管一件事**：结构判据（复制之后临时目录**一个文件都不许多** + "去抖到期必须出现"的对照组）
  管"有没有写盘"，与机器快慢无关；时长判据（40 个样本，中位与 p95 分开）管"不写盘但算了多久"。
  只要计时判据会在慢机器上恒红、快机器上恒绿；只要结构判据会漏掉"没写盘但卡 200ms"。
- **门槛从实测推导**：本机三次跑 `median=0.59 / 0.56 / 0.63ms`、`p95=1.46 / 1.28 / 1.34ms`、
  `max=3.08 / 2.27 / 1.50ms` ⇒ 中位门槛 10ms（实测的 17 倍，且在可感知线 ≈100ms 之下），
  p95 门槛 40ms（4×）。Runner 若顶红，按 R38 的规矩是**门槛错**不是产品错。
- **BACKLOG 73 结案**：R48 那次 260ms 抓帧空档**不在产品的采集链上**（产品侧 `add` 中位 0.6ms、
  盘上不多文件），它是探针自己对新生子树的首帧 `cacheDisplay` —— R11 在同一份文件里记过
  "新窗口的头两次要 260–340ms 一帧"，量级与位置都对得上。旁证：开臂 `粗260`、**关臂 `粗6`**。
  剩下的真问题另开 **BACKLOG 74**（淡入第一帧的真实成本，现在的读数混着冷缓存不能当产品数用）。
- **R48 的 CI 已读**（run 38536051202，success）：`Executed 745 tests / 36 skipped / 0 failures`、
  离屏闸门 `passed=25 skipped=9 failed=0 NOT_RUN=24`、
  地板闸门 `MOTION_FLOOR_OK=4/4 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`（judged 从 R47 的 3/4 回到 4/4）。
  **但 `motion suite exit: 1`** —— 这一步是 report-only，所以红的是一条被吞掉的用例：
  ```
  MOTION_NATIVE row-insert 开 帧数=4 峰值=0.052 采样≈28ms
  MOTION_NATIVE row-insert 关 帧数=1 峰值=0.061 采样≈18ms
  MOTION_NATIVE row-move   开 帧数=1 峰值=0.047 采样≈28ms
  MOTION_NATIVE row-move   关 帧数=1 峰值=0.047 采样≈15ms
  testNativeRowMoveIsVisibleToTheRuler]' failed (2.682 seconds)
  ```
  这是**这台机器第一次真的跑完这条判据**（以前每次都是 `app-not-active` 而 skip）。
  同一次运行里 `row-insert` 看得见（开 4 帧 / 关 1 帧），`row-move` 开关两臂一模一样 ⇒
  **探针能看见行动画，而"移动"这一条没被看见**。新开 **BACKLOG 75**，
  它是阶段二以来第一条"可能是产品少做了一段动画"的候选（不是尺的问题，因为同一卷里 insert 是好的）。
- **本轮自己错一处**：先写的 `XCTAssertEqual(samples.count, Self.sampleCount)` 恒真
  （断言右边就是驱动循环的常量），设计 M243 时才看见 ⇒ 改成与取值无关的地板 `minimumSampleCount = 20`。
- **验证**：3 条判据 + 真值表 7 格、M240–M244 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）、
  748 tests / 29 skipped / 0 failures、闸门 `红=0`、脚本 101 全绿、0 告警、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、`Sources/` 与提交前逐字节相同（M240 改过，已还原）。
  **本轮不换装**。自评 **94 / 100**（涨的那一分在七个维度里没有能诚实收下它的位置，记在文字里）。
- **下一步（R50）**：① **BACKLOG 75**（行移动到底有没有动画：本机复现 + 归因，
  这次要防的是"把它当成探针的锅"——同一卷里 insert 是被看见的）；
  ② BACKLOG 71（热图梯子相邻档可分辨性）；③ BACKLOG 72（其余调用点还在跨度上）；④ 读 R49 的 CI。
'''

BACKLOG75 = '''
75. **runner 第一次跑完 `testNativeRowMoveIsVisibleToTheRuler`，它红了**（R48 的 CI，run 38536051202）：
    ```
    MOTION_NATIVE row-insert 开 帧数=4 峰值=0.052 采样≈28ms / 关 帧数=1 峰值=0.061 采样≈18ms
    MOTION_NATIVE row-move   开 帧数=1 峰值=0.047 采样≈28ms / 关 帧数=1 峰值=0.047 采样≈15ms
    ```
    这条判据以前每次都是 `MOTION_NOT_RUN=app-not-active`（非激活进程里 NSTableView 不跑行动画），
    所以它**从来没有在 runner 上出过结论**。这一次出了，而且是红。
    为什么这次不能直接归给探针：**同一卷里 `row-insert` 看得见**（开 4 帧、关 1 帧）
    ⇒ 那台机器、那个进程、那次采样是**能看见行动画的**，只有"移动"这一条两臂完全相同。
    产品语义上这条最该动：复制一条已有记录会把它**移到列表顶部**，
    如果它是瞬移，用户看到的是"这一条消失了、另一条冒出来"，而不是"它跑到上面去了"。
    怎么查（不许猜着修，也不许先改判据）：
    ① 本机复现 —— 想办法让探针进程真的激活（`NSApp.activate` 之后 `NSApp.isActive` 必须为 true，
       这条判据现在就是靠它 skip 的），拿到与 runner 同一形状的第二份读数；
    ② 读产品代码：那条移动走的是 `List` 的数据重排还是 `withAnimation`？
       如果重排发生在 `HistoryStore` 里而外面没有动画事务，那"看不见"就是**产品没做**；
    ③ 若 ② 成立 ⇒ 补一段 `withAnimation(.rowReorder)` 并让这条判据从"看不见=红"
       变成"看不见=红且能看见=绿"的正常形状；若 ② 不成立（有事务仍看不见）
       ⇒ 那是 `List` 在 macOS 12 上不做行移动动画，要写进"这一维的上限"，别再空转。
    **这一步的判别力关键**：`row-insert` 在同一卷里是好的，所以"探针不行"这个解释已经被否掉一半。
'''

BATCH = '''

---

## 批次 51 · R49：本轮没有产品改动；有一条**只有你的眼睛能判**的新问题（U-75 / BACKLOG 75）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮加的是判据，不是画面。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 51.1 | 在列表里**复制一条已经在列表里的旧记录**（选中它按 ⌘C，或点"复制"） | 它是**滑到顶部**的，还是**瞬间跳上去**的？如果它是"从原位置消失、又出现在顶部"，请说这一句 | runner 第一次跑到这条判据就报红：同一卷里"新增一行"看得见动画，"移动一行"两臂完全相同。我这边进程无法激活，量不到 |
| 51.2 | 顺手回答 50.2：复制那一下有没有约 0.1–0.3 秒的停顿 | 有 / 没有 / 说不清 | 本轮把产品的 `add` 量到 0.6ms 中位，所以如果仍有可感停顿，它不在采集链上，得换地方找 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50 共 20 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**51.1（移动到底动没动）**。
'''


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve(expected_count):
    """曲线由解析器生成，并与报告里现有那一行做**前缀对账**（理由见 R48 那段）。"""
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
    old_clause = "自评曲线（%s 轮，Round 9–%s，均值 **%s**，最低 %s）：\n%s。\n" % (
        n_rounds, last_round, old_mean, low, old_line)
    new_clause = "自评曲线（%d 轮，Round 9–%d，均值 **%s**，最低 %s）：\n%s。\n" % (
        len(values), int(last_round) + 1, mean, low, bolded(values))
    return head, old_clause, new_clause


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


def main():
    head, curve_old_clause, curve_new_clause = check_curve(42)
    pairs = [
        ("| 阶段二 **41 轮**审计（R9–R48） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–48 |",
         "| 阶段二 **42 轮**审计（R9–R49） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–49 |"),
        ("| 决定台账 | D-069 … D-107 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-108 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **745** 例（29 skip / 0 failures",
         "| 判据 | 653 → **748** 例（29 skip / 0 failures"),
        ("+ **M100–M239**（阶段二 140 支）",
         "+ **M100–M244**（阶段二 145 支）"),
        (curve_old_clause, curve_new_clause),
        ("| 视觉台账 | U-31 … U-74（44 条；", "| 视觉台账 | U-31 … U-75（45 条；"),
        ("U-74 是**把「没抓到」写成「看不见」**",
         "U-75 是**一条硬要求写了 40 轮、没有一条判据在管**：目标里"
         "\"采集路径上不许有同步磁盘写\"直到 R49 才有会红的判据（M240 拿产品代码试过，确实会红）；\n"
         "U-74 是**把「没抓到」写成「看不见」**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–50 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–51 轮 |"),
    ]
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    for old, _ in pairs:
        assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])
    with io.open("AGENT_STATE.md", "a", encoding="utf-8") as f:
        f.write(STATE.lstrip("\n"))
    with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
        f.write(BACKLOG75)
    with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
        f.write(BATCH)
    patch("AGENT_FINAL_REPORT.md", pairs)
    print("R49 第二段台账已写入；曲线核对：", head)


main()
