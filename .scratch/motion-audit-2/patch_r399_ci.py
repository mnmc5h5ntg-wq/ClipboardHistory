#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R399 追记：CI 三步红分诊、436 结案、帧数从 4→18、电池/修复后的读数。"""
import io
import os

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)


def once(text, anchor, repl):
    assert text.count(anchor) == 1, "锚点命中 %d 次：%r" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, repl, 1)


ui = rd("AGENT_UI_AUDIT.md").splitlines(keepends=True)
out = []
inserted_1420 = False
replaced_1418 = False
replaced_1419 = False
for line in ui:
    if line.startswith("- **U-1418："):
        out.append("- **U-1418：BACKLOG 436 结案 —— 第五臂在 runner 上真的判到了。** `40280951026 ↔ cfbcec7` 现读 `MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=-`；`40280864844 ↔ ae202dd` 仍 in_progress（未读，不拿它许愿）。已按实测把 `settings-reset-fade` 写进 `scripts/motion_floor_expectations.json`（`must_judge=true`、无 allowed_not_run_reasons），并一次性更新 `test_motion_floor_gate.py`：SUMMARY 五臂、地板 4、R46 旧日志预期多一格 MISSING_KEY；把同一组 runner 行重放进闸门现读 `MOTION_FLOOR_OK=5/5 REDS=0`，`test_motion_floor_gate` 50/50 OK。**436 关单**：不是拿本地读数关的，是 runner 自己判到 5/5。\n")
        replaced_1418 = True
        continue
    if line.startswith("- **U-1419："):
        out.append("- **U-1419：① 367 rot 与八步。** `HIDDEN_ARMS 表=242 可判=835 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`；预检 `tables=155 covered=138 arms=417 bad=0`、全仓 248 文件 / 901 把；三表 `M1039/M1040/M1041` 全 CAUGHT。build **0** 告警；全量 `Executed 1060 tests, with 52 tests skipped and 0 failures`；捕获 `CAPTURED 182 -> /tmp/r399_shots`，与 R398 逐张比 `变了=18`（四张 600pt 布局帧 + 空态/加载墨档 14 张），帧基线同一笔 `UPDATED=182`、复验 `COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `381=381`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（as-of 398；本轮产品视觉已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 398`）。电池 `Ran 683 / OK (skipped=4)`。\n")
        out.append("- **U-1420：CI 三步红的分诊与修复。** `40280951026 ↔ cfbcec7` = failure，全部失败步骤逐条：`STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`。① Swift tests `Executed 1057 tests, with 64 tests skipped and 2 failures`：`testCopyFailurePillTurnsRedAndSuccessDoesNot` 在 runner 亮 **2.90** / 暗 **2.55**（地板 3.0）；`testCaptureKeyViews` 的 R392 录制环 `idleBlue=4284/465`（runner 整页 diff 把侧栏强调蓝卷进来）与 R398 加载句 **3.75**（0.85 墨档在 1x 字体平滑下不够）。② Capture gate `passed=89 skipped=16 failed=2 有名字的红=2`，红名就是上面两条，不是未知红。③ Motion floor 唯一红是 `MOTION_FLOOR_UNLISTED_SCENARIO settings-reset-fade`，即 436，已按 U-1418 登记。归因：`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e`、`40221947072 ↔ 43ff699` 三跑均 success ⇒ 这些红是 R392（录制环 guard）/R394（失败红）/R398（加载墨档）在 runner 上第一次被跑到，不是 R399 布局位引入；但本轮必须修。修法：录制环只数产品控件自己的带（x470..620/y240..285pt，runner 的整页 diff 不再卷侧栏蓝）；`paneMessageInkStyle` 从 0.85 抬到 `.primary`（本地空态/加载 6.73/8.31）；失败红改亮 `0.72,0,0` / 暗 `1.0,0.62,0.58`（本地 8.38/6.45）。本地重跑 copy 测试通过、capture 卷 182 帧通过、全量 1060/52/0；这些修复要等下一次 push 的 runner 跑签收。\n")
        replaced_1419 = True
        continue
    out.append(line)
assert replaced_1418 and replaced_1419
ui = "".join(out)
ui = once(ui, "U-1415…U-1419）：600pt", "U-1415…U-1420）：600pt")
ui = once(ui, "U-1415…U-1419 · 产品 2 文件", "U-1415…U-1420 · 产品 2 文件")
wr("AGENT_UI_AUDIT.md", ui)

state = rd("AGENT_STATE.md")
state_note = """### R399 追记：CI 40280951026 三步红与 436 结案（2026-10-26）

`40280951026 ↔ cfbcec7` 现读 failure，三个失败步骤逐条：`STEP[15] Swift tests`、`STEP[17] Capture gate`、`STEP[19] Motion coverage floor`。Swift 卷 `Executed 1057 / skipped 64 / failures 2`：复制失败红在 runner 亮 2.90 / 暗 2.55（地板 3.0）；`testCaptureKeyViews` 的录制环 idleBlue=4284/465，以及 R398 加载句 3.75（0.85 墨档在 runner 1x 字体平滑下不够）。Capture gate 的 2 条红有名字；Motion floor 唯一红是 UNLISTED `settings-reset-fade`。旧两跑 `40234023212↔d38ea10` / `40234058148↔5c7814e` / 对照 `40221947072↔43ff699` 均 success ⇒ 红来自 R392/R394/R398 在 runner 上的首次执行，不是 R399 布局位；本轮已修：录制环只数控件带、pane 墨档抬到 primary、失败红亮 0.72,0,0 / 暗 1.0,0.62,0.58。修后本地：copy 测试通过、capture 182 帧通过、全量 `1060/52/0`、电池 `683/4`。

**436 结案**：`40280951026` 的 `MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=-`，`settings-reset-fade=2` 真的判到；已把第五臂写进 `motion_floor_expectations.json`（`must_judge=true`）并同步 `test_motion_floor_gate.py`（SUMMARY 五臂、地板 4、旧日志多一格 MISSING_KEY）；重放同一组 runner 行 `MOTION_FLOOR_OK=5/5 REDS=0`。`40280864844 ↔ ae202dd` 仍 in_progress 未读。

**R400 ⓪ 目标**：push R399 后读新 run 全部失败步骤（尤其确认三条修复在 runner 上通过）；补读 40280864844；若新 run 仍红，按步骤名逐条落账，不用 0 字节日志猜绿。
"""
state = once(state, "## R398 状态（2026-10-26", state_note + "\n## R398 状态（2026-10-26")
wr("AGENT_STATE.md", state)

