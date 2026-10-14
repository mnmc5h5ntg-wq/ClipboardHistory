#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R46 收尾：BACKLOG 57 补两个数、人工批次 48、AGENT_FINAL_REPORT 的计数。

曲线与均值**现算 + assert**（R44 凭记忆写曲线写错过一次）。
字符串里一律用「」不用 ASCII 双引号 —— R45 那版脚本因为 `\\"` 直接 SyntaxError，
而它是在跑之前不会被发现的（解析期就炸），这种坑靠"写完先 ast.parse"挡。
"""
import ast
import io
import os
import re

os.chdir("/Users/wangziyi/Codex_Project0")


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


t = io.open("AGENT_VISUAL_ITERATION.md", encoding="utf-8").read()
cur = None
scored = []
pat_score = re.compile(r"(?:^### 自评 |\*\*自评 )(\d+) ?/ ?100")
for line in t.split("\n"):
    m = re.match(r"^## (Round [0-9]+[a-z]?)(?:（[^）]*）)?", line)
    if m:
        cur = m.group(1)
        continue
    if cur:
        s = pat_score.search(line)
        if s:
            scored.append((cur, int(s.group(1))))
            cur = None
vals = [v for r, v in scored if int(re.match(r"Round (\d+)", r).group(1)) >= 9]
n = len(vals)
mean = sum(vals) / n
assert n == 39, ("阶段二应为 39 轮（Round 9…46，含 29d）", n)
assert vals[-2:] == [94, 94], vals[-2:]
print("曲线 n=%d mean=%.4f min=%d below90=%d"
      % (n, mean, min(vals), sum(1 for v in vals if v < 90)))
curve = " · ".join(str(v) if v >= 90 else "**%d**" % v for v in vals) + "。"

OLD_CURVE = ("91 · 90 · 92 · 93 · 94 · 95 · 96 · 93 · 95 · 91 · **86** · **89** · 91 · **87** · 90 · 92 · "
             "91 · 92 · 91 · 92 · 90 · **89** · 90 · **89** · 94 · 90 · 90 · **89** · 90 · 91 · 90 · "
             "**89** · 90 · 91 · 92 · 92 · 93 · 94。")
assert OLD_CURVE in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read(), "旧曲线锚点没找到"

patch("AGENT_BACKLOG.md", [(
    "       在复现之前，账本里这两个数字**不许**被当成同一把尺比较（U-62 的口径版）。",
    "       在复现之前，账本里这两个数字**不许**被当成同一把尺比较（U-62 的口径版）。\n"
    "    **R46 又添两个数**（同一个计数器，两次 CI）：run 38514753036（R44）`NOT_RUN=8`、\n"
    "    run 38519597818（R45）`NOT_RUN=24`，而两次的 `Executed 735/742 tests, with 36 skipped` 几乎一样。\n"
    "    ⇒ 这条不再是「某两轮之间少 35 条」的孤例，而是**这个计数器每次都在动**：\n"
    "    40 → 5 → 8 → 24。四个数、同一把尺，中间没有改过打印路径的轮次占多数。\n"
    "    R46 的新闸门管的是动效那一族（它数的是**臂**，不是行数），管不到这里 —— 已明确记进 D-105。\n"
    "    下一轮做这件事的方法不变：**先复现再解释**，本机跑一次带 `CLIPBOARD_HISTORY_UI_SHOTS` 的\n"
    "    `--filter UICaptureTests` 把闸门喂进去，看本机报几；再对某一次 runner 日志逐条点名。",
)])

BATCH = '''

---

## 批次 48 · R46 本轮**没有可人工验收的东西**（U-72 / D-105）

这一轮改的是 CI 的一道闸门（`scripts/motion_floor_gate.py` + 一份登记表），
`Sources/` 一个字节没动，116 张帧逐字节不变 ⇒ **没换装**，装了旧包和装新包界面上不会有任何差别。
如果你在机器上看到任何不同，那说明我提交的东西和我说得不是一回事，请直接把版本号告诉我。

延续有效、仍然欢迎回答的：**批次 43、44、45、47 共 16 条**。
最想要回答的两条还是 45.1（导出反馈数据不再弹模态，你更喜欢哪一种）与
47.1（热图那些格子，鼠标划过去**那一圈到底出现没有** —— 本轮量的是「画出来长什么样」，
"鼠标真的会触发它"这一半只有你的机器能判）。

下一轮（R47）的靶已经在台账里：`testHeatmapFadeIsNotVisibleToThisRuler` 那条 A/B
用帧数当判据，而本机实测两臂峰值完全相同（0.226 / 0.226）—— 红的是尺，不是产品。

'''
with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
    f.write(BATCH)

R = "AGENT_FINAL_REPORT.md"
patch(R, [
    ("阶段二 全面独立动效与视觉审计 R9–R45", "阶段二 全面独立动效与视觉审计 R9–R46"),
    ("| 阶段二 **38 轮**审计（R9–R45） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 | `AGENT_VISUAL_ITERATION.md` Round 9–45 |",
     "| 阶段二 **39 轮**审计（R9–R46） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 | `AGENT_VISUAL_ITERATION.md` Round 9–46 |"),
    ("| 视觉台账 | U-31 … U-71（41 条；", "| 视觉台账 | U-31 … U-72（42 条；"),
    ("而那一圈从没被画出来量过（112 张帧里没有一张带悬停态） | `AGENT_UI_AUDIT.md` 第 10–47 轮 |",
     "而那一圈从没被画出来量过（112 张帧里没有一张带悬停态）；\n"
     "U-72 是**闸门自己的洞**：动效覆盖地板从 R7 起只问 `judged<2`，于是 R44 那次 `4/4 → 3/4`"
     "（一臂整个没采到）整步仍然绿，而理由行被 `head -24` 挤出了日志 —— 我是人肉对比三次 run 才发现的 | "
     "`AGENT_UI_AUDIT.md` 第 10–48 轮 |"),
    ("| 决定台账 | D-069 … D-104 | `AGENT_DECISIONS.md` |", "| 决定台账 | D-069 … D-105 | `AGENT_DECISIONS.md` |"),
    ("| 脚本测试 | 72 → **83** passed（R36 新增闸门自测 11 条 + 硬门的四个形状） | `python3 -m unittest discover -s scripts/tests` |",
     "| 脚本测试 | 72 → 83 → **101** passed（R36 闸门自测 11 条 + 硬门的四个形状；"
     "R46 新增 `test_motion_floor_gate` 18 条，含一份**逐字真日志**当正对照） | "
     "`python3 -m unittest discover -s scripts/tests` |"),
    ("**M100–M215**（阶段二 116 支）", "**M100–M222**（阶段二 123 支）"),
    ("自评曲线（38 轮，Round 9–45，均值 **91.2**，最低 86）：",
     "自评曲线（39 轮，Round 9–46，均值 **%.1f**，最低 86）：" % mean),
    (OLD_CURVE, curve),
    ("| **BACKLOG 66 / 67 新开**（R45） |",
     "| **BACKLOG 66 已收口**（R46 / U-72 / D-105） | 动效覆盖地板从 R7 起只问 `judged<2` ⇒ "
     "R44 那次 `4/4 → 3/4`（`notice-banner-dismiss` 一臂没采到）整步仍然绿，而理由行被 `head -24` 挤出日志 | "
     "R45 读 CI 时是人肉对比三次 run 才发现 —— 这正说明「没人守」 | "
     "判据搬进 `scripts/motion_floor_gate.py` + 登记表 `motion_floor_expectations.json`，"
     "八条规则各配一支变异（M216–M222 全 CAUGHT）。**红不红取决于登记，不取决于读数**："
     "会随采样漂的臂判到、判不到都不红（否则恒红 → 守卫被人删），"
     "而「跑完却没有结论行」从 `exit 0` 改成红。**不判帧数**（R2 已证它随采样相位漂）。脚本自测 83 → 101 |\n"
     "| **BACKLOG 68 新开**（R46，R47 的靶） | `testHeatmapFadeIsNotVisibleToThisRuler` 的 A/B "
     "拿**帧数**当「看得见这条淡入」的判据 | 本机真跑一遍的读数是 "
     "`开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— 两臂峰值完全相同，只有帧数不同 | "
     "这条判据在用**自己宣布过不可靠的量**（R2：同一份代码本机跑过 2/3/2）⇒ 红的是尺，不是产品。"
     "R47 换成时长轴 + 真值表 + 变异 |\n"
     "| **BACKLOG 66 / 67 新开**（R45） |"),
])
print("R46 收尾台账已写入")
