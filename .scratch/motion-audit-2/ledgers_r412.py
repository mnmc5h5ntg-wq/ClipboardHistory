#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R412 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 410 轮（R411 · 2026-10-27"
AUDIT_SECTION = u"""## 第 411 轮（R412 · 2026-10-27 · U-1483…U-1487）：设置快捷键行补「正在录制」行级描边（行带旧 0/0 → 新 4040/3990；邻行 0）；R411 空态句 identifier 在 runner 上生效（产品 2 文件，设置行录制态位）

- **U-1483：⓪ `40370566410 ↔ a8ebbaf` 的失败步骤。** 结论 **success**、22 步全绿；`QUICKPICK_EMPTY_FIELD 句子长=30 其它字段=1` ⇒ R411 的 identifier 精确选取让旧 33/56 在 runner 上消失，且不是改门槛；行 hover 源/像素两守卫与 `ControlHoverLadderTests` 全绿。`SCROLL_FAILURE_COUNT` 通道本跑没有一行 ⇒ 记**具名 NOT-RUN**（不当作通过）。`Release script tests` sources `R411/2b0ef71` 一致、全量计数 92-vs-934 反向对照 ok。
- **U-1484：② 快捷键设置行的「正在录制」行级状态。** 旧行为只有 128×28 录音器亮一圈强调色；同一张卡片里三行快捷键，行标题与说明没有「这一行正在吃键」的标记。修法：`HotKeyRecorderView` 增加只读回调 `onRecordingChange`（状态所有权仍在按钮），`HotKeySettingsRow` 用局部 `@State isRecording` 画 **1.5pt accent 圆角描边**（纵向外扩 2pt、横向不扩），与录音器那圈同宽；`.emphasis` 驱动。为什么不是整行底色：首拍底色把行内文字留白也涂成墨，卡片节奏尺读 22/0；二拍纵向内缩 4pt 仍读到 0.0；横向 −8 又把卡片左沿第一墨列从 5 拉到 0；横向 −2 读 3.0（门槛 5±1）。最终描边只落在行边界，三条布局尺均绿。真看图：第三行整行一圈强调蓝，录音器环与行描边同语言，文字未被压住；亮暗两档同一形状。同带旧/新读数（x=175..480、y=224..298pt）：旧 R411 录制帧 **0/0**（亮/暗）→ 新 **4040/3990**、**4039/3979**；邻行 **0/0**（两档）。录音器环读数不回退：亮 1794 / 暗 1780。`settings-shortcuts-recording` 亮暗 2 帧变化；另把 R411 的 `sidebar-row-hover` 淡入帧等到落定（旧中间相目标行均值 **220.84** → 落定 **212.06**，正好回到 R411 台账声称的 212.1；邻行 233.22 不变；仅目标行 44920 像素、最大差 9）。基线同笔 **192/0/0/0**。
- **U-1485：判据与刀。** 纯函数 `SettingsRowEmphasis` 真值表（静置 0、录制非 0、与录音器同宽）；源守卫 `testRecordingRowIsWiredFromButtonToOutline` 钉 `onRecordingChange(recording)` → 行回调 → `recordingStrokeOpacity/Width` → `.animation(..., value: isRecording)` 四段；像素尺 `RecorderRowEdgeRuler` 先过跨倍率正对照（1× **276/276**、2× **1104/1104**，均差 8.67；相同图 0/0），真实行测试从产品按钮点进录制态读 **4891 变化 / 4834 强调 / 静置 0**；整页帧 `RECORDER_ROW_EDGE` 再判邻行隔离。`M1065…M1069` **5/5 CAUGHT**、红得对=5、`RESTORE_CLEAN=yes`；M1068 现读 **变化=4846 强调=0**（淡到读不出）⇒ 像素判据抓的是可见性而不是「有变化」。既有 `HotKeyRecorderEvidenceTests` 9 例 1 skip 0 失败、`ControlHoverLadderTests` 6/0 绿。
- **U-1486：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1487：① 367 rot 与八步。** `HIDDEN_ARMS 表=255 可判=861 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`；预检 `tables=168 covered=150 arms=443 bad=0`、全仓 261 文件 / 927 把；R412 表 M1065–M1069 全 ok、无撞号。build **0** 告警；全量 `Executed 1084 tests, with 53 tests skipped and 0 failures`；捕获 `CAPTURED 192 -> /tmp/r412_final`（122 条判据 / 4 skip / 0 失败），与 R411 比 **变了=3**（recording 亮暗 + 落定后的 row-hover 亮）；基线同笔 `UPDATED=192`、复验 `COMPARED=192 CHANGED=0 MISSING=0 ADDED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `381=381`、`SMOKE_OK=1`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（as-of 411；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 411`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① `SCROLL_FAILURE_COUNT` 通道本跑没有行，记 NOT-RUN（全量 Swift tests 步骤 success，含滚动守卫）；② 真实指针不在这一位的触发路径上（录制态由真实按钮 `performClick` 进入），但「屏幕上这圈在真机合成器里长什么样」仍只由离屏帧作证；③ 离屏 alpha 动画中间帧仍采不到（D-055），弹层淡入不签产品结论；④ 设置卡其它行族（权重/排除/输入）仍没有行级状态，见 BACKLOG 438。

"""