report = rd("AGENT_FINAL_REPORT.md")
report = once(report, "U-31 … U-1419（R399 现读抬到最新一节）", "U-31 … U-1420（R399 现读抬到最新一节）")
report = once(report, "D-069 … **D-389**", "D-069 … **D-390**")
report = once(report, "默认 182 帧中四张 600pt 帧变化", "默认 182 帧中 18 张变化（4 张 600pt 布局 + 14 张空态/加载墨档）")
report = once(report, "436 无可用 runner motion 读数，仍未结案；rot 0/0。", "436 已在追记结案（runner 5/5）；rot 0/0。")
report = once(
    report,
    "**push 已恢复：`5c7814e..ae202dd` → ahead=0；两旧跑 success 无失败步骤，新跑 `40280864844`/`40280951026` in_progress 记具名 NOT-RUN。**",
    "**push 已恢复：`5c7814e..ae202dd` → ahead=0；两旧跑 success 无失败步骤。新跑 `40280951026 ↔ cfbcec7` 三步红（Swift/Capture/Motion floor）已分诊并修，`40280864844 ↔ ae202dd` 仍 in_progress。**")
report = report.rstrip() + "\n\n- **R399 追记（CI 分诊 + 436 结案）**：`40280951026 ↔ cfbcec7` failure 的三个失败步骤是 `Swift tests` / `Capture gate` / `Motion coverage floor`。Swift 卷 2 条红：复制失败红 runner 亮 `2.90` / 暗 `2.55`（地板 3.0）、`testCaptureKeyViews` 的录制环 idleBlue `4284/465` 与 R398 加载句 `3.75`；Capture gate 红名同上；Motion floor 唯一红是 UNLISTED `settings-reset-fade`。旧两跑与对照三跑 success ⇒ 红来自 R392/R394/R398 的 runner 首跑，不是 R399 布局位。已修：录制环只数控件带、pane 墨档抬到 primary（本地 6.73/8.31）、失败红改亮 `0.72,0,0` / 暗 `1.0,0.62,0.58`（本地 8.38/6.45）；本机 copy/capture/全量 `1060/52/0`、电池 `683/4`。**436 结案**：runner `judged=5/5`、`settings-reset-fade=2`，JSON 已登记 `must_judge=true`，自测五臂且 `MOTION_FLOOR_OK=5/5 REDS=0`；`40280864844` 仍 in_progress 未读。\n"
wr("AGENT_FINAL_REPORT.md", report)

decisions = rd("AGENT_DECISIONS.md").rstrip() + "\n" + """
### D-390（399）本机 2x 的对比度读数是 runner 1x 的上界：红/墨档必须在 runner 上签过

R399 现读：复制失败红本机亮 4.57 / 暗 4.70，runner 只有 **2.90 / 2.55**；pane 墨档 0.85 本机 4.84，runner **3.75**；R392 录制环的整页 diff 在 runner 上把侧栏强调蓝卷进来（idleBlue 4284/465）。三者都不是本轮布局位引入，而是 R392/R394/R398 第一次在 runner 上被跑到。
**Why**：本机是 2x、字体平滑与 runner 不同，同一份颜色/字墨在 1x 上会掉一档；拿本机读数替 runner 签字，等于把“会在用户面前发生的那档机器”排除在验收之外。整页 diff 还会把无关的强调色卷进蓝色计数，把通道噪声读成产品残留。
**How to apply**：① 任何新的对比度/颜色判据，本机通过只是候选，runner 现读才是签字；② 失败红用“亮压深 / 暗提亮”的一对值，不用单一系统红赌两档；③ 录制/浮层类像素守卫只数**产品控件自己的带**，整页 diff 只做端态证据；④ 颜色/墨档改动要同时保留 local 与 runner 两个读数，差一档时先改产品再谈放宽地板。
"""
wr("AGENT_DECISIONS.md", decisions)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """
436 结案（R399 · runner 读数到手）：`40280951026 ↔ cfbcec7` 现读 `MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2` ⇒ 第五臂 `settings-reset-fade` 在 runner 上真的判到。已把 `settings-reset-fade` 写进 `scripts/motion_floor_expectations.json`（`must_judge=true`、`stale_if_judged=false`、无 allowed_not_run_reasons），并同步 `scripts/tests/test_motion_floor_gate.py`（SUMMARY 五臂、地板 4、R46 旧日志预期多一格 MISSING_KEY）；把同一组 runner 行重放进闸门 `MOTION_FLOOR_OK=5/5 REDS=0`、50/50 OK。**这一单不是拿本地 `judged=5/5` 关的，是 runner 自己判到的。** `40280864844 ↔ ae202dd` 仍 in_progress，未拿它替这一单签字。
"""
wr("AGENT_BACKLOG.md", backlog)
print("R399_CI_PATCH_OK")