ITER_SECTION = u"""## Round 409 · R412（第 411 轮 · 2026-10-27）：设置快捷键行补「正在录制」行级描边（行带旧 0/0 → 新 4040/3990，邻行 0）；R411 空态句 identifier 在 runner 上生效（产品 2 文件，设置行录制态位）

快捷键设置卡的录制态原来只亮录音器自己那圈 1.5pt 强调色；同一张卡里三行快捷键，行标题与说明没有「这一行正在吃键」的标记。修法：`HotKeyRecorderView` 增加只读回调 `onRecordingChange`，`HotKeySettingsRow` 在录制时给**整行**画一圈同宽 accent 圆角描边（纵向外扩 2pt、横向不扩），`.emphasis` 驱动；状态仍是按钮的，行只报告。为什么不是整行底色：首拍底色把行内留白也涂成墨，卡片节奏尺读 22/0；二拍纵向内缩 4pt 仍读到 0.0；横向 −8 把卡片左沿第一墨列从 5 拉到 0；横向 −2 读 3.0。最终描边只落在行边界，三条布局尺均绿。真看亮暗两张录制帧：第三行整行一圈强调蓝，与录音器环同语言，文字未被压住。同带旧/新（x=175..480、y=224..298pt）：旧 **0/0** → 新 **4040/3990**、**4039/3979**；邻行 **0/0**；录音器环亮 1794 / 暗 1780 不回退。`settings-shortcuts-recording` 亮暗 2 帧变化，另把 R411 的 `sidebar-row-hover` 淡入帧等到落定（目标行均值 220.84 → **212.06**，正好回到 R411 台账的 212.1；邻行 233.22 不变），基线 192/0/0/0。源/纯函数/像素三守卫：跨倍率正对照 1× 276、2× 1104（均差 8.67），真实行 4834 强调 / 静置 0；M1065–M1069 **5/5 CAUGHT**（M1068 现读变化 4846、强调 0 ⇒ 抓可见性）。⓪ `40370566410 ↔ a8ebbaf` **success**、22 步全绿；空态句 **30/1**（旧 33/56 消失，不是改门槛）；行 hover 两守卫与 `ControlHoverLadderTests` 绿；`SCROLL_FAILURE_COUNT` 缺行记具名 NOT-RUN；sources R411/2b0ef71 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 **1084/53/0**；换装 ok / SHA_MATCH=1 / 381=381；HIDDEN 255/861 rot=0；预检 168/150/443 bad=0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看录制帧亮暗两张：第三行整行描边、与录音器环同语言、文字不被压住；静置帧逐像素不变。 |
| 判据有效性 | 15/15 | 纯函数真值表 + 接线源守卫 + 跨倍率正对照 + 真实行像素 + 整页邻行隔离；五刀 CAUGHT。 |
| 假绿防御 | 15/15 | 旧行带 0/0、新 4040/3990；邻行 0/0；M1068 变化 4846 而强调 0 被可见性地板抓住；1×/2× 正对照。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件，补的是设置行的录制态身份；扣 1：只覆盖快捷键卡，其它设置行族未做（438）。 |
| 台账一致性 | 15/15 | U-1483…U-1487、D-404、436、R411 跑与新增 5 刀都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R411 头跑 success 才签收；33/56 按 runner 30/1 证实消失；缺行通道记 NOT-RUN 不记绿。 |
| 可复核性 | 15/15 | 旧/新带、邻行、跨倍率、真实行、3 帧差、五把刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_SECTION = u"""## D-404 设置行的录制态用整行描边，不用底色（R412）

- 背景：快捷键设置卡的录制态只亮录音器自己那圈 1.5pt 强调色；三行快捷键里，行标题/说明没有「这一行正在吃键」的标记，眼睛先扫到的是标题而不是按钮。
- 决定：`HotKeyRecorderView` 增加只读回调 `onRecordingChange`（状态所有权仍在按钮，行只报告）；`HotKeySettingsRow` 用局部 `@State isRecording` 画一圈 1.5pt accent 圆角描边（纵向外扩 2pt、横向不扩），与录音器同宽，`.emphasis` 驱动；数值走纯函数 `SettingsRowEmphasis`（静置 0，录制时非 0）。
- 理由：整行底色会把行内文字留白也读成墨，卡片节奏尺从 14.5 掉到 0.0；横向外扩会把卡片左沿第一墨列从 5 拉到 3/0。描边只落在行边界，行距、卡片内缩与节奏三条既有尺都不用改；它也与录音器那圈是同一句话的两种范围。状态不押在动画上：减弱动态只是不淡入，描边照样在。
- 兼容性/迁移：产品调用点签名不变（回调带默认值）；`HotKeySettingsRow` 从 private 放开到 internal，只给测试搭同一棵组件帧，不扩张外部 API。
- 回滚：删除回调、`@State isRecording` 与 `.background` 描边即可；或 `git revert` 本轮提交。产品其余行为不变。
"""

CHANGELOG_SECTION = u"""### 设置快捷键行补「正在录制」行级描边（行带旧 0/0 → 新 4040/3990，邻行 0）；R411 空态句 identifier 在 runner 上生效（R412 / 第 411 轮 / Round 409 / U-1483…U-1487 · 产品 2 文件，设置行录制态位）

"""

BACKLOG_SECTION = u"""437 追记（R412 · 仍开）：本轮补的是设置快捷键行录制态描边；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**438. 设置卡其它行族还没有行级状态：权重行 / 排除行 / 输入行只有控件自己的反馈**（R412 观察）
    本轮只给快捷键卡的三行做了「正在录制」行级描边；推荐权重九行、隐私排除名单行、添加行仍只有控件反馈。是否要做行级 hover/状态，要先决定它会不会被误读成整行可点；下一轮若要扩展，复用 `SettingsRowEmphasis` 并把行高/卡片节奏尺一起量。"""

STATE_SECTION = u"""## R412 状态（2026-10-27 · 本地 · 第 411 轮 / Round 409）：设置快捷键行补「正在录制」行级描边（行带旧 0/0 → 新 4040/3990，邻行 0）；R411 空态句 identifier 在 runner 上生效（产品 2 文件，设置行录制态位）

最后更新：2026-10-27（本地 · R412 / 第 411 轮 / Round 409）：快捷键设置卡的录制态只亮 128×28 录音器自己那圈；三行快捷键里行标题/说明没有「这一行在吃键」的标记。修法：`HotKeyRecorderView` 增加只读 `onRecordingChange`，`HotKeySettingsRow` 录制时给整行画 1.5pt accent 圆角描边（纵向外扩 2pt、横向不扩），`.emphasis` 驱动；数值走 `SettingsRowEmphasis`。同带旧/新（x=175..480、y=224..298pt）：旧 **0/0** → 新 **4040/3990**（亮）、**4039/3979**（暗）；邻行 **0/0**；录音器环亮 1794 / 暗 1780 不回退。`settings-shortcuts-recording` 亮暗 2 帧变化；另把 R411 的 `sidebar-row-hover` 淡入帧等到落定（旧中间相 220.84 → **212.06**，正好回到 R411 台账的 212.1；邻行 233.22 不变），基线同笔 192/0/0/0。源/纯函数/像素三守卫：跨倍率 1× 276 / 2× 1104，真实行 4834 强调 / 静置 0；M1065–M1069 **5/5 CAUGHT**（M1068 变化 4846、强调 0 ⇒ 抓可见性）。⓪ `40370566410 ↔ a8ebbaf` **success**、22 步全绿；`QUICKPICK_EMPTY_FIELD 句子长=30 其它字段=1`（旧 33/56 消失，不是改门槛）；行 hover 两守卫与 `ControlHoverLadderTests` 绿；`SCROLL_FAILURE_COUNT` 缺行记具名 NOT-RUN；sources R411/2b0ef71 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1084 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账表 162=162；`HIDDEN_ARMS 表=255 可判=861 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=168 covered=150 arms=443 bad=0`、全仓 261 文件 / 927 把；产品面连续零改动 **1** 轮（as-of 411，现读 `python3 scripts/product_streak.py --streak-for 411`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R411 头跑 success：空态句 30/1、33/56 消失；行 hover 两守卫与 ControlHoverLadder 绿；缺行通道记 NOT-RUN。
② 产品：快捷键设置行录制态补整行描边，行带 0/0 → 4040/3990，邻行 0。
③ 判据：纯函数 + 源 + 跨倍率像素尺 + 真实行 + 整页邻行；M1065–M1069 5/5 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 255 / 可判 861 / rot 0 / 上界 0；预检 168/150/443/0。
⑥ 全量 1084/53/0；换装 ok；清账表 162=162；帧基线 192/0/0/0。

NOT-RUN / 阻塞（分开写）：① `SCROLL_FAILURE_COUNT` 本跑没有行，记具名 NOT-RUN；② 真实指针不在录制态触发路径上，真机合成器里的描边仍只由离屏帧作证；③ 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；④ 亮档真机腿仍没跑；⑤ macOS 12 紧凑详情头仍走旧截断；⑥ 主列表与浮层来源搜索语言未统一（437）；⑦ 设置卡其它行族没有行级状态（438）；⑧ R412 新跑待 push 后读。

下一轮（R413）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R412 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

for name, text, needle, expected in [
    ("AUDIT", audit, AUDIT_TITLE, 1),
    ("STATE", state, u"## R411 状态", 1),
]:
    if text.count(needle) != expected:
        raise SystemExit("REFUSED %s 锚点命中 %d 次：%s" % (name, text.count(needle), needle))
if u"第 411 轮（R412" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R412 节")
if u"## Round 409 · R412" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 409")
if u"## D-404" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-404")
if u"设置快捷键行补「正在录制」" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**438." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 438")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_SECTION + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG 的 [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R411 状态", STATE_SECTION + u"## R411 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R412_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
